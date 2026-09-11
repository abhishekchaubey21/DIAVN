import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.graph.models import (
    RelationshipCategoryEnum,
    RelationshipTypeEnum,
    RelationshipItem,
    RelationshipGraphResponse,
    DealerConcentrationSummary,
    CaseRelationshipAnalysisResponse
)
from app.graph.engine import relationship_engine
from app.graph.normalization import mask_phone, mask_email, mask_address
from app.db.supabase_client import get_supabase_admin_client

logger = logging.getLogger(__name__)

# Synthetic fallback records for local testing and offline verification
_SYNTHETIC_DEALERS: Dict[str, Dict[str, Any]] = {
    "22222222-2222-2222-2222-222222222201": {
        "id": "22222222-2222-2222-2222-222222222201",
        "dealer_code": "DLR-APX-01",
        "name": "Apex Solar Equipment Pvt Ltd",
        "business_name": "Apex Solar Solutions",
        "address": "Plot 45, MIDC Phase II, Bhosari, Pune, Maharashtra - 411019",
        "contact_phone": "+91-9823000001",
        "contact_email": "compliance@apexsolar.synthetic"
    },
    "22222222-2222-2222-2222-222222222202": {
        "id": "22222222-2222-2222-2222-222222222202",
        "dealer_code": "DLR-SUN-02",
        "name": "SunPower Retail & Infra Solutions",
        "business_name": "SunPower Infra",
        "address": "12, Commercial Hub, Ring Road, Surat, Gujarat - 395002",
        "contact_phone": "+91-9823000002",
        "contact_email": "accounts@sunpowerinfra.synthetic"
    },
    "22222222-2222-2222-2222-222222222203": {
        "id": "22222222-2222-2222-2222-222222222203",
        "dealer_code": "DLR-RAD-03",
        "name": "Radiant AgroTech Distributions",
        "business_name": "Radiant Agro Dist",
        "address": "88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka - 560024",
        "contact_phone": "+91-9823000003",
        "contact_email": "ops@radiantagrotech.synthetic"
    }
}

# Alias standard short codes
_SYNTHETIC_DEALERS["DLR-001"] = _SYNTHETIC_DEALERS["22222222-2222-2222-2222-222222222201"]
_SYNTHETIC_DEALERS["DLR-002"] = _SYNTHETIC_DEALERS["22222222-2222-2222-2222-222222222202"]
_SYNTHETIC_DEALERS["DLR-003"] = _SYNTHETIC_DEALERS["22222222-2222-2222-2222-222222222203"]

_SYNTHETIC_CUSTOMERS: Dict[str, Dict[str, Any]] = {
    "33333333-3333-3333-3333-333333333301": {
        "id": "33333333-3333-3333-3333-333333333301",
        "customer_code": "CUST-001",
        "full_name": "Rajesh Sharma",
        "contact_phone": "+91-9800000001",
        "contact_email": "rajesh.sharma@example.synthetic",
        "address": "Village Khed, Taluka Shirur, Pune, Maharashtra - 412218"
    },
    "33333333-3333-3333-3333-333333333302": {
        "id": "33333333-3333-3333-3333-333333333302",
        "customer_code": "CUST-002",
        "full_name": "Meera Patel",
        "contact_phone": "+91-9800000002",
        "contact_email": "meera.patel@example.synthetic",
        "address": "Farm 4A, Bardoli Road, Surat, Gujarat - 394601"
    },
    "33333333-3333-3333-3333-333333333303": {
        "id": "33333333-3333-3333-3333-333333333303",
        "customer_code": "CUST-003",
        "full_name": "GreenFields Agri Enterprises",
        "contact_phone": "+91-9800000003",
        "contact_email": "billing@greenfields.synthetic",
        "address": "88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka - 560024" # Shares address with DLR-03
    },
    "33333333-3333-3333-3333-333333333304": {
        "id": "33333333-3333-3333-3333-333333333304",
        "customer_code": "CUST-004",
        "full_name": "Vikas Deshmukh",
        "contact_phone": "+91-9800000004",
        "contact_email": "vikas.deshmukh@example.synthetic",
        "address": "Survey 52, Baramati Farm Sector, Baramati, Maharashtra - 413102"
    },
    "33333333-3333-3333-3333-333333333305": {
        "id": "33333333-3333-3333-3333-333333333305",
        "customer_code": "CUST-005",
        "full_name": "Anita Sundaram",
        "contact_phone": "+91-9823000003", # Shares phone with DLR-03
        "contact_email": "anita.sundaram@example.synthetic",
        "address": "88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka - 560024" # Shares address with DLR-03 & CUST-003
    }
}

_SYNTHETIC_CASES: Dict[str, Dict[str, Any]] = {
    "CAS-2026-001": {
        "id": "55555555-5555-5555-5555-555555555501",
        "case_number": "CAS-2026-001",
        "dealer_id": "22222222-2222-2222-2222-222222222201",
        "customer_id": "33333333-3333-3333-3333-333333333301",
        "asset_type": "Solar Water Pump 5HP",
        "claimed_installation_address": "Plot 12, Farm Sector B, Shirur, Pune, Maharashtra",
        "loan_amount": 195000.0,
        "status": "verified"
    },
    "CAS-2026-007": {
        "id": "55555555-5555-5555-5555-555555555507",
        "case_number": "CAS-2026-007",
        "dealer_id": "22222222-2222-2222-2222-222222222203",
        "customer_id": "33333333-3333-3333-3333-333333333303",
        "asset_type": "Micro-Irrigation Controller",
        "claimed_installation_address": "88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka",
        "loan_amount": 34000.0,
        "status": "flagged"
    },
    "CAS-2026-008": {
        "id": "55555555-5555-5555-5555-555555555508",
        "case_number": "CAS-2026-008",
        "dealer_id": "22222222-2222-2222-2222-222222222203",
        "customer_id": "33333333-3333-3333-3333-333333333305",
        "asset_type": "Solar Inverter 5kVA",
        "claimed_installation_address": "88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka",
        "loan_amount": 56000.0,
        "status": "flagged"
    }
}

# Add UUID aliases
_SYNTHETIC_CASES["55555555-5555-5555-5555-555555555501"] = _SYNTHETIC_CASES["CAS-2026-001"]
_SYNTHETIC_CASES["55555555-5555-5555-5555-555555555507"] = _SYNTHETIC_CASES["CAS-2026-007"]
_SYNTHETIC_CASES["55555555-5555-5555-5555-555555555508"] = _SYNTHETIC_CASES["CAS-2026-008"]

# In-memory persistence store for dynamic relationship evaluation
_RELATIONSHIPS_CACHE: Dict[str, List[RelationshipItem]] = {}


class RelationshipService:
    """
    Service coordinating relationship evaluation, database queries, in-memory caching,
    and graph projections.
    """

    def get_case_data(self, case_id: str) -> Dict[str, Any]:
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.table("cases").select("*").eq("id", case_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Could not fetch case {case_id} from Supabase: {e}")
        
        # Fallback
        if case_id in _SYNTHETIC_CASES:
            return _SYNTHETIC_CASES[case_id]
        return {
            "id": case_id,
            "case_number": case_id,
            "dealer_id": "22222222-2222-2222-2222-222222222201",
            "customer_id": "33333333-3333-3333-3333-333333333301",
            "asset_type": "Solar Equipment",
            "claimed_installation_address": "Plot 1, Site Alpha",
            "loan_amount": 100000.0,
            "status": "submitted"
        }

    def get_dealer_data(self, dealer_id: str) -> Dict[str, Any]:
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.table("dealers").select("*").eq("id", dealer_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Could not fetch dealer {dealer_id} from Supabase: {e}")
        
        if dealer_id in _SYNTHETIC_DEALERS:
            return _SYNTHETIC_DEALERS[dealer_id]
        return {
            "id": dealer_id,
            "dealer_code": "DLR-GEN",
            "name": f"Dealer {dealer_id}",
            "address": "Commercial Hub",
            "contact_phone": "+91-9800000000",
            "contact_email": "contact@dealer.synthetic"
        }

    def get_customer_data(self, customer_id: str) -> Dict[str, Any]:
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.table("customers").select("*").eq("id", customer_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Could not fetch customer {customer_id} from Supabase: {e}")
        
        if customer_id in _SYNTHETIC_CUSTOMERS:
            return _SYNTHETIC_CUSTOMERS[customer_id]
        return {
            "id": customer_id,
            "customer_code": "CUST-GEN",
            "full_name": f"Customer {customer_id}",
            "address": "Residential Area",
            "contact_phone": "+91-9800000000",
            "contact_email": "customer@example.synthetic"
        }

    def analyze_and_persist_case_relationships(self, case_id: str) -> CaseRelationshipAnalysisResponse:
        """
        Executes deterministic relationship analysis and caches/persists the structured results.
        """
        case_data = self.get_case_data(case_id)
        dealer_id = case_data.get("dealer_id", "")
        customer_id = case_data.get("customer_id", "")

        dealer_data = self.get_dealer_data(dealer_id)
        customer_data = self.get_customer_data(customer_id)

        # Invoices and assets
        invoices = []
        assets = []
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                i_res = admin_client.table("invoices").select("*, invoice_line_items(*)").eq("case_id", case_id).execute()
                if i_res and i_res.data:
                    invoices = i_res.data
            except Exception as e:
                logger.debug(f"Could not fetch invoices: {e}")

        # Active signals from Phase 3-6
        active_signals = []
        try:
            from app.risk_engine.service import RiskEngineService
            risk_service = RiskEngineService()
            active_signals = risk_service.collect_case_signals(case_id)
        except Exception as e:
            logger.debug(f"Could not load risk signals: {e}")

        all_cases = list(_SYNTHETIC_CASES.values())
        all_customers = list(_SYNTHETIC_CUSTOMERS.values())
        all_dealers = list(_SYNTHETIC_DEALERS.values())

        structural, evidence, anomalies, generated_signals = relationship_engine.analyze_case_relationships(
            case_id=case_id,
            case_data=case_data,
            dealer_data=dealer_data,
            customer_data=customer_data,
            invoices=invoices,
            assets=assets,
            all_cases=all_cases,
            all_customers=all_customers,
            all_dealers=all_dealers,
            active_signals=active_signals
        )

        all_rels = structural + evidence + anomalies
        _RELATIONSHIPS_CACHE[case_id] = all_rels

        # Prepare metadata map for graph nodes
        entity_meta = {
            f"dealer:{dealer_id}": {
                "label": dealer_data.get("name", dealer_id),
                "code": dealer_data.get("dealer_code"),
                "city": dealer_data.get("city")
            },
            f"customer:{customer_id}": {
                "label": customer_data.get("full_name", customer_id),
                "masked_phone": mask_phone(customer_data.get("contact_phone")),
                "masked_email": mask_email(customer_data.get("contact_email"))
            },
            f"case:{case_id}": {
                "label": case_data.get("case_number", case_id),
                "asset_type": case_data.get("asset_type"),
                "loan_amount": case_data.get("loan_amount")
            }
        }

        graph = relationship_engine.build_graph_projection(
            case_id=case_id,
            dealer_id=dealer_id,
            structural_links=structural,
            evidence_links=evidence,
            potential_anomalies=anomalies,
            entity_metadata_map=entity_meta
        )

        return CaseRelationshipAnalysisResponse(
            case_id=case_id,
            dealer_id=dealer_id,
            customer_id=customer_id,
            structural_relationships=structural,
            evidence_relationships=evidence,
            potential_anomalies=anomalies,
            relationship_signals=generated_signals,
            total_relationships_count=len(all_rels),
            graph=graph
        )

    def get_case_relationships(self, case_id: str) -> CaseRelationshipAnalysisResponse:
        return self.analyze_and_persist_case_relationships(case_id)

    def get_dealer_concentration(self, dealer_id: str) -> DealerConcentrationSummary:
        dealer_data = self.get_dealer_data(dealer_id)
        
        # Find cases for dealer
        cases = [c for c in _SYNTHETIC_CASES.values() if c.get("dealer_id") == dealer_id or dealer_id in ["DLR-001", "DLR-002", "DLR-003"]]
        
        # Collect all relationships for dealer cases
        all_rels: List[RelationshipItem] = []
        for c in cases:
            c_id = c.get("id")
            if c_id not in _RELATIONSHIPS_CACHE:
                self.analyze_and_persist_case_relationships(c_id)
            all_rels.extend(_RELATIONSHIPS_CACHE.get(c_id, []))

        active_anomalies_count = sum(
            1 for r in all_rels if r.category == RelationshipCategoryEnum.POTENTIAL_ANOMALY
        )

        return relationship_engine.calculate_dealer_concentration(
            dealer_id=dealer_id,
            dealer_data=dealer_data,
            dealer_cases=cases,
            dealer_invoices=[],
            dealer_assets=[],
            all_relationships=all_rels,
            active_anomalies_count=active_anomalies_count
        )

    def get_case_graph(self, case_id: str) -> RelationshipGraphResponse:
        analysis = self.analyze_and_persist_case_relationships(case_id)
        return analysis.graph

    def get_dealer_graph(self, dealer_id: str) -> RelationshipGraphResponse:
        summary = self.get_dealer_concentration(dealer_id)
        dealer_data = self.get_dealer_data(dealer_id)
        cases = [c for c in _SYNTHETIC_CASES.values() if c.get("dealer_id") == dealer_id or dealer_id in ["DLR-001", "DLR-002", "DLR-003"]]
        
        all_rels: List[RelationshipItem] = []
        for c in cases:
            all_rels.extend(_RELATIONSHIPS_CACHE.get(c.get("id"), []))

        structural = [r for r in all_rels if r.category == RelationshipCategoryEnum.STRUCTURAL]
        evidence = [r for r in all_rels if r.category == RelationshipCategoryEnum.EVIDENCE]
        anomalies = [r for r in all_rels if r.category == RelationshipCategoryEnum.POTENTIAL_ANOMALY]

        entity_meta = {
            f"dealer:{dealer_id}": {
                "label": dealer_data.get("name", dealer_id),
                "code": dealer_data.get("dealer_code")
            }
        }
        for c in cases:
            c_id = c.get("id")
            entity_meta[f"case:{c_id}"] = {"label": c.get("case_number", c_id)}

        return relationship_engine.build_graph_projection(
            case_id=None,
            dealer_id=dealer_id,
            structural_links=structural,
            evidence_links=evidence,
            potential_anomalies=anomalies,
            entity_metadata_map=entity_meta
        )


relationship_service = RelationshipService()
