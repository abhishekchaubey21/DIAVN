import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.verification.models import (
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
    VerificationCheckItem,
    InvoiceVerificationSummary
)
from app.verification.price_checks import verify_price_benchmark
from app.verification.serial_checks import verify_serial_numbers
from app.verification.consistency_checks import (
    verify_case_entity_consistency,
    verify_invoice_arithmetic,
    verify_required_evidence_fields
)
from app.services.invoice_service import invoice_service

logger = logging.getLogger(__name__)

# Verification summary cache & signals store (synced with DB/Supabase)
_verification_summaries_db: Dict[str, InvoiceVerificationSummary] = {}
_risk_signals_db: Dict[str, List[Dict[str, Any]]] = {}

# Synthetic fallback case registry for cases seeded in Phase 1
SYNTHETIC_CASE_REGISTRY = {
    "CAS-2026-001": {
        "id": "55555555-5555-5555-5555-555555555501",
        "case_number": "CAS-2026-001",
        "dealer_id": "DLR-APX-01",
        "dealer_name": "Apex Solar Solutions",
        "customer_id": "CUST-001",
        "customer_name": "Rajesh Sharma",
        "asset_type": "Solar Water Pump 5HP",
        "loan_amount": 195000.0,
        "claimed_installation_address": "Plot 12, Farm Sector B, Shirur, Pune, Maharashtra"
    },
    "CAS-2026-002": {
        "id": "55555555-5555-5555-5555-555555555502",
        "case_number": "CAS-2026-002",
        "dealer_id": "DLR-APX-01",
        "dealer_name": "Apex Solar Solutions",
        "customer_id": "CUST-004",
        "customer_name": "Vikas Deshmukh",
        "asset_type": "Solar Inverter 5kVA",
        "loan_amount": 55000.0,
        "claimed_installation_address": "Survey 52, Baramati Farm Sector, Baramati, Maharashtra"
    },
    "CAS-2026-003": {
        "id": "55555555-5555-5555-5555-555555555503",
        "case_number": "CAS-2026-003",
        "dealer_id": "DLR-SUN-02",
        "dealer_name": "SunPower Retail & Infra Solutions",
        "customer_id": "CUST-002",
        "customer_name": "Meera Patel",
        "asset_type": "Solar Inverter 5kVA",
        "loan_amount": 115000.0,
        "claimed_installation_address": "Farm 4A, Bardoli Road, Surat, Gujarat"
    },
    "CAS-2026-005": {
        "id": "55555555-5555-5555-5555-555555555505",
        "case_number": "CAS-2026-005",
        "dealer_id": "DLR-RAD-03",
        "dealer_name": "Radiant AgroTech Distributions",
        "customer_id": "CUST-003",
        "customer_name": "GreenFields Agri Enterprises",
        "asset_type": "Solar Water Pump 5HP",
        "loan_amount": 190000.0,
        "claimed_installation_address": "Sy 102/4, Devanahalli Rural, Bengaluru Rural, Karnataka"
    },
    "CAS-2026-007": {
        "id": "55555555-5555-5555-5555-555555555507",
        "case_number": "CAS-2026-007",
        "dealer_id": "DLR-RAD-03",
        "dealer_name": "Radiant AgroTech Distributions",
        "customer_id": "CUST-003",
        "customer_name": "GreenFields Agri Enterprises",
        "asset_type": "Micro-Irrigation Controller",
        "loan_amount": 34000.0,
        "claimed_installation_address": "88, Agro Yard Extension, Hebbal, Bengaluru, Karnataka"
    }
}


class DeterministicVerificationService:
    def get_case_context(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieves case context from store or synthetic registry.
        """
        try:
            from app.api.cases import _cases_store
            from app.api.dealers import _dealers_store
            if case_id in _cases_store:
                c = _cases_store[case_id]
                dealer = _dealers_store.get(c.dealer_id) if hasattr(c, 'dealer_id') else None
                return {
                    "id": c.id,
                    "case_number": c.case_number,
                    "dealer_id": getattr(c, "dealer_id", None),
                    "dealer_name": getattr(dealer, "name", None) if dealer else None,
                    "customer_id": getattr(c, "customer_id", None),
                    "customer_name": getattr(c, "customer_name", None),
                    "asset_type": getattr(c, "asset_type", None),
                    "loan_amount": getattr(c, "loan_amount", 0.0),
                    "claimed_installation_address": getattr(c, "claimed_installation_address", "")
                }
        except Exception:
            pass

        if case_id in SYNTHETIC_CASE_REGISTRY:
            return SYNTHETIC_CASE_REGISTRY[case_id]

        # Default minimal placeholder context
        return {
            "id": case_id,
            "case_number": case_id,
            "dealer_name": None,
            "customer_name": None,
            "asset_type": None,
            "loan_amount": 0.0
        }

    def verify_invoice(self, invoice_id: str) -> Optional[InvoiceVerificationSummary]:
        """
        Executes complete suite of deterministic consistency checks against extracted invoice.
        Idempotent: replaces previous verification signals for this invoice.
        """
        invoice = invoice_service.get_invoice(invoice_id)
        if not invoice:
            logger.warning(f"Cannot run verification: Invoice #{invoice_id} not found.")
            return None

        # Check that extraction is completed
        extraction_status = invoice.get("status", "unknown")
        if extraction_status != "completed" and not invoice.get("extraction"):
            logger.warning(f"Cannot run verification: Invoice #{invoice_id} extraction status is '{extraction_status}' (not completed).")
            return None

        case_id = invoice.get("case_id", "UNKNOWN_CASE")
        case_data = self.get_case_context(case_id)

        # Merge top-level invoice fields with extracted dictionary
        extraction = invoice.get("extraction") or {}
        line_items = invoice.get("line_items") or extraction.get("items") or []

        combined_invoice_data = {
            **invoice,
            **extraction,
            "line_items": line_items,
            "items": line_items
        }

        all_checks: List[VerificationCheckItem] = []

        # 1. Price Benchmark Check
        price_results = verify_price_benchmark(line_items=line_items)
        all_checks.extend(price_results)

        # 2. Serial Number Checks (Format + Internal Duplication + Same Invoice)
        serial_results = verify_serial_numbers(current_case_id=case_id, line_items=line_items)
        all_checks.extend(serial_results)

        # 3. Entity Consistency (Dealer, Customer, Asset Model)
        entity_results = verify_case_entity_consistency(
            invoice_data=combined_invoice_data,
            case_data=case_data
        )
        all_checks.extend(entity_results)

        # 4. Arithmetic Consistency (Multiplication & Gross Total)
        arithmetic_results = verify_invoice_arithmetic(invoice_data=combined_invoice_data)
        all_checks.extend(arithmetic_results)

        # 5. Required Evidence Completeness
        evidence_results = verify_required_evidence_fields(invoice_data=combined_invoice_data)
        all_checks.extend(evidence_results)

        # Calculate tally
        passed_count = sum(1 for c in all_checks if c.status == CheckStatusEnum.PASS)
        anomaly_count = sum(1 for c in all_checks if c.status == CheckStatusEnum.ANOMALY)
        inconclusive_count = sum(1 for c in all_checks if c.status == CheckStatusEnum.INCONCLUSIVE)

        # Convert anomalies into discrete risk_signals (IDEMPOTENT REPLACEMENT)
        generated_signals: List[Dict[str, Any]] = []
        for chk in all_checks:
            if chk.status == CheckStatusEnum.ANOMALY:
                sig_id = str(uuid.uuid4())
                category = "price" if chk.check_type == CheckTypeEnum.PRICE_BENCHMARK else (
                    "serial_asset" if "SERIAL" in chk.check_type.value else (
                        "dealer_network" if chk.check_type == CheckTypeEnum.CASE_ENTITY_CONSISTENCY else "document"
                    )
                )
                signal_record = {
                    "id": sig_id,
                    "case_id": case_id,
                    "invoice_id": invoice_id,
                    "category": category,
                    "signal_name": chk.check_type.value,
                    "severity": chk.severity.value.lower(),
                    "confidence_score": 95.0,  # Deterministic rule confidence
                    "evidence_payload": chk.evidence,
                    "description": chk.message,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                generated_signals.append(signal_record)

        # Idempotent storage of risk signals for this invoice
        _risk_signals_db[invoice_id] = generated_signals

        summary = InvoiceVerificationSummary(
            invoice_id=invoice_id,
            case_id=case_id,
            extraction_status=extraction_status,
            verification_status="completed",
            total_checks=len(all_checks),
            passed_count=passed_count,
            anomaly_count=anomaly_count,
            inconclusive_count=inconclusive_count,
            checks=all_checks,
            signals_generated=generated_signals,
            verified_at=datetime.now(timezone.utc),
            notes="Deterministic verification checks completed without calculating composite risk score."
        )

        _verification_summaries_db[invoice_id] = summary
        logger.info(f"Verification completed for invoice #{invoice_id}: {passed_count} PASS, {anomaly_count} ANOMALY, {inconclusive_count} INCONCLUSIVE.")
        return summary

    def get_verification_summary(self, invoice_id: str) -> Optional[InvoiceVerificationSummary]:
        """
        Retrieves existing deterministic verification summary if available.
        """
        return _verification_summaries_db.get(invoice_id)

    def get_case_signals(self, case_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all deterministic risk signals for a case.
        """
        all_signals = []
        for inv_id, signals in _risk_signals_db.items():
            for s in signals:
                if s.get("case_id") == case_id:
                    all_signals.append(s)
        return all_signals


verification_service = DeterministicVerificationService()
