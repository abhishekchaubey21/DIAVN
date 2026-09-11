import pytest
from datetime import datetime, timezone

from app.risk_engine.models import (
    RiskBandEnum,
    EvidenceGroupEnum,
    RiskAssessmentResult,
    ScoreComponentItem
)
from app.risk_engine.rules import (
    POLICY_VERSION,
    DEFAULT_POLICY_WEIGHTS,
    DEFAULT_GROUP_CAPS,
    TOTAL_SCORE_CAP,
    get_risk_band_for_score,
    get_recommended_action_for_band
)
from app.risk_engine.calculator import calculate_case_risk_assessment
from app.risk_engine.service import RiskEngineService


# =============================================================================
# 1. BASELINE CALCULATIONS & SINGLE-SIGNAL TESTS
# =============================================================================

def test_clean_case_returns_score_zero():
    """Case with zero active anomalies must return score 0, LOW band, and baseline recommendation."""
    assessment = calculate_case_risk_assessment(
        case_id="CAS-CLEAN-01",
        raw_signals=[]
    )
    assert assessment.overall_score == 0
    assert assessment.raw_score == 0
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.recommended_action == "No immediate additional verification indicated by the configured DIAVN rules."
    assert len(assessment.components) == 0


def test_single_low_weight_signal():
    """Single low extraction confidence signal adds +5."""
    signals = [{
        "id": "SIG-EXT-01",
        "signal_type": "LOW_EXTRACTION_CONFIDENCE",
        "severity": "low",
        "description": "Invoice extraction confidence 0.58 below threshold.",
        "evidence_data": {"confidence": 0.58},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-LOW-01", signals)
    assert assessment.overall_score == 5
    assert assessment.raw_score == 5
    assert assessment.risk_band == RiskBandEnum.LOW


def test_duplicate_serial_contribution():
    """Duplicate internal serial signal adds +35."""
    signals = [{
        "id": "SIG-SER-01",
        "signal_type": "DUPLICATE_SERIAL",
        "severity": "critical",
        "description": "Serial number ASP-2025-99881 already registered in case CAS-2026-001.",
        "evidence_data": {"serial_number": "ASP-2025-99881"},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-SER-01", signals)
    assert assessment.overall_score == 35
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.components[0].effective_contribution == 35
    assert assessment.components[0].group == EvidenceGroupEnum.SERIAL


def test_invoice_price_anomaly_contribution():
    """Invoice price anomaly signal adds +20."""
    signals = [{
        "id": "SIG-PRC-01",
        "signal_type": "INVOICE_PRICE_ANOMALY",
        "severity": "medium",
        "description": "Invoice unit price 55000 exceeds benchmark average 45000 by 22.2%.",
        "evidence_data": {"claimed_price": 55000, "variance_pct": 22.2},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-PRC-01", signals)
    assert assessment.overall_score == 20
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.components[0].effective_contribution == 20
    assert assessment.components[0].group == EvidenceGroupEnum.INVOICE_PRICE


def test_image_phash_reuse_contribution():
    """Image pHash cross-case reuse adds +20."""
    signals = [{
        "id": "SIG-PHASH-01",
        "signal_type": "IMAGE_PHASH_REUSE",
        "severity": "high",
        "description": "Exact perceptual image match detected with case CAS-2026-001.",
        "evidence_data": {"hamming_distance": 0, "matching_case_id": "CAS-2026-001"},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-PHASH-01", signals)
    assert assessment.overall_score == 20
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.components[0].effective_contribution == 20


def test_image_embedding_similarity_contribution():
    """Image deep visual feature embedding similarity adds +15."""
    signals = [{
        "id": "SIG-EMB-01",
        "signal_type": "IMAGE_EMBEDDING_SIMILARITY",
        "severity": "high",
        "description": "Deep visual feature similarity 0.9850 detected with case CAS-2026-001.",
        "evidence_data": {"cosine_similarity": 0.9850, "matching_case_id": "CAS-2026-001"},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-EMB-01", signals)
    assert assessment.overall_score == 15
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.components[0].effective_contribution == 15


def test_gps_mismatch_contribution():
    """GPS location distance anomaly adds +12."""
    signals = [{
        "id": "SIG-GPS-01",
        "signal_type": "GPS_MISMATCH",
        "severity": "high",
        "description": "Photo GPS is 234.8 km from claimed installation site.",
        "evidence_data": {"distance_km": 234.8, "threshold_km": 1.0},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-GPS-01", signals)
    assert assessment.overall_score == 12
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.components[0].effective_contribution == 12


def test_missing_exif_contribution_when_configured():
    """Missing EXIF metadata adds +8 when configured as active risk signal."""
    signals = [{
        "id": "SIG-EXIF-01",
        "signal_type": "MISSING_EXIF",
        "severity": "low",
        "description": "No camera telemetry found in installation image.",
        "evidence_data": {"has_exif": False},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-EXIF-01", signals)
    assert assessment.overall_score == 8
    assert assessment.risk_band == RiskBandEnum.LOW


# =============================================================================
# 2. ANTI-DOUBLE-COUNTING & GROUP CAPPING TESTS
# =============================================================================

def test_image_reuse_group_cap_prevents_double_counting():
    """
    pHash reuse (+20) and Embedding similarity (+15) for the same underlying image
    must have raw sum 35, but capped to IMAGE_REUSE_GROUP_MAX = 25.
    """
    signals = [
        {
            "id": "SIG-IMG-01",
            "signal_type": "IMAGE_PHASH_REUSE",
            "severity": "high",
            "description": "Exact pHash reuse.",
            "evidence_data": {"current_image_id": "IMG-01", "matching_case_id": "CAS-999"},
            "is_active": True
        },
        {
            "id": "SIG-IMG-02",
            "signal_type": "IMAGE_EMBEDDING_SIMILARITY",
            "severity": "high",
            "description": "Deep visual feature similarity 0.9920.",
            "evidence_data": {"current_image_id": "IMG-01", "matching_case_id": "CAS-999"},
            "is_active": True
        }
    ]
    assessment = calculate_case_risk_assessment("CAS-REUSE-01", signals)

    assert assessment.raw_score == 35
    assert assessment.overall_score == 25  # Group capped to 25
    assert assessment.group_contributions["IMAGE_REUSE"].raw_sum == 35
    assert assessment.group_contributions["IMAGE_REUSE"].effective_contribution == 25
    assert assessment.group_contributions["IMAGE_REUSE"].group_cap == 25

    # Sum of component effective contributions must equal 25
    total_effective = sum(c.effective_contribution for c in assessment.components)
    assert total_effective == 25


def test_duplicate_serial_deduplication():
    """Multiple duplicate serial signals for the same serial number count only once (+35)."""
    signals = [
        {
            "id": "SIG-SER-01",
            "signal_type": "DUPLICATE_SERIAL",
            "severity": "critical",
            "description": "Serial ASP-99881 in line item 1 duplicated.",
            "evidence_data": {"serial_number": "ASP-99881"},
            "is_active": True
        },
        {
            "id": "SIG-SER-02",
            "signal_type": "DUPLICATE_SERIAL",
            "severity": "critical",
            "description": "Serial ASP-99881 in line item 2 duplicated.",
            "evidence_data": {"serial_number": "ASP-99881"},
            "is_active": True
        },
        {
            "id": "SIG-SER-03",
            "signal_type": "DUPLICATE_SERIAL",
            "severity": "critical",
            "description": "Serial ASP-99881 registered asset check duplicated.",
            "evidence_data": {"serial_number": "ASP-99881"},
            "is_active": True
        }
    ]
    assessment = calculate_case_risk_assessment("CAS-DEDUP-01", signals)

    # Deduplication ensures only 1 distinct serial condition contributes
    assert len(assessment.components) == 1
    assert assessment.overall_score == 35


# =============================================================================
# 3. NON-RISK & INCONCLUSIVE SIGNAL HANDLING
# =============================================================================

def test_same_case_image_duplicate_does_not_score():
    """Same-case duplicate image has weight 0 and does not increase score."""
    signals = [{
        "id": "SIG-SAME-01",
        "signal_type": "IMAGE_SAME_CASE_DUPLICATE",
        "severity": "info",
        "description": "Image is redundant within same case.",
        "evidence_data": {},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-SAME-01", signals)
    assert assessment.overall_score == 0


def test_inconclusive_checks_do_not_contribute_to_risk():
    """Signals with status INCONCLUSIVE, PASS, or INFO must have 0 contribution."""
    signals = [
        {
            "id": "SIG-INC-01",
            "signal_type": "PRICE_BENCHMARK_MATCH",
            "status": "INCONCLUSIVE",
            "severity": "info",
            "description": "No benchmark found for model.",
            "evidence_data": {}
        },
        {
            "id": "SIG-INC-02",
            "signal_type": "GPS_LOCATION_CONSISTENCY",
            "status": "INCONCLUSIVE",
            "severity": "info",
            "description": "No reference GPS coordinates available.",
            "evidence_data": {}
        },
        {
            "id": "SIG-INC-03",
            "signal_type": "IMAGE_EMBEDDING_SIMILARITY",
            "status": "PASS",
            "severity": "info",
            "description": "No similar images found.",
            "evidence_data": {}
        }
    ]
    assessment = calculate_case_risk_assessment("CAS-INC-01", signals)
    assert assessment.overall_score == 0
    assert len(assessment.components) == 0


# =============================================================================
# 4. RISK BANDS & TOTAL SCORE CAPS
# =============================================================================

def test_risk_bands_mapping():
    """Verify exact mapping of numerical scores to categorical risk bands."""
    assert get_risk_band_for_score(0) == RiskBandEnum.LOW
    assert get_risk_band_for_score(39) == RiskBandEnum.LOW
    assert get_risk_band_for_score(40) == RiskBandEnum.MEDIUM
    assert get_risk_band_for_score(69) == RiskBandEnum.MEDIUM
    assert get_risk_band_for_score(70) == RiskBandEnum.HIGH
    assert get_risk_band_for_score(100) == RiskBandEnum.HIGH


def test_recommended_action_mapping():
    """Verify action text per risk band."""
    assert get_recommended_action_for_band(RiskBandEnum.LOW) == "No immediate additional verification indicated by the configured DIAVN rules."
    assert get_recommended_action_for_band(RiskBandEnum.MEDIUM) == "Additional document/evidence review recommended."
    assert get_recommended_action_for_band(RiskBandEnum.HIGH) == "Field verification recommended."


def test_total_score_capped_at_100():
    """Score must never exceed 100 regardless of the number of stacked anomalies."""
    signals = [
        {"id": "S1", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial": "A"}, "is_active": True}, # 35
        {"id": "S2", "signal_type": "INVOICE_PRICE_ANOMALY", "evidence_data": {}, "is_active": True},          # 20
        {"id": "S3", "signal_type": "GPS_MISMATCH", "evidence_data": {}, "is_active": True},                  # 12
        {"id": "S4", "signal_type": "IMAGE_PHASH_REUSE", "evidence_data": {}, "is_active": True},             # 20 (cap 25)
        {"id": "S5", "signal_type": "IMAGE_EMBEDDING_SIMILARITY", "evidence_data": {}, "is_active": True},    # 15
        {"id": "S6", "signal_type": "DEALER_RELATIONSHIP_ANOMALY", "evidence_data": {}, "is_active": True},   # 15
        {"id": "S7", "signal_type": "CASE_ENTITY_CONSISTENCY", "evidence_data": {}, "is_active": True},       # 15
        {"id": "S8", "signal_type": "MISSING_EXIF", "evidence_data": {}, "is_active": True},                  # 8
    ]
    assessment = calculate_case_risk_assessment("CAS-EXTREME-01", signals)

    assert assessment.raw_score > 100
    assert assessment.overall_score == 100
    assert assessment.risk_band == RiskBandEnum.HIGH
    assert assessment.recommended_action == "Field verification recommended."


# =============================================================================
# 5. CONTROLLED SYNTHETIC SCENARIOS (CASES A – F)
# =============================================================================

def test_scenario_case_a_clean():
    """CASE A — CLEAN: No anomalies -> score 0, LOW band."""
    assessment = calculate_case_risk_assessment("CAS-2026-001", [])
    assert assessment.overall_score == 0
    assert assessment.risk_band == RiskBandEnum.LOW
    assert assessment.recommended_action == "No immediate additional verification indicated by the configured DIAVN rules."


def test_scenario_case_b_price_anomaly():
    """CASE B — PRICE ANOMALY: Price anomaly only -> score 20, LOW band."""
    signals = [{
        "id": "SIG-PRC",
        "signal_type": "INVOICE_PRICE_ANOMALY",
        "evidence_data": {"claimed_price": 55000, "variance_pct": 22.2},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-2026-002", signals)
    assert assessment.overall_score == 20
    assert assessment.risk_band == RiskBandEnum.LOW


def test_scenario_case_c_duplicate_serial():
    """CASE C — DUPLICATE SERIAL: Serial duplicate only -> score 35, LOW band."""
    signals = [{
        "id": "SIG-SER",
        "signal_type": "DUPLICATE_SERIAL",
        "evidence_data": {"serial_number": "ASP-99881"},
        "is_active": True
    }]
    assessment = calculate_case_risk_assessment("CAS-SER-ONLY", signals)
    assert assessment.overall_score == 35
    assert assessment.risk_band == RiskBandEnum.LOW


def test_scenario_case_d_image_reuse():
    """CASE D — IMAGE REUSE: pHash (20) + Embedding (15) -> raw 35, group cap 25."""
    signals = [
        {"id": "S-PHASH", "signal_type": "IMAGE_PHASH_REUSE", "evidence_data": {"img": "1"}, "is_active": True},
        {"id": "S-EMB", "signal_type": "IMAGE_EMBEDDING_SIMILARITY", "evidence_data": {"img": "1"}, "is_active": True},
    ]
    assessment = calculate_case_risk_assessment("CAS-2026-005", signals)
    assert assessment.raw_score == 35
    assert assessment.overall_score == 25
    assert assessment.risk_band == RiskBandEnum.LOW


def test_scenario_case_e_multiple_anomalies():
    """
    CASE E — MULTIPLE ANOMALIES:
    Duplicate serial (35) + Price anomaly (20) + GPS mismatch (12) + Image reuse (25 capped)
    Raw sum: 92 -> Overall score: 92, HIGH band.
    """
    signals = [
        {"id": "S-SER", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial": "MIC-019"}, "is_active": True},   # 35
        {"id": "S-PRC", "signal_type": "INVOICE_PRICE_ANOMALY", "evidence_data": {}, "is_active": True},                  # 20
        {"id": "S-GPS", "signal_type": "GPS_MISMATCH", "evidence_data": {}, "is_active": True},                          # 12
        {"id": "S-PHASH", "signal_type": "IMAGE_PHASH_REUSE", "evidence_data": {"img": "1"}, "is_active": True},         # 20
        {"id": "S-EMB", "signal_type": "IMAGE_EMBEDDING_SIMILARITY", "evidence_data": {"img": "1"}, "is_active": True},  # 15 -> (cap 25)
    ]
    assessment = calculate_case_risk_assessment("CAS-2026-007", signals)
    assert assessment.raw_score == 102
    assert assessment.overall_score == 92
    assert assessment.risk_band == RiskBandEnum.HIGH
    assert assessment.recommended_action == "Field verification recommended."


def test_scenario_case_f_extreme_anomalies():
    """CASE F — EXTREME: Multiple high signals capped at 100."""
    signals = [
        {"id": "S1", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial": "S1"}, "is_active": True},
        {"id": "S2", "signal_type": "INVOICE_PRICE_ANOMALY", "evidence_data": {}, "is_active": True},
        {"id": "S3", "signal_type": "GPS_MISMATCH", "evidence_data": {}, "is_active": True},
        {"id": "S4", "signal_type": "IMAGE_PHASH_REUSE", "evidence_data": {"img": "1"}, "is_active": True},
        {"id": "S5", "signal_type": "DEALER_RELATIONSHIP_ANOMALY", "evidence_data": {}, "is_active": True},
        {"id": "S6", "signal_type": "CASE_ENTITY_CONSISTENCY", "evidence_data": {}, "is_active": True},
    ]
    assessment = calculate_case_risk_assessment("CAS-EXTREME", signals)
    assert assessment.overall_score == 100
    assert assessment.risk_band == RiskBandEnum.HIGH


# =============================================================================
# 6. SCORE INTEGRITY, DETERMINISM, & POLICY VERSIONING
# =============================================================================

def test_score_integrity_displayed_breakdown_matches_score():
    """
    Confirm that the sum of displayed component contributions equals the persisted score.
    """
    signals = [
        {"id": "S-SER", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial": "S1"}, "is_active": True},
        {"id": "S-PRC", "signal_type": "INVOICE_PRICE_ANOMALY", "evidence_data": {}, "is_active": True},
        {"id": "S-GPS", "signal_type": "GPS_MISMATCH", "evidence_data": {}, "is_active": True},
        {"id": "S-PHASH", "signal_type": "IMAGE_PHASH_REUSE", "evidence_data": {"img": "1"}, "is_active": True},
        {"id": "S-EMB", "signal_type": "IMAGE_EMBEDDING_SIMILARITY", "evidence_data": {"img": "1"}, "is_active": True},
    ]
    assessment = calculate_case_risk_assessment("CAS-INTEGRITY", signals)

    # Calculate sum of components
    components_sum = sum(c.effective_contribution for c in assessment.components)
    assert components_sum == assessment.overall_score
    assert components_sum == 92


def test_deterministic_recalculation():
    """Running calculation 10 times on identical inputs produces identical results."""
    signals = [
        {"id": "S1", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial": "S1"}, "is_active": True},
        {"id": "S2", "signal_type": "INVOICE_PRICE_ANOMALY", "evidence_data": {}, "is_active": True}
    ]

    first = calculate_case_risk_assessment("CAS-DET", signals)
    for _ in range(9):
        current = calculate_case_risk_assessment("CAS-DET", signals)
        assert current.overall_score == first.overall_score
        assert current.raw_score == first.raw_score
        assert current.risk_band == first.risk_band
        assert len(current.components) == len(first.components)


def test_policy_version_and_audit_note_presence():
    """Assessment must specify policy version and legal/compliance notice."""
    assessment = calculate_case_risk_assessment("CAS-AUDIT", [])
    assert assessment.policy_version == "risk-v1"
    assert "not a statistical probability of fraud" in assessment.audit_note


def test_every_component_has_evidence_and_source():
    """Every score contribution must have non-null evidence and pipeline source info."""
    signals = [
        {"id": "S1", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial_number": "ASP-001"}, "is_active": True},
        {"id": "S2", "signal_type": "GPS_MISMATCH", "evidence_data": {"distance_km": 15.0}, "is_active": True}
    ]
    assessment = calculate_case_risk_assessment("CAS-EV-TEST", signals)

    for comp in assessment.components:
        assert comp.source in ["invoice_verification", "image_forensics", "deep_visual_embeddings", "dealer_network_analysis", "verification_pipeline"]
        assert isinstance(comp.evidence, dict)
        assert len(comp.evidence) > 0


def test_service_persistence_and_history():
    """RiskEngineService persists assessments and preserves historical records."""
    service = RiskEngineService()

    res1 = service.calculate_and_persist_assessment("CAS-HIST-01", policy_version="risk-v1")
    assert res1.case_id == "CAS-HIST-01"

    res2 = service.get_case_assessment("CAS-HIST-01")
    assert res2.overall_score == res1.overall_score

    history = service.get_case_assessment_history("CAS-HIST-01")
    assert len(history) >= 1
    assert history[-1].policy_version == "risk-v1"
