import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.risk_engine.models import RiskAssessmentResult, ScoreComponentItem
from app.risk_engine.service import risk_engine_service
from app.schemas.common import RiskSignalResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Risk Engine"])


class CalculateRiskRequest(BaseModel):
    policy_version: Optional[str] = "risk-v1"
    actor_id: Optional[str] = None


# =============================================================================
# EXPLAINABLE DETERMINISTIC RISK ENGINE ENDPOINTS (PHASE 6)
# =============================================================================

@router.post("/risk/cases/{case_id}/calculate", response_model=RiskAssessmentResult)
@router.post("/risk-score/{case_id}/calculate", response_model=RiskAssessmentResult)
async def calculate_case_risk_endpoint(
    case_id: str,
    request: Optional[CalculateRiskRequest] = None
):
    """
    Executes explainable deterministic risk scoring for a case:
    1. Collects active verification risk signals from invoices, image forensics, and deep embeddings
    2. Deduplicates repeated observations of the same underlying evidence
    3. Groups signals and applies anti-double-counting group caps (e.g., IMAGE_REUSE_GROUP_MAX = 25)
    4. Computes deterministic score in [0, 100] and maps to categorical risk band (LOW / MEDIUM / HIGH)
    5. Returns full traceable breakdown with underlying evidence and workflow recommendation
    Runs 100% server-side with zero external APIs, zero LLM calls, and zero fraud probabilities.
    """
    policy_ver = request.policy_version if request and request.policy_version else "risk-v1"
    actor = request.actor_id if request else None

    assessment = risk_engine_service.calculate_and_persist_assessment(
        case_id=case_id,
        policy_version=policy_ver,
        actor_id=actor
    )
    return assessment


@router.get("/risk/cases/{case_id}", response_model=RiskAssessmentResult)
@router.get("/risk-score/{case_id}", response_model=RiskAssessmentResult)
async def get_case_risk_assessment_endpoint(case_id: str):
    """
    Retrieves the latest explainable deterministic risk assessment for a case.
    """
    assessment = risk_engine_service.get_case_assessment(case_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk assessment for case #{case_id} not found."
        )
    return assessment


@router.get("/risk/cases/{case_id}/history", response_model=List[RiskAssessmentResult])
@router.get("/risk-score/{case_id}/history", response_model=List[RiskAssessmentResult])
async def get_case_risk_history_endpoint(case_id: str):
    """
    Retrieves policy-versioned historical risk assessments for a case.
    """
    return risk_engine_service.get_case_assessment_history(case_id)


@router.get("/risk-signals/{case_id}")
@router.get("/risk/cases/{case_id}/signals")
async def get_case_risk_signals_endpoint(case_id: str):
    """
    Retrieve all raw and active deterministic risk signals for a case.
    """
    signals = risk_engine_service.collect_case_signals(case_id)
    return {
        "case_id": case_id,
        "total_signals": len(signals),
        "signals": signals
    }
