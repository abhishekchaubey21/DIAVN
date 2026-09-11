import io
import re
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from PIL import Image, ExifTags
from app.verification.models import (
    VerificationCheckItem,
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
)

logger = logging.getLogger(__name__)


def _sanitize_string(val: Any, max_len: int = 100) -> Optional[str]:
    """
    Sanitize untrusted EXIF text values (strip control chars, truncate).
    """
    if val is None:
        return None
    s = str(val).strip()
    # Strip null bytes and non-printable control characters
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s[:max_len] if s else None


def _parse_dms_coordinate(coords: Any, ref: Optional[str]) -> Optional[float]:
    """
    Convert EXIF GPS coordinates (Degrees, Minutes, Seconds) to signed decimal degrees.
    Handles tuples/lists of IFDRational or numeric values.
    """
    try:
        if not coords or len(coords) < 3:
            return None

        def to_float(v):
            if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, (tuple, list)) and len(v) == 2:
                return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
            return float(v)

        deg = to_float(coords[0])
        minutes = to_float(coords[1])
        seconds = to_float(coords[2])

        decimal = deg + (minutes / 60.0) + (seconds / 3600.0)

        if ref and str(ref).strip().upper() in ("S", "W"):
            decimal = -decimal

        return round(decimal, 7)
    except Exception as e:
        logger.debug(f"Failed to parse GPS DMS coordinates: {e}")
        return None


def _parse_exif_timestamp(ts_str: Optional[str]) -> Optional[str]:
    """
    Safely parse EXIF timestamp string ('YYYY:MM:DD HH:MM:SS') into ISO 8601 string.
    """
    if not ts_str:
        return None
    cleaned = ts_str.strip()
    if cleaned.startswith("0000") or cleaned == "0000:00:00 00:00:00":
        return None

    # Common EXIF formats
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned[:19], fmt[:19])
            return dt.isoformat()
        except ValueError:
            continue

    return None


def extract_exif_metadata(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extract and sanitize all relevant EXIF metadata fields from raw image bytes.
    Returns structured dictionary with both raw/sanitized metadata and normalized fields.
    """
    result: Dict[str, Any] = {
        "has_exif": False,
        "capture_timestamp": None,
        "gps_lat": None,
        "gps_lng": None,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "orientation": None,
        "raw_exif": {}
    }

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            exif_data = img.getexif()
            if not exif_data:
                return result

            result["has_exif"] = True
            raw_dict = {}

            # Standard EXIF tags
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                raw_dict[tag_name] = str(value)[:200]

            result["camera_make"] = _sanitize_string(raw_dict.get("Make"))
            result["camera_model"] = _sanitize_string(raw_dict.get("Model"))
            result["software"] = _sanitize_string(raw_dict.get("Software"))
            result["orientation"] = raw_dict.get("Orientation")

            # Check capture date in primary tags or Exif sub-IFD
            dt_raw = raw_dict.get("DateTimeOriginal") or raw_dict.get("DateTime")
            
            # Check Exif sub-IFD (tag 0x8769 / 34665)
            if hasattr(exif_data, "get_ifd"):
                try:
                    exif_ifd = exif_data.get_ifd(0x8769)
                    if exif_ifd:
                        for sub_tag, sub_val in exif_ifd.items():
                            sub_name = ExifTags.TAGS.get(sub_tag, str(sub_tag))
                            raw_dict[sub_name] = str(sub_val)[:200]
                        if not dt_raw:
                            dt_raw = raw_dict.get("DateTimeOriginal") or raw_dict.get("DateTimeDigitized")
                except Exception:
                    pass

                # Check GPS sub-IFD (tag 0x8825 / 34853)
                try:
                    gps_ifd = exif_data.get_ifd(0x8825)
                    if gps_ifd:
                        gps_dict = {}
                        for g_tag, g_val in gps_ifd.items():
                            g_name = ExifTags.GPSTAGS.get(g_tag, str(g_tag))
                            gps_dict[g_name] = g_val

                        raw_dict["GPSInfo"] = {k: str(v)[:100] for k, v in gps_dict.items()}

                        lat_val = gps_dict.get("GPSLatitude")
                        lat_ref = gps_dict.get("GPSLatitudeRef")
                        lng_val = gps_dict.get("GPSLongitude")
                        lng_ref = gps_dict.get("GPSLongitudeRef")

                        result["gps_lat"] = _parse_dms_coordinate(lat_val, lat_ref)
                        result["gps_lng"] = _parse_dms_coordinate(lng_val, lng_ref)
                except Exception as e:
                    logger.debug(f"Error parsing GPS IFD: {e}")

            result["capture_timestamp"] = _parse_exif_timestamp(dt_raw)
            result["raw_exif"] = raw_dict

    except Exception as e:
        logger.warning(f"Error during EXIF extraction: {e}")

    return result


def check_exif_metadata(exif_summary: Dict[str, Any]) -> VerificationCheckItem:
    """
    Produce structured VerificationCheckItem for EXIF_METADATA.
    Missing EXIF is strictly INCONCLUSIVE (never anomaly/fraud).
    """
    if not exif_summary.get("has_exif"):
        return VerificationCheckItem(
            check_type=CheckTypeEnum.EXIF_METADATA,
            check_name="EXIF Telemetry & Camera Metadata Presence",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="No usable EXIF camera metadata found in image. (Note: Missing EXIF does not prove image manipulation).",
            evidence={"has_exif": False}
        )

    evidence_payload = {
        "camera_make": exif_summary.get("camera_make"),
        "camera_model": exif_summary.get("camera_model"),
        "software": exif_summary.get("software"),
        "capture_timestamp": exif_summary.get("capture_timestamp"),
        "has_gps": exif_summary.get("gps_lat") is not None and exif_summary.get("gps_lng") is not None
    }

    return VerificationCheckItem(
        check_type=CheckTypeEnum.EXIF_METADATA,
        check_name="EXIF Telemetry & Camera Metadata Presence",
        status=CheckStatusEnum.PASS,
        severity=CheckSeverityEnum.INFO,
        message=f"EXIF metadata successfully extracted (Camera: {exif_summary.get('camera_make') or 'Unknown'} {exif_summary.get('camera_model') or ''}, Captured: {exif_summary.get('capture_timestamp') or 'N/A'}).",
        evidence=evidence_payload
    )
