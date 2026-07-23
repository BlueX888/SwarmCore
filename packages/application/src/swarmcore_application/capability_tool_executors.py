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
from swarmcore_persistence.models import (
    BusinessDocument,
    BusinessDocumentVersion,
    Connection,
    ConnectionVersion,
    DocumentProcessingResult,
    DocumentUsageSnapshot,
    Evaluation,
    OutboxEvent,
    Report,
    ResourceDefinition,
    ResourceSnapshot,
    WorkItem,
)
from swarmcore_persistence.repositories import canonical_hash

from .document_intelligence import (
    CrossFileRule,
    DocumentIntelligenceResult,
    evaluate_cross_file_consistency,
    pdf_report_payload,
    render_evidence_pdf,
    render_text_pdf,
)
from .integrity import AttachmentInput, IntegrityRuleDocument, evaluate_integrity
from .post_evaluation import (
    PostEvaluationConfiguration,
    PostEvaluationPayload,
    PostEvaluationResult,
    assemble_post_evaluation_payload,
    evaluate_post_evaluation,
    post_evaluation_report_lines,
)
from .resource_plane import FakeConnector


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


async def post_evaluation_evaluate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    payload = PostEvaluationPayload.model_validate(input_value["payload"])
    raw_configuration = input_value.get("configuration", {})
    configuration = PostEvaluationConfiguration.model_validate(raw_configuration)
    result = evaluate_post_evaluation(payload, configuration)
    return result.model_dump(mode="json", by_alias=True)


async def post_evaluation_assemble(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = assemble_post_evaluation_payload(
        dict(input_value["payload"]),
        [dict(value) for value in input_value["sources"]],
    )
    return result.model_dump(mode="json", by_alias=True)


async def post_evaluation_report_render(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = PostEvaluationResult.model_validate(input_value["result"])
    lines = (str(input_value["title"]), *post_evaluation_report_lines(result))
    return pdf_report_payload(render_text_pdf(lines))


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


class BoundResourceReadExecutor:
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
        resource_input = dict(input_value["resource"])
        resource_id = UUID(str(resource_input["resourceId"]))
        connection_version_id = UUID(str(resource_input["connectionVersionId"]))
        slot = str(resource_input["slot"])
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            resource = await session.scalar(
                select(ResourceDefinition).where(
                    ResourceDefinition.id == resource_id,
                    ResourceDefinition.tenant_id == tenant_id,
                    ResourceDefinition.project_id == project_id,
                )
            )
            version = await session.scalar(
                select(ConnectionVersion).where(
                    ConnectionVersion.id == connection_version_id,
                    ConnectionVersion.tenant_id == tenant_id,
                    ConnectionVersion.project_id == project_id,
                )
            )
            if resource is None or version is None:
                raise LookupError("bound resource snapshot is not available")
            connection = await session.scalar(
                select(Connection).where(
                    Connection.id == resource.connection_id,
                    Connection.tenant_id == tenant_id,
                    Connection.project_id == project_id,
                )
            )
            if connection is None or version.connection_id != connection.id:
                raise ValueError("bound resource connection version does not match")
            if connection.connector_ref != "connector://fake/files@1":
                raise ValueError(f"unsupported connector executor: {connection.connector_ref}")
            data = await FakeConnector().read(dict(resource.locator))
            content_hash = canonical_hash(data)
            bound_snapshot = await session.scalar(
                select(ResourceSnapshot).where(
                    ResourceSnapshot.evaluation_id == evaluation_id,
                    ResourceSnapshot.slot == slot,
                    ResourceSnapshot.resource_definition_id == resource.id,
                    ResourceSnapshot.snapshot_key == "bound-resource",
                )
            )
            if bound_snapshot is None:
                raise LookupError("bound resource provenance snapshot is missing")
            read_snapshot = await session.scalar(
                select(ResourceSnapshot).where(
                    ResourceSnapshot.evaluation_id == evaluation_id,
                    ResourceSnapshot.slot == slot,
                    ResourceSnapshot.snapshot_key == "read-result",
                )
            )
            if read_snapshot is not None and read_snapshot.content_hash != content_hash:
                raise ValueError(
                    "bound resource returned different content for the same evaluation"
                )
            if read_snapshot is None:
                session.add(
                    ResourceSnapshot(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        evaluation_id=evaluation_id,
                        slot=slot,
                        resource_definition_id=resource.id,
                        snapshot_key="read-result",
                        connection_version_id=version.id,
                        direction="INPUT",
                        observed_version=str(version.version),
                        content_hash=content_hash,
                        replayability="REFERENCE_ONLY",
                        metadata_json={
                            "effectId": effect_id,
                            "mappingConfiguration": dict(
                                resource_input.get("mappingConfiguration", {})
                            ),
                        },
                    )
                )
            return {
                "slot": slot,
                "resourceId": str(resource.id),
                "connectionVersionId": str(version.id),
                "contentHash": content_hash,
                "data": data,
            }


class BoundDocumentReadExecutor:
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
        descriptors = [dict(value) for value in input_value["documents"]]
        results: list[dict[str, Any]] = []
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            for descriptor in descriptors:
                version_id = UUID(str(descriptor["documentVersionId"]))
                snapshot = await session.scalar(
                    select(DocumentUsageSnapshot).where(
                        DocumentUsageSnapshot.evaluation_id == evaluation_id,
                        DocumentUsageSnapshot.business_document_version_id == version_id,
                        DocumentUsageSnapshot.tenant_id == tenant_id,
                        DocumentUsageSnapshot.project_id == project_id,
                    )
                )
                version = await session.scalar(
                    select(BusinessDocumentVersion).where(
                        BusinessDocumentVersion.id == version_id,
                        BusinessDocumentVersion.tenant_id == tenant_id,
                        BusinessDocumentVersion.project_id == project_id,
                    )
                )
                if snapshot is None or version is None:
                    raise LookupError("frozen document version is not available")
                if snapshot.sha256 != version.sha256 or snapshot.blob_id != version.blob_id:
                    raise ValueError("frozen document content identity does not match")
                document = await session.scalar(
                    select(BusinessDocument).where(
                        BusinessDocument.id == version.business_document_id,
                        BusinessDocument.tenant_id == tenant_id,
                        BusinessDocument.project_id == project_id,
                    )
                )
                if document is None:
                    raise LookupError("document metadata is not available")
                processing = await session.scalar(
                    select(DocumentProcessingResult)
                    .where(
                        DocumentProcessingResult.business_document_version_id == version.id,
                        DocumentProcessingResult.tenant_id == tenant_id,
                        DocumentProcessingResult.project_id == project_id,
                        DocumentProcessingResult.status.in_(("AVAILABLE", "CONFIRMED")),
                    )
                    .order_by(
                        DocumentProcessingResult.confirmed_at.desc().nullslast(),
                        DocumentProcessingResult.created_at.desc(),
                    )
                )
                results.append(
                    {
                        "documentId": str(document.id),
                        "documentVersionId": str(version.id),
                        "blobId": str(version.blob_id),
                        "name": document.name,
                        "category": document.category,
                        "filename": version.filename,
                        "mediaType": version.media_type,
                        "sizeBytes": version.size_bytes,
                        "version": version.version,
                        "sha256": version.sha256,
                        "data": dict(processing.result) if processing is not None else {},
                        "evidence": list(processing.evidence) if processing is not None else [],
                    }
                )
        return {
            "contentHash": canonical_hash(results),
            "documents": results,
            "effectId": effect_id,
        }


class PostEvaluationRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result = PostEvaluationResult.model_validate(input_value["result"])
        result_payload = result.model_dump(mode="json", by_alias=True)
        result_hash = canonical_hash(result_payload)
        report_payload = dict(input_value["report"])
        content = base64.b64decode(str(report_payload["contentBase64"]), validate=True)
        if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
            raise ValueError("post-evaluation report sha256 does not match content")
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
            item = await session.scalar(
                select(WorkItem)
                .where(
                    WorkItem.id == evaluation.work_item_id,
                    WorkItem.tenant_id == tenant_id,
                    WorkItem.project_id == project_id,
                )
                .with_for_update()
            )
            if item is None:
                raise LookupError("work item not found in capability scope")
            evaluation.result = result_payload
            evaluation.status = "SUCCEEDED"
            item.status = "COMPLETED" if result.passed else "IN_REVIEW"
            reports = (
                Report(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    work_item_id=item.id,
                    evaluation_id=evaluation.id,
                    format="JSON",
                    template_version=evaluation.report_template_version,
                    result_schema_version=evaluation.output_schema_version,
                    content=result_payload,
                    content_hash=result_hash,
                ),
                Report(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    work_item_id=item.id,
                    evaluation_id=evaluation.id,
                    format="PDF",
                    template_version=evaluation.report_template_version,
                    result_schema_version=evaluation.output_schema_version,
                    content=report_payload,
                    content_hash=str(report_payload["sha256"]),
                ),
            )
            session.add_all(reports)
            await session.flush()
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
                        "overallScore": result.overall_score,
                        "riskLevel": result.risk_level.value,
                    },
                )
            )
            for report in reports:
                session.add(
                    OutboxEvent(
                        id=uuid7(),
                        tenant_id=tenant_id,
                        aggregate_id=evaluation.id,
                        destination="nats",
                        partition_key=str(evaluation.id),
                        source_id=report.id,
                        type="report.created",
                        payload={
                            "reportId": str(report.id),
                            "evaluationId": str(evaluation.id),
                            "format": report.format,
                            "contentHash": report.content_hash,
                        },
                    )
                )
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=str(context.execution_id),
                action="evaluation.record-post-evaluation",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={"effectId": effect_id, "resultHash": result_hash},
            )
            return self._receipt(evaluation_id, effect_id, result_hash, recorded=True)


def capability_executors(sessions: async_sessionmaker[Any]) -> dict[str, Any]:
    recorder = EvaluationRecorderExecutor(sessions)
    return {
        "contract.document_read": document_read,
        "contract.rules_evaluate": rules_evaluate,
        "contract.cross_file_consistency": cross_file_consistency,
        "workbench.record_evaluation": recorder,
        "report.render": report_render,
        "contract.post_evaluation": post_evaluation_evaluate,
        "contract.post_evaluation_assemble": post_evaluation_assemble,
        "resource.read_bound": BoundResourceReadExecutor(sessions),
        "document.read_versions": BoundDocumentReadExecutor(sessions),
        "report.render_post_evaluation": post_evaluation_report_render,
        "workbench.record_post_evaluation": PostEvaluationRecorderExecutor(sessions),
    }
