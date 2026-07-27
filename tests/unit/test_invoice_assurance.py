from __future__ import annotations

import json
from pathlib import Path

from swarmcore_application.invoice_assurance import (
    SCHEMA_VERSION,
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

FIXTURE_XML = Path("tests/fixtures/documents/demo-invoice.xml")
GOLDEN = Path("tests/fixtures/business/invoice-assurance-golden.json")


def _golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_parse_xml_demo_invoice_extracts_structured_fields() -> None:
    content = FIXTURE_XML.read_text(encoding="utf-8")
    fact_set = parse_invoice(
        content,
        media_type="application/xml",
        document_version_id="doc-demo-v1",
    )

    assert fact_set["parseStatus"] == "STRUCTURED"
    assert fact_set["needsFieldConfirmation"] is False
    assert fact_set["invoiceNumber"] == "99992000000000000001"
    assert fact_set["seller"]["taxId"] == "91310000MA0DEMOSELL"
    assert fact_set["totals"]["amountIncludingTax"] == 1130.0
    assert fact_set["totals"]["taxAmount"] == 130.0
    assert len(fact_set["lines"]) == 1
    assert fact_set["lines"][0]["amount"] == 1000.0
    assert "doc-demo-v1" in fact_set["evidenceRefs"]


def test_parse_non_structured_requires_field_confirmation_without_inventing_numbers() -> None:
    fact_set = parse_invoice("scanned image bytes", media_type="image/png")

    assert fact_set["needsFieldConfirmation"] is True
    assert fact_set["parseStatus"] == "UNSUPPORTED"
    assert fact_set["invoiceNumber"] is None
    assert fact_set["totals"]["amountIncludingTax"] is None
    assert "NON_STRUCTURED_INPUT" in fact_set["qualityFlags"]


def test_arithmetic_check_fails_when_totals_do_not_close() -> None:
    fact_set = {
        "totals": {
            "amountExcludingTax": 1000.0,
            "taxAmount": 130.0,
            "amountIncludingTax": 1200.0,
        },
        "lines": [],
        "evidenceRefs": ["e1"],
    }
    results = arithmetic_check(fact_set)
    failed = [item for item in results if item["ruleId"] == "ARITHMETIC_TOTALS_CLOSE"]

    assert failed
    assert failed[0]["status"] == "FAIL"
    assert failed[0]["blocking"] is True
    assert abs(failed[0]["delta"]) == 70.0


def test_paid_duplicate_blocks_payment() -> None:
    fact_set = {
        "invoiceCode": "",
        "invoiceNumber": "99992000000000000001",
        "isRed": False,
        "evidenceRefs": ["e1"],
    }
    duplication = deduplicate(
        fact_set,
        [
            {
                "invoiceNumber": "99992000000000000001",
                "status": "PAID",
                "voucherId": "V-1",
                "amount": 1130.0,
            }
        ],
    )
    assert duplication["blocking"] is True
    assert duplication["reasonCode"] == "PAID_DUPLICATE"

    gate = payment_gate(
        {
            "verification": {"status": "FACE_MATCHED"},
            "duplication": duplication,
            "ruleResults": [],
            "commercialMatch": {"status": "PASS"},
        }
    )
    assert gate["status"] == "PAYMENT_BLOCKED"
    assert "PAID_DUPLICATE" in gate["hardBlocks"]


def test_seller_tax_mismatch_is_critical_fail() -> None:
    fact_set = {
        "seller": {"taxId": "91310000MA0OTHER", "bankAccount": "6222000000000001"},
        "buyer": {"taxId": "91110000MA0DEMOBUY"},
        "evidenceRefs": ["e1"],
    }
    vendor = {
        "taxId": "91310000MA0DEMOSELL",
        "approvedBankAccounts": [{"accountNumber": "6222000000000001"}],
    }
    results = party_check(fact_set, vendor, buyer_tax_id="91110000MA0DEMOBUY")
    tax_rule = next(item for item in results if item["ruleId"] == "PARTY_SELLER_TAX_MATCH")

    assert tax_rule["status"] == "FAIL"
    assert tax_rule["severity"] == "CRITICAL"
    assert tax_rule["blocking"] is True


def test_unapproved_bank_account_is_critical_fail() -> None:
    fact_set = {
        "seller": {
            "taxId": "91310000MA0DEMOSELL",
            "bankAccount": "6222999999999999",
        },
        "evidenceRefs": ["e1"],
    }
    vendor = {
        "taxId": "91310000MA0DEMOSELL",
        "approvedBankAccounts": [{"accountNumber": "6222000000000001"}],
    }
    results = party_check(fact_set, vendor)
    bank_rule = next(item for item in results if item["ruleId"] == "PARTY_BANK_APPROVED")

    assert bank_rule["status"] == "FAIL"
    assert bank_rule["severity"] == "CRITICAL"
    assert bank_rule["blocking"] is True


def test_official_verify_pending_human_and_unavailable_connector() -> None:
    fact_set = {"invoiceNumber": "1", "totals": {}, "evidenceRefs": []}

    pending = official_verify(fact_set, mode="HUMAN_ASSISTED")
    assert pending["status"] == "PENDING_HUMAN"

    unavailable = official_verify(fact_set, mode="AUTHORIZED_CONNECTOR")
    assert unavailable["status"] == "UNAVAILABLE"

    matched = official_verify(
        fact_set,
        mode="HUMAN_ASSISTED",
        human_receipt={"status": "FACE_MATCHED", "verifiedAt": "2026-03-20T10:00:00+08:00"},
    )
    assert matched["status"] == "FACE_MATCHED"


def test_happy_path_payment_ready_and_golden_fixture() -> None:
    golden = _golden()
    fact_set = golden["factSet"]
    snapshot = read_business_snapshot({**golden["businessSnapshot"], "vendor": golden["vendor"]})
    verification = official_verify(
        fact_set,
        mode="HUMAN_ASSISTED",
        human_receipt=golden["humanReceipt"],
    )
    rules = [
        *arithmetic_check(fact_set),
        *party_check(fact_set, golden["vendor"], buyer_tax_id="91110000MA0DEMOBUY"),
    ]
    duplication = deduplicate(fact_set, snapshot["apLedger"])
    match_result = commercial_match(fact_set, snapshot)
    gate = payment_gate(
        {
            "verification": verification,
            "duplication": duplication,
            "ruleResults": rules,
            "commercialMatch": match_result,
            "budget": snapshot["budget"],
        }
    )
    result = finalize_invoice_assurance(
        fact_set=fact_set,
        verification=verification,
        business_snapshot=snapshot,
        rule_results=rules,
        match_result=match_result,
        duplication=duplication,
        gate_result=gate,
        narrative={"executiveSummary": "演示发票通过付款前置校验。"},
        provenance={"parserVersion": "parser://invoice-assurance/xml@1"},
        title="演示发票一致性校验",
        as_of="2026-03-20",
    )

    assert verification["status"] == golden["expected"]["verificationStatus"]
    assert match_result["status"] == "PASS"
    assert gate["status"] == "PAYMENT_READY"
    assert result["outcome"] == golden["expected"]["outcome"]
    assert result["schemaVersion"] == SCHEMA_VERSION
    assert result["invoiceFactSet"]["totals"]["amountIncludingTax"] == (
        golden["expected"]["amountIncludingTax"]
    )
    validated = validate_invoice_assurance_result(result)
    assert validated["outcome"] == "PAYMENT_READY"
    lines = invoice_assurance_report_lines(result)
    assert any("可进入付款队列" in line for line in lines)
    assert any("99992000000000000001" in line for line in lines)


def test_missing_vendor_is_unknown_or_warn() -> None:
    results = party_check(
        {"seller": {"taxId": "91310000MA0DEMOSELL"}, "evidenceRefs": []},
        None,
    )
    statuses = {item["ruleId"]: item["status"] for item in results}
    assert statuses["PARTY_VENDOR_PRESENT"] == "UNKNOWN"
    assert statuses["PARTY_SELLER_TAX_MATCH"] == "UNKNOWN"
    assert statuses["PARTY_BANK_APPROVED"] == "WARN"


def test_red_credit_still_paying_is_hard_block() -> None:
    fact_set = {
        "invoiceNumber": "RED-1",
        "isRed": True,
        "blueInvoiceRef": {"invoiceNumber": "BLUE-1"},
        "evidenceRefs": [],
    }
    duplication = deduplicate(fact_set, [])
    assert duplication["reasonCode"] == "RED_CREDIT_STILL_PAYING"
    gate = payment_gate(
        {
            "verification": {"status": "FACE_MATCHED"},
            "duplication": duplication,
            "ruleResults": [],
            "commercialMatch": {"status": "PASS"},
        }
    )
    assert gate["status"] == "PAYMENT_BLOCKED"
    assert "RED_CREDIT_STILL_PAYING" in gate["hardBlocks"]
