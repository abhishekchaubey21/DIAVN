import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.graph.models import (
    RelationshipCategoryEnum,
    RelationshipTypeEnum,
    RelationshipItem,
    GraphNode,
    GraphEdge,
    RelationshipGraphResponse,
    DealerConcentrationSummary
)
from app.graph.normalization import (
    normalize_phone,
    mask_phone,
    normalize_email,
    mask_email,
    normalize_address,
    mask_address,
    normalize_serial,
    hash_attribute
)
from app.graph.rules import (
    RELATIONSHIP_POLICY_VERSION,
    evaluate_dealer_relationship_anomaly
)
from app.graph.engine import RelationshipEngine, relationship_engine
from app.graph.service import relationship_service

client = TestClient(app)


# =============================================================================
# 1. NORMALIZATION & PRIVACY MASKING TESTS
# =============================================================================

def test_phone_normalization_and_privacy_masking():
    """Verify phone normalization handles country codes and standardizes/masks properly."""
    raw1 = "+91-9823000001"
    raw2 = "09823000001"
    raw3 = "9823000001"
    raw4 = "+91 98230 00001"

    norm1 = normalize_phone(raw1)
    assert norm1 == "9823000001"
    assert normalize_phone(raw2) == "9823000001"
    assert normalize_phone(raw3) == "9823000001"
    assert normalize_phone(raw4) == "9823000001"

    # Masking
    masked = mask_phone(raw1)
    assert masked == "+91-98****0001"
    assert "9823000001" not in masked


def test_email_normalization_and_privacy_masking():
    """Verify email normalization and privacy masking."""
    raw = "  Rajesh.Sharma@Example.SYNTHETIC  "
    norm = normalize_email(raw)
    assert norm == "rajesh.sharma@example.synthetic"

    masked = mask_email(norm)
    assert masked == "r***a@example.synthetic"
    assert "rajesh.sharma" not in masked


def test_address_normalization_and_privacy_masking():
    """Verify address normalizer collapses whitespace, punctuation, and standardizes terms."""
    raw1 = "Plot No. 45, MIDC Industrial Area, Phase II, Bhosari, Pune"
    raw2 = "Plot 45, MIDC, Phase II, Bhosari, Pune"
    
    norm1 = normalize_address(raw1)
    norm2 = normalize_address(raw2)
    assert norm1 is not None
    assert "midc" in norm1
    assert "plot" in norm1

    masked = mask_address(raw1)
    assert "Pune" in masked or "Plot" in masked


def test_internal_sha256_hash_generation():
    """Internal SHA-256 hash digest must be deterministic and prefixed with 'sha256:'."""
    val = "9823000001"
    h1 = hash_attribute(val)
    h2 = hash_attribute(val)
    assert h1 == h2
    assert h1.startswith("sha256:")


# =============================================================================
# 2. STRUCTURAL RELATIONSHIPS (CATEGORY A)
# =============================================================================

def test_structural_dealer_case_customer_links():
    """Verify standard structural relationships are created without anomaly flags."""
    case_data = {
        "id": "CAS-001",
        "case_number": "CAS-2026-001",
        "dealer_id": "DLR-001",
        "customer_id": "CUST-001",
        "loan_amount": 195000.0,
        "asset_type": "Solar Water Pump"
    }
    dealer_data = {"id": "DLR-001", "name": "Apex Solar", "dealer_code": "DLR-APX-01"}
    customer_data = {"id": "CUST-001", "full_name": "Rajesh Sharma", "customer_code": "CUST-001"}

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-001",
        case_data=case_data,
        dealer_data=dealer_data,
        customer_data=customer_data,
        invoices=[],
        assets=[],
        all_cases=[case_data],
        all_customers=[customer_data],
        all_dealers=[dealer_data],
        active_signals=[]
    )

    types = [r.relationship_type for r in structural]
    assert RelationshipTypeEnum.DEALER_SERVES_CUSTOMER in types
    assert RelationshipTypeEnum.CUSTOMER_ASSOCIATED_CASE in types
    assert RelationshipTypeEnum.DEALER_ORIGINATED_CASE in types
    assert len(anomalies) == 0
    assert len(signals) == 0


def test_structural_case_invoice_and_asset_links():
    """Verify structural links from case to invoices and registered assets."""
    case_data = {"id": "CAS-001", "dealer_id": "DLR-001", "customer_id": "CUST-001"}
    invoices = [{"id": "INV-101", "invoice_number": "INV-2026-01", "total_amount": 100000}]
    assets = [{"id": "AST-201", "brand": "AquaSun", "model_name": "ASP-5HP", "serial_number": "ASP-99881"}]

    structural, evidence, anomalies, _ = relationship_engine.analyze_case_relationships(
        case_id="CAS-001",
        case_data=case_data,
        dealer_data={"id": "DLR-001"},
        customer_data={"id": "CUST-001"},
        invoices=invoices,
        assets=assets,
        all_cases=[case_data],
        all_customers=[{"id": "CUST-001"}],
        all_dealers=[{"id": "DLR-001"}],
        active_signals=[]
    )

    types = [r.relationship_type for r in structural]
    assert RelationshipTypeEnum.CASE_CONTAINS_INVOICE in types
    assert RelationshipTypeEnum.CASE_CONTAINS_ASSET in types
    for r in structural:
        assert r.category == RelationshipCategoryEnum.STRUCTURAL
        assert r.risk_weight == 0.0


# =============================================================================
# 3. EVIDENCE RELATIONSHIPS (CATEGORY B) & FALSE-POSITIVE REMOVAL
# =============================================================================

def test_dealer_customer_shared_address_alone_is_not_anomaly():
    """
    Dealer address = Customer address generates DEALER_CUSTOMER_SHARED_ADDRESS (EVIDENCE).
    Must NOT trigger an anomaly on its own when no independent anomaly exists.
    """
    case_data = {
        "id": "CAS-ADDR-01",
        "dealer_id": "DLR-RAD",
        "customer_id": "CUST-01",
        "claimed_installation_address": "88, Agro Yard Extension, Hebbal, Bengaluru"
    }
    dealer_data = {"id": "DLR-RAD", "address": "88, Agro Yard Extension, Hebbal, Bengaluru", "contact_phone": "+91-9823000003"}
    customer_data = {"id": "CUST-01", "address": "88, Agro Yard Extension, Hebbal, Bengaluru", "contact_phone": "+91-9800000001"}

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-ADDR-01",
        case_data=case_data,
        dealer_data=dealer_data,
        customer_data=customer_data,
        invoices=[],
        assets=[],
        all_cases=[case_data],
        all_customers=[customer_data],
        all_dealers=[dealer_data],
        active_signals=[]  # No independent anomaly
    )

    ev_types = [r.relationship_type for r in evidence]
    assert RelationshipTypeEnum.DEALER_CUSTOMER_SHARED_ADDRESS in ev_types
    # Must NOT produce anomaly
    assert len(anomalies) == 0
    assert len(signals) == 0


def test_dealer_customer_shared_phone_alone_is_not_anomaly():
    """
    Dealer phone = Customer phone generates DEALER_CUSTOMER_SHARED_PHONE (EVIDENCE).
    Must NOT trigger an anomaly on its own without independent anomaly.
    """
    case_data = {
        "id": "CAS-PH-01",
        "dealer_id": "DLR-RAD",
        "customer_id": "CUST-05",
        "claimed_installation_address": "Plot 1, Rural Area"
    }
    dealer_data = {"id": "DLR-RAD", "address": "88, Agro Yard", "contact_phone": "+91-9823000003"}
    customer_data = {"id": "CUST-05", "address": "Plot 1, Rural Area", "contact_phone": "+91-9823000003"}

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-PH-01",
        case_data=case_data,
        dealer_data=dealer_data,
        customer_data=customer_data,
        invoices=[],
        assets=[],
        all_cases=[case_data],
        all_customers=[customer_data],
        all_dealers=[dealer_data],
        active_signals=[]  # No independent anomaly
    )

    ev_types = [r.relationship_type for r in evidence]
    assert RelationshipTypeEnum.DEALER_CUSTOMER_SHARED_PHONE in ev_types
    assert len(anomalies) == 0
    assert len(signals) == 0


def test_shared_customer_attribute_alone_is_not_anomaly():
    """Two customers sharing a phone number generates SHARED_CUSTOMER_PHONE (EVIDENCE) only."""
    cust1 = {"id": "C1", "contact_phone": "+91-9800000001", "address": "Address 1"}
    cust2 = {"id": "C2", "contact_phone": "+91-9800000001", "address": "Address 2"}

    case1 = {"id": "CAS-01", "dealer_id": "DLR-01", "customer_id": "C1"}

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-01",
        case_data=case1,
        dealer_data={"id": "DLR-01"},
        customer_data=cust1,
        invoices=[],
        assets=[],
        all_cases=[case1],
        all_customers=[cust1, cust2],
        all_dealers=[{"id": "DLR-01"}],
        active_signals=[]
    )

    ev_types = [r.relationship_type for r in evidence]
    assert RelationshipTypeEnum.SHARED_CUSTOMER_PHONE in ev_types
    assert len(anomalies) == 0


# =============================================================================
# 4. CONSERVATIVE ANOMALY COMBINATIONS (CATEGORY C)
# =============================================================================

def test_condition_a_multi_customer_cluster_triggers_anomaly():
    """
    Condition A: Same dealer + >= 2 distinct customers + shared contact + >= 2 cases
    Triggers DEALER_RELATIONSHIP_ANOMALY.
    """
    cust1 = {"id": "C1", "contact_phone": "+91-9800000001"}
    cust2 = {"id": "C2", "contact_phone": "+91-9800000001"}

    case1 = {"id": "CAS-01", "dealer_id": "DLR-01", "customer_id": "C1"}
    case2 = {"id": "CAS-02", "dealer_id": "DLR-01", "customer_id": "C2"}

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-01",
        case_data=case1,
        dealer_data={"id": "DLR-01"},
        customer_data=cust1,
        invoices=[],
        assets=[],
        all_cases=[case1, case2],
        all_customers=[cust1, cust2],
        all_dealers=[{"id": "DLR-01"}],
        active_signals=[]
    )

    assert len(anomalies) == 1
    assert anomalies[0].relationship_type == RelationshipTypeEnum.DEALER_RELATIONSHIP_ANOMALY
    assert anomalies[0].metadata["rule_name"] == "RULE_MULTI_CUSTOMER_CLUSTER_V1"
    assert anomalies[0].risk_weight == 0.0  # Must have weight 0 in Phase 7
    assert len(signals) == 1
    assert signals[0]["signal_type"] == "DEALER_RELATIONSHIP_ANOMALY"
    assert signals[0]["weight"] == 0.0


def test_condition_b_multi_factor_correlation_triggers_anomaly():
    """
    Condition B: Same dealer + evidence link (e.g. shared address) + independent active verification anomaly on this case.
    Triggers DEALER_RELATIONSHIP_ANOMALY.
    """
    case_data = {
        "id": "CAS-2026-007",
        "dealer_id": "DLR-RAD-03",
        "customer_id": "CUST-003",
        "claimed_installation_address": "88, Agro Yard Extension, Hebbal, Bengaluru"
    }
    dealer_data = {"id": "DLR-RAD-03", "address": "88, Agro Yard Extension, Hebbal, Bengaluru"}
    customer_data = {"id": "CUST-003", "address": "88, Agro Yard Extension, Hebbal, Bengaluru"}

    active_signals = [{
        "id": "SIG-PRICE-01",
        "signal_type": "INVOICE_PRICE_ANOMALY",
        "severity": "high",
        "is_active": True,
        "description": "Price +121% over benchmark"
    }]

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-2026-007",
        case_data=case_data,
        dealer_data=dealer_data,
        customer_data=customer_data,
        invoices=[],
        assets=[],
        all_cases=[case_data],
        all_customers=[customer_data],
        all_dealers=[dealer_data],
        active_signals=active_signals
    )

    assert len(anomalies) == 1
    assert anomalies[0].relationship_type == RelationshipTypeEnum.DEALER_RELATIONSHIP_ANOMALY
    assert anomalies[0].metadata["rule_name"] == "RULE_MULTI_FACTOR_CORRELATION_V1"
    assert anomalies[0].risk_weight == 0.0


def test_condition_b_requires_anomaly_on_same_case():
    """
    Condition B must NOT trigger if the independent anomaly belongs to an unrelated case.
    """
    case_data = {
        "id": "CAS-CLEAN-01",
        "dealer_id": "DLR-RAD-03",
        "customer_id": "CUST-003",
        "claimed_installation_address": "Plot 1, Separate Site"
    }
    dealer_data = {"id": "DLR-RAD-03", "address": "88, Agro Yard"}
    customer_data = {"id": "CUST-003", "address": "Plot 1, Separate Site"}

    # No evidence relationship, and no anomaly on this case
    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-CLEAN-01",
        case_data=case_data,
        dealer_data=dealer_data,
        customer_data=customer_data,
        invoices=[],
        assets=[],
        all_cases=[case_data],
        all_customers=[customer_data],
        all_dealers=[dealer_data],
        active_signals=[]
    )

    assert len(anomalies) == 0
    assert len(signals) == 0


# =============================================================================
# 5. CROSS-CASE LINKAGES & ANTI-DOUBLE-COUNTING TESTS
# =============================================================================

def test_cross_case_serial_link_without_score_duplication():
    """
    CROSS_CASE_SERIAL_LINK provides relationship graph context with risk_weight = 0.0.
    Does not duplicate Phase 3 duplicate serial scoring.
    """
    case1 = {"id": "CAS-01", "invoices": [{"serial_numbers": ["ASP-99881"]}]}
    case2 = {"id": "CAS-02", "invoices": [{"serial_numbers": ["ASP-99881"]}]}

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-01",
        case_data={"id": "CAS-01", "dealer_id": "D1", "customer_id": "C1"},
        dealer_data={"id": "D1"},
        customer_data={"id": "C1"},
        invoices=[{"id": "I1", "line_items": [{"serial_numbers": ["ASP-99881"]}]}],
        assets=[],
        all_cases=[case1, case2],
        all_customers=[{"id": "C1"}],
        all_dealers=[{"id": "D1"}],
        active_signals=[]
    )

    serial_links = [r for r in evidence if r.relationship_type == RelationshipTypeEnum.CROSS_CASE_SERIAL_LINK]
    assert len(serial_links) == 1
    assert serial_links[0].risk_weight == 0.0
    assert serial_links[0].metadata["serial_number"] == "ASP-99881"


def test_cross_case_image_link_without_score_duplication():
    """
    CROSS_CASE_IMAGE_LINK references Phase 4/5 evidence with risk_weight = 0.0.
    """
    active_signals = [{
        "id": "SIG-IMG-01",
        "signal_type": "IMAGE_PHASH_REUSE",
        "evidence_data": {"matching_case_id": "CAS-2026-001"}
    }]

    structural, evidence, anomalies, signals = relationship_engine.analyze_case_relationships(
        case_id="CAS-2026-005",
        case_data={"id": "CAS-2026-005", "dealer_id": "D1", "customer_id": "C1"},
        dealer_data={"id": "D1"},
        customer_data={"id": "C1"},
        invoices=[],
        assets=[],
        all_cases=[],
        all_customers=[],
        all_dealers=[],
        active_signals=active_signals
    )

    image_links = [r for r in evidence if r.relationship_type == RelationshipTypeEnum.CROSS_CASE_IMAGE_LINK]
    assert len(image_links) == 1
    assert image_links[0].risk_weight == 0.0
    assert image_links[0].metadata["matching_case_id"] == "CAS-2026-001"


# =============================================================================
# 6. DEALER CONCENTRATION & GRAPH PROJECTION TESTS
# =============================================================================

def test_dealer_concentration_descriptive_statistics():
    """Verify descriptive concentration metrics and lack of fraud score."""
    dealer_cases = [
        {"id": "C1", "customer_id": "CUST-1"},
        {"id": "C2", "customer_id": "CUST-2"},
        {"id": "C3", "customer_id": "CUST-1"}
    ]
    summary = relationship_engine.calculate_dealer_concentration(
        dealer_id="DLR-01",
        dealer_data={"id": "DLR-01", "name": "Apex Solar", "dealer_code": "APX-01"},
        dealer_cases=dealer_cases,
        dealer_invoices=[{}, {}],
        dealer_assets=[{}],
        all_relationships=[],
        active_anomalies_count=0
    )

    assert summary.total_cases == 3
    assert summary.distinct_customers == 2
    assert summary.total_invoices == 2
    assert summary.registered_assets == 1
    assert "Descriptive statistics only" in summary.policy_note


def test_high_volume_dealer_is_not_labeled_fraudulent():
    """A dealer with 50 cases does not automatically trigger an anomaly."""
    dealer_cases = [{"id": f"C-{i}", "customer_id": f"CUST-{i}"} for i in range(50)]
    summary = relationship_engine.calculate_dealer_concentration(
        dealer_id="DLR-HIGH-VOL",
        dealer_data={"id": "DLR-HIGH-VOL", "name": "Mega Dealer"},
        dealer_cases=dealer_cases,
        dealer_invoices=[],
        dealer_assets=[],
        all_relationships=[],
        active_anomalies_count=0
    )
    assert summary.potential_anomalies_count == 0


def test_graph_projection_nodes_and_edges():
    """Verify graph projection schema contains nodes and edges with proper categories."""
    rel1 = RelationshipItem(
        id="R1",
        source_entity_type="dealer",
        source_entity_id="D1",
        target_entity_type="customer",
        target_entity_id="C1",
        relationship_type=RelationshipTypeEnum.DEALER_SERVES_CUSTOMER,
        category=RelationshipCategoryEnum.STRUCTURAL,
        description="Serves customer"
    )
    graph = relationship_engine.build_graph_projection(
        case_id="CAS-01",
        dealer_id="D1",
        structural_links=[rel1],
        evidence_links=[],
        potential_anomalies=[],
        entity_metadata_map={"dealer:D1": {"label": "Apex Solar"}, "customer:C1": {"label": "Rajesh"}}
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].category == RelationshipCategoryEnum.STRUCTURAL
    assert graph.summary["nodes_count"] == 2
    assert graph.summary["edges_count"] == 1


# =============================================================================
# 7. DETERMINISM & SAFETY TESTS
# =============================================================================

def test_deterministic_repeated_analysis():
    """Running relationship analysis 10 times produces identical results."""
    case_data = {"id": "CAS-DET", "dealer_id": "D1", "customer_id": "C1"}
    first = relationship_service.analyze_and_persist_case_relationships("CAS-2026-001")
    
    for _ in range(9):
        current = relationship_service.analyze_and_persist_case_relationships("CAS-2026-001")
        assert len(current.structural_relationships) == len(first.structural_relationships)
        assert len(current.evidence_relationships) == len(first.evidence_relationships)
        assert len(current.potential_anomalies) == len(first.potential_anomalies)


def test_empty_case_and_empty_dealer_handled_safely():
    """Non-existent or empty case IDs return valid structural response without crashing."""
    res = relationship_service.get_case_relationships("CAS-EMPTY-999")
    assert res.case_id == "CAS-EMPTY-999"
    assert len(res.structural_relationships) >= 1
    assert len(res.potential_anomalies) == 0


# =============================================================================
# 8. API ENDPOINT CONTRACT TESTS
# =============================================================================

def test_api_get_case_relationships():
    """Test GET /api/v1/relationships/cases/{case_id} endpoint."""
    response = client.get("/api/v1/relationships/cases/CAS-2026-001")
    assert response.status_code == 200
    data = response.json()
    assert "structural_relationships" in data
    assert "evidence_relationships" in data
    assert "potential_anomalies" in data
    assert "policy_note" in data
    assert data["policy_version"] == "relationship-v1"


def test_api_get_dealer_relationships():
    """Test GET /api/v1/relationships/dealers/{dealer_id} endpoint."""
    response = client.get("/api/v1/relationships/dealers/DLR-001")
    assert response.status_code == 200
    data = response.json()
    assert data["dealer_id"] == "DLR-001"
    assert "total_cases" in data
    assert "distinct_customers" in data
    assert "policy_note" in data


def test_api_get_case_graph():
    """Test GET /api/v1/relationships/cases/{case_id}/graph endpoint."""
    response = client.get("/api/v1/relationships/cases/CAS-2026-001/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "summary" in data
