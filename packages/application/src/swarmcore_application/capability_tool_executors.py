from __future__ import annotations

import base64
import hashlib
import json
from datetime import date
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
    Finding,
    OutboxEvent,
    Report,
    ResourceDefinition,
    ResourceSnapshot,
    WorkItem,
)
from swarmcore_persistence.repositories import canonical_hash

from .deviation_analysis import (
    aggregate_responsibility,
    build_deviation_trends,
    calculate_cost_deviation,
    calculate_time_deviation,
    compare_content_deviation,
    deviation_report_lines,
    finalize_deviation_result,
    merge_deviation_facts,
    validate_deviation_result,
)
from .invoice_assurance import (
    arithmetic_check,
    commercial_match,
    deduplicate,
    finalize_invoice_assurance,
    invoice_assurance_report_lines,
    official_verify,
    parse_invoice,
    party_check,
    payment_gate,
    read_business_snapshot,
    validate_invoice_assurance_result,
)
from .document_intelligence import (
    CrossFileRule,
    DocumentIntelligenceResult,
    evaluate_cross_file_consistency,
    pdf_report_payload,
    render_embedded_text_pdf,
    render_evidence_pdf,
    render_text_pdf,
)
from .formal_post_evaluation_report import (
    assess_document_readability,
    compose_formal_post_evaluation_report,
    finalize_formal_report_quality,
    render_formal_post_evaluation_pdf,
    verify_report_citations,
)
from .integrity import AttachmentInput, IntegrityRuleDocument, evaluate_integrity
from .post_evaluation import (
    PostEvaluationConfiguration,
    PostEvaluationResult,
    assemble_post_evaluation_payload,
    evaluate_post_evaluation,
    post_evaluation_report_lines,
)
from .post_evaluation_expanded import (
    aggregate_deviations,
    aggregate_risks,
    assure_invoices,
    calculate_timeline,
    check_document_coverage,
    check_evidence_consistency,
    finalize_expanded_result,
    merge_domain_analyses,
    normalize_post_evaluation_payload,
    reconcile_amounts,
    search_evidence,
    validate_expanded_result,
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
    payload = normalize_post_evaluation_payload(dict(input_value["payload"]))
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


async def evidence_search(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return search_evidence(
        [dict(value) for value in input_value["documents"]],
        domain=str(input_value["domain"]),
        keywords=[str(value) for value in input_value.get("keywords", [])],
        max_hits=int(input_value.get("maxHits", 12)),
    )


async def document_coverage_check(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return check_document_coverage(
        [dict(value) for value in input_value["documents"]],
        [dict(value) for value in input_value["requirements"]],
    )


async def post_evaluation_merge_domains(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return merge_domain_analyses(
        dict(input_value["basePayload"]),
        {key: dict(value) for key, value in dict(input_value["analyses"]).items()},
    )


async def post_evaluation_timeline(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return calculate_timeline(dict(input_value["payload"]))


async def post_evaluation_amounts(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return reconcile_amounts(dict(input_value["payload"]))


async def post_evaluation_invoices(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return assure_invoices(dict(input_value["payload"]))


async def post_evaluation_deviations(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return aggregate_deviations(dict(input_value["payload"]))


async def post_evaluation_risks(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return aggregate_risks(dict(input_value["payload"]))


async def evidence_consistency_check(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return check_evidence_consistency(
        dict(input_value["payload"]),
        [dict(value) for value in input_value.get("evidenceFacts", [])],
        [str(value) for value in input_value.get("declaredConflicts", [])],
    )


async def post_evaluation_finalize(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return finalize_expanded_result(
        score=dict(input_value["score"]),
        review=dict(input_value["review"]),
        narrative=dict(input_value["narrative"]),
        coverage=dict(input_value["coverage"]),
        consistency=dict(input_value["consistency"]),
        diagnostics=dict(input_value["diagnostics"]),
        provenance=dict(input_value["provenance"]),
    )


async def post_evaluation_report_render_v2(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = validate_expanded_result(dict(input_value["result"]))
    score_payload = {
        key: value
        for key, value in result.items()
        if key
        not in {
            "evidenceSummary",
            "review",
            "narrative",
            "diagnostics",
            "provenance",
        }
    }
    score_payload["schemaVersion"] = "schema://contract/post-evaluation-result@1"
    score = PostEvaluationResult.model_validate(score_payload)
    narrative = dict(result["narrative"])
    lines = [
        str(input_value["title"]),
        *post_evaluation_report_lines(score),
        "证据与复核",
        f"资料数量: {result['evidenceSummary']['documentCount']}",
        f"可读取数量: {result['evidenceSummary']['contentAvailableCount']}",
        f"是否需要复核: {'是' if result['reviewRequired'] else '否'}",
    ]
    recommendations = narrative.get("recommendations")
    if isinstance(recommendations, list) and recommendations:
        lines.append("改进建议")
        lines.extend(f"- {value}" for value in recommendations)
    return pdf_report_payload(render_text_pdf(tuple(lines)))


async def post_evaluation_report_render_v3(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    return await post_evaluation_report_render_v2(input_value, effect_id)


async def post_evaluation_readability_gate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return assess_document_readability(
        dict(input_value["coverage"]),
        formal_threshold=float(input_value.get("formalThreshold", 0.8)),
    )


async def post_evaluation_report_compose(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    approval = input_value.get("approval")
    return compose_formal_post_evaluation_report(
        title=str(input_value["title"]),
        result=dict(input_value["result"]),
        readability=dict(input_value["readability"]),
        section_drafts={
            key: dict(value)
            for key, value in dict(input_value.get("sectionDrafts") or {}).items()
            if isinstance(value, dict)
        },
        editorial=dict(input_value["editorial"]),
        review=dict(input_value["review"]),
        coverage=dict(input_value["coverage"]),
        consistency=dict(input_value["consistency"]),
        diagnostics=dict(input_value["diagnostics"]),
        approval=dict(approval) if isinstance(approval, dict) else None,
    )


async def post_evaluation_report_citations(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return verify_report_citations(
        dict(input_value["reportDocument"]),
        dict(input_value["sourceResult"]),
    )


async def post_evaluation_report_quality(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return finalize_formal_report_quality(
        source_result=dict(input_value["sourceResult"]),
        report_document=dict(input_value["reportDocument"]),
        citation_check=dict(input_value["citationCheck"]),
        model_review=dict(input_value["modelReview"]),
        readability=dict(input_value["readability"]),
    )


async def post_evaluation_report_render_v4(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = dict(input_value["result"])
    if result.get("schemaVersion") != "schema://contract/post-evaluation-result@3":
        raise ValueError("formal post-evaluation result schema version is required")
    return pdf_report_payload(render_formal_post_evaluation_pdf(result))


async def deviation_facts_merge(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    merged = merge_deviation_facts(
        dict(input_value["basePayload"]),
        {key: dict(value) for key, value in dict(input_value["analyses"]).items()},
    )
    configuration = input_value.get("configuration", {})
    if isinstance(configuration, dict):
        payload = dict(merged["payload"])
        for key in (
            "dimensions",
            "timezone",
            "currency",
            "trendWindow",
            "evidenceTopK",
            "thresholds",
            "approval",
            "approvalRules",
        ):
            if key in configuration:
                payload[key] = configuration[key]
        merged["payload"] = payload
    merged["facts"] = [
        _deviation_consistency_fact(item)
        for item in merged.get("facts", [])
        if isinstance(item, dict)
    ]
    return merged


def _deviation_consistency_fact(fact: dict[str, Any]) -> dict[str, Any]:
    serialized = json.dumps(
        fact, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    evidence_refs = next(
        (
            value
            for key in ("evidenceRefs", "evidenceVersionIds", "evidence")
            if isinstance((value := fact.get(key)), list)
        ),
        [
            value
            for key in ("immutableRef", "documentVersionId", "evidenceRef")
            if (value := fact.get(key))
        ],
    )
    return {
        "factId": str(
            fact.get("factId")
            or f"deviation-fact-{hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:20]}"
        ),
        "factType": str(
            fact.get("factType")
            or fact.get("type")
            or fact.get("category")
            or "DEVIATION_FACT"
        ),
        "value": (
            str(fact["value"])
            if isinstance(fact.get("value"), str | int | float | bool)
            else serialized
        ),
        "confidence": max(0.0, min(1.0, float(fact.get("confidence", 0.8)))),
        "evidenceRefs": [
            normalized
            for value in evidence_refs
            if (normalized := _leading_document_version_id(value))
        ],
    }


def _leading_document_version_id(value: Any) -> str | None:
    text = str(value).strip()
    if len(text) < 36:
        return None
    candidate = text[:36].lower()
    try:
        return str(UUID(candidate)) if candidate[8] == "-" else None
    except ValueError:
        return None


async def deviation_time_calculate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return calculate_time_deviation(dict(input_value["payload"]))


async def deviation_content_compare(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return compare_content_deviation(dict(input_value["payload"]))


async def deviation_cost_calculate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return calculate_cost_deviation(dict(input_value["payload"]))


async def deviation_trend_build(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return build_deviation_trends(
        dict(input_value["current"]),
        [dict(value) for value in input_value.get("history", [])],
    )


async def deviation_responsibility_aggregate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return aggregate_responsibility(
        dict(value) for value in input_value.get("proposals", [])
    )


async def deviation_finalize(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return finalize_deviation_result(
        payload=dict(input_value["payload"]),
        dimensions={
            key: dict(value)
            for key, value in dict(input_value["dimensions"]).items()
        },
        root_causes=[
            dict(value) for value in input_value.get("rootCauses", [])
        ],
        trends=dict(input_value["trends"]),
        responsibility=dict(input_value["responsibility"]),
        coverage=dict(input_value["coverage"]),
        evidence_review=dict(input_value["evidenceReview"]),
        narrative=dict(input_value["narrative"]),
        provenance=dict(input_value["provenance"]),
    )


async def deviation_report_render(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = validate_deviation_result(dict(input_value["result"]))
    return pdf_report_payload(render_embedded_text_pdf(deviation_report_lines(result)))


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
                        DocumentProcessingResult.status.in_(
                            ("READY", "AVAILABLE", "CONFIRMED", "REVIEW_REQUIRED")
                        ),
                    )
                    .order_by(
                        DocumentProcessingResult.confirmed_at.desc().nullslast(),
                        DocumentProcessingResult.created_at.desc(),
                    )
                )
                processing_data = (
                    _compact_processing_result(processing.result)
                    if processing is not None
                    else {}
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
                        "data": processing_data,
                        "evidence": list(processing.evidence) if processing is not None else [],
                    }
                )
        return {
            "contentHash": canonical_hash(results),
            "documents": results,
            "effectId": effect_id,
        }


def _compact_processing_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = dict(result)
    content = compact.get("content")
    if isinstance(content, dict):
        compact_content = {
            key: content[key]
            for key in (
                "textExcerpt",
                "tables",
                "sheets",
                "embeddedMetadata",
                "needsOcr",
                "warnings",
            )
            if key in content
        }
        text_excerpt = compact_content.get("textExcerpt")
        if isinstance(text_excerpt, str) and len(text_excerpt) > 2_000:
            compact_content["textExcerpt"] = text_excerpt[:2_000]
            compact_content["textTruncated"] = True
        compact["content"] = compact_content
    return compact


class PostEvaluationRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        raw_result = dict(input_value["result"])
        if raw_result.get("schemaVersion") == "schema://contract/post-evaluation-result@3":
            required = {"reportDocument", "reportQuality", "readabilityGate"}
            missing = required - raw_result.keys()
            if missing:
                raise ValueError(
                    "formal post-evaluation result is incomplete: "
                    + ", ".join(sorted(missing))
                )
            if not dict(raw_result["reportQuality"]).get("passed"):
                raise ValueError("formal post-evaluation report quality gate did not pass")
            result_payload = raw_result
        elif raw_result.get("schemaVersion") == "schema://contract/post-evaluation-result@2":
            result_payload = validate_expanded_result(raw_result)
        else:
            result = PostEvaluationResult.model_validate(raw_result)
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
            item.status = "COMPLETED" if bool(result_payload["passed"]) else "IN_REVIEW"
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
                        "overallScore": result_payload["overallScore"],
                        "riskLevel": result_payload["riskLevel"],
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


class DeviationHistoryReadExecutor:
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
        del effect_id
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        subject_id = str(input_value["subjectId"])
        baseline_hash = str(input_value["baselineHash"])
        configuration_hash = str(input_value["configurationHash"])
        limit = min(max(int(input_value.get("limit", 12)), 1), 50)
        as_of = date.fromisoformat(str(input_value["asOf"]))
        trend_window = str(input_value.get("trendWindow", "P6M"))
        months = (
            int(trend_window[1:-1])
            if trend_window.startswith("P")
            and trend_window.endswith("M")
            and trend_window[1:-1].isdigit()
            else 6
        )
        month_index = as_of.year * 12 + as_of.month - 1 - months
        earliest = date(month_index // 12, month_index % 12 + 1, 1)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            values = (
                await session.scalars(
                    select(Evaluation)
                    .where(
                        Evaluation.tenant_id == tenant_id,
                        Evaluation.project_id == project_id,
                        Evaluation.id != evaluation_id,
                        Evaluation.status == "SUCCEEDED",
                        Evaluation.result.is_not(None),
                    )
                    .order_by(Evaluation.created_at.desc())
                    .limit(100)
                )
            ).all()
        history: list[dict[str, Any]] = []
        for evaluation in values:
            result = evaluation.result
            if not isinstance(result, dict):
                continue
            if result.get("schemaVersion") != "schema://deviation-analysis/result@1":
                continue
            subject = result.get("subject", {})
            provenance = result.get("provenance", {})
            if (
                not isinstance(subject, dict)
                or str(subject.get("subjectId")) != subject_id
                or not isinstance(provenance, dict)
                or provenance.get("baselineHash") != baseline_hash
                or provenance.get("configurationHash") != configuration_hash
            ):
                continue
            result_as_of = result.get("asOf")
            if not isinstance(result_as_of, str):
                continue
            try:
                if date.fromisoformat(result_as_of) < earliest:
                    continue
            except ValueError:
                continue
            dimensions = result.get("dimensions", {})
            time_metrics = (
                dimensions.get("TIME", {}).get("metrics", {})
                if isinstance(dimensions, dict)
                else {}
            )
            content_metrics = (
                dimensions.get("CONTENT", {}).get("metrics", {})
                if isinstance(dimensions, dict)
                else {}
            )
            cost_metrics = (
                dimensions.get("COST", {}).get("metrics", {})
                if isinstance(dimensions, dict)
                else {}
            )
            history.append(
                {
                    "evaluationId": str(evaluation.id),
                    "subjectId": subject_id,
                    "asOf": result.get("asOf"),
                    "baselineHash": baseline_hash,
                    "configurationHash": configuration_hash,
                    "timeVarianceDays": time_metrics.get("maximumDelayDays"),
                    "contentVarianceRate": content_metrics.get("contentVarianceRate"),
                    "costVarianceRate": cost_metrics.get("costVarianceRate"),
                }
            )
            if len(history) >= limit:
                break
        return {"items": history, "count": len(history)}


class DeviationRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result_payload = validate_deviation_result(dict(input_value["result"]))
        result_hash = canonical_hash(result_payload)
        report_payload = dict(input_value["report"])
        content = base64.b64decode(str(report_payload["contentBase64"]), validate=True)
        if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
            raise ValueError("deviation-analysis report sha256 does not match content")
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
            item.status = (
                "COMPLETED"
                if result_payload["qualityStatus"] == "READY"
                else "IN_REVIEW"
            )
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
            existing_findings = {
                value.rule_key: value
                for value in (
                    await session.scalars(
                        select(Finding)
                        .where(Finding.work_item_id == item.id)
                        .with_for_update()
                    )
                ).all()
            }
            for finding_payload in result_payload.get("findings", []):
                if not isinstance(finding_payload, dict):
                    continue
                code = str(finding_payload.get("code") or "DEVIATION_REVIEW")
                rule_key = f"deviation-analysis:{code}"
                finding = existing_findings.get(rule_key)
                dimension = str(
                    finding_payload.get("dimension") or "DEVIATION_ANALYSIS"
                )
                detail = str(
                    finding_payload.get("rationale")
                    or finding_payload.get("status")
                    or "偏差分析关注项"
                )
                evidence = {
                    "evidenceRefs": list(finding_payload.get("evidenceRefs", [])),
                    "resultHash": result_hash,
                }
                if finding is None:
                    finding = Finding(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        work_item_id=item.id,
                        evaluation_id=evaluation.id,
                        rule_key=rule_key,
                        code=code,
                        category=dimension,
                        severity=(
                            "HIGH"
                            if finding_payload.get("material")
                            or finding_payload.get("status") == "CONFLICTED"
                            else "MEDIUM"
                        ),
                        status="OPEN",
                        title=f"{dimension} 偏差关注项",
                        detail=detail,
                        evidence=evidence,
                    )
                    session.add(finding)
                    existing_findings[rule_key] = finding
                else:
                    finding.evaluation_id = evaluation.id
                    finding.category = dimension
                    finding.detail = detail
                    finding.evidence = evidence
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
                        "qualityStatus": result_payload["qualityStatus"],
                        "reviewRequired": result_payload["reviewRequired"],
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
                action="evaluation.record-deviation-analysis",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={"effectId": effect_id, "resultHash": result_hash},
            )
            return self._receipt(evaluation_id, effect_id, result_hash, recorded=True)


def _invoice_original_content(input_value: dict[str, Any]) -> tuple[Any, str | None, str | None]:
    if "content" in input_value and input_value["content"] is not None:
        return (
            input_value["content"],
            input_value.get("mediaType"),
            input_value.get("documentVersionId"),
        )
    payload = input_value.get("payload")
    if isinstance(payload, dict):
        if isinstance(payload.get("invoiceFactSet"), dict):
            return payload["invoiceFactSet"], "application/json", None
        if payload.get("invoiceContent") is not None:
            return (
                payload["invoiceContent"],
                payload.get("invoiceMediaType") or "application/xml",
                payload.get("invoiceDocumentVersionId"),
            )
    documents = input_value.get("documents")
    if isinstance(documents, list):
        preferred = [
            item
            for item in documents
            if isinstance(item, dict)
            and str(item.get("category") or "").upper()
            in {"INVOICE_ORIGINAL", "INVOICE"}
        ] or [item for item in documents if isinstance(item, dict)]
        for document in preferred:
            version_id = document.get("documentVersionId")
            media_type = document.get("mediaType")
            data = document.get("data")
            if isinstance(data, dict):
                content = data.get("content")
                if isinstance(content, dict):
                    for key in ("text", "rawText", "xml", "markdown"):
                        if content.get(key):
                            return content[key], media_type, str(version_id) if version_id else None
                for key in ("text", "rawText", "xml", "extractedText"):
                    if data.get(key):
                        return data[key], media_type, str(version_id) if version_id else None
                if data.get("invoiceFactSet"):
                    return data["invoiceFactSet"], "application/json", (
                        str(version_id) if version_id else None
                    )
            if document.get("text"):
                return document["text"], media_type, str(version_id) if version_id else None
    raise ValueError("invoice original content is not available for parsing")


def _flatten_invoice_rules(rule_results: Any) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    if isinstance(rule_results, list):
        flat.extend(dict(item) for item in rule_results if isinstance(item, dict))
        return flat
    if not isinstance(rule_results, dict):
        return flat
    for value in rule_results.values():
        if isinstance(value, list):
            flat.extend(dict(item) for item in value if isinstance(item, dict))
        elif isinstance(value, dict):
            nested = value.get("ruleResults")
            if isinstance(nested, list):
                flat.extend(dict(item) for item in nested if isinstance(item, dict))
            else:
                flat.append(dict(value))
    return flat


async def invoice_parse(input_value: dict[str, Any], effect_id: str, context: Any) -> dict[str, Any]:
    del effect_id, context
    content, media_type, document_version_id = _invoice_original_content(input_value)
    fact_set = parse_invoice(
        content,
        media_type=media_type,
        document_version_id=document_version_id,
    )
    return {
        "invoiceFactSet": fact_set,
        "needsFieldConfirmation": bool(fact_set.get("needsFieldConfirmation")),
        "qualityFlags": list(fact_set.get("qualityFlags") or []),
    }


async def invoice_official_verify(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    payload = input_value.get("payload") if isinstance(input_value.get("payload"), dict) else {}
    configuration = (
        input_value.get("configuration")
        if isinstance(input_value.get("configuration"), dict)
        else {}
    )
    mode = (
        input_value.get("verificationMode")
        or payload.get("verificationMode")
        or configuration.get("verificationMode")
        or "HUMAN_ASSISTED"
    )
    human_receipt = input_value.get("humanVerification") or payload.get("humanVerification")
    connector_result = input_value.get("connectorResult") or payload.get("connectorResult")
    return official_verify(
        dict(input_value["invoiceFactSet"]),
        mode=str(mode),
        human_receipt=human_receipt if isinstance(human_receipt, dict) else None,
        connector_result=connector_result if isinstance(connector_result, dict) else None,
    )


async def business_snapshot_read(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    payload = dict(input_value.get("payload") or {})
    if input_value.get("documents") and "documents" not in payload:
        payload["documents"] = input_value["documents"]
    if input_value.get("subjects") and "subjects" not in payload:
        payload["subjects"] = input_value["subjects"]
    if input_value.get("asOf") and "asOf" not in payload:
        payload["asOf"] = input_value["asOf"]
    return read_business_snapshot(payload)


async def invoice_arithmetic_check(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    rules = arithmetic_check(dict(input_value["invoiceFactSet"]))
    return {"ruleResults": rules, "status": "FAIL" if any(r["status"] == "FAIL" for r in rules) else "PASS"}


async def invoice_party_check(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    snapshot = input_value.get("businessSnapshot")
    vendor = None
    buyer_tax_id = None
    if isinstance(snapshot, dict):
        vendor = snapshot.get("vendor") if isinstance(snapshot.get("vendor"), dict) else None
        configuration = input_value.get("configuration")
        if isinstance(configuration, dict):
            buyer_tax_id = configuration.get("buyerTaxId")
        buyer_tax_id = buyer_tax_id or snapshot.get("buyerTaxId")
    rules = party_check(
        dict(input_value["invoiceFactSet"]),
        vendor,
        buyer_tax_id=str(buyer_tax_id) if buyer_tax_id else None,
    )
    return {
        "ruleResults": rules,
        "status": "FAIL" if any(r.get("status") == "FAIL" for r in rules) else "PASS",
    }


async def invoice_deduplicate(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    snapshot = input_value.get("businessSnapshot")
    ledger = None
    if isinstance(snapshot, dict):
        ledger = snapshot.get("apLedger")
    return deduplicate(dict(input_value["invoiceFactSet"]), ledger)


async def invoice_commercial_match(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    candidates = input_value.get("matchCandidates")
    return commercial_match(
        dict(input_value["invoiceFactSet"]),
        dict(input_value.get("businessSnapshot") or {}),
        candidates if isinstance(candidates, list) else None,
    )


async def invoice_payment_gate(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    nested = input_value.get("ruleResults")
    arithmetic = []
    parties = []
    duplication: dict[str, Any] = {}
    if isinstance(nested, dict):
        arithmetic_block = nested.get("arithmetic")
        parties_block = nested.get("parties")
        duplication_block = nested.get("duplication")
        if isinstance(arithmetic_block, dict):
            arithmetic = list(arithmetic_block.get("ruleResults") or [])
        elif isinstance(arithmetic_block, list):
            arithmetic = arithmetic_block
        if isinstance(parties_block, dict):
            parties = list(parties_block.get("ruleResults") or [])
        elif isinstance(parties_block, list):
            parties = parties_block
        if isinstance(duplication_block, dict):
            duplication = duplication_block
    snapshot = input_value.get("businessSnapshot") if isinstance(input_value.get("businessSnapshot"), dict) else {}
    return payment_gate(
        {
            "verification": input_value.get("verification") or {},
            "duplication": duplication,
            "ruleResults": [*arithmetic, *parties],
            "commercialMatch": input_value.get("matchResults") or {},
            "budget": snapshot.get("budget") if isinstance(snapshot, dict) else {},
        }
    )


async def invoice_finalize(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    nested = input_value.get("ruleResults")
    duplication: dict[str, Any] = {}
    rules = _flatten_invoice_rules(nested)
    if isinstance(nested, dict) and isinstance(nested.get("duplication"), dict):
        duplication = nested["duplication"]
        rules.extend(_flatten_invoice_rules(duplication.get("ruleResults")))
    payload = input_value.get("payload") if isinstance(input_value.get("payload"), dict) else {}
    evidence_review = (
        input_value.get("evidenceReview")
        if isinstance(input_value.get("evidenceReview"), dict)
        else {}
    )
    narrative = evidence_review.get("narrative") if isinstance(evidence_review, dict) else None
    business_snapshot = input_value.get("businessSnapshot")
    if not isinstance(business_snapshot, dict):
        business_snapshot = {
            "hash": input_value.get("businessSnapshotHash"),
            **(payload.get("businessSnapshot") or {}),
        }
    approvals_raw = input_value.get("approvals")
    approvals: list[dict[str, Any]] = []
    if isinstance(approvals_raw, dict):
        for key, value in approvals_raw.items():
            if isinstance(value, dict):
                approvals.append({"source": key, **value})
    elif isinstance(approvals_raw, list):
        approvals = [dict(item) for item in approvals_raw if isinstance(item, dict)]
    return finalize_invoice_assurance(
        fact_set=dict(input_value["invoiceFactSet"]),
        verification=dict(input_value.get("verification") or {}),
        business_snapshot=business_snapshot,
        rule_results=rules,
        match_result=dict(input_value.get("matchResults") or {}),
        duplication=duplication,
        gate_result=dict(input_value.get("gateResults") or {}),
        narrative=narrative if isinstance(narrative, dict) else None,
        provenance=dict(input_value.get("provenance") or {}),
        approvals=approvals,
        title=str(payload.get("title") or "发票一致性校验"),
        as_of=payload.get("asOf"),
    )


async def invoice_assurance_report_render(
    input_value: dict[str, Any], effect_id: str, context: Any
) -> dict[str, Any]:
    del effect_id, context
    result = validate_invoice_assurance_result(dict(input_value["result"]))
    return pdf_report_payload(render_embedded_text_pdf(invoice_assurance_report_lines(result)))


class InvoiceAssuranceRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result_payload = validate_invoice_assurance_result(dict(input_value["result"]))
        result_hash = str(result_payload.get("resultHash") or canonical_hash(result_payload))
        report_payload = dict(input_value["report"])
        content = base64.b64decode(str(report_payload["contentBase64"]), validate=True)
        if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
            raise ValueError("invoice-assurance report sha256 does not match content")
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
                if canonical_hash(evaluation.result) != canonical_hash(result_payload):
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
            outcome = str(result_payload.get("outcome") or "")
            item.status = "COMPLETED" if outcome == "PAYMENT_READY" else "IN_REVIEW"
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
            existing_findings = {
                value.rule_key: value
                for value in (
                    await session.scalars(
                        select(Finding)
                        .where(Finding.work_item_id == item.id)
                        .with_for_update()
                    )
                ).all()
            }
            for finding_payload in result_payload.get("findings", []):
                if not isinstance(finding_payload, dict):
                    continue
                code = str(finding_payload.get("code") or "INVOICE_REVIEW")
                rule_key = f"invoice-assurance:{code}"
                finding = existing_findings.get(rule_key)
                severity = str(finding_payload.get("severity") or "MEDIUM")
                detail = str(
                    finding_payload.get("summary")
                    or finding_payload.get("detail")
                    or "发票一致性校验关注项"
                )
                evidence = {
                    "evidenceRefs": list(finding_payload.get("evidenceRefs", [])),
                    "resultHash": result_hash,
                    "blocking": bool(finding_payload.get("blocking")),
                }
                if finding is None:
                    finding = Finding(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        work_item_id=item.id,
                        evaluation_id=evaluation.id,
                        rule_key=rule_key,
                        code=code,
                        category=str(finding_payload.get("dimension") or "INVOICE_ASSURANCE"),
                        severity=severity,
                        status="OPEN",
                        title=f"发票校验 · {code}",
                        detail=detail,
                        evidence=evidence,
                    )
                    session.add(finding)
                    existing_findings[rule_key] = finding
                else:
                    finding.evaluation_id = evaluation.id
                    finding.detail = detail
                    finding.severity = severity
                    finding.evidence = evidence
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
                    type="capability.invoice-assurance.assessment.completed",
                    payload={
                        "evaluationId": str(evaluation.id),
                        "effectId": effect_id,
                        "resultHash": result_hash,
                        "outcome": outcome,
                        "reviewRequired": bool(result_payload.get("reviewRequired")),
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
                action="evaluation.record-invoice-assurance",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={"effectId": effect_id, "resultHash": result_hash, "outcome": outcome},
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
        "evidence.search": evidence_search,
        "document.coverage_check": document_coverage_check,
        "contract.post_evaluation_merge_domains": post_evaluation_merge_domains,
        "contract.post_evaluation_timeline": post_evaluation_timeline,
        "finance.post_evaluation_amounts": post_evaluation_amounts,
        "invoice.post_evaluation_assurance": post_evaluation_invoices,
        "deviation.post_evaluation_aggregate": post_evaluation_deviations,
        "risk.post_evaluation_aggregate": post_evaluation_risks,
        "evidence.consistency_check": evidence_consistency_check,
        "contract.post_evaluation_finalize": post_evaluation_finalize,
        "report.render_post_evaluation": post_evaluation_report_render,
        "report.render_post_evaluation_v2": post_evaluation_report_render_v2,
        "report.render_post_evaluation_v3": post_evaluation_report_render_v3,
        "document.post_evaluation_readability_gate": post_evaluation_readability_gate,
        "report.compose_post_evaluation": post_evaluation_report_compose,
        "report.verify_post_evaluation_citations": post_evaluation_report_citations,
        "report.check_post_evaluation_quality": post_evaluation_report_quality,
        "report.render_post_evaluation_v4": post_evaluation_report_render_v4,
        "workbench.record_post_evaluation": PostEvaluationRecorderExecutor(sessions),
        "deviation.facts_merge": deviation_facts_merge,
        "deviation.time_calculate": deviation_time_calculate,
        "deviation.content_compare": deviation_content_compare,
        "deviation.cost_calculate": deviation_cost_calculate,
        "deviation.history_read": DeviationHistoryReadExecutor(sessions),
        "deviation.trend_build": deviation_trend_build,
        "deviation.responsibility_aggregate": deviation_responsibility_aggregate,
        "deviation.finalize": deviation_finalize,
        "report.render_deviation_analysis": deviation_report_render,
        "workbench.record_deviation_analysis": DeviationRecorderExecutor(sessions),
        "invoice.parse": invoice_parse,
        "invoice.official_verify": invoice_official_verify,
        "business.snapshot_read": business_snapshot_read,
        "invoice.deduplicate": invoice_deduplicate,
        "invoice.arithmetic_check": invoice_arithmetic_check,
        "invoice.party_check": invoice_party_check,
        "invoice.commercial_match": invoice_commercial_match,
        "invoice.payment_gate": invoice_payment_gate,
        "invoice.finalize": invoice_finalize,
        "report.render_invoice_assurance": invoice_assurance_report_render,
        "workbench.record_invoice_assurance": InvoiceAssuranceRecorderExecutor(sessions),
    }
