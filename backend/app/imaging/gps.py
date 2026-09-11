import math
import logging
from typing import Optional, Tuple, Dict, Any
from app.verification.models import (
    VerificationCheckItem,
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


def validate_gps_coordinates(lat: Optional[float], lng: Optional[float]) -> Tuple[bool, Optional[str]]:
    """
    Validate that latitude and longitude are within standard geographical boundaries.
    """
    if lat is None or lng is None:
        return False, "GPS coordinates are absent."

    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        return False, "GPS coordinates must be numeric."

    if math.isnan(lat) or math.isnan(lng) or math.isinf(lat) or math.isinf(lng):
        return False, "GPS coordinates contain NaN or infinite values."

    if lat < -90.0 or lat > 90.0:
        return False, f"Latitude {lat} is outside valid range [-90, +90]."

    if lng < -180.0 or lng > 180.0:
        return False, f"Longitude {lng} is outside valid range [-180, +180]."

    return True, None


def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth (in kilometers).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = EARTH_RADIUS_KM * c
    return round(distance, 4)


def check_gps_coordinate_validity(lat: Optional[float], lng: Optional[float]) -> VerificationCheckItem:
    """
    Produce structured check for GPS_COORDINATE_VALIDITY.
    """
    if lat is None or lng is None:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_COORDINATE_VALIDITY,
            check_name="Photo Geotag & Coordinate Boundary Validity",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="No GPS coordinates embedded in photo metadata. (Cannot verify geotag).",
            evidence={"has_gps": False}
        )

    is_valid, err_msg = validate_gps_coordinates(lat, lng)
    if not is_valid:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_COORDINATE_VALIDITY,
            check_name="Photo Geotag & Coordinate Boundary Validity",
            status=CheckStatusEnum.ANOMALY,
            severity=CheckSeverityEnum.MEDIUM,
            message=f"Embedded GPS coordinates are mathematically invalid: {err_msg}",
            evidence={"gps_lat": lat, "gps_lng": lng, "error": err_msg}
        )

    return VerificationCheckItem(
        check_type=CheckTypeEnum.GPS_COORDINATE_VALIDITY,
        check_name="Photo Geotag & Coordinate Boundary Validity",
        status=CheckStatusEnum.PASS,
        severity=CheckSeverityEnum.INFO,
        message=f"GPS coordinates ({lat:.5f}, {lng:.5f}) are mathematically valid and within standard boundaries.",
        evidence={"gps_lat": lat, "gps_lng": lng}
    )


def check_gps_location_consistency(
    photo_lat: Optional[float],
    photo_lng: Optional[float],
    ref_lat: Optional[float],
    ref_lng: Optional[float],
    threshold_km: Optional[float] = None
) -> VerificationCheckItem:
    """
    Produce structured check for GPS_LOCATION_CONSISTENCY.
    Compares photo coordinates vs reference case coordinates via Haversine.
    Zero external APIs.
    """
    limit_km = threshold_km or settings.MAX_INSTALLATION_DISTANCE_KM

    # If photo GPS is missing
    if photo_lat is None or photo_lng is None:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_LOCATION_CONSISTENCY,
            check_name="Installation Site GPS Distance Consistency",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="Photo contains no GPS coordinates for site distance comparison.",
            evidence={"photo_gps_available": False}
        )

    # If case reference GPS is missing
    if ref_lat is None or ref_lng is None:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_LOCATION_CONSISTENCY,
            check_name="Installation Site GPS Distance Consistency",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="No reference installation coordinates available in case record for deterministic distance verification.",
            evidence={
                "photo_lat": photo_lat,
                "photo_lng": photo_lng,
                "reference_gps_available": False
            }
        )

    # Validate both sets of coordinates
    is_photo_valid, _ = validate_gps_coordinates(photo_lat, photo_lng)
    is_ref_valid, _ = validate_gps_coordinates(ref_lat, ref_lng)

    if not is_photo_valid or not is_ref_valid:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_LOCATION_CONSISTENCY,
            check_name="Installation Site GPS Distance Consistency",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.LOW,
            message="Cannot compute distance due to invalid coordinate boundaries.",
            evidence={
                "photo_lat": photo_lat,
                "photo_lng": photo_lng,
                "ref_lat": ref_lat,
                "ref_lng": ref_lng
            }
        )

    dist_km = haversine_distance_km(photo_lat, photo_lng, ref_lat, ref_lng)

    evidence = {
        "photo_lat": photo_lat,
        "photo_lng": photo_lng,
        "reference_lat": ref_lat,
        "reference_lng": ref_lng,
        "distance_km": dist_km,
        "threshold_km": limit_km
    }

    if dist_km <= limit_km:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_LOCATION_CONSISTENCY,
            check_name="Installation Site GPS Distance Consistency",
            status=CheckStatusEnum.PASS,
            severity=CheckSeverityEnum.INFO,
            message=f"Photo GPS is within {dist_km:.2f} km of claimed installation site (allowed threshold: {limit_km:.1f} km).",
            evidence=evidence
        )
    else:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.GPS_LOCATION_CONSISTENCY,
            check_name="Installation Site GPS Distance Consistency",
            status=CheckStatusEnum.ANOMALY,
            severity=CheckSeverityEnum.HIGH,
            message=f"Photo GPS is {dist_km:.2f} km away from claimed installation site (exceeds threshold of {limit_km:.1f} km).",
            evidence=evidence
        )
