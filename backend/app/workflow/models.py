from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class WorkflowEventTypeEnum(str, Enum):
    CASE_VERIFICATION_COMPLETED = "CASE_VERIFICATION_COMPLETED"
    CASE_VERIFICATION_HIGH_RISK = "CASE_VERIFICATION_HIGH_RISK"
    VERIFICATION_TASK_CREATED = "VERIFICATION_TASK_CREATED"
    CASE_VERIFICATION_PARTIAL = "CASE_VERIFICATION_PARTIAL"
    CASE_VERIFICATION_FAILED = "CASE_VERIFICATION_FAILED"


class WorkflowEventStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"


class WorkflowEventPayload(BaseModel):
    """
    Standardized payload for DIAVN workflow events.
    Strictly excludes raw PII (unmasked phone/email/passwords/image binaries).
    """
    event_id: str = Field(..., description="Unique deterministic identifier of the event")
    event_type: WorkflowEventTypeEnum = Field(..., description="Taxonomic classification of event")
    event_version: str = Field(default="event-v1", description="Event schema version")
    case_id: str = Field(..., description="Internal UUID of the verification case")
    case_number: str = Field(..., description="Human-readable case identifier (e.g. CAS-2026-007)")
    pipeline_run_id: Optional[str] = Field(None, description="UUID of pipeline execution run")
    risk_score: int = Field(..., ge=0, le=100, description="Authoritative 0-100 deterministic risk score from Phase 6")
    risk_band: str = Field(..., description="LOW, MEDIUM, or HIGH risk classification")
    recommended_action: str = Field(..., description="Policy-compliant recommended operational action")
    top_anomalies: List[str] = Field(default_factory=list, description="Descriptions of top anomalies from Phase 6")
    verification_task_id: Optional[str] = Field(None, description="ID of associated physical verification task if created")
    case_url: str = Field(..., description="Direct operational link to DIAVN case review page")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO UTC timestamp")


class WorkflowEventRecord(BaseModel):
    """
    Database representation of a workflow event outbox item.
    """
    id: str
    event_id: str
    event_type: WorkflowEventTypeEnum
    event_version: str = "event-v1"
    case_id: str
    pipeline_run_id: Optional[str] = None
    payload: Dict[str, Any]
    status: WorkflowEventStatusEnum
    attempt_count: int = 0
    max_attempts: int = 3
    next_attempt_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    locked_by: Optional[str] = None
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime


class WorkflowEventListResponse(BaseModel):
    case_id: str
    events: List[WorkflowEventRecord]
    total_count: int


class DeliveryResult(BaseModel):
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    is_duplicate: bool = False
