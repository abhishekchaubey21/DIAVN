import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.risk_engine.models import (
    RiskAssessmentResult,
    ScoreComponentItem,
    GroupContributionSummary,
    RiskBandEnum,
    EvidenceGroupEnum
)
from app.risk_engine.rules import (
    POLICY_VERSION,
    DEFAULT_POLICY_WEIGHTS,
    DEFAULT_GROUP_CAPS,
    TOTAL_SCORE_CAP,
    get_risk_band_for_score,
    get_recommended_action_for_band
)
from app.risk_engine.grouping import (
    deduplicate_raw_signals,
    group_and_cap_signals,
    normalize_signal_type
)

logger = logging.getLogger(__name__)


def calculate_case_risk_assessment(
    case_id: str,
    raw_signals: List[Dict[str, Any]],
    policy_version: str = POLICY_VERSION,
    policy_weights: Optional[Dict[str, int]] = None,
    group_caps: Optional[Dict[EvidenceGroupEnum, int]] = None
) -> RiskAssessmentResult:
    """
    Pure deterministic risk calculation engine.
    Calculates case risk score in [0, 100], risk band, and evidence breakdown.
    Zero external APIs. Zero LLM calls. Zero fraud probability claims.
    """
    weights = policy_weights or DEFAULT_POLICY_WEIGHTS
    caps = group_caps or DEFAULT_GROUP_CAPS

    # 1. Filter only active, applicable anomaly signals
    active_signals: List[Dict[str, Any]] = []
    for sig in raw_signals:
        # Check active status if present
        if sig.get("is_active") is False:
            continue
            
        status = str(sig.get("status", "")).upper()
        if status in ["PASS", "INCONCLUSIVE", "NOT_CHECKED", "INFO"]:
            continue

        active_signals.append(sig)

    # 2. Deduplicate signals to prevent double-counting
    deduped_signals = deduplicate_raw_signals(active_signals)

    # 3. Group signals and apply group caps
    components, group_summaries, raw_total, capped_total = group_and_cap_signals(
        deduped_signals=deduped_signals,
        policy_weights=weights,
        group_caps=caps
    )

    # 4. Enforce overall score cap
    overall_score = min(capped_total, TOTAL_SCORE_CAP)

    # 5. Determine categorical risk band & recommended workflow action
    risk_band = get_risk_band_for_score(overall_score)
    recommended_action = get_recommended_action_for_band(risk_band)

    # 6. Calculate subcategory scores (normalized to 0-100 scale for UI gauges)
    def calc_subscore(group_enum: EvidenceGroupEnum, max_baseline: int) -> int:
        summary = group_summaries.get(group_enum.value)
        if not summary or summary.effective_contribution == 0:
            return 0
        return min(100, int((summary.effective_contribution / float(max_baseline)) * 100))

    price_subscore = calc_subscore(EvidenceGroupEnum.INVOICE_PRICE, 25)
    serial_subscore = calc_subscore(EvidenceGroupEnum.SERIAL, 35)
    image_subscore = calc_subscore(EvidenceGroupEnum.IMAGE_REUSE, 25)
    dealer_subscore = calc_subscore(EvidenceGroupEnum.DEALER, 25)

    # 7. Generate deterministic explainable summary reasoning
    if overall_score == 0:
        summary_reasoning = (
            f"No active verification anomalies detected under policy '{policy_version}'. "
            f"Baseline evidence-based verification risk is LOW (0/100). "
            f"{recommended_action}"
        )
    else:
        active_reasons = []
        for comp in components:
            if comp.effective_contribution > 0:
                cap_note = f" (capped from +{comp.policy_weight})" if comp.is_group_capped else ""
                active_reasons.append(f"+{comp.effective_contribution} {comp.signal_type.replace('_', ' ').title()}{cap_note}")

        summary_reasoning = (
            f"Deterministic verification assessment ({policy_version}): "
            f"Overall score {overall_score}/100 [{risk_band.value}]. "
            f"Active risk contributions: {', '.join(active_reasons)}. "
            f"Action: {recommended_action}"
        )

    result = RiskAssessmentResult(
        id=f"RSK-{case_id}-{int(datetime.now(timezone.utc).timestamp())}",
        case_id=case_id,
        overall_score=overall_score,
        raw_score=raw_total,
        risk_band=risk_band,
        risk_level=risk_band.value.lower(),
        policy_version=policy_version,
        recommended_action=recommended_action,
        price_anomaly_score=price_subscore,
        image_anomaly_score=image_subscore,
        dealer_network_score=dealer_subscore,
        serial_anomaly_score=serial_subscore,
        components=components,
        group_contributions=group_summaries,
        summary_reasoning=summary_reasoning,
        calculated_at=datetime.now(timezone.utc)
    )

    logger.info(
        f"Calculated risk assessment for case #{case_id}: "
        f"score={overall_score} ({risk_band.value}), raw={raw_total}, components={len(components)}"
    )

    return result
