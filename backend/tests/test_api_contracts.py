import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dealers_contract():
    response = client.get("/dealers")
    assert response.status_code == 200
    dealers = response.json()
    assert isinstance(dealers, list)
    assert len(dealers) >= 3
    
    # Check specific dealer
    dlr_resp = client.get("/dealers/DLR-001")
    assert dlr_resp.status_code == 200
    assert dlr_resp.json()["name"] == "Apex Solar Equipment Pvt Ltd"


def test_cases_contract():
    # List cases
    response = client.get("/cases")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Create case
    payload = {
        "dealer_id": "DLR-001",
        "customer_id": "CUST-001",
        "asset_type": "Solar Inverter 5kVA",
        "claimed_installation_address": "Plot 12, Rural Agripark, Pune, Maharashtra",
        "loan_amount": 185000.0,
        "notes": "Synthetic test case"
    }
    create_resp = client.post("/cases", json=payload)
    assert create_resp.status_code == 201
    created_case = create_resp.json()
    assert created_case["dealer_id"] == "DLR-001"
    assert "id" in created_case

    # Get case details
    get_resp = client.get(f"/cases/{created_case['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["asset_type"] == "Solar Inverter 5kVA"


def test_pipeline_contract_no_fake_verification():
    # Running pipeline returns clean not_implemented response
    response = client.post("/pipeline/run", json={"case_id": "test-case-123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_implemented"
    assert "Phase 1 Foundation" in data["message"]


def test_risk_score_contract_no_fake_verification():
    response = client.get("/risk-score/test-case-123")
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["requires_verification", "low"]
    assert "overall_score" in data

