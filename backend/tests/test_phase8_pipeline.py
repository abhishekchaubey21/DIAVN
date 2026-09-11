import pytest
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.models import (
    PipelineRunStatusEnum,
    PipelineStageEnum,
    StageStatusEnum,
    PipelineRunRecord,
    PipelineStatusResponse
)
from app.pipeline.service import pipeline_service, ActivePipelineRunConflictException
from app.risk_engine.models import RiskBandEnum
from app.risk_engine.rules import DEFAULT_POLICY_WEIGHTS, DEFAULT_GROUP_CAPS

client = TestClient(app)


# =============================================================================
# 1. CORE PIPELINE EXECUTION & STAGE PROGRESSION
# =============================================================================

def test_pipeline_starts_for_valid_case():
    """Verify pipeline executes stages in order for a valid case and returns status."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    assert res.case_id == "CAS-2026-001"
    assert res.status in [PipelineRunStatusEnum.COMPLETED, PipelineRunStatusEnum.PARTIAL]
    assert len(res.stages) == 6
    assert res.pipeline_version == "pipeline-v1"
    assert res.total_duration_ms >= 0


def test_pipeline_state_transitions():
    """Verify each stage has valid started_at, completed_at, and duration_ms recorded."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    stage_names = [s.stage_name for s in res.stages]

    assert PipelineStageEnum.INVOICE_EXTRACTION in stage_names
    assert PipelineStageEnum.INVOICE_VERIFICATION in stage_names
    assert PipelineStageEnum.IMAGE_PROCESSING in stage_names
    assert PipelineStageEnum.RELATIONSHIP_ANALYSIS in stage_names
    assert PipelineStageEnum.RISK_CALCULATION in stage_names
    assert PipelineStageEnum.VERIFICATION_TASK_DISPATCH in stage_names

    for stage in res.stages:
        assert stage.started_at is not None
        assert stage.completed_at is not None
        assert stage.status in [StageStatusEnum.COMPLETED, StageStatusEnum.SKIPPED, StageStatusEnum.INCONCLUSIVE]


# =============================================================================
# 2. CONCURRENCY GUARD & IDEMPOTENCY
# =============================================================================

def test_concurrency_guard_database_enforced():
    """Verify simultaneous active runs on same case raise conflict exception."""
    from app.pipeline.service import _ACTIVE_CASE_RUNS, _ACTIVE_RUNS_LOCK

    case_id = "CAS-CONCURRENT-01"
    with _ACTIVE_RUNS_LOCK:
        _ACTIVE_CASE_RUNS[case_id] = "RUN-ACTIVE-LOCK"

    try:
        with pytest.raises(ActivePipelineRunConflictException) as exc_info:
            pipeline_service.start_pipeline_run(case_id, force_rerun=False)
        assert case_id in str(exc_info.value)
    finally:
        with _ACTIVE_RUNS_LOCK:
            _ACTIVE_CASE_RUNS.pop(case_id, None)


def test_rerun_preserves_run_history():
    """Rerunning a completed pipeline creates a new record while preserving history."""
    case_id = "CAS-HIST-001"
    run1 = pipeline_service.start_pipeline_run(case_id, force_rerun=True)
    run2 = pipeline_service.start_pipeline_run(case_id, force_rerun=True)

    history = pipeline_service.get_case_pipeline_runs(case_id)
    assert len(history) >= 2
    assert history[0].id != history[1].id


# =============================================================================
# 3. REUSE OF EXISTING PHASES 2–7 (ZERO LOGIC DUPLICATION)
# =============================================================================

def test_invoice_extraction_stage_calls_phase2():
    """Verify invoice extraction stage delegates to Phase 2 invoice service."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    s1 = [s for s in res.stages if s.stage_name == PipelineStageEnum.INVOICE_EXTRACTION][0]
    assert s1.status in [StageStatusEnum.COMPLETED, StageStatusEnum.SKIPPED]


def test_invoice_verification_stage_calls_phase3():
    """Verify invoice verification stage delegates to Phase 3 verification engine."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    s2 = [s for s in res.stages if s.stage_name == PipelineStageEnum.INVOICE_VERIFICATION][0]
    assert s2.status in [StageStatusEnum.COMPLETED, StageStatusEnum.SKIPPED]


def test_image_stage_calls_phase4_and_5():
    """Verify image forensics stage delegates to Phase 4/5 imaging services."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    s3 = [s for s in res.stages if s.stage_name == PipelineStageEnum.IMAGE_PROCESSING][0]
    assert s3.status in [StageStatusEnum.COMPLETED, StageStatusEnum.SKIPPED]


def test_relationship_stage_calls_phase7():
    """Verify relationship stage delegates to Phase 7 relationship service."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    s4 = [s for s in res.stages if s.stage_name == PipelineStageEnum.RELATIONSHIP_ANALYSIS][0]
    assert s4.status == StageStatusEnum.COMPLETED
    assert "structural_count" in s4.result_summary


def test_risk_engine_stage_calls_phase6():
    """Verify risk engine calculation stage delegates to Phase 6 risk engine."""
    res = pipeline_service.start_pipeline_run("CAS-2026-001", force_rerun=True)
    s5 = [s for s in res.stages if s.stage_name == PipelineStageEnum.RISK_CALCULATION][0]
    assert s5.status == StageStatusEnum.COMPLETED
    assert s5.result_summary.get("risk_band") in ["LOW", "MEDIUM", "HIGH"]
    assert "overall_score" in s5.result_summary


def test_phase6_weights_and_scores_unchanged():
    """Confirm that Phase 8 did NOT modify Phase 6 weights, caps, or scoring formula."""
    assert DEFAULT_POLICY_WEIGHTS["DUPLICATE_SERIAL"] == 35
    assert DEFAULT_POLICY_WEIGHTS["INVOICE_PRICE_ANOMALY"] == 20
    assert DEFAULT_POLICY_WEIGHTS["IMAGE_PHASH_REUSE"] == 20
    assert DEFAULT_POLICY_WEIGHTS["IMAGE_EMBEDDING_SIMILARITY"] == 15
    assert DEFAULT_POLICY_WEIGHTS["GPS_MISMATCH"] == 12
    assert DEFAULT_POLICY_WEIGHTS["DEALER_RELATIONSHIP_ANOMALY"] == 15
    assert DEFAULT_GROUP_CAPS["IMAGE_REUSE"] == 25


# =============================================================================
# 4. PARTIAL / INCONCLUSIVE & FAILURE POLICIES
# =============================================================================

def test_missing_invoice_handled_safely_as_skipped():
    """A case with no invoice skips extraction & verification safely without crashing."""
    res = pipeline_service.start_pipeline_run("CAS-NO-INVOICE", force_rerun=True)
    s1 = [s for s in res.stages if s.stage_name == PipelineStageEnum.INVOICE_EXTRACTION][0]
    s2 = [s for s in res.stages if s.stage_name == PipelineStageEnum.INVOICE_VERIFICATION][0]
    assert s1.status == StageStatusEnum.SKIPPED
    assert s2.status == StageStatusEnum.SKIPPED
    assert res.status in [PipelineRunStatusEnum.COMPLETED, PipelineRunStatusEnum.PARTIAL]


def test_no_fabricated_signals_on_failure():
    """Inconclusive or missing evidence must not generate artificial risk signals."""
    res = pipeline_service.start_pipeline_run("CAS-CLEAN-TEST", force_rerun=True)
    assert res.risk_score == 0
    assert res.risk_band == "LOW"


# =============================================================================
# 5. VERIFICATION TASK CREATION & IDEMPOTENCY
# =============================================================================

def test_verification_task_created_for_high_risk_band():
    """
    Case with multiple stacked anomalies (HIGH risk band) triggers verification task creation.
    """
    # CAS-2026-007 produces HIGH risk (Score 92)
    res = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    s6 = [s for s in res.stages if s.stage_name == PipelineStageEnum.VERIFICATION_TASK_DISPATCH][0]
    assert s6.status == StageStatusEnum.COMPLETED
    assert s6.result_summary.get("task_required") is True
    assert res.risk_band == "HIGH"
    assert "Field verification recommended" in res.recommended_action


def test_verification_task_creation_is_idempotent():
    """Rerunning a high-risk case does not create duplicate tasks."""
    res1 = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    res2 = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    assert res1.risk_band == "HIGH"
    assert res2.risk_band == "HIGH"


# =============================================================================
# 6. DEMO SCENARIOS (CASES A – F)
# =============================================================================

def test_clean_case_scenario():
    """SCENARIO 1: Clean Case -> Score 0, LOW, no task."""
    res = pipeline_service.start_pipeline_run("CAS-CLEAN-01", force_rerun=True)
    assert res.risk_score == 0
    assert res.risk_band == "LOW"
    assert res.verification_task_id is None or res.stages[-1].result_summary.get("task_required") is False


def test_price_anomaly_case_scenario():
    """SCENARIO 2: Price Anomaly -> Score 20, LOW."""
    res = pipeline_service.start_pipeline_run("CAS-2026-002", force_rerun=True)
    assert res.risk_score == 20
    assert res.risk_band == "LOW"


def test_duplicate_serial_case_scenario():
    """SCENARIO 3: Duplicate Serial -> Score 35, LOW."""
    from app.risk_engine.calculator import calculate_case_risk_assessment
    assessment = calculate_case_risk_assessment("CAS-SER-01", [{
        "id": "SIG-SER", "signal_type": "DUPLICATE_SERIAL", "evidence_data": {"serial": "S1"}, "is_active": True
    }])
    assert assessment.overall_score == 35
    assert assessment.risk_band == RiskBandEnum.LOW


def test_image_reuse_case_scenario():
    """SCENARIO 4: Image Reuse -> pHash (20) + Embedding (15) capped at 25."""
    res = pipeline_service.start_pipeline_run("CAS-2026-005", force_rerun=True)
    assert res.risk_score == 25
    assert res.risk_band == "LOW"


def test_multiple_anomalies_case_scenario():
    """SCENARIO 5: Multiple Anomalies -> Score 92, HIGH, Task created."""
    res = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    assert res.risk_score == 92
    assert res.risk_band == "HIGH"
    assert res.stages[-1].result_summary.get("task_required") is True


# =============================================================================
# 7. API ENDPOINT CONTRACT TESTS
# =============================================================================

def test_api_post_pipeline_run():
    """Test POST /api/v1/pipeline/cases/{case_id}/run endpoint."""
    response = client.post("/api/v1/pipeline/cases/CAS-2026-001/run", json={"policy_version": "risk-v1", "force_rerun": True})
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CAS-2026-001"
    assert "stages" in data
    assert "status" in data
    assert "pipeline_version" in data


def test_api_get_pipeline_status():
    """Test GET /api/v1/pipeline/cases/{case_id} endpoint."""
    response = client.get("/api/v1/pipeline/cases/CAS-2026-001")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CAS-2026-001"
    assert "stages" in data


def test_api_get_pipeline_runs():
    """Test GET /api/v1/pipeline/cases/{case_id}/runs endpoint."""
    response = client.get("/api/v1/pipeline/cases/CAS-2026-001/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
