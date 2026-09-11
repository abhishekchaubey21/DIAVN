from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    REQUIRES_VERIFICATION = "requires_verification"
    UNKNOWN = "unknown"


class CaseStatusEnum(str, Enum):
    SUBMITTED = "submitted"
    VERIFICATION_PENDING = "verification_pending"
    UNDER_REVIEW = "under_review"
    FLAGGED = "flagged"
    VERIFIED = "verified"
    REJECTED = "rejected"


class CaseBase(BaseModel):
    dealer_id: str
    customer_id: str
    asset_type: str
    claimed_installation_address: str
    loan_amount: Optional[float] = None
    notes: Optional[str] = None


class CaseCreate(CaseBase):
    invoice_file_name: Optional[str] = None
    installation_image_file_name: Optional[str] = None


class CaseResponse(CaseBase):
    id: str
    case_number: str
    status: CaseStatusEnum = CaseStatusEnum.SUBMITTED
    risk_level: RiskLevelEnum = RiskLevelEnum.UNKNOWN
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseResponse):
    dealer_name: Optional[str] = None
    customer_name: Optional[str] = None
    invoices: List[Dict[str, Any]] = []
    installation_images: List[Dict[str, Any]] = []
    risk_signals: List[Dict[str, Any]] = []
    risk_score: Optional[Dict[str, Any]] = None
    verification_tasks: List[Dict[str, Any]] = []
