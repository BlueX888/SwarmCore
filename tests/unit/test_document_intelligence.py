from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from swarmcore_application import (
    CrossFileRule,
    DocumentIntelligenceError,
    DocumentIntelligenceService,
    InMemoryIntelligenceStore,
    RetryPolicy,
    calculate_accuracy_baseline,
    evaluate_cross_file_consistency,
    pdf_report_payload,
    render_evidence_pdf,
)
from swarmcore_capability_contract_integrity import SCHEMAS

EXTRACTION_SCHEMA = SCHEMAS["schema://contract/document-extraction@1"]


class Parser:
    name = "fixture-ocr"
    version = "1"

    def __init__(self, failures: int = 0) -> None:
        self.calls = 0
        self._failures = failures

    async def parse(self, request: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.calls <= self._failures:
            raise TimeoutError("provider timed out")
        return {
            "provider": self.name,
            "providerVersion": self.version,
            "pages": [{"page": 1, "text": f"contract {request['sha256'][:8]}"}],
        }


class Agent:
    name = "fixture-extractor"
    version = "1"

    def __init__(self, *, confidence: float = 0.95, invalid: bool = False) -> None:
        self.calls = 0
        self._confidence = confidence
        self._invalid = invalid

    async def extract(self, parsed: Any, *, output_schema: dict[str, Any]) -> dict[str, Any]:
        del parsed, output_schema
        self.calls += 1
        if self._invalid:
            return {"schemaVersion": "schema://contract/document-extraction@1"}
        evidence = [{"page": 1, "boundingBox": [0.1, 0.1, 0.9, 0.2], "text": "ACME"}]
        return {
            "schemaVersion": "schema://contract/document-extraction@1",
            "classification": {
                "documentType": "contract",
                "confidence": self._confidence,
                "evidence": evidence,
            },
            "fields": [
                {
                    "name": "party",
                    "value": "ACME",
                    "confidence": self._confidence,
                    "evidence": evidence,
                }
            ],
        }


async def _process(
    parser: Parser, agent: Agent, store: InMemoryIntelligenceStore, *, digest: str = "a" * 64
) -> Any:
    return await DocumentIntelligenceService(
        parser,
        agent,
        store,
        retry_policy=RetryPolicy(attempts=3, timeout_seconds=1),
    ).process(
        blob_id="00000000-0000-0000-0000-000000000001",
        sha256=digest,
        media_type="application/pdf",
        capability_token="scoped-token",
        output_schema=EXTRACTION_SCHEMA,
        schema_version="schema://contract/document-extraction@1",
    )


@pytest.mark.asyncio
async def test_document_extraction_is_schema_checked_and_idempotent() -> None:
    parser = Parser()
    agent = Agent()
    store = InMemoryIntelligenceStore()
    first = await _process(parser, agent, store)
    second = await _process(parser, agent, store)
    assert first == second
    assert first.status == "COMPLETED"
    assert parser.calls == agent.calls == 1


@pytest.mark.asyncio
async def test_concurrent_retry_does_not_duplicate_extraction() -> None:
    parser = Parser()
    agent = Agent()
    store = InMemoryIntelligenceStore()
    service = DocumentIntelligenceService(parser, agent, store)
    arguments = {
        "blob_id": "00000000-0000-0000-0000-000000000001",
        "sha256": "b" * 64,
        "media_type": "application/pdf",
        "capability_token": "scoped-token",
        "output_schema": EXTRACTION_SCHEMA,
        "schema_version": "schema://contract/document-extraction@1",
    }
    first, second = await asyncio.gather(service.process(**arguments), service.process(**arguments))
    assert first == second
    assert parser.calls == agent.calls == 1


@pytest.mark.asyncio
async def test_low_confidence_requires_human_review() -> None:
    result = await _process(Parser(), Agent(confidence=0.4), InMemoryIntelligenceStore())
    assert result.status == "REVIEW_REQUIRED"
    assert result.review_reasons == (
        "CLASSIFICATION_CONFIDENCE_LOW",
        "FIELD_CONFIDENCE_LOW:party",
    )


@pytest.mark.asyncio
async def test_invalid_model_output_never_reaches_hard_checks() -> None:
    with pytest.raises(DocumentIntelligenceError) as raised:
        await _process(Parser(), Agent(invalid=True), InMemoryIntelligenceStore())
    assert raised.value.diagnostic.code == "MODEL_OUTPUT_SCHEMA_INVALID"
    assert not raised.value.diagnostic.retryable


@pytest.mark.asyncio
async def test_provider_timeout_retries_with_diagnostic() -> None:
    parser = Parser(failures=3)
    with pytest.raises(DocumentIntelligenceError) as raised:
        await _process(parser, Agent(), InMemoryIntelligenceStore())
    assert raised.value.diagnostic.code == "OCR_RETRY_EXHAUSTED"
    assert raised.value.diagnostic.attempts == 3
    assert raised.value.diagnostic.retryable


@pytest.mark.asyncio
async def test_cross_file_check_pdf_and_accuracy_baseline() -> None:
    first = await _process(Parser(), Agent(), InMemoryIntelligenceStore(), digest="c" * 64)
    second = first.model_copy(deep=True)
    assert second.extraction is not None
    second.extraction.fields[0].value = "Other"
    findings = evaluate_cross_file_consistency(
        [first, second],
        [
            CrossFileRule(
                key="party-consistency",
                field="party",
                documentTypes=("contract", "contract"),
            )
        ],
    )
    assert [item.code for item in findings] == ["CROSS_FILE_VALUE_MISMATCH"]
    pdf = render_evidence_pdf("Evidence report", [first, second], findings)
    assert pdf.startswith(b"%PDF-1.4") and pdf.endswith(b"%%EOF\n")
    assert pdf_report_payload(pdf)["mediaType"] == "application/pdf"
    assert pdf == render_evidence_pdf("Evidence report", [first, second], findings)
    baseline = calculate_accuracy_baseline(
        [{("party", "ACME")}, {("party", "Other")}], [first, second]
    )
    assert baseline.precision == baseline.recall == 1
    assert baseline.review_rate == 0


def test_pdf_report_preserves_chinese_text_font() -> None:
    pdf = render_evidence_pdf("采购履约后评价报告", [], [])

    assert b"STSong-Light" in pdf


def test_deidentified_accuracy_fixture_has_frozen_baseline() -> None:
    fixture = json.loads(
        Path("tests/fixtures/business/document-intelligence-baseline.json").read_text(
            encoding="utf-8"
        )
    )
    samples = fixture["samples"]
    true_positive = sum(
        len(
            {tuple(value) for value in sample["expected"]}
            & {tuple(value) for value in sample["predicted"]}
        )
        for sample in samples
    )
    predicted = sum(len(sample["predicted"]) for sample in samples)
    expected = sum(len(sample["expected"]) for sample in samples)
    actual = {
        "precision": true_positive / predicted,
        "recall": true_positive / expected,
        "reviewRate": sum(bool(sample["reviewRequired"]) for sample in samples) / len(samples),
    }
    assert actual == fixture["baseline"]
