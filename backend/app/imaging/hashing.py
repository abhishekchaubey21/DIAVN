import io
import logging
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image
import imagehash
from app.verification.models import (
    VerificationCheckItem,
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def compute_phash_from_bytes(file_bytes: bytes) -> Optional[str]:
    """
    Compute 64-bit Discrete Cosine Transform (DCT) Perceptual Hash from raw image bytes.
    Returns normalized 16-character hexadecimal string.
    """
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            # Convert to RGB / Grayscale to handle RGBA or palette modes consistently
            rgb_img = img.convert("RGB")
            h = imagehash.phash(rgb_img)
            return str(h).lower()
    except Exception as e:
        logger.warning(f"Error computing pHash: {e}")
        return None


def compute_phash_from_image(img: Image.Image) -> Optional[str]:
    """
    Compute 64-bit pHash directly from a PIL Image object.
    """
    try:
        rgb_img = img.convert("RGB")
        h = imagehash.phash(rgb_img)
        return str(h).lower()
    except Exception as e:
        logger.warning(f"Error computing pHash from PIL image: {e}")
        return None


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """
    Calculate bitwise Hamming distance between two 16-character hex pHashes (0 to 64).
    """
    try:
        ha = imagehash.hex_to_hash(hash_a)
        hb = imagehash.hex_to_hash(hash_b)
        return int(ha - hb)
    except Exception:
        # Fallback to manual bitwise XOR count
        try:
            val_a = int(hash_a, 16)
            val_b = int(hash_b, 16)
            xor_val = val_a ^ val_b
            return bin(xor_val).count("1")
        except Exception as e:
            logger.warning(f"Error calculating Hamming distance between '{hash_a}' and '{hash_b}': {e}")
            return 64


def find_similar_images_in_database(
    current_image_id: str,
    current_case_id: str,
    current_phash: str,
    candidate_images: List[Dict[str, Any]],
    threshold: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Scan candidate images in database:
    Returns (cross_case_matches, same_case_matches) where distance <= threshold.
    """
    match_limit = threshold if threshold is not None else settings.PHASH_NEAR_MATCH_THRESHOLD

    cross_case_matches: List[Dict[str, Any]] = []
    same_case_matches: List[Dict[str, Any]] = []

    if not current_phash:
        return cross_case_matches, same_case_matches

    for cand in candidate_images:
        cand_id = cand.get("id")
        cand_case_id = cand.get("case_id")
        cand_phash = cand.get("phash")

        if not cand_phash or cand_id == current_image_id:
            continue

        dist = hamming_distance(current_phash, cand_phash)

        match_info = {
            "candidate_image_id": cand_id,
            "candidate_case_id": cand_case_id,
            "candidate_phash": cand_phash,
            "current_phash": current_phash,
            "hamming_distance": dist,
            "match_type": "exact" if dist == 0 else "near_match",
            "threshold": match_limit,
            "created_at": cand.get("created_at")
        }

        if dist <= match_limit:
            if cand_case_id == current_case_id:
                same_case_matches.append(match_info)
            else:
                cross_case_matches.append(match_info)

    # Sort matches by lowest Hamming distance
    cross_case_matches.sort(key=lambda x: x["hamming_distance"])
    same_case_matches.sort(key=lambda x: x["hamming_distance"])

    return cross_case_matches, same_case_matches


def check_phash_cross_case_reuse(
    current_image_id: str,
    current_case_id: str,
    current_phash: Optional[str],
    cross_case_matches: List[Dict[str, Any]],
    threshold: Optional[int] = None
) -> VerificationCheckItem:
    """
    Produce structured check for IMAGE_PHASH_REUSE (cross-case).
    """
    limit = threshold if threshold is not None else settings.PHASH_NEAR_MATCH_THRESHOLD

    if not current_phash:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_PHASH_REUSE,
            check_name="Internal Image Perceptual Hash (pHash) Cross-Case Reuse",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="No perceptual hash available for cross-case image comparison.",
            evidence={"phash_available": False}
        )

    if not cross_case_matches:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_PHASH_REUSE,
            check_name="Internal Image Perceptual Hash (pHash) Cross-Case Reuse",
            status=CheckStatusEnum.PASS,
            severity=CheckSeverityEnum.INFO,
            message=f"No matching or near-duplicate installation images detected in internal database (threshold: d <= {limit}).",
            evidence={
                "current_phash": current_phash,
                "evaluated_candidates": True,
                "matches_found": 0,
                "threshold": limit
            }
        )

    best_match = cross_case_matches[0]
    best_dist = best_match["hamming_distance"]
    match_type = "Exact perceptual match" if best_dist == 0 else "Near perceptual match"

    return VerificationCheckItem(
        check_type=CheckTypeEnum.IMAGE_PHASH_REUSE,
        check_name="Internal Image Perceptual Hash (pHash) Cross-Case Reuse",
        status=CheckStatusEnum.ANOMALY,
        severity=CheckSeverityEnum.HIGH,
        message=f"{match_type} (Hamming distance {best_dist}) detected with installation image from case #{best_match['candidate_case_id']}. Requires underwriter review.",
        evidence={
            "current_image_id": current_image_id,
            "current_case_id": current_case_id,
            "current_phash": current_phash,
            "matching_image_id": best_match["candidate_image_id"],
            "matching_case_id": best_match["candidate_case_id"],
            "matching_phash": best_match["candidate_phash"],
            "hamming_distance": best_dist,
            "threshold": limit,
            "registry_scope": "internal_lender_records"
        }
    )


def check_same_case_duplicate(
    current_image_id: str,
    current_case_id: str,
    same_case_matches: List[Dict[str, Any]]
) -> VerificationCheckItem:
    """
    Produce structured check for IMAGE_SAME_CASE_DUPLICATE.
    Duplicate within the same case is INFO/PASS (not a risk anomaly).
    """
    if not same_case_matches:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_SAME_CASE_DUPLICATE,
            check_name="Intra-Case Image Redundancy Check",
            status=CheckStatusEnum.PASS,
            severity=CheckSeverityEnum.INFO,
            message="Image is unique within the current case application.",
            evidence={"intra_case_duplicates": 0}
        )

    first_match = same_case_matches[0]
    return VerificationCheckItem(
        check_type=CheckTypeEnum.IMAGE_SAME_CASE_DUPLICATE,
        check_name="Intra-Case Image Redundancy Check",
        status=CheckStatusEnum.PASS,
        severity=CheckSeverityEnum.INFO,
        message=f"Duplicate or near-duplicate installation photo detected within the same case #{current_case_id} (Hamming distance {first_match['hamming_distance']}).",
        evidence={
            "current_image_id": current_image_id,
            "matching_image_id": first_match["candidate_image_id"],
            "case_id": current_case_id,
            "hamming_distance": first_match["hamming_distance"]
        }
    )
