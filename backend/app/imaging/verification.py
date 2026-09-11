import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timezone
from app.verification.models import (
    VerificationCheckItem,
    ImageVerificationSummary,
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
)
from app.imaging.integrity import check_image_file_integrity, validate_image_file_bytes
from app.imaging.exif import extract_exif_metadata, check_exif_metadata
from app.imaging.gps import (
    check_gps_coordinate_validity,
    check_gps_location_consistency,
)
from app.imaging.hashing import (
    compute_phash_from_bytes,
    find_similar_images_in_database,
    check_phash_cross_case_reuse,
    check_same_case_duplicate,
)
from app.imaging.embeddings import (
    generate_embedding_from_bytes,
    find_top_k_similar_embeddings,
    check_embedding_visual_similarity,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_DIMENSION,
)
from app.db.supabase_client import get_supabase_admin_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory storage for test/local runs without persistent database
_IMAGE_VERIFICATION_CACHE: Dict[str, ImageVerificationSummary] = {}
_IMAGE_RECORDS_CACHE: Dict[str, Dict[str, Any]] = {}
_EMBEDDING_VERIFICATION_CACHE: Dict[str, Any] = {}


def check_image_timestamp_consistency(
    capture_ts_str: Optional[str],
    invoice_date_str: Optional[str] = None,
    case_created_at_str: Optional[str] = None
) -> VerificationCheckItem:
    """
    Produce structured check for IMAGE_TIMESTAMP_CONSISTENCY.
    Compares EXIF capture timestamp against case/invoice timeline.
    Zero external APIs.
    """
    if not capture_ts_str:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_TIMESTAMP_CONSISTENCY,
            check_name="Photo Capture Timestamp & Chronology Consistency",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="No capture timestamp found in image EXIF telemetry.",
            evidence={"capture_timestamp_available": False}
        )

    try:
        # Parse capture timestamp
        cap_dt = datetime.fromisoformat(capture_ts_str.replace("Z", "+00:00")).date()
    except Exception:
        try:
            cap_dt = datetime.strptime(capture_ts_str[:10], "%Y-%m-%d").date()
        except Exception:
            return VerificationCheckItem(
                check_type=CheckTypeEnum.IMAGE_TIMESTAMP_CONSISTENCY,
                check_name="Photo Capture Timestamp & Chronology Consistency",
                status=CheckStatusEnum.INCONCLUSIVE,
                severity=CheckSeverityEnum.LOW,
                message=f"Could not parse capture timestamp '{capture_ts_str}' into valid date.",
                evidence={"raw_timestamp": capture_ts_str}
            )

    # Check for clearly impossible timestamps (e.g., year before 2010 or futuristic year > 2030)
    current_year = datetime.now(timezone.utc).year
    if cap_dt.year < 2010 or cap_dt.year > current_year + 1:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_TIMESTAMP_CONSISTENCY,
            check_name="Photo Capture Timestamp & Chronology Consistency",
            status=CheckStatusEnum.ANOMALY,
            severity=CheckSeverityEnum.MEDIUM,
            message=f"Photo capture timestamp ({cap_dt.isoformat()}) contains an impossible or uncalibrated year ({cap_dt.year}).",
            evidence={"capture_date": cap_dt.isoformat(), "detected_year": cap_dt.year}
        )

    ref_date: Optional[date] = None
    ref_source = None

    if invoice_date_str:
        try:
            ref_date = datetime.strptime(invoice_date_str[:10], "%Y-%m-%d").date()
            ref_source = "invoice_date"
        except Exception:
            pass

    if not ref_date and case_created_at_str:
        try:
            ref_date = datetime.fromisoformat(case_created_at_str.replace("Z", "+00:00")).date()
            ref_source = "case_created_at"
        except Exception:
            pass

    if not ref_date:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_TIMESTAMP_CONSISTENCY,
            check_name="Photo Capture Timestamp & Chronology Consistency",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message=f"Photo capture date ({cap_dt.isoformat()}) extracted, but no reference invoice or case date available for timeline comparison.",
            evidence={"capture_date": cap_dt.isoformat(), "reference_date_available": False}
        )

    # Calculate days difference: positive means photo taken AFTER reference, negative means BEFORE reference
    diff_days = (cap_dt - ref_date).days

    evidence = {
        "photo_capture_date": cap_dt.isoformat(),
        "reference_date": ref_date.isoformat(),
        "reference_source": ref_source,
        "delta_days": diff_days
    }

    if diff_days < 0:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_TIMESTAMP_CONSISTENCY,
            check_name="Photo Capture Timestamp & Chronology Consistency",
            status=CheckStatusEnum.PASS,
            severity=CheckSeverityEnum.INFO,
            message=f"Photo capture date ({cap_dt.isoformat()}) is {abs(diff_days)} days prior to {ref_source}. (Configurable policy note: Pre-invoice equipment staging; not evidence of manipulation).",
            evidence=evidence
        )

    return VerificationCheckItem(
        check_type=CheckTypeEnum.IMAGE_TIMESTAMP_CONSISTENCY,
        check_name="Photo Capture Timestamp & Chronology Consistency",
        status=CheckStatusEnum.PASS,
        severity=CheckSeverityEnum.INFO,
        message=f"Photo capture date ({cap_dt.isoformat()}) is consistent with case application timeline ({diff_days:+d} days relative to {ref_source}).",
        evidence=evidence
    )


class ImageVerificationService:
    """
    Deterministic installation image verification service.
    Zero external APIs. All checks run locally against database & metadata.
    """

    def get_candidate_images(self, exclude_image_id: str) -> List[Dict[str, Any]]:
        """
        Fetch existing installation images from Supabase or memory cache for pHash comparison.
        """
        admin_client = get_supabase_admin_client()
        candidates: List[Dict[str, Any]] = []

        if admin_client:
            try:
                res = admin_client.table("installation_images").select(
                    "id, case_id, image_type, phash, embedding, created_at"
                ).neq("id", exclude_image_id).execute()
                if res and res.data:
                    candidates = res.data
            except Exception as e:
                logger.warning(f"Could not query Supabase installation_images: {e}")

        # Combine with in-memory records
        for img_id, img_data in _IMAGE_RECORDS_CACHE.items():
            if img_id != exclude_image_id:
                if not any(c.get("id") == img_id for c in candidates):
                    candidates.append({
                        "id": img_id,
                        "case_id": img_data.get("case_id"),
                        "image_type": img_data.get("image_type"),
                        "phash": img_data.get("phash"),
                        "embedding": img_data.get("embedding"),
                        "created_at": img_data.get("created_at")
                    })

        return candidates

    def get_case_reference_data(self, case_id: str) -> Dict[str, Any]:
        """
        Fetch case reference details (claimed_lat, claimed_lng, created_at, invoices).
        """
        admin_client = get_supabase_admin_client()
        case_data: Dict[str, Any] = {
            "claimed_lat": None,
            "claimed_lng": None,
            "created_at": None,
            "invoice_date": None
        }

        if admin_client:
            try:
                res = admin_client.table("cases").select(
                    "id, case_number, claimed_lat, claimed_lng, created_at"
                ).eq("id", case_id).execute()
                if res and res.data and len(res.data) > 0:
                    c = res.data[0]
                    case_data["claimed_lat"] = float(c["claimed_lat"]) if c.get("claimed_lat") is not None else None
                    case_data["claimed_lng"] = float(c["claimed_lng"]) if c.get("claimed_lng") is not None else None
                    case_data["created_at"] = c.get("created_at")
            except Exception as e:
                logger.debug(f"Could not query case table: {e}")

        return case_data

    def run_image_verification(
        self,
        image_id: str,
        case_id: str,
        filename: str,
        file_bytes: bytes,
        mime_type: Optional[str] = None,
        image_type: str = "installation_wide",
        reference_lat: Optional[float] = None,
        reference_lng: Optional[float] = None,
        reference_invoice_date: Optional[str] = None,
        reference_case_created_at: Optional[str] = None,
        candidate_images: Optional[List[Dict[str, Any]]] = None
    ) -> ImageVerificationSummary:
        """
        Execute the 7 deterministic image checks and persist results.
        """
        checks: List[VerificationCheckItem] = []

        # 1. Image File Integrity & Container Validation
        integrity_check = check_image_file_integrity(file_bytes, filename, mime_type)
        checks.append(integrity_check)

        # 2. EXIF Telemetry Extraction & Sanitization
        exif_data = extract_exif_metadata(file_bytes)
        exif_check = check_exif_metadata(exif_data)
        checks.append(exif_check)

        # 3. GPS Coordinate Validity
        photo_lat = exif_data.get("gps_lat")
        photo_lng = exif_data.get("gps_lng")
        gps_val_check = check_gps_coordinate_validity(photo_lat, photo_lng)
        checks.append(gps_val_check)

        # 4. GPS Location Consistency (Haversine distance vs reference site)
        # Fetch reference data if not provided directly
        if reference_lat is None and reference_lng is None:
            case_ref = self.get_case_reference_data(case_id)
            ref_lat = case_ref.get("claimed_lat")
            ref_lng = case_ref.get("claimed_lng")
            if not reference_invoice_date:
                reference_invoice_date = case_ref.get("invoice_date")
            if not reference_case_created_at:
                reference_case_created_at = case_ref.get("created_at")
        else:
            ref_lat = reference_lat
            ref_lng = reference_lng

        gps_dist_check = check_gps_location_consistency(
            photo_lat=photo_lat,
            photo_lng=photo_lng,
            ref_lat=ref_lat,
            ref_lng=ref_lng,
            threshold_km=settings.MAX_INSTALLATION_DISTANCE_KM
        )
        checks.append(gps_dist_check)

        # 5. Image Capture Timestamp Consistency
        capture_ts = exif_data.get("capture_timestamp")
        ts_check = check_image_timestamp_consistency(
            capture_ts_str=capture_ts,
            invoice_date_str=reference_invoice_date,
            case_created_at_str=reference_case_created_at
        )
        checks.append(ts_check)

        # 6. Perceptual Hash (pHash) Computation & Internal Reuse Detection
        current_phash = compute_phash_from_bytes(file_bytes)
        candidates = candidate_images if candidate_images is not None else self.get_candidate_images(image_id)

        cross_case_matches, same_case_matches = find_similar_images_in_database(
            current_image_id=image_id,
            current_case_id=case_id,
            current_phash=current_phash or "",
            candidate_images=candidates,
            threshold=settings.PHASH_NEAR_MATCH_THRESHOLD
        )

        phash_cross_check = check_phash_cross_case_reuse(
            current_image_id=image_id,
            current_case_id=case_id,
            current_phash=current_phash,
            cross_case_matches=cross_case_matches,
            threshold=settings.PHASH_NEAR_MATCH_THRESHOLD
        )
        checks.append(phash_cross_check)

        # 7. Same-Case Duplicate Check
        same_case_check = check_same_case_duplicate(
            current_image_id=image_id,
            current_case_id=case_id,
            same_case_matches=same_case_matches
        )
        checks.append(same_case_check)

        # Summary Metrics
        total_checks = len(checks)
        passed_count = sum(1 for c in checks if c.status == CheckStatusEnum.PASS)
        anomaly_count = sum(1 for c in checks if c.status == CheckStatusEnum.ANOMALY)
        inconclusive_count = sum(1 for c in checks if c.status == CheckStatusEnum.INCONCLUSIVE)

        # Generate idempotent risk signals for anomalies
        signals_generated: List[Dict[str, Any]] = []
        for c in checks:
            if c.status == CheckStatusEnum.ANOMALY:
                signals_generated.append({
                    "case_id": case_id,
                    "signal_type": f"IMAGE_{c.check_type.value}",
                    "severity": c.severity.value,
                    "description": c.message,
                    "evidence_data": c.evidence,
                    "weight": 0  # Phase 4 does not compute composite risk scores
                })

        # Persist signals idempotently
        self._persist_image_signals_idempotent(case_id, image_id, signals_generated)

        # Update database record if client available
        self._update_image_record_in_db(
            image_id=image_id,
            phash=current_phash,
            gps_lat=photo_lat,
            gps_lng=photo_lng,
            capture_ts=capture_ts,
            exif_data=exif_data,
            verification_status="duplicate_detected" if phash_cross_check.status == CheckStatusEnum.ANOMALY else "analyzed"
        )

        summary = ImageVerificationSummary(
            image_id=image_id,
            case_id=case_id,
            original_filename=filename,
            image_type=image_type,
            verification_status="completed",
            total_checks=total_checks,
            passed_count=passed_count,
            anomaly_count=anomaly_count,
            inconclusive_count=inconclusive_count,
            checks=checks,
            signals_generated=signals_generated,
            exif_summary={
                "has_exif": exif_data.get("has_exif"),
                "camera_make": exif_data.get("camera_make"),
                "camera_model": exif_data.get("camera_model"),
                "capture_timestamp": exif_data.get("capture_timestamp"),
                "gps_lat": photo_lat,
                "gps_lng": photo_lng,
            },
            phash=current_phash,
            verified_at=datetime.utcnow()
        )

        _IMAGE_VERIFICATION_CACHE[image_id] = summary
        return summary

    def _persist_image_signals_idempotent(
        self,
        case_id: str,
        image_id: str,
        signals: List[Dict[str, Any]]
    ) -> None:
        """
        Idempotently store verification anomalies in risk_signals.
        Replaces previous signals associated with this image.
        """
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                # Remove previous signals for this image
                admin_client.table("risk_signals").delete().eq(
                    "case_id", case_id
                ).ilike("description", f"%{image_id}%").execute()

                # Insert new signals
                if signals:
                    admin_client.table("risk_signals").insert(signals).execute()
            except Exception as e:
                logger.debug(f"Could not sync image signals to Supabase: {e}")

    def verify_image_embedding(
        self,
        image_id: str,
        case_id: str,
        file_bytes: bytes,
        candidate_images: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> Any:
        """
        Extracts 512-dim deep visual feature vector using ResNet-18, searches database for
        cosine similarity matches, and returns structured audit evidence.
        """
        from app.verification.models import EmbeddingVerificationSummary

        sim_limit = threshold if threshold is not None else getattr(settings, "EMBEDDING_SIMILARITY_THRESHOLD", 0.85)

        # 1. Extract feature vector
        embedding = generate_embedding_from_bytes(file_bytes)

        # 2. Update record with embedding
        if embedding and image_id in _IMAGE_RECORDS_CACHE:
            _IMAGE_RECORDS_CACHE[image_id]["embedding"] = embedding

        admin_client = get_supabase_admin_client()
        if admin_client and embedding:
            try:
                admin_client.table("installation_images").update({
                    "embedding": embedding,
                    "embedding_model": EMBEDDING_MODEL_NAME,
                    "embedding_model_version": EMBEDDING_MODEL_VERSION,
                    "embedding_dimension": EMBEDDING_DIMENSION
                }).eq("id", image_id).execute()
            except Exception as e:
                logger.debug(f"Could not persist embedding in Supabase: {e}")

        # 3. Retrieve candidates
        candidates = candidate_images if candidate_images is not None else self.get_candidate_images(image_id)

        cross_matches, same_matches = find_top_k_similar_embeddings(
            current_image_id=image_id,
            current_case_id=case_id,
            current_embedding=embedding,
            candidate_images=candidates,
            top_k=top_k,
            threshold=sim_limit
        )

        check_item = check_embedding_visual_similarity(
            current_image_id=image_id,
            current_case_id=case_id,
            current_embedding=embedding,
            cross_case_matches=cross_matches,
            threshold=sim_limit
        )

        top_sim = cross_matches[0]["similarity"] if cross_matches else 0.0

        # Persist signal if anomaly
        if check_item.status == CheckStatusEnum.ANOMALY:
            signals = [{
                "case_id": case_id,
                "signal_type": "IMAGE_EMBEDDING_SIMILARITY",
                "severity": check_item.severity.value,
                "description": check_item.message,
                "evidence_data": check_item.evidence,
                "weight": 0  # Phase 5 does not compute composite risk scores
            }]
            self._persist_image_signals_idempotent(case_id, f"{image_id}_emb", signals)

        summary = EmbeddingVerificationSummary(
            image_id=image_id,
            case_id=case_id,
            model=EMBEDDING_MODEL_NAME,
            model_version=EMBEDDING_MODEL_VERSION,
            embedding_dimension=EMBEDDING_DIMENSION,
            has_embedding=embedding is not None,
            status=check_item.status,
            top_similarity=top_sim,
            threshold=sim_limit,
            top_matches=cross_matches,
            check_item=check_item,
            verified_at=datetime.utcnow()
        )

        _EMBEDDING_VERIFICATION_CACHE[image_id] = summary
        return summary

    def _update_image_record_in_db(
        self,
        image_id: str,
        phash: Optional[str],
        gps_lat: Optional[float],
        gps_lng: Optional[float],
        capture_ts: Optional[str],
        exif_data: Dict[str, Any],
        verification_status: str,
        embedding: Optional[List[float]] = None
    ) -> None:
        """
        Update installation_images record with extracted telemetry, pHash, and embedding.
        """
        admin_client = get_supabase_admin_client()
        if admin_client:
            try:
                update_payload = {
                    "phash": phash,
                    "exif_lat": gps_lat,
                    "exif_lng": gps_lng,
                    "exif_timestamp": capture_ts,
                    "exif_device_model": f"{exif_data.get('camera_make') or ''} {exif_data.get('camera_model') or ''}".strip() or None,
                    "verification_status": verification_status
                }
                if embedding:
                    update_payload["embedding"] = embedding
                admin_client.table("installation_images").update(update_payload).eq("id", image_id).execute()
            except Exception as e:
                logger.debug(f"Could not update installation_images record in Supabase: {e}")

        # Update cache
        if image_id in _IMAGE_RECORDS_CACHE:
            _IMAGE_RECORDS_CACHE[image_id].update({
                "phash": phash,
                "gps_lat": gps_lat,
                "gps_lng": gps_lng,
                "capture_timestamp": capture_ts,
                "verification_status": verification_status,
                "embedding": embedding or _IMAGE_RECORDS_CACHE[image_id].get("embedding")
            })


image_verification_service = ImageVerificationService()
