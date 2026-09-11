from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class PipelineRunStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class PipelineStageEnum(str, Enum):
    INVOICE_EXTRACTION = "INVOICE_EXTRACTION"
    INVOICE_VERIFICATION = "INVOICE_VERIFICATION"
    IMAGE_PROCESSING = "IMAGE_PROCESSING"
    RELATIONSHIP_ANALYSIS = "RELATIONSHIP_ANALYSIS"
    RISK_CALCULATION = "RISK_CALCULATION"
    VERIFICATION_TASK_DISPATCH = "VERIFICATION_TASK_DISPATCH"


class StageStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAILED = "FAILED"


class PipelineStageItem(BaseModel):
    id: str
    stage_name: PipelineStageEnum
    status: StageStatusEnum = StageStatusEnum.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    result_summary: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class PipelineRunRecord(BaseModel):
    id: str
    case_id: str
    status: PipelineRunStatusEnum = PipelineRunStatusEnum.QUEUED
    current_stage: Optional[str] = None
    pipeline_version: str = "pipeline-v1"
    stages: List[PipelineStageItem] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PipelineRunRequest(BaseModel):
    policy_version: str = "risk-v1"
    force_rerun: bool = False


class PipelineStatusResponse(BaseModel):
    case_id: str
    run_id: Optional[str] = None
    status: PipelineRunStatusEnum
    current_stage: Optional[str] = None
    pipeline_version: str = "pipeline-v1"
    stages: List[PipelineStageItem] = Field(default_factory=list)
    risk_score: Optional[int] = None
    risk_band: Optional[str] = None
    recommended_action: Optional[str] = None
    verification_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0
    message: str = ""
