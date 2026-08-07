from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import re
from asyncio import sleep, to_thread
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository, tenant_transaction
from swarmcore_persistence.models import (
    Artifact,
    BlobObject,
    BusinessDocument,
    BusinessDocumentVersion,
    CalibrationEvidenceSnapshot,
    CalibrationFallbackRecord,
    CalibrationQualityEvaluation,
    CalibrationRouteDecision,
    Connection,
    ConnectionVersion,
    DocumentProcessingEvent,
    DocumentProcessingResult,
    DocumentProcessingRun,
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

from .contract_performance import (
    apply_approved_changes,
    build_schedule,
    calculate_status,
    contract_performance_report_lines,
    finalize_contract_performance,
    match_evidence,
    normalize_plan,
    validate_contract_performance_result,
)
from .deviation_analysis import (
    SCHEMA_VERSION as DEVIATION_SCHEMA_VERSION,
)
from .deviation_analysis import (
    aggregate_responsibility,
    build_deviation_trends,
    calculate_cost_deviation,
    calculate_time_deviation,
    compare_content_deviation,
    deviation_report_lines,
    finalize_deviation_result,
    merge_deviation_facts,
    upstream_performance_analysis,
    validate_deviation_result,
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
from .document_structuring import (
    apply_human_review,
    document_package_artifacts,
    finalize_document_structuring,
    prepare_document_structuring,
    select_document_structuring_analysis,
    select_document_structuring_review,
)
from .formal_post_evaluation_report import (
    assess_document_readability,
    compose_formal_post_evaluation_report,
    finalize_formal_report_quality,
    render_formal_post_evaluation_pdf,
    verify_report_citations,
)
from .integrity import (
    AttachmentInput,
    IntegrityRuleDocument,
    evaluate_integrity,
    finalize_integrity_result,
)
from .invoice_assurance import (
    arithmetic_check,
    commercial_match,
    deduplicate,
    enterprise_public_status_check,
    finalize_invoice_assurance,
    invoice_assurance_report_lines,
    official_verify,
    parse_invoice,
    party_check,
    payment_gate,
    read_business_snapshot,
    validate_invoice_assurance_result,
)
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
from .procurement_supplier_risk import (
    calculate_supplier_performance,
    collect_risk_observations,
    compare_procurement_clauses,
    decide_supplier_risk,
    diff_supplier_risk_snapshots,
    finalize_procurement_supplier_risk,
    validate_procurement_supplier_risk_result,
)
from .procurement_supplier_risk_service import ProcurementSupplierRiskService
from .quality_benchmark import (
    evaluate_quality_benchmark,
    quality_benchmark_report_lines,
)
from .resource_plane import FakeConnector
from .swarm_calibration import (
    GitHubEvidenceClient,
    RepositorySandboxVerifier,
    build_route_decision,
    calibration_report_lines,
    finalize_calibration_result,
    freeze_evidence,
    score_quality,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


_NO_REDIRECT_OPENER = build_opener(_NoRedirectHandler())


def urlopen(request: Request, *, timeout: float) -> Any:
    """Open allowlisted capability sources without automatic redirects."""
    return _NO_REDIRECT_OPENER.open(request, timeout=timeout)


def _nested_value(value: Any, path: str) -> Any:
    current = value
    for part in (item for item in path.split(".") if item):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _validate_supplier_risk_response_url(
    response: Any,
    *,
    requested_url: str,
    allowed_hosts: frozenset[str],
) -> None:
    geturl = getattr(response, "geturl", None)
    final_url = str(geturl()) if callable(geturl) else requested_url
    parsed = urlparse(final_url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in allowed_hosts:
        raise ValueError("supplier risk provider redirected to a disallowed host")


def _supplier_risk_http_fetch(
    source: dict[str, Any],
    supplier: dict[str, Any],
    as_of: str,
    *,
    allowed_hosts: frozenset[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    endpoint = str(source.get("endpoint") or "").strip()
    parsed = urlparse(endpoint)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in allowed_hosts:
        raise ValueError("supplier risk endpoint is not an allowed HTTPS host")
    method = str(source.get("method") or "GET").upper()
    if method not in {"GET", "POST"}:
        raise ValueError("supplier risk endpoint method must be GET or POST")
    query = {
        **dict(source.get("query") or {}),
        "creditCode": str(supplier.get("creditCode") or ""),
        "name": str(supplier.get("name") or ""),
        "asOf": as_of,
    }
    body: bytes | None = None
    source_headers = {
        str(key): str(value) for key, value in dict(source.get("headers") or {}).items()
    }
    forbidden_headers = {
        key
        for key in source_headers
        if key.casefold() in {"authorization", "x-api-key", "api-key", "cookie"}
    }
    if forbidden_headers:
        raise ValueError(
            "supplier risk credentials must use credentials secretRef and credentialHeaderMap"
        )
    headers = {
        "Accept": "application/json",
        "User-Agent": "SwarmCore-SupplierRisk/1.0",
        **source_headers,
    }
    credentials = source.get("credentials")
    header_map = source.get("credentialHeaderMap")
    if isinstance(credentials, dict) and isinstance(header_map, dict):
        for credential_key, header_name in header_map.items():
            materialized = credentials.get(str(credential_key))
            if materialized is not None:
                headers[str(header_name)] = str(materialized)
    if method == "GET":
        separator = "&" if parsed.query else "?"
        endpoint = f"{endpoint}{separator}{urlencode(query)}"
    else:
        body_payload = {**dict(source.get("body") or {}), **query}
        body = json.dumps(body_payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(endpoint, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            _validate_supplier_risk_response_url(
                response,
                requested_url=endpoint,
                allowed_hosts=allowed_hosts,
            )
            raw = response.read(10 * 1024 * 1024 + 1)
            if len(raw) > 10 * 1024 * 1024:
                raise ValueError("supplier risk provider response exceeds 10 MiB")
            payload = json.loads(raw)
    except HTTPError as exc:
        raise RuntimeError(f"supplier risk provider HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("supplier risk provider is unavailable") from exc
    records = _nested_value(payload, str(source.get("recordsPath") or "records"))
    if not isinstance(records, list):
        raise ValueError("supplier risk provider recordsPath did not resolve to an array")
    fetched_at = datetime.now(UTC).isoformat()
    response_hash = hashlib.sha256(raw).hexdigest()
    normalized_records = []
    for item in records:
        if not isinstance(item, dict):
            continue
        normalized_records.append(
            {
                **item,
                "evidenceRefs": [
                    *list(item.get("evidenceRefs") or []),
                    {
                        "sourceUrl": endpoint.split("?", 1)[0],
                        "fetchedAt": fetched_at,
                        "responseHash": response_hash,
                    },
                ],
            }
        )
    return {
        "sourceRef": str(source.get("sourceRef") or hostname),
        "status": "SUCCEEDED",
        "fetchedAt": fetched_at,
        "records": normalized_records,
    }


class _CcgpBlacklistParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, Any]] = []
        self._in_row = False
        self._in_cell = False
        self._cells: list[str] = []
        self._cell_parts: list[str] = []
        self._record_id: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "tr" and "trShow" in str(attributes.get("class") or "").split():
            self._in_row = True
            self._cells = []
            self._record_id = None
        elif self._in_row and tag == "td":
            self._in_cell = True
            self._cell_parts = []
        elif self._in_row and tag == "a":
            match = re.search(r"detail\('([^']+)'\)", str(attributes.get("onclick") or ""))
            if match:
                self._record_id = match.group(1)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._in_row and tag == "td":
            value = " ".join("".join(self._cell_parts).split())
            self._cells.append(value)
            self._in_cell = False
            self._cell_parts = []
        elif self._in_row and tag == "tr":
            if len(self._cells) >= 10:
                self.rows.append(
                    {
                        "ordinal": self._cells[0],
                        "supplierName": self._cells[1],
                        "creditCode": self._cells[2],
                        "address": self._cells[3],
                        "violation": self._cells[4],
                        "punishment": self._cells[5],
                        "legalBasis": self._cells[6],
                        "punishedAt": self._cells[7],
                        "publishedAt": self._cells[8],
                        "enforcementAuthority": self._cells[9],
                        "sourceRecordId": self._record_id,
                    }
                )
            self._in_row = False
            self._in_cell = False


def _ccgp_ban_period(punished_at: str, punishment: str) -> tuple[str | None, str | None]:
    start = _supplier_risk_date(punished_at)
    if start is None or "禁止参加政府采购活动" not in punishment:
        return None, None
    years_match = re.search(r"([一二三123])年", punishment)
    months_match = re.search(r"([一二三四五六七八九十\d]+)个?月", punishment)
    years = _simple_chinese_number(years_match.group(1)) if years_match else 0
    if not years and not months_match:
        return start.isoformat(), None
    months = _simple_chinese_number(months_match.group(1)) if months_match else 0
    total_month = start.month - 1 + years * 12 + months
    target_year = start.year + total_month // 12
    target_month = total_month % 12 + 1
    for day_value in range(start.day, 0, -1):
        try:
            end = date(target_year, target_month, day_value)
            return start.isoformat(), end.isoformat()
        except ValueError:
            continue
    return start.isoformat(), None


def _simple_chinese_number(value: str) -> int:
    values = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if value.isdecimal():
        return int(value)
    if value in values:
        return values[value]
    if "十" in value:
        left, right = value.split("十", 1)
        tens = values.get(left, 1) if left else 1
        units = values.get(right, 0) if right else 0
        return tens * 10 + units
    raise ValueError("unsupported Chinese number")


def _supplier_risk_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _supplier_risk_ccgp_fetch(
    source: dict[str, Any],
    supplier: dict[str, Any],
    as_of: str,
    *,
    allowed_hosts: frozenset[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    endpoint = str(source.get("endpoint") or "https://www.ccgp.gov.cn/cr/list")
    parsed = urlparse(endpoint)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in allowed_hosts:
        raise ValueError("CCGP endpoint is not an allowed HTTPS host")
    credit_code = str(supplier.get("creditCode") or "").strip().upper()
    if not credit_code:
        raise ValueError("supplier.creditCode is required for CCGP lookup")
    body = urlencode({"orgCode": credit_code, "searchType": "1", "gp": "1"}).encode()
    request = Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SwarmCore-SupplierRisk/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            _validate_supplier_risk_response_url(
                response,
                requested_url=endpoint,
                allowed_hosts=allowed_hosts,
            )
            raw = response.read(10 * 1024 * 1024 + 1)
    except HTTPError as exc:
        raise RuntimeError(f"CCGP supplier risk HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("CCGP supplier risk source is unavailable") from exc
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("CCGP supplier risk response exceeds 10 MiB")
    text = raw.decode("utf-8", errors="replace")
    parser = _CcgpBlacklistParser()
    parser.feed(text)
    fetched_at = datetime.now(UTC).isoformat()
    response_hash = hashlib.sha256(raw).hexdigest()
    query_date = _supplier_risk_date(as_of) or datetime.now(UTC).date()
    records = []
    for row in parser.rows:
        if str(row["creditCode"]).strip().upper() != credit_code:
            continue
        effective_from, effective_to = _ccgp_ban_period(
            str(row["punishedAt"]), str(row["punishment"])
        )
        active = bool(
            effective_from
            and date.fromisoformat(effective_from) <= query_date
            and (effective_to is None or query_date <= date.fromisoformat(effective_to))
        )
        detail_url = (
            f"https://www.ccgp.gov.cn/cr/list/detail?id={row['sourceRecordId']}"
            if row.get("sourceRecordId")
            else endpoint
        )
        records.append(
            {
                **row,
                "riskType": (
                    "GOVERNMENT_PROCUREMENT_BAN"
                    if "禁止参加政府采购活动" in str(row["punishment"])
                    else "GOVERNMENT_PROCUREMENT_VIOLATION"
                ),
                "effectiveFrom": effective_from,
                "effectiveTo": effective_to,
                "active": active,
                "contentHash": canonical_hash(row),
                "evidenceRefs": [
                    {
                        "sourceUrl": detail_url,
                        "queryUrl": endpoint,
                        "fetchedAt": fetched_at,
                        "responseHash": response_hash,
                    }
                ],
            }
        )
    return {
        "sourceRef": str(source.get("sourceRef") or "official://ccgp/serious-illegal"),
        "status": "SUCCEEDED",
        "fetchedAt": fetched_at,
        "records": records,
    }


class SupplierRiskCollectExecutor:
    def __init__(
        self,
        *,
        allowed_hosts: tuple[str, ...] = (
            "www.ccgp.gov.cn",
            "api.qichacha.com",
            "open.api.tianyancha.com",
        ),
        timeout_seconds: int = 30,
    ) -> None:
        self._allowed_hosts = frozenset(item.lower() for item in allowed_hosts)
        self._timeout_seconds = timeout_seconds

    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        del effect_id, context
        supplier = dict(input_value.get("supplier") or {})
        as_of = str(input_value.get("asOf") or datetime.now(UTC).date().isoformat())
        normalized_sources: list[dict[str, Any]] = []
        for raw in input_value.get("sources") or []:
            if not isinstance(raw, dict):
                continue
            source = dict(raw)
            if str(source.get("kind") or "").upper() == "CCGP_SERIOUS_ILLEGAL":
                try:
                    source = await to_thread(
                        _supplier_risk_ccgp_fetch,
                        source,
                        supplier,
                        as_of,
                        allowed_hosts=self._allowed_hosts,
                        timeout_seconds=self._timeout_seconds,
                    )
                except (RuntimeError, ValueError) as exc:
                    source = {
                        "sourceRef": str(raw.get("sourceRef") or "official://ccgp/serious-illegal"),
                        "status": "FAILED",
                        "fetchedAt": datetime.now(UTC).isoformat(),
                        "errorCode": type(exc).__name__.upper(),
                    }
            elif source.get("endpoint"):
                try:
                    source = await to_thread(
                        _supplier_risk_http_fetch,
                        source,
                        supplier,
                        as_of,
                        allowed_hosts=self._allowed_hosts,
                        timeout_seconds=self._timeout_seconds,
                    )
                except (RuntimeError, ValueError) as exc:
                    source = {
                        "sourceRef": str(raw.get("sourceRef") or "unknown"),
                        "status": "FAILED",
                        "fetchedAt": datetime.now(UTC).isoformat(),
                        "errorCode": type(exc).__name__.upper(),
                    }
            normalized_sources.append(source)
        return collect_risk_observations(
            {"supplier": supplier, "sources": normalized_sources, "asOf": as_of}
        )

    async def healthy(self) -> bool:
        return bool(self._allowed_hosts)


async def procurement_consistency_compare(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return compare_procurement_clauses(input_value)


async def supplier_performance_calculate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return calculate_supplier_performance(input_value)


async def supplier_risk_decide(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return decide_supplier_risk(input_value)


async def supplier_history_diff(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    previous = input_value.get("previous")
    return diff_supplier_risk_snapshots(
        dict(previous) if isinstance(previous, dict) else None,
        dict(input_value.get("current") or {}),
    )


async def procurement_supplier_risk_finalize(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return finalize_procurement_supplier_risk(input_value)


def _procurement_supplier_risk_report_lines(result: dict[str, Any]) -> list[str]:
    consistency = dict(result.get("consistency") or {})
    risk = dict(result.get("risk") or {})
    performance = dict(result.get("performance") or {})
    counts = dict(consistency.get("counts") or {})
    lines = [
        "招采一致性与供应商风控报告",
        f"供应商: {(result.get('supplier') or {}).get('name') or '-'}",
        f"统一社会信用代码: {(result.get('supplier') or {}).get('creditCode') or '-'}",
        f"评估日期: {result.get('asOf') or '-'}",
        f"签署建议: {result.get('decision') or '-'}",
        f"风险等级: {result.get('riskLevel') or '-'}",
        (
            "差异统计: "
            f"阻断 {counts.get('BLOCKER', 0)} / 高 {counts.get('HIGH', 0)} / "
            f"中 {counts.get('MEDIUM', 0)} / 低 {counts.get('LOW', 0)}"
        ),
        f"外部风险分: {risk.get('externalRiskScore', '-')}",
        f"综合风险分: {risk.get('overallRiskScore', '-')}",
        f"绩效分: {performance.get('score', '-')}",
        f"绩效覆盖率: {performance.get('coverage', '-')}%",
        "",
        "重大差异",
    ]
    for finding in consistency.get("findings") or []:
        if not isinstance(finding, dict) or finding.get("severity") not in {
            "BLOCKER",
            "HIGH",
        }:
            continue
        lines.append(
            f"[{finding.get('severity')}] {finding.get('title')}: {finding.get('summary')}"
        )
    lines.extend(("", "硬性门禁"))
    for gate in risk.get("hardGates") or []:
        if isinstance(gate, dict):
            lines.append(
                f"{gate.get('code')} · {gate.get('sourceRef')} · "
                f"有效至 {gate.get('effectiveTo') or '-'}"
            )
    lines.extend(("", f"结果哈希: {result.get('resultHash') or '-'}"))
    return lines


async def procurement_supplier_risk_report_render(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = validate_procurement_supplier_risk_result(dict(input_value["result"]))
    return pdf_report_payload(
        render_embedded_text_pdf(_procurement_supplier_risk_report_lines(result))
    )


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


async def integrity_finalize(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    approval = input_value.get("approval")
    return finalize_integrity_result(
        dict(input_value["ruleResult"]),
        dict(input_value["consistencyResult"]),
        dict(input_value["documentIntelligence"]),
        dict(approval) if isinstance(approval, dict) else None,
    )


async def report_render(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    results = [DocumentIntelligenceResult.model_validate(item) for item in input_value["results"]]
    findings = evaluate_cross_file_consistency(
        results,
        [CrossFileRule.model_validate(rule) for rule in input_value.get("rules", [])],
    )
    return pdf_report_payload(render_evidence_pdf(str(input_value["title"]), results, findings))


async def post_evaluation_evaluate(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    payload = normalize_post_evaluation_payload(dict(input_value["payload"]))
    raw_configuration = input_value.get("configuration", {})
    configuration = PostEvaluationConfiguration.model_validate(raw_configuration)
    result = evaluate_post_evaluation(payload, configuration)
    return result.model_dump(mode="json", by_alias=True)


async def post_evaluation_assemble(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
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


async def evidence_search_contextual(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return search_evidence(
        [dict(value) for value in input_value["documents"]],
        domain=str(input_value["domain"]),
        keywords=[str(value) for value in input_value.get("keywords", [])],
        max_hits=int(input_value.get("maxHits", 12)),
        contextual=True,
    )


class BoundEvidenceSearchExecutor:
    """Search compact document bindings while hydrating large parsed content in-tool."""

    def __init__(
        self,
        sessions: async_sessionmaker[Any],
        *,
        artifact_root: Path | None = None,
    ) -> None:
        self._sessions = sessions
        self._artifact_root = (
            artifact_root or Path(os.environ.get("SWARMCORE_ARTIFACT_ROOT", ".tmp/artifacts"))
        ).resolve()

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
        documents = [dict(value) for value in input_value["documents"] if isinstance(value, dict)]
        hydrated: list[dict[str, Any]] = []
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            for document in documents:
                hydrated.append(
                    await self._hydrate_document(
                        session,
                        document=document,
                        tenant_id=tenant_id,
                        project_id=project_id,
                    )
                )
        result = search_evidence(
            hydrated,
            domain=str(input_value["domain"]),
            keywords=[str(value) for value in input_value.get("keywords", [])],
            max_hits=int(input_value.get("maxHits", 12)),
            contextual=True,
        )
        del effect_id
        return result

    async def _hydrate_document(
        self,
        session: Any,
        *,
        document: dict[str, Any],
        tenant_id: UUID,
        project_id: UUID,
    ) -> dict[str, Any]:
        data = document.get("data")
        if not isinstance(data, dict):
            return document
        content_ref = data.get("contentArtifactRef")
        if not isinstance(content_ref, str) or not content_ref.startswith("blob://"):
            return document
        try:
            blob_id = UUID(content_ref.removeprefix("blob://"))
        except ValueError:
            return document
        blob = await session.scalar(
            select(BlobObject).where(
                BlobObject.id == blob_id,
                BlobObject.tenant_id == tenant_id,
                BlobObject.project_id == project_id,
                BlobObject.status == "AVAILABLE",
            )
        )
        if blob is None:
            return document
        target = (self._artifact_root / blob.object_key).resolve()
        if self._artifact_root not in target.parents or not target.is_file():
            return document
        try:
            content = json.loads(await to_thread(target.read_text, encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return document
        if not isinstance(content, dict):
            return document
        hydrated_data = dict(data)
        hydrated_data["content"] = content
        return {**document, "data": hydrated_data}


async def document_coverage_check(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
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
        [dict(value) for value in input_value.get("upstreamEvaluations", [])],
    )


async def post_evaluation_timeline(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return calculate_timeline(dict(input_value["payload"]))


async def post_evaluation_amounts(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return reconcile_amounts(dict(input_value["payload"]))


async def post_evaluation_invoices(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return assure_invoices(dict(input_value["payload"]))


async def post_evaluation_deviations(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return aggregate_deviations(dict(input_value["payload"]))


async def post_evaluation_risks(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return aggregate_risks(dict(input_value["payload"]))


async def evidence_consistency_check(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return check_evidence_consistency(
        dict(input_value["payload"]),
        [dict(value) for value in input_value.get("evidenceFacts", [])],
        [str(value) for value in input_value.get("declaredConflicts", [])],
    )


async def post_evaluation_finalize(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
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


async def deviation_facts_merge(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    merged = merge_deviation_facts(
        dict(input_value["basePayload"]),
        {
            **{key: dict(value) for key, value in dict(input_value["analyses"]).items()},
            "confirmedPerformance": upstream_performance_analysis(
                [
                    dict(value)
                    for value in input_value.get("upstreamEvaluations", [])
                    if isinstance(value, dict)
                ]
            ),
        },
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
            fact.get("factType") or fact.get("type") or fact.get("category") or "DEVIATION_FACT"
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


async def deviation_time_calculate(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return calculate_time_deviation(dict(input_value["payload"]))


async def deviation_content_compare(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return compare_content_deviation(dict(input_value["payload"]))


async def deviation_cost_calculate(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return calculate_cost_deviation(dict(input_value["payload"]))


async def deviation_trend_build(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return build_deviation_trends(
        dict(input_value["current"]),
        [dict(value) for value in input_value.get("history", [])],
    )


async def deviation_responsibility_aggregate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return aggregate_responsibility(dict(value) for value in input_value.get("proposals", []))


async def deviation_finalize(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return finalize_deviation_result(
        payload=dict(input_value["payload"]),
        dimensions={key: dict(value) for key, value in dict(input_value["dimensions"]).items()},
        root_causes=[dict(value) for value in input_value.get("rootCauses", [])],
        trends=dict(input_value["trends"]),
        responsibility=dict(input_value["responsibility"]),
        coverage=dict(input_value["coverage"]),
        evidence_review=dict(input_value["evidenceReview"]),
        narrative=dict(input_value["narrative"]),
        provenance=dict(input_value["provenance"]),
        approvals=[
            dict(value)
            for value in input_value.get("approvals", [])
            if isinstance(value, dict) and value
        ],
        schema_version=str(input_value.get("schemaVersion") or DEVIATION_SCHEMA_VERSION),
    )


async def deviation_report_render(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    result = validate_deviation_result(dict(input_value["result"]))
    return pdf_report_payload(render_embedded_text_pdf(deviation_report_lines(result)))


class GitHubCalibrationExecutor:
    def __init__(self, operation: str, *, token: str = "", base_url: str = "") -> None:
        self._operation = operation
        self._token = token
        self._base_url = base_url

    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        del effect_id, context
        client = (
            GitHubEvidenceClient(token=self._token, base_url=self._base_url)
            if self._base_url
            else GitHubEvidenceClient(token=self._token)
        )
        try:
            if self._operation == "issue":
                return await client.get_issue(str(input_value["issueUrl"]))
            if self._operation == "discussion":
                return await client.get_discussion(str(input_value["issueUrl"]))
            if self._operation == "pull":
                candidates = input_value.get("pullCandidates")
                if not isinstance(candidates, list):
                    raise ValueError("pullCandidates must be an array")
                return await client.get_pull_evidence(
                    str(input_value["issueUrl"]),
                    [dict(item) for item in candidates if isinstance(item, dict)],
                )
            raise ValueError(f"unsupported GitHub calibration operation: {self._operation}")
        finally:
            await client.close()


async def calibration_freeze_evidence(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return freeze_evidence(
        dict(input_value["issue"]),
        dict(input_value["discussion"]),
        dict(input_value["pullRequest"]),
    )


async def calibration_route_select(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return build_route_decision(
        dict(input_value["recommendation"]),
        primary_ready=bool(input_value.get("primaryReady", True)),
        standby_ready=bool(input_value.get("standbyReady", True)),
    )


async def calibration_quality_score(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    diagnosis = dict(input_value["diagnosis"])
    required = {
        "summary",
        "rootCause",
        "impact",
        "fixMechanism",
        "verificationPlan",
        "claims",
        "acceptanceMapping",
        "confidence",
    }
    evidence_index = input_value.get("evidenceIndex")
    evidence_items = evidence_index if isinstance(evidence_index, list) else []
    result = score_quality(
        diagnosis=diagnosis,
        schema_valid=required.issubset(diagnosis),
        evidence_ids={
            str(item["evidenceId"])
            for item in evidence_items
            if isinstance(item, dict) and "evidenceId" in item
        },
        sandbox=dict(input_value["sandbox"]),
        judge=dict(input_value["judge"]),
        acceptance_criteria=[str(item) for item in input_value.get("acceptanceCriteria", [])],
    )
    return {**result, "attempt": int(input_value.get("attempt", 1))}


async def calibration_attempt_select(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    selected = input_value.get("selectedAttempt")
    if not isinstance(selected, dict):
        raise ValueError("selectedAttempt must be an object")
    loop_last = selected.get("last")
    attempt = loop_last if isinstance(loop_last, dict) else selected
    items = attempt.get("items") if isinstance(attempt, dict) else None
    if not isinstance(items, list) or len(items) != 2:
        raise ValueError("selectedAttempt must contain diagnosis and quality outputs")
    diagnosis_output = next(
        (
            item
            for item in items
            if isinstance(item, dict)
            and isinstance(item.get("content"), dict)
            and (
                isinstance(item.get("fallback"), dict)
                or (
                    "model" in item
                    and not ("decision" in item["content"] and "components" in item["content"])
                )
            )
        ),
        None,
    )
    quality_output = next(
        (
            item
            for item in items
            if isinstance(item, dict)
            and isinstance(item.get("content"), dict)
            and "decision" in item["content"]
            and "components" in item["content"]
        ),
        None,
    )
    if not isinstance(diagnosis_output, dict) or not isinstance(quality_output, dict):
        raise ValueError("selectedAttempt outputs do not match calibration contracts")
    fallback = diagnosis_output.get("fallback")
    return {
        "diagnosis": dict(diagnosis_output["content"]),
        "quality": dict(quality_output["content"]),
        "fallback": dict(fallback) if isinstance(fallback, dict) else {"used": False},
    }


async def calibration_finalize(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    approvals = input_value.get("approvals")
    fallback = input_value.get("fallback")
    return finalize_calibration_result(
        payload=dict(input_value["payload"]),
        evidence=dict(input_value["evidence"]),
        route=dict(input_value["route"]),
        diagnosis=dict(input_value["diagnosis"]),
        quality=dict(input_value["quality"]),
        sandbox=dict(input_value["sandbox"]),
        approvals=dict(approvals) if isinstance(approvals, dict) else None,
        fallback=dict(fallback) if isinstance(fallback, dict) else None,
    )


async def calibration_report_render(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    result = dict(input_value["result"])
    return pdf_report_payload(render_embedded_text_pdf(calibration_report_lines(result)))


async def ai_quality_benchmark(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return evaluate_quality_benchmark(dict(input_value["payload"]))


async def ai_quality_finalize(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    approval = input_value.get("approval")
    payload = dict(input_value["payload"])
    return evaluate_quality_benchmark(
        payload,
        dict(approval) if isinstance(approval, dict) and approval else None,
    )


async def ai_quality_report(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    result = dict(input_value["result"])
    return pdf_report_payload(
        render_embedded_text_pdf(quality_benchmark_report_lines(result))
    )


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
        report_value = input_value.get("report")
        report_payload = dict(report_value) if isinstance(report_value, dict) else None
        if report_payload is not None:
            content = base64.b64decode(
                str(report_payload["contentBase64"]), validate=True
            )
            if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
                raise ValueError("evaluation report sha256 does not match content")
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
            item: WorkItem | None = None
            if report_payload is not None:
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
            evaluation.result = result
            evaluation.status = "SUCCEEDED"
            if item is not None and report_payload is not None:
                item.status = (
                    "IN_REVIEW" if result.get("reviewRequired") is True else "COMPLETED"
                )
                session.add_all(
                    [
                        Report(
                            tenant_id=tenant_id,
                            project_id=project_id,
                            work_item_id=item.id,
                            evaluation_id=evaluation.id,
                            format="JSON",
                            template_version=evaluation.report_template_version,
                            result_schema_version=evaluation.output_schema_version,
                            content=result,
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
                    ]
                )
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


class ConfirmedEvaluationReportGenerator:
    """Create or reuse a report for a confirmed source evaluation."""

    _TEMPLATE = "report://confirmed-evaluation@1"
    _RESULT_SCHEMA = "schema://report-generation/result@1"

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
        source_evaluation_id = UUID(str(input_value["sourceEvaluationId"]))
        report_format = str(input_value.get("format", "PDF")).upper()
        if report_format not in {"JSON", "PDF"}:
            raise ValueError("report format must be JSON or PDF")
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            source = await session.scalar(
                select(Evaluation)
                .where(
                    Evaluation.id == source_evaluation_id,
                    Evaluation.tenant_id == tenant_id,
                    Evaluation.project_id == project_id,
                )
                .with_for_update()
            )
            if source is None:
                raise LookupError("source evaluation not found in capability scope")
            if source.status != "SUCCEEDED" or not self._confirmed(source.result):
                raise ValueError("source evaluation is not confirmed for report generation")
            source_result = dict(source.result or {})
            source_result_hash = canonical_hash(source_result)
            existing = await session.scalar(
                select(Report).where(
                    Report.evaluation_id == source.id,
                    Report.format == report_format,
                    Report.tenant_id == tenant_id,
                    Report.project_id == project_id,
                )
            )
            if existing is not None:
                return self._result(
                    source=source,
                    report=existing,
                    source_result_hash=source_result_hash,
                    generated=False,
                )

            title = str(input_value.get("title") or "业务评价报告")
            if report_format == "JSON":
                report_content: dict[str, Any] = source_result
                content_hash = source_result_hash
            else:
                pdf_payload = pdf_report_payload(
                    render_embedded_text_pdf(
                        [
                            title,
                            f"来源评价: {source.id}",
                            "结果摘要: "
                            + json.dumps(source_result, ensure_ascii=False, sort_keys=True),
                        ]
                    )
                )
                report_content = pdf_payload
                content_hash = str(pdf_payload["sha256"])
            report = Report(
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_id=source.work_item_id,
                evaluation_id=source.id,
                format=report_format,
                template_version=self._TEMPLATE,
                result_schema_version=source.output_schema_version,
                content=report_content,
                content_hash=content_hash,
            )
            session.add(report)
            await session.flush()
            session.add(
                OutboxEvent(
                    id=uuid7(),
                    tenant_id=tenant_id,
                    aggregate_id=source.id,
                    destination="nats",
                    partition_key=str(source.id),
                    source_id=report.id,
                    type="report.created",
                    payload={
                        "reportId": str(report.id),
                        "evaluationId": str(source.id),
                        "format": report.format,
                        "contentHash": report.content_hash,
                        "effectId": effect_id,
                    },
                )
            )
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=str(context.execution_id),
                action="report.generate-confirmed-evaluation",
                resource_type="report",
                resource_id=str(report.id),
                run_id=UUID(str(context.run_id)),
                metadata={
                    "effectId": effect_id,
                    "sourceEvaluationId": str(source.id),
                    "format": report_format,
                    "contentHash": report.content_hash,
                },
            )
            return self._result(
                source=source,
                report=report,
                source_result_hash=source_result_hash,
                generated=True,
            )

    @staticmethod
    def _confirmed(result: dict[str, Any] | None) -> bool:
        if not isinstance(result, dict) or result.get("reviewRequired") is True:
            return False
        if isinstance(result.get("passed"), bool):
            return result["passed"] is True
        report_quality = result.get("reportQuality")
        if isinstance(report_quality, dict):
            return report_quality.get("passed") is True
        if result.get("qualityStatus") is not None:
            return result.get("qualityStatus") == "READY"
        return result.get("status") in {"COMPLETED", "COMPLETED_DEGRADED"}

    def _result(
        self,
        *,
        source: Evaluation,
        report: Report,
        source_result_hash: str,
        generated: bool,
    ) -> dict[str, Any]:
        result = {
            "schemaVersion": self._RESULT_SCHEMA,
            "sourceEvaluationId": str(source.id),
            "reportId": str(report.id),
            "format": report.format,
            "contentHash": report.content_hash,
            "sourceResultHash": source_result_hash,
            "status": "READY",
            "qualityStatus": "READY",
            "reviewRequired": False,
            "passed": True,
            "generated": generated,
            "provenance": {"template": self._TEMPLATE},
        }
        result["resultHash"] = canonical_hash(result)
        return result


class SwarmCalibrationRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result = dict(input_value["result"])
        result_hash = canonical_hash(result)
        if result.get("resultHash") != result_hash:
            expected = result.pop("resultHash", None)
            calculated = canonical_hash(result)
            result["resultHash"] = expected
            if expected != calculated:
                raise ValueError("swarm-calibration resultHash does not match result")
            result_hash = canonical_hash(result)
        report_payload = dict(input_value["report"])
        content = base64.b64decode(str(report_payload["contentBase64"]), validate=True)
        if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
            raise ValueError("swarm-calibration report sha256 does not match content")
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
            evaluation.result = result
            evaluation.status = "SUCCEEDED"
            item.status = (
                "COMPLETED"
                if result["status"] in {"COMPLETED", "COMPLETED_DEGRADED"}
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
                    content=result,
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
            evidence_rows = [
                CalibrationEvidenceSnapshot(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    evaluation_id=evaluation.id,
                    evidence_key=str(evidence["evidenceId"]),
                    source_type=str(evidence["sourceType"]),
                    source_url=str(evidence["sourceUrl"]),
                    commit_sha=(str(evidence["commitSha"]) if evidence.get("commitSha") else None),
                    etag=str(evidence["etag"]) if evidence.get("etag") else None,
                    content_hash=str(evidence["contentHash"]),
                    retrieved_at=datetime.fromisoformat(
                        str(evidence["retrievedAt"]).replace("Z", "+00:00")
                    ),
                    security=dict(evidence.get("security") or {}),
                    metadata_json={
                        "evidenceManifestHash": result["provenance"]["evidenceManifestHash"]
                    },
                )
                for evidence in result["evidence"]
                if isinstance(evidence, dict)
            ]
            route = dict(result["route"])
            route_row = CalibrationRouteDecision(
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=evaluation.id,
                sequence=1,
                recommended_route=str(route["recommendedRoute"]),
                selected_route=str(route["selectedRoute"]),
                reason_codes=[str(item) for item in route.get("reasonCodes", [])],
                primary_agent_ref=(
                    str(route["primaryAgentRef"]) if route.get("primaryAgentRef") else None
                ),
                selected_agent_ref=(
                    str(route["selectedAgentRef"]) if route.get("selectedAgentRef") else None
                ),
                runtime_authoritative=bool(route.get("runtimeAuthoritative")),
            )
            quality = dict(result["quality"])
            quality_row = CalibrationQualityEvaluation(
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=evaluation.id,
                attempt=int(quality.get("attempt", 1)),
                decision=str(quality["decision"]),
                score=round(float(quality["score"])),
                threshold=round(float(quality["threshold"])),
                components=dict(quality["components"]),
                hard_failures=[str(item) for item in quality.get("hardFailures", [])],
                evidence_coverage_bps=round(float(quality.get("evidenceCoverage", 0)) * 10_000),
                acceptance_coverage_bps=round(float(quality.get("acceptanceCoverage", 0)) * 10_000),
                sandbox_status=str(
                    quality.get("sandboxStatus") or result["sandbox"].get("status") or "UNVERIFIED"
                ),
            )
            decision_records: list[Any] = [*evidence_rows, route_row, quality_row]
            fallback = route.get("fallback")
            if isinstance(fallback, dict) and fallback.get("used"):
                decision_records.append(
                    CalibrationFallbackRecord(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        evaluation_id=evaluation.id,
                        sequence=1,
                        from_agent_ref=str(fallback["fromAgentRef"]),
                        to_agent_ref=str(fallback["toAgentRef"]),
                        trigger_code=str(fallback["triggerCode"]),
                        error_message=(str(fallback["error"]) if fallback.get("error") else None),
                    )
                )
            session.add_all(decision_records)
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
                    type="capability.swarm-calibration.assessment.completed",
                    payload={
                        "evaluationId": str(evaluation.id),
                        "effectId": effect_id,
                        "resultHash": result_hash,
                        "status": result["status"],
                        "qualityScore": result["quality"]["score"],
                        "selectedRoute": result["route"]["selectedRoute"],
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
                action="evaluation.record-swarm-calibration",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={
                    "effectId": effect_id,
                    "resultHash": result_hash,
                    "selectedRoute": result["route"]["selectedRoute"],
                },
            )
            return self._receipt(evaluation_id, effect_id, result_hash, recorded=True)


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
                    _compact_processing_result(processing.result) if processing is not None else {}
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
                "sections",
                "tables",
                "sheets",
                "chunks",
                "layout",
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


async def document_structuring_prepare(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    prepared = prepare_document_structuring(
        [dict(value) for value in input_value.get("documents") or [] if isinstance(value, dict)]
    )
    return {**prepared, "effectId": effect_id}


async def document_structuring_quality_check(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    result = finalize_document_structuring(
        dict(input_value["prepared"]),
        dict(input_value["analysis"]),
    )
    return {**result, "effectId": effect_id}


async def document_structuring_analysis_select(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    selected = select_document_structuring_analysis(
        dict(input_value["original"]),
        dict(input_value["reprocessed"]) if input_value.get("reprocessed") else None,
        dict(input_value["review"]) if input_value.get("review") else None,
    )
    return {**selected, "effectId": effect_id}


async def document_structuring_review_select(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    selected = select_document_structuring_review(
        dict(input_value["initial"]) if input_value.get("initial") else None,
        dict(input_value["reprocessed"]) if input_value.get("reprocessed") else None,
        was_reprocessed=bool(input_value.get("wasReprocessed")),
    )
    return {"approval": selected, "effectId": effect_id}


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
                    "formal post-evaluation result is incomplete: " + ", ".join(sorted(missing))
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
            item.status = "COMPLETED" if result_payload["qualityStatus"] == "READY" else "IN_REVIEW"
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
                        select(Finding).where(Finding.work_item_id == item.id).with_for_update()
                    )
                ).all()
            }
            for finding_payload in result_payload.get("findings", []):
                if not isinstance(finding_payload, dict):
                    continue
                code = str(finding_payload.get("code") or "DEVIATION_REVIEW")
                rule_key = f"deviation-analysis:{code}"
                finding = existing_findings.get(rule_key)
                dimension = str(finding_payload.get("dimension") or "DEVIATION_ANALYSIS")
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
            and str(item.get("category") or "").upper() in {"INVOICE_ORIGINAL", "INVOICE"}
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
                    text_excerpt = content.get("textExcerpt")
                    if isinstance(text_excerpt, str) and text_excerpt.strip():
                        if content.get("textTruncated") is True:
                            raise ValueError(
                                "invoice original content is truncated in the document projection"
                            )
                        return text_excerpt, media_type, str(version_id) if version_id else None
                for key in ("text", "rawText", "xml", "extractedText"):
                    if data.get(key):
                        return data[key], media_type, str(version_id) if version_id else None
                if data.get("invoiceFactSet"):
                    return (
                        data["invoiceFactSet"],
                        "application/json",
                        (str(version_id) if version_id else None),
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


async def invoice_parse(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
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


async def invoice_official_verify(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    payload_value = input_value.get("payload")
    payload: dict[str, Any] = dict(payload_value) if isinstance(payload_value, dict) else {}
    configuration_value = input_value.get("configuration")
    configuration: dict[str, Any] = (
        dict(configuration_value) if isinstance(configuration_value, dict) else {}
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


async def business_snapshot_read(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    payload = dict(input_value.get("payload") or {})
    if input_value.get("documents") and "documents" not in payload:
        payload["documents"] = input_value["documents"]
    if input_value.get("subjects") and "subjects" not in payload:
        payload["subjects"] = input_value["subjects"]
    if input_value.get("asOf") and "asOf" not in payload:
        payload["asOf"] = input_value["asOf"]
    return read_business_snapshot(payload)


async def invoice_arithmetic_check(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    rules = arithmetic_check(dict(input_value["invoiceFactSet"]))
    return {
        "ruleResults": rules,
        "status": "FAIL" if any(r["status"] == "FAIL" for r in rules) else "PASS",
    }


async def invoice_party_check(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
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


async def invoice_enterprise_status_check(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    payload = input_value.get("payload")
    evidence = input_value.get("enterprisePublicStatusEvidence")
    if not isinstance(evidence, dict) and isinstance(payload, dict):
        candidate = payload.get("enterprisePublicStatusEvidence")
        evidence = candidate if isinstance(candidate, dict) else None
    return enterprise_public_status_check(
        dict(input_value["invoiceFactSet"]),
        evidence,
    )


async def invoice_deduplicate(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    snapshot = input_value.get("businessSnapshot")
    ledger = None
    if isinstance(snapshot, dict):
        ledger = snapshot.get("apLedger")
    return deduplicate(dict(input_value["invoiceFactSet"]), ledger)


async def invoice_commercial_match(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    candidates = input_value.get("matchCandidates")
    return commercial_match(
        dict(input_value["invoiceFactSet"]),
        dict(input_value.get("businessSnapshot") or {}),
        candidates if isinstance(candidates, list) else None,
    )


async def invoice_payment_gate(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
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
    snapshot = (
        input_value.get("businessSnapshot")
        if isinstance(input_value.get("businessSnapshot"), dict)
        else {}
    )
    return payment_gate(
        {
            "verification": input_value.get("verification") or {},
            "duplication": duplication,
            "ruleResults": [*arithmetic, *parties],
            "commercialMatch": input_value.get("matchResults") or {},
            "budget": snapshot.get("budget") if isinstance(snapshot, dict) else {},
        }
    )


async def invoice_finalize(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    nested = input_value.get("ruleResults")
    duplication: dict[str, Any] = {}
    rules = _flatten_invoice_rules(nested)
    if isinstance(nested, dict) and isinstance(nested.get("duplication"), dict):
        duplication = nested["duplication"]
        rules.extend(_flatten_invoice_rules(duplication.get("ruleResults")))
    payload_value = input_value.get("payload")
    payload: dict[str, Any] = dict(payload_value) if isinstance(payload_value, dict) else {}
    evidence_review = (
        input_value.get("evidenceReview")
        if isinstance(input_value.get("evidenceReview"), dict)
        else {}
    )
    narrative = evidence_review.get("narrative") if isinstance(evidence_review, dict) else None
    business_snapshot = input_value.get("businessSnapshot")
    if not isinstance(business_snapshot, dict):
        payload_snapshot = payload.get("businessSnapshot")
        business_snapshot = {
            "hash": input_value.get("businessSnapshotHash"),
            **(dict(payload_snapshot) if isinstance(payload_snapshot, dict) else {}),
        }
    approvals_raw = input_value.get("approvals")
    approvals: list[dict[str, Any]] = []
    if isinstance(approvals_raw, dict):
        for key, value in approvals_raw.items():
            if isinstance(value, dict) and value:
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
        enterprise_public_status=dict(input_value.get("enterprisePublicStatus") or {}),
        narrative=narrative if isinstance(narrative, dict) else None,
        provenance=dict(input_value.get("provenance") or {}),
        approvals=approvals,
        title=str(payload.get("title") or "发票一致性校验"),
        as_of=payload.get("asOf"),
    )


async def invoice_assurance_report_render(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
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
                        select(Finding).where(Finding.work_item_id == item.id).with_for_update()
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


_CONTRACT_PUBLIC_SOURCE_HOSTS = frozenset({"assets.publishing.service.gov.uk"})
_CONTRACT_PUBLIC_SOURCE_MAX_BYTES = 20 * 1024 * 1024


class _PublicSourceDownloadError(RuntimeError):
    def __init__(self, code: str, *, attempts: int) -> None:
        super().__init__(code)
        self.attempts = attempts


def _download_contract_public_source(url: str) -> tuple[bytes, dict[str, str]]:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() not in _CONTRACT_PUBLIC_SOURCE_HOSTS
        or not parsed.path.lower().endswith(".csv")
    ):
        raise ValueError("PUBLIC_SOURCE_URL_NOT_ALLOWED")
    request = Request(
        url,
        headers={
            "Accept": "text/csv",
            "User-Agent": "SwarmCore-ContractPerformance/1.0",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=120) as response:
            final = urlparse(response.geturl())
            if (final.hostname or "").lower() not in _CONTRACT_PUBLIC_SOURCE_HOSTS:
                raise ValueError("PUBLIC_SOURCE_REDIRECT_NOT_ALLOWED")
            content = response.read(_CONTRACT_PUBLIC_SOURCE_MAX_BYTES + 1)
            metadata = {
                "etag": str(response.headers.get("ETag") or ""),
                "lastModified": str(response.headers.get("Last-Modified") or ""),
                "contentType": str(response.headers.get("Content-Type") or ""),
            }
    except HTTPError as exc:
        raise RuntimeError(f"PUBLIC_SOURCE_HTTP_{exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("PUBLIC_SOURCE_UNAVAILABLE") from exc
    if len(content) > _CONTRACT_PUBLIC_SOURCE_MAX_BYTES:
        raise ValueError("PUBLIC_SOURCE_TOO_LARGE")
    return content, metadata


def _public_source_retryable(exc: RuntimeError) -> bool:
    code = str(exc)
    if code == "PUBLIC_SOURCE_UNAVAILABLE":
        return True
    if not code.startswith("PUBLIC_SOURCE_HTTP_"):
        return False
    try:
        status = int(code.rsplit("_", 1)[-1])
    except ValueError:
        return False
    return status == 429 or status >= 500


async def _download_contract_public_source_with_retry(
    url: str,
    *,
    max_attempts: int = 3,
) -> tuple[bytes, dict[str, str], int]:
    if max_attempts < 1:
        raise ValueError("PUBLIC_SOURCE_MAX_ATTEMPTS_INVALID")
    for attempt in range(1, max_attempts + 1):
        try:
            content, metadata = await to_thread(_download_contract_public_source, url)
            return content, metadata, attempt
        except RuntimeError as exc:
            if attempt >= max_attempts or not _public_source_retryable(exc):
                raise _PublicSourceDownloadError(str(exc), attempts=attempt) from exc
            await sleep(2 ** (attempt - 1))
    raise RuntimeError("PUBLIC_SOURCE_UNAVAILABLE")


def _public_dfe_spend_snapshots(
    raw: dict[str, Any],
    *,
    content: bytes,
    response_metadata: dict[str, str],
) -> tuple[list[dict[str, Any]], str]:
    source_ref = str(raw.get("sourceRef") or "")
    if not source_ref:
        raise ValueError("PUBLIC_SOURCE_REF_REQUIRED")
    url = str(raw.get("url") or "")
    source_sha256 = hashlib.sha256(content).hexdigest()
    if str(raw.get("cursor") or "") == source_sha256:
        return [], source_sha256
    try:
        text = content.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        text = content.decode("cp1252")
        encoding = "cp1252"
    reader = csv.DictReader(io.StringIO(text, newline=""))
    required_columns = {
        "Date",
        "Expense Area",
        "Supplier",
        "Transaction Number",
        "Amount",
        "Description",
    }
    if reader.fieldnames is None or not required_columns <= set(reader.fieldnames):
        raise ValueError("PUBLIC_DFE_SPEND_SCHEMA_MISMATCH")
    filters = {
        str(key): str(value) for key, value in dict(raw.get("filters") or {}).items() if str(value)
    }
    if set(filters) - set(reader.fieldnames):
        raise ValueError("PUBLIC_DFE_SPEND_FILTER_UNKNOWN")
    retrieved_at = datetime.now(UTC).isoformat()
    snapshots: list[dict[str, Any]] = []
    for row_number, row in enumerate(reader, start=2):
        if any(
            str(row.get(key) or "").strip().casefold() != value.strip().casefold()
            for key, value in filters.items()
        ):
            continue
        transaction_number = str(row.get("Transaction Number") or "").strip()
        if not transaction_number:
            raise ValueError("PUBLIC_DFE_SPEND_TRANSACTION_ID_MISSING")
        try:
            amount = float(Decimal(str(row.get("Amount") or "").replace(",", "").strip()))
            business_date = (
                datetime.strptime(str(row.get("Date") or "").strip(), "%d/%m/%Y").date().isoformat()
            )
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("PUBLIC_DFE_SPEND_VALUE_INVALID") from exc
        supplier = str(row.get("Supplier") or "").strip()
        expense_area = str(row.get("Expense Area") or "").strip()
        description = str(row.get("Description") or "").strip()
        excerpt = json.dumps(
            {
                "amount": amount,
                "date": business_date,
                "description": description,
                "expenseArea": expense_area,
                "supplier": supplier,
                "transactionNumber": transaction_number,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        evidence_ref = {
            "sourceRef": source_ref,
            "sourceRecordId": transaction_number,
            "row": row_number,
            "text": excerpt,
        }
        snapshots.append(
            {
                "id": transaction_number,
                "type": str(raw.get("evidenceType") or "PAYMENT").upper(),
                "sourceRef": source_ref,
                "sourceRecordId": transaction_number,
                "sourceVersion": source_sha256,
                "sourceTimestamp": business_date,
                "collectedAt": retrieved_at,
                "businessDate": business_date,
                "amount": amount,
                "currency": str(raw.get("currency") or "GBP"),
                "description": description,
                "contractKeys": {
                    "supplier": supplier,
                    "expenseArea": expense_area,
                },
                "contentHash": canonical_hash(row),
                "category": "PAYMENT_EVIDENCE",
                "name": f"DfE spend {transaction_number}",
                "filename": url.rsplit("/", 1)[-1],
                "data": {
                    "content": {
                        "textExcerpt": excerpt,
                        "tables": [dict(row)],
                    }
                },
                "evidence": [evidence_ref],
                "provenance": {
                    "url": url,
                    "sourceSha256": source_sha256,
                    "encoding": encoding,
                    **response_metadata,
                },
            }
        )
    return snapshots, source_sha256


async def contract_performance_source_collect(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    evidence: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    next_cursors: dict[str, str] = {}
    source_results: list[dict[str, Any]] = []
    failures = 0
    sources = input_value.get("sources") or []
    for raw in sources:
        if not isinstance(raw, dict):
            continue
        source_ref = str(raw.get("sourceRef") or "")
        if str(raw.get("kind") or "").upper() == "PUBLIC_DFE_SPEND_CSV":
            try:
                content, metadata, attempts = await _download_contract_public_source_with_retry(
                    str(raw.get("url") or ""),
                )
                source_snapshots, next_cursor = _public_dfe_spend_snapshots(
                    raw,
                    content=content,
                    response_metadata=metadata,
                )
            except (RuntimeError, ValueError) as exc:
                failures += 1
                source_results.append(
                    {
                        "sourceRef": source_ref,
                        "status": "FAILED",
                        "code": str(exc),
                        "attempts": int(getattr(exc, "attempts", 1)),
                    }
                )
                continue
            snapshots.extend(source_snapshots)
            evidence.extend(source_snapshots)
            next_cursors[source_ref] = next_cursor
            source_results.append(
                {
                    "sourceRef": source_ref,
                    "status": "SUCCEEDED",
                    "recordCount": len(source_snapshots),
                    "nextCursor": next_cursor,
                    "attempts": attempts,
                }
            )
            continue
        status = str(raw.get("status") or "SUCCEEDED").upper()
        if status != "SUCCEEDED":
            failures += 1
            source_results.append({"sourceRef": source_ref, "status": "FAILED"})
            continue
        records = raw.get("records") or []
        for record in records:
            if not isinstance(record, dict):
                continue
            snapshot = {
                **record,
                "sourceRef": source_ref,
                "sourceRecordId": str(record.get("sourceRecordId") or record.get("id") or ""),
                "contentHash": str(record.get("contentHash") or canonical_hash(record)),
            }
            snapshots.append(snapshot)
            evidence.append(snapshot)
        if raw.get("nextCursor") is not None:
            next_cursors[source_ref] = str(raw["nextCursor"])
        source_results.append(
            {
                "sourceRef": source_ref,
                "status": "SUCCEEDED",
                "recordCount": len(records),
                "nextCursor": next_cursors.get(source_ref),
            }
        )
    collection_status = (
        "FAILED" if sources and failures == len(sources) else "PARTIAL" if failures else "COMPLETE"
    )
    return {
        "snapshots": snapshots,
        "evidence": evidence,
        "nextCursors": next_cursors,
        "collectionStatus": collection_status,
        "sourceResults": source_results,
    }


async def contract_performance_document_parse(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    content = input_value.get("content")
    text = content if isinstance(content, str) else ""
    return {
        "text": text,
        "tables": list(input_value.get("tables") or []),
        "locators": list(input_value.get("locators") or []),
        "quality": "PARSED" if text else "REVIEW_REQUIRED",
    }


async def contract_performance_document_ocr(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    blocks = list(input_value.get("blocks") or [])
    return {
        "blocks": blocks,
        "quality": "OCR_COMPLETE" if blocks else "REVIEW_REQUIRED",
        "humanConfirmationRequired": not blocks,
    }


async def contract_performance_plan_normalize(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    configuration = input_value.get("configuration") or {}
    return {
        "plan": normalize_plan(
            dict(input_value.get("candidates") or {}),
            timezone=str(configuration.get("timezone") or "Asia/Shanghai"),
            currency=str(configuration.get("currency") or "CNY"),
        )
    }


async def contract_performance_change_apply(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return apply_approved_changes(
        dict(input_value["plan"]),
        [item for item in input_value.get("changes", []) if isinstance(item, dict)],
        as_of=str(input_value["asOf"]),
    )


async def contract_performance_schedule_build(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    original = input_value.get("originalPlan")
    actuals = input_value.get("actuals")
    return build_schedule(
        dict(input_value["plan"]),
        original_plan=dict(original) if isinstance(original, dict) else None,
        actuals=dict(actuals) if isinstance(actuals, dict) else None,
        as_of=str(input_value["asOf"]),
    )


async def contract_performance_evidence_match(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return match_evidence(
        dict(input_value["plan"]),
        [item for item in input_value.get("evidence", []) if isinstance(item, dict)],
        [item for item in input_value.get("candidates", []) if isinstance(item, dict)],
    )


async def contract_performance_status_calculate(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    return calculate_status(
        dict(input_value["plan"]),
        [item for item in input_value.get("evidence", []) if isinstance(item, dict)],
        [item for item in input_value.get("links", []) if isinstance(item, dict)],
        as_of=str(input_value["asOf"]),
        collection_status=str(input_value.get("collectionStatus") or "COMPLETE"),
        approved_exceptions=[str(item) for item in input_value.get("approvedExceptions", [])],
    )


async def contract_performance_finalize(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    plan = dict(input_value.get("plan") or {})
    performance = input_value.get("performance")
    if not isinstance(performance, dict):
        approved = bool((input_value.get("approval") or {}).get("approved"))
        if approved:
            required_sections = (
                "obligations",
                "deliverables",
                "milestones",
                "acceptanceCriteria",
                "serviceLevels",
                "paymentConditions",
            )
            missing_sections = [
                section
                for section in required_sections
                if not isinstance(plan.get(section), list) or not plan[section]
            ]
            if not isinstance(plan.get("contract"), dict) or not plan["contract"]:
                missing_sections.insert(0, "contract")
            if missing_sections:
                raise ValueError("PLAN_MINIMUM_CONTENT_REQUIRED:" + ",".join(missing_sections))
            plan = {**plan, "status": "PUBLISHED"}
            plan["planHash"] = canonical_hash(
                {key: value for key, value in plan.items() if key != "planHash"}
            )
        plan_findings: list[dict[str, Any]] = []
        for item in plan.get("conflicts") or []:
            if isinstance(item, dict):
                plan_findings.append(
                    {
                        **item,
                        "code": str(item.get("code") or "PLAN_CONFLICT"),
                        "severity": str(item.get("severity") or "HIGH"),
                        "reviewType": str(item.get("reviewType") or "CONTRACT"),
                    }
                )
        for item in plan.get("gaps") or []:
            if isinstance(item, dict):
                code = str(item.get("code") or "PLAN_GAP")
                plan_findings.append(
                    {
                        **item,
                        "code": code,
                        "severity": str(
                            item.get("severity")
                            or ("HIGH" if code == "PAYMENT_TOTAL_MISMATCH" else "MEDIUM")
                        ),
                        "reviewType": str(
                            item.get("reviewType")
                            or ("FINANCE" if code == "PAYMENT_TOTAL_MISMATCH" else "CONTRACT")
                        ),
                    }
                )
        performance = {
            "asOf": input_value.get("asOf") or (input_value.get("payload") or {}).get("asOf"),
            "status": "ON_TRACK" if approved and not plan_findings else "REVIEW_REQUIRED",
            "collectionStatus": "COMPLETE",
            "milestones": [],
            "paymentGates": [],
            "findings": plan_findings,
            "reviewRequired": not approved or bool(plan_findings),
            "ruleVersion": "rule://contract-performance@2",
        }
    gantt = dict(input_value.get("gantt") or {})
    if "ganttHash" not in gantt:
        as_of = performance.get("asOf")
        if as_of is None:
            raise ValueError("contract-performance finalize requires asOf")
        gantt = build_schedule(
            plan,
            as_of=str(as_of),
        )
    approval = input_value.get("approval")
    approvals = [dict(approval)] if isinstance(approval, dict) and approval else []
    change_history = input_value.get("changeHistory")
    if not isinstance(change_history, dict):
        change_history = plan.get("changeHistory")
    if not isinstance(change_history, dict):
        change_history = {
            "appliedChanges": [
                dict(item)
                for item in plan.get("changes") or []
                if isinstance(item, dict) and str(item.get("status") or "").upper() == "APPROVED"
            ],
            "differences": [],
            "unapprovedChangeRisks": [],
        }
    return finalize_contract_performance(
        case_id=str(input_value.get("caseId") or ""),
        plan_version=int(input_value.get("planVersion") or 1),
        plan=plan,
        performance=performance,
        gantt=gantt,
        evidence_ledger=dict(input_value.get("evidenceLedger") or {}),
        change_history=change_history,
        provenance=dict(input_value.get("provenance") or {}),
        approvals=approvals,
    )


async def contract_performance_report_render(
    input_value: dict[str, Any], effect_id: str
) -> dict[str, Any]:
    del effect_id
    result = validate_contract_performance_result(dict(input_value["result"]))
    return pdf_report_payload(render_embedded_text_pdf(contract_performance_report_lines(result)))


class ContractPerformanceRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result = validate_contract_performance_result(dict(input_value["result"]))
        result_hash = str(result["resultHash"])
        report_payload = dict(input_value["report"])
        content = base64.b64decode(str(report_payload["contentBase64"]), validate=True)
        if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
            raise ValueError("contract-performance report sha256 does not match content")

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
                if canonical_hash(evaluation.result) != canonical_hash(result):
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

            evaluation.result = result
            evaluation.status = "SUCCEEDED"
            item.status = "COMPLETED" if result["status"] == "COMPLETED" else "IN_REVIEW"
            reports = (
                Report(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    work_item_id=item.id,
                    evaluation_id=evaluation.id,
                    format="JSON",
                    template_version=evaluation.report_template_version,
                    result_schema_version=evaluation.output_schema_version,
                    content=result,
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

            for payload in result.get("performance", {}).get("findings", []):
                if not isinstance(payload, dict):
                    continue
                code = str(payload.get("code") or "PERFORMANCE_REVIEW")
                target = str(
                    payload.get("milestoneId")
                    or payload.get("paymentConditionId")
                    or payload.get("targetId")
                    or "general"
                )
                session.add(
                    Finding(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        work_item_id=item.id,
                        evaluation_id=evaluation.id,
                        rule_key=f"contract-performance:{code}:{target}",
                        code=code,
                        category=str(payload.get("category") or "CONTRACT_PERFORMANCE"),
                        severity=str(payload.get("severity") or "MEDIUM"),
                        status="OPEN",
                        title=str(payload.get("title") or f"合同履约 · {code}"),
                        detail=str(
                            payload.get("summary") or payload.get("detail") or "合同履约关注项"
                        ),
                        evidence={
                            "evidenceRefs": list(payload.get("evidenceRefs") or []),
                            "resultHash": result_hash,
                            "blocking": bool(payload.get("blocking")),
                        },
                    )
                )

            await session.flush()
            session.add(
                OutboxEvent(
                    id=uuid7(),
                    tenant_id=tenant_id,
                    aggregate_id=evaluation.id,
                    destination="nats",
                    partition_key=str(evaluation.id),
                    source_id=evaluation.id,
                    type="capability.contract-performance.snapshot.finalized",
                    payload={
                        "projectId": str(project_id),
                        "evaluationId": str(evaluation.id),
                        "effectId": effect_id,
                        "resultHash": result_hash,
                        "status": result["status"],
                        "reviewRequired": bool(result.get("performance", {}).get("reviewRequired")),
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
                            "projectId": str(project_id),
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
                action="evaluation.record-contract-performance",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={
                    "effectId": effect_id,
                    "resultHash": result_hash,
                    "status": result["status"],
                },
            )
            return self._receipt(evaluation_id, effect_id, result_hash, recorded=True)


class ProcurementSupplierRiskRecorderExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        result = validate_procurement_supplier_risk_result(dict(input_value["result"]))
        result_hash = str(result["resultHash"])
        report_payload = dict(input_value["report"])
        content = base64.b64decode(str(report_payload["contentBase64"]), validate=True)
        if hashlib.sha256(content).hexdigest() != report_payload["sha256"]:
            raise ValueError("procurement supplier risk report sha256 does not match content")
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
                if canonical_hash(evaluation.result) != canonical_hash(result):
                    raise ValueError("evaluation already contains a different result")
                return self._receipt(evaluation_id, effect_id, result_hash, recorded=False)
            if evaluation.status != "RUNNING":
                raise ValueError(f"evaluation cannot be recorded from {evaluation.status}")
            work_item = await session.scalar(
                select(WorkItem)
                .where(
                    WorkItem.id == evaluation.work_item_id,
                    WorkItem.tenant_id == tenant_id,
                    WorkItem.project_id == project_id,
                )
                .with_for_update()
            )
            if work_item is None:
                raise LookupError("work item not found in capability scope")
            evaluation.result = result
            evaluation.status = "SUCCEEDED"
            work_item.status = "COMPLETED" if result["decision"] == "PASS" else "IN_REVIEW"
            reports = (
                Report(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    work_item_id=work_item.id,
                    evaluation_id=evaluation.id,
                    format="JSON",
                    template_version=evaluation.report_template_version,
                    result_schema_version=evaluation.output_schema_version,
                    content=result,
                    content_hash=result_hash,
                ),
                Report(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    work_item_id=work_item.id,
                    evaluation_id=evaluation.id,
                    format="PDF",
                    template_version=evaluation.report_template_version,
                    result_schema_version=evaluation.output_schema_version,
                    content=report_payload,
                    content_hash=str(report_payload["sha256"]),
                ),
            )
            session.add_all(reports)
            finding_payloads = [
                finding
                for finding in result.get("consistency", {}).get("findings", [])
                if isinstance(finding, dict)
            ]
            finding_payloads.extend(
                {
                    "findingId": (f"gate-{gate.get('code')}-{gate.get('sourceRecordId') or index}"),
                    "code": str(gate.get("code") or "SUPPLIER_RISK_GATE"),
                    "category": "SUPPLIER_RISK",
                    "severity": "BLOCKER",
                    "title": f"供应商硬性门禁: {gate.get('code')}",
                    "summary": (
                        f"来源 {gate.get('sourceRef') or '-'} 命中有效风险记录, "
                        f"有效至 {gate.get('effectiveTo') or '未提供'}。"
                    ),
                    "evidenceRefs": list(gate.get("evidenceRefs") or []),
                }
                for index, gate in enumerate(result.get("risk", {}).get("hardGates", []))
                if isinstance(gate, dict)
            )
            for finding_payload in finding_payloads:
                finding_id = str(
                    finding_payload.get("findingId") or canonical_hash(finding_payload)[:24]
                )
                session.add(
                    Finding(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        work_item_id=work_item.id,
                        evaluation_id=evaluation.id,
                        rule_key=(f"procurement-supplier-risk:{finding_id}:{result_hash[:12]}"),
                        code=str(finding_payload.get("code") or "PROCUREMENT_RISK"),
                        category=str(finding_payload.get("category") or "PROCUREMENT_CONSISTENCY"),
                        severity=str(finding_payload.get("severity") or "MEDIUM"),
                        status="OPEN",
                        title=str(finding_payload.get("title") or "招采与供应商风险"),
                        detail=str(
                            finding_payload.get("summary")
                            or finding_payload.get("detail")
                            or "需要复核"
                        ),
                        evidence={
                            "evidenceRefs": list(finding_payload.get("evidenceRefs") or []),
                            "resultHash": result_hash,
                            "sourceFindingId": finding_id,
                        },
                    )
                )
            monitor_id = result.get("monitorId")
            if monitor_id:
                await ProcurementSupplierRiskService().record_snapshot(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    monitor_id=UUID(str(monitor_id)),
                    evaluation_id=evaluation.id,
                    result=result,
                    actor=str(context.execution_id),
                )
            await session.flush()
            event_types = ["capability.procurement-supplier-risk.assessment.completed"]
            if result.get("risk", {}).get("hardGates"):
                event_types.append("capability.supplier-risk.alert.opened")
            for event_type in event_types:
                event_id = uuid7()
                session.add(
                    OutboxEvent(
                        id=event_id,
                        tenant_id=tenant_id,
                        aggregate_id=evaluation.id,
                        destination="nats",
                        partition_key=str(evaluation.id),
                        source_id=event_id,
                        type=event_type,
                        payload={
                            "projectId": str(project_id),
                            "evaluationId": str(evaluation.id),
                            "caseId": result["caseId"],
                            "supplier": result["supplier"],
                            "effectId": effect_id,
                            "resultHash": result_hash,
                            "decision": result["decision"],
                            "riskLevel": result["riskLevel"],
                            "snapshotHash": result["snapshotHash"],
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
                            "projectId": str(project_id),
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
                action="evaluation.record-procurement-supplier-risk",
                resource_type="evaluation",
                resource_id=str(evaluation.id),
                run_id=UUID(str(context.run_id)),
                metadata={
                    "effectId": effect_id,
                    "resultHash": result_hash,
                    "decision": result["decision"],
                    "riskLevel": result["riskLevel"],
                    "hardGateCount": len(result.get("risk", {}).get("hardGates", [])),
                },
            )
            return self._receipt(evaluation_id, effect_id, result_hash, recorded=True)


class DocumentStructuringPublisherExecutor(EvaluationRecorderExecutor):
    async def execute(
        self, input_value: dict[str, Any], effect_id: str, context: Any
    ) -> dict[str, Any]:
        tenant_id = UUID(str(context.tenant_id))
        project_id = UUID(str(context.project_id))
        run_id = UUID(str(context.run_id))
        evaluation_id = UUID(str(input_value["evaluationId"]))
        raw_result = dict(input_value["result"])
        approval_value = input_value.get("approval")
        approval = dict(approval_value) if isinstance(approval_value, dict) else None
        reviewed = apply_human_review(raw_result, approval)
        published_input_hash = canonical_hash(reviewed)
        created_paths: list[Path] = []
        try:
            async with tenant_transaction(
                self._sessions, tenant_id=tenant_id, project_id=project_id
            ) as session:
                evaluation = await session.scalar(
                    select(Evaluation)
                    .where(
                        Evaluation.id == evaluation_id,
                        Evaluation.tenant_id == tenant_id,
                        Evaluation.project_id == project_id,
                        Evaluation.run_id == run_id,
                    )
                    .with_for_update()
                )
                if evaluation is None:
                    raise LookupError("evaluation not found in capability run scope")
                if evaluation.result is not None:
                    provenance = dict(evaluation.result.get("provenance") or {})
                    if provenance.get("publishedInputHash") != published_input_hash:
                        raise ValueError("evaluation already contains a different result")
                    return self._receipt(
                        evaluation_id,
                        effect_id,
                        canonical_hash(evaluation.result),
                        recorded=False,
                    )
                if evaluation.status != "RUNNING":
                    raise ValueError(f"evaluation cannot be published from {evaluation.status}")
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

                artifact_ids = {
                    filename: uuid7() for filename in document_package_artifacts(reviewed)
                }
                reviewed["artifacts"] = [
                    {
                        "artifactId": str(artifact_id),
                        "filename": filename,
                        "downloadRef": f"artifact://{artifact_id}",
                    }
                    for filename, artifact_id in artifact_ids.items()
                ]
                reviewed["provenance"] = {
                    **dict(reviewed.get("provenance") or {}),
                    "publishedInputHash": published_input_hash,
                    "runId": str(run_id),
                    "evaluationId": str(evaluation_id),
                    "effectId": effect_id,
                }
                reviewed["contentHash"] = canonical_hash(
                    {key: value for key, value in reviewed.items() if key != "contentHash"}
                )
                artifact_payloads = document_package_artifacts(reviewed)
                artifact_root = Path(
                    os.environ.get("SWARMCORE_ARTIFACT_ROOT", ".tmp/artifacts")
                ).resolve()
                artifact_rows: list[Artifact] = []
                for filename, content in artifact_payloads.items():
                    artifact_id = artifact_ids[filename]
                    safe_filename = filename.replace("\\", "/").lstrip("/")
                    object_key = _document_artifact_object_key(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        run_id=run_id,
                        artifact_id=artifact_id,
                        filename=safe_filename,
                    )
                    target = (artifact_root / object_key).resolve()
                    if artifact_root not in target.parents:
                        raise ValueError("document artifact path escapes artifact root")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    created_paths.append(target)
                    artifact_rows.append(
                        Artifact(
                            id=artifact_id,
                            tenant_id=tenant_id,
                            project_id=project_id,
                            run_id=run_id,
                            kind="document-structuring-output",
                            filename=safe_filename,
                            media_type=_document_artifact_media_type(safe_filename),
                            object_key=object_key,
                            size_bytes=len(content),
                            sha256=hashlib.sha256(content).hexdigest(),
                            status="AVAILABLE",
                            data_classification="internal",
                            retention_until=datetime.now(UTC) + timedelta(days=1_095),
                        )
                    )

                for document in reviewed.get("documents") or []:
                    version_id = UUID(str(document["documentVersionId"]))
                    snapshot = await session.scalar(
                        select(DocumentUsageSnapshot).where(
                            DocumentUsageSnapshot.evaluation_id == evaluation_id,
                            DocumentUsageSnapshot.business_document_version_id == version_id,
                            DocumentUsageSnapshot.tenant_id == tenant_id,
                            DocumentUsageSnapshot.project_id == project_id,
                        )
                    )
                    if snapshot is None:
                        raise LookupError("structured result targets an unfrozen document version")
                    version = await session.scalar(
                        select(BusinessDocumentVersion).where(
                            BusinessDocumentVersion.id == version_id,
                            BusinessDocumentVersion.tenant_id == tenant_id,
                            BusinessDocumentVersion.project_id == project_id,
                        )
                    )
                    if version is None:
                        raise LookupError("document version is not available")
                    source_document = await session.scalar(
                        select(BusinessDocument).where(
                            BusinessDocument.id == version.business_document_id,
                            BusinessDocument.tenant_id == tenant_id,
                            BusinessDocument.project_id == project_id,
                        )
                    )
                    if source_document is None:
                        raise LookupError("document metadata is not available")
                    existing = list(
                        (
                            await session.scalars(
                                select(DocumentProcessingResult)
                                .where(
                                    DocumentProcessingResult.business_document_version_id
                                    == version_id,
                                    DocumentProcessingResult.tenant_id == tenant_id,
                                    DocumentProcessingResult.project_id == project_id,
                                    DocumentProcessingResult.result_type == "STRUCTURED_PACKAGE",
                                )
                                .order_by(DocumentProcessingResult.result_version.desc())
                            )
                        ).all()
                    )
                    document_result = {
                        **dict(document),
                        "packageContentHash": reviewed["contentHash"],
                        "crossFormatConsistency": reviewed["crossFormatConsistency"],
                        "quality": dict(reviewed.get("quality") or {}),
                        "qualityFlags": list(reviewed.get("qualityFlags") or []),
                        "artifacts": list(reviewed["artifacts"]),
                        "provenance": dict(reviewed["provenance"]),
                    }
                    if existing and canonical_hash(existing[0].result) == canonical_hash(
                        document_result
                    ):
                        continue
                    evidence = [
                        {
                            **dict(value),
                            "fieldPath": field.get("fieldPath"),
                        }
                        for field in document.get("fields") or []
                        for value in field.get("evidenceRefs") or []
                        if isinstance(value, dict)
                    ]
                    session.add(
                        DocumentProcessingResult(
                            tenant_id=tenant_id,
                            project_id=project_id,
                            business_document_version_id=version_id,
                            result_type="STRUCTURED_PACKAGE",
                            result_version=(int(existing[0].result_version) + 1 if existing else 1),
                            status=("CONFIRMED" if reviewed.get("humanReview") else "READY"),
                            schema_ref=str(reviewed["schemaVersion"]),
                            producer_ref="agent://document/structurer@1",
                            result=document_result,
                            evidence=evidence,
                            confirmed_by=(
                                str(context.execution_id) if reviewed.get("humanReview") else None
                            ),
                            confirmed_at=(
                                datetime.now(UTC) if reviewed.get("humanReview") else None
                            ),
                        )
                    )
                    version.processing_status = "READY"
                    source_document.status = "AVAILABLE"
                    organization = document.get("organization")
                    if isinstance(organization, dict):
                        suggested_name = str(organization.get("suggestedName") or "").strip()
                        suggested_category = str(organization.get("category") or "").strip()
                        suggested_tags = [
                            str(value).strip()
                            for value in organization.get("tags") or []
                            if str(value).strip()
                        ]
                        if suggested_name:
                            source_document.name = suggested_name[:512]
                        if suggested_category:
                            source_document.category = suggested_category[:128]
                        source_document.tags = list(
                            dict.fromkeys([*source_document.tags, *suggested_tags])
                        )
                    processing_run = await session.scalar(
                        select(DocumentProcessingRun)
                        .where(
                            DocumentProcessingRun.business_document_version_id == version_id,
                            DocumentProcessingRun.tenant_id == tenant_id,
                            DocumentProcessingRun.project_id == project_id,
                        )
                        .order_by(DocumentProcessingRun.attempt.desc())
                        .with_for_update()
                    )
                    if processing_run is not None:
                        session.add(
                            DocumentProcessingEvent(
                                tenant_id=tenant_id,
                                project_id=project_id,
                                processing_run_id=processing_run.id,
                                business_document_version_id=version_id,
                                event_seq=int(processing_run.next_event_seq or 1),
                                type="document.agent.completed",
                                stage="EXTRACTING",
                                payload={
                                    "agentRef": "agent://document/structurer@1",
                                    "modelRef": "model://document-nlp@1",
                                    "resultHash": reviewed["contentHash"],
                                    "reviewed": bool(reviewed.get("humanReview")),
                                },
                                output_hash=reviewed["contentHash"],
                                tool_ref="agent://document/structurer@1",
                                actor_id=str(context.execution_id),
                            )
                        )
                        processing_run.next_event_seq = int(processing_run.next_event_seq or 1) + 1

                evaluation.result = reviewed
                evaluation.status = "SUCCEEDED"
                item.status = "COMPLETED"
                session.add_all(artifact_rows)
                primary_artifact = artifact_ids["structured-document.json"]
                report = Report(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    work_item_id=item.id,
                    evaluation_id=evaluation.id,
                    format="JSON",
                    template_version=evaluation.report_template_version,
                    result_schema_version=evaluation.output_schema_version,
                    content=reviewed,
                    artifact_id=primary_artifact,
                    content_hash=reviewed["contentHash"],
                )
                session.add(report)
                await session.flush()
                session.add_all(
                    [
                        OutboxEvent(
                            id=uuid7(),
                            tenant_id=tenant_id,
                            aggregate_id=evaluation.id,
                            destination="nats",
                            partition_key=str(evaluation.id),
                            source_id=evaluation.id,
                            type="capability.document-structuring.completed",
                            payload={
                                "evaluationId": str(evaluation.id),
                                "runId": str(run_id),
                                "effectId": effect_id,
                                "resultHash": reviewed["contentHash"],
                                "artifactIds": [str(value) for value in artifact_ids.values()],
                            },
                        ),
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
                        ),
                    ]
                )
                await AuditRepository().append(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    actor_id=str(context.execution_id),
                    action="document.structured-package-published",
                    resource_type="evaluation",
                    resource_id=str(evaluation.id),
                    run_id=run_id,
                    metadata={
                        "effectId": effect_id,
                        "resultHash": reviewed["contentHash"],
                        "documentCount": len(reviewed.get("documents") or []),
                        "artifactCount": len(artifact_rows),
                        "humanReviewed": bool(reviewed.get("humanReview")),
                    },
                )
                return self._receipt(
                    evaluation_id,
                    effect_id,
                    reviewed["contentHash"],
                    recorded=True,
                )
        except Exception:
            for path in created_paths:
                path.unlink(missing_ok=True)
            raise


def _document_artifact_media_type(filename: str) -> str:
    if filename.endswith(".json"):
        return "application/json"
    if filename.endswith(".md"):
        return "text/markdown; charset=utf-8"
    if filename.endswith(".csv"):
        return "text/csv; charset=utf-8"
    return "application/octet-stream"


def _document_artifact_object_key(
    *,
    tenant_id: UUID,
    project_id: UUID,
    run_id: UUID,
    artifact_id: UUID,
    filename: str,
) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{tenant_id}/{project_id}/runs/{run_id}/document-structuring/{artifact_id}{suffix}"


def capability_executors(
    sessions: async_sessionmaker[Any],
    *,
    github_token: str = "",
    github_api_url: str = "",
    calibration_sandbox_enabled: bool = False,
    calibration_sandbox_image: str = "",
    calibration_sandbox_docker_binary: str = "docker",
    calibration_sandbox_timeout_seconds: int = 600,
    supplier_risk_allowed_hosts: tuple[str, ...] = (
        "www.ccgp.gov.cn",
        "api.qichacha.com",
        "open.api.tianyancha.com",
    ),
    supplier_risk_timeout_seconds: int = 30,
) -> dict[str, Any]:
    recorder = EvaluationRecorderExecutor(sessions)
    return {
        "contract.document_read": document_read,
        "contract.rules_evaluate": rules_evaluate,
        "contract.cross_file_consistency": cross_file_consistency,
        "contract.integrity_finalize": integrity_finalize,
        "workbench.record_evaluation": recorder,
        "report.render": report_render,
        "contract.post_evaluation": post_evaluation_evaluate,
        "contract.post_evaluation_assemble": post_evaluation_assemble,
        "resource.read_bound": BoundResourceReadExecutor(sessions),
        "document.read_versions": BoundDocumentReadExecutor(sessions),
        "document.structure_prepare": document_structuring_prepare,
        "document.analysis_select": document_structuring_analysis_select,
        "document.quality_check": document_structuring_quality_check,
        "document.review_select": document_structuring_review_select,
        "document.publish": DocumentStructuringPublisherExecutor(sessions),
        "evidence.search": evidence_search,
        "evidence.search_contextual": BoundEvidenceSearchExecutor(sessions),
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
        "invoice.enterprise_status_check": invoice_enterprise_status_check,
        "invoice.party_check": invoice_party_check,
        "invoice.commercial_match": invoice_commercial_match,
        "invoice.payment_gate": invoice_payment_gate,
        "invoice.finalize": invoice_finalize,
        "report.render_invoice_assurance": invoice_assurance_report_render,
        "workbench.record_invoice_assurance": InvoiceAssuranceRecorderExecutor(sessions),
        "contract_performance.source_collect": contract_performance_source_collect,
        "document.parse": contract_performance_document_parse,
        "document.ocr": contract_performance_document_ocr,
        "contract_performance.plan_normalize": contract_performance_plan_normalize,
        "contract_performance.schedule_build": contract_performance_schedule_build,
        "contract_performance.change_apply": contract_performance_change_apply,
        "contract_performance.evidence_match": contract_performance_evidence_match,
        "contract_performance.status_calculate": contract_performance_status_calculate,
        "contract_performance.finalize": contract_performance_finalize,
        "report.render_contract_performance": contract_performance_report_render,
        "workbench.record_contract_performance": ContractPerformanceRecorderExecutor(sessions),
        "procurement.consistency_compare": procurement_consistency_compare,
        "supplier.risk_collect": SupplierRiskCollectExecutor(
            allowed_hosts=supplier_risk_allowed_hosts,
            timeout_seconds=supplier_risk_timeout_seconds,
        ),
        "supplier.performance_calculate": supplier_performance_calculate,
        "supplier.risk_decide": supplier_risk_decide,
        "supplier.history_diff": supplier_history_diff,
        "procurement_supplier_risk.finalize": procurement_supplier_risk_finalize,
        "report.render_procurement_supplier_risk": procurement_supplier_risk_report_render,
        "workbench.record_procurement_supplier_risk": ProcurementSupplierRiskRecorderExecutor(
            sessions
        ),
        "github.get_issue": GitHubCalibrationExecutor(
            "issue", token=github_token, base_url=github_api_url
        ),
        "github.get_discussion": GitHubCalibrationExecutor(
            "discussion", token=github_token, base_url=github_api_url
        ),
        "github.get_pull_evidence": GitHubCalibrationExecutor(
            "pull", token=github_token, base_url=github_api_url
        ),
        "calibration.freeze_evidence": calibration_freeze_evidence,
        "calibration.route_select": calibration_route_select,
        "sandbox.verify_repository": RepositorySandboxVerifier(
            enabled=calibration_sandbox_enabled,
            image=calibration_sandbox_image,
            docker_binary=calibration_sandbox_docker_binary,
            timeout_seconds=calibration_sandbox_timeout_seconds,
            github_token=github_token,
        ),
        "calibration.quality_score": calibration_quality_score,
        "calibration.attempt_select": calibration_attempt_select,
        "calibration.finalize": calibration_finalize,
        "report.render_swarm_calibration": calibration_report_render,
        "workbench.record_swarm_calibration": SwarmCalibrationRecorderExecutor(sessions),
        "ai.quality_benchmark": ai_quality_benchmark,
        "ai.quality_finalize": ai_quality_finalize,
        "report.render_ai_quality": ai_quality_report,
        "workbench.record_ai_quality": recorder,
        "report.generate_confirmed": ConfirmedEvaluationReportGenerator(sessions),
    }
