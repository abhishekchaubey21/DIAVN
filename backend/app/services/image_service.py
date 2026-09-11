import os
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

from app.core.config import settings
from app.db.supabase_client import get_supabase_admin_client, get_supabase_client
from app.imaging.integrity import validate_image_file_bytes
from app.imaging.exif import extract_exif_metadata
from app.imaging.hashing import compute_phash_from_bytes
from app.imaging.verification import _IMAGE_RECORDS_CACHE

logger = logging.getLogger(__name__)

LOCAL_IMAGES_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "installation_images")


class ImageService:
    def __init__(self):
        self.bucket_name = settings.SUPABASE_INSTALLATION_IMAGES_BUCKET
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_BYTES
        os.makedirs(LOCAL_IMAGES_STORAGE_DIR, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal or unsafe characters.
        """
        base_name = os.path.basename(filename)
        cleaned = re.sub(r'[^a-zA-Z0-9._-]', '_', base_name)
        return cleaned or "installation_photo.jpg"

    def generate_storage_path(self, case_id: str, original_filename: str) -> str:
        """
        Generate safe isolated storage path: {case_id}/{uuid}_{sanitized_name}
        """
        safe_name = self.sanitize_filename(original_filename)
        file_uuid = uuid.uuid4().hex[:12]
        return f"{case_id}/{file_uuid}_{safe_name}"

    def upload_image_file(
        self,
        case_id: str,
        original_filename: str,
        file_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> Tuple[str, str]:
        """
        Upload installation image to private Supabase Storage bucket or local fallback directory.
        Returns (storage_path, storage_provider).
        """
        storage_path = self.generate_storage_path(case_id, original_filename)
        admin_client = get_supabase_admin_client()

        if admin_client:
            try:
                # Ensure private bucket exists
                try:
                    admin_client.storage.create_bucket(self.bucket_name, options={"public": False})
                except Exception:
                    pass

                admin_client.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "false"}
                )
                logger.info(f"Uploaded installation image to Supabase bucket '{self.bucket_name}': {storage_path}")
                return storage_path, "supabase"
            except Exception as e:
                logger.warning(f"Supabase image upload failed: {e}. Falling back to local storage.")

        # Local storage fallback
        local_target_path = os.path.join(LOCAL_IMAGES_STORAGE_DIR, storage_path.replace("/", "_"))
        os.makedirs(os.path.dirname(local_target_path), exist_ok=True)
        with open(local_target_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Stored installation image locally at: {local_target_path}")
        return storage_path, "local"

    def download_image_bytes(self, storage_path: str, storage_provider: str = "supabase") -> Optional[bytes]:
        """
        Retrieve image bytes from storage for local analysis.
        """
        admin_client = get_supabase_admin_client()
        if storage_provider == "supabase" and admin_client:
            try:
                response = admin_client.storage.from_(self.bucket_name).download(storage_path)
                return response
            except Exception as e:
                logger.warning(f"Failed to download image from Supabase storage: {e}")

        local_target_path = os.path.join(LOCAL_IMAGES_STORAGE_DIR, storage_path.replace("/", "_"))
        if os.path.exists(local_target_path):
            with open(local_target_path, "rb") as f:
                return f.read()

        return None

    def create_signed_url(self, storage_path: str, expires_in_seconds: int = 3600) -> Optional[str]:
        """
        Generate temporary signed URL for viewing from private bucket.
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
                logger.warning(f"Failed to generate signed URL for image: {e}")

        # Local preview URL
        return f"/api/v1/images/download-local?path={storage_path}"

    def create_image_record(
        self,
        case_id: str,
        original_filename: str,
        file_bytes: bytes,
        image_type: str = "installation_wide",
        mime_type: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validates file, saves to private storage, extracts initial EXIF and pHash, and persists record.
        """
        is_valid, err_msg, meta = validate_image_file_bytes(file_bytes, original_filename, mime_type)
        if not is_valid:
            return False, None, err_msg

        actual_mime = mime_type or f"image/{meta.get('detected_format', 'jpeg').lower()}"
        storage_path, storage_provider = self.upload_image_file(
            case_id=case_id,
            original_filename=original_filename,
            file_bytes=file_bytes,
            content_type=actual_mime
        )

        image_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Extract initial EXIF & pHash
        exif_data = extract_exif_metadata(file_bytes)
        phash_val = compute_phash_from_bytes(file_bytes)

        record = {
            "id": image_id,
            "case_id": case_id,
            "image_type": image_type,
            "file_path": storage_path,
            "storage_provider": storage_provider,
            "original_filename": original_filename,
            "file_size_bytes": len(file_bytes),
            "mime_type": actual_mime,
            "phash": phash_val,
            "exif_timestamp": exif_data.get("capture_timestamp"),
            "exif_lat": exif_data.get("gps_lat"),
            "exif_lng": exif_data.get("gps_lng"),
            "exif_device_model": f"{exif_data.get('camera_make') or ''} {exif_data.get('camera_model') or ''}".strip() or None,
            "verification_status": "uploaded",
            "dimensions": meta.get("dimensions", [0, 0]),
            "created_at": now
        }

        # Cache in memory
        _IMAGE_RECORDS_CACHE[image_id] = {
            **record,
            "file_bytes": file_bytes
        }

        # Persist in Supabase if configured
        client = get_supabase_client()
        if client:
            try:
                client.table("installation_images").insert({
                    "id": image_id,
                    "case_id": case_id,
                    "image_type": image_type,
                    "file_path": storage_path,
                    "original_filename": original_filename,
                    "file_size_bytes": len(file_bytes),
                    "mime_type": actual_mime,
                    "phash": phash_val,
                    "exif_timestamp": exif_data.get("capture_timestamp"),
                    "exif_lat": exif_data.get("gps_lat"),
                    "exif_lng": exif_data.get("gps_lng"),
                    "exif_device_model": record["exif_device_model"],
                    "verification_status": "uploaded"
                }).execute()
            except Exception as e:
                logger.info(f"Supabase DB image insert note: {e}")

        logger.info(f"Created installation image record #{image_id} for case #{case_id}")
        return True, record, None

    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve image record with signed URL.
        """
        record = _IMAGE_RECORDS_CACHE.get(image_id)
        if not record:
            client = get_supabase_client()
            if client:
                try:
                    res = client.table("installation_images").select("*").eq("id", image_id).execute()
                    if res and res.data and len(res.data) > 0:
                        record = res.data[0]
                except Exception as e:
                    logger.debug(f"Could not load image from DB: {e}")

        if not record:
            return None

        storage_path = record.get("file_path")
        signed_url = None
        if storage_path:
            signed_url = self.create_signed_url(storage_path)

        return {
            **record,
            "signed_url": signed_url
        }

    def list_images_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """
        List all installation images for a case.
        """
        images = []
        for img_id, rec in _IMAGE_RECORDS_CACHE.items():
            if rec.get("case_id") == case_id:
                images.append(self.get_image(img_id))
        return images


image_service = ImageService()
