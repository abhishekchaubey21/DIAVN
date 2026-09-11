import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from pydantic import BaseModel

from app.services.storage_service import storage_service
from app.services.invoice_service import invoice_service
from app.api.cases import _cases_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Invoices"])

# Seeded / known valid cases for validation
SEEDED_CASE_IDS = {
    "CAS-2026-001", "CAS-2026-002", "CAS-2026-003", "CAS-2026-004", "CAS-2026-005",
    "CAS-2026-006", "CAS-2026-007", "CAS-2026-008", "CAS-2026-009", "CAS-2026-010",
    "55555555-5555-5555-5555-555555555501", "55555555-5555-5555-5555-555555555502",
    "55555555-5555-5555-5555-555555555503", "55555555-5555-5555-5555-555555555504",
    "55555555-5555-5555-5555-555555555505", "55555555-5555-5555-5555-555555555506",
    "55555555-5555-5555-5555-555555555507", "55555555-5555-5555-5555-555555555508",
    "55555555-5555-5555-5555-555555555509", "55555555-5555-5555-5555-555555555510"
}


class InvoiceUploadResponse(BaseModel):
    invoice_id: str
    case_id: str
    status: str
    original_filename: str
    message: str


class InvoiceDetailResponse(BaseModel):
    id: str
    case_id: str
    status: str
    verification_status: str
    original_filename: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    dealer_name: Optional[str] = None
    dealer_gstin: Optional[str] = None
    customer_name: Optional[str] = None
    total_amount: float = 0.0
    tax_amount: float = 0.0
    extraction_confidence: float = 0.0
    extraction: Optional[Dict[str, Any]] = None
    line_items: List[Dict[str, Any]] = []
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str


class SignedUrlResponse(BaseModel):
    invoice_id: str
    download_url: Optional[str] = None
    expires_in_seconds: int = 3600


@router.post("/invoices", response_model=InvoiceUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    case_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload an invoice document for a verification case.
    1. Validates that the case exists.
    2. Validates file format (PDF, PNG, JPG, WEBP) and size (max 10MB).
    3. Saves to private Supabase Storage (or secure local fallback).
    4. Creates invoice record with status 'processing'.
    5. Dispatches background extraction via Gemini Free Tier.
    """
    # 1. Validate case
    if case_id not in _cases_store and case_id not in SEEDED_CASE_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification case #{case_id} not found."
        )

    # 2. Read and validate file
    file_bytes = await file.read()
    file_size = len(file_bytes)
    filename = file.filename or "invoice.pdf"
    content_type = file.content_type or "application/pdf"

    is_valid, err_msg = storage_service.validate_file(
        filename=filename,
        content_type=content_type,
        file_size=file_size
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    # 3. Store file securely
    storage_path, provider = storage_service.upload_invoice_file(
        case_id=case_id,
        original_filename=filename,
        file_bytes=file_bytes,
        content_type=content_type
    )

    # 4. Create database record
    invoice_record = invoice_service.create_invoice_record(
        case_id=case_id,
        original_filename=filename,
        storage_path=storage_path,
        storage_provider=provider,
        content_type=content_type,
        file_size_bytes=file_size
    )

    # 5. Queue background extraction with Gemini Free Tier
    background_tasks.add_task(invoice_service.process_extraction, invoice_record["id"])

    return InvoiceUploadResponse(
        invoice_id=invoice_record["id"],
        case_id=case_id,
        status="processing",
        original_filename=filename,
        message="Invoice uploaded successfully. AI extraction scheduled."
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(invoice_id: str):
    """
    Retrieve full invoice extraction status, extracted fields, line items, and confidence.
    """
    record = invoice_service.get_invoice(invoice_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )
    return InvoiceDetailResponse(**record)


@router.get("/invoices/{invoice_id}/download-url", response_model=SignedUrlResponse)
async def get_invoice_download_url(invoice_id: str):
    """
    Generate a secure, short-lived signed URL to preview/download the original invoice document.
    Never exposes raw private storage buckets to the public.
    """
    record = invoice_service.get_invoice(invoice_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    signed_url = record.get("download_url")
    return SignedUrlResponse(
        invoice_id=invoice_id,
        download_url=signed_url,
        expires_in_seconds=3600
    )


@router.get("/invoices/case/{case_id}", response_model=List[InvoiceDetailResponse])
async def list_case_invoices(case_id: str):
    """
    List all uploaded and extracted invoices for a given case.
    """
    invoices = invoice_service.list_invoices_for_case(case_id)
    return [InvoiceDetailResponse(**inv) for inv in invoices]
