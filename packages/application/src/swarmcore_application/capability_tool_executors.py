from __future__ import annotations

import base64
import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository, tenant_transaction
from swarmcore_persistence.models import Evaluation, OutboxEvent
from swarmcore_persistence.repositories import canonical_hash

from .document_intelligence import (
    CrossFileRule,
    DocumentIntelligenceResult,
    evaluate_cross_file_consistency,
    pdf_report_payload,
    render_evidence_pdf,
)
from .integrity import AttachmentInput, IntegrityRuleDocument, evaluate_integrity


async def document_read(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    content = base64.b64decode(str(input_value["contentBase64"]), validate=True)
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("document exceeds the 10 MiB executor limit")
    digest = hashlib.sha256(content).hexdigest()
    if digest != input_value["sha256"]:
        raise ValueError("document sha256 does not match content")
    media_type = str(input_value["mediaType"])
    if media_type == "application/json":
        text = json.dumps(json.loads(content), ensure_ascii=False, sort_keys=True)
    elif media_type == "text/plain":
        text = content.decode("utf-8")
    else:
        raise ValueError(f"unsupported document media type: {media_type}")
    return {
        "documentId": str(input_value["documentId"]),
        "filename": str(input_value["filename"]),
        "mediaType": media_type,
        "sha256": digest,
        "pages": [
            {"page": index, "text": page} for index, page in enumerate(text.split("\f"), start=1)
        ],
    }


async def rules_evaluate(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    result = evaluate_integrity(
        rule_set_version_id=str(input_value["ruleSetVersionId"]),
        document=IntegrityRuleDocument.model_validate(input_value["rules"]),
        attachments=[AttachmentInput.model_validate(item) for item in input_value["attachments"]],
        attachment_manifest_hash=str(input_value["attachmentManifestHash"]),
    )
    return result.model_dump(mode="json", by_alias=True)


async def cross_file_consistency(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    findings = evaluate_cross_file_consistency(
        [DocumentIntelligenceResult.model_validate(item) for item in input_value["results"]],
        [CrossFileRule.model_validate(item) for item in input_value["rules"]],
    )
    return {
        "findings": [item.model_dump(mode="json", by_alias=True) for item in findings],
        "reviewRequired": any(item.requires_review for item in findings),
    }


async def report_render(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    results = [DocumentIntelligenceResult.model_validate(item) for item in input_value["results"]]
    findings = evaluate_cross_file_consistency(
        results,
        [CrossFileRule.model_validate(rule) for rule in input_value.get("rules", [])],
    )
    return pdf_report_payload(render_evidence_pdf(str(input_value["title"]), results, findings))


class EvaluationRecorderExecutor:
    def __init__(self, sessions: async_sessionmaker[Any]) -> None:
        self._sessions = sessions

    async def healthy(self) -> bool:
        try:
            async with self._sessions() as session:
                await session.execute(select(1))
            return True
        except SQLAlchemyError:
            return False

    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result = dict(input_value["result"])
        result_hash = canonical_hash(result)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            evaluation = await session.scalar(
                select(Evaluation)
                .where(
                    Evaluation.id == evaluation_id,
                    Evaluation.tenant_id == tenant_id,
                    Evaluation.project_id == project_id,
                )
                .with_for_update()
            )
            if evaluation is None:
                raise LookupError("evaluation not found in capability scope")
            if evaluation.result is not None:
                if canonical_hash(evaluation.result) != result_hash:
                    raise ValueError("evaluation already contains a different result")
                return self._receipt(evaluation_id, effect_id, result_hash, recorded=False)
            if evaluation.status != "RUNNING":
                raise ValueError(f"evaluation cannot be recorded from {evaluation.status}")
            evaluation.result = result
            evaluation.status = "SUCCEEDED"
            session.add(
                OutboxEvent(
                    id=uuid7(),
                    tenant_id=tenant_id,
                    aggregate_id=evaluation.id,
                    destination="nats",
                    partition_key=str(evaluation.id),
                    source_id=evaluation.id,
                    type="evaluation.succeeded",
                    payload={
                        "evaluationId": str(evaluation.id),
                        "effectId": effect_id,
                        "resultHash": result_hash,
                    },
                )
            )
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=str(context.execution_id),
                action="evaluation.record-result",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={"effectId": effect_id, "resultHash": result_hash},
            )
            return self._receipt(evaluation_id, effect_id, result_hash, recorded=True)

    @staticmethod
    def _receipt(
        evaluation_id: UUID, effect_id: str, result_hash: str, *, recorded: bool
    ) -> dict[str, Any]:
        return {
            "evaluationId": str(evaluation_id),
            "recorded": recorded,
            "effectId": effect_id,
            "resultHash": result_hash,
        }


def capability_executors(sessions: async_sessionmaker[Any]) -> dict[str, Any]:
    return {
        "contract.document_read": document_read,
        "contract.rules_evaluate": rules_evaluate,
        "contract.cross_file_consistency": cross_file_consistency,
        "workbench.record_evaluation": EvaluationRecorderExecutor(sessions),
        "report.render": report_render,
    }
