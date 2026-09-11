import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from app.graph.models import (
    RelationshipCategoryEnum,
    RelationshipTypeEnum,
    RelationshipItem,
    GraphNode,
    GraphEdge,
    RelationshipGraphResponse,
    DealerConcentrationSummary
)
from app.graph.normalization import (
    normalize_phone,
    mask_phone,
    normalize_email,
    mask_email,
    normalize_address,
    mask_address,
    normalize_serial,
    hash_attribute
)
from app.graph.rules import (
    RELATIONSHIP_POLICY_VERSION,
    evaluate_dealer_relationship_anomaly
)

logger = logging.getLogger(__name__)


class RelationshipEngine:
    """
    Deterministic Relationship Analysis Engine for DIAVN.
    Extracts structural links, surfaces evidence links, evaluates conservative anomaly rules,
    and projects graph views without graph databases, external APIs, or ML/LLMs.
    """

    def analyze_case_relationships(
        self,
        case_id: str,
        case_data: Dict[str, Any],
        dealer_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        invoices: List[Dict[str, Any]],
        assets: List[Dict[str, Any]],
        all_cases: List[Dict[str, Any]],
        all_customers: List[Dict[str, Any]],
        all_dealers: List[Dict[str, Any]],
        active_signals: List[Dict[str, Any]]
    ) -> Tuple[List[RelationshipItem], List[RelationshipItem], List[RelationshipItem], List[Dict[str, Any]]]:
        """
        Executes full deterministic relationship analysis for a single case.
        Returns:
          (structural_relationships, evidence_relationships, potential_anomalies, risk_signals)
        """
        structural_links: List[RelationshipItem] = []
        evidence_links: List[RelationshipItem] = []
        potential_anomalies: List[RelationshipItem] = []
        generated_signals: List[Dict[str, Any]] = []

        dealer_id = case_data.get("dealer_id") or dealer_data.get("id") or "DLR-UNKNOWN"
        customer_id = case_data.get("customer_id") or customer_data.get("id") or "CUST-UNKNOWN"
        case_num = case_data.get("case_number", case_id)

        # ---------------------------------------------------------------------
        # 1. CATEGORY A: STRUCTURAL RELATIONSHIPS (Context Only, Zero Risk)
        # ---------------------------------------------------------------------
        # 1.1 Dealer Serves Customer
        structural_links.append(RelationshipItem(
            id=f"REL-STR-DC-{dealer_id}-{customer_id}",
            case_id=case_id,
            source_entity_type="dealer",
            source_entity_id=dealer_id,
            target_entity_type="customer",
            target_entity_id=customer_id,
            relationship_type=RelationshipTypeEnum.DEALER_SERVES_CUSTOMER,
            category=RelationshipCategoryEnum.STRUCTURAL,
            description=f"Dealer {dealer_data.get('name', dealer_id)} serves borrower {customer_data.get('full_name', customer_id)}.",
            strength=1.0,
            risk_weight=0.0,
            policy_version=RELATIONSHIP_POLICY_VERSION,
            metadata={"dealer_code": dealer_data.get("dealer_code"), "customer_code": customer_data.get("customer_code")}
        ))

        # 1.2 Customer Associated Case
        structural_links.append(RelationshipItem(
            id=f"REL-STR-CC-{customer_id}-{case_id}",
            case_id=case_id,
            source_entity_type="customer",
            source_entity_id=customer_id,
            target_entity_type="case",
            target_entity_id=case_id,
            relationship_type=RelationshipTypeEnum.CUSTOMER_ASSOCIATED_CASE,
            category=RelationshipCategoryEnum.STRUCTURAL,
            description=f"Borrower {customer_data.get('full_name', customer_id)} submitted application {case_num}.",
            strength=1.0,
            risk_weight=0.0,
            policy_version=RELATIONSHIP_POLICY_VERSION,
            metadata={"loan_amount": case_data.get("loan_amount")}
        ))

        # 1.3 Dealer Originated Case
        structural_links.append(RelationshipItem(
            id=f"REL-STR-DOC-{dealer_id}-{case_id}",
            case_id=case_id,
            source_entity_type="dealer",
            source_entity_id=dealer_id,
            target_entity_type="case",
            target_entity_id=case_id,
            relationship_type=RelationshipTypeEnum.DEALER_ORIGINATED_CASE,
            category=RelationshipCategoryEnum.STRUCTURAL,
            description=f"Case application {case_num} originated through dealer {dealer_data.get('name', dealer_id)}.",
            strength=1.0,
            risk_weight=0.0,
            policy_version=RELATIONSHIP_POLICY_VERSION,
            metadata={"status": case_data.get("status")}
        ))

        # 1.4 Case Contains Invoices
        for inv in invoices:
            inv_id = str(inv.get("id", "INV-0"))
            inv_num = inv.get("invoice_number", inv_id)
            structural_links.append(RelationshipItem(
                id=f"REL-STR-CI-{case_id}-{inv_id}",
                case_id=case_id,
                source_entity_type="case",
                source_entity_id=case_id,
                target_entity_type="invoice",
                target_entity_id=inv_id,
                relationship_type=RelationshipTypeEnum.CASE_CONTAINS_INVOICE,
                category=RelationshipCategoryEnum.STRUCTURAL,
                description=f"Case {case_num} includes invoice {inv_num}.",
                strength=1.0,
                risk_weight=0.0,
                policy_version=RELATIONSHIP_POLICY_VERSION,
                metadata={"invoice_number": inv_num, "total_amount": inv.get("total_amount")}
            ))

        # 1.5 Case Contains Assets & Serial Numbers
        case_serials = set()
        for inv in invoices:
            line_items = inv.get("line_items") or []
            for item in line_items:
                for s in (item.get("serial_numbers") or []):
                    norm_s = normalize_serial(s)
                    if norm_s:
                        case_serials.add(norm_s)
        
        for asset in assets:
            a_id = str(asset.get("id", "AST-0"))
            a_serial = normalize_serial(asset.get("serial_number"))
            if a_serial:
                case_serials.add(a_serial)
            structural_links.append(RelationshipItem(
                id=f"REL-STR-CA-{case_id}-{a_id}",
                case_id=case_id,
                source_entity_type="case",
                source_entity_id=case_id,
                target_entity_type="asset",
                target_entity_id=a_id,
                relationship_type=RelationshipTypeEnum.CASE_CONTAINS_ASSET,
                category=RelationshipCategoryEnum.STRUCTURAL,
                description=f"Case {case_num} references equipment asset {asset.get('brand', '')} {asset.get('model_name', '')}.",
                strength=1.0,
                risk_weight=0.0,
                policy_version=RELATIONSHIP_POLICY_VERSION,
                metadata={"serial_number": a_serial, "asset_type": asset.get("asset_type")}
            ))

        # ---------------------------------------------------------------------
        # 2. CATEGORY B: EVIDENCE RELATIONSHIPS (Observed Patterns, Zero Risk)
        # ---------------------------------------------------------------------
        # 2.1 Dealer - Customer Shared Address (Direct match)
        norm_dealer_addr = normalize_address(dealer_data.get("address"))
        norm_cust_addr = normalize_address(customer_data.get("address"))
        norm_claimed_addr = normalize_address(case_data.get("claimed_installation_address"))

        if norm_dealer_addr and (norm_dealer_addr == norm_cust_addr or norm_dealer_addr == norm_claimed_addr):
            evidence_links.append(RelationshipItem(
                id=f"REL-EVD-DCA-{dealer_id}-{customer_id}",
                case_id=case_id,
                source_entity_type="dealer",
                source_entity_id=dealer_id,
                target_entity_type="customer",
                target_entity_id=customer_id,
                relationship_type=RelationshipTypeEnum.DEALER_CUSTOMER_SHARED_ADDRESS,
                category=RelationshipCategoryEnum.EVIDENCE,
                description=f"Customer claimed address coincides with dealer registered office ({mask_address(dealer_data.get('address'))}).",
                strength=1.0,
                risk_weight=0.0,
                policy_version=RELATIONSHIP_POLICY_VERSION,
                metadata={
                    "attribute_type": "address",
                    "masked_address": mask_address(dealer_data.get("address")),
                    "address_hash": hash_attribute(norm_dealer_addr)
                }
            ))

        # 2.2 Dealer - Customer Shared Phone
        norm_dealer_phone = normalize_phone(dealer_data.get("contact_phone"))
        norm_cust_phone = normalize_phone(customer_data.get("contact_phone"))
        if norm_dealer_phone and norm_cust_phone and norm_dealer_phone == norm_cust_phone:
            evidence_links.append(RelationshipItem(
                id=f"REL-EVD-DCP-{dealer_id}-{customer_id}",
                case_id=case_id,
                source_entity_type="dealer",
                source_entity_id=dealer_id,
                target_entity_type="customer",
                target_entity_id=customer_id,
                relationship_type=RelationshipTypeEnum.DEALER_CUSTOMER_SHARED_PHONE,
                category=RelationshipCategoryEnum.EVIDENCE,
                description=f"Customer contact phone matches dealer contact phone ({mask_phone(customer_data.get('contact_phone'))}).",
                strength=1.0,
                risk_weight=0.0,
                policy_version=RELATIONSHIP_POLICY_VERSION,
                metadata={
                    "attribute_type": "phone",
                    "masked_phone": mask_phone(customer_data.get("contact_phone")),
                    "phone_hash": hash_attribute(norm_cust_phone)
                }
            ))

        # 2.3 Shared Customer Phone across Database
        if norm_cust_phone:
            matching_customers = [
                c for c in all_customers 
                if c.get("id") != customer_id and normalize_phone(c.get("contact_phone")) == norm_cust_phone
            ]
            if matching_customers:
                matched_c_ids = [customer_id] + [c.get("id") for c in matching_customers]
                matched_case_ids = [
                    c.get("id") for c in all_cases if c.get("customer_id") in matched_c_ids
                ]
                evidence_links.append(RelationshipItem(
                    id=f"REL-EVD-SCP-{customer_id}",
                    case_id=case_id,
                    source_entity_type="customer",
                    source_entity_id=customer_id,
                    target_entity_type="customer",
                    target_entity_id=matching_customers[0].get("id"),
                    relationship_type=RelationshipTypeEnum.SHARED_CUSTOMER_PHONE,
                    category=RelationshipCategoryEnum.EVIDENCE,
                    description=f"{len(matched_c_ids)} customer records share normalized contact phone ({mask_phone(customer_data.get('contact_phone'))}).",
                    strength=1.0,
                    risk_weight=0.0,
                    policy_version=RELATIONSHIP_POLICY_VERSION,
                    metadata={
                        "attribute_type": "phone",
                        "entity_ids": matched_c_ids,
                        "case_ids": matched_case_ids,
                        "masked_value": mask_phone(customer_data.get("contact_phone")),
                        "value_hash": hash_attribute(norm_cust_phone)
                    }
                ))

        # 2.4 Shared Customer Email across Database
        norm_cust_email = normalize_email(customer_data.get("contact_email"))
        if norm_cust_email:
            matching_email_customers = [
                c for c in all_customers 
                if c.get("id") != customer_id and normalize_email(c.get("contact_email")) == norm_cust_email
            ]
            if matching_email_customers:
                matched_email_c_ids = [customer_id] + [c.get("id") for c in matching_email_customers]
                matched_email_case_ids = [
                    c.get("id") for c in all_cases if c.get("customer_id") in matched_email_c_ids
                ]
                evidence_links.append(RelationshipItem(
                    id=f"REL-EVD-SCE-{customer_id}",
                    case_id=case_id,
                    source_entity_type="customer",
                    source_entity_id=customer_id,
                    target_entity_type="customer",
                    target_entity_id=matching_email_customers[0].get("id"),
                    relationship_type=RelationshipTypeEnum.SHARED_CUSTOMER_EMAIL,
                    category=RelationshipCategoryEnum.EVIDENCE,
                    description=f"{len(matched_email_c_ids)} customer records share normalized email ({mask_email(customer_data.get('contact_email'))}).",
                    strength=1.0,
                    risk_weight=0.0,
                    policy_version=RELATIONSHIP_POLICY_VERSION,
                    metadata={
                        "attribute_type": "email",
                        "entity_ids": matched_email_c_ids,
                        "case_ids": matched_email_case_ids,
                        "masked_value": mask_email(customer_data.get("contact_email")),
                        "value_hash": hash_attribute(norm_cust_email)
                    }
                ))

        # 2.5 Shared Customer Address across Database
        if norm_cust_addr:
            matching_addr_customers = [
                c for c in all_customers 
                if c.get("id") != customer_id and normalize_address(c.get("address")) == norm_cust_addr
            ]
            if matching_addr_customers:
                matched_addr_c_ids = [customer_id] + [c.get("id") for c in matching_addr_customers]
                evidence_links.append(RelationshipItem(
                    id=f"REL-EVD-SCA-{customer_id}",
                    case_id=case_id,
                    source_entity_type="customer",
                    source_entity_id=customer_id,
                    target_entity_type="customer",
                    target_entity_id=matching_addr_customers[0].get("id"),
                    relationship_type=RelationshipTypeEnum.SHARED_CUSTOMER_ADDRESS,
                    category=RelationshipCategoryEnum.EVIDENCE,
                    description=f"{len(matched_addr_c_ids)} customer records share identical normalized address ({mask_address(customer_data.get('address'))}).",
                    strength=1.0,
                    risk_weight=0.0,
                    policy_version=RELATIONSHIP_POLICY_VERSION,
                    metadata={
                        "attribute_type": "address",
                        "entity_ids": matched_addr_c_ids,
                        "masked_value": mask_address(customer_data.get("address")),
                        "value_hash": hash_attribute(norm_cust_addr)
                    }
                ))

        # 2.6 Cross-Case Serial Link (Visual Linkage Only, No Duplicate Risk Weight)
        for s in case_serials:
            other_cases_with_serial = [
                c for c in all_cases 
                if c.get("id") != case_id and s in [
                    normalize_serial(item) for inv_i in (c.get("invoices") or [])
                    for item in (inv_i.get("serial_numbers") or [])
                ]
            ]
            for other_c in other_cases_with_serial:
                evidence_links.append(RelationshipItem(
                    id=f"REL-EVD-CCSL-{case_id}-{other_c.get('id')}",
                    case_id=case_id,
                    source_entity_type="case",
                    source_entity_id=case_id,
                    target_entity_type="case",
                    target_entity_id=other_c.get("id"),
                    relationship_type=RelationshipTypeEnum.CROSS_CASE_SERIAL_LINK,
                    category=RelationshipCategoryEnum.EVIDENCE,
                    description=f"Serial number {s} is also referenced in case {other_c.get('case_number', other_c.get('id'))}.",
                    strength=1.0,
                    risk_weight=0.0,  # Zero weight: Phase 3 already evaluated serial risk
                    policy_version=RELATIONSHIP_POLICY_VERSION,
                    metadata={"serial_number": s, "matching_case_id": other_c.get("id")}
                ))

        # 2.7 Cross-Case Image Link (Visual Linkage Only, No Duplicate Risk Weight)
        for sig in active_signals:
            if sig.get("signal_type") in ["IMAGE_PHASH_REUSE", "IMAGE_EMBEDDING_SIMILARITY"]:
                matching_c_id = sig.get("evidence_data", {}).get("matching_case_id")
                if matching_c_id and matching_c_id != case_id:
                    evidence_links.append(RelationshipItem(
                        id=f"REL-EVD-CCIL-{case_id}-{matching_c_id}",
                        case_id=case_id,
                        source_entity_type="case",
                        source_entity_id=case_id,
                        target_entity_type="case",
                        target_entity_id=matching_c_id,
                        relationship_type=RelationshipTypeEnum.CROSS_CASE_IMAGE_LINK,
                        category=RelationshipCategoryEnum.EVIDENCE,
                        description=f"Installation visual evidence matches records from case {matching_c_id}.",
                        strength=1.0,
                        risk_weight=0.0,  # Zero weight: Phase 4/5 already evaluated image risk
                        policy_version=RELATIONSHIP_POLICY_VERSION,
                        metadata={"matching_case_id": matching_c_id, "underlying_signal": sig.get("signal_type")}
                    ))

        # ---------------------------------------------------------------------
        # 3. CATEGORY C: POTENTIAL ANOMALY (Multi-Factor Combination Evaluation)
        # ---------------------------------------------------------------------
        anomaly_item = evaluate_dealer_relationship_anomaly(
            case_id=case_id,
            dealer_id=dealer_id,
            customer_id=customer_id,
            evidence_relationships=evidence_links,
            active_case_anomalies=active_signals,
            dealer_customer_cases_map={}
        )
        
        if anomaly_item:
            potential_anomalies.append(anomaly_item)
            # Create a corresponding risk signal record for Phase 6 risk engine consumption
            generated_signals.append({
                "id": f"SIG-REL-{case_id}",
                "case_id": case_id,
                "category": "dealer_network",
                "signal_name": "DEALER_RELATIONSHIP_ANOMALY",
                "signal_type": "DEALER_RELATIONSHIP_ANOMALY",
                "severity": "high",
                "confidence_score": 90.0,
                "weight": 0.0,  # Phase 7 constraint: weight is 0.00
                "is_active": True,
                "description": anomaly_item.description,
                "evidence_payload": anomaly_item.metadata
            })

        return structural_links, evidence_links, potential_anomalies, generated_signals

    def build_graph_projection(
        self,
        case_id: Optional[str],
        dealer_id: Optional[str],
        structural_links: List[RelationshipItem],
        evidence_links: List[RelationshipItem],
        potential_anomalies: List[RelationshipItem],
        entity_metadata_map: Dict[str, Dict[str, Any]]
    ) -> RelationshipGraphResponse:
        """
        Projects relationships into a clean node-and-edge graph schema for frontend rendering.
        """
        nodes_dict: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []

        all_rels = structural_links + evidence_links + potential_anomalies

        for rel in all_rels:
            # Source Node
            src_key = f"{rel.source_entity_type}:{rel.source_entity_id}"
            if src_key not in nodes_dict:
                meta = entity_metadata_map.get(src_key, {})
                label = meta.get("label", rel.source_entity_id)
                nodes_dict[src_key] = GraphNode(
                    id=src_key,
                    label=label,
                    entity_type=rel.source_entity_type,
                    metadata=meta
                )

            # Target Node
            tgt_key = f"{rel.target_entity_type}:{rel.target_entity_id}"
            if tgt_key not in nodes_dict:
                meta = entity_metadata_map.get(tgt_key, {})
                label = meta.get("label", rel.target_entity_id)
                nodes_dict[tgt_key] = GraphNode(
                    id=tgt_key,
                    label=label,
                    entity_type=rel.target_entity_type,
                    metadata=meta
                )

            # Edge
            edge_id = f"EDGE-{rel.id}"
            edges.append(GraphEdge(
                id=edge_id,
                source=src_key,
                target=tgt_key,
                relationship=rel.relationship_type.value,
                category=rel.category,
                strength=rel.strength,
                label=rel.relationship_type.value.replace("_", " "),
                metadata=rel.metadata
            ))

        return RelationshipGraphResponse(
            case_id=case_id,
            dealer_id=dealer_id,
            nodes=list(nodes_dict.values()),
            edges=edges,
            summary={
                "nodes_count": len(nodes_dict),
                "edges_count": len(edges),
                "structural_edges": len(structural_links),
                "evidence_edges": len(evidence_links),
                "anomaly_edges": len(potential_anomalies)
            }
        )

    def calculate_dealer_concentration(
        self,
        dealer_id: str,
        dealer_data: Dict[str, Any],
        dealer_cases: List[Dict[str, Any]],
        dealer_invoices: List[Dict[str, Any]],
        dealer_assets: List[Dict[str, Any]],
        all_relationships: List[RelationshipItem],
        active_anomalies_count: int
    ) -> DealerConcentrationSummary:
        """
        Calculates descriptive concentration metrics for a dealer without calculating a fraud score.
        """
        distinct_cust_ids = set(c.get("customer_id") for c in dealer_cases if c.get("customer_id"))
        
        structural_count = sum(1 for r in all_relationships if r.category == RelationshipCategoryEnum.STRUCTURAL)
        evidence_count = sum(1 for r in all_relationships if r.category == RelationshipCategoryEnum.EVIDENCE)
        anomaly_count = sum(1 for r in all_relationships if r.category == RelationshipCategoryEnum.POTENTIAL_ANOMALY)

        # Detect shared attribute clusters for reporting
        clusters = []
        for r in all_relationships:
            if r.category == RelationshipCategoryEnum.EVIDENCE and "entity_ids" in r.metadata:
                clusters.append({
                    "attribute_type": r.metadata.get("attribute_type"),
                    "affected_entities_count": len(r.metadata.get("entity_ids", [])),
                    "masked_reference": r.metadata.get("masked_value")
                })

        return DealerConcentrationSummary(
            dealer_id=dealer_id,
            dealer_name=dealer_data.get("name", dealer_id),
            dealer_code=dealer_data.get("dealer_code", dealer_id),
            total_cases=len(dealer_cases),
            distinct_customers=len(distinct_cust_ids),
            total_invoices=len(dealer_invoices),
            registered_assets=len(dealer_assets),
            structural_relationships_count=structural_count,
            evidence_relationships_count=evidence_count,
            potential_anomalies_count=anomaly_count,
            shared_attribute_clusters=clusters,
            active_verification_anomalies_count=active_anomalies_count
        )


relationship_engine = RelationshipEngine()
