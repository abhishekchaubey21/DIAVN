"""
DIAVN Phase 4 Imaging Forensics Engine
Zero external APIs • Deterministic EXIF, GPS, pHash, and reuse detection.
"""

from app.imaging.integrity import (
    validate_image_file_bytes,
    check_image_file_integrity,
    detect_image_format_from_bytes,
)
from app.imaging.exif import (
    extract_exif_metadata,
    check_exif_metadata,
)
from app.imaging.gps import (
    validate_gps_coordinates,
    haversine_distance_km,
    check_gps_coordinate_validity,
    check_gps_location_consistency,
)
from app.imaging.hashing import (
    compute_phash_from_bytes,
    compute_phash_from_image,
    hamming_distance,
    find_similar_images_in_database,
    check_phash_cross_case_reuse,
    check_same_case_duplicate,
)
from app.imaging.embeddings import (
    generate_embedding_from_bytes,
    generate_embedding_from_image,
    cosine_similarity,
    find_top_k_similar_embeddings,
    check_embedding_visual_similarity,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_DIMENSION,
)
from app.imaging.verification import (
    ImageVerificationService,
    image_verification_service,
    check_image_timestamp_consistency,
    _IMAGE_VERIFICATION_CACHE,
    _IMAGE_RECORDS_CACHE,
)

__all__ = [
    "validate_image_file_bytes",
    "check_image_file_integrity",
    "detect_image_format_from_bytes",
    "extract_exif_metadata",
    "check_exif_metadata",
    "validate_gps_coordinates",
    "haversine_distance_km",
    "check_gps_coordinate_validity",
    "check_gps_location_consistency",
    "compute_phash_from_bytes",
    "compute_phash_from_image",
    "hamming_distance",
    "find_similar_images_in_database",
    "check_phash_cross_case_reuse",
    "check_same_case_duplicate",
    "check_image_timestamp_consistency",
    "ImageVerificationService",
    "image_verification_service",
    "_IMAGE_VERIFICATION_CACHE",
    "_IMAGE_RECORDS_CACHE",
]
