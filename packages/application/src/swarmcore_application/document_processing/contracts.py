"""Generic document intake and processing contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProcessingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


ProcessingStage = Literal[
    "PENDING",
    "UPLOADING",
    "SCANNING",
    "PARSING",
    "OCR_PROCESSING",
    "CLASSIFYING",
    "EXTRACTING",
    "QUALITY_CHECK",
    "REVIEW_REQUIRED",
    "READY",
    "FAILED",
    "CANCELLED",
]

ProcessingStatus = Literal[
    "PENDING",
    "UPLOADING",
    "SCANNING",
    "PARSING",
    "OCR_PROCESSING",
    "CLASSIFYING",
    "EXTRACTING",
    "QUALITY_CHECK",
    "REVIEW_REQUIRED",
    "READY",
    "FAILED",
    "CANCELLED",
]

TERMINAL_STATUSES = frozenset({"READY", "FAILED", "CANCELLED"})
SUCCESSFUL_IMMUTABLE_STAGES = frozenset({"SCANNING", "PARSING", "OCR_PROCESSING"})


class DocumentProcessingProfile(ProcessingModel):
    profile_id: str = Field(alias="profileId", min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    version: str = Field(min_length=1, max_length=64)
    accepted_media_types: tuple[str, ...] = Field(
        default_factory=tuple, alias="acceptedMediaTypes"
    )
    parser_policy: dict[str, Any] = Field(default_factory=dict, alias="parserPolicy")
    ocr_policy: dict[str, Any] = Field(default_factory=dict, alias="ocrPolicy")
    classifier_ref: str = Field(default="classifier://label-candidates@1", alias="classifierRef")
    extraction_schema_refs: tuple[str, ...] = Field(
        default_factory=tuple, alias="extractionSchemaRefs"
    )
    quality_thresholds: dict[str, float] = Field(
        default_factory=lambda: {"classification": 0.7, "extraction": 0.75},
        alias="qualityThresholds",
    )
    human_review_policy: dict[str, Any] = Field(
        default_factory=lambda: {"requireReviewBelowThreshold": True},
        alias="humanReviewPolicy",
    )

    @property
    def ref(self) -> str:
        return f"document-profile://{self.profile_id}@{self.version}"


class DocumentRequirement(ProcessingModel):
    key: str = Field(min_length=1, max_length=128)
    display_name: str = Field(alias="displayName", min_length=1, max_length=256)
    description: str = ""
    required: bool = True
    min_count: int = Field(default=1, alias="minCount", ge=0)
    max_count: int | None = Field(default=None, alias="maxCount", ge=1)
    accepted_media_types: tuple[str, ...] = Field(
        default_factory=tuple, alias="acceptedMediaTypes"
    )
    classification_labels: tuple[str, ...] = Field(
        default_factory=tuple, alias="classificationLabels"
    )
    processing_profile_ref: str | None = Field(default=None, alias="processingProfileRef")
    extraction_schema_ref: str | None = Field(default=None, alias="extractionSchemaRef")
    review_policy: dict[str, Any] = Field(default_factory=dict, alias="reviewPolicy")
    category: str | None = None

    @field_validator("max_count")
    @classmethod
    def valid_max(cls, value: int | None) -> int | None:
        return value


class ParsedContent(ProcessingModel):
    pages: list[dict[str, Any]] = Field(default_factory=list)
    paragraphs: list[dict[str, Any]] = Field(default_factory=list)
    sections: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    sheets: list[dict[str, Any]] = Field(default_factory=list)
    chunks: list[dict[str, Any]] = Field(default_factory=list)
    layout: dict[str, Any] = Field(default_factory=dict)
    embedded_metadata: dict[str, Any] = Field(default_factory=dict, alias="embeddedMetadata")
    warnings: list[str] = Field(default_factory=list)
    text_excerpt: str = Field(default="", alias="textExcerpt", max_length=8000)
    needs_ocr: bool = Field(default=False, alias="needsOcr")


class ClassificationResult(ProcessingModel):
    label: str
    display_name: str = Field(alias="displayName")
    confidence: float = Field(ge=0, le=1)
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confirmed_label: str | None = Field(default=None, alias="confirmedLabel")
    confirmed_by: str | None = Field(default=None, alias="confirmedBy")


class ExtractionField(ProcessingModel):
    field_path: str = Field(alias="fieldPath")
    display_name: str = Field(alias="displayName")
    value: Any = None
    value_type: str = Field(default="string", alias="valueType")
    critical: bool = False
    confidence: float = Field(default=0.0, ge=0, le=1)
    review_status: Literal[
        "AUTO_ACCEPTED", "PENDING", "CONFIRMED", "CORRECTED", "UNCONFIRMED"
    ] = Field(default="PENDING", alias="reviewStatus")
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list, alias="evidenceRefs")
    machine_value: Any = Field(default=None, alias="machineValue")
    confirmed_value: Any = Field(default=None, alias="confirmedValue")
    quality_flags: list[str] = Field(default_factory=list, alias="qualityFlags")


class ProcessingResultEnvelope(ProcessingModel):
    schema_version: str = Field(
        default="schema://document-processing-result/v2", alias="schemaVersion"
    )
    status: Literal["READY", "REVIEW_REQUIRED", "FAILED"] = "REVIEW_REQUIRED"
    document_type: ClassificationResult | None = Field(default=None, alias="documentType")
    content: ParsedContent = Field(default_factory=ParsedContent)
    extractions: list[ExtractionField] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    organization: dict[str, Any] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list, alias="qualityFlags")
    warnings: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    content_artifact_ref: str | None = Field(default=None, alias="contentArtifactRef")


DEFAULT_BUSINESS_PROFILE = DocumentProcessingProfile(
    profileId="business-default",
    name="Business default",
    version="1",
    acceptedMediaTypes=(
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/json",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "image/png",
        "image/jpeg",
        "image/tiff",
    ),
    parserPolicy={
        "preferNativeText": True,
        "largeFilePageThreshold": 50,
        "largeFileByteThreshold": 26_214_400,
        "largeSpreadsheetRowThreshold": 100_000,
        "pageBatchSize": 10,
        "maxPageCount": 500,
        "maxSpreadsheetRows": 500_000,
        "maxFileBytes": 209_715_200,
    },
    ocrPolicy={
        "enabled": True,
        "requiredWhenNoText": True,
        "pageTextCoverageThreshold": 0.02,
        "dpi": 300,
        "pageBatchSize": 10,
    },
    classifierRef="classifier://label-candidates@1",
    extractionSchemaRefs=(),
    qualityThresholds={"classification": 0.7, "extraction": 0.75},
    humanReviewPolicy={"requireReviewBelowThreshold": True},
)

BUSINESS_STRUCTURING_PROFILE = DEFAULT_BUSINESS_PROFILE.model_copy(
    update={
        "profile_id": "business-structuring",
        "name": "Business document structuring",
        "version": "1",
        "classifier_ref": "classifier://document-nlp@1",
        "extraction_schema_refs": ("schema://document/contract-structure@1",),
        "quality_thresholds": {
            "classification": 0.90,
            "extraction": 0.85,
            "criticalExtraction": 0.95,
            "ocr": 0.90,
        },
        "human_review_policy": {
            "requireReviewBelowThreshold": True,
            "requireCriticalFieldEvidence": True,
        },
    }
)


def resolve_profile(profile_ref: str | None) -> DocumentProcessingProfile:
    if profile_ref in (None, "", DEFAULT_BUSINESS_PROFILE.ref):
        return DEFAULT_BUSINESS_PROFILE
    if profile_ref is not None and profile_ref.startswith(
        "document-profile://business-default@"
    ):
        return DEFAULT_BUSINESS_PROFILE
    if profile_ref in (
        BUSINESS_STRUCTURING_PROFILE.ref,
        "document-profile://business-structuring",
    ):
        return BUSINESS_STRUCTURING_PROFILE
    if profile_ref is not None and profile_ref.startswith(
        "document-profile://business-structuring@"
    ):
        return BUSINESS_STRUCTURING_PROFILE
    raise LookupError("PROCESSING_PROFILE_NOT_FOUND")


STAGE_LABELS_ZH: dict[str, str] = {
    "PENDING": "等待处理",
    "UPLOADING": "上传中",
    "SCANNING": "安全扫描",
    "PARSING": "解析文件",
    "OCR_PROCESSING": "文字识别",
    "CLASSIFYING": "文档分类",
    "EXTRACTING": "字段抽取",
    "QUALITY_CHECK": "质量检查",
    "REVIEW_REQUIRED": "待人工确认",
    "READY": "已就绪",
    "FAILED": "处理失败",
    "CANCELLED": "已取消",
}
