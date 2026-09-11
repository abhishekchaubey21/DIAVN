from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.graph.models import (
    RelationshipCategoryEnum,
    RelationshipTypeEnum,
    RelationshipItem
)

RELATIONSHIP_POLICY_VERSION = "relationship-v1"


def evaluate_dealer_relationship_anomaly(
    case_id: str,
    dealer_id: str,
    customer_id: str,
    evidence_relationships: List[RelationshipItem],
    active_case_anomalies: List[Dict[str, Any]],
    dealer_customer_cases_map: Dict[str, List[str]]
) -> Optional[RelationshipItem]:
    """
    Evaluates whether the analyzed case/dealer/customer context warrants a DEALER_RELATIONSHIP_ANOMALY.
    
    Strict Conservative Trigger Conditions:
    
    Condition A (Cluster Attribute Overlap across Distinct Borrowers):
    - Same originating Dealer (dealer_id)
    - At least 2 distinct Customer records (C1 != C2) sharing a normalized identifying attribute (Phone or Email)
    - Linked across at least 2 distinct Case applications under that dealer
    
    Condition B (Multi-Factor Dimension Correlation on Analyzed Case):
    - Same originating Dealer (dealer_id)
    - At least 1 observed Evidence Relationship directly involving this customer/dealer/case (e.g. Dealer-Customer address/phone match or Customer-Customer shared phone/address)
    - At least 1 INDEPENDENT existing verification anomaly associated directly with the analyzed case/customer (e.g., INVOICE_PRICE_ANOMALY, DUPLICATE_SERIAL, or IMAGE_PHASH_REUSE / IMAGE_EMBEDDING_SIMILARITY)
    
    If neither condition is satisfied, returns None (no anomaly forced).
    """
    
    # 1. Evaluate Condition A: Multi-customer shared phone/email cluster
    shared_cust_signals = [
        r for r in evidence_relationships 
        if r.relationship_type in [
            RelationshipTypeEnum.SHARED_CUSTOMER_PHONE,
            RelationshipTypeEnum.SHARED_CUSTOMER_EMAIL
        ]
    ]
    for rel in shared_cust_signals:
        distinct_customers = rel.metadata.get("entity_ids", [])
        associated_cases = rel.metadata.get("case_ids", [])
        if len(distinct_customers) >= 2 and len(associated_cases) >= 2:
            return RelationshipItem(
                id=f"REL-ANOMALY-A-{case_id}",
                case_id=case_id,
                source_entity_type="dealer",
                source_entity_id=dealer_id,
                target_entity_type="customer",
                target_entity_id=customer_id,
                relationship_type=RelationshipTypeEnum.DEALER_RELATIONSHIP_ANOMALY,
                category=RelationshipCategoryEnum.POTENTIAL_ANOMALY,
                description=(
                    "Potentially unusual relationship pattern: Multiple distinct borrower records associated "
                    "with this dealer share normalized identifying contact attributes across multiple cases."
                ),
                strength=1.0,
                risk_weight=0.0,  # Strict Phase 7 constraint: weight is 0.0
                policy_version=RELATIONSHIP_POLICY_VERSION,
                metadata={
                    "rule_name": "RULE_MULTI_CUSTOMER_CLUSTER_V1",
                    "condition": "Condition_A_Shared_Contact_Cluster",
                    "dealer_id": dealer_id,
                    "customer_count": len(distinct_customers),
                    "case_count": len(associated_cases),
                    "attribute_type": rel.metadata.get("attribute_type", "contact")
                }
            )

    # 2. Evaluate Condition B: Multi-Factor Dimension Correlation on Current Case
    # Check if this case or customer has an observed evidence relationship
    relevant_evidence_links = [
        r for r in evidence_relationships 
        if r.category == RelationshipCategoryEnum.EVIDENCE and (
            r.source_entity_id == customer_id or 
            r.target_entity_id == customer_id or
            r.case_id == case_id or
            r.relationship_type in [
                RelationshipTypeEnum.DEALER_CUSTOMER_SHARED_ADDRESS,
                RelationshipTypeEnum.DEALER_CUSTOMER_SHARED_PHONE,
                RelationshipTypeEnum.SHARED_CUSTOMER_PHONE,
                RelationshipTypeEnum.SHARED_CUSTOMER_ADDRESS
            ]
        )
    ]
    
    # Check if the specific analyzed case has independent active anomalies from Phase 3-5
    # (e.g. INVOICE_PRICE_ANOMALY, DUPLICATE_SERIAL, IMAGE_PHASH_REUSE, IMAGE_EMBEDDING_SIMILARITY)
    valid_independent_anomaly_types = {
        "INVOICE_PRICE_ANOMALY",
        "BENCHMARK_PRICE_DEVIATION_HIGH",
        "DUPLICATE_SERIAL",
        "DUPLICATE_SERIAL_CROSS_CASE_DETECTED",
        "IMAGE_PHASH_REUSE",
        "IMAGE_EMBEDDING_SIMILARITY",
        "GPS_MISMATCH",
        "GEOLOCATION_DISCREPANCY_EXIF_VS_CLAIMED"
    }
    case_independent_anomalies = [
        a for a in active_case_anomalies 
        if (a.get("signal_type") in valid_independent_anomaly_types or a.get("signal_name") in valid_independent_anomaly_types)
        and a.get("is_active", True)
    ]
    
    if len(relevant_evidence_links) >= 1 and len(case_independent_anomalies) >= 1:
        primary_anomaly = case_independent_anomalies[0]
        anomaly_type_name = primary_anomaly.get("signal_type") or primary_anomaly.get("signal_name")
        return RelationshipItem(
            id=f"REL-ANOMALY-B-{case_id}",
            case_id=case_id,
            source_entity_type="dealer",
            source_entity_id=dealer_id,
            target_entity_type="customer",
            target_entity_id=customer_id,
            relationship_type=RelationshipTypeEnum.DEALER_RELATIONSHIP_ANOMALY,
            category=RelationshipCategoryEnum.POTENTIAL_ANOMALY,
            description=(
                f"Potentially unusual relationship: Dealer/borrower contextual relationship coincides with an "
                f"independent verification anomaly ({anomaly_type_name}) on this case."
            ),
            strength=1.0,
            risk_weight=0.0,  # Strict Phase 7 constraint: weight is 0.0
            policy_version=RELATIONSHIP_POLICY_VERSION,
            metadata={
                "rule_name": "RULE_MULTI_FACTOR_CORRELATION_V1",
                "condition": "Condition_B_Coinciding_Independent_Anomaly",
                "dealer_id": dealer_id,
                "case_id": case_id,
                "evidence_relationship_type": relevant_evidence_links[0].relationship_type.value,
                "independent_anomaly_signal": anomaly_type_name
            }
        )

    return None
