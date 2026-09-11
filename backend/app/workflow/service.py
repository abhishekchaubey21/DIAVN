import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.workflow.models import (
    WorkflowEventTypeEnum,
    WorkflowEventStatusEnum,
    WorkflowEventPayload,
    WorkflowEventRecord,
    DeliveryResult
)
from app.workflow.adapters import (
    BaseNotificationAdapter,
    WebhookNotificationAdapter,
    ConsoleNotificationAdapter
)
from app.db.supabase_client import get_supabase_admin_client

logger = logging.getLogger(__name__)

# In-memory store for local testing, fallback, and unit tests
_IN_MEMORY_OUTBOX: Dict[str, WorkflowEventRecord] = {}


class WorkflowService:
    def __init__(self, adapter: Optional[BaseNotificationAdapter] = None):
        self.adapter = adapter or WebhookNotificationAdapter()
        self.worker_id = f"worker-{uuid.uuid4().hex[:8]}"

    def generate_deterministic_event_id(
        self,
        case_number: str,
        pipeline_run_id: Optional[str],
        event_type: WorkflowEventTypeEnum
    ) -> str:
        """
        Generates an immutable deterministic identifier for the event.
        Format: EVT-{case_number}-{pipeline_run_id[:8]}-{event_type_slug}
        """
        run_slug = (pipeline_run_id or "norun")[:8]
        type_slug = event_type.value.replace("CASE_VERIFICATION_", "").replace("_", "-")
        return f"EVT-{case_number}-{run_slug}-{type_slug}".upper()

    def record_and_enqueue_event(
        self,
        case_id: str,
        case_number: str,
        risk_score: int,
        risk_band: str,
        recommended_action: str,
        pipeline_run_id: Optional[str] = None,
        top_anomalies: Optional[List[str]] = None,
        verification_task_id: Optional[str] = None,
        event_type: Optional[WorkflowEventTypeEnum] = None
    ) -> WorkflowEventRecord:
        """
        Persists a workflow event into the outbox.
        Determines appropriate event type based on risk band if not specified.
        """
        if event_type is None:
            if risk_band.upper() == "HIGH" or risk_score >= 70:
                event_type = WorkflowEventTypeEnum.CASE_VERIFICATION_HIGH_RISK
            else:
                event_type = WorkflowEventTypeEnum.CASE_VERIFICATION_COMPLETED

        event_id = self.generate_deterministic_event_id(case_number, pipeline_run_id, event_type)
        now = datetime.now(timezone.utc)
        case_url = f"{settings.FRONTEND_BASE_URL}/cases/{case_id}"

        payload = WorkflowEventPayload(
            event_id=event_id,
            event_type=event_type,
            event_version="event-v1",
            case_id=case_id,
            case_number=case_number,
            pipeline_run_id=pipeline_run_id,
            risk_score=risk_score,
            risk_band=risk_band.upper(),
            recommended_action=recommended_action,
            top_anomalies=top_anomalies or [],
            verification_task_id=verification_task_id,
            case_url=case_url,
            timestamp=now.isoformat()
        )

        record = WorkflowEventRecord(
            id=str(uuid.uuid4()),
            event_id=event_id,
            event_type=event_type,
            event_version="event-v1",
            case_id=case_id,
            pipeline_run_id=pipeline_run_id,
            payload=payload.model_dump(),
            status=WorkflowEventStatusEnum.PENDING,
            attempt_count=0,
            max_attempts=settings.WORKFLOW_MAX_RETRIES,
            next_attempt_at=now,
            created_at=now
        )

        # 1. Persist to database outbox if available
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                # Upsert to respect database unique event_id constraint
                admin_client.table("workflow_events").upsert({
                    "id": record.id,
                    "event_id": record.event_id,
                    "event_type": record.event_type.value,
                    "event_version": record.event_version,
                    "case_id": record.case_id,
                    "pipeline_run_id": record.pipeline_run_id,
                    "payload": record.payload,
                    "status": record.status.value,
                    "attempt_count": record.attempt_count,
                    "max_attempts": record.max_attempts,
                    "next_attempt_at": record.next_attempt_at.isoformat() if record.next_attempt_at else None,
                    "created_at": record.created_at.isoformat()
                }, on_conflict="event_id").execute()
            except Exception as e:
                logger.debug(f"Database outbox upsert note: {e}")

        # 2. Update in-memory fallback store
        _IN_MEMORY_OUTBOX[event_id] = record
        logger.info(f"Recorded workflow event {event_id} ({event_type.value}) for case {case_number}")
        return record

    def claim_next_pending_event(self, worker_id: Optional[str] = None) -> Optional[WorkflowEventRecord]:
        """
        Atomically claims a single PENDING or RETRY_PENDING event for delivery.
        Prevents multiple workers from dispatching the same event concurrently.
        """
        w_id = worker_id or self.worker_id
        now = datetime.now(timezone.utc)
        lock_timeout = now - timedelta(seconds=60)

        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                # Find eligible event
                res = admin_client.table("workflow_events").select("*") \
                    .in_("status", ["PENDING", "RETRY_PENDING"]) \
                    .lte("next_attempt_at", now.isoformat()) \
                    .order("created_at", desc=False) \
                    .limit(1) \
                    .execute()

                if res and res.data:
                    ev_data = res.data[0]
                    ev_id = ev_data["id"]

                    # Atomic claim transition
                    claim_res = admin_client.table("workflow_events").update({
                        "status": "PROCESSING",
                        "locked_at": now.isoformat(),
                        "locked_by": w_id,
                        "attempt_count": ev_data.get("attempt_count", 0) + 1,
                        "last_attempt_at": now.isoformat()
                    }).eq("id", ev_id).in_("status", ["PENDING", "RETRY_PENDING"]).execute()

                    if claim_res and claim_res.data:
                        d = claim_res.data[0]
                        return WorkflowEventRecord(
                            id=d["id"],
                            event_id=d["event_id"],
                            event_type=WorkflowEventTypeEnum(d["event_type"]),
                            event_version=d.get("event_version", "event-v1"),
                            case_id=d["case_id"],
                            pipeline_run_id=d.get("pipeline_run_id"),
                            payload=d["payload"],
                            status=WorkflowEventStatusEnum(d["status"]),
                            attempt_count=d.get("attempt_count", 1),
                            max_attempts=d.get("max_attempts", 3),
                            next_attempt_at=datetime.fromisoformat(d["next_attempt_at"]) if d.get("next_attempt_at") else None,
                            locked_at=datetime.fromisoformat(d["locked_at"]) if d.get("locked_at") else None,
                            locked_by=d.get("locked_by"),
                            last_attempt_at=datetime.fromisoformat(d["last_attempt_at"]) if d.get("last_attempt_at") else None,
                            created_at=datetime.fromisoformat(d["created_at"])
                        )
            except Exception as e:
                logger.debug(f"Database claim attempt note: {e}")

        # In-memory claim fallback for local/unit testing
        for ev_id, ev in _IN_MEMORY_OUTBOX.items():
            if ev.status in [WorkflowEventStatusEnum.PENDING, WorkflowEventStatusEnum.RETRY_PENDING]:
                if ev.next_attempt_at is None or ev.next_attempt_at <= now:
                    if ev.locked_at is None or ev.locked_at < lock_timeout:
                        ev.status = WorkflowEventStatusEnum.PROCESSING
                        ev.locked_at = now
                        ev.locked_by = w_id
                        ev.attempt_count += 1
                        ev.last_attempt_at = now
                        return ev
        return None

    def update_event_status(
        self,
        event_id: str,
        result: DeliveryResult
    ) -> WorkflowEventRecord:
        """
        Updates the event state after a delivery attempt, implementing bounded exponential backoff.
        """
        now = datetime.now(timezone.utc)
        record = self.get_workflow_event(event_id)
        if not record:
            raise ValueError(f"Workflow event #{event_id} not found.")

        if result.success:
            record.status = WorkflowEventStatusEnum.DELIVERED
            record.last_error = None
            record.processed_at = now
            record.locked_at = None
            record.locked_by = None
        else:
            record.last_error = result.error_message
            if record.attempt_count >= record.max_attempts:
                record.status = WorkflowEventStatusEnum.FAILED
                record.processed_at = now
                record.locked_at = None
                record.locked_by = None
            else:
                record.status = WorkflowEventStatusEnum.RETRY_PENDING
                # Exponential backoff: attempt 1 -> +30s, attempt 2 -> +120s
                delay_sec = 30 if record.attempt_count == 1 else 120
                record.next_attempt_at = now + timedelta(seconds=delay_sec)
                record.locked_at = None
                record.locked_by = None

        # Database update
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                admin_client.table("workflow_events").update({
                    "status": record.status.value,
                    "attempt_count": record.attempt_count,
                    "next_attempt_at": record.next_attempt_at.isoformat() if record.next_attempt_at else None,
                    "last_attempt_at": record.last_attempt_at.isoformat() if record.last_attempt_at else None,
                    "last_error": record.last_error,
                    "processed_at": record.processed_at.isoformat() if record.processed_at else None,
                    "locked_at": None,
                    "locked_by": None
                }).eq("event_id", event_id).execute()
            except Exception as e:
                logger.debug(f"Database status update note: {e}")

        _IN_MEMORY_OUTBOX[event_id] = record
        return record

    def get_workflow_event(self, event_id: str) -> Optional[WorkflowEventRecord]:
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.table("workflow_events").select("*").eq("event_id", event_id).execute()
                if res and res.data:
                    d = res.data[0]
                    return WorkflowEventRecord(
                        id=d["id"],
                        event_id=d["event_id"],
                        event_type=WorkflowEventTypeEnum(d["event_type"]),
                        event_version=d.get("event_version", "event-v1"),
                        case_id=d["case_id"],
                        pipeline_run_id=d.get("pipeline_run_id"),
                        payload=d["payload"],
                        status=WorkflowEventStatusEnum(d["status"]),
                        attempt_count=d.get("attempt_count", 0),
                        max_attempts=d.get("max_attempts", 3),
                        next_attempt_at=datetime.fromisoformat(d["next_attempt_at"]) if d.get("next_attempt_at") else None,
                        locked_at=datetime.fromisoformat(d["locked_at"]) if d.get("locked_at") else None,
                        locked_by=d.get("locked_by"),
                        last_attempt_at=datetime.fromisoformat(d["last_attempt_at"]) if d.get("last_attempt_at") else None,
                        last_error=d.get("last_error"),
                        processed_at=datetime.fromisoformat(d["processed_at"]) if d.get("processed_at") else None,
                        created_at=datetime.fromisoformat(d["created_at"])
                    )
            except Exception as e:
                logger.debug(f"Database get note: {e}")

        return _IN_MEMORY_OUTBOX.get(event_id)

    def list_case_workflow_events(self, case_id: str) -> List[WorkflowEventRecord]:
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.table("workflow_events").select("*").eq("case_id", case_id).order("created_at", desc=True).execute()
                if res and res.data:
                    return [
                        WorkflowEventRecord(
                            id=d["id"],
                            event_id=d["event_id"],
                            event_type=WorkflowEventTypeEnum(d["event_type"]),
                            event_version=d.get("event_version", "event-v1"),
                            case_id=d["case_id"],
                            pipeline_run_id=d.get("pipeline_run_id"),
                            payload=d["payload"],
                            status=WorkflowEventStatusEnum(d["status"]),
                            attempt_count=d.get("attempt_count", 0),
                            max_attempts=d.get("max_attempts", 3),
                            next_attempt_at=datetime.fromisoformat(d["next_attempt_at"]) if d.get("next_attempt_at") else None,
                            locked_at=datetime.fromisoformat(d["locked_at"]) if d.get("locked_at") else None,
                            locked_by=d.get("locked_by"),
                            last_attempt_at=datetime.fromisoformat(d["last_attempt_at"]) if d.get("last_attempt_at") else None,
                            last_error=d.get("last_error"),
                            processed_at=datetime.fromisoformat(d["processed_at"]) if d.get("processed_at") else None,
                            created_at=datetime.fromisoformat(d["created_at"])
                        )
                        for d in res.data
                    ]
            except Exception as e:
                logger.debug(f"Database list note: {e}")

        return [e for e in _IN_MEMORY_OUTBOX.values() if e.case_id == case_id]

    def retry_workflow_event(self, event_id: str) -> Optional[WorkflowEventRecord]:
        """
        Manually retries a FAILED or RETRY_PENDING event.
        Guarantees that the exact same event_id is preserved and complete attempt history is maintained.
        """
        record = self.get_workflow_event(event_id)
        if not record:
            return None

        record.status = WorkflowEventStatusEnum.RETRY_PENDING
        record.next_attempt_at = datetime.now(timezone.utc)
        record.locked_at = None
        record.locked_by = None

        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                admin_client.table("workflow_events").update({
                    "status": "RETRY_PENDING",
                    "next_attempt_at": record.next_attempt_at.isoformat(),
                    "locked_at": None,
                    "locked_by": None
                }).eq("event_id", event_id).execute()
            except Exception as e:
                logger.debug(f"Database retry note: {e}")

        _IN_MEMORY_OUTBOX[event_id] = record
        return record


workflow_service = WorkflowService()
