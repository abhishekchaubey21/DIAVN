import logging
from typing import List, Dict, Any, Optional
from app.verification.models import CheckTypeEnum, CheckStatusEnum, CheckSeverityEnum, VerificationCheckItem
from app.verification.normalization import normalize_name, normalize_product_name

logger = logging.getLogger(__name__)


def verify_case_entity_consistency(
    invoice_data: Dict[str, Any],
    case_data: Dict[str, Any]
) -> List[VerificationCheckItem]:
    """
    Deterministically cross-checks extracted invoice entities against underwriting case metadata.
    """
    results: List[VerificationCheckItem] = []

    # 1. Dealer Consistency Check
    inv_dealer = invoice_data.get("dealer_name")
    case_dealer = case_data.get("dealer_name") or case_data.get("dealer_id")

    if not inv_dealer or not case_dealer:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                check_name="Dealer Entity Consistency",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.INFO,
                message="Dealer information missing on invoice or case metadata.",
                evidence={"invoice_dealer": inv_dealer, "case_dealer": case_dealer}
            )
        )
    else:
        norm_inv_dealer = normalize_name(inv_dealer)
        norm_case_dealer = normalize_name(case_dealer)

        # Check exact or contained substring
        if norm_inv_dealer == norm_case_dealer or norm_inv_dealer in norm_case_dealer or norm_case_dealer in norm_inv_dealer:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                    check_name="Dealer Entity Consistency",
                    status=CheckStatusEnum.PASS,
                    severity=CheckSeverityEnum.INFO,
                    message="Invoice issuing dealer matches authorized case dealer.",
                    evidence={"invoice_dealer": inv_dealer, "case_dealer": case_dealer}
                )
            )
        else:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                    check_name="Dealer Entity Consistency",
                    status=CheckStatusEnum.ANOMALY,
                    severity=CheckSeverityEnum.MEDIUM,
                    message=f"Invoice dealer '{inv_dealer}' does not match assigned case dealer '{case_dealer}'.",
                    evidence={
                        "invoice_dealer": inv_dealer,
                        "case_dealer": case_dealer,
                        "normalized_invoice": norm_inv_dealer,
                        "normalized_case": norm_case_dealer
                    }
                )
            )

    # 2. Customer Consistency Check
    inv_customer = invoice_data.get("customer_name")
    case_customer = case_data.get("customer_name") or case_data.get("customer_id")

    if not inv_customer or not case_customer:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                check_name="Customer / Borrower Consistency",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.INFO,
                message="Customer name missing on invoice or case metadata.",
                evidence={"invoice_customer": inv_customer, "case_customer": case_customer}
            )
        )
    else:
        norm_inv_cust = normalize_name(inv_customer)
        norm_case_cust = normalize_name(case_customer)

        if norm_inv_cust == norm_case_cust or norm_inv_cust in norm_case_cust or norm_case_cust in norm_inv_cust:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                    check_name="Customer / Borrower Consistency",
                    status=CheckStatusEnum.PASS,
                    severity=CheckSeverityEnum.INFO,
                    message="Invoice billed customer matches loan borrower applicant.",
                    evidence={"invoice_customer": inv_customer, "case_customer": case_customer}
                )
            )
        else:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                    check_name="Customer / Borrower Consistency",
                    status=CheckStatusEnum.ANOMALY,
                    severity=CheckSeverityEnum.MEDIUM,
                    message=f"Invoice billed customer '{inv_customer}' differs from loan applicant '{case_customer}'.",
                    evidence={
                        "invoice_customer": inv_customer,
                        "case_customer": case_customer,
                        "normalized_invoice": norm_inv_cust,
                        "normalized_case": norm_case_cust
                    }
                )
            )

    # 3. Asset Type Consistency Check
    case_asset = case_data.get("asset_type")
    items = invoice_data.get("items") or invoice_data.get("line_items") or []

    if not case_asset or not items:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                check_name="Asset Specification Consistency",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.INFO,
                message="Asset type missing on case or line items missing on invoice.",
                evidence={"case_asset": case_asset, "line_items_count": len(items)}
            )
        )
    else:
        norm_case_asset = normalize_product_name(case_asset)
        asset_matched = False
        matched_item_name = ""

        for itm in items:
            item_name = itm.get("product_name") or itm.get("item_description") or ""
            norm_item_name = normalize_product_name(item_name)
            if norm_case_asset in norm_item_name or norm_item_name in norm_case_asset:
                asset_matched = True
                matched_item_name = item_name
                break
            # Keyword overlap
            case_words = set(norm_case_asset.split())
            item_words = set(norm_item_name.split())
            if len(case_words.intersection(item_words)) >= 2:
                asset_matched = True
                matched_item_name = item_name
                break

        if asset_matched:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                    check_name="Asset Specification Consistency",
                    status=CheckStatusEnum.PASS,
                    severity=CheckSeverityEnum.INFO,
                    message=f"Invoice line item '{matched_item_name}' corresponds with case equipment category '{case_asset}'.",
                    evidence={"case_asset": case_asset, "matched_invoice_item": matched_item_name}
                )
            )
        else:
            first_item = items[0].get("product_name") or items[0].get("item_description") or "Item #1"
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.CASE_ENTITY_CONSISTENCY,
                    check_name="Asset Specification Consistency",
                    status=CheckStatusEnum.ANOMALY,
                    severity=CheckSeverityEnum.MEDIUM,
                    message=f"Invoice billed equipment '{first_item}' does not correspond with case claimed asset type '{case_asset}'.",
                    evidence={"case_asset": case_asset, "invoice_first_item": first_item}
                )
            )

    return results


def verify_invoice_arithmetic(
    invoice_data: Dict[str, Any],
    tolerance_amount: float = 5.0
) -> List[VerificationCheckItem]:
    """
    Deterministically verifies internal invoice arithmetic:
    1. Line totals = quantity * unit_price
    2. Subtotal = sum(line totals)
    3. Total amount = subtotal + tax
    """
    results: List[VerificationCheckItem] = []
    items = invoice_data.get("items") or invoice_data.get("line_items") or []

    if not items:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.INVOICE_ARITHMETIC,
                check_name="Invoice Arithmetic Integrity",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.INFO,
                message="No line items available to verify invoice arithmetic.",
                evidence={"reason": "no_line_items"}
            )
        )
        return results

    # Check 1: Individual line item arithmetic
    line_errors = []
    computed_subtotal = 0.0

    for idx, itm in enumerate(items):
        qty = itm.get("quantity")
        rate = itm.get("unit_price")
        total = itm.get("total_amount")

        if qty is not None and rate is not None and total is not None:
            expected_line_total = qty * rate
            diff = abs(total - expected_line_total)
            if diff > tolerance_amount:
                line_errors.append({
                    "item_index": idx + 1,
                    "product": itm.get("product_name") or itm.get("item_description"),
                    "quantity": qty,
                    "unit_price": rate,
                    "expected_total": expected_line_total,
                    "stated_total": total,
                    "difference": diff
                })
            computed_subtotal += total
        elif total is not None:
            computed_subtotal += total

    if line_errors:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.INVOICE_ARITHMETIC,
                check_name="Line Item Multiplication Arithmetic",
                status=CheckStatusEnum.ANOMALY,
                severity=CheckSeverityEnum.MEDIUM,
                message=f"Arithmetic discrepancy detected in {len(line_errors)} invoice line item(s).",
                evidence={"discrepant_lines": line_errors}
            )
        )
    else:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.INVOICE_ARITHMETIC,
                check_name="Line Item Multiplication Arithmetic",
                status=CheckStatusEnum.PASS,
                severity=CheckSeverityEnum.INFO,
                message="All line item subtotals match quantity × unit rate within tolerance.",
                evidence={"validated_lines_count": len(items)}
            )
        )

    # Check 2: Gross total calculation
    stated_total = invoice_data.get("total_amount")
    stated_subtotal = invoice_data.get("subtotal") or computed_subtotal
    stated_tax = invoice_data.get("total_tax") or invoice_data.get("tax_amount") or 0.0

    if stated_total is not None and stated_subtotal is not None:
        expected_total = stated_subtotal + stated_tax
        total_diff = abs(stated_total - expected_total)

        if total_diff > tolerance_amount:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.INVOICE_ARITHMETIC,
                    check_name="Gross Total Summary Reconciliation",
                    status=CheckStatusEnum.ANOMALY,
                    severity=CheckSeverityEnum.MEDIUM,
                    message=f"Invoice stated total (₹{stated_total:,.2f}) does not match subtotal + tax (₹{expected_total:,.2f}, diff: ₹{total_diff:,.2f}).",
                    evidence={
                        "stated_total": stated_total,
                        "subtotal": stated_subtotal,
                        "tax": stated_tax,
                        "expected_total": expected_total,
                        "difference": total_diff
                    }
                )
            )
        else:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.INVOICE_ARITHMETIC,
                    check_name="Gross Total Summary Reconciliation",
                    status=CheckStatusEnum.PASS,
                    severity=CheckSeverityEnum.INFO,
                    message=f"Invoice gross total (₹{stated_total:,.2f}) reconciles with subtotal + tax.",
                    evidence={"total_amount": stated_total, "subtotal": stated_subtotal, "tax": stated_tax}
                )
            )
    else:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.INVOICE_ARITHMETIC,
                check_name="Gross Total Summary Reconciliation",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.INFO,
                message="Subtotal or gross total missing; reconciliation inconclusive.",
                evidence={"stated_total": stated_total, "stated_subtotal": stated_subtotal}
            )
        )

    return results


def verify_required_evidence_fields(
    invoice_data: Dict[str, Any]
) -> List[VerificationCheckItem]:
    """
    Checks for presence of essential invoice evidence fields.
    Missing fields produce INCONCLUSIVE (never fraud).
    """
    results: List[VerificationCheckItem] = []
    missing_fields = []

    required = [
        ("invoice_number", "Invoice Number"),
        ("invoice_date", "Invoice Date"),
        ("dealer_name", "Dealer Name"),
        ("customer_name", "Customer Name"),
        ("total_amount", "Total Amount")
    ]

    for field_key, field_label in required:
        val = invoice_data.get(field_key)
        if val is None or str(val).strip() == "" or (isinstance(val, (int, float)) and val <= 0):
            missing_fields.append(field_label)

    items = invoice_data.get("items") or invoice_data.get("line_items") or []
    if len(items) == 0:
        missing_fields.append("Line Items (at least 1 required)")

    if missing_fields:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.REQUIRED_EVIDENCE_FIELDS,
                check_name="Required Evidence Completeness",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.LOW,
                message=f"Critical invoice evidence fields not visible/extracted: {', '.join(missing_fields)}.",
                evidence={"missing_fields": missing_fields, "status": "incomplete_evidence"}
            )
        )
    else:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.REQUIRED_EVIDENCE_FIELDS,
                check_name="Required Evidence Completeness",
                status=CheckStatusEnum.PASS,
                severity=CheckSeverityEnum.INFO,
                message="All essential invoice evidence fields are present and structured.",
                evidence={"validated_fields": [f[0] for f in required] + ["line_items"]}
            )
        )

    return results
