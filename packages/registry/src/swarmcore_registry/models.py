from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ToolRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentRegistration(FrozenModel):
    ref: str
    version: str
    role: str
    instructions: str
    model: str
    tools: tuple[str, ...] = ()
    input_schema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object"}, alias="inputSchema"
    )
    output_schema: dict[str, Any] | None = Field(default=None, alias="outputSchema")


class ModelRegistration(FrozenModel):
    ref: str
    version: str
    runtime: str
    provider_model: str = Field(alias="providerModel")
    environments: tuple[str, ...]


class ToolRegistration(FrozenModel):
    ref: str
    version: str
    operation: str
    description: str
    risk: ToolRisk
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    output_schema: dict[str, Any] = Field(alias="outputSchema")
    idempotent: bool
    side_effecting: bool = Field(alias="sideEffecting")
    cost_usd: float = Field(default=0.0, alias="costUsd", ge=0)
    recovery_policy: Literal["idempotent", "compensate", "manual"] = Field(alias="recoveryPolicy")
    compensation_operation: str | None = Field(default=None, alias="compensationOperation")

    @model_validator(mode="after")
    def side_effects_require_idempotency(self) -> ToolRegistration:
        if self.side_effecting and self.recovery_policy == "idempotent" and not self.idempotent:
            raise ValueError("idempotent recovery requires the gateway effect id")
        if (self.recovery_policy == "compensate") != (self.compensation_operation is not None):
            raise ValueError("compensate recovery requires exactly one compensation operation")
        return self


class RegistrySnapshot(FrozenModel):
    snapshot_id: str = Field(alias="snapshotId")
    agents: tuple[AgentRegistration, ...] = ()
    models: tuple[ModelRegistration, ...] = ()
    tools: tuple[ToolRegistration, ...] = ()

    def resolve_agent(self, reference: str) -> AgentRegistration | None:
        return self._resolve(reference, self.agents)

    def resolve_model(self, reference: str) -> ModelRegistration | None:
        return self._resolve(reference, self.models)

    def resolve_tool(self, reference: str) -> ToolRegistration | None:
        return self._resolve(reference, self.tools)

    @staticmethod
    def _resolve(reference: str, values: tuple[Any, ...]) -> Any | None:
        exact = next((item for item in values if item.ref == reference), None)
        if exact is not None:
            return exact
        if "@" in reference:
            return None
        candidates = [item for item in values if item.ref.rsplit("@", 1)[0] == reference]
        return candidates[0] if len(candidates) == 1 else None

    @classmethod
    def create(
        cls,
        *,
        agents: tuple[AgentRegistration, ...] = (),
        models: tuple[ModelRegistration, ...] = (),
        tools: tuple[ToolRegistration, ...] = (),
    ) -> RegistrySnapshot:
        payload = {
            "agents": [item.model_dump(mode="json", by_alias=True) for item in agents],
            "models": [item.model_dump(mode="json", by_alias=True) for item in models],
            "tools": [item.model_dump(mode="json", by_alias=True) for item in tools],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode()).hexdigest()[:16]
        return cls(snapshotId=f"registry:{digest}", agents=agents, models=models, tools=tools)


def _object_schema(*, required: tuple[str, ...], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": properties,
        "additionalProperties": False,
    }


_EVIDENCE_SCHEMA = _object_schema(
    required=("page", "text"),
    properties={
        "page": {"type": "integer", "minimum": 1},
        "boundingBox": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 4,
            "maxItems": 4,
        },
        "text": {"type": "string", "minLength": 1},
    },
)

_EXTRACTED_FIELD_SCHEMA = _object_schema(
    required=("name", "value", "confidence", "evidence"),
    properties={
        "name": {"type": "string", "minLength": 1},
        "value": {"type": ["string", "number", "integer", "boolean", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {"type": "array", "minItems": 1, "items": _EVIDENCE_SCHEMA},
    },
)

_CLASSIFICATION_SCHEMA = _object_schema(
    required=("documentType", "confidence", "evidence"),
    properties={
        "documentType": {"type": "string", "minLength": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {"type": "array", "minItems": 1, "items": _EVIDENCE_SCHEMA},
    },
)

_AGENT_EXTRACTION_SCHEMA = _object_schema(
    required=("schemaVersion", "classification", "fields"),
    properties={
        "schemaVersion": {"type": "string", "minLength": 1},
        "classification": _CLASSIFICATION_SCHEMA,
        "fields": {"type": "array", "items": _EXTRACTED_FIELD_SCHEMA},
    },
)

_DIAGNOSTIC_SCHEMA = _object_schema(
    required=("code", "stage", "message", "retryable", "attempts"),
    properties={
        "code": {"type": "string"},
        "stage": {"enum": ["OCR", "CLASSIFICATION", "EXTRACTION", "SCHEMA", "PROVIDER"]},
        "message": {"type": "string"},
        "retryable": {"type": "boolean"},
        "attempts": {"type": "integer", "minimum": 1},
    },
)

_EXTRACTION_RESULT_SCHEMA = _object_schema(
    required=("blobId", "sha256", "pipelineVersion", "status"),
    properties={
        "blobId": {"type": "string", "format": "uuid"},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "pipelineVersion": {"type": "string", "minLength": 1},
        "status": {"enum": ["COMPLETED", "REVIEW_REQUIRED", "FAILED"]},
        "extraction": {"anyOf": [_AGENT_EXTRACTION_SCHEMA, {"type": "null"}]},
        "reviewReasons": {"type": "array", "items": {"type": "string"}},
        "diagnostics": {"type": "array", "items": _DIAGNOSTIC_SCHEMA},
    },
)

_CROSS_FILE_RULE_SCHEMA = _object_schema(
    required=("key", "field", "documentTypes"),
    properties={
        "key": {"type": "string", "minLength": 1},
        "field": {"type": "string", "minLength": 1},
        "documentTypes": {
            "type": "array",
            "minItems": 2,
            "items": {"type": "string"},
        },
        "severity": {"enum": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]},
    },
)

_CROSS_FILE_FINDING_SCHEMA = _object_schema(
    required=("ruleKey", "code", "severity", "detail", "evidence", "requiresReview"),
    properties={
        "ruleKey": {"type": "string"},
        "code": {"type": "string"},
        "severity": {"type": "string"},
        "detail": {"type": "string"},
        "evidence": {"type": "array", "items": _EVIDENCE_SCHEMA},
        "requiresReview": {"type": "boolean"},
    },
)

_DOCUMENT_REQUIREMENT_SCHEMA = _object_schema(
    required=("key", "documentType"),
    properties={
        "key": {"type": "string", "minLength": 1},
        "documentType": {"type": "string", "minLength": 1},
        "required": {"type": "boolean"},
        "minCount": {"type": "integer", "minimum": 0},
        "maxCount": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
        "mediaTypes": {"type": "array", "items": {"type": "string"}},
        "allowDuplicates": {"type": "boolean"},
        "minimumVersion": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
        "requireUnexpired": {"type": "boolean"},
        "severity": {"enum": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]},
    },
)

_RULE_DOCUMENT_SCHEMA = _object_schema(
    required=("schemaVersion", "match", "requirements"),
    properties={
        "schemaVersion": {"const": "schema://contract/checklist-rule@1"},
        "match": {"type": "object", "additionalProperties": {"type": "string"}},
        "requirements": {"type": "array", "items": _DOCUMENT_REQUIREMENT_SCHEMA},
    },
)

_ATTACHMENT_SCHEMA = _object_schema(
    required=("attachmentId", "blobId", "documentType", "filename", "mediaType", "sha256"),
    properties={
        "attachmentId": {"type": "string"},
        "blobId": {"type": "string"},
        "documentType": {"type": "string"},
        "filename": {"type": "string"},
        "mediaType": {"type": "string"},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "version": {"type": "integer", "minimum": 1},
        "readable": {"type": "boolean"},
        "expiresAt": {"anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]},
    },
)

_INTEGRITY_FINDING_SCHEMA = _object_schema(
    required=("ruleKey", "code", "category", "severity", "title", "detail", "evidence"),
    properties={
        "ruleKey": {"type": "string"},
        "code": {"type": "string"},
        "category": {"type": "string"},
        "severity": {"type": "string"},
        "title": {"type": "string"},
        "detail": {"type": "string"},
        "evidence": {"type": "object"},
    },
)

_INTEGRITY_RESULT_SCHEMA = _object_schema(
    required=("passed", "ruleSetVersionId", "attachmentManifestHash", "checks", "findings"),
    properties={
        "passed": {"type": "boolean"},
        "ruleSetVersionId": {"type": "string"},
        "attachmentManifestHash": {"type": "string"},
        "checks": {"type": "object", "additionalProperties": {"type": "integer"}},
        "findings": {"type": "array", "items": _INTEGRITY_FINDING_SCHEMA},
    },
)

_POST_EVALUATION_DIMENSION_SCHEMA = _object_schema(
    required=(
        "code",
        "name",
        "weight",
        "score",
        "status",
        "summary",
        "metrics",
        "evidenceRefs",
    ),
    properties={
        "code": {
            "enum": [
                "DOCUMENT_COMPLETENESS",
                "DELIVERY_TIMELINESS",
                "DELIVERY_QUALITY",
                "COST_CONTROL",
                "INVOICE_COMPLIANCE",
                "DEVIATION_GOVERNANCE",
                "RISK_GOVERNANCE",
            ]
        },
        "name": {"type": "string", "minLength": 1},
        "weight": {"type": "integer", "minimum": 0, "maximum": 100},
        "score": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
        "status": {"enum": ["EVALUATED", "DATA_INSUFFICIENT"]},
        "summary": {"type": "string", "minLength": 1},
        "metrics": {"type": "object"},
        "evidenceRefs": {"type": "array", "items": {"type": "string"}},
    },
)

_POST_EVALUATION_FINDING_SCHEMA = _object_schema(
    required=("dimension", "severity", "code", "title", "detail", "evidenceRefs"),
    properties={
        "dimension": {"type": "string", "minLength": 1},
        "severity": {"enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "code": {"enum": ["DATA_INSUFFICIENT", "DIMENSION_BELOW_TARGET"]},
        "title": {"type": "string", "minLength": 1},
        "detail": {"type": "string", "minLength": 1},
        "evidenceRefs": {"type": "array", "items": {"type": "string"}},
    },
)

_POST_EVALUATION_RESULT_SCHEMA = _object_schema(
    required=(
        "schemaVersion",
        "evaluationPeriod",
        "contractId",
        "overallScore",
        "grade",
        "riskLevel",
        "passed",
        "reviewRequired",
        "executiveSummary",
        "dimensions",
        "findings",
    ),
    properties={
        "schemaVersion": {"const": "schema://contract/post-evaluation-result@1"},
        "evaluationPeriod": _object_schema(
            required=("start", "end"),
            properties={
                "start": {"type": "string", "format": "date"},
                "end": {"type": "string", "format": "date"},
            },
        ),
        "contractId": {"type": "string", "minLength": 1},
        "overallScore": {"type": "number", "minimum": 0, "maximum": 100},
        "grade": {"type": "string", "minLength": 1},
        "riskLevel": {"enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "passed": {"type": "boolean"},
        "reviewRequired": {"type": "boolean"},
        "executiveSummary": {"type": "string", "minLength": 1},
        "dimensions": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": _POST_EVALUATION_DIMENSION_SCHEMA,
        },
        "findings": {"type": "array", "items": _POST_EVALUATION_FINDING_SCHEMA},
    },
)

_PDF_REPORT_SCHEMA = _object_schema(
    required=("mediaType", "sha256", "contentBase64"),
    properties={
        "mediaType": {"const": "application/pdf"},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "contentBase64": {"type": "string", "minLength": 1},
    },
)

_BOUND_RESOURCE_SCHEMA = _object_schema(
    required=(
        "slot",
        "resourceId",
        "connectionVersionId",
        "connectorRef",
        "accessMode",
        "mappingConfiguration",
    ),
    properties={
        "slot": {"type": "string", "minLength": 1},
        "resourceId": {"type": "string", "format": "uuid"},
        "connectionVersionId": {"type": "string", "format": "uuid"},
        "connectorRef": {"type": "string", "minLength": 1},
        "accessMode": {"enum": ["READ", "WRITE", "READ_WRITE"]},
        "mappingConfiguration": {"type": "object"},
    },
)

_BOUND_RESOURCE_RESULT_SCHEMA = _object_schema(
    required=("slot", "resourceId", "connectionVersionId", "contentHash", "data"),
    properties={
        "slot": {"type": "string", "minLength": 1},
        "resourceId": {"type": "string", "format": "uuid"},
        "connectionVersionId": {"type": "string", "format": "uuid"},
        "contentHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "data": {"type": "object"},
    },
)

_BOUND_DOCUMENT_SCHEMA = _object_schema(
    required=(
        "documentId",
        "documentVersionId",
        "blobId",
        "name",
        "category",
        "filename",
        "mediaType",
        "sizeBytes",
        "sha256",
        "version",
    ),
    properties={
        "documentId": {"type": "string", "format": "uuid"},
        "documentVersionId": {"type": "string", "format": "uuid"},
        "blobId": {"type": "string", "format": "uuid"},
        "name": {"type": "string", "minLength": 1},
        "category": {"type": "string", "minLength": 1},
        "filename": {"type": "string", "minLength": 1},
        "mediaType": {"type": "string", "minLength": 1},
        "sizeBytes": {"type": "integer", "minimum": 1},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "version": {"type": "integer", "minimum": 1},
    },
)

_BOUND_DOCUMENT_RESULT_SCHEMA = _object_schema(
    required=("contentHash", "documents", "effectId"),
    properties={
        "contentHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "documents": {"type": "array", "items": {"type": "object"}},
        "effectId": {"type": "string", "minLength": 1},
    },
)

_POST_EVALUATION_PAYLOAD_SCHEMA = _object_schema(
    required=(
        "title",
        "evaluationPeriod",
        "contract",
        "documents",
        "obligations",
        "deviations",
        "invoices",
        "risks",
    ),
    properties={
        "title": {"type": "string", "minLength": 1},
        "evaluationPeriod": {"type": "object"},
        "contract": {"type": "object"},
        "documents": {"type": "array", "items": {"type": "object"}},
        "obligations": {"type": "array", "items": {"type": "object"}},
        "deviations": {"type": "array", "items": {"type": "object"}},
        "invoices": {"type": "array", "items": {"type": "object"}},
        "risks": {"type": "array", "items": {"type": "object"}},
        "evidenceAvailability": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
)

_EVIDENCE_FACT_SCHEMA_V1 = _object_schema(
    required=("factId", "factType", "value", "confidence", "evidenceRefs"),
    properties={
        "factId": {"type": "string", "minLength": 1},
        "factType": {"type": "string", "minLength": 1},
        "value": {},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidenceRefs": {"type": "array", "items": {"type": "string", "minLength": 1}},
    },
)

_DOMAIN_ANALYSIS_SCHEMA_V1 = _object_schema(
    required=("domain", "payloadPatch", "facts", "conflicts", "missingEvidence"),
    properties={
        "domain": {"enum": ["contract", "performance", "finance", "governance"]},
        "payloadPatch": {"type": "object"},
        "facts": {"type": "array", "items": _EVIDENCE_FACT_SCHEMA_V1},
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "missingEvidence": {"type": "array", "items": {"type": "string"}},
    },
)

_EVIDENCE_FACT_SCHEMA = _object_schema(
    required=("factId", "factType", "value", "confidence", "evidenceRefs"),
    properties={
        "factId": {"type": "string", "minLength": 1},
        "factType": {"type": "string", "minLength": 1},
        "value": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidenceRefs": {"type": "array", "items": {"type": "string", "minLength": 1}},
    },
)

_DOMAIN_ANALYSIS_SCHEMA = _object_schema(
    required=("domain", "payloadPatch", "facts", "conflicts", "missingEvidence"),
    properties={
        "domain": {
            "type": "string",
            "enum": ["contract", "performance", "finance", "governance"],
        },
        "payloadPatch": {"type": "object"},
        "facts": {"type": "array", "items": _EVIDENCE_FACT_SCHEMA},
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "missingEvidence": {"type": "array", "items": {"type": "string"}},
    },
)

_EVIDENCE_REVIEW_SCHEMA = _object_schema(
    required=("reviewRequired", "reasons", "acceptedFactIds", "rejectedFactIds"),
    properties={
        "reviewRequired": {"type": "boolean"},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "acceptedFactIds": {"type": "array", "items": {"type": "string"}},
        "rejectedFactIds": {"type": "array", "items": {"type": "string"}},
    },
)

_REPORT_NARRATIVE_SCHEMA = _object_schema(
    required=("executiveSummary", "dimensionNarratives", "recommendations"),
    properties={
        "executiveSummary": {"type": "string", "minLength": 1},
        "dimensionNarratives": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "managementConclusions": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
)

_REPORT_SECTION_DRAFT_SCHEMA = _object_schema(
    required=(
        "title",
        "summary",
        "dimensionNarratives",
        "recommendations",
        "evidenceRefs",
    ),
    properties={
        "title": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
        "dimensionNarratives": {
            "type": "object",
            "additionalProperties": {"type": "string", "minLength": 1},
        },
        "recommendations": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "evidenceRefs": {"type": "array", "items": {"type": "string", "minLength": 1}},
    },
)

_FORMAL_EDITORIAL_SCHEMA = _object_schema(
    required=(
        "executiveSummary",
        "dimensionNarratives",
        "recommendations",
        "managementConclusions",
        "limitations",
    ),
    properties={
        "executiveSummary": {"type": "string", "minLength": 1},
        "dimensionNarratives": {
            "type": "object",
            "additionalProperties": {"type": "string", "minLength": 1},
        },
        "recommendations": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "managementConclusions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "limitations": {"type": "array", "items": {"type": "string", "minLength": 1}},
    },
)

_REPORT_MODEL_REVIEW_SCHEMA = _object_schema(
    required=("passed", "issues"),
    properties={
        "passed": {"type": "boolean"},
        "issues": {
            "type": "array",
            "items": _object_schema(
                required=("severity", "section", "detail"),
                properties={
                    "severity": {
                        "enum": ["INFO", "WARNING", "BLOCKING", "CRITICAL"]
                    },
                    "section": {"type": "string", "minLength": 1},
                    "detail": {"type": "string", "minLength": 1},
                },
            ),
        },
    },
)

_READABILITY_GATE_SCHEMA = _object_schema(
    required=(
        "documentCount",
        "readableDocumentCount",
        "readabilityRate",
        "formalThreshold",
        "formalEligible",
        "reportMode",
        "reasons",
    ),
    properties={
        "documentCount": {"type": "integer", "minimum": 0},
        "readableDocumentCount": {"type": "integer", "minimum": 0},
        "readabilityRate": {"type": "number", "minimum": 0, "maximum": 1},
        "formalThreshold": {"type": "number", "minimum": 0, "maximum": 1},
        "formalEligible": {"type": "boolean"},
        "reportMode": {"enum": ["FORMAL_REPORT", "PRE_REVIEW_REPORT"]},
        "reasons": {"type": "array", "items": {"type": "string"}},
    },
)

_FORMAL_REPORT_DOCUMENT_SCHEMA = _object_schema(
    required=(
        "schemaVersion",
        "title",
        "reportNumber",
        "version",
        "reportMode",
        "formalEligible",
        "contractProfile",
        "managementSummary",
        "methodology",
        "dimensionOverview",
        "dimensionSections",
        "timeline",
        "financialAnalysis",
        "invoiceAnalysis",
        "deviationAndRisk",
        "evidenceAndLimitations",
        "remediationPlan",
        "approval",
        "provenance",
    ),
    properties={
        "schemaVersion": {
            "const": "schema://report/contract-post-evaluation-document@1"
        },
        "title": {"type": "string", "minLength": 1},
        "reportNumber": {"type": "string", "minLength": 1},
        "version": {"type": "string", "minLength": 1},
        "reportMode": {"enum": ["FORMAL_REPORT", "PRE_REVIEW_REPORT"]},
        "formalEligible": {"type": "boolean"},
        "contractProfile": {"type": "object"},
        "managementSummary": {"type": "object"},
        "methodology": {"type": "object"},
        "dimensionOverview": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {"type": "object"},
        },
        "dimensionSections": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {"type": "object"},
        },
        "timeline": {"type": "array", "items": {"type": "object"}},
        "financialAnalysis": {"type": "object"},
        "invoiceAnalysis": {"type": "object"},
        "deviationAndRisk": {"type": "object"},
        "evidenceAndLimitations": {"type": "object"},
        "remediationPlan": {"type": "array", "items": {"type": "object"}},
        "approval": {"type": "object"},
        "provenance": {"type": "object"},
    },
)

_CITATION_CHECK_SCHEMA = _object_schema(
    required=(
        "passed",
        "indexedEvidenceCount",
        "citedEvidenceCount",
        "unknownCitationCodes",
        "dimensionsWithoutCitations",
        "scoreMismatches",
    ),
    properties={
        "passed": {"type": "boolean"},
        "indexedEvidenceCount": {"type": "integer", "minimum": 0},
        "citedEvidenceCount": {"type": "integer", "minimum": 0},
        "unknownCitationCodes": {"type": "array", "items": {"type": "string"}},
        "dimensionsWithoutCitations": {"type": "array", "items": {"type": "string"}},
        "scoreMismatches": {"type": "array", "items": {"type": "string"}},
    },
)

_REPORT_QUALITY_SCHEMA = _object_schema(
    required=("passed", "blockingIssues", "warnings", "checks"),
    properties={
        "passed": {"type": "boolean"},
        "blockingIssues": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "checks": {"type": "object"},
    },
)

_EVIDENCE_SEARCH_RESULT_SCHEMA = _object_schema(
    required=(
        "domain",
        "searchedDocuments",
        "contentAvailableDocuments",
        "hits",
        "contentHash",
    ),
    properties={
        "domain": {"enum": ["contract", "performance", "finance", "governance"]},
        "searchedDocuments": {"type": "integer", "minimum": 0},
        "contentAvailableDocuments": {"type": "integer", "minimum": 0},
        "hits": {"type": "array", "items": {"type": "object"}},
        "contentHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
)

_COVERAGE_RESULT_SCHEMA = _object_schema(
    required=(
        "complete",
        "reviewRequired",
        "documentCount",
        "contentAvailableCount",
        "requirements",
        "missingRequired",
        "unreadableDocumentVersionIds",
        "duplicateSha256",
        "warnings",
    ),
    properties={
        "complete": {"type": "boolean"},
        "reviewRequired": {"type": "boolean"},
        "documentCount": {"type": "integer", "minimum": 0},
        "contentAvailableCount": {"type": "integer", "minimum": 0},
        "requirements": {"type": "array", "items": {"type": "object"}},
        "missingRequired": {"type": "array", "items": {"type": "string"}},
        "unreadableDocumentVersionIds": {
            "type": "array",
            "items": {"type": "string"},
        },
        "duplicateSha256": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
)

_MERGED_DOMAIN_SCHEMA = _object_schema(
    required=("payload", "evidenceFacts", "conflicts", "missingEvidence", "sourceAgents"),
    properties={
        "payload": _POST_EVALUATION_PAYLOAD_SCHEMA,
        "evidenceFacts": {"type": "array", "items": _EVIDENCE_FACT_SCHEMA},
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "missingEvidence": {"type": "array", "items": {"type": "string"}},
        "sourceAgents": {"type": "array", "items": {"type": "string"}},
    },
)

_CONSISTENCY_RESULT_SCHEMA = _object_schema(
    required=(
        "reviewRequired",
        "conflicts",
        "warnings",
        "unsupportedFactIds",
        "lowConfidenceFactIds",
        "duplicateIds",
        "checkedFactCount",
    ),
    properties={
        "reviewRequired": {"type": "boolean"},
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "unsupportedFactIds": {"type": "array", "items": {"type": "string"}},
        "lowConfidenceFactIds": {"type": "array", "items": {"type": "string"}},
        "duplicateIds": {"type": "object"},
        "checkedFactCount": {"type": "integer", "minimum": 0},
    },
)

_POST_EVALUATION_RESULT_V2_SCHEMA = _object_schema(
    required=(
        "schemaVersion",
        "evaluationPeriod",
        "contractId",
        "overallScore",
        "grade",
        "riskLevel",
        "passed",
        "reviewRequired",
        "executiveSummary",
        "dimensions",
        "findings",
        "evidenceSummary",
        "review",
        "narrative",
        "diagnostics",
        "provenance",
    ),
    properties={
        **_POST_EVALUATION_RESULT_SCHEMA["properties"],
        "schemaVersion": {"const": "schema://contract/post-evaluation-result@2"},
        "evidenceSummary": {"type": "object"},
        "review": {"type": "object"},
        "narrative": {"type": "object"},
        "diagnostics": {"type": "object"},
        "provenance": {"type": "object"},
    },
)

_POST_EVALUATION_RESULT_V3_SCHEMA = _object_schema(
    required=(
        *_POST_EVALUATION_RESULT_V2_SCHEMA["required"],
        "readabilityGate",
        "reportDocument",
        "reportQuality",
    ),
    properties={
        **_POST_EVALUATION_RESULT_V2_SCHEMA["properties"],
        "schemaVersion": {"const": "schema://contract/post-evaluation-result@3"},
        "readabilityGate": _READABILITY_GATE_SCHEMA,
        "reportDocument": _FORMAL_REPORT_DOCUMENT_SCHEMA,
        "reportQuality": _REPORT_QUALITY_SCHEMA,
    },
)

_DEVIATION_FACT_ANALYSIS_SCHEMA = _object_schema(
    required=("payloadPatch", "facts", "conflicts", "missingEvidence"),
    properties={
        "payloadPatch": {"type": "object"},
        "facts": {"type": "array", "items": {"type": "object"}},
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "missingEvidence": {"type": "array", "items": {"type": "string"}},
    },
)

_DEVIATION_ROOT_CAUSE_SCHEMA = _object_schema(
    required=("rootCauses",),
    properties={
        "rootCauses": {
            "type": "array",
            "items": _object_schema(
                required=(
                    "causeId",
                    "title",
                    "hypothesis",
                    "impact",
                    "confidence",
                    "evidenceRefs",
                ),
                properties={
                    "causeId": {"type": "string", "minLength": 1},
                    "title": {"type": "string", "minLength": 1},
                    "hypothesis": {"type": "string", "minLength": 1},
                    "impact": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidenceRefs": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            ),
        }
    },
)

_DEVIATION_RESPONSIBILITY_SCHEMA = _object_schema(
    required=("proposals",),
    properties={
        "proposals": {
            "type": "array",
            "items": _object_schema(
                required=(
                    "proposalId",
                    "party",
                    "scope",
                    "rationale",
                    "confidence",
                    "evidenceRefs",
                ),
                properties={
                    "proposalId": {"type": "string", "minLength": 1},
                    "party": {"type": "string", "minLength": 1},
                    "scope": {"type": "string", "minLength": 1},
                    "rationale": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidenceRefs": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            ),
        }
    },
)

_DEVIATION_REVIEW_SCHEMA = _object_schema(
    required=("reviewRequired", "reasons"),
    properties={
        "reviewRequired": {"type": "boolean"},
        "reasons": {"type": "array", "items": {"type": "string"}},
    },
)

_DEVIATION_NARRATIVE_SCHEMA = _object_schema(
    required=("executiveSummary", "dimensionNarratives", "recommendations"),
    properties={
        "executiveSummary": {"type": "string", "minLength": 1},
        "dimensionNarratives": {"type": "object"},
        "recommendations": {"type": "array", "items": {"type": "string"}},
    },
)

_DEVIATION_RESULT_SCHEMA = {
    "type": "object",
    "required": [
        "schemaVersion",
        "qualityStatus",
        "reviewRequired",
        "dimensions",
        "responsibility",
        "provenance",
    ],
    "properties": {
        "schemaVersion": {"const": "schema://deviation-analysis/result@1"},
        "qualityStatus": {"enum": ["READY", "REVIEW_REQUIRED", "BLOCKED"]},
        "reviewRequired": {"type": "boolean"},
        "dimensions": {"type": "object"},
        "responsibility": {"type": "object"},
        "provenance": {"type": "object"},
    },
}

_INVOICE_FACT_SET_SCHEMA = {"type": "object"}

_INVOICE_NORMALIZER_SCHEMA = _object_schema(
    required=("invoiceFactSet",),
    properties={
        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
        "qualityFlags": {"type": "array", "items": {"type": "object"}},
        "evidenceFacts": {"type": "array", "items": {"type": "object"}},
        "conflicts": {"type": "array", "items": {"type": "string"}},
    },
)

_INVOICE_MATCH_CANDIDATE_SCHEMA = _object_schema(
    required=("matchCandidates",),
    properties={
        "matchCandidates": {"type": "array", "items": {"type": "object"}},
        "ambiguities": {"type": "array", "items": {"type": "object"}},
        "missingEvidence": {"type": "array", "items": {"type": "string"}},
    },
)

_INVOICE_REVIEW_SCHEMA = _object_schema(
    required=("reviewRequired", "narrative"),
    properties={
        "reviewRequired": {"type": "boolean"},
        "narrative": {
            "type": "object",
            "required": ("executiveSummary",),
            "properties": {
                "executiveSummary": {"type": "string", "minLength": 1},
                "riskSummary": {"type": "string"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
        },
        "conflicts": {"type": "array", "items": {"type": "string"}},
        "unsupportedConclusions": {"type": "array", "items": {"type": "string"}},
        "outcomeHint": {
            "enum": ["PAYMENT_READY", "REVIEW_REQUIRED", "PAYMENT_BLOCKED", "UNKNOWN"]
        },
    },
)

_INVOICE_ASSURANCE_RESULT_SCHEMA = {
    "type": "object",
    "required": [
        "schemaVersion",
        "outcome",
        "reviewRequired",
        "dimensions",
        "provenance",
    ],
    "properties": {
        "schemaVersion": {"const": "schema://invoice-assurance/result@1"},
        "outcome": {"enum": ["PAYMENT_READY", "REVIEW_REQUIRED", "PAYMENT_BLOCKED"]},
        "reviewRequired": {"type": "boolean"},
        "dimensions": {"type": "object"},
        "findings": {"type": "array", "items": {"type": "object"}},
        "provenance": {"type": "object"},
        "resultHash": {"type": "string"},
    },
}


def builtin_registry() -> RegistrySnapshot:
    return RegistrySnapshot.create(
        agents=(
            AgentRegistration(
                ref="agent://builtin/researcher@1",
                version="1",
                role="researcher",
                instructions=(
                    "Research the requested topic with the controlled search tool. Prioritize "
                    "authoritative and recent sources, separate verified facts from inference, "
                    "cite the supporting source for every material claim, and return concise "
                    "structured findings in the requested language."
                ),
                model="model://general@1",
                tools=("tool://search@1",),
                inputSchema=_object_schema(
                    required=("topic",),
                    properties={
                        "topic": {"type": "string", "title": "研究主题", "minLength": 1},
                        "objective": {
                            "type": "string",
                            "title": "研究目标",
                            "default": "形成包含关键结论、证据来源和待确认事项的研究摘要",
                        },
                        "language": {
                            "type": "string",
                            "title": "输出语言",
                            "default": "简体中文",
                        },
                        "maxSources": {
                            "type": "integer",
                            "title": "最多参考来源数",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 8,
                        },
                    },
                ),
            ),
            AgentRegistration(
                ref="agent://contract/document-classifier@1",
                version="1",
                role="contract-document-classifier",
                instructions=(
                    "Classify the supplied contract text using the requested candidate types. "
                    "Base the decision only on document evidence, preserve the most relevant "
                    "page or text excerpts, lower confidence when evidence is ambiguous, and "
                    "return output that exactly matches the declared schema."
                ),
                model="model://general@1",
                tools=("tool://document/read@1",),
                inputSchema=_object_schema(
                    required=("documentText",),
                    properties={
                        "documentText": {
                            "type": "string",
                            "title": "合同文本",
                            "minLength": 1,
                        },
                        "documentName": {
                            "type": "string",
                            "title": "文档名称",
                            "default": "待分类合同",
                        },
                        "candidateTypes": {
                            "type": "string",
                            "title": "候选类型(逗号分隔)",
                            "default": "主合同,补充协议,附件,往来函件,其他",
                        },
                        "language": {
                            "type": "string",
                            "title": "输出语言",
                            "default": "简体中文",
                        },
                    },
                ),
                outputSchema=_CLASSIFICATION_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/field-extractor@1",
                version="1",
                role="contract-field-extractor",
                instructions=(
                    "Extract only the requested fields from the supplied contract text. Never "
                    "invent missing values; attach page-level or text evidence and a calibrated "
                    "confidence score to every extracted value, and return output that exactly "
                    "matches the declared schema."
                ),
                model="model://general@1",
                tools=("tool://document/read@1",),
                inputSchema=_object_schema(
                    required=("documentText",),
                    properties={
                        "documentText": {
                            "type": "string",
                            "title": "合同文本",
                            "minLength": 1,
                        },
                        "requestedFields": {
                            "type": "string",
                            "title": "提取字段(逗号分隔)",
                            "default": "合同编号,合同主体,生效日期,到期日期,合同金额,付款条件",
                        },
                        "minimumConfidence": {
                            "type": "number",
                            "title": "最低置信度",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.8,
                        },
                        "language": {
                            "type": "string",
                            "title": "输出语言",
                            "default": "简体中文",
                        },
                    },
                ),
                outputSchema=_AGENT_EXTRACTION_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/post-evaluation-analyst@1",
                version="1",
                role="contract-post-evaluation-analyst",
                instructions=(
                    "Read every supplied file and the user-defined workflow, then produce one "
                    "normalized contract post-evaluation payload. Extract contract facts, required "
                    "documents, delivery obligations, deviations, invoices, and risks only from "
                    "the supplied evidence. Apply the user's workflow when deciding which evidence "
                    "is relevant. Preserve the supplied fallback identifiers and evaluation period "
                    "when the files do not contain them. Use empty arrays for genuinely absent "
                    "categories, use null for an unavailable actual cost, and return output that "
                    "exactly matches the declared schema."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("workflow", "basePayload", "uploadedFiles"),
                    properties={
                        "workflow": {"type": "string", "minLength": 1},
                        "basePayload": {"type": "object"},
                        "uploadedFiles": {"type": "object"},
                    },
                ),
                outputSchema=_POST_EVALUATION_PAYLOAD_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/baseline-analyst@1",
                version="1",
                role="contract-baseline-analyst",
                instructions=(
                    "Analyze only contract-baseline evidence: primary contracts, amendments, "
                    "procurement commitments, parties, amount, period, and required documents. "
                    "Return domain='contract'. Put normalized contract/documents fields in "
                    "payloadPatch. Every material fact must include immutable document-version "
                    "evidence references; never invent missing values. Report contradictions and "
                    "missing evidence explicitly and match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA_V1,
            ),
            AgentRegistration(
                ref="agent://contract/performance-quality-analyst@1",
                version="1",
                role="contract-performance-quality-analyst",
                instructions=(
                    "Analyze only delivery, milestone, acceptance, timeliness, and quality "
                    "evidence. Return domain='performance' and normalized obligations in "
                    "payloadPatch. Preserve fallback identifiers only when evidence does not "
                    "supply them. Cite immutable document-version evidence for each fact, surface "
                    "conflicts and missing evidence, and match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA_V1,
            ),
            AgentRegistration(
                ref="agent://contract/finance-invoice-analyst@1",
                version="1",
                role="contract-finance-invoice-analyst",
                instructions=(
                    "Analyze only contract amount, amendments, actual cost, invoices, tax and "
                    "payment evidence. Return domain='finance'; place contract updates and "
                    "normalized invoices in payloadPatch. Never treat missing finance records as "
                    "zero. Cite immutable document-version evidence for every material fact, "
                    "report conflicts and gaps, and match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA_V1,
            ),
            AgentRegistration(
                ref="agent://contract/deviation-risk-analyst@1",
                version="1",
                role="contract-deviation-risk-analyst",
                instructions=(
                    "Analyze only deviations, changes, remediation, supplier and risk evidence. "
                    "Return domain='governance' with normalized deviations and risks in "
                    "payloadPatch. Distinguish 'no registered record' from 'records unavailable'. "
                    "Cite immutable document-version evidence for each fact, surface conflicts "
                    "and missing evidence, and match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA_V1,
            ),
            AgentRegistration(
                ref="agent://contract/baseline-analyst@2",
                version="2",
                role="contract-baseline-analyst",
                instructions=(
                    "Analyze only contract-baseline evidence: contracts, amendments, procurement "
                    "commitments, parties, amount, period, and required documents. Return "
                    "domain='contract'. Put normalized contract/documents fields in payloadPatch. "
                    "Every fact value must be a string and must cite immutable document-version "
                    "evidence. Never invent values; report conflicts and missing evidence."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/performance-quality-analyst@2",
                version="2",
                role="contract-performance-quality-analyst",
                instructions=(
                    "Analyze only delivery, milestone, acceptance, timeliness, and quality "
                    "evidence. Return domain='performance' and normalized obligations in "
                    "payloadPatch. Every fact value must be a string and cite immutable "
                    "document-version evidence. Surface conflicts and missing evidence."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/finance-invoice-analyst@2",
                version="2",
                role="contract-finance-invoice-analyst",
                instructions=(
                    "Analyze only contract amount, amendments, actual cost, invoices, tax and "
                    "payment evidence. Return domain='finance'; place normalized contract updates "
                    "and invoices in payloadPatch. Every fact value must be a string and cite "
                    "immutable document-version evidence. Missing records are not zero."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/deviation-risk-analyst@2",
                version="2",
                role="contract-deviation-risk-analyst",
                instructions=(
                    "Analyze only deviations, changes, remediation, supplier and risk evidence. "
                    "Return domain='governance' with normalized deviations and risks in "
                    "payloadPatch. Every fact value must be a string and cite immutable "
                    "document-version evidence. Distinguish no record from unavailable records."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "evidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_DOMAIN_ANALYSIS_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/evidence-reviewer@1",
                version="1",
                role="contract-evidence-reviewer",
                instructions=(
                    "Review the deterministic coverage, consistency, timeline, finance, invoice, "
                    "deviation and risk diagnostics. Require human review for unresolved material "
                    "conflicts, unreadable required documents, missing required evidence, or "
                    "low-confidence material facts. Do not change extracted facts or scores. "
                    "Return accepted/rejected fact identifiers and concise reasons using exactly "
                    "the declared schema."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("coverage", "consistency", "diagnostics", "facts"),
                    properties={
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "consistency": _CONSISTENCY_RESULT_SCHEMA,
                        "diagnostics": {"type": "object"},
                        "facts": {"type": "array", "items": _EVIDENCE_FACT_SCHEMA},
                    },
                ),
                outputSchema=_EVIDENCE_REVIEW_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/report-narrator@1",
                version="1",
                role="contract-post-evaluation-report-narrator",
                instructions=(
                    "Explain the frozen deterministic seven-dimension result in concise Chinese. "
                    "Do not alter scores, grades, risk level, findings, or evidence. Provide one "
                    "executive summary, narratives keyed by dimension code, and actionable "
                    "recommendations. Match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("result", "review", "diagnostics"),
                    properties={
                        "result": _POST_EVALUATION_RESULT_SCHEMA,
                        "review": _EVIDENCE_REVIEW_SCHEMA,
                        "diagnostics": {"type": "object"},
                    },
                ),
                outputSchema=_REPORT_NARRATIVE_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/performance-report-writer@1",
                version="1",
                role="contract-performance-report-writer",
                instructions=(
                    "Write the Chinese business-report sections for document completeness, "
                    "delivery timeliness and delivery quality. Use only the frozen score, "
                    "diagnostics and cited evidence. Explain management impact, evidence "
                    "limitations and concrete remediation without changing any score, grade, "
                    "risk level or evidence identifier. Match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("result", "diagnostics", "readability"),
                    properties={
                        "result": _POST_EVALUATION_RESULT_SCHEMA,
                        "diagnostics": {"type": "object"},
                        "readability": _READABILITY_GATE_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_REPORT_SECTION_DRAFT_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/governance-report-writer@1",
                version="1",
                role="contract-governance-report-writer",
                instructions=(
                    "Write the Chinese business-report sections for cost, invoice, deviation "
                    "and risk governance. Use only frozen deterministic results and cited "
                    "evidence. Distinguish verified facts, conflicts and data limitations. "
                    "Produce actionable remediation without changing scores or evidence. "
                    "Match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("result", "diagnostics", "readability"),
                    properties={
                        "result": _POST_EVALUATION_RESULT_SCHEMA,
                        "diagnostics": {"type": "object"},
                        "readability": _READABILITY_GATE_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_REPORT_SECTION_DRAFT_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/report-narrator@2",
                version="2",
                role="contract-post-evaluation-executive-editor",
                instructions=(
                    "Act as the executive editor for a formal Chinese contract post-evaluation "
                    "report. Reconcile the two section drafts with the frozen seven-dimension "
                    "result, evidence review, diagnostics and readability gate. Produce a "
                    "decision-oriented executive summary, narratives for all seven dimension "
                    "codes, prioritized recommendations, management conclusions and explicit "
                    "limitations. Never alter scores, grades, risk level or evidence. Do not "
                    "expose internal tool, agent or schema identifiers. Match the schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=(
                        "result",
                        "review",
                        "diagnostics",
                        "sectionDrafts",
                        "readability",
                    ),
                    properties={
                        "result": _POST_EVALUATION_RESULT_SCHEMA,
                        "review": _EVIDENCE_REVIEW_SCHEMA,
                        "diagnostics": {"type": "object"},
                        "sectionDrafts": {"type": "object"},
                        "readability": _READABILITY_GATE_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_FORMAL_EDITORIAL_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://contract/report-quality-reviewer@1",
                version="1",
                role="contract-post-evaluation-report-quality-reviewer",
                instructions=(
                    "Review the composed formal report against the frozen result, citation "
                    "check and readability gate. Flag only concrete omissions, contradictions, "
                    "unsupported claims, internal identifiers or unsuitable formal-report "
                    "language. Do not rewrite the report and do not change scores. A pre-review "
                    "report may pass when its data-quality limitation and watermark are explicit. "
                    "Match the declared schema exactly."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=(
                        "reportDocument",
                        "sourceResult",
                        "citationCheck",
                        "readability",
                    ),
                    properties={
                        "reportDocument": _FORMAL_REPORT_DOCUMENT_SCHEMA,
                        "sourceResult": _POST_EVALUATION_RESULT_V2_SCHEMA,
                        "citationCheck": _CITATION_CHECK_SCHEMA,
                        "readability": _READABILITY_GATE_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_REPORT_MODEL_REVIEW_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://deviation/schedule-scope-fact-analyst@1",
                version="1",
                role="deviation-schedule-scope-fact-analyst",
                instructions=(
                    "Extract only schedule baselines, actual or forecast milestone dates, "
                    "critical-path indicators, PV/EV, scope items, delivery and acceptance "
                    "statuses. Cite immutable document-version evidence for every material fact. "
                    "Do not calculate variances, scores, SPI or trends. Never choose documents, "
                    "invent missing values or resolve baseline ambiguity."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "scheduleEvidence", "scopeEvidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "scheduleEvidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "scopeEvidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_DEVIATION_FACT_ANALYSIS_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://deviation/cost-change-fact-analyst@1",
                version="1",
                role="deviation-cost-change-fact-analyst",
                instructions=(
                    "Extract only original budget, approved changes, current budget, AC, "
                    "commitments, EAC, PV/EV, currency and frozen exchange-rate facts. Separate "
                    "approved from proposed changes and actual cost from commitments. Cite "
                    "immutable evidence. Do not calculate cost variance, CV or CPI."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "costEvidence", "changeEvidence", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "costEvidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "changeEvidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_DEVIATION_FACT_ANALYSIS_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://deviation/root-cause-analyst@1",
                version="1",
                role="deviation-root-cause-analyst",
                instructions=(
                    "Explain plausible root causes only from deterministic dimension diagnostics "
                    "and cited evidence. Separate observation, causal hypothesis and impact. "
                    "Return confidence and evidence references; do not modify any metric or state "
                    "an unsupported cause as fact."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("dimensions", "evidence"),
                    properties={
                        "dimensions": {"type": "object"},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_DEVIATION_ROOT_CAUSE_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://deviation/responsibility-analyst@1",
                version="1",
                role="deviation-responsibility-analyst",
                instructions=(
                    "Propose possible responsibility allocation from root causes, RACI, contract "
                    "clauses, approvals and meeting evidence. Every item is a proposal only and "
                    "must cite evidence and confidence. Never output CONFIRMED or DISPUTED and "
                    "never infer responsibility from a metric alone."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("rootCauses", "evidence"),
                    properties={
                        "rootCauses": {"type": "array", "items": {"type": "object"}},
                        "evidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_DEVIATION_RESPONSIBILITY_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://deviation/evidence-reviewer@1",
                version="1",
                role="deviation-evidence-reviewer",
                instructions=(
                    "Review coverage, immutable evidence, conflicts, baseline ambiguity, blocked "
                    "dimensions and responsibility proposals. Require human review for missing "
                    "required documents, material conflicts, cross-currency blocks or any "
                    "responsibility proposal. Do not change facts or deterministic metrics."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=(
                        "coverage",
                        "consistency",
                        "dimensions",
                        "rootCauses",
                        "responsibility",
                    ),
                    properties={
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "consistency": _CONSISTENCY_RESULT_SCHEMA,
                        "dimensions": {"type": "object"},
                        "rootCauses": {"type": "array", "items": {"type": "object"}},
                        "responsibility": {"type": "object"},
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_DEVIATION_REVIEW_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://deviation/report-narrator@1",
                version="1",
                role="deviation-report-narrator",
                instructions=(
                    "Write a concise Chinese management narrative from frozen deterministic "
                    "metrics, evidence review, root causes, trends and proposed responsibility. "
                    "Do not alter numbers, statuses, evidence or responsibility state. Explicitly "
                    "label responsibility as pending human confirmation."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=(
                        "dimensions",
                        "rootCauses",
                        "trends",
                        "responsibility",
                        "review",
                    ),
                    properties={
                        "dimensions": {"type": "object"},
                        "rootCauses": {"type": "array", "items": {"type": "object"}},
                        "trends": {"type": "object"},
                        "responsibility": {"type": "object"},
                        "review": _DEVIATION_REVIEW_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_DEVIATION_NARRATIVE_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://invoice/fact-normalizer@1",
                version="1",
                role="invoice-fact-normalizer",
                instructions=(
                    "Normalize only low-confidence OCR candidates and invoice line item "
                    "semantics. Preserve all high-confidence XML or structured original values "
                    "unchanged. Return invoiceFactSet with evidenceFacts for every change. "
                    "Never invent tax IDs, invoice numbers, bank accounts, amounts or taxes. "
                    "Never decide authenticity or payment readiness."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "invoiceFactSet", "coverage"),
                    properties={
                        "basePayload": {"type": "object"},
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "parseQuality": {"type": "array", "items": {"type": "object"}},
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "fieldConfirmations": {"type": "array", "items": {"type": "object"}},
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_INVOICE_NORMALIZER_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://invoice/commercial-match-analyst@1",
                version="1",
                role="invoice-commercial-match-analyst",
                instructions=(
                    "Propose candidate mappings between invoice lines and contract, purchase "
                    "order or acceptance lines when descriptions differ. Every candidate must "
                    "include invoiceLineId, targetLineId, reasons, evidenceRefs and ambiguities. "
                    "Do not approve over-quantity or over-price, and do not compute cumulative "
                    "amounts. Deterministic tools own final matched amounts."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=("basePayload", "invoiceFactSet", "businessSnapshot"),
                    properties={
                        "basePayload": {"type": "object"},
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "businessSnapshot": {"type": "object"},
                        "commercialEvidence": _EVIDENCE_SEARCH_RESULT_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_INVOICE_MATCH_CANDIDATE_SCHEMA,
            ),
            AgentRegistration(
                ref="agent://invoice/evidence-risk-reviewer@1",
                version="1",
                role="invoice-evidence-risk-reviewer",
                instructions=(
                    "Review evidence coverage, conflicts and unsupported claims across "
                    "verification, arithmetic, party, duplication, commercial match and payment "
                    "gates. Write a concise Chinese risk narrative. Require human review for "
                    "pending verification, hard blocks, material conflicts or missing required "
                    "documents. Never change rule statuses, risk grades or payment outcomes."
                ),
                model="model://general@1",
                inputSchema=_object_schema(
                    required=(
                        "coverage",
                        "verification",
                        "ruleResults",
                        "matchResults",
                        "gateResults",
                        "invoiceFactSet",
                    ),
                    properties={
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "verification": {"type": "object"},
                        "ruleResults": {"type": "object"},
                        "matchResults": {"type": "object"},
                        "gateResults": {"type": "object"},
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "_contextMode": {"const": "node_only"},
                    },
                ),
                outputSchema=_INVOICE_REVIEW_SCHEMA,
            ),
        ),
        models=(
            ModelRegistration(
                ref="model://general@1",
                version="1",
                runtime="agno",
                providerModel="openai:gpt-4o-mini",
                environments=("development", "production"),
            ),
            ModelRegistration(
                ref="model://deepseek-v4-flash@1",
                version="1",
                runtime="agno",
                providerModel="DeepSeek-V4-Flash",
                environments=("development", "production"),
            ),
            ModelRegistration(
                ref="model://deepseek-v4-pro@1",
                version="1",
                runtime="agno",
                providerModel="DeepSeek-V4-Pro",
                environments=("development", "production"),
            ),
            ModelRegistration(
                ref="model://kimi-k2.5@1",
                version="1",
                runtime="agno",
                providerModel="kimi-k2.5",
                environments=("development", "production"),
            ),
            ModelRegistration(
                ref="model://kimi-k2.7-code@1",
                version="1",
                runtime="agno",
                providerModel="kimi-k2.7-code",
                environments=("development", "production"),
            ),
            ModelRegistration(
                ref="model://fake-deterministic@1",
                version="1",
                runtime="fake-deterministic",
                providerModel="fake:deterministic",
                environments=("development", "test"),
            ),
        ),
        tools=(
            ToolRegistration(
                ref="tool://search@1",
                version="1",
                operation="builtin.search",
                description="Search the configured knowledge source.",
                risk=ToolRisk.LOW,
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {"query": {"type": "string"}},
                    "additionalProperties": False,
                },
                outputSchema={
                    "type": "object",
                    "required": ["items"],
                    "properties": {"items": {"type": "array"}},
                },
                idempotent=True,
                sideEffecting=False,
                costUsd=0.001,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://publish-report@1",
                version="1",
                operation="builtin.publish_report",
                description="Publish an approved report to the controlled business sink.",
                risk=ToolRisk.HIGH,
                inputSchema={
                    "type": "object",
                    "required": ["reports"],
                    "properties": {"reports": {"type": "object"}},
                    "additionalProperties": False,
                },
                outputSchema={
                    "type": "object",
                    "required": ["publicationId", "reports"],
                    "properties": {
                        "publicationId": {"type": "string"},
                        "reports": {"type": "object"},
                    },
                },
                idempotent=True,
                sideEffecting=True,
                costUsd=0.01,
                recoveryPolicy="compensate",
                compensationOperation="builtin.unpublish_report",
            ),
            ToolRegistration(
                ref="tool://document/read@1",
                version="1",
                operation="contract.document_read",
                description="Read a controlled project document for contract analysis.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("documentId", "filename", "mediaType", "sha256", "contentBase64"),
                    properties={
                        "documentId": {"type": "string", "format": "uuid"},
                        "filename": {"type": "string", "minLength": 1},
                        "mediaType": {"enum": ["text/plain", "application/json"]},
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "contentBase64": {"type": "string", "minLength": 1},
                    },
                ),
                outputSchema=_object_schema(
                    required=("documentId", "filename", "mediaType", "sha256", "pages"),
                    properties={
                        "documentId": {"type": "string"},
                        "filename": {"type": "string"},
                        "mediaType": {"type": "string"},
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "pages": {
                            "type": "array",
                            "minItems": 1,
                            "items": _object_schema(
                                required=("page", "text"),
                                properties={
                                    "page": {"type": "integer", "minimum": 1},
                                    "text": {"type": "string"},
                                },
                            ),
                        },
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://rules/evaluate@1",
                version="1",
                operation="contract.rules_evaluate",
                description="Evaluate a versioned contract rule set against structured facts.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("ruleSetVersionId", "rules", "attachments", "attachmentManifestHash"),
                    properties={
                        "ruleSetVersionId": {"type": "string", "minLength": 1},
                        "rules": _RULE_DOCUMENT_SCHEMA,
                        "attachments": {"type": "array", "items": _ATTACHMENT_SCHEMA},
                        "attachmentManifestHash": {"type": "string", "minLength": 1},
                    },
                ),
                outputSchema=_INTEGRITY_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://contract/cross-file-consistency@1",
                version="1",
                operation="contract.cross_file_consistency",
                description="Check evidence-backed fields for consistency across contract files.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("results", "rules"),
                    properties={
                        "results": {"type": "array", "items": _EXTRACTION_RESULT_SCHEMA},
                        "rules": {"type": "array", "items": _CROSS_FILE_RULE_SCHEMA},
                    },
                ),
                outputSchema=_object_schema(
                    required=("findings", "reviewRequired"),
                    properties={
                        "findings": {"type": "array", "items": _CROSS_FILE_FINDING_SCHEMA},
                        "reviewRequired": {"type": "boolean"},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://workbench/record-evaluation@1",
                version="1",
                operation="workbench.record_evaluation",
                description="Record an idempotent business workbench evaluation result.",
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("evaluationId", "result"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "result": _INTEGRITY_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_object_schema(
                    required=("evaluationId", "recorded", "effectId", "resultHash"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "recorded": {"type": "boolean"},
                        "effectId": {"type": "string"},
                        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render@1",
                version="1",
                operation="report.render",
                description="Render a deterministic report from a structured evaluation result.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("title", "results"),
                    properties={
                        "title": {"type": "string", "minLength": 1},
                        "results": {"type": "array", "items": _EXTRACTION_RESULT_SCHEMA},
                        "rules": {"type": "array", "items": _CROSS_FILE_RULE_SCHEMA},
                    },
                ),
                outputSchema=_object_schema(
                    required=("mediaType", "sha256", "contentBase64"),
                    properties={
                        "mediaType": {"const": "application/pdf"},
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "contentBase64": {"type": "string", "minLength": 1},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://resource/read-bound@1",
                version="1",
                operation="resource.read_bound",
                description=(
                    "Read a frozen capability resource binding and record its content hash."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("evaluationId", "resource"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "resource": _BOUND_RESOURCE_SCHEMA,
                    },
                ),
                outputSchema=_BOUND_RESOURCE_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://document/read-versions@1",
                version="1",
                operation="document.read_versions",
                description="Read the immutable document versions frozen for an assessment.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("evaluationId", "documents"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "documents": {
                            "type": "array",
                            "items": _BOUND_DOCUMENT_SCHEMA,
                        },
                    },
                ),
                outputSchema=_BOUND_DOCUMENT_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://evidence/search@1",
                version="1",
                operation="evidence.search",
                description=(
                    "Search compact processed content from frozen document versions by domain."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("documents", "domain"),
                    properties={
                        "documents": {"type": "array", "items": {"type": "object"}},
                        "domain": {
                            "enum": ["contract", "performance", "finance", "governance"]
                        },
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "maxHits": {"type": "integer", "minimum": 1, "maximum": 50},
                    },
                ),
                outputSchema=_EVIDENCE_SEARCH_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://document/coverage-check@1",
                version="1",
                operation="document.coverage_check",
                description=(
                    "Evaluate required document categories, readability and duplicate content."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("documents", "requirements"),
                    properties={
                        "documents": {"type": "array", "items": {"type": "object"}},
                        "requirements": {"type": "array", "items": {"type": "object"}},
                    },
                ),
                outputSchema=_COVERAGE_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://contract/post-evaluation/merge-domains@1",
                version="1",
                operation="contract.post_evaluation_merge_domains",
                description=(
                    "Merge four evidence-backed domain analyses into one normalized payload."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("basePayload", "analyses"),
                    properties={
                        "basePayload": {"type": "object"},
                        "analyses": {"type": "object"},
                    },
                ),
                outputSchema=_MERGED_DOMAIN_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://contract/timeline-calculate@1",
                version="1",
                operation="contract.post_evaluation_timeline",
                description="Calculate deterministic obligation timeliness diagnostics.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",),
                    properties={"payload": _POST_EVALUATION_PAYLOAD_SCHEMA},
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://finance/amount-reconcile@1",
                version="1",
                operation="finance.post_evaluation_amounts",
                description=(
                    "Reconcile contract amount, actual cost and invoiced amount deterministically."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",),
                    properties={"payload": _POST_EVALUATION_PAYLOAD_SCHEMA},
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/assurance@1",
                version="1",
                operation="invoice.post_evaluation_assurance",
                description=(
                    "Calculate invoice matching, duplicate and compliance diagnostics."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",),
                    properties={"payload": _POST_EVALUATION_PAYLOAD_SCHEMA},
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/aggregate@1",
                version="1",
                operation="deviation.post_evaluation_aggregate",
                description="Aggregate deviation closure, severity, delay and cost impact.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",),
                    properties={"payload": _POST_EVALUATION_PAYLOAD_SCHEMA},
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://risk/aggregate@1",
                version="1",
                operation="risk.post_evaluation_aggregate",
                description="Aggregate risk closure, level and overdue remediation diagnostics.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",),
                    properties={"payload": _POST_EVALUATION_PAYLOAD_SCHEMA},
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://evidence/consistency-check@1",
                version="1",
                operation="evidence.consistency_check",
                description=(
                    "Check identifiers, declared conflicts, evidence references and confidence."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload", "evidenceFacts", "declaredConflicts"),
                    properties={
                        "payload": _POST_EVALUATION_PAYLOAD_SCHEMA,
                        "evidenceFacts": {"type": "array", "items": _EVIDENCE_FACT_SCHEMA},
                        "declaredConflicts": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                ),
                outputSchema=_CONSISTENCY_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://contract/post-evaluation/assemble@1",
                version="1",
                operation="contract.post_evaluation_assemble",
                description=(
                    "Normalize five bound data sources into one contract post-evaluation payload."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload", "sources"),
                    properties={
                        "payload": {"type": "object"},
                        "sources": {
                            "type": "array",
                            "minItems": 5,
                            "maxItems": 5,
                            "items": _BOUND_RESOURCE_RESULT_SCHEMA,
                        },
                    },
                ),
                outputSchema=_POST_EVALUATION_PAYLOAD_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://contract/post-evaluation@1",
                version="1",
                operation="contract.post_evaluation",
                description=(
                    "Calculate a deterministic seven-dimension contract post-evaluation from "
                    "structured document, performance, deviation, invoice, and risk facts."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload", "configuration", "attachmentManifestHash"),
                    properties={
                        "payload": {"type": "object"},
                        "configuration": {"type": "object"},
                        "attachmentManifestHash": {"type": "string", "minLength": 1},
                    },
                ),
                outputSchema=_POST_EVALUATION_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://contract/post-evaluation/finalize@2",
                version="2",
                operation="contract.post_evaluation_finalize",
                description=(
                    "Freeze deterministic scoring, evidence review, diagnostics and narrative "
                    "into the version 2 post-evaluation result."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(
                        "score",
                        "review",
                        "narrative",
                        "coverage",
                        "consistency",
                        "diagnostics",
                        "provenance",
                    ),
                    properties={
                        "score": _POST_EVALUATION_RESULT_SCHEMA,
                        "review": _EVIDENCE_REVIEW_SCHEMA,
                        "narrative": _REPORT_NARRATIVE_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "consistency": _CONSISTENCY_RESULT_SCHEMA,
                        "diagnostics": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
                outputSchema=_POST_EVALUATION_RESULT_V2_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render-post-evaluation@1",
                version="1",
                operation="report.render_post_evaluation",
                description="Render a PDF from the structured seven-dimension evaluation result.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("title", "result"),
                    properties={
                        "title": {"type": "string", "minLength": 1},
                        "result": _POST_EVALUATION_RESULT_SCHEMA,
                    },
                ),
                outputSchema=_PDF_REPORT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render-post-evaluation@2",
                version="2",
                operation="report.render_post_evaluation_v2",
                description=(
                    "Render a PDF from the evidence-backed version 2 post-evaluation result."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("title", "result"),
                    properties={
                        "title": {"type": "string", "minLength": 1},
                        "result": _POST_EVALUATION_RESULT_V2_SCHEMA,
                    },
                ),
                outputSchema=_PDF_REPORT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render-post-evaluation@3",
                version="3",
                operation="report.render_post_evaluation_v3",
                description=(
                    "Render a CJK-capable PDF from the evidence-backed version 2 "
                    "post-evaluation result."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("title", "result"),
                    properties={
                        "title": {"type": "string", "minLength": 1},
                        "result": _POST_EVALUATION_RESULT_V2_SCHEMA,
                    },
                ),
                outputSchema=_PDF_REPORT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://document/readability-gate@1",
                version="1",
                operation="document.post_evaluation_readability_gate",
                description=(
                    "Classify a frozen document set as formal-report eligible or pre-review "
                    "using a deterministic readable-content threshold."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("coverage", "formalThreshold"),
                    properties={
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "formalThreshold": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                    },
                ),
                outputSchema=_READABILITY_GATE_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/compose-post-evaluation@1",
                version="1",
                operation="report.compose_post_evaluation",
                description=(
                    "Compose a complete business-grade report document from frozen results, "
                    "diagnostics, approved evidence and bounded model narratives."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(
                        "title",
                        "result",
                        "readability",
                        "sectionDrafts",
                        "editorial",
                        "review",
                        "coverage",
                        "consistency",
                        "diagnostics",
                        "approval",
                    ),
                    properties={
                        "title": {"type": "string", "minLength": 1},
                        "result": _POST_EVALUATION_RESULT_V2_SCHEMA,
                        "readability": _READABILITY_GATE_SCHEMA,
                        "sectionDrafts": {"type": "object"},
                        "editorial": _FORMAL_EDITORIAL_SCHEMA,
                        "review": _EVIDENCE_REVIEW_SCHEMA,
                        "coverage": _COVERAGE_RESULT_SCHEMA,
                        "consistency": _CONSISTENCY_RESULT_SCHEMA,
                        "diagnostics": {"type": "object"},
                        "approval": {"type": ["object", "null"]},
                    },
                ),
                outputSchema=_FORMAL_REPORT_DOCUMENT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/verify-post-evaluation-citations@1",
                version="1",
                operation="report.verify_post_evaluation_citations",
                description=(
                    "Verify report citations and prove that all displayed scores match the "
                    "frozen evaluation."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("reportDocument", "sourceResult"),
                    properties={
                        "reportDocument": _FORMAL_REPORT_DOCUMENT_SCHEMA,
                        "sourceResult": _POST_EVALUATION_RESULT_V2_SCHEMA,
                    },
                ),
                outputSchema=_CITATION_CHECK_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/check-post-evaluation-quality@1",
                version="1",
                operation="report.check_post_evaluation_quality",
                description=(
                    "Apply the deterministic formal-report completeness, score, citation and "
                    "business-language gate and emit the version 3 frozen result."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(
                        "sourceResult",
                        "reportDocument",
                        "citationCheck",
                        "modelReview",
                        "readability",
                    ),
                    properties={
                        "sourceResult": _POST_EVALUATION_RESULT_V2_SCHEMA,
                        "reportDocument": _FORMAL_REPORT_DOCUMENT_SCHEMA,
                        "citationCheck": _CITATION_CHECK_SCHEMA,
                        "modelReview": _REPORT_MODEL_REVIEW_SCHEMA,
                        "readability": _READABILITY_GATE_SCHEMA,
                    },
                ),
                outputSchema=_POST_EVALUATION_RESULT_V3_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render-post-evaluation@4",
                version="4",
                operation="report.render_post_evaluation_v4",
                description=(
                    "Render a quality-gated, multi-section Chinese contract post-evaluation "
                    "PDF with cover, score chart, tables, evidence, remediation and approval."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("result",),
                    properties={"result": _POST_EVALUATION_RESULT_V3_SCHEMA},
                ),
                outputSchema=_PDF_REPORT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://workbench/record-post-evaluation@1",
                version="1",
                operation="workbench.record_post_evaluation",
                description="Record an idempotent contract post-evaluation result.",
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("evaluationId", "result", "report"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "result": _POST_EVALUATION_RESULT_SCHEMA,
                        "report": _PDF_REPORT_SCHEMA,
                    },
                ),
                outputSchema=_object_schema(
                    required=("evaluationId", "recorded", "effectId", "resultHash"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "recorded": {"type": "boolean"},
                        "effectId": {"type": "string"},
                        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://workbench/record-post-evaluation@2",
                version="2",
                operation="workbench.record_post_evaluation",
                description=(
                    "Idempotently persist an evidence-backed version 2 evaluation and reports."
                ),
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("evaluationId", "result", "report"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "result": _POST_EVALUATION_RESULT_V2_SCHEMA,
                        "report": _PDF_REPORT_SCHEMA,
                    },
                ),
                outputSchema=_object_schema(
                    required=("evaluationId", "recorded", "effectId", "resultHash"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "recorded": {"type": "boolean"},
                        "effectId": {"type": "string"},
                        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://workbench/record-post-evaluation@3",
                version="3",
                operation="workbench.record_post_evaluation",
                description=(
                    "Idempotently persist the version 3 evaluation, formal report document, "
                    "quality gate and rendered PDF."
                ),
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("evaluationId", "result", "report"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "result": _POST_EVALUATION_RESULT_V3_SCHEMA,
                        "report": _PDF_REPORT_SCHEMA,
                    },
                ),
                outputSchema=_object_schema(
                    required=("evaluationId", "recorded", "effectId", "resultHash"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "recorded": {"type": "boolean"},
                        "effectId": {"type": "string"},
                        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/facts-merge@1",
                version="1",
                operation="deviation.facts_merge",
                description=(
                    "Merge evidence-backed deviation fact patches without calculating metrics."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("basePayload", "analyses"),
                    properties={
                        "basePayload": {"type": "object"},
                        "analyses": {"type": "object"},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema=_object_schema(
                    required=("payload", "facts", "conflicts", "missingEvidence"),
                    properties={
                        "payload": {"type": "object"},
                        "facts": {"type": "array", "items": {"type": "object"}},
                        "conflicts": {"type": "array", "items": {"type": "string"}},
                        "missingEvidence": {"type": "array", "items": {"type": "string"}},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/time-calculate@1",
                version="1",
                operation="deviation.time_calculate",
                description=(
                    "Calculate milestone, on-time, critical-path and optional SPI diagnostics."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",), properties={"payload": {"type": "object"}}
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/content-compare@1",
                version="1",
                operation="deviation.content_compare",
                description=(
                    "Compare baseline deliverables and acceptance using frozen scoring rules."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",), properties={"payload": {"type": "object"}}
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/cost-calculate@1",
                version="1",
                operation="deviation.cost_calculate",
                description=(
                    "Calculate current BAC, EAC variance and optional CV/CPI deterministically."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",), properties={"payload": {"type": "object"}}
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/history-read@1",
                version="1",
                operation="deviation.history_read",
                description=(
                    "Read same-subject historical results with identical baseline "
                    "and configuration."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(
                        "evaluationId",
                        "subjectId",
                        "baselineHash",
                        "configurationHash",
                        "asOf",
                    ),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "subjectId": {"type": "string", "minLength": 1},
                        "baselineHash": {"type": "string", "minLength": 1},
                        "configurationHash": {"type": "string", "minLength": 1},
                        "asOf": {"type": "string", "format": "date"},
                        "trendWindow": {
                            "type": "string",
                            "pattern": "^P[0-9]+M$",
                        },
                        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                    },
                ),
                outputSchema=_object_schema(
                    required=("items", "count"),
                    properties={
                        "items": {"type": "array", "items": {"type": "object"}},
                        "count": {"type": "integer", "minimum": 0},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/trend-build@1",
                version="1",
                operation="deviation.trend_build",
                description=(
                    "Build comparable trends and decline judgment on a first or incompatible run."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("current", "history"),
                    properties={
                        "current": {"type": "object"},
                        "history": {"type": "array", "items": {"type": "object"}},
                    },
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/responsibility-aggregate@1",
                version="1",
                operation="deviation.responsibility_aggregate",
                description=(
                    "Normalize AI responsibility output as human-confirmable proposals only."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("proposals",),
                    properties={"proposals": {"type": "array", "items": {"type": "object"}}},
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://deviation/finalize@1",
                version="1",
                operation="deviation.finalize",
                description=(
                    "Freeze metrics, root causes, trends, responsibility, review and provenance."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(
                        "payload",
                        "dimensions",
                        "rootCauses",
                        "trends",
                        "responsibility",
                        "coverage",
                        "evidenceReview",
                        "narrative",
                        "provenance",
                    ),
                    properties={
                        "payload": {"type": "object"},
                        "dimensions": {"type": "object"},
                        "rootCauses": {"type": "array", "items": {"type": "object"}},
                        "trends": {"type": "object"},
                        "responsibility": {"type": "object"},
                        "coverage": {"type": "object"},
                        "evidenceReview": {"type": "object"},
                        "narrative": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
                outputSchema=_DEVIATION_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render-deviation-analysis@1",
                version="1",
                operation="report.render_deviation_analysis",
                description="Render a deterministic PDF from the structured deviation result.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("result",), properties={"result": _DEVIATION_RESULT_SCHEMA}
                ),
                outputSchema=_PDF_REPORT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://workbench/record-deviation-analysis@1",
                version="1",
                operation="workbench.record_deviation_analysis",
                description="Idempotently persist deviation JSON/PDF, audit and outbox events.",
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("evaluationId", "result", "report"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "result": _DEVIATION_RESULT_SCHEMA,
                        "report": _PDF_REPORT_SCHEMA,
                    },
                ),
                outputSchema=_object_schema(
                    required=("evaluationId", "recorded", "effectId", "resultHash"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "recorded": {"type": "boolean"},
                        "effectId": {"type": "string"},
                        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/parse@1",
                version="1",
                operation="invoice.parse",
                description=(
                    "Parse invoice originals preferring XML structured data; mark low-confidence "
                    "fields for human confirmation without inventing values."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(),
                    properties={
                        "documents": {"type": "array", "items": {"type": "object"}},
                        "payload": {"type": "object"},
                        "configuration": {"type": "object"},
                        "content": {"type": ["string", "object"]},
                        "mediaType": {"type": "string"},
                        "documentVersionId": {"type": "string"},
                    },
                ),
                outputSchema=_object_schema(
                    required=("invoiceFactSet",),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "needsFieldConfirmation": {"type": "boolean"},
                        "qualityFlags": {"type": "array", "items": {"type": "object"}},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/official-verify@1",
                version="1",
                operation="invoice.official_verify",
                description=(
                    "Run authorized tax verification or create a human-assisted verification "
                    "task. Never fabricate a successful face match."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("invoiceFactSet",),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "verificationMode": {
                            "enum": ["AUTHORIZED_CONNECTOR", "HUMAN_ASSISTED"]
                        },
                        "humanVerification": {"type": "object"},
                        "connectorResult": {"type": "object"},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://business/snapshot-read@1",
                version="1",
                operation="business.snapshot_read",
                description=(
                    "Normalize and hash frozen business snapshots for contracts, POs, "
                    "acceptance, vendor, AP ledger and budget policy."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("payload",),
                    properties={
                        "payload": {"type": "object"},
                        "subjects": {"type": "array", "items": {"type": "object"}},
                        "documents": {"type": "array", "items": {"type": "object"}},
                        "asOf": {"type": "string"},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/deduplicate@1",
                version="1",
                operation="invoice.deduplicate",
                description=(
                    "Detect duplicate invoices and red/blue credit relationships in the AP ledger."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("invoiceFactSet",),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "businessSnapshot": {"type": "object"},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/arithmetic-check@1",
                version="1",
                operation="invoice.arithmetic_check",
                description=(
                    "Deterministically validate invoice amounts, taxes and required face fields."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("invoiceFactSet",),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={
                    "type": "object",
                    "required": ["ruleResults"],
                    "properties": {
                        "ruleResults": {"type": "array", "items": {"type": "object"}}
                    },
                },
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/party-check@1",
                version="1",
                operation="invoice.party_check",
                description=(
                    "Compare buyer/seller tax IDs and approved bank accounts against vendor master."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("invoiceFactSet",),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "businessSnapshot": {"type": "object"},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={
                    "type": "object",
                    "required": ["ruleResults"],
                    "properties": {
                        "ruleResults": {"type": "array", "items": {"type": "object"}}
                    },
                },
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/commercial-match@1",
                version="1",
                operation="invoice.commercial_match",
                description=(
                    "Deterministically match invoice amounts to contract, PO and acceptance lines."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("invoiceFactSet", "businessSnapshot"),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "businessSnapshot": {"type": "object"},
                        "matchCandidates": {"type": "array", "items": {"type": "object"}},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/payment-gate@1",
                version="1",
                operation="invoice.payment_gate",
                description=(
                    "Evaluate payment readiness gates including hard blocks that cannot auto-pass."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("verification",),
                    properties={
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "verification": {"type": "object"},
                        "ruleResults": {"type": "object"},
                        "matchResults": {"type": "object"},
                        "businessSnapshot": {"type": "object"},
                        "configuration": {"type": "object"},
                    },
                ),
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://invoice/finalize@1",
                version="1",
                operation="invoice.finalize",
                description=(
                    "Assemble the immutable InvoiceAssuranceResult and payment outcome."
                ),
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=(
                        "invoiceFactSet",
                        "verification",
                        "ruleResults",
                        "matchResults",
                        "gateResults",
                    ),
                    properties={
                        "payload": {"type": "object"},
                        "invoiceFactSet": _INVOICE_FACT_SET_SCHEMA,
                        "verification": {"type": "object"},
                        "businessSnapshotHash": {"type": "string"},
                        "businessSnapshot": {"type": "object"},
                        "ruleResults": {"type": "object"},
                        "matchResults": {"type": "object"},
                        "gateResults": {"type": "object"},
                        "coverage": {"type": "object"},
                        "evidenceReview": {"type": "object"},
                        "approvals": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                ),
                outputSchema=_INVOICE_ASSURANCE_RESULT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://report/render-invoice-assurance@1",
                version="1",
                operation="report.render_invoice_assurance",
                description="Render a deterministic Chinese PDF from the invoice assurance result.",
                risk=ToolRisk.LOW,
                inputSchema=_object_schema(
                    required=("result",),
                    properties={"result": _INVOICE_ASSURANCE_RESULT_SCHEMA},
                ),
                outputSchema=_PDF_REPORT_SCHEMA,
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://workbench/record-invoice-assurance@1",
                version="1",
                operation="workbench.record_invoice_assurance",
                description=(
                    "Idempotently persist invoice assurance JSON/PDF, findings, audit and outbox."
                ),
                risk=ToolRisk.HIGH,
                inputSchema=_object_schema(
                    required=("evaluationId", "result", "report"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "result": _INVOICE_ASSURANCE_RESULT_SCHEMA,
                        "report": _PDF_REPORT_SCHEMA,
                    },
                ),
                outputSchema=_object_schema(
                    required=("evaluationId", "recorded", "effectId", "resultHash"),
                    properties={
                        "evaluationId": {"type": "string", "format": "uuid"},
                        "recorded": {"type": "boolean"},
                        "effectId": {"type": "string"},
                        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://filesystem/read-text@1",
                version="1",
                operation="filesystem.read_text",
                description="Read a UTF text file from a tenant/project logical filesystem mount.",
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("mount", "path"),
                    properties={
                        "mount": {"type": "string", "minLength": 1, "maxLength": 64},
                        "path": {"type": "string", "minLength": 1, "maxLength": 1024},
                        "encoding": {"type": "string", "minLength": 1, "default": "utf-8"},
                        "expectedSha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                outputSchema=_object_schema(
                    required=("mount", "path", "content", "encoding", "sizeBytes", "sha256"),
                    properties={
                        "mount": {"type": "string"},
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "encoding": {"type": "string"},
                        "sizeBytes": {"type": "integer", "minimum": 0},
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://filesystem/write-text@1",
                version="1",
                operation="filesystem.write_text",
                description=(
                    "Atomically write a UTF text file under a tenant/project logical mount."
                ),
                risk=ToolRisk.HIGH,
                inputSchema=_object_schema(
                    required=("mount", "path", "content"),
                    properties={
                        "mount": {"type": "string", "minLength": 1, "maxLength": 64},
                        "path": {"type": "string", "minLength": 1, "maxLength": 1024},
                        "content": {"type": "string"},
                        "encoding": {"type": "string", "minLength": 1, "default": "utf-8"},
                        "mode": {"enum": ["create", "replace"], "default": "create"},
                        "expectedSha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                ),
                outputSchema=_object_schema(
                    required=("mount", "path", "created", "sizeBytes", "sha256", "effectId"),
                    properties={
                        "mount": {"type": "string"},
                        "path": {"type": "string"},
                        "created": {"type": "boolean"},
                        "sizeBytes": {"type": "integer", "minimum": 0},
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "effectId": {"type": "string", "minLength": 1},
                    },
                ),
                idempotent=True,
                sideEffecting=True,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://filesystem/list@1",
                version="1",
                operation="filesystem.list",
                description="List direct children under a tenant/project logical filesystem path.",
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("mount", "path"),
                    properties={
                        "mount": {"type": "string", "minLength": 1, "maxLength": 64},
                        "path": {"type": "string", "minLength": 1, "maxLength": 1024},
                    },
                ),
                outputSchema=_object_schema(
                    required=("mount", "path", "entries"),
                    properties={
                        "mount": {"type": "string"},
                        "path": {"type": "string"},
                        "entries": {
                            "type": "array",
                            "items": _object_schema(
                                required=("name", "path", "type", "sizeBytes", "rejectedLink"),
                                properties={
                                    "name": {"type": "string"},
                                    "path": {"type": "string"},
                                    "type": {
                                        "enum": ["file", "directory", "link", "other"],
                                    },
                                    "sizeBytes": {"type": "integer", "minimum": 0},
                                    "rejectedLink": {"type": "boolean"},
                                },
                            ),
                        },
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://filesystem/stat@1",
                version="1",
                operation="filesystem.stat",
                description="Stat a path under a tenant/project logical filesystem mount.",
                risk=ToolRisk.MEDIUM,
                inputSchema=_object_schema(
                    required=("mount", "path"),
                    properties={
                        "mount": {"type": "string", "minLength": 1, "maxLength": 64},
                        "path": {"type": "string", "minLength": 1, "maxLength": 1024},
                    },
                ),
                outputSchema=_object_schema(
                    required=(
                        "mount",
                        "path",
                        "type",
                        "sizeBytes",
                        "modifiedAt",
                        "sha256",
                        "rejectedLink",
                    ),
                    properties={
                        "mount": {"type": "string"},
                        "path": {"type": "string"},
                        "type": {"enum": ["file", "directory", "link", "other"]},
                        "sizeBytes": {"type": "integer", "minimum": 0},
                        "modifiedAt": {"type": ["string", "null"]},
                        "sha256": {
                            "anyOf": [
                                {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                {"type": "null"},
                            ]
                        },
                        "rejectedLink": {"type": "boolean"},
                    },
                ),
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
        ),
    )
