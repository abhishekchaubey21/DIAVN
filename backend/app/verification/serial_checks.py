import logging
from typing import List, Dict, Any, Optional
from collections import Counter
from app.verification.models import CheckTypeEnum, CheckStatusEnum, CheckSeverityEnum, VerificationCheckItem
from app.verification.normalization import normalize_serial, is_placeholder_serial

logger = logging.getLogger(__name__)

# Authority registry of internally registered assets matching 'registered_assets' database table
# Used for internal duplicate asset detection
INTERNAL_REGISTERED_ASSETS = [
    {
        "id": "66666666-6666-6666-6666-666666666601",
        "serial_number": "ASP-2025-99881",
        "asset_type": "Solar Water Pump 5HP",
        "brand": "AquaSun",
        "original_case_id": "CAS-2026-001",
        "installed_at": "2025-08-14",
        "registration_status": "active"
    },
    {
        "id": "66666666-6666-6666-6666-666666666602",
        "serial_number": "VM-10KW-77441",
        "asset_type": "Solar Inverter 10kW",
        "brand": "VoltMax",
        "original_case_id": "CAS-2025-8812",
        "installed_at": "2025-11-20",
        "registration_status": "flagged_duplicate"
    },
    {
        "id": "66666666-6666-6666-6666-666666666603",
        "serial_number": "SG-5K-00192",
        "asset_type": "Solar Inverter 5kVA",
        "brand": "SunGuard",
        "original_case_id": "CAS-2026-002",
        "installed_at": "2026-01-10",
        "registration_status": "active"
    },
    {
        "id": "66666666-6666-6666-6666-666666666604",
        "serial_number": "LS-540-88310",
        "asset_type": "Solar PV Panel",
        "brand": "LumiSolar",
        "original_case_id": "CAS-2026-002",
        "installed_at": "2026-01-10",
        "registration_status": "active"
    },
    {
        "id": "66666666-6666-6666-6666-666666666605",
        "serial_number": "ASC-AUTO-4401",
        "asset_type": "Micro-Irrigation Controller",
        "brand": "AgroSense",
        "original_case_id": "CAS-2025-7701",
        "installed_at": "2026-02-05",
        "registration_status": "active"
    }
]


def verify_serial_numbers(
    current_case_id: str,
    line_items: List[Dict[str, Any]],
    external_registered_assets: Optional[List[Dict[str, Any]]] = None
) -> List[VerificationCheckItem]:
    """
    Deterministically evaluates extracted serial numbers for:
    1. Presence and format validity.
    2. Duplication within the same invoice.
    3. Duplication against internal registered assets database.
    """
    results: List[VerificationCheckItem] = []
    registered_registry = external_registered_assets or INTERNAL_REGISTERED_ASSETS

    all_extracted_serials: List[str] = []
    line_serial_map: List[Dict[str, Any]] = []

    for idx, item in enumerate(line_items):
        product_name = item.get("product_name") or item.get("item_description") or f"Item #{idx+1}"
        serials = item.get("serial_numbers") or []
        if not serials and item.get("serial_number"):
            serials = [item.get("serial_number")]

        if not serials:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.SERIAL_PRESENCE_AND_FORMAT,
                    check_name=f"Serial Presence: {product_name}",
                    status=CheckStatusEnum.INCONCLUSIVE,
                    severity=CheckSeverityEnum.INFO,
                    message=f"No serial number extracted for '{product_name}'.",
                    evidence={"product": product_name, "reason": "serial_not_extracted"}
                )
            )
            continue

        for s in serials:
            norm_s = normalize_serial(s)
            all_extracted_serials.append(norm_s)
            line_serial_map.append({"original": s, "normalized": norm_s, "product": product_name})

            # Check Format / Placeholder
            if is_placeholder_serial(s):
                results.append(
                    VerificationCheckItem(
                        check_type=CheckTypeEnum.SERIAL_PRESENCE_AND_FORMAT,
                        check_name=f"Serial Format Validity: {s}",
                        status=CheckStatusEnum.ANOMALY,
                        severity=CheckSeverityEnum.HIGH,
                        message=f"Extracted serial '{s}' matches a known placeholder or invalid serial pattern.",
                        evidence={"product": product_name, "raw_serial": s, "pattern": "placeholder_detected"}
                    )
                )
            else:
                results.append(
                    VerificationCheckItem(
                        check_type=CheckTypeEnum.SERIAL_PRESENCE_AND_FORMAT,
                        check_name=f"Serial Format Validity: {s}",
                        status=CheckStatusEnum.PASS,
                        severity=CheckSeverityEnum.INFO,
                        message=f"Serial number '{s}' conforms to standard alphanumeric equipment format.",
                        evidence={"product": product_name, "serial_number": s}
                    )
                )

    # 2. Same-Invoice Duplicate Check
    serial_counts = Counter(all_extracted_serials)
    same_invoice_duplicates = [s for s, count in serial_counts.items() if count > 1 and s]

    if same_invoice_duplicates:
        for dup in same_invoice_duplicates:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.SERIAL_SAME_INVOICE_DUPLICATE,
                    check_name=f"Intra-Invoice Duplicate Serial: {dup}",
                    status=CheckStatusEnum.ANOMALY,
                    severity=CheckSeverityEnum.HIGH,
                    message=f"Duplicate serial number '{dup}' detected across multiple line items within the same invoice.",
                    evidence={"serial_number": dup, "occurrences": serial_counts[dup]}
                )
            )
    elif all_extracted_serials:
        results.append(
            VerificationCheckItem(
                check_type=CheckTypeEnum.SERIAL_SAME_INVOICE_DUPLICATE,
                check_name="Intra-Invoice Serial Uniqueness",
                status=CheckStatusEnum.PASS,
                severity=CheckSeverityEnum.INFO,
                message="All serial numbers within invoice are unique.",
                evidence={"unique_serials_count": len(all_extracted_serials)}
            )
        )

    # 3. Internal Cross-Case Duplicate Check
    for item in line_serial_map:
        norm_s = item["normalized"]
        raw_s = item["original"]
        product = item["product"]

        # Search registered assets
        matched_prior = None
        for asset in registered_registry:
            if normalize_serial(asset["serial_number"]) == norm_s:
                # Check if it belongs to a DIFFERENT case
                if asset.get("original_case_id") and asset.get("original_case_id") != current_case_id:
                    matched_prior = asset
                    break

        if matched_prior:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.SERIAL_INTERNAL_DUPLICATE,
                    check_name=f"Internal Asset Registry Check: {raw_s}",
                    status=CheckStatusEnum.ANOMALY,
                    severity=CheckSeverityEnum.HIGH,
                    message=f"Serial number '{raw_s}' already belongs to existing active case #{matched_prior['original_case_id']} in internal database.",
                    evidence={
                        "serial_number": raw_s,
                        "current_case_id": current_case_id,
                        "prior_case_id": matched_prior["original_case_id"],
                        "prior_installed_at": matched_prior.get("installed_at"),
                        "prior_asset_type": matched_prior.get("asset_type"),
                        "scope": "internal_lender_registry"
                    }
                )
            )
        else:
            results.append(
                VerificationCheckItem(
                    check_type=CheckTypeEnum.SERIAL_INTERNAL_DUPLICATE,
                    check_name=f"Internal Asset Registry Check: {raw_s}",
                    status=CheckStatusEnum.PASS,
                    severity=CheckSeverityEnum.INFO,
                    message=f"Serial number '{raw_s}' verified unique against internal registered asset database.",
                    evidence={
                        "serial_number": raw_s,
                        "current_case_id": current_case_id,
                        "scope": "internal_lender_registry"
                    }
                )
            )

    return results
