import io
import os
import logging
from typing import Tuple, Optional, Dict, Any
from PIL import Image
from app.verification.models import (
    VerificationCheckItem,
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}

# File Signatures / Magic Bytes
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_RIFF = b"RIFF"
MAGIC_WEBP = b"WEBP"


def detect_image_format_from_bytes(file_bytes: bytes) -> Optional[str]:
    """
    Inspect magic bytes to determine image container type without trusting headers.
    """
    if len(file_bytes) < 12:
        return None
    if file_bytes.startswith(MAGIC_JPEG):
        return "JPEG"
    if file_bytes.startswith(MAGIC_PNG):
        return "PNG"
    if file_bytes.startswith(MAGIC_RIFF) and file_bytes[8:12] == MAGIC_WEBP:
        return "WEBP"
    return None


def validate_image_file_bytes(
    file_bytes: bytes,
    filename: str,
    mime_type: Optional[str] = None
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Comprehensive low-level file integrity and safety check.
    Validates magic bytes, file size, decode capability, and dimension ranges.
    """
    file_size = len(file_bytes)
    max_size = settings.MAX_UPLOAD_SIZE_BYTES

    if file_size == 0:
        return False, "Image file is completely empty (0 bytes).", {}

    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"Image file size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit of {max_mb:.1f} MB.", {}

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Unsupported image file extension '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}", {}

    detected_format = detect_image_format_from_bytes(file_bytes)
    if not detected_format:
        return False, f"File signature / magic bytes do not match any supported image format (JPEG, PNG, WEBP).", {}

    # Attempt decoding image container
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            img_format = img.format
            img_mode = img.mode

            if width <= 0 or height <= 0:
                return False, f"Invalid image dimensions: {width}x{height}.", {}

            if width > 20000 or height > 20000:
                return False, f"Image dimensions ({width}x{height}) exceed maximum allowed dimension limits.", {}

            metadata = {
                "detected_format": detected_format,
                "pillow_format": img_format,
                "dimensions": [width, height],
                "mode": img_mode,
                "file_size_bytes": file_size,
            }
            return True, None, metadata

    except Exception as e:
        logger.warning(f"Failed to decode image '{filename}': {e}")
        return False, f"Corrupted or malformed image data. Could not decode: {str(e)}", {}


def check_image_file_integrity(
    file_bytes: bytes,
    filename: str,
    mime_type: Optional[str] = None
) -> VerificationCheckItem:
    """
    Produce structured VerificationCheckItem for IMAGE_FILE_INTEGRITY.
    """
    is_valid, error_msg, meta = validate_image_file_bytes(file_bytes, filename, mime_type)

    if not is_valid:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_FILE_INTEGRITY,
            check_name="Image File Integrity & Container Validation",
            status=CheckStatusEnum.ANOMALY,
            severity=CheckSeverityEnum.HIGH,
            message=error_msg or "Image file failed container validation.",
            evidence={
                "filename": filename,
                "declared_mime": mime_type,
                "error": error_msg,
                "file_size_bytes": len(file_bytes),
            }
        )

    return VerificationCheckItem(
        check_type=CheckTypeEnum.IMAGE_FILE_INTEGRITY,
        check_name="Image File Integrity & Container Validation",
        status=CheckStatusEnum.PASS,
        severity=CheckSeverityEnum.INFO,
        message=f"Image decoded successfully ({meta.get('detected_format')}, {meta.get('dimensions', [0, 0])[0]}x{meta.get('dimensions', [0, 0])[1]}px).",
        evidence=meta
    )
