from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class RelationshipCategoryEnum(str, Enum):
    STRUCTURAL = "structural"
    EVIDENCE = "evidence"
    POTENTIAL_ANOMALY = "potential_anomaly"


class RelationshipTypeEnum(str, Enum):
    # Category A: Structural (Normal Context)
    DEALER_SERVES_CUSTOMER = "DEALER_SERVES_CUSTOMER"
    CUSTOMER_ASSOCIATED_CASE = "CUSTOMER_ASSOCIATED_CASE"
    DEALER_ORIGINATED_CASE = "DEALER_ORIGINATED_CASE"
    CASE_CONTAINS_INVOICE = "CASE_CONTAINS_INVOICE"
    CASE_CONTAINS_ASSET = "CASE_CONTAINS_ASSET"
    SERIAL_ASSOCIATED_CASE = "SERIAL_ASSOCIATED_CASE"
    
    # Category B: Evidence Links (Observed Relationships)
    SHARED_CUSTOMER_PHONE = "SHARED_CUSTOMER_PHONE"
    SHARED_CUSTOMER_EMAIL = "SHARED_CUSTOMER_EMAIL"
    SHARED_CUSTOMER_ADDRESS = "SHARED_CUSTOMER_ADDRESS"
    DEALER_CUSTOMER_SHARED_ADDRESS = "DEALER_CUSTOMER_SHARED_ADDRESS"
    DEALER_CUSTOMER_SHARED_PHONE = "DEALER_CUSTOMER_SHARED_PHONE"
    CROSS_CASE_SERIAL_LINK = "CROSS_CASE_SERIAL_LINK"
    CROSS_CASE_IMAGE_LINK = "CROSS_CASE_IMAGE_LINK"
    
    # Category C: Potential Anomaly (Multi-Factor Combination)
    DEALER_RELATIONSHIP_ANOMALY = "DEALER_RELATIONSHIP_ANOMALY"


class RelationshipItem(BaseModel):
    id: str
    case_id: Optional[str] = None
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    relationship_type: RelationshipTypeEnum
    category: RelationshipCategoryEnum
    description: str
    strength: float = 1.0
    risk_weight: float = 0.0
    policy_version: str = "relationship-v1"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphNode(BaseModel):
    id: str
    label: str
    entity_type: str  # dealer, customer, case, invoice, asset, serial, attribute
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    category: RelationshipCategoryEnum
    strength: float = 1.0
    label: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelationshipGraphResponse(BaseModel):
    case_id: Optional[str] = None
    dealer_id: Optional[str] = None
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    summary: Dict[str, int] = Field(default_factory=dict)


class DealerConcentrationSummary(BaseModel):
    dealer_id: str
    dealer_name: str
    dealer_code: str
    total_cases: int
    distinct_customers: int
    total_invoices: int
    registered_assets: int
    structural_relationships_count: int
    evidence_relationships_count: int
    potential_anomalies_count: int
    shared_attribute_clusters: List[Dict[str, Any]] = Field(default_factory=list)
    active_verification_anomalies_count: int
    policy_note: str = (
        "Descriptive statistics only. High case or customer count is an operational volume metric "
        "and does not constitute evidence of dealer misconduct or fraud."
    )


class CaseRelationshipAnalysisResponse(BaseModel):
    case_id: str
    dealer_id: str
    customer_id: str
    policy_version: str = "relationship-v1"
    structural_relationships: List[RelationshipItem]
    evidence_relationships: List[RelationshipItem]
    potential_anomalies: List[RelationshipItem]
    relationship_signals: List[Dict[str, Any]]
    total_relationships_count: int
    graph: RelationshipGraphResponse
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_note: str = (
        "DIAVN relationship analysis identifies repeated or unusual relationships within the internal "
        "DIAVN dataset. It does not prove collusion, fraud, or intentional misconduct. All signals generated "
        "have risk_weight = 0.0 in Phase 7 to prevent double-counting."
    )
