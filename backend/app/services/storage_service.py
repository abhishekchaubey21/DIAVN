import os
import re
import uuid
import logging
from typing import Tuple, Optional
from app.core.config import settings
from app.db.supabase_client import get_supabase_admin_client

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "invoices")


class StorageService:
    def __init__(self):
        self.bucket_name = settings.SUPABASE_INVOICE_BUCKET
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_BYTES
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

    def validate_file(self, filename: str, content_type: Optional[str], file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file extension, MIME type, and size.
        """
        if file_size <= 0:
            return False, "Uploaded file is empty."

        if file_size > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            return False, f"File size exceeds maximum allowed limit of {max_mb:.1f} MB."

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            # Check if extension matches allowed
            if ext not in ALLOWED_EXTENSIONS:
                return False, f"Unsupported MIME type '{content_type}'."

        return True, None

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal or unsafe characters.
        """
        base_name = os.path.basename(filename)
        # Remove any non-alphanumeric characters except dots, hyphens, and underscores
        cleaned = re.sub(r'[^a-zA-Z0-9._-]', '_', base_name)
        return cleaned or "document.pdf"

    def generate_storage_path(self, case_id: str, original_filename: str) -> str:
        """
        Generate safe isolated storage path: {case_id}/{uuid}_{sanitized_name}
        """
        safe_name = self.sanitize_filename(original_filename)
        file_uuid = uuid.uuid4().hex[:12]
        return f"{case_id}/{file_uuid}_{safe_name}"

    def upload_invoice_file(
        self,
        case_id: str,
        original_filename: str,
        file_bytes: bytes,
        content_type: str = "application/pdf"
    ) -> Tuple[str, str]:
        """
        Upload invoice to private Supabase Storage bucket or local fallback directory.
        Returns tuple of (storage_path, storage_provider).
        """
        storage_path = self.generate_storage_path(case_id, original_filename)
        admin_client = get_supabase_admin_client()

        if admin_client:
            try:
                # Ensure private bucket exists
                try:
                    admin_client.storage.create_bucket(self.bucket_name, options={"public": False})
                except Exception:
                    pass  # Bucket likely already exists

                # Upload to private bucket
                admin_client.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "false"}
                )
                logger.info(f"Uploaded invoice to Supabase private bucket '{self.bucket_name}': {storage_path}")
                return storage_path, "supabase"
            except Exception as e:
                logger.warning(f"Supabase storage upload failed: {e}. Falling back to local storage.")

        # Local storage fallback
        local_target_path = os.path.join(LOCAL_STORAGE_DIR, storage_path.replace("/", "_"))
        os.makedirs(os.path.dirname(local_target_path), exist_ok=True)
        with open(local_target_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Stored invoice locally at: {local_target_path}")
        return storage_path, "local"

    def download_invoice_bytes(self, storage_path: str, storage_provider: str = "supabase") -> Optional[bytes]:
        """
        Retrieve file bytes for processing by Gemini AI extractor.
        """
        admin_client = get_supabase_admin_client()
        if storage_provider == "supabase" and admin_client:
            try:
                response = admin_client.storage.from_(self.bucket_name).download(storage_path)
                return response
            except Exception as e:
                logger.warning(f"Failed to download from Supabase storage: {e}")

        # Check local path fallback
        local_target_path = os.path.join(LOCAL_STORAGE_DIR, storage_path.replace("/", "_"))
        if os.path.exists(local_target_path):
            with open(local_target_path, "rb") as f:
                return f.read()

        return None

    def create_signed_url(self, storage_path: str, expires_in_seconds: int = 3600) -> Optional[str]:
        """
        Generate temporary signed URL for secure download/preview from private bucket.
        """
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                res = admin_client.storage.from_(self.bucket_name).create_signed_url(
                    storage_path,
                    expires_in=expires_in_seconds
                )
                if isinstance(res, dict) and "signedURL" in res:
                    return res["signedURL"]
                elif hasattr(res, "signed_url"):
                    return res.signed_url
                elif isinstance(res, str):
                    return res
            except Exception as e:
                logger.warning(f"Failed to generate signed URL: {e}")
        
        # Local placeholder
        return f"/api/v1/invoices/download-local?path={storage_path}"


storage_service = StorageService()
