import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from app.services.image_service import image_service
from app.imaging.verification import image_verification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["Installation Images"])


class ImageUploadResponse(BaseModel):
    id: str
    case_id: str
    image_type: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    phash: Optional[str] = None
    exif_lat: Optional[float] = None
    exif_lng: Optional[float] = None
    exif_timestamp: Optional[str] = None
    verification_status: str
    message: str


@router.post("", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_installation_image(
    case_id: str = Form(...),
    image_type: str = Form("installation_wide"),
    file: UploadFile = File(...)
):
    """
    Ingest installation image document into private storage bucket.
    Validates magic bytes, file size, extracts EXIF and computes initial pHash.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid image file is required."
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    success, record, err_msg = image_service.create_image_record(
        case_id=case_id,
        original_filename=file.filename,
        file_bytes=file_bytes,
        image_type=image_type,
        mime_type=file.content_type
    )

    if not success or not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg or "Failed to process and store installation image."
        )

    return ImageUploadResponse(
        id=record["id"],
        case_id=record["case_id"],
        image_type=record["image_type"],
        original_filename=record["original_filename"],
        file_size_bytes=record["file_size_bytes"],
        mime_type=record["mime_type"],
        phash=record["phash"],
        exif_lat=record["exif_lat"],
        exif_lng=record["exif_lng"],
        exif_timestamp=record["exif_timestamp"],
        verification_status=record["verification_status"],
        message="Installation image uploaded, stored securely in private bucket, and initial metadata extracted."
    )


@router.get("/{image_id}")
async def get_installation_image(image_id: str):
    """
    Retrieve installation image record and metadata.
    """
    image = image_service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation image #{image_id} not found."
        )
    return image


@router.get("/{image_id}/download-url")
async def get_image_download_url(image_id: str):
    """
    Retrieve time-limited signed download/preview URL for private installation image.
    """
    image = image_service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation image #{image_id} not found."
        )

    signed_url = image.get("signed_url")
    return {
        "image_id": image_id,
        "filename": image.get("original_filename"),
        "download_url": signed_url,
        "expires_in_seconds": 3600
    }


@router.get("/case/{case_id}")
async def list_case_images(case_id: str):
    """
    List all installation images attached to a case.
    """
    images = image_service.list_images_for_case(case_id)
    return {
        "case_id": case_id,
        "total_images": len(images),
        "images": images
    }


@router.get("/{image_id}/similar-images")
async def get_similar_images_endpoint(image_id: str, top_k: int = 5, threshold: Optional[float] = None):
    """
    Retrieve top-K visually similar images across cases based on deep visual feature embeddings.
    Zero external APIs.
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

    return {
        "image_id": image_id,
        "case_id": image_record["case_id"],
        "model": summary.model,
        "model_version": summary.model_version,
        "embedding_dimension": summary.embedding_dimension,
        "top_similarity": summary.top_similarity,
        "threshold": summary.threshold,
        "status": summary.status,
        "matches": summary.top_matches
    }


