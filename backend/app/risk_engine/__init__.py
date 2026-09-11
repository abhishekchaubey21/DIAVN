"""
DIAVN: Phase 6 Explainable Deterministic Risk Engine
Deterministic, evidence-traceable risk assessment with configurable policy weights,
group capping (anti-double-counting), risk bands, and recommended underwriting actions.
Zero external APIs. Zero LLM calls. Zero fraud probability claims.
"""

from app.risk_engine.models import (
    RiskBandEnum,
    EvidenceGroupEnum,
    ScoreComponentItem,
    GroupContributionSummary,
    RiskAssessmentResult,
)
from app.risk_engine.rules import (
    POLICY_VERSION,
    DEFAULT_POLICY_WEIGHTS,
    DEFAULT_GROUP_CAPS,
    TOTAL_SCORE_CAP,
    RISK_BANDS,
    RECOMMENDED_ACTIONS,
    get_risk_band_for_score,
    get_recommended_action_for_band,
)
from app.risk_engine.grouping import (
    normalize_signal_type,
    get_signal_group,
    deduplicate_raw_signals,
    group_and_cap_signals,
)
from app.risk_engine.calculator import calculate_case_risk_assessment
from app.risk_engine.service import risk_engine_service, RiskEngineService

__all__ = [
    "RiskBandEnum",
    "EvidenceGroupEnum",
    "ScoreComponentItem",
    "GroupContributionSummary",
    "RiskAssessmentResult",
    "POLICY_VERSION",
    "DEFAULT_POLICY_WEIGHTS",
    "DEFAULT_GROUP_CAPS",
    "TOTAL_SCORE_CAP",
    "RISK_BANDS",
    "RECOMMENDED_ACTIONS",
    "get_risk_band_for_score",
    "get_recommended_action_for_band",
    "normalize_signal_type",
    "get_signal_group",
    "deduplicate_raw_signals",
    "group_and_cap_signals",
    "calculate_case_risk_assessment",
    "risk_engine_service",
    "RiskEngineService",
]
