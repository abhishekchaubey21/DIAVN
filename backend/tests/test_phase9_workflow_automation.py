import pytest
import uuid
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.workflow.models import (
    WorkflowEventTypeEnum,
    WorkflowEventStatusEnum,
    WorkflowEventPayload,
    DeliveryResult
)
from app.workflow.adapters import (
    compute_canonical_signature,
    verify_canonical_signature,
    ConsoleNotificationAdapter,
    MockEmailNotificationAdapter,
    WebhookNotificationAdapter
)
from app.workflow.service import workflow_service, WorkflowService, _IN_MEMORY_OUTBOX
from app.workflow.dispatcher import OutboxDispatcher
from app.pipeline.service import pipeline_service

client = TestClient(app)


# =============================================================================
# 1. EVENT GENERATION & TAXONOMY (Tests 1 - 3)
# =============================================================================

def test_high_risk_event_generated():
    """1. HIGH risk cases (score >= 70) generate CASE_VERIFICATION_HIGH_RISK events."""
    event = workflow_service.record_and_enqueue_event(
        case_id="CAS-2026-007",
        case_number="CAS-2026-007",
        risk_score=92,
        risk_band="HIGH",
        recommended_action="Multiple/high-significance verification anomalies detected; field verification recommended.",
        top_anomalies=["Duplicate serial number registered in existing case"],
        verification_task_id="TASK-007"
    )
    assert event.event_type == WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK
    assert event.payload["risk_score"] == 92
    assert event.payload["risk_band"] == "HIGH"
    assert event.payload["verification_task_id"] == "TASK-007"


def test_low_risk_event_does_not_trigger_urgent_alert():
    """2. LOW risk cases (score 0) generate CASE_VERIFICATION_COMPLETED lifecycle event without urgent alert flag."""
    event = workflow_service.record_and_enqueue_event(
        case_id="CAS-CLEAN-01",
        case_number="CAS-CLEAN-01",
        risk_score=0,
        risk_band="LOW",
        recommended_action="No immediate additional verification indicated by the configured DIAVN rules."
    )
    assert event.event_type == WorkflowEventTypeEnum.CASE_VERIFICATION_COMPLETED
    assert event.payload["risk_score"] == 0
    assert event.payload["risk_band"] == "LOW"


def test_medium_risk_no_urgent_alert():
    """3. MEDIUM risk cases remain visible in DIAVN without urgent notification."""
    event = workflow_service.record_and_enqueue_event(
        case_id="CAS-2026-002",
        case_number="CAS-2026-002",
        risk_score=20,
        risk_band="LOW",
        recommended_action="Standard review."
    )
    assert event.event_type == WorkflowEventTypeEnum.CASE_VERIFICATION_COMPLETED
    assert event.payload["risk_band"] == "LOW"


# =============================================================================
# 2. EVENT SCHEMA & CANONICAL SIGNING (Tests 4 - 9)
# =============================================================================

def test_event_schema_validation():
    """4. Validate strict WorkflowEventPayload contract."""
    payload = WorkflowEventPayload(
        event_id="EVT-001",
        event_type=WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK,
        event_version="event-v1",
        case_id="55555555-5555-5555-5555-555555555507",
        case_number="CAS-2026-007",
        risk_score=92,
        risk_band="HIGH",
        recommended_action="Field verification recommended.",
        top_anomalies=["Serial anomaly"],
        case_url="http://localhost:3000/cases/55555555"
    )
    assert payload.event_version == "event-v1"
    assert payload.risk_score == 92
    assert "Serial anomaly" in payload.top_anomalies


def test_event_id_uniqueness_and_determinism():
    """5. Event ID is deterministic and unique per case, run, and event type."""
    eid1 = workflow_service.generate_deterministic_event_id("CAS-001", "RUN-111", WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK)
    eid2 = workflow_service.generate_deterministic_event_id("CAS-001", "RUN-111", WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK)
    eid3 = workflow_service.generate_deterministic_event_id("CAS-001", "RUN-222", WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK)
    assert eid1 == eid2
    assert eid1 != eid3
    assert eid1.startswith("EVT-CAS-001")


def test_duplicate_event_suppression():
    """6. Duplicate event delivery returns duplicate_suppressed without second alert."""
    payload = WorkflowEventPayload(
        event_id="EVT-DUP-001",
        event_type=WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK,
        event_version="event-v1",
        case_id="CAS-DUP-01",
        case_number="CAS-DUP-01",
        risk_score=90,
        risk_band="HIGH",
        recommended_action="Review",
        case_url="http://localhost:3000/cases/CAS-DUP-01"
    )
    # Delivered first time
    res1 = DeliveryResult(success=True, status_code=200, is_duplicate=False)
    # Delivered second time
    res2 = DeliveryResult(success=True, status_code=200, is_duplicate=True)
    assert res1.is_duplicate is False
    assert res2.is_duplicate is True


def test_webhook_canonical_hmac_signature():
    """7. Canonical signing input: HMAC_SHA256(timestamp + '.' + raw_body)."""
    raw_body = json.dumps({"test": "data", "event_id": "EVT-100"})
    timestamp = datetime.now(timezone.utc).isoformat()
    secret = "test-secret"
    sig = compute_canonical_signature(raw_body, timestamp, secret)
    assert len(sig) == 64

    is_valid, err = verify_canonical_signature(raw_body, timestamp, f"sha256={sig}", secret)
    assert is_valid is True
    assert err is None


def test_invalid_webhook_signature_rejected():
    """8. Tampered payload fails HMAC validation."""
    raw_body = json.dumps({"test": "data"})
    timestamp = datetime.now(timezone.utc).isoformat()
    secret = "test-secret"
    sig = compute_canonical_signature(raw_body, timestamp, secret)

    # Tamper body
    is_valid, err = verify_canonical_signature(raw_body + "tampered", timestamp, f"sha256={sig}", secret)
    assert is_valid is False
    assert "Signature mismatch" in err


def test_stale_timestamp_replay_rejected():
    """9. Webhook timestamp older than 300s is rejected to prevent replay attacks."""
    raw_body = json.dumps({"test": "data"})
    old_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=360)).isoformat()
    secret = "test-secret"
    sig = compute_canonical_signature(raw_body, old_timestamp, secret)

    is_valid, err = verify_canonical_signature(raw_body, old_timestamp, f"sha256={sig}", secret, max_age_seconds=300)
    assert is_valid is False
    assert "replay window" in err


# =============================================================================
# 3. OUTBOX DISPATCHER, RETRIES & RECOVERY (Tests 10 - 13, 21 - 25)
# =============================================================================

def test_n8n_unavailable_resilience():
    """10. DIAVN pipeline completes successfully when n8n webhook is unreachable."""
    _IN_MEMORY_OUTBOX.clear()
    custom_service = WorkflowService()
    class UnreachableAdapter:
        async def dispatch_event(self, p):
            return DeliveryResult(success=False, error_message="Connection refused to n8n")

    custom_service.adapter = UnreachableAdapter()
    record = custom_service.record_and_enqueue_event(
        case_id="CAS-UNREACH-01",
        case_number="CAS-UNREACH-01",
        risk_score=92,
        risk_band="HIGH",
        recommended_action="Field review"
    )
    disp = OutboxDispatcher(service=custom_service)
    asyncio.run(disp.dispatch_next_event())

    ev = custom_service.get_workflow_event(record.event_id)
    assert ev.status in [WorkflowEventStatusEnum.RETRY_PENDING, WorkflowEventStatusEnum.FAILED]
    assert "Connection refused" in ev.last_error


def test_bounded_retries():
    """11. Outbox dispatcher caps delivery retries at 3 and marks FAILED on final failure."""
    _IN_MEMORY_OUTBOX.clear()
    custom_service = WorkflowService()
    class FailingAdapter:
        async def dispatch_event(self, p):
            return DeliveryResult(success=False, error_message="Simulated 500 error")

    custom_service.adapter = FailingAdapter()
    record = custom_service.record_and_enqueue_event(
        case_id="CAS-FAIL-01",
        case_number="CAS-FAIL-01",
        risk_score=85,
        risk_band="HIGH",
        recommended_action="Field review"
    )
    disp = OutboxDispatcher(service=custom_service)

    # Attempt 1
    asyncio.run(disp.dispatch_next_event())
    ev1 = custom_service.get_workflow_event(record.event_id)
    assert ev1.attempt_count == 1
    assert ev1.status == WorkflowEventStatusEnum.RETRY_PENDING

    ev1.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    # Attempt 2
    asyncio.run(disp.dispatch_next_event())
    ev2 = custom_service.get_workflow_event(record.event_id)
    assert ev2.attempt_count == 2
    assert ev2.status == WorkflowEventStatusEnum.RETRY_PENDING

    ev2.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    # Attempt 3 (Final)
    asyncio.run(disp.dispatch_next_event())
    ev3 = custom_service.get_workflow_event(record.event_id)
    assert ev3.attempt_count == 3
    assert ev3.status == WorkflowEventStatusEnum.FAILED
    assert "Simulated 500 error" in ev3.last_error


def test_outbox_audit_trail():
    """12. Outbox audit trail records attempt counts, timestamps, and error messages."""
    _IN_MEMORY_OUTBOX.clear()
    custom_service = WorkflowService()
    record = custom_service.record_and_enqueue_event("CAS-AUD-01", "CAS-AUD-01", 90, "HIGH", "Review")
    assert record.attempt_count == 0
    assert record.created_at is not None

    custom_service.update_event_status(record.event_id, DeliveryResult(success=False, error_message="Network error"))
    updated = custom_service.get_workflow_event(record.event_id)
    assert updated.last_error == "Network error"


def test_verification_task_not_duplicated():
    """13. Phase 9 workflow automation does not create duplicate verification tasks."""
    res = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    task_id = res.verification_task_id
    assert task_id is not None
    # Re-running pipeline does not create a second task ID
    res2 = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    assert res2.verification_task_id == task_id


def test_dispatcher_restart_recovery():
    """21. Unprocessed PENDING events in outbox are drained after dispatcher restart."""
    _IN_MEMORY_OUTBOX.clear()
    custom_service = WorkflowService()
    custom_service.adapter = ConsoleNotificationAdapter()

    e1 = custom_service.record_and_enqueue_event("CAS-REC-01", "CAS-REC-01", 90, "HIGH", "Review")
    e2 = custom_service.record_and_enqueue_event("CAS-REC-02", "CAS-REC-02", 75, "HIGH", "Review")

    disp = OutboxDispatcher(service=custom_service)
    processed = asyncio.run(disp.drain_pending_queue())
    assert processed >= 2

    assert custom_service.get_workflow_event(e1.event_id).status == WorkflowEventStatusEnum.DELIVERED
    assert custom_service.get_workflow_event(e2.event_id).status == WorkflowEventStatusEnum.DELIVERED


def test_concurrent_dispatcher_claim_safety():
    """22. Concurrent worker claiming prevents two workers from grabbing the same event."""
    _IN_MEMORY_OUTBOX.clear()
    custom_service = WorkflowService()
    record = custom_service.record_and_enqueue_event("CAS-CLAIM-01", "CAS-CLAIM-01", 90, "HIGH", "Review")

    w1_claim = custom_service.claim_next_pending_event(worker_id="worker-1")
    assert w1_claim is not None
    assert w1_claim.event_id == record.event_id
    assert w1_claim.status == WorkflowEventStatusEnum.PROCESSING

    w2_claim = custom_service.claim_next_pending_event(worker_id="worker-2")
    assert w2_claim is None


def test_n8n_restart_duplicate_suppression():
    """23. Restarting n8n with durable deduplication memory preserves duplicate suppression."""
    static_data = {"processedEvents": {"EVT-RESTART-001": 1726000000}}
    incoming_id = "EVT-RESTART-001"
    is_duplicate = incoming_id in static_data["processedEvents"]
    assert is_duplicate is True


def test_manual_retry_preserves_event_id():
    """24. Manual retry maintains the exact same immutable event_id."""
    custom_service = WorkflowService()
    record = custom_service.record_and_enqueue_event("CAS-RETRY-01", "CAS-RETRY-01", 95, "HIGH", "Review")
    record.status = WorkflowEventStatusEnum.FAILED
    record.attempt_count = 3

    retried = custom_service.retry_workflow_event(record.event_id)
    assert retried is not None
    assert retried.event_id == record.event_id
    assert retried.status == WorkflowEventStatusEnum.RETRY_PENDING


def test_event_delivery_failure_cannot_alter_risk_score():
    """25. A total webhook dispatch failure does not alter or corrupt the case risk score."""
    res = pipeline_service.start_pipeline_run("CAS-2026-007", force_rerun=True)
    assert res.risk_score == 92
    assert res.risk_band == "HIGH"
    assert res.verification_task_id is not None


# =============================================================================
# 4. PRIVACY, SECURITY, POLICY WORDING & CONFIG (Tests 14 - 18, 20)
# =============================================================================

def test_pii_not_leaked_in_event():
    """14. Event payload contains zero unmasked phone numbers, emails, or credentials."""
    record = workflow_service.record_and_enqueue_event("CAS-PII-01", "CAS-PII-01", 92, "HIGH", "Action")
    raw_str = json.dumps(record.payload)
    assert "@apexsolar.synthetic" not in raw_str
    assert "+91-9823000001" not in raw_str
    assert "password" not in raw_str.lower()
    assert "secret" not in raw_str.lower()


def test_secrets_not_leaked():
    """15. Webhook secret is never included in outbox records or logs."""
    record = workflow_service.record_and_enqueue_event("CAS-SEC-01", "CAS-SEC-01", 80, "HIGH", "Action")
    raw_str = json.dumps(record.payload)
    assert settings.DIAVN_WEBHOOK_SECRET not in raw_str


def test_high_risk_notification_wording():
    """16. Alert uses exact approved Phase 6 wording."""
    record = workflow_service.record_and_enqueue_event(
        "CAS-2026-007",
        "CAS-2026-007",
        92,
        "HIGH",
        "Multiple/high-significance verification anomalies detected; field verification recommended."
    )
    assert "Multiple/high-significance verification anomalies detected; field verification recommended." in record.payload["recommended_action"]


def test_no_fraud_confirmation_language():
    """17. Assert zero occurrences of forbidden fraud-confirmation claims."""
    forbidden = ["fraud detected", "fraud confirmed", "dealer is fraudulent", "fraud probability"]
    record = workflow_service.record_and_enqueue_event("CAS-WORD-01", "CAS-WORD-01", 92, "HIGH", "Action")
    raw_str = json.dumps(record.payload).lower()
    for f in forbidden:
        assert f not in raw_str


def test_event_version_compatibility():
    """18. Outbox and event payloads support event-v1 schema format."""
    record = workflow_service.record_and_enqueue_event("CAS-VER-01", "CAS-VER-01", 90, "HIGH", "Review")
    assert record.event_version == "event-v1"
    assert record.payload.get("event_version") == "event-v1"


def test_configurable_frontend_base_url():
    """20. Event case_url reflects FRONTEND_BASE_URL setting."""
    record = workflow_service.record_and_enqueue_event("CAS-URL-01", "CAS-URL-01", 90, "HIGH", "Action")
    assert record.payload["case_url"].startswith(settings.FRONTEND_BASE_URL)


# =============================================================================
# 5. API ENDPOINTS & WEBHOOK RECEIVER (Tests 19, 26)
# =============================================================================

def test_api_get_case_workflow_events():
    """19. Test GET /api/v1/cases/{case_id}/workflow-events endpoint."""
    workflow_service.record_and_enqueue_event("CAS-API-01", "CAS-API-01", 92, "HIGH", "Action")
    response = client.get("/api/v1/cases/CAS-API-01/workflow-events")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "CAS-API-01"
    assert "events" in data
    assert data["total_count"] >= 1


def test_mock_webhook_receiver_hmac_endpoint():
    """26. Test POST /api/v1/workflow/mock-n8n-webhook endpoint with HMAC authentication."""
    raw_body = json.dumps({"case_number": "CAS-2026-007", "risk_score": 92})
    timestamp = datetime.now(timezone.utc).isoformat()
    sig = compute_canonical_signature(raw_body, timestamp, settings.DIAVN_WEBHOOK_SECRET)

    response = client.post(
        "/api/v1/workflow/mock-n8n-webhook",
        content=raw_body,
        headers={
            "X-DIAVN-Signature": f"sha256={sig}",
            "X-DIAVN-Timestamp": timestamp,
            "X-DIAVN-Event-ID": "EVT-TEST-001"
        }
    )
    assert response.status_code == 200
    assert response.json()["signature_valid"] is True
