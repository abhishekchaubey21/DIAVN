import logging
from typing import List, Dict, Any, Tuple
from app.risk_engine.models import EvidenceGroupEnum, ScoreComponentItem, GroupContributionSummary
from app.risk_engine.rules import (
    DEFAULT_POLICY_WEIGHTS,
    SIGNAL_GROUP_MAPPING,
    DEFAULT_GROUP_CAPS
)

logger = logging.getLogger(__name__)


def normalize_signal_type(raw_type: str) -> str:
    """
    Normalize signal names from different phases into canonical policy types.
    """
    clean = raw_type.strip().upper()
    if clean.startswith("IMAGE_IMAGE_"):
        clean = clean[6:]
    return clean


def get_signal_group(signal_type: str) -> EvidenceGroupEnum:
    """
    Resolve evidence group for a signal type.
    """
    norm_type = normalize_signal_type(signal_type)
    if norm_type in SIGNAL_GROUP_MAPPING:
        return SIGNAL_GROUP_MAPPING[norm_type]
    
    # Fallback heuristics
    if "SERIAL" in norm_type:
        return EvidenceGroupEnum.SERIAL
    if "PRICE" in norm_type or "BENCHMARK" in norm_type:
        return EvidenceGroupEnum.INVOICE_PRICE
    if "PHASH" in norm_type or "EMBEDDING" in norm_type or "IMAGE_REUSE" in norm_type:
        return EvidenceGroupEnum.IMAGE_REUSE
    if "GPS" in norm_type or "GEO" in norm_type or "LOCATION" in norm_type:
        return EvidenceGroupEnum.LOCATION
    if "EXIF" in norm_type or "TIMESTAMP" in norm_type or "INTEGRITY" in norm_type:
        return EvidenceGroupEnum.METADATA
    if "EXTRACTION" in norm_type or "ARITHMETIC" in norm_type or "ENTITY" in norm_type:
        return EvidenceGroupEnum.EXTRACTION
    if "DEALER" in norm_type:
        return EvidenceGroupEnum.DEALER
        
    return EvidenceGroupEnum.OTHER


def deduplicate_raw_signals(raw_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates raw risk signals to prevent double counting of identical underlying conditions.
    Examples:
    - Same serial number flagged multiple times across line items -> retain single signal
    - Same image flagged repeatedly with identical check -> retain single signal
    """
    deduped: List[Dict[str, Any]] = []
    seen_keys = set()

    for sig in raw_signals:
        sig_type = sig.get("signal_type") or sig.get("signal_name") or ""
        norm_type = normalize_signal_type(sig_type)
        evidence = sig.get("evidence_data") or sig.get("evidence_payload") or sig.get("evidence") or {}

        # Construct specific deduplication key
        if "SERIAL" in norm_type:
            # Deduplicate by serial number if present in evidence
            serial_val = (
                evidence.get("serial_number") or
                evidence.get("serial") or
                (evidence.get("duplicate_serials") and str(evidence.get("duplicate_serials"))) or
                "generic_serial"
            )
            dedup_key = f"SERIAL:{norm_type}:{serial_val}"
        elif "IMAGE" in norm_type:
            # Deduplicate by image_id + check_type
            img_id = evidence.get("current_image_id") or sig.get("image_id") or "generic_img"
            match_id = evidence.get("matching_image_id") or evidence.get("matching_case_id") or ""
            dedup_key = f"IMAGE:{norm_type}:{img_id}:{match_id}"
        elif "PRICE" in norm_type:
            inv_id = sig.get("invoice_id") or "generic_inv"
            dedup_key = f"PRICE:{norm_type}:{inv_id}"
        elif "GPS" in norm_type or "LOCATION" in norm_type:
            img_id = evidence.get("current_image_id") or "generic_loc"
            dedup_key = f"GPS:{norm_type}:{img_id}"
        else:
            dedup_key = f"GENERIC:{norm_type}:{sig.get('description', '')}"

        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            deduped.append(sig)

    return deduped


def group_and_cap_signals(
    deduped_signals: List[Dict[str, Any]],
    policy_weights: Dict[str, int] = DEFAULT_POLICY_WEIGHTS,
    group_caps: Dict[EvidenceGroupEnum, int] = DEFAULT_GROUP_CAPS
) -> Tuple[List[ScoreComponentItem], Dict[str, GroupContributionSummary], int, int]:
    """
    Groups deduplicated signals, applies policy weights, enforces group caps,
    and returns traceable components with effective contributions.
    Returns: (components, group_summaries, raw_total, capped_total)
    """
    # Group signals
    grouped_items: Dict[EvidenceGroupEnum, List[Tuple[Dict[str, Any], int]]] = {
        grp: [] for grp in EvidenceGroupEnum
    }

    raw_total = 0

    for sig in deduped_signals:
        sig_type = sig.get("signal_type") or sig.get("signal_name") or ""
        norm_type = normalize_signal_type(sig_type)
        
        # Determine weight
        weight = policy_weights.get(norm_type, 0)
        if weight == 0:
            # Try matching prefixes or general keywords
            for k, v in policy_weights.items():
                if k in norm_type or norm_type in k:
                    weight = v
                    break

        group = get_signal_group(norm_type)
        grouped_items[group].append((sig, weight))
        raw_total += weight

    components: List[ScoreComponentItem] = []
    group_summaries: Dict[str, GroupContributionSummary] = {}
    capped_total = 0

    for group, items in grouped_items.items():
        if not items:
            continue

        group_cap = group_caps.get(group, 20)
        group_raw_sum = sum(weight for _, weight in items)
        group_effective = min(group_raw_sum, group_cap)
        is_capped = group_raw_sum > group_cap

        group_summaries[group.value] = GroupContributionSummary(
            group=group,
            raw_sum=group_raw_sum,
            group_cap=group_cap,
            effective_contribution=group_effective,
            signal_count=len(items)
        )
        capped_total += group_effective

        # Distribute group_effective sequentially across group items
        remaining_budget = group_effective
        for sig, weight in items:
            sig_type = sig.get("signal_type") or sig.get("signal_name") or ""
            norm_type = normalize_signal_type(sig_type)
            evidence = sig.get("evidence_data") or sig.get("evidence_payload") or sig.get("evidence") or {}

            # Contribution allocated to this item
            item_contrib = min(weight, remaining_budget)
            remaining_budget = max(0, remaining_budget - item_contrib)

            # Determine pipeline stage source
            if "IMAGE" in norm_type or "EXIF" in norm_type or "GPS" in norm_type:
                source = "image_forensics" if "EMBEDDING" not in norm_type else "deep_visual_embeddings"
            elif "PRICE" in norm_type or "SERIAL" in norm_type or "ARITHMETIC" in norm_type:
                source = "invoice_verification"
            elif "DEALER" in norm_type:
                source = "dealer_network_analysis"
            else:
                source = "verification_pipeline"

            comp = ScoreComponentItem(
                signal_id=sig.get("id"),
                signal_type=norm_type,
                group=group,
                source=source,
                severity=str(sig.get("severity", "medium")).lower(),
                policy_weight=weight,
                effective_contribution=item_contrib,
                is_group_capped=is_capped and (item_contrib < weight),
                group_cap_applied=group_cap if is_capped else None,
                description=sig.get("description") or f"Active risk anomaly detected: {norm_type}",
                evidence=evidence,
                created_at=sig.get("created_at")
            )
            components.append(comp)

    return components, group_summaries, raw_total, capped_total
