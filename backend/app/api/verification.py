import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
import uuid

from app.schemas.common import VerificationTaskCreate, VerificationTaskUpdate, VerificationTaskResponse
from app.verification.models import InvoiceVerificationSummary, ImageVerificationSummary
from app.verification.service import verification_service
from app.services.invoice_service import invoice_service
from app.services.image_service import image_service
from app.imaging.verification import image_verification_service, _IMAGE_VERIFICATION_CACHE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Verification"])

_tasks_store = {}


# =============================================================================
# DETERMINISTIC INVOICE VERIFICATION ENDPOINTS (PHASE 3)
# =============================================================================

@router.post("/verification/invoice/{invoice_id}", response_model=InvoiceVerificationSummary)
async def run_invoice_verification(invoice_id: str):
    """
    Executes real deterministic verification checks on an extracted invoice:
    1. Price benchmark matching and tolerance analysis
    2. Serial number format, presence, same-invoice, and internal cross-case duplication checks
    3. Case entity consistency (dealer, customer, asset model)
    4. Invoice internal arithmetic consistency
    5. Required evidence completeness
    Generates deterministic verification signals without computing composite fraud scores.
    """
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    if invoice.get("status") != "completed" and not invoice.get("extraction"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot verify invoice #{invoice_id}: AI extraction has not completed (current status: '{invoice.get('status')}')."
        )

    summary = verification_service.verify_invoice(invoice_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deterministic verification execution failed."
        )

    return summary


@router.get("/verification/invoice/{invoice_id}", response_model=InvoiceVerificationSummary)
async def get_invoice_verification(invoice_id: str):
    """
    Retrieves the latest deterministic verification summary for an invoice.
    """
    summary = verification_service.get_verification_summary(invoice_id)
    if not summary:
        invoice = invoice_service.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice #{invoice_id} not found."
            )
        # If invoice exists and extraction is completed, run verification automatically
        if invoice.get("status") == "completed" or invoice.get("extraction"):
            return verification_service.verify_invoice(invoice_id)
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verification summary found for invoice #{invoice_id}. Run POST /api/v1/verification/invoice/{invoice_id} first."
        )

    return summary


# =============================================================================
# DETERMINISTIC IMAGE FORENSICS VERIFICATION ENDPOINTS (PHASE 4)
# =============================================================================

@router.post("/verification/image/{image_id}", response_model=ImageVerificationSummary)
async def run_image_verification_endpoint(image_id: str):
    """
    Executes deterministic installation image forensics:
    1. Image file integrity and container magic bytes verification
    2. EXIF camera telemetry extraction and sanitization
    3. GPS coordinate validity and boundary checks
    4. GPS Haversine distance consistency vs case claimed installation site
    5. Photo capture timestamp and chronology consistency
    6. Perceptual Hash (pHash) 64-bit cross-case visual reuse detection
    7. Intra-case duplicate redundancy check
    Generates deterministic verification signals without computing composite fraud scores.
    """
    image_record = image_service.get_image(image_id)
    if not image_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation image #{image_id} not found."
        )

    # Retrieve image bytes
    file_bytes = image_record.get("file_bytes")
    if not file_bytes and image_record.get("file_path"):
        file_bytes = image_service.download_image_bytes(
            image_record["file_path"],
            image_record.get("storage_provider", "supabase")
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not retrieve image bytes for image #{image_id} from storage."
        )

    summary = image_verification_service.run_image_verification(
        image_id=image_id,
        case_id=image_record["case_id"],
        filename=image_record.get("original_filename", "installation_photo.jpg"),
        file_bytes=file_bytes,
        mime_type=image_record.get("mime_type"),
        image_type=image_record.get("image_type", "installation_wide")
    )

    return summary


@router.get("/verification/image/{image_id}", response_model=ImageVerificationSummary)
async def get_image_verification_endpoint(image_id: str):
    """
    Retrieves the latest deterministic verification summary for an installation image.
    """
    if image_id in _IMAGE_VERIFICATION_CACHE:
        return _IMAGE_VERIFICATION_CACHE[image_id]

    image_record = image_service.get_image(image_id)
    if not image_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation image #{image_id} not found."
        )

    # Run verification automatically if image exists
    file_bytes = image_record.get("file_bytes")
    if not file_bytes and image_record.get("file_path"):
        file_bytes = image_service.download_image_bytes(
            image_record["file_path"],
            image_record.get("storage_provider", "supabase")
        )

    if file_bytes:
        return image_verification_service.run_image_verification(
            image_id=image_id,
            case_id=image_record["case_id"],
            filename=image_record.get("original_filename", "installation_photo.jpg"),
            file_bytes=file_bytes,
            mime_type=image_record.get("mime_type"),
            image_type=image_record.get("image_type", "installation_wide")
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No verification summary found for image #{image_id}. Run POST /api/v1/verification/image/{image_id} first."
    )


# =============================================================================
# DEEP VISUAL FEATURE EMBEDDING VERIFICATION ENDPOINTS (PHASE 5)
# =============================================================================

@router.post("/verification/image/{image_id}/embedding")
async def run_image_embedding_verification_endpoint(image_id: str, top_k: int = 5, threshold: Optional[float] = None):
    """
    Executes deep visual feature embedding verification for an installation image:
    1. Extracts 512-dimensional feature vector using local ResNet-18 (CPU)
    2. Searches internal database for cross-case visual feature similarity
    3. Computes top-K cosine similarity matches
    4. Evaluates against provisional configurable threshold
    Runs 100% locally with zero paid/external APIs.
    """
    image_record = image_service.get_image(image_id)
    if not image_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation image #{image_id} not found."
        )

    file_bytes = image_record.get("file_bytes")
    if not file_bytes and image_record.get("file_path"):
        file_bytes = image_service.download_image_bytes(
            image_record["file_path"],
            image_record.get("storage_provider", "supabase")
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not retrieve image bytes for image #{image_id} from storage."
        )

    summary = image_verification_service.verify_image_embedding(
        image_id=image_id,
        case_id=image_record["case_id"],
        file_bytes=file_bytes,
        top_k=top_k,
        threshold=threshold
    )

    return summary


@router.get("/verification/image/{image_id}/embedding")
async def get_image_embedding_verification_endpoint(image_id: str):
    """
    Retrieves the latest deep visual feature embedding verification summary for an installation image.
    """
    from app.imaging.verification import _EMBEDDING_VERIFICATION_CACHE

    if image_id in _EMBEDDING_VERIFICATION_CACHE:
        return _EMBEDDING_VERIFICATION_CACHE[image_id]

    image_record = image_service.get_image(image_id)
    if not image_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation image #{image_id} not found."
        )

    file_bytes = image_record.get("file_bytes")
    if not file_bytes and image_record.get("file_path"):
        file_bytes = image_service.download_image_bytes(
            image_record["file_path"],
            image_record.get("storage_provider", "supabase")
        )

    if file_bytes:
        return image_verification_service.verify_image_embedding(
            image_id=image_id,
            case_id=image_record["case_id"],
            file_bytes=file_bytes
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No embedding verification summary found for image #{image_id}. Run POST /api/v1/verification/image/{image_id}/embedding first."
    )


# =============================================================================
# VERIFICATION TASKS ENDPOINTS (PHASE 1 FOUNDATION)
# =============================================================================

@router.post("/verification-task", response_model=VerificationTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_verification_task(task_in: VerificationTaskCreate):
    """
    Create a manual or automated verification follow-up task.
    """
    task_id = str(uuid.uuid4())
    task = VerificationTaskResponse(
        id=task_id,
        case_id=task_in.case_id,
        task_type=task_in.task_type,
        status="pending",
        assigned_to=task_in.assigned_to,
        instructions=task_in.instructions,
        findings=None,
        created_at=datetime.now(timezone.utc),
        completed_at=None
    )
    _tasks_store[task_id] = task
    return task


@router.patch("/verification-task/{task_id}", response_model=VerificationTaskResponse)
async def update_verification_task(task_id: str, task_update: VerificationTaskUpdate):
    """
    Update verification task findings or status.
    """
    if task_id not in _tasks_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification task #{task_id} not found."
        )
    task = _tasks_store[task_id]
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.findings is not None:
        task.findings = task_update.findings
    if task_update.completed_at is not None:
        task.completed_at = task_update.completed_at
    elif task_update.status in ["completed", "verified", "rejected"]:
        task.completed_at = datetime.now(timezone.utc)
    return task
