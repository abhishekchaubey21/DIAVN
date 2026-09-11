from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RiskBandEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EvidenceGroupEnum(str, Enum):
    SERIAL = "SERIAL"
    INVOICE_PRICE = "INVOICE_PRICE"
    IMAGE_REUSE = "IMAGE_REUSE"
    LOCATION = "LOCATION"
    METADATA = "METADATA"
    EXTRACTION = "EXTRACTION"
    DEALER = "DEALER"
    OTHER = "OTHER"


class ScoreComponentItem(BaseModel):
    """
    Traceable explanation item for every active risk signal contributing to the score.
    """
    signal_id: Optional[str] = None
    signal_type: str = Field(..., description="Canonical signal type name")
    group: EvidenceGroupEnum = Field(..., description="Evidence group for deduplication/capping")
    source: str = Field(..., description="Pipeline stage originating the signal (e.g., invoice_verification, image_forensics, visual_embeddings)")
    severity: str = Field(..., description="Severity level: info, low, medium, high, critical")
    policy_weight: int = Field(..., description="Configured initial policy weight")
    effective_contribution: int = Field(..., description="Actual score added after applying group and total caps")
    is_group_capped: bool = Field(False, description="True if this contribution was reduced due to a group cap")
    group_cap_applied: Optional[int] = Field(None, description="Group cap value if applicable")
    description: str = Field(..., description="Human-readable explanation of why this signal was generated")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Underlying verification evidence payload")
    created_at: Optional[str] = None


class GroupContributionSummary(BaseModel):
    """
    Summary of raw vs capped contributions for an evidence group.
    """
    group: EvidenceGroupEnum
    raw_sum: int
    group_cap: int
    effective_contribution: int
    signal_count: int


class RiskAssessmentResult(BaseModel):
    """
    Comprehensive, explainable, deterministic risk assessment for a case.
    Zero external APIs. Zero fraud probabilities. 100% auditable.
    """
    id: Optional[str] = None
    case_id: str
    overall_score: int = Field(..., ge=0, le=100, description="Final deterministic verification risk score in [0, 100]")
    raw_score: int = Field(..., ge=0, description="Sum of raw uncapped policy weights before group and total caps")
    risk_band: RiskBandEnum = Field(..., description="Categorical risk band: LOW (0-39), MEDIUM (40-69), HIGH (70-100)")
    risk_level: str = Field(default="low", description="Compatibility field alias for risk_band")
    policy_version: str = Field(..., description="Version of policy weights and rules applied (e.g., risk-v1)")
    recommended_action: str = Field(..., description="Deterministic underwriting workflow recommendation")
    price_anomaly_score: int = Field(0, ge=0, le=100, description="Subcategory score for pricing anomalies")
    image_anomaly_score: int = Field(0, ge=0, le=100, description="Subcategory score for image forensics and visual reuse")
    dealer_network_score: int = Field(0, ge=0, le=100, description="Subcategory score for dealer relationship/collusion")
    serial_anomaly_score: int = Field(0, ge=0, le=100, description="Subcategory score for serial duplication")
    components: List[ScoreComponentItem] = Field(default_factory=list, description="List of all traceable risk signal contributions")
    group_contributions: Dict[str, GroupContributionSummary] = Field(default_factory=dict, description="Group-level raw vs capped breakdown")
    summary_reasoning: str = Field(..., description="Explainable deterministic summary of detected verification anomalies")
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    audit_note: str = Field(
        default="The DIAVN risk score is an explainable policy-based verification risk score, not a statistical probability of fraud.",
        description="Mandatory compliance and underwriting standard notice"
    )
