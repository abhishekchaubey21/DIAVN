import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.schemas.invoice_extraction import InvoiceExtraction
from app.services.storage_service import storage_service
from app.ai.invoice_extractor import invoice_extractor
from app.db.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# In-memory invoice store for active runtime & tests (synced with DB/Supabase when available)
_invoices_db: Dict[str, Dict[str, Any]] = {}
_line_items_db: Dict[str, List[Dict[str, Any]]] = {}


class InvoiceService:
    def create_invoice_record(
        self,
        case_id: str,
        original_filename: str,
        storage_path: str,
        storage_provider: str = "supabase",
        content_type: str = "application/pdf",
        file_size_bytes: int = 0
    ) -> Dict[str, Any]:
        """
        Creates initial invoice record before AI extraction.
        Status is initialized to 'processing'.
        """
        invoice_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "id": invoice_id,
            "case_id": case_id,
            "original_filename": original_filename,
            "storage_path": storage_path,
            "storage_provider": storage_provider,
            "content_type": content_type,
            "file_size_bytes": file_size_bytes,
            "status": "processing",  # 'uploaded', 'processing', 'completed', 'failed'
            "verification_status": "pending_verification",
            "invoice_number": None,
            "invoice_date": None,
            "dealer_name": None,
            "dealer_gstin": None,
            "customer_name": None,
            "total_amount": 0.0,
            "tax_amount": 0.0,
            "extraction": None,
            "extraction_confidence": 0.0,
            "error_message": None,
            "created_at": now,
            "updated_at": now
        }

        _invoices_db[invoice_id] = record
        _line_items_db[invoice_id] = []

        # Attempt to insert into PostgreSQL/Supabase if configured
        client = get_supabase_client()
        if client:
            try:
                client.table("invoices").insert({
                    "id": invoice_id,
                    "case_id": case_id,
                    "dealer_id": None,  # Populated after extraction
                    "invoice_number": "PENDING_EXTRACTION",
                    "invoice_date": datetime.now(timezone.utc).date().isoformat(),
                    "total_amount": 0.0,
                    "file_path": storage_path,
                    "verification_status": "pending"
                }).execute()
            except Exception as e:
                logger.info(f"Supabase DB insert note: {e}")

        logger.info(f"Created invoice record #{invoice_id} for case #{case_id} (status: processing)")
        return record

    def process_extraction(self, invoice_id: str) -> Dict[str, Any]:
        """
        Executes Gemini AI extraction on the stored invoice document.
        Called asynchronously or synchronously.
        """
        invoice = _invoices_db.get(invoice_id)
        if not invoice:
            logger.error(f"Cannot process extraction: Invoice #{invoice_id} not found.")
            return {}

        storage_path = invoice["storage_path"]
        storage_provider = invoice.get("storage_provider", "supabase")
        content_type = invoice.get("content_type", "application/pdf")

        # 1. Download file bytes from storage
        file_bytes = storage_service.download_invoice_bytes(storage_path, storage_provider)
        if not file_bytes:
            invoice["status"] = "failed"
            invoice["error_message"] = "Invoice file could not be retrieved from storage for extraction."
            invoice["updated_at"] = datetime.now(timezone.utc).isoformat()
            logger.error(f"Failed to read file bytes for invoice #{invoice_id}")
            return invoice

        # 2. Invoke Gemini AI extractor
        success, extraction, error_msg, duration = invoice_extractor.extract_from_bytes(
            file_bytes=file_bytes,
            content_type=content_type
        )

        now = datetime.now(timezone.utc).isoformat()
        invoice["updated_at"] = now

        if success and extraction:
            invoice["status"] = "completed"
            invoice["invoice_number"] = extraction.invoice_number
            invoice["invoice_date"] = extraction.invoice_date
            invoice["dealer_name"] = extraction.dealer_name
            invoice["dealer_gstin"] = extraction.dealer_gstin
            invoice["customer_name"] = extraction.customer_name
            invoice["total_amount"] = extraction.total_amount or 0.0
            invoice["tax_amount"] = extraction.total_tax or 0.0
            invoice["extraction"] = extraction.model_dump()
            invoice["extraction_confidence"] = extraction.extraction_confidence
            invoice["error_message"] = None

            # Populate line items
            extracted_items = []
            for item in extraction.items:
                line_item_id = str(uuid.uuid4())
                serials = item.serial_numbers or ([item.serial_number] if item.serial_number else [])
                item_record = {
                    "id": line_item_id,
                    "invoice_id": invoice_id,
                    "product_name": item.product_name or "Unspecified Product",
                    "description": item.description,
                    "hsn_code": item.hsn_code,
                    "quantity": item.quantity or 1.0,
                    "unit_price": item.unit_price or 0.0,
                    "taxable_amount": item.taxable_amount or 0.0,
                    "tax_rate": item.tax_rate,
                    "tax_amount": item.tax_amount or 0.0,
                    "total_amount": item.total_amount or (item.unit_price or 0.0) * (item.quantity or 1.0),
                    "serial_numbers": serials,
                    "created_at": now
                }
                extracted_items.append(item_record)

            _line_items_db[invoice_id] = extracted_items
            logger.info(f"Extraction completed for invoice #{invoice_id}: {len(extracted_items)} items parsed.")
        else:
            invoice["status"] = "failed"
            invoice["error_message"] = error_msg or "Invoice extraction unavailable. Original document preserved."
            logger.warning(f"Extraction failed for invoice #{invoice_id}: {invoice['error_message']}")

        return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full invoice record, line items, and signed download URL.
        """
        invoice = _invoices_db.get(invoice_id)
        if not invoice:
            return None

        storage_path = invoice.get("storage_path")
        signed_url = None
        if storage_path:
            signed_url = storage_service.create_signed_url(storage_path)

        line_items = _line_items_db.get(invoice_id, [])

        return {
            **invoice,
            "line_items": line_items,
            "download_url": signed_url
        }

    def list_invoices_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """
        Returns all invoices associated with a case.
        """
        results = []
        for inv_id, inv in _invoices_db.items():
            if inv.get("case_id") == case_id:
                results.append(self.get_invoice(inv_id))
        return results


invoice_service = InvoiceService()
