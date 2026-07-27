from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from swarmcore_persistence.repositories import canonical_hash

SCHEMA_VERSION = "schema://invoice-assurance/result@1"
RULE_VERSION = "rule://invoice-assurance@1"
PARSER_VERSION = "parser://invoice-assurance/xml@1"
_MONEY_TOLERANCE = Decimal("0.01")
_OUTCOMES = frozenset({"PAYMENT_READY", "REVIEW_REQUIRED", "PAYMENT_BLOCKED"})
_RULE_STATUSES = frozenset({"PASS", "WARN", "FAIL", "UNKNOWN", "NOT_APPLICABLE"})
_VERIFICATION_STATUSES = frozenset(
    {"FACE_MATCHED", "FACE_MISMATCH", "NOT_FOUND", "UNAVAILABLE", "PENDING_HUMAN"}
)
_HARD_BLOCK_REASON_CODES = frozenset(
    {
        "FACE_MISMATCH",
        "NOT_FOUND",
        "PAID_DUPLICATE",
        "RED_CREDIT_STILL_PAYING",
        "SELLER_TAX_MISMATCH",
        "UNAPPROVED_BANK_ACCOUNT",
    }
)

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "invoiceNumber": ("发票号码", "InvoiceNumber", "fpHm", "fphm", "EIinvoiceNumber"),
    "invoiceCode": ("发票代码", "InvoiceCode", "fpDm", "fpdm"),
    "issueDate": ("开票日期", "IssueDate", "kprq", "InvoiceDate"),
    "invoiceType": ("发票类型", "InvoiceType", "fplx", "InvoiceTypeCode"),
    "checkCode": ("校验码", "CheckCode", "jym"),
    "buyerName": ("购买方名称", "BuyerName", "PurchaserName", "gmfmc"),
    "buyerTaxId": (
        "购买方统一社会信用代码",
        "购买方纳税人识别号",
        "BuyerTaxId",
        "BuyerTaxID",
        "PurchaserTaxID",
        "gmfsbh",
    ),
    "sellerName": ("销售方名称", "SellerName", "SalesName", "xsfmc"),
    "sellerTaxId": (
        "销售方统一社会信用代码",
        "销售方纳税人识别号",
        "SellerTaxId",
        "SellerTaxID",
        "SalesTaxID",
        "xsfsbh",
    ),
    "amountExcludingTax": ("合计金额", "TotalAmount", "AmountExcludingTax", "hjje"),
    "taxAmount": ("合计税额", "TotalTax", "TaxAmount", "hjse"),
    "amountIncludingTax": ("价税合计", "AmountInTax", "AmountIncludingTax", "jshj"),
    "currency": ("币种", "Currency", "CurrencyCode"),
    "bankAccount": ("销售方银行账号", "收款账号", "BankAccount", "SellerBankAccount"),
    "bankName": ("销售方开户行", "收款银行", "BankName", "SellerBankName"),
    "isRed": ("是否红字", "IsRedInvoice", "RedFlag"),
    "blueInvoiceNumber": ("蓝字发票号码", "BlueInvoiceNumber", "OriginalInvoiceNumber"),
    "blueInvoiceCode": ("蓝字发票代码", "BlueInvoiceCode", "OriginalInvoiceCode"),
}

_LINE_ALIASES: dict[str, tuple[str, ...]] = {
    "name": ("项目名称", "ItemName", "GoodsName", "xmmc"),
    "spec": ("规格型号", "Spec", "Specification"),
    "unit": ("单位", "Unit", "MeasurementDimension"),
    "quantity": ("数量", "Quantity", "Qty"),
    "unitPrice": ("单价", "UnitPrice", "Price"),
    "amount": ("金额", "Amount", "LineAmount"),
    "taxRate": ("税率", "TaxRate", "Rate"),
    "taxAmount": ("税额", "TaxAmount", "LineTax"),
}

_LINE_CONTAINER_NAMES = frozenset(
    {
        "商品行",
        "明细",
        "明细行",
        "发票行",
        "IssuItemInformation",
        "ItemInformation",
        "InvoiceLine",
        "GoodsInfos",
        "GoodsInfo",
        "Line",
    }
)


def _decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a number")
    text = str(value).strip().replace(",", "")
    if not text:
        raise ValueError(f"{field} must be a number")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc


def _optional_decimal(value: Any, *, field: str) -> Decimal | None:
    if value is None or value == "":
        return None
    return _decimal(value, field=field)


def _number(value: Decimal | None, places: str = "0.01") -> float | None:
    if value is None:
        return None
    return float(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _normalize_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _alias_match(local: str, aliases: Sequence[str]) -> bool:
    normalized = _normalize_name(local)
    return any(_normalize_name(alias) == normalized for alias in aliases)


def _iter_elements(root: ET.Element) -> Iterable[ET.Element]:
    yield root
    yield from root.iter()


def _find_text(root: ET.Element, aliases: Sequence[str]) -> str | None:
    for element in _iter_elements(root):
        if _alias_match(_local_name(element.tag), aliases):
            text = "".join(element.itertext()).strip()
            if text:
                return text
        for key, value in element.attrib.items():
            if _alias_match(_local_name(key), aliases) and str(value).strip():
                return str(value).strip()
    return None


def _field(
    value: Any,
    *,
    confidence: str,
    source: str,
    locator: str | None = None,
    document_version_id: str | None = None,
) -> dict[str, Any]:
    return {
        "value": value,
        "confidence": confidence,
        "source": source,
        "locator": locator,
        "documentVersionId": document_version_id,
        "qualityFlags": [] if confidence == "HIGH" else ["LOW_CONFIDENCE"],
    }


def _empty_fact_set(
    *,
    document_version_id: str | None,
    needs_confirmation: bool,
    parse_status: str,
    media_type: str | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "invoiceType": None,
        "invoiceCode": None,
        "invoiceNumber": None,
        "issueDate": None,
        "buyer": {"name": None, "taxId": None},
        "seller": {"name": None, "taxId": None, "bankAccount": None, "bankName": None},
        "lines": [],
        "totals": {
            "amountExcludingTax": None,
            "taxAmount": None,
            "amountIncludingTax": None,
            "currency": "CNY",
        },
        "isRed": False,
        "blueInvoiceRef": None,
        "fields": {},
        "evidenceRefs": (
            [str(document_version_id)] if document_version_id is not None else []
        ),
        "needsFieldConfirmation": needs_confirmation,
        "parseStatus": parse_status,
        "parserVersion": PARSER_VERSION,
        "mediaType": media_type,
        "qualityFlags": [reason],
    }


def _party_from_fields(
    fields: Mapping[str, Any],
    *,
    name_key: str,
    tax_key: str,
    bank_account_key: str | None = None,
    bank_name_key: str | None = None,
) -> dict[str, Any]:
    party: dict[str, Any] = {
        "name": (fields.get(name_key) or {}).get("value"),
        "taxId": (fields.get(tax_key) or {}).get("value"),
    }
    if bank_account_key is not None:
        party["bankAccount"] = (fields.get(bank_account_key) or {}).get("value")
    if bank_name_key is not None:
        party["bankName"] = (fields.get(bank_name_key) or {}).get("value")
    return party


def _totals_from_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    currency = (fields.get("currency") or {}).get("value") or "CNY"
    return {
        "amountExcludingTax": (fields.get("amountExcludingTax") or {}).get("value"),
        "taxAmount": (fields.get("taxAmount") or {}).get("value"),
        "amountIncludingTax": (fields.get("amountIncludingTax") or {}).get("value"),
        "currency": currency,
    }


def _money_field_value(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return _number(_decimal(raw, field="money"))
    except ValueError:
        return None


def _parse_xml_invoice(
    content: str,
    *,
    document_version_id: str | None,
    media_type: str | None,
) -> dict[str, Any]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return _empty_fact_set(
            document_version_id=document_version_id,
            needs_confirmation=True,
            parse_status="PARSE_FAILED",
            media_type=media_type,
            reason="XML_PARSE_FAILED",
        )

    fields: dict[str, Any] = {}
    for key, aliases in _FIELD_ALIASES.items():
        text = _find_text(root, aliases)
        if text is None:
            continue
        if key in {
            "amountExcludingTax",
            "taxAmount",
            "amountIncludingTax",
        }:
            value = _money_field_value(text)
            if value is None:
                continue
            fields[key] = _field(
                value,
                confidence="HIGH",
                source="XML",
                locator=aliases[0],
                document_version_id=document_version_id,
            )
        elif key == "isRed":
            fields[key] = _field(
                text.strip() in {"1", "Y", "y", "true", "TRUE", "是", "红字"},
                confidence="HIGH",
                source="XML",
                locator=aliases[0],
                document_version_id=document_version_id,
            )
        else:
            fields[key] = _field(
                text,
                confidence="HIGH",
                source="XML",
                locator=aliases[0],
                document_version_id=document_version_id,
            )

    lines: list[dict[str, Any]] = []
    for element in _iter_elements(root):
        if not _alias_match(_local_name(element.tag), tuple(_LINE_CONTAINER_NAMES)):
            continue
        line_fields: dict[str, Any] = {}
        for key, aliases in _LINE_ALIASES.items():
            text = _find_text(element, aliases)
            if text is None:
                # Prefer direct children for line-scoped values.
                for child in list(element):
                    if _alias_match(_local_name(child.tag), aliases):
                        text = "".join(child.itertext()).strip() or None
                        break
            if text is None:
                continue
            if key in {"quantity", "unitPrice", "amount", "taxRate", "taxAmount"}:
                value = _money_field_value(text)
                if value is None:
                    continue
                line_fields[key] = value
            else:
                line_fields[key] = text
        if line_fields:
            lines.append(
                {
                    "lineId": f"L{len(lines) + 1}",
                    **line_fields,
                    "confidence": "HIGH",
                    "source": "XML",
                }
            )

    is_red = bool((fields.get("isRed") or {}).get("value"))
    blue_number = (fields.get("blueInvoiceNumber") or {}).get("value")
    blue_code = (fields.get("blueInvoiceCode") or {}).get("value")
    blue_ref = None
    if blue_number or blue_code:
        blue_ref = {"invoiceNumber": blue_number, "invoiceCode": blue_code}

    critical_present = any(
        key in fields
        for key in ("invoiceNumber", "amountIncludingTax", "sellerTaxId")
    )
    return {
        "invoiceType": (fields.get("invoiceType") or {}).get("value"),
        "invoiceCode": (fields.get("invoiceCode") or {}).get("value"),
        "invoiceNumber": (fields.get("invoiceNumber") or {}).get("value"),
        "issueDate": (fields.get("issueDate") or {}).get("value"),
        "buyer": _party_from_fields(fields, name_key="buyerName", tax_key="buyerTaxId"),
        "seller": _party_from_fields(
            fields,
            name_key="sellerName",
            tax_key="sellerTaxId",
            bank_account_key="bankAccount",
            bank_name_key="bankName",
        ),
        "lines": lines,
        "totals": _totals_from_fields(fields),
        "isRed": is_red,
        "blueInvoiceRef": blue_ref,
        "fields": fields,
        "evidenceRefs": (
            [str(document_version_id)] if document_version_id is not None else []
        ),
        "needsFieldConfirmation": not critical_present,
        "parseStatus": "STRUCTURED" if critical_present else "PARTIAL",
        "parserVersion": PARSER_VERSION,
        "mediaType": media_type or "application/xml",
        "qualityFlags": [] if critical_present else ["MISSING_CRITICAL_FIELDS"],
    }


def _parse_json_invoice(
    payload: Mapping[str, Any],
    *,
    document_version_id: str | None,
    media_type: str | None,
) -> dict[str, Any]:
    source = payload.get("invoiceFactSet") if isinstance(payload.get("invoiceFactSet"), Mapping) else payload
    if not isinstance(source, Mapping):
        return _empty_fact_set(
            document_version_id=document_version_id,
            needs_confirmation=True,
            parse_status="UNSUPPORTED",
            media_type=media_type,
            reason="NON_STRUCTURED_INPUT",
        )

    def _scalar(key: str, *aliases: str) -> Any:
        for name in (key, *aliases):
            if name in source and source[name] not in (None, ""):
                return source[name]
        nested = source.get("totals")
        if isinstance(nested, Mapping) and key in nested:
            return nested[key]
        party_key = "buyer" if key.startswith("buyer") else "seller" if key.startswith("seller") else None
        if party_key and isinstance(source.get(party_key), Mapping):
            party = source[party_key]
            short = key[len(party_key) :]
            short = short[:1].lower() + short[1:] if short else short
            mapping = {"Name": "name", "TaxId": "taxId", "BankAccount": "bankAccount"}
            return party.get(mapping.get(short, short))
        return None

    totals_raw = source.get("totals") if isinstance(source.get("totals"), Mapping) else {}
    amount_ex = _scalar("amountExcludingTax", "totalAmount", "hjje")
    tax_amount = _scalar("taxAmount", "totalTax", "hjse")
    amount_in = _scalar("amountIncludingTax", "amountInTax", "jshj")
    if amount_ex is None and isinstance(totals_raw, Mapping):
        amount_ex = totals_raw.get("amountExcludingTax")
    if tax_amount is None and isinstance(totals_raw, Mapping):
        tax_amount = totals_raw.get("taxAmount")
    if amount_in is None and isinstance(totals_raw, Mapping):
        amount_in = totals_raw.get("amountIncludingTax")

    def _as_money(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return _number(_decimal(value, field="json-money"))
        except ValueError:
            return None

    lines_raw = source.get("lines")
    lines: list[dict[str, Any]] = []
    if isinstance(lines_raw, list):
        for index, item in enumerate(lines_raw):
            if not isinstance(item, Mapping):
                continue
            line: dict[str, Any] = {
                "lineId": str(item.get("lineId") or f"L{index + 1}"),
                "name": item.get("name") or item.get("itemName"),
                "confidence": "HIGH",
                "source": "JSON",
            }
            for key in ("quantity", "unitPrice", "amount", "taxRate", "taxAmount"):
                money = _as_money(item.get(key))
                if money is not None:
                    line[key] = money
            lines.append(line)

    invoice_number = _scalar("invoiceNumber", "fphm")
    seller_tax = _scalar("sellerTaxId", "sellerTaxID")
    amount_including = _as_money(amount_in)
    fact_set = {
        "invoiceType": _scalar("invoiceType"),
        "invoiceCode": _scalar("invoiceCode", "fpdm"),
        "invoiceNumber": invoice_number,
        "issueDate": _scalar("issueDate", "kprq"),
        "buyer": {
            "name": _scalar("buyerName"),
            "taxId": _scalar("buyerTaxId", "buyerTaxID"),
        },
        "seller": {
            "name": _scalar("sellerName"),
            "taxId": seller_tax,
            "bankAccount": _scalar("bankAccount", "sellerBankAccount"),
            "bankName": _scalar("bankName", "sellerBankName"),
        },
        "lines": lines,
        "totals": {
            "amountExcludingTax": _as_money(amount_ex),
            "taxAmount": _as_money(tax_amount),
            "amountIncludingTax": amount_including,
            "currency": _scalar("currency") or "CNY",
        },
        "isRed": bool(source.get("isRed")),
        "blueInvoiceRef": source.get("blueInvoiceRef"),
        "fields": {},
        "evidenceRefs": (
            [str(document_version_id)] if document_version_id is not None else []
        ),
        "needsFieldConfirmation": not bool(invoice_number and seller_tax and amount_including is not None),
        "parseStatus": "STRUCTURED",
        "parserVersion": PARSER_VERSION,
        "mediaType": media_type or "application/json",
        "qualityFlags": [],
    }
    return fact_set


def parse_invoice(
    content: Any,
    *,
    media_type: str | None = None,
    document_version_id: str | None = None,
) -> dict[str, Any]:
    """Parse invoice original content into an InvoiceFactSet without inventing numbers."""
    normalized_media = (media_type or "").split(";")[0].strip().lower()
    if isinstance(content, Mapping):
        return _parse_json_invoice(
            content,
            document_version_id=document_version_id,
            media_type=normalized_media or "application/json",
        )

    text = content.decode("utf-8") if isinstance(content, (bytes, bytearray)) else str(content)
    stripped = text.strip()
    looks_xml = normalized_media in {"application/xml", "text/xml"} or stripped.startswith(
        ("<?xml", "<")
    )
    if looks_xml and stripped.startswith(("<", "<?xml")):
        return _parse_xml_invoice(
            stripped,
            document_version_id=document_version_id,
            media_type=normalized_media or "application/xml",
        )

    if normalized_media in {"application/json", "text/json"} or stripped.startswith(("{", "[")):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, Mapping):
            return _parse_json_invoice(
                payload,
                document_version_id=document_version_id,
                media_type=normalized_media or "application/json",
            )

    return _empty_fact_set(
        document_version_id=document_version_id,
        needs_confirmation=True,
        parse_status="UNSUPPORTED",
        media_type=normalized_media or media_type,
        reason="NON_STRUCTURED_INPUT",
    )


def official_verify(
    fact_set: Mapping[str, Any],
    *,
    mode: str,
    human_receipt: Mapping[str, Any] | None = None,
    connector_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return official face verification evidence without fabricating success."""
    normalized_mode = str(mode or "").upper()
    invoice_key = {
        "invoiceCode": fact_set.get("invoiceCode"),
        "invoiceNumber": fact_set.get("invoiceNumber"),
        "issueDate": fact_set.get("issueDate"),
        "amountExcludingTax": (fact_set.get("totals") or {}).get("amountExcludingTax")
        if isinstance(fact_set.get("totals"), Mapping)
        else None,
    }
    base = {
        "mode": normalized_mode,
        "invoiceKey": invoice_key,
        "provider": None,
        "verifiedAt": None,
        "operator": None,
        "returnedFields": {},
        "artifactHash": None,
        "evidenceRefs": list(fact_set.get("evidenceRefs") or []),
    }

    if normalized_mode == "HUMAN_ASSISTED":
        if not human_receipt:
            return {
                **base,
                "status": "PENDING_HUMAN",
                "reasonCode": "AWAITING_HUMAN_RECEIPT",
            }
        status = str(human_receipt.get("status") or "").upper()
        if status not in _VERIFICATION_STATUSES:
            status = "PENDING_HUMAN"
        return {
            **base,
            "status": status,
            "provider": human_receipt.get("provider") or "national-vat-verification-portal",
            "verifiedAt": human_receipt.get("verifiedAt"),
            "operator": human_receipt.get("operator"),
            "returnedFields": dict(human_receipt.get("returnedFields") or {}),
            "artifactHash": human_receipt.get("artifactHash"),
            "reasonCode": human_receipt.get("reasonCode"),
        }

    if normalized_mode == "AUTHORIZED_CONNECTOR":
        if not connector_result:
            return {
                **base,
                "status": "UNAVAILABLE",
                "reasonCode": "CONNECTOR_RESULT_MISSING",
            }
        status = str(connector_result.get("status") or "").upper()
        if status not in _VERIFICATION_STATUSES:
            status = "UNAVAILABLE"
        return {
            **base,
            "status": status,
            "provider": connector_result.get("provider") or "authorized-tax-connector",
            "verifiedAt": connector_result.get("verifiedAt"),
            "operator": connector_result.get("operator"),
            "returnedFields": dict(connector_result.get("returnedFields") or {}),
            "artifactHash": connector_result.get("artifactHash"),
            "reasonCode": connector_result.get("reasonCode"),
        }

    return {
        **base,
        "status": "UNAVAILABLE",
        "reasonCode": "UNSUPPORTED_VERIFICATION_MODE",
    }


def read_business_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a business-system snapshot and attach a canonical content hash."""
    snapshot = {
        "contracts": list(payload.get("contracts") or []),
        "purchaseOrders": list(payload.get("purchaseOrders") or []),
        "receipts": list(payload.get("receipts") or []),
        "acceptances": list(payload.get("acceptances") or []),
        "vendor": dict(payload.get("vendor") or {})
        if isinstance(payload.get("vendor"), Mapping)
        else {},
        "apLedger": list(payload.get("apLedger") or []),
        "budget": dict(payload.get("budget") or {})
        if isinstance(payload.get("budget"), Mapping)
        else {},
        "bankApprovals": list(payload.get("bankApprovals") or []),
        "asOf": payload.get("asOf"),
        "sourceSystem": payload.get("sourceSystem"),
        "sourceVersion": payload.get("sourceVersion"),
    }
    digest = canonical_hash(snapshot)
    return {**snapshot, "hash": digest, "contentHash": digest}


def _rule_result(
    *,
    rule_id: str,
    dimension: str,
    status: str,
    severity: str,
    expected: Any = None,
    actual: Any = None,
    delta: Any = None,
    reason: str | None = None,
    evidence_refs: Iterable[str] = (),
    blocking: bool = False,
) -> dict[str, Any]:
    return {
        "ruleId": rule_id,
        "ruleVersion": RULE_VERSION,
        "dimension": dimension,
        "status": status,
        "severity": severity,
        "expected": expected,
        "actual": actual,
        "delta": delta,
        "reason": reason,
        "blocking": blocking,
        "evidenceRefs": list(dict.fromkeys(evidence_refs)),
    }


def arithmetic_check(fact_set: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Validate invoice money totals with Decimal arithmetic within 0.01."""
    totals = fact_set.get("totals") if isinstance(fact_set.get("totals"), Mapping) else {}
    lines = fact_set.get("lines") if isinstance(fact_set.get("lines"), list) else []
    evidence = [str(item) for item in fact_set.get("evidenceRefs") or []]

    try:
        amount_ex = _optional_decimal(totals.get("amountExcludingTax"), field="amountExcludingTax")
        tax_amount = _optional_decimal(totals.get("taxAmount"), field="taxAmount")
        amount_in = _optional_decimal(
            totals.get("amountIncludingTax"), field="amountIncludingTax"
        )
    except ValueError as exc:
        return [
            _rule_result(
                rule_id="ARITHMETIC_PARSEABLE",
                dimension="faceCompliance",
                status="FAIL",
                severity="HIGH",
                reason=str(exc),
                evidence_refs=evidence,
                blocking=True,
            )
        ]

    if amount_ex is None or tax_amount is None or amount_in is None:
        return [
            _rule_result(
                rule_id="ARITHMETIC_REQUIRED_TOTALS",
                dimension="faceCompliance",
                status="UNKNOWN",
                severity="HIGH",
                reason="missing totals for arithmetic check",
                evidence_refs=evidence,
            )
        ]

    results: list[dict[str, Any]] = []
    total_close_delta = (amount_ex + tax_amount) - amount_in
    total_ok = abs(total_close_delta) <= _MONEY_TOLERANCE
    results.append(
        _rule_result(
            rule_id="ARITHMETIC_TOTALS_CLOSE",
            dimension="faceCompliance",
            status="PASS" if total_ok else "FAIL",
            severity="CRITICAL" if not total_ok else "LOW",
            expected=_number(amount_in),
            actual=_number(amount_ex + tax_amount),
            delta=_number(total_close_delta),
            reason=None if total_ok else "amountExcludingTax + taxAmount does not equal amountIncludingTax",
            evidence_refs=evidence,
            blocking=not total_ok,
        )
    )

    line_amount_sum = Decimal("0")
    line_tax_sum = Decimal("0")
    line_complete = True
    for index, line in enumerate(lines):
        if not isinstance(line, Mapping):
            continue
        try:
            line_amount = _optional_decimal(line.get("amount"), field=f"lines[{index}].amount")
            line_tax = _optional_decimal(line.get("taxAmount"), field=f"lines[{index}].taxAmount")
        except ValueError:
            line_complete = False
            continue
        if line_amount is None:
            line_complete = False
            continue
        line_amount_sum += line_amount
        if line_tax is not None:
            line_tax_sum += line_tax
        else:
            line_complete = False

    if lines and line_complete:
        amount_delta = line_amount_sum - amount_ex
        amount_ok = abs(amount_delta) <= _MONEY_TOLERANCE
        results.append(
            _rule_result(
                rule_id="ARITHMETIC_LINE_AMOUNT_SUM",
                dimension="faceCompliance",
                status="PASS" if amount_ok else "FAIL",
                severity="HIGH" if not amount_ok else "LOW",
                expected=_number(amount_ex),
                actual=_number(line_amount_sum),
                delta=_number(amount_delta),
                reason=None if amount_ok else "line amounts do not sum to amountExcludingTax",
                evidence_refs=evidence,
                blocking=not amount_ok,
            )
        )
        tax_delta = line_tax_sum - tax_amount
        tax_ok = abs(tax_delta) <= _MONEY_TOLERANCE
        results.append(
            _rule_result(
                rule_id="ARITHMETIC_LINE_TAX_SUM",
                dimension="faceCompliance",
                status="PASS" if tax_ok else "FAIL",
                severity="HIGH" if not tax_ok else "LOW",
                expected=_number(tax_amount),
                actual=_number(line_tax_sum),
                delta=_number(tax_delta),
                reason=None if tax_ok else "line tax amounts do not sum to taxAmount",
                evidence_refs=evidence,
                blocking=not tax_ok,
            )
        )
    elif lines:
        results.append(
            _rule_result(
                rule_id="ARITHMETIC_LINE_AMOUNT_SUM",
                dimension="faceCompliance",
                status="UNKNOWN",
                severity="MEDIUM",
                reason="one or more invoice lines lack amount/taxAmount",
                evidence_refs=evidence,
            )
        )

    return results


def party_check(
    fact_set: Mapping[str, Any],
    vendor: Mapping[str, Any] | None,
    *,
    buyer_tax_id: str | None = None,
) -> list[dict[str, Any]]:
    """Compare seller/buyer identity and approved remittance accounts."""
    evidence = [str(item) for item in fact_set.get("evidenceRefs") or []]
    seller = fact_set.get("seller") if isinstance(fact_set.get("seller"), Mapping) else {}
    buyer = fact_set.get("buyer") if isinstance(fact_set.get("buyer"), Mapping) else {}
    results: list[dict[str, Any]] = []

    if not vendor:
        results.append(
            _rule_result(
                rule_id="PARTY_VENDOR_PRESENT",
                dimension="parties",
                status="UNKNOWN",
                severity="HIGH",
                reason="vendor master data missing",
                evidence_refs=evidence,
            )
        )
        results.append(
            _rule_result(
                rule_id="PARTY_SELLER_TAX_MATCH",
                dimension="parties",
                status="UNKNOWN",
                severity="CRITICAL",
                reason="cannot verify seller tax id without vendor master",
                evidence_refs=evidence,
            )
        )
        results.append(
            _rule_result(
                rule_id="PARTY_BANK_APPROVED",
                dimension="parties",
                status="WARN",
                severity="HIGH",
                reason="cannot verify bank account without vendor master",
                evidence_refs=evidence,
            )
        )
        return results

    seller_tax = str(seller.get("taxId") or "").strip()
    vendor_tax = str(vendor.get("taxId") or vendor.get("unifiedSocialCreditCode") or "").strip()
    if not seller_tax or not vendor_tax:
        results.append(
            _rule_result(
                rule_id="PARTY_SELLER_TAX_MATCH",
                dimension="parties",
                status="UNKNOWN",
                severity="CRITICAL",
                expected=vendor_tax or None,
                actual=seller_tax or None,
                reason="seller or vendor tax id missing",
                evidence_refs=evidence,
            )
        )
    elif seller_tax == vendor_tax:
        results.append(
            _rule_result(
                rule_id="PARTY_SELLER_TAX_MATCH",
                dimension="parties",
                status="PASS",
                severity="LOW",
                expected=vendor_tax,
                actual=seller_tax,
                evidence_refs=evidence,
            )
        )
    else:
        results.append(
            _rule_result(
                rule_id="PARTY_SELLER_TAX_MATCH",
                dimension="parties",
                status="FAIL",
                severity="CRITICAL",
                expected=vendor_tax,
                actual=seller_tax,
                reason="seller tax id does not match approved vendor",
                evidence_refs=evidence,
                blocking=True,
            )
        )

    approved_accounts = {
        str(item.get("accountNumber") or item.get("bankAccount") or "").strip()
        for item in (vendor.get("approvedBankAccounts") or [])
        if isinstance(item, Mapping)
    }
    approved_accounts.update(
        str(item).strip()
        for item in (vendor.get("approvedAccounts") or [])
        if item not in (None, "")
    )
    invoice_account = str(seller.get("bankAccount") or "").strip()
    if not invoice_account:
        results.append(
            _rule_result(
                rule_id="PARTY_BANK_APPROVED",
                dimension="parties",
                status="WARN",
                severity="MEDIUM",
                reason="invoice remittance account not present on face",
                evidence_refs=evidence,
            )
        )
    elif not approved_accounts:
        results.append(
            _rule_result(
                rule_id="PARTY_BANK_APPROVED",
                dimension="parties",
                status="UNKNOWN",
                severity="CRITICAL",
                actual=invoice_account,
                reason="vendor has no approved bank accounts on file",
                evidence_refs=evidence,
            )
        )
    elif invoice_account in approved_accounts:
        results.append(
            _rule_result(
                rule_id="PARTY_BANK_APPROVED",
                dimension="parties",
                status="PASS",
                severity="LOW",
                expected=sorted(approved_accounts),
                actual=invoice_account,
                evidence_refs=evidence,
            )
        )
    else:
        results.append(
            _rule_result(
                rule_id="PARTY_BANK_APPROVED",
                dimension="parties",
                status="FAIL",
                severity="CRITICAL",
                expected=sorted(approved_accounts),
                actual=invoice_account,
                reason="remittance account is not an approved vendor bank account",
                evidence_refs=evidence,
                blocking=True,
            )
        )

    if buyer_tax_id is not None:
        actual_buyer = str(buyer.get("taxId") or "").strip()
        expected_buyer = str(buyer_tax_id).strip()
        if not actual_buyer:
            results.append(
                _rule_result(
                    rule_id="PARTY_BUYER_TAX_MATCH",
                    dimension="parties",
                    status="WARN",
                    severity="MEDIUM",
                    expected=expected_buyer,
                    reason="buyer tax id missing on invoice",
                    evidence_refs=evidence,
                )
            )
        elif actual_buyer == expected_buyer:
            results.append(
                _rule_result(
                    rule_id="PARTY_BUYER_TAX_MATCH",
                    dimension="parties",
                    status="PASS",
                    severity="LOW",
                    expected=expected_buyer,
                    actual=actual_buyer,
                    evidence_refs=evidence,
                )
            )
        else:
            results.append(
                _rule_result(
                    rule_id="PARTY_BUYER_TAX_MATCH",
                    dimension="parties",
                    status="FAIL",
                    severity="HIGH",
                    expected=expected_buyer,
                    actual=actual_buyer,
                    reason="buyer tax id does not match tenant tax id",
                    evidence_refs=evidence,
                )
            )

    return results


def _invoice_key(fact_set: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(fact_set.get("invoiceCode") or "").strip(),
        str(fact_set.get("invoiceNumber") or "").strip(),
    )


def deduplicate(
    fact_set: Mapping[str, Any],
    ap_ledger: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Detect paid duplicates and red/blue invoice linkage."""
    code, number = _invoice_key(fact_set)
    evidence = [str(item) for item in fact_set.get("evidenceRefs") or []]
    if ap_ledger is None:
        return {
            "status": "UNKNOWN",
            "blocking": False,
            "duplicates": [],
            "redBlueLinks": [],
            "reasonCode": "AP_LEDGER_MISSING",
            "evidenceRefs": evidence,
        }

    duplicates: list[dict[str, Any]] = []
    for entry in ap_ledger:
        if not isinstance(entry, Mapping):
            continue
        entry_code = str(entry.get("invoiceCode") or "").strip()
        entry_number = str(entry.get("invoiceNumber") or "").strip()
        if number and entry_number == number and (not code or not entry_code or entry_code == code):
            status = str(entry.get("status") or entry.get("paymentStatus") or "").upper()
            paid = status in {"PAID", "SETTLED"} or bool(entry.get("paid"))
            duplicates.append(
                {
                    "invoiceCode": entry_code or None,
                    "invoiceNumber": entry_number,
                    "status": status or ("PAID" if paid else "RECORDED"),
                    "paid": paid,
                    "voucherId": entry.get("voucherId") or entry.get("sourceRecordId"),
                    "amount": entry.get("amount"),
                }
            )

    paid_duplicates = [item for item in duplicates if item.get("paid")]
    red_blue_links: list[dict[str, Any]] = []
    blue_ref = fact_set.get("blueInvoiceRef")
    if fact_set.get("isRed") and isinstance(blue_ref, Mapping):
        red_blue_links.append(
            {
                "type": "RED_TO_BLUE",
                "redInvoiceNumber": number or None,
                "blueInvoiceNumber": blue_ref.get("invoiceNumber"),
                "blueInvoiceCode": blue_ref.get("invoiceCode"),
            }
        )
    for entry in ap_ledger:
        if not isinstance(entry, Mapping):
            continue
        if entry.get("isRed") and str(entry.get("blueInvoiceNumber") or "") == number:
            red_blue_links.append(
                {
                    "type": "BLUE_HAS_RED",
                    "blueInvoiceNumber": number or None,
                    "redInvoiceNumber": entry.get("invoiceNumber"),
                    "redInvoiceCode": entry.get("invoiceCode"),
                    "status": entry.get("status"),
                }
            )

    blocking = bool(paid_duplicates) or (
        bool(fact_set.get("isRed")) and not bool(fact_set.get("allowRedPayment"))
    )
    reason_code = None
    if paid_duplicates:
        reason_code = "PAID_DUPLICATE"
    elif fact_set.get("isRed") and not fact_set.get("allowRedPayment"):
        reason_code = "RED_CREDIT_STILL_PAYING"

    status = "FAIL" if blocking else ("WARN" if duplicates or red_blue_links else "PASS")
    return {
        "status": status,
        "blocking": blocking,
        "duplicates": duplicates,
        "paidDuplicates": paid_duplicates,
        "redBlueLinks": red_blue_links,
        "reasonCode": reason_code,
        "evidenceRefs": evidence,
    }


def commercial_match(
    fact_set: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deterministically match invoice totals to commercial snapshots; agents only suggest."""
    totals = fact_set.get("totals") if isinstance(fact_set.get("totals"), Mapping) else {}
    try:
        invoice_amount = _optional_decimal(
            totals.get("amountIncludingTax"), field="amountIncludingTax"
        )
    except ValueError:
        invoice_amount = None

    purchase_orders = [
        item for item in (snapshot.get("purchaseOrders") or []) if isinstance(item, Mapping)
    ]
    acceptances = [
        item for item in (snapshot.get("acceptances") or []) if isinstance(item, Mapping)
    ]
    contracts = [
        item for item in (snapshot.get("contracts") or []) if isinstance(item, Mapping)
    ]

    matched: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []

    def _amount_of(item: Mapping[str, Any]) -> Decimal | None:
        for key in ("amountIncludingTax", "amount", "totalAmount", "acceptedAmount"):
            if item.get(key) is not None:
                try:
                    return _decimal(item[key], field=key)
                except ValueError:
                    return None
        return None

    exact_targets: list[tuple[str, Mapping[str, Any], Decimal]] = []
    for collection_name, collection in (
        ("purchaseOrder", purchase_orders),
        ("acceptance", acceptances),
        ("contract", contracts),
    ):
        for item in collection:
            amount = _amount_of(item)
            if amount is None or invoice_amount is None:
                continue
            if abs(amount - invoice_amount) <= _MONEY_TOLERANCE:
                exact_targets.append((collection_name, item, amount))

    if len(exact_targets) == 1:
        kind, item, amount = exact_targets[0]
        matched.append(
            {
                "invoiceLineId": None,
                "targetRefs": [
                    {
                        "type": kind,
                        "id": item.get("id") or item.get("purchaseOrderId") or item.get("contractId"),
                    }
                ],
                "matchedAmount": _number(amount),
                "confidenceState": "MATCHED",
                "decisionSource": "DETERMINISTIC",
                "evidenceRefs": [
                    str(ref)
                    for ref in item.get("evidenceRefs") or []
                    if ref is not None
                ],
            }
        )
    elif len(exact_targets) > 1:
        ambiguities.extend(
            {
                "type": kind,
                "id": item.get("id") or item.get("purchaseOrderId") or item.get("contractId"),
                "amount": _number(amount),
            }
            for kind, item, amount in exact_targets
        )

    suggested = [dict(item) for item in candidates or [] if isinstance(item, Mapping)]
    for item in suggested:
        item.setdefault("decisionSource", "AGENT_SUGGESTION")
        item.setdefault("confidenceState", "CANDIDATE")

    if matched and not ambiguities:
        status = "PASS"
    elif ambiguities or suggested:
        status = "REVIEW_REQUIRED"
    elif invoice_amount is None:
        status = "UNKNOWN"
    else:
        status = "FAIL"

    return {
        "status": status,
        "matchedAmount": _number(invoice_amount),
        "matches": matched,
        "ambiguities": ambiguities,
        "candidates": suggested,
        "evidenceRefs": list(fact_set.get("evidenceRefs") or []),
    }


def payment_gate(context: Mapping[str, Any]) -> dict[str, Any]:
    """Compute hard payment blocks versus soft review gates."""
    verification = context.get("verification") if isinstance(context.get("verification"), Mapping) else {}
    duplication = context.get("duplication") if isinstance(context.get("duplication"), Mapping) else {}
    rule_results = [
        item for item in (context.get("ruleResults") or []) if isinstance(item, Mapping)
    ]
    match_result = (
        context.get("commercialMatch")
        if isinstance(context.get("commercialMatch"), Mapping)
        else {}
    )
    budget = context.get("budget") if isinstance(context.get("budget"), Mapping) else {}

    gates: list[dict[str, Any]] = []
    hard_blocks: list[str] = []

    verification_status = str(verification.get("status") or "").upper()
    if verification_status in {"FACE_MISMATCH", "NOT_FOUND"}:
        hard_blocks.append(verification_status)
        gates.append(
            {
                "gateId": "OFFICIAL_VERIFICATION",
                "status": "FAIL",
                "blocking": True,
                "reasonCode": verification_status,
                "remediation": "取得税务机关鉴定或更换合法原件后重新评估",
                "evidenceRefs": list(verification.get("evidenceRefs") or []),
            }
        )
    elif verification_status == "FACE_MATCHED":
        gates.append(
            {
                "gateId": "OFFICIAL_VERIFICATION",
                "status": "PASS",
                "blocking": False,
                "reasonCode": "FACE_MATCHED",
                "remediation": None,
                "evidenceRefs": list(verification.get("evidenceRefs") or []),
            }
        )
    else:
        gates.append(
            {
                "gateId": "OFFICIAL_VERIFICATION",
                "status": "REVIEW",
                "blocking": False,
                "reasonCode": verification_status or "VERIFICATION_INCOMPLETE",
                "remediation": "完成官方查验或提交人工查验回执",
                "evidenceRefs": list(verification.get("evidenceRefs") or []),
            }
        )

    if duplication.get("reasonCode") == "PAID_DUPLICATE" or (
        duplication.get("blocking") and duplication.get("paidDuplicates")
    ):
        hard_blocks.append("PAID_DUPLICATE")
        gates.append(
            {
                "gateId": "DUPLICATE_PAYMENT",
                "status": "FAIL",
                "blocking": True,
                "reasonCode": "PAID_DUPLICATE",
                "remediation": "核对历史付款凭证，禁止重复支付",
                "evidenceRefs": list(duplication.get("evidenceRefs") or []),
            }
        )
    elif duplication.get("reasonCode") == "RED_CREDIT_STILL_PAYING":
        hard_blocks.append("RED_CREDIT_STILL_PAYING")
        gates.append(
            {
                "gateId": "RED_CREDIT",
                "status": "FAIL",
                "blocking": True,
                "reasonCode": "RED_CREDIT_STILL_PAYING",
                "remediation": "红字发票不得作为付款依据",
                "evidenceRefs": list(duplication.get("evidenceRefs") or []),
            }
        )
    else:
        gates.append(
            {
                "gateId": "DUPLICATE_PAYMENT",
                "status": "PASS" if duplication.get("status") == "PASS" else "REVIEW",
                "blocking": False,
                "reasonCode": duplication.get("reasonCode") or duplication.get("status") or "OK",
                "remediation": None,
                "evidenceRefs": list(duplication.get("evidenceRefs") or []),
            }
        )

    for rule in rule_results:
        rule_id = str(rule.get("ruleId") or "")
        if rule.get("blocking") or (
            rule.get("status") == "FAIL" and rule.get("severity") == "CRITICAL"
        ):
            if rule_id == "PARTY_SELLER_TAX_MATCH":
                hard_blocks.append("SELLER_TAX_MISMATCH")
                reason = "SELLER_TAX_MISMATCH"
            elif rule_id == "PARTY_BANK_APPROVED":
                hard_blocks.append("UNAPPROVED_BANK_ACCOUNT")
                reason = "UNAPPROVED_BANK_ACCOUNT"
            elif rule_id.startswith("ARITHMETIC_"):
                reason = "ARITHMETIC_FAIL"
            else:
                reason = rule_id or "RULE_FAIL"
            gates.append(
                {
                    "gateId": rule_id or "RULE",
                    "status": "FAIL",
                    "blocking": reason in _HARD_BLOCK_REASON_CODES,
                    "reasonCode": reason,
                    "remediation": rule.get("reason"),
                    "evidenceRefs": list(rule.get("evidenceRefs") or []),
                }
            )

    if match_result.get("status") in {"FAIL", "REVIEW_REQUIRED", "UNKNOWN"}:
        gates.append(
            {
                "gateId": "COMMERCIAL_MATCH",
                "status": "REVIEW" if match_result.get("status") != "FAIL" else "FAIL",
                "blocking": False,
                "reasonCode": str(match_result.get("status")),
                "remediation": "由采购确认合同/订单/验收匹配",
                "evidenceRefs": list(match_result.get("evidenceRefs") or []),
            }
        )
    elif match_result:
        gates.append(
            {
                "gateId": "COMMERCIAL_MATCH",
                "status": "PASS",
                "blocking": False,
                "reasonCode": "MATCHED",
                "remediation": None,
                "evidenceRefs": list(match_result.get("evidenceRefs") or []),
            }
        )

    if budget:
        available = budget.get("availableAmount")
        requested = budget.get("requestedAmount")
        try:
            if available is not None and requested is not None:
                available_value = _decimal(available, field="budget.availableAmount")
                requested_value = _decimal(requested, field="budget.requestedAmount")
                if requested_value > available_value + _MONEY_TOLERANCE:
                    gates.append(
                        {
                            "gateId": "BUDGET",
                            "status": "REVIEW",
                            "blocking": False,
                            "reasonCode": "BUDGET_EXCEEDED",
                            "remediation": "申请预算追加或调整付款计划",
                            "evidenceRefs": [],
                        }
                    )
                else:
                    gates.append(
                        {
                            "gateId": "BUDGET",
                            "status": "PASS",
                            "blocking": False,
                            "reasonCode": "WITHIN_BUDGET",
                            "remediation": None,
                            "evidenceRefs": [],
                        }
                    )
        except ValueError:
            gates.append(
                {
                    "gateId": "BUDGET",
                    "status": "REVIEW",
                    "blocking": False,
                    "reasonCode": "BUDGET_DATA_INVALID",
                    "remediation": "补正预算快照后重试",
                    "evidenceRefs": [],
                }
            )

    unique_blocks = list(dict.fromkeys(hard_blocks))
    soft_reviews = [
        gate
        for gate in gates
        if not gate.get("blocking") and gate.get("status") in {"REVIEW", "FAIL"}
    ]
    verification_pending = verification_status in {"PENDING_HUMAN", "UNAVAILABLE"}
    if unique_blocks:
        status = "PAYMENT_BLOCKED"
    elif soft_reviews or verification_pending:
        status = "REVIEW_REQUIRED"
    else:
        status = "PAYMENT_READY"

    return {
        "status": status,
        "blocking": bool(unique_blocks),
        "hardBlocks": unique_blocks,
        "gates": gates,
        "evidenceRefs": list(
            dict.fromkeys(
                str(ref)
                for gate in gates
                for ref in gate.get("evidenceRefs") or []
            )
        ),
    }


def _dimension_from_rules(
    rule_results: Sequence[Mapping[str, Any]],
    *,
    dimension: str,
    fallback_status: str = "NOT_APPLICABLE",
) -> dict[str, Any]:
    matched = [item for item in rule_results if item.get("dimension") == dimension]
    if not matched:
        return {
            "status": fallback_status,
            "severity": "LOW",
            "summary": f"{dimension} not evaluated",
            "ruleIds": [],
        }
    if any(item.get("status") == "FAIL" for item in matched):
        status = "FAIL"
    elif any(item.get("status") == "UNKNOWN" for item in matched):
        status = "UNKNOWN"
    elif any(item.get("status") == "WARN" for item in matched):
        status = "WARN"
    else:
        status = "PASS"
    severity = "LOW"
    for item in matched:
        item_severity = str(item.get("severity") or "LOW")
        order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        if order.get(item_severity, 0) > order.get(severity, 0):
            severity = item_severity
    return {
        "status": status,
        "severity": severity,
        "summary": f"{len(matched)} rule(s)",
        "ruleIds": [str(item.get("ruleId")) for item in matched],
    }


def finalize_invoice_assurance(
    *,
    fact_set: Mapping[str, Any],
    verification: Mapping[str, Any],
    business_snapshot: Mapping[str, Any],
    rule_results: Iterable[Mapping[str, Any]],
    match_result: Mapping[str, Any],
    duplication: Mapping[str, Any],
    gate_result: Mapping[str, Any],
    narrative: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    approvals: Iterable[Mapping[str, Any]] = (),
    title: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Assemble the immutable InvoiceAssuranceResult and payment outcome."""
    rules = [dict(item) for item in rule_results]
    hard_blocks = [
        str(code)
        for code in (gate_result.get("hardBlocks") or [])
        if code is not None
    ]
    verification_status = str(verification.get("status") or "").upper()

    critical_rules = [
        item
        for item in rules
        if item.get("severity") == "CRITICAL"
    ]
    critical_pass = all(item.get("status") == "PASS" for item in critical_rules) if critical_rules else True
    verification_ok = verification_status == "FACE_MATCHED"
    no_hard_blocks = not hard_blocks and not gate_result.get("blocking")

    if hard_blocks or gate_result.get("status") == "PAYMENT_BLOCKED":
        outcome = "PAYMENT_BLOCKED"
    elif (
        verification_ok
        and no_hard_blocks
        and critical_pass
        and gate_result.get("status") == "PAYMENT_READY"
        and match_result.get("status") == "PASS"
        and not fact_set.get("needsFieldConfirmation")
    ):
        outcome = "PAYMENT_READY"
    else:
        outcome = "REVIEW_REQUIRED"

    findings: list[dict[str, Any]] = []
    for code in hard_blocks:
        findings.append(
            {
                "code": code,
                "severity": "CRITICAL",
                "status": "OPEN",
                "blocking": True,
                "summary": code,
            }
        )
    for rule in rules:
        if rule.get("status") in {"FAIL", "WARN", "UNKNOWN"}:
            findings.append(
                {
                    "code": str(rule.get("ruleId")),
                    "severity": rule.get("severity") or "MEDIUM",
                    "status": "OPEN",
                    "blocking": bool(rule.get("blocking")),
                    "summary": rule.get("reason") or rule.get("ruleId"),
                    "dimension": rule.get("dimension"),
                }
            )
    if duplication.get("blocking"):
        findings.append(
            {
                "code": duplication.get("reasonCode") or "DUPLICATE",
                "severity": "CRITICAL",
                "status": "OPEN",
                "blocking": True,
                "summary": duplication.get("reasonCode") or "duplicate detected",
            }
        )
    if match_result.get("status") in {"FAIL", "REVIEW_REQUIRED", "UNKNOWN"}:
        findings.append(
            {
                "code": "COMMERCIAL_MATCH",
                "severity": "MEDIUM",
                "status": "OPEN",
                "blocking": False,
                "summary": f"commercial match {match_result.get('status')}",
            }
        )

    dimensions = {
        "officialVerification": {
            "status": verification_status or "UNKNOWN",
            "severity": "CRITICAL"
            if verification_status in {"FACE_MISMATCH", "NOT_FOUND"}
            else "LOW",
            "summary": verification.get("reasonCode") or verification_status,
        },
        "faceCompliance": _dimension_from_rules(rules, dimension="faceCompliance"),
        "parties": _dimension_from_rules(rules, dimension="parties"),
        "commercialMatch": {
            "status": match_result.get("status") or "UNKNOWN",
            "severity": "MEDIUM",
            "summary": f"{len(match_result.get('matches') or [])} match(es)",
        },
        "fulfillment": {
            "status": match_result.get("status") or "UNKNOWN",
            "severity": "MEDIUM",
            "summary": "derived from commercial match / acceptance",
        },
        "duplication": {
            "status": duplication.get("status") or "UNKNOWN",
            "severity": "CRITICAL" if duplication.get("blocking") else "LOW",
            "summary": duplication.get("reasonCode") or duplication.get("status"),
        },
        "paymentGates": {
            "status": gate_result.get("status") or "UNKNOWN",
            "severity": "CRITICAL" if gate_result.get("blocking") else "LOW",
            "summary": ",".join(hard_blocks) if hard_blocks else "no hard blocks",
        },
    }

    snapshot_hash = business_snapshot.get("hash") or business_snapshot.get("contentHash")
    if snapshot_hash is None:
        snapshot_hash = canonical_hash(
            {
                key: business_snapshot.get(key)
                for key in (
                    "contracts",
                    "purchaseOrders",
                    "receipts",
                    "acceptances",
                    "vendor",
                    "apLedger",
                    "budget",
                    "bankApprovals",
                    "asOf",
                )
            }
        )

    score = {
        "PAYMENT_READY": 1.0,
        "REVIEW_REQUIRED": 0.5,
        "PAYMENT_BLOCKED": 0.0,
    }[outcome]

    result = {
        "schemaVersion": SCHEMA_VERSION,
        "title": title or "发票一致性校验报告",
        "asOf": as_of or business_snapshot.get("asOf"),
        "outcome": outcome,
        "score": score,
        "reviewRequired": outcome != "PAYMENT_READY",
        "dimensions": dimensions,
        "invoiceFactSet": dict(fact_set),
        "verification": dict(verification),
        "businessSnapshotHash": snapshot_hash,
        "ruleResults": rules,
        "matchResults": list(match_result.get("matches") or []),
        "commercialMatch": dict(match_result),
        "duplication": dict(duplication),
        "gateResults": list(gate_result.get("gates") or []),
        "paymentGate": dict(gate_result),
        "findings": findings,
        "approvals": [dict(item) for item in approvals],
        "narrative": dict(narrative or {}),
        "provenance": dict(provenance or {}),
        "artifacts": [],
        "qualityFlags": list(fact_set.get("qualityFlags") or []),
    }
    result["resultHash"] = canonical_hash(
        {
            key: result[key]
            for key in (
                "schemaVersion",
                "outcome",
                "score",
                "dimensions",
                "invoiceFactSet",
                "verification",
                "businessSnapshotHash",
                "ruleResults",
                "matchResults",
                "gateResults",
                "findings",
            )
        }
    )
    return result


def validate_invoice_assurance_result(result: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(result)
    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("unexpected invoice-assurance result schemaVersion")
    required = {
        "outcome",
        "score",
        "dimensions",
        "invoiceFactSet",
        "verification",
        "businessSnapshotHash",
        "ruleResults",
        "matchResults",
        "gateResults",
        "findings",
        "approvals",
        "narrative",
        "provenance",
        "artifacts",
        "qualityFlags",
        "reviewRequired",
        "title",
        "asOf",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(
            f"invoice-assurance result missing fields: {', '.join(missing)}"
        )
    if payload.get("outcome") not in _OUTCOMES:
        raise ValueError("invalid invoice-assurance outcome")
    verification = payload.get("verification")
    if not isinstance(verification, Mapping):
        raise ValueError("verification must be an object")
    status = verification.get("status")
    if status not in _VERIFICATION_STATUSES:
        raise ValueError("invalid verification status")
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise ValueError("dimensions must be an object")
    for key in (
        "officialVerification",
        "faceCompliance",
        "parties",
        "commercialMatch",
        "fulfillment",
        "duplication",
        "paymentGates",
    ):
        if key not in dimensions:
            raise ValueError(f"dimensions missing {key}")
    for rule in payload.get("ruleResults") or []:
        if not isinstance(rule, Mapping) or rule.get("status") not in _RULE_STATUSES:
            raise ValueError("invalid rule result status")
    return payload


def invoice_assurance_report_lines(result: Mapping[str, Any]) -> list[str]:
    """Render Chinese summary lines for PDF report composition."""
    outcome = str(result.get("outcome") or "UNKNOWN")
    outcome_label = {
        "PAYMENT_READY": "可进入付款队列",
        "REVIEW_REQUIRED": "需人工复核",
        "PAYMENT_BLOCKED": "付款阻断",
    }.get(outcome, outcome)
    fact_set = result.get("invoiceFactSet") if isinstance(result.get("invoiceFactSet"), Mapping) else {}
    totals = fact_set.get("totals") if isinstance(fact_set.get("totals"), Mapping) else {}
    verification = result.get("verification") if isinstance(result.get("verification"), Mapping) else {}
    seller = fact_set.get("seller") if isinstance(fact_set.get("seller"), Mapping) else {}
    lines = [
        str(result.get("title") or "发票一致性校验报告"),
        f"评估日期: {result.get('asOf') or '-'}",
        f"总体结论: {outcome_label} ({outcome})",
        f"是否需要复核: {'是' if result.get('reviewRequired') else '否'}",
        "票面摘要",
        f"- 发票号码: {fact_set.get('invoiceNumber') or '-'}",
        f"- 开票日期: {fact_set.get('issueDate') or '-'}",
        f"- 销售方: {seller.get('name') or '-'} / {seller.get('taxId') or '-'}",
        f"- 价税合计: {totals.get('amountIncludingTax') if totals.get('amountIncludingTax') is not None else '-'} "
        f"{totals.get('currency') or 'CNY'}",
        "官方查验",
        f"- 模式: {verification.get('mode') or '-'}",
        f"- 状态: {verification.get('status') or '-'}",
        "维度结论",
    ]
    dimensions = result.get("dimensions") if isinstance(result.get("dimensions"), Mapping) else {}
    dimension_labels = {
        "officialVerification": "官方查验",
        "faceCompliance": "票面合规",
        "parties": "购销主体",
        "commercialMatch": "合同/订单匹配",
        "fulfillment": "履约/验收",
        "duplication": "重复与红冲",
        "paymentGates": "付款门禁",
    }
    for key, label in dimension_labels.items():
        dimension = dimensions.get(key) if isinstance(dimensions.get(key), Mapping) else {}
        lines.append(
            f"- {label}: {dimension.get('status') or 'UNKNOWN'}"
            f" [{dimension.get('severity') or 'LOW'}]"
        )

    findings = result.get("findings") if isinstance(result.get("findings"), list) else []
    if findings:
        lines.append("风险项")
        for item in findings:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"- {item.get('code') or 'FINDING'}: {item.get('summary') or ''}"
                f" ({item.get('severity') or 'MEDIUM'})"
            )

    narrative = result.get("narrative") if isinstance(result.get("narrative"), Mapping) else {}
    if narrative.get("executiveSummary"):
        lines.extend(("管理摘要", str(narrative["executiveSummary"])))

    lines.extend(
        (
            "声明",
            "官方查验仅证明平台返回的票面信息，不代表交易真实或允许付款。",
            "金额、税额、重复和付款阻断由确定性规则计算；模型输出不得改写这些结论。",
            "本报告用于付款前置条件校验，不发起银行付款。",
        )
    )
    return lines
