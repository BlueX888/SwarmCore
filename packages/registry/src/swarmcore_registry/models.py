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
        ),
    )
