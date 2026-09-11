import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.verification.models import CheckStatusEnum, CheckTypeEnum, CheckSeverityEnum
from app.verification.price_checks import verify_price_benchmark
from app.verification.serial_checks import verify_serial_numbers
from app.verification.consistency_checks import (
    verify_case_entity_consistency,
    verify_invoice_arithmetic,
    verify_required_evidence_fields
)
from app.verification.service import verification_service
from app.services.invoice_service import invoice_service

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Price Benchmark Checks
# ---------------------------------------------------------------------------
def test_price_within_tolerance_passes():
    # Benchmark for SG-5KVA-HYBRID is ₹52,000 with 15% tolerance: [₹44,200 – ₹59,800]
    items = [{"product_name": "Solar Inverter 5kVA", "unit_price": 50000.0, "quantity": 1}]
    results = verify_price_benchmark(items)
    assert len(results) == 1
    assert results[0].status == CheckStatusEnum.PASS
    assert "within normal benchmark range" in results[0].message


def test_price_outside_tolerance_anomaly():
    # Invoiced at ₹115,000 (+121% over benchmark)
    items = [{"product_name": "Solar Inverter 5kVA", "unit_price": 115000.0, "quantity": 1}]
    results = verify_price_benchmark(items)
    assert len(results) == 1
    assert results[0].status == CheckStatusEnum.ANOMALY
    assert results[0].severity == CheckSeverityEnum.HIGH
    assert results[0].evidence["variance_pct"] > 50.0


def test_missing_benchmark_inconclusive():
    # Unlisted product must be INCONCLUSIVE, NEVER fraud or anomaly
    items = [{"product_name": "Ultra Custom Satellite Receiver XY-900", "unit_price": 99000.0, "quantity": 1}]
    results = verify_price_benchmark(items)
    assert len(results) == 1
    assert results[0].status == CheckStatusEnum.INCONCLUSIVE
    assert "No benchmark available" in results[0].message


# ---------------------------------------------------------------------------
# 2. Serial Number Checks
# ---------------------------------------------------------------------------
def test_serial_format_valid_passes():
    items = [{"product_name": "Pump System", "serial_numbers": ["PUMP-2026-X9921"]}]
    results = verify_serial_numbers(current_case_id="CAS-2026-999", line_items=items)
    format_results = [r for r in results if r.check_type == CheckTypeEnum.SERIAL_PRESENCE_AND_FORMAT]
    assert len(format_results) == 1
    assert format_results[0].status == CheckStatusEnum.PASS


def test_serial_format_invalid_anomaly():
    placeholders = ["TEST", "UNKNOWN", "123456", "000000", "N/A"]
    for ph in placeholders:
        items = [{"product_name": "Inverter", "serial_numbers": [ph]}]
        results = verify_serial_numbers(current_case_id="CAS-2026-999", line_items=items)
        format_results = [r for r in results if r.check_type == CheckTypeEnum.SERIAL_PRESENCE_AND_FORMAT]
        assert len(format_results) == 1
        assert format_results[0].status == CheckStatusEnum.ANOMALY
        assert "placeholder" in format_results[0].message.lower()


def test_duplicate_serial_across_internal_cases_anomaly():
    # ASP-2025-99881 is registered to CAS-2026-001 in seed data
    items = [{"product_name": "Solar Pump", "serial_numbers": ["ASP-2025-99881"]}]
    results = verify_serial_numbers(current_case_id="CAS-2026-005", line_items=items)
    dup_results = [r for r in results if r.check_type == CheckTypeEnum.SERIAL_INTERNAL_DUPLICATE]
    assert len(dup_results) == 1
    assert dup_results[0].status == CheckStatusEnum.ANOMALY
    assert dup_results[0].severity == CheckSeverityEnum.HIGH
    assert dup_results[0].evidence["prior_case_id"] == "CAS-2026-001"
    assert dup_results[0].evidence["scope"] == "internal_lender_registry"


def test_duplicate_serial_within_same_invoice_anomaly():
    items = [
        {"product_name": "Solar Pump Unit A", "serial_numbers": ["PUMP-UNIQUE-101"]},
        {"product_name": "Solar Pump Unit B", "serial_numbers": ["PUMP-UNIQUE-101"]}
    ]
    results = verify_serial_numbers(current_case_id="CAS-2026-999", line_items=items)
    same_inv_dups = [r for r in results if r.check_type == CheckTypeEnum.SERIAL_SAME_INVOICE_DUPLICATE]
    assert len(same_inv_dups) == 1
    assert same_inv_dups[0].status == CheckStatusEnum.ANOMALY


# ---------------------------------------------------------------------------
# 3. Entity & Case Consistency Checks
# ---------------------------------------------------------------------------
def test_case_entity_consistency_passes():
    invoice_data = {
        "dealer_name": "Apex Solar Solutions Pvt Ltd",
        "customer_name": "Rajesh Sharma",
        "line_items": [{"product_name": "Solar Water Pump 5HP"}]
    }
    case_data = {
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "asset_type": "Solar Water Pump 5HP"
    }
    results = verify_case_entity_consistency(invoice_data, case_data)
    assert len(results) == 3
    assert all(r.status == CheckStatusEnum.PASS for r in results)


def test_dealer_mismatch_anomaly():
    invoice_data = {
        "dealer_name": "Completely Unrelated Dist Ltd",
        "customer_name": "Rajesh Sharma",
        "line_items": [{"product_name": "Solar Water Pump 5HP"}]
    }
    case_data = {
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "asset_type": "Solar Water Pump 5HP"
    }
    results = verify_case_entity_consistency(invoice_data, case_data)
    dealer_res = [r for r in results if "Dealer" in r.check_name][0]
    assert dealer_res.status == CheckStatusEnum.ANOMALY
    assert dealer_res.severity == CheckSeverityEnum.MEDIUM


def test_customer_mismatch_anomaly():
    invoice_data = {
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Different Unknown Person",
        "line_items": [{"product_name": "Solar Water Pump 5HP"}]
    }
    case_data = {
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "asset_type": "Solar Water Pump 5HP"
    }
    results = verify_case_entity_consistency(invoice_data, case_data)
    cust_res = [r for r in results if "Customer" in r.check_name][0]
    assert cust_res.status == CheckStatusEnum.ANOMALY


def test_asset_mismatch_anomaly():
    invoice_data = {
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "line_items": [{"product_name": "Diesel Generator 50kVA"}]
    }
    case_data = {
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "asset_type": "Solar Water Pump 5HP"
    }
    results = verify_case_entity_consistency(invoice_data, case_data)
    asset_res = [r for r in results if "Asset" in r.check_name][0]
    assert asset_res.status == CheckStatusEnum.ANOMALY


# ---------------------------------------------------------------------------
# 4. Arithmetic & Required Evidence Checks
# ---------------------------------------------------------------------------
def test_invoice_arithmetic_valid_passes():
    invoice_data = {
        "subtotal": 100000.0,
        "tax_amount": 18000.0,
        "total_amount": 118000.0,
        "line_items": [{"product_name": "Inverter", "quantity": 2, "unit_price": 50000.0, "total_amount": 100000.0}]
    }
    results = verify_invoice_arithmetic(invoice_data)
    assert all(r.status == CheckStatusEnum.PASS for r in results)


def test_invoice_arithmetic_invalid_anomaly():
    invoice_data = {
        "subtotal": 100000.0,
        "tax_amount": 18000.0,
        "total_amount": 150000.0,  # Expected: 118000.0
        "line_items": [{"product_name": "Inverter", "quantity": 2, "unit_price": 50000.0, "total_amount": 100000.0}]
    }
    results = verify_invoice_arithmetic(invoice_data)
    gross_total_res = [r for r in results if "Gross Total" in r.check_name][0]
    assert gross_total_res.status == CheckStatusEnum.ANOMALY
    assert gross_total_res.evidence["difference"] == 32000.0


def test_missing_required_fields_inconclusive():
    incomplete_invoice = {
        "invoice_number": "INV-001",
        # Missing date, dealer_name, customer_name, total_amount, line_items
    }
    results = verify_required_evidence_fields(incomplete_invoice)
    assert len(results) == 1
    assert results[0].status == CheckStatusEnum.INCONCLUSIVE
    assert len(results[0].evidence["missing_fields"]) > 0


# ---------------------------------------------------------------------------
# 5. Service Orchestration, Idempotency & API Endpoints
# ---------------------------------------------------------------------------
def test_verification_api_lifecycle_and_idempotency():
    # 1. Create completed invoice record in memory store
    record = invoice_service.create_invoice_record(
        case_id="CAS-2026-001",
        original_filename="synthetic_verified_invoice.pdf",
        storage_path="CAS-2026-001/invoice_001.pdf"
    )
    inv_id = record["id"]

    # Populate extracted data
    record["status"] = "completed"
    record["invoice_number"] = "INV-APX-2026-001"
    record["invoice_date"] = "2026-01-12"
    record["dealer_name"] = "Apex Solar Solutions"
    record["customer_name"] = "Rajesh Sharma"
    record["total_amount"] = 195000.0
    record["tax_amount"] = 29728.8
    record["extraction"] = {
        "invoice_number": "INV-APX-2026-001",
        "invoice_date": "2026-01-12",
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "total_amount": 195000.0,
        "items": [
            {
                "product_name": "Solar Water Pump 5HP",
                "hsn_code": "84137010",
                "quantity": 1,
                "unit_price": 165271.2,
                "total_amount": 165271.2,
                "serial_numbers": ["ASP-2026-CLEAN-01"]
            }
        ]
    }
    record["line_items"] = record["extraction"]["items"]

    # 2. Call verification API
    response = client.post(f"/api/v1/verification/invoice/{inv_id}")
    assert response.status_code == 200
    summary = response.json()
    assert summary["invoice_id"] == inv_id
    assert summary["verification_status"] == "completed"
    assert summary["total_checks"] >= 5
    assert summary["passed_count"] > 0

    # 3. Verify Idempotency: Running a second time should replace cleanly and not multiply signals
    response_2 = client.post(f"/api/v1/verification/invoice/{inv_id}")
    assert response_2.status_code == 200
    summary_2 = response_2.json()
    assert summary_2["total_checks"] == summary["total_checks"]

    # 4. Get verification summary via GET
    get_res = client.get(f"/api/v1/verification/invoice/{inv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["invoice_id"] == inv_id


def test_incomplete_extraction_rejected_by_verification_endpoint():
    # Create invoice with status 'processing' (not completed)
    record = invoice_service.create_invoice_record(
        case_id="CAS-2026-001",
        original_filename="pending_inv.pdf",
        storage_path="CAS-2026-001/pending.pdf"
    )
    inv_id = record["id"]
    record["status"] = "processing"

    response = client.post(f"/api/v1/verification/invoice/{inv_id}")
    assert response.status_code == 400
    assert "AI extraction has not completed" in response.json()["detail"]


def test_zero_final_risk_score_created_in_phase3():
    # Verify that Phase 3 does NOT compute a 0-100 fraud score
    summary = verification_service.verify_invoice("NON_EXISTENT_ID")
    assert summary is None  # Safe handling

    # Check that verification summary notes explicitly state no composite scoring
    record = invoice_service.create_invoice_record(
        case_id="CAS-2026-001",
        original_filename="test_clean.pdf",
        storage_path="CAS-2026-001/test_clean.pdf"
    )
    record["status"] = "completed"
    record["extraction"] = {
        "invoice_number": "INV-001",
        "invoice_date": "2026-01-01",
        "dealer_name": "Apex Solar Solutions",
        "customer_name": "Rajesh Sharma",
        "total_amount": 50000.0,
        "items": [{"product_name": "Solar Inverter 5kVA", "unit_price": 50000.0, "quantity": 1}]
    }
    summary = verification_service.verify_invoice(record["id"])
    assert summary is not None
    assert "Final composite risk scoring not yet computed" in summary.notes or "without calculating composite" in summary.notes
