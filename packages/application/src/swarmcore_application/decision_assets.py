from __future__ import annotations

import json
from typing import Any, Literal, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import (
    CapabilityPackVersion,
    DecisionExecution,
    EvaluationDecision,
    ProjectCapabilityBinding,
    ProjectCapabilityDecisionBinding,
    RuleSet,
    RuleSetDraft,
    RuleSetVersion,
)
from swarmcore_persistence.repositories import canonical_hash
from swarmcore_registry import CapabilityPackManifest
from swarmcore_spec.expressions import evaluate_condition, render_templates, validate_condition

from .integrity import IntegrityRuleDocument

DecisionType = Literal["CHECKLIST", "DECISION_TABLE", "EXPRESSION", "THRESHOLD"]


class DecisionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DecisionTestCase(DecisionModel):
    name: str = Field(min_length=1, max_length=128)
    input: dict[str, Any]
    expected: dict[str, Any]


class DecisionEnvelope(DecisionModel):
    api_version: Literal["swarmcore.io/decision/v1"] = Field(alias="apiVersion")
    kind: Literal["DecisionAsset"]
    type: DecisionType
    engine: Literal["swarmcore.rules.v1"]
    input_schema: str = Field(alias="inputSchema")
    output_schema: str = Field(alias="outputSchema")
    definition: dict[str, Any]
    tests: tuple[DecisionTestCase, ...] = ()

    @model_validator(mode="after")
    def validate_definition(self) -> DecisionEnvelope:
        if not self.input_schema.startswith("schema://") or "@" not in self.input_schema:
            raise ValueError("DECISION_ASSET_INVALID")
        if not self.output_schema.startswith("schema://") or "@" not in self.output_schema:
            raise ValueError("DECISION_ASSET_INVALID")
        if self.type == "EXPRESSION":
            expression = self.definition.get("condition")
            if not isinstance(expression, str):
                raise ValueError("DECISION_ASSET_INVALID")
            validate_condition(expression)
        return self


def normalize_decision(value: dict[str, Any]) -> DecisionEnvelope:
    if value.get("apiVersion") == "swarmcore.io/decision/v1":
        return DecisionEnvelope.model_validate(value)
    legacy = IntegrityRuleDocument.model_validate(value)
    return DecisionEnvelope(
        apiVersion="swarmcore.io/decision/v1",
        kind="DecisionAsset",
        type="CHECKLIST",
        engine="swarmcore.rules.v1",
        inputSchema="schema://contract/validation-input@1",
        outputSchema="schema://contract/validation-result@1",
        definition=legacy.model_dump(mode="json", by_alias=True),
        tests=(),
    )


def execute_decision(envelope: DecisionEnvelope, value: dict[str, Any]) -> dict[str, Any]:
    definition = envelope.definition
    if envelope.type == "EXPRESSION":
        return {"matched": evaluate_condition(str(definition["condition"]), value)}
    if envelope.type == "THRESHOLD":
        path = str(definition.get("path", "value"))
        operator = str(definition.get("operator", ">="))
        threshold = definition.get("threshold")
        return {
            "matched": evaluate_condition(
                f"{path} {operator} {json.dumps(threshold, ensure_ascii=False)}", value
            )
        }
    if envelope.type == "DECISION_TABLE":
        for row in definition.get("rows", []):
            if not isinstance(row, dict):
                continue
            condition = row.get("when")
            output = row.get("output")
            if (
                isinstance(condition, str)
                and isinstance(output, dict)
                and evaluate_condition(condition, value)
            ):
                return cast(dict[str, Any], render_templates(output, value))
        default = definition.get("default", {})
        return default if isinstance(default, dict) else {}
    return {"valid": True, "requirements": definition.get("requirements", [])}


class DecisionAssetService:
    def __init__(self) -> None:
        self._audit = AuditRepository()

    def validate(self, value: dict[str, Any]) -> DecisionEnvelope:
        envelope = normalize_decision(value)
        failures = [
            test.name
            for test in envelope.tests
            if execute_decision(envelope, test.input) != test.expected
        ]
        if failures:
            raise ValueError(f"DECISION_TEST_FAILED: {','.join(failures)}")
        return envelope

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        name: str,
        purpose: str,
        definition: dict[str, Any],
        actor: str,
    ) -> tuple[RuleSet, RuleSetDraft]:
        envelope = self.validate(definition)
        rule_set = RuleSet(
            tenant_id=tenant_id,
            project_id=project_id,
            name=name,
            purpose=purpose,
        )
        session.add(rule_set)
        await session.flush()
        draft = RuleSetDraft(
            tenant_id=tenant_id,
            project_id=project_id,
            rule_set_id=rule_set.id,
            revision=1,
            rules=envelope.model_dump(mode="json", by_alias=True),
            updated_by=actor,
        )
        session.add(draft)
        await session.flush()
        return rule_set, draft

    async def publish(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        draft_id: UUID,
        actor: str,
    ) -> RuleSetVersion:
        draft = await session.scalar(
            select(RuleSetDraft).where(
                RuleSetDraft.id == draft_id,
                RuleSetDraft.tenant_id == tenant_id,
                RuleSetDraft.project_id == project_id,
            )
        )
        if draft is None:
            raise LookupError("DECISION_ASSET_NOT_FOUND")
        envelope = self.validate(draft.rules)
        normalized = envelope.model_dump(mode="json", by_alias=True)
        digest = canonical_hash(normalized)
        existing = await session.scalar(
            select(RuleSetVersion).where(
                RuleSetVersion.rule_set_id == draft.rule_set_id,
                RuleSetVersion.content_hash == digest,
            )
        )
        if existing is not None:
            return existing
        latest = await session.scalar(
            select(func.max(RuleSetVersion.version)).where(
                RuleSetVersion.rule_set_id == draft.rule_set_id
            )
        )
        version = RuleSetVersion(
            tenant_id=tenant_id,
            project_id=project_id,
            rule_set_id=draft.rule_set_id,
            version=(latest or 0) + 1,
            schema_version=envelope.input_schema,
            match_expression={},
            rules=normalized,
            content_hash=digest,
            status="PUBLISHED",
            created_by=actor,
        )
        session.add(version)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="decision-asset.publish",
            resource_type="decision_version",
            resource_id=str(version.id),
            metadata={"contentHash": digest, "decisionType": envelope.type},
        )
        return version


class DecisionExecutionService:
    async def bind(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        project_capability_binding_id: UUID,
        slot: str,
        rule_set_version_id: UUID,
        actor: str,
    ) -> ProjectCapabilityDecisionBinding:
        pack_binding = await session.scalar(
            select(ProjectCapabilityBinding).where(
                ProjectCapabilityBinding.id == project_capability_binding_id,
                ProjectCapabilityBinding.tenant_id == tenant_id,
                ProjectCapabilityBinding.project_id == project_id,
            )
        )
        version = await session.scalar(
            select(RuleSetVersion).where(
                RuleSetVersion.id == rule_set_version_id,
                RuleSetVersion.tenant_id == tenant_id,
                RuleSetVersion.project_id == project_id,
                RuleSetVersion.status == "PUBLISHED",
            )
        )
        if pack_binding is None:
            raise ValueError("OBJECT_RELATION_SCOPE_MISMATCH")
        if version is None:
            raise ValueError("DECISION_VERSION_NOT_PUBLISHED")
        pack_version = await session.scalar(
            select(CapabilityPackVersion).where(
                CapabilityPackVersion.id == pack_binding.pack_version_id,
                CapabilityPackVersion.tenant_id == tenant_id,
            )
        )
        if pack_version is None:
            raise ValueError("CAPABILITY_PACK_VERSION_NOT_FOUND")
        manifest = CapabilityPackManifest.model_validate(pack_version.manifest)
        slot_contract = next(
            (candidate for candidate in manifest.spec.decisions if candidate.slot == slot), None
        )
        if slot_contract is None:
            raise ValueError("DECISION_SLOT_NOT_DECLARED")
        envelope = normalize_decision(version.rules)
        if (
            envelope.type not in slot_contract.allowed_types
            or envelope.input_schema != slot_contract.input_schema
            or envelope.output_schema != slot_contract.output_schema
        ):
            raise ValueError("DECISION_SCHEMA_MISMATCH")
        binding = await session.scalar(
            select(ProjectCapabilityDecisionBinding).where(
                ProjectCapabilityDecisionBinding.project_capability_binding_id
                == project_capability_binding_id,
                ProjectCapabilityDecisionBinding.slot == slot,
            )
        )
        if binding is None:
            binding = ProjectCapabilityDecisionBinding(
                tenant_id=tenant_id,
                project_id=project_id,
                project_capability_binding_id=project_capability_binding_id,
                slot=slot,
                rule_set_version_id=version.id,
                content_hash=version.content_hash,
                bound_by=actor,
            )
            session.add(binding)
        else:
            binding.rule_set_version_id = version.id
            binding.content_hash = version.content_hash
            binding.bound_by = actor
        await session.flush()
        return binding

    async def freeze(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        evaluation_id: UUID,
        binding: ProjectCapabilityDecisionBinding,
    ) -> EvaluationDecision:
        existing = await session.scalar(
            select(EvaluationDecision).where(
                EvaluationDecision.evaluation_id == evaluation_id,
                EvaluationDecision.slot == binding.slot,
            )
        )
        if existing is not None:
            return existing
        version = await session.get(RuleSetVersion, binding.rule_set_version_id)
        if version is None or version.content_hash != binding.content_hash:
            raise ValueError("DECISION_SCHEMA_MISMATCH")
        envelope = normalize_decision(version.rules)
        frozen = EvaluationDecision(
            tenant_id=tenant_id,
            project_id=project_id,
            evaluation_id=evaluation_id,
            slot=binding.slot,
            rule_set_version_id=version.id,
            decision_content_hash=version.content_hash,
            input_schema_ref=envelope.input_schema,
            output_schema_ref=envelope.output_schema,
            engine=envelope.engine,
        )
        session.add(frozen)
        await session.flush()
        return frozen

    async def record(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        evaluation_decision_id: UUID,
        execution_key: str,
        attempt: int,
        status: str,
        input_value: dict[str, Any],
        output: dict[str, Any] | None,
        matched_rule_ids: list[str],
        duration_ms: int,
        run_id: UUID | None = None,
        task_id: UUID | None = None,
        trace_id: str | None = None,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> tuple[DecisionExecution, bool]:
        existing = await session.scalar(
            select(DecisionExecution).where(
                DecisionExecution.evaluation_decision_id == evaluation_decision_id,
                DecisionExecution.execution_key == execution_key,
                DecisionExecution.attempt == attempt,
            )
        )
        if existing is not None:
            return existing, False
        if duration_ms < 0 or status not in {"SUCCEEDED", "FAILED"}:
            raise ValueError("DECISION_ASSET_INVALID")
        if len(json.dumps(input_value, ensure_ascii=False).encode()) > 256 * 1024 or (
            output is not None
            and len(json.dumps(output, ensure_ascii=False).encode()) > 256 * 1024
        ):
            raise ValueError("DECISION_SNAPSHOT_TOO_LARGE")
        record = DecisionExecution(
            tenant_id=tenant_id,
            project_id=project_id,
            evaluation_decision_id=evaluation_decision_id,
            run_id=run_id,
            task_id=task_id,
            trace_id=trace_id,
            execution_key=execution_key,
            attempt=attempt,
            status=status,
            input_snapshot=input_value,
            input_hash=canonical_hash(input_value),
            output=output,
            output_hash=canonical_hash(output) if output is not None else None,
            matched_rule_ids=matched_rule_ids,
            duration_ms=duration_ms,
            error_code=error_code,
            error_summary=error_summary,
        )
        session.add(record)
        await session.flush()
        return record, True
