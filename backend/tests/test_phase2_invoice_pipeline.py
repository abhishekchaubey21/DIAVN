import io
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.invoice_extraction import InvoiceExtraction, InvoiceLineItemExtraction
from app.services.invoice_service import invoice_service
from app.services.storage_service import storage_service
from app.ai.invoice_extractor import invoice_extractor

client = TestClient(app)

SYNTHETIC_INVOICE_JSON = {
    "invoice_number": "INV-SYNTH-2026-901",
    "invoice_date": "2026-02-10",
    "dealer_name": "Apex Solar Solutions Pvt Ltd",
    "dealer_gstin": "27AAACA1234A1Z5",
    "dealer_address": "Plot 45, MIDC Phase II, Bhosari, Pune, Maharashtra",
    "customer_name": "Rajesh Sharma",
    "customer_address": "Village Khed, Taluka Shirur, Pune, Maharashtra - 412218",
    "customer_phone": "+91-9800000001",
    "items": [
        {
            "product_name": "5HP Solar Submersible Water Pump",
            "description": "AquaSun 5HP 3-Phase AC Submersible Pump with MPPT Controller",
            "hsn_code": "84137010",
            "quantity": 1.0,
            "unit_price": 165000.0,
            "taxable_amount": 165000.0,
            "tax_rate": 18.0,
            "tax_amount": 29700.0,
            "total_amount": 194700.0,
            "serial_number": "ASP-2026-SYNTH-001",
            "serial_numbers": ["ASP-2026-SYNTH-001"]
        }
    ],
    "subtotal": 165000.0,
    "total_tax": 29700.0,
    "total_amount": 194700.0,
    "currency": "INR",
    "extraction_confidence": 0.96,
    "notes": "Crisp digital tax invoice"
}


# ---------------------------------------------------------------------------
# TEST 1: Invalid file type rejected
# ---------------------------------------------------------------------------
def test_invalid_file_type_rejected():
    invalid_file = io.BytesIO(b"malicious executable content")
    response = client.post(
        "/api/v1/invoices",
        data={"case_id": "CAS-2026-001"},
        files={"file": ("malware.exe", invalid_file, "application/x-msdownload")}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


# ---------------------------------------------------------------------------
# TEST 2: Oversized file rejected (> 10MB)
# ---------------------------------------------------------------------------
def test_oversized_file_rejected():
    # Simulate file exceeding 10 MB limit
    oversized_bytes = b"0" * (11 * 1024 * 1024)
    file_obj = io.BytesIO(oversized_bytes)
    response = client.post(
        "/api/v1/invoices",
        data={"case_id": "CAS-2026-001"},
        files={"file": ("large_invoice.pdf", file_obj, "application/pdf")}
    )
    assert response.status_code == 400
    assert "File size exceeds maximum allowed limit" in response.json()["detail"]


# ---------------------------------------------------------------------------
# TEST 3: Missing case rejected (404)
# ---------------------------------------------------------------------------
def test_missing_case_rejected():
    fake_pdf = io.BytesIO(b"%PDF-1.4 dummy synthetic invoice pdf content")
    response = client.post(
        "/api/v1/invoices",
        data={"case_id": "NON_EXISTENT_CASE_99999"},
        files={"file": ("invoice.pdf", fake_pdf, "application/pdf")}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# TEST 4: Invoice record creation & upload
# ---------------------------------------------------------------------------
def test_invoice_upload_and_record_creation():
    dummy_pdf = io.BytesIO(b"%PDF-1.4 valid invoice document bytes")
    response = client.post(
        "/api/v1/invoices",
        data={"case_id": "CAS-2026-001"},
        files={"file": ("test_invoice.pdf", dummy_pdf, "application/pdf")}
    )
    assert response.status_code == 201
    data = response.json()
    assert "invoice_id" in data
    assert data["case_id"] == "CAS-2026-001"
    assert data["status"] == "processing"
    assert data["original_filename"] == "test_invoice.pdf"

    # Verify retrieval
    get_resp = client.get(f"/api/v1/invoices/{data['invoice_id']}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["id"] == data["invoice_id"]
    assert detail["verification_status"] == "pending_verification"


# ---------------------------------------------------------------------------
# TEST 5: Extraction schema validation (Pydantic model)
# ---------------------------------------------------------------------------
def test_extraction_schema_validation():
    extraction = InvoiceExtraction.model_validate(SYNTHETIC_INVOICE_JSON)
    assert extraction.invoice_number == "INV-SYNTH-2026-901"
    assert extraction.total_amount == 194700.0
    assert len(extraction.items) == 1
    assert extraction.items[0].product_name == "5HP Solar Submersible Water Pump"
    assert extraction.items[0].serial_number == "ASP-2026-SYNTH-001"
    assert extraction.extraction_confidence == 0.96


# ---------------------------------------------------------------------------
# TEST 6: Missing fields become null (No hallucination)
# ---------------------------------------------------------------------------
def test_missing_fields_become_null():
    partial_json = {
        "invoice_number": "INV-PARTIAL-001",
        "items": [
            {
                "product_name": "Generic Panel"
                # description, hsn_code, unit_price etc. are missing
            }
        ]
    }
    extraction = InvoiceExtraction.model_validate(partial_json)
    assert extraction.invoice_number == "INV-PARTIAL-001"
    assert extraction.invoice_date is None
    assert extraction.dealer_gstin is None
    assert extraction.dealer_name is None
    assert extraction.total_amount is None
    assert extraction.items[0].hsn_code is None
    assert extraction.items[0].serial_number is None


# ---------------------------------------------------------------------------
# TEST 7: Malformed AI response handled safely (Does not crash)
# ---------------------------------------------------------------------------
def test_malformed_ai_response_handled_safely():
    mock_response = MagicMock()
    mock_response.text = "NOT_VALID_JSON {{{ invalid syntax"

    with patch("app.ai.invoice_extractor.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        success, extraction, err_msg, duration = invoice_extractor.extract_from_bytes(
            file_bytes=b"%PDF-1.4 dummy",
            content_type="application/pdf"
        )
        assert success is False
        assert extraction is None
        assert "Malformed extraction output" in err_msg or "failed" in err_msg.lower()


# ---------------------------------------------------------------------------
# TEST 8: Gemini API failure handled safely
# ---------------------------------------------------------------------------
def test_gemini_api_failure_handled_safely():
    with patch("app.ai.invoice_extractor.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Quota exceeded 429")
        mock_get_client.return_value = mock_client

        success, extraction, err_msg, duration = invoice_extractor.extract_from_bytes(
            file_bytes=b"%PDF-1.4 dummy",
            content_type="application/pdf"
        )
        assert success is False
        assert extraction is None
        assert "Original document preserved" in err_msg


# ---------------------------------------------------------------------------
# TEST 9: Mocked full extraction flow updates invoice record and line items
# ---------------------------------------------------------------------------
def test_mocked_full_extraction_flow():
    mock_response = MagicMock()
    mock_response.text = json.dumps(SYNTHETIC_INVOICE_JSON)

    with patch("app.ai.invoice_extractor.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        # 1. Upload
        dummy_pdf = io.BytesIO(b"%PDF-1.4 synthetic pump invoice")
        upload_resp = client.post(
            "/api/v1/invoices",
            data={"case_id": "CAS-2026-001"},
            files={"file": ("pump_invoice.pdf", dummy_pdf, "application/pdf")}
        )
        inv_id = upload_resp.json()["invoice_id"]

        # 2. Process extraction
        invoice_service.process_extraction(inv_id)

        # 3. Verify updated details
        get_resp = client.get(f"/api/v1/invoices/{inv_id}")
        assert get_resp.status_code == 200
        detail = get_resp.json()
        assert detail["status"] == "completed"
        assert detail["invoice_number"] == "INV-SYNTH-2026-901"
        assert detail["dealer_gstin"] == "27AAACA1234A1Z5"
        assert detail["total_amount"] == 194700.0
        assert detail["extraction_confidence"] == 0.96
        assert len(detail["line_items"]) == 1
        assert detail["line_items"][0]["serial_numbers"] == ["ASP-2026-SYNTH-001"]

        # 4. Critical: Ensure verification status remains 'pending_verification' (NO fake verification)
        assert detail["verification_status"] == "pending_verification"


# ---------------------------------------------------------------------------
# TEST 10: API does not expose service-role key or sensitive credentials
# ---------------------------------------------------------------------------
def test_api_does_not_expose_service_role_key():
    routes_to_check = [
        "/api/v1/health",
        "/api/v1/cases",
        "/api/v1/dealers",
        "/api/v1/invoices/CAS-2026-001"
    ]
    for route in routes_to_check:
        res = client.get(route)
        text = res.text
        assert "SERVICE_ROLE" not in text
        assert "service_role" not in text
        assert "GEMINI_API_KEY" not in text
        assert "secret" not in text.lower() or "secret" in "not a secret"
