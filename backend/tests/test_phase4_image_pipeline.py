import io
import pytest
from datetime import datetime, timezone, date
from PIL import Image, ImageDraw, ImageEnhance
import piexif
from fastapi.testclient import TestClient

from app.main import app
from app.imaging.integrity import (
    validate_image_file_bytes,
    check_image_file_integrity,
    detect_image_format_from_bytes,
)
from app.imaging.exif import (
    extract_exif_metadata,
    check_exif_metadata,
    _parse_dms_coordinate,
    _parse_exif_timestamp,
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
from app.imaging.verification import (
    image_verification_service,
    check_image_timestamp_consistency,
    _IMAGE_RECORDS_CACHE,
    _IMAGE_VERIFICATION_CACHE,
)
from app.verification.models import CheckStatusEnum, CheckSeverityEnum, CheckTypeEnum

client = TestClient(app)


def _create_synthetic_solar_panel_image_bytes(exif_dict=None, format="JPEG") -> bytes:
    """Helper to generate a clean synthetic solar panel image in memory with optional EXIF."""
    img = Image.new("RGB", (320, 240), color=(25, 45, 85))
    draw = ImageDraw.Draw(img)
    for x in range(20, 300, 35):
        for y in range(20, 220, 40):
            draw.rectangle([x, y, x + 30, y + 35], fill=(45, 95, 175), outline=(210, 210, 210), width=2)
    draw.line([(20, 120), (300, 120)], fill=(230, 230, 230), width=3)

    buf = io.BytesIO()
    if exif_dict and format.upper() == "JPEG":
        exif_bytes = piexif.dump(exif_dict)
        img.save(buf, format=format, exif=exif_bytes, quality=90)
    else:
        img.save(buf, format=format)
    return buf.getvalue()


def _create_synthetic_water_pump_image_bytes() -> bytes:
    """Helper to generate a distinct synthetic water pump image in memory."""
    img = Image.new("RGB", (320, 240), color=(20, 75, 40))
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 40, 240, 200], fill=(130, 150, 140), outline=(40, 40, 40), width=4)
    draw.rectangle([140, 20, 180, 50], fill=(70, 70, 70))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# =============================================================================
# 1. FILE INTEGRITY & MAGIC BYTES TESTS
# =============================================================================

def test_image_integrity_valid_jpeg():
    raw_bytes = _create_synthetic_solar_panel_image_bytes(format="JPEG")
    is_valid, err, meta = validate_image_file_bytes(raw_bytes, "panel.jpg", "image/jpeg")
    assert is_valid is True
    assert err is None
    assert meta["detected_format"] == "JPEG"
    assert meta["dimensions"] == [320, 240]

    check = check_image_file_integrity(raw_bytes, "panel.jpg", "image/jpeg")
    assert check.status == CheckStatusEnum.PASS
    assert check.check_type == CheckTypeEnum.IMAGE_FILE_INTEGRITY


def test_image_integrity_valid_png_and_webp():
    png_bytes = _create_synthetic_solar_panel_image_bytes(format="PNG")
    assert detect_image_format_from_bytes(png_bytes) == "PNG"
    is_valid, _, meta = validate_image_file_bytes(png_bytes, "panel.png", "image/png")
    assert is_valid is True
    assert meta["detected_format"] == "PNG"

    webp_bytes = _create_synthetic_solar_panel_image_bytes(format="WEBP")
    assert detect_image_format_from_bytes(webp_bytes) == "WEBP"
    is_valid_w, _, meta_w = validate_image_file_bytes(webp_bytes, "panel.webp", "image/webp")
    assert is_valid_w is True
    assert meta_w["detected_format"] == "WEBP"


def test_corrupt_image_handled_safely():
    corrupt_bytes = b"\xff\xd8\xff\xe0" + b"random corrupt binary payload not real image"
    is_valid, err, _ = validate_image_file_bytes(corrupt_bytes, "corrupt.jpg", "image/jpeg")
    assert is_valid is False
    assert "Corrupted" in err or "decode" in err

    check = check_image_file_integrity(corrupt_bytes, "corrupt.jpg", "image/jpeg")
    assert check.status == CheckStatusEnum.ANOMALY
    assert check.severity == CheckSeverityEnum.HIGH


def test_unsupported_extension_rejected():
    raw_bytes = b"echo 'malicious script'"
    is_valid, err, _ = validate_image_file_bytes(raw_bytes, "script.sh", "text/x-sh")
    assert is_valid is False
    assert "Unsupported image file extension" in err


def test_oversized_image_rejected():
    large_bytes = b"0" * (11 * 1024 * 1024)  # 11MB
    is_valid, err, _ = validate_image_file_bytes(large_bytes, "large.jpg", "image/jpeg")
    assert is_valid is False
    assert "exceeds maximum allowed limit" in err


# =============================================================================
# 2. EXIF EXTRACTION & SANITIZATION TESTS
# =============================================================================

def test_exif_extraction_with_valid_metadata():
    # 28°38'20.4"N 77°13'44.4"E (Delhi coordinates)
    # 28 deg + 38 min / 60 + 20.4 sec / 3600 = 28.6390
    # 77 deg + 13 min / 60 + 44.4 sec / 3600 = 77.2290
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: "N",
        piexif.GPSIFD.GPSLatitude: ((28, 1), (38, 1), (204, 10)),
        piexif.GPSIFD.GPSLongitudeRef: "E",
        piexif.GPSIFD.GPSLongitude: ((77, 1), (13, 1), (444, 10)),
    }
    zeroth_ifd = {
        piexif.ImageIFD.Make: "Nikon",
        piexif.ImageIFD.Model: "D850 Pro",
        piexif.ImageIFD.Software: "Ver.1.20\x00\x01",  # Test control character stripping
        piexif.ImageIFD.DateTime: "2026:01:20 14:35:00",
    }
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: "2026:01:20 14:35:00"
    }

    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd}
    img_bytes = _create_synthetic_solar_panel_image_bytes(exif_dict=exif_dict)

    meta = extract_exif_metadata(img_bytes)
    assert meta["has_exif"] is True
    assert meta["camera_make"] == "Nikon"
    assert meta["camera_model"] == "D850 Pro"
    assert "Ver.1.20" in meta["software"]
    assert meta["capture_timestamp"] == "2026-01-20T14:35:00"
    assert meta["gps_lat"] is not None
    assert abs(meta["gps_lat"] - 28.6390) < 0.001
    assert abs(meta["gps_lng"] - 77.2290) < 0.001

    check = check_exif_metadata(meta)
    assert check.status == CheckStatusEnum.PASS
    assert check.check_type == CheckTypeEnum.EXIF_METADATA


def test_missing_exif_is_strictly_inconclusive():
    img_bytes = _create_synthetic_solar_panel_image_bytes()  # No EXIF
    meta = extract_exif_metadata(img_bytes)
    assert meta["has_exif"] is False

    check = check_exif_metadata(meta)
    assert check.status == CheckStatusEnum.INCONCLUSIVE
    assert "Missing EXIF does not prove image manipulation" in check.message


# =============================================================================
# 3. GPS BOUNDARY & HAVERSINE DISTANCE TESTS
# =============================================================================

def test_gps_coordinate_boundaries():
    assert validate_gps_coordinates(28.6139, 77.2090)[0] is True
    assert validate_gps_coordinates(95.0, 77.2090)[0] is False  # Lat > 90
    assert validate_gps_coordinates(28.6139, 195.0)[0] is False  # Lng > 180
    assert validate_gps_coordinates(None, 77.0)[0] is False

    valid_check = check_gps_coordinate_validity(28.6139, 77.2090)
    assert valid_check.status == CheckStatusEnum.PASS

    invalid_check = check_gps_coordinate_validity(95.0, 77.2090)
    assert invalid_check.status == CheckStatusEnum.ANOMALY


def test_haversine_gps_within_threshold_passes():
    # Photo: Delhi Connaught Place (28.6315, 77.2167)
    # Claimed: Delhi Barakhamba (28.6290, 77.2220) (~0.6 km apart)
    check = check_gps_location_consistency(
        photo_lat=28.6315,
        photo_lng=77.2167,
        ref_lat=28.6290,
        ref_lng=77.2220,
        threshold_km=1.0
    )
    assert check.status == CheckStatusEnum.PASS
    assert check.evidence["distance_km"] < 1.0
    assert check.check_type == CheckTypeEnum.GPS_LOCATION_CONSISTENCY


def test_haversine_gps_outside_threshold_produces_anomaly():
    # Photo: Delhi (28.6139, 77.2090)
    # Claimed Site: Jaipur (26.9124, 75.7873) (~235 km away)
    check = check_gps_location_consistency(
        photo_lat=28.6139,
        photo_lng=77.2090,
        ref_lat=26.9124,
        ref_lng=75.7873,
        threshold_km=1.0
    )
    assert check.status == CheckStatusEnum.ANOMALY
    assert check.severity == CheckSeverityEnum.HIGH
    assert check.evidence["distance_km"] > 200.0
    assert "exceeds threshold" in check.message
    # Verify no fraud claim
    assert "spoof" not in check.message.lower()


def test_missing_reference_gps_is_inconclusive():
    check = check_gps_location_consistency(
        photo_lat=28.6139,
        photo_lng=77.2090,
        ref_lat=None,
        ref_lng=None,
        threshold_km=1.0
    )
    assert check.status == CheckStatusEnum.INCONCLUSIVE
    assert "No reference installation coordinates" in check.message


# =============================================================================
# 4. pHASH EMPIRICAL & REUSE DETECTION TESTS
# =============================================================================

def test_phash_computation_deterministic():
    img_bytes = _create_synthetic_solar_panel_image_bytes()
    h1 = compute_phash_from_bytes(img_bytes)
    h2 = compute_phash_from_bytes(img_bytes)
    assert h1 is not None
    assert len(h1) == 16
    assert h1 == h2
    assert hamming_distance(h1, h2) == 0


def test_exact_phash_cross_case_duplicate_anomaly():
    base_bytes = _create_synthetic_solar_panel_image_bytes()
    h_base = compute_phash_from_bytes(base_bytes)

    candidates = [
        {
            "id": "IMG-OLD-001",
            "case_id": "CAS-2025-099",  # Different case
            "phash": h_base,
            "created_at": "2025-11-01T10:00:00Z"
        }
    ]

    cross_matches, same_matches = find_similar_images_in_database(
        current_image_id="IMG-CURR-002",
        current_case_id="CAS-2026-001",
        current_phash=h_base,
        candidate_images=candidates,
        threshold=6
    )
    assert len(cross_matches) == 1
    assert cross_matches[0]["hamming_distance"] == 0

    check = check_phash_cross_case_reuse(
        current_image_id="IMG-CURR-002",
        current_case_id="CAS-2026-001",
        current_phash=h_base,
        cross_case_matches=cross_matches,
        threshold=6
    )
    assert check.status == CheckStatusEnum.ANOMALY
    assert check.severity == CheckSeverityEnum.HIGH
    assert check.evidence["matching_case_id"] == "CAS-2025-099"
    assert "Exact perceptual match" in check.message
    # Must not claim fraud
    assert "fraud" not in check.message.lower()


def test_near_phash_resized_and_recompressed_images():
    base_img = Image.open(io.BytesIO(_create_synthetic_solar_panel_image_bytes()))
    h_base = compute_phash_from_image(base_img)

    # 1. Resized 50%
    resized = base_img.resize((160, 120))
    h_resized = compute_phash_from_image(resized)
    dist_resize = hamming_distance(h_base, h_resized)
    assert dist_resize <= 4

    # 2. 5% Crop
    w, h = base_img.size
    crop_img = base_img.crop((int(w * 0.025), int(h * 0.025), int(w * 0.975), int(h * 0.975)))
    h_crop = compute_phash_from_image(crop_img)
    dist_crop = hamming_distance(h_base, h_crop)
    assert dist_crop <= 8

    # 3. High quality vs low quality recompression
    buf_low = io.BytesIO()
    base_img.save(buf_low, format="JPEG", quality=35)
    buf_low.seek(0)
    h_low = compute_phash_from_image(Image.open(buf_low))
    dist_low = hamming_distance(h_base, h_low)
    assert dist_low <= 8


def test_distinct_equipment_phash_passes():
    solar_bytes = _create_synthetic_solar_panel_image_bytes()
    pump_bytes = _create_synthetic_water_pump_image_bytes()

    h_solar = compute_phash_from_bytes(solar_bytes)
    h_pump = compute_phash_from_bytes(pump_bytes)

    dist = hamming_distance(h_solar, h_pump)
    assert dist >= 18  # Distinct scenes have high Hamming distance

    candidates = [
        {
            "id": "IMG-PUMP-001",
            "case_id": "CAS-2025-088",
            "phash": h_pump,
            "created_at": "2025-10-15T10:00:00Z"
        }
    ]

    cross_matches, _ = find_similar_images_in_database(
        current_image_id="IMG-SOLAR-001",
        current_case_id="CAS-2026-001",
        current_phash=h_solar,
        candidate_images=candidates,
        threshold=6
    )
    assert len(cross_matches) == 0

    check = check_phash_cross_case_reuse(
        current_image_id="IMG-SOLAR-001",
        current_case_id="CAS-2026-001",
        current_phash=h_solar,
        cross_case_matches=cross_matches,
        threshold=6
    )
    assert check.status == CheckStatusEnum.PASS


def test_same_case_duplicate_image_is_pass_info():
    base_bytes = _create_synthetic_solar_panel_image_bytes()
    h_base = compute_phash_from_bytes(base_bytes)

    candidates = [
        {
            "id": "IMG-SAME-001",
            "case_id": "CAS-2026-001",  # SAME case
            "phash": h_base,
            "created_at": "2026-01-15T10:00:00Z"
        }
    ]

    _, same_matches = find_similar_images_in_database(
        current_image_id="IMG-SAME-002",
        current_case_id="CAS-2026-001",
        current_phash=h_base,
        candidate_images=candidates,
        threshold=6
    )
    assert len(same_matches) == 1

    check = check_same_case_duplicate(
        current_image_id="IMG-SAME-002",
        current_case_id="CAS-2026-001",
        same_case_matches=same_matches
    )
    assert check.status == CheckStatusEnum.PASS
    assert check.severity == CheckSeverityEnum.INFO
    assert "installation photo detected within the same case" in check.message


# =============================================================================
# 5. TIMESTAMP CONSISTENCY TESTS
# =============================================================================

def test_timestamp_consistency_valid_timeline():
    # Photo taken 2026-01-20, Invoice dated 2026-01-15 (+5 days) -> PASS
    check = check_image_timestamp_consistency(
        capture_ts_str="2026-01-20T14:30:00",
        invoice_date_str="2026-01-15",
        case_created_at_str="2026-01-15T09:00:00Z"
    )
    assert check.status == CheckStatusEnum.PASS
    assert check.evidence["delta_days"] == 5


def test_timestamp_prior_to_invoice_passes_with_policy_note():
    # Photo taken 2024-06-10, Invoice dated 2026-01-15 -> PASS with policy note (not an anomaly)
    check = check_image_timestamp_consistency(
        capture_ts_str="2024-06-10T11:00:00",
        invoice_date_str="2026-01-15",
        case_created_at_str="2026-01-15T09:00:00Z"
    )
    assert check.status == CheckStatusEnum.PASS
    assert check.severity == CheckSeverityEnum.INFO
    assert "Pre-invoice equipment staging" in check.message


def test_impossible_timestamp_anomaly():
    # Photo with uncalibrated/impossible year (e.g. 2005)
    check = check_image_timestamp_consistency(
        capture_ts_str="2005-06-10T11:00:00",
        invoice_date_str="2026-01-15"
    )
    assert check.status == CheckStatusEnum.ANOMALY
    assert "impossible or uncalibrated year" in check.message


def test_missing_timestamp_is_inconclusive():
    check = check_image_timestamp_consistency(
        capture_ts_str=None,
        invoice_date_str="2026-01-15"
    )
    assert check.status == CheckStatusEnum.INCONCLUSIVE


# =============================================================================
# 6. END-TO-END IMAGE VERIFICATION & API IDEMPOTENCY
# =============================================================================

def test_full_image_verification_lifecycle_and_idempotency():
    # Prepare image with GPS and EXIF
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: "N",
        piexif.GPSIFD.GPSLatitude: ((28, 1), (38, 1), (0, 1)),
        piexif.GPSIFD.GPSLongitudeRef: "E",
        piexif.GPSIFD.GPSLongitude: ((77, 1), (13, 1), (0, 1)),
    }
    zeroth_ifd = {
        piexif.ImageIFD.Make: "Canon",
        piexif.ImageIFD.Model: "EOS R6",
        piexif.ImageIFD.DateTime: "2026:01:18 10:15:00",
    }
    exif_dict = {"0th": zeroth_ifd, "Exif": {piexif.ExifIFD.DateTimeOriginal: "2026:01:18 10:15:00"}, "GPS": gps_ifd}
    img_bytes = _create_synthetic_solar_panel_image_bytes(exif_dict=exif_dict)

    # 1. Upload image via API
    upload_res = client.post(
        "/api/v1/images",
        data={"case_id": "CAS-2026-001", "image_type": "installation_wide"},
        files={"file": ("site_photo_01.jpg", img_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 201
    uploaded_data = upload_res.json()
    image_id = uploaded_data["id"]
    assert uploaded_data["case_id"] == "CAS-2026-001"
    assert uploaded_data["phash"] is not None

    # 2. Run Verification via API
    verif_res = client.post(f"/api/v1/verification/image/{image_id}")
    assert verif_res.status_code == 200
    summary = verif_res.json()
    assert summary["image_id"] == image_id
    assert summary["total_checks"] == 7
    assert summary["verification_status"] == "completed"

    # 3. Verify Idempotency - running second time returns same results without duplicating
    verif_res2 = client.post(f"/api/v1/verification/image/{image_id}")
    assert verif_res2.status_code == 200
    summary2 = verif_res2.json()
    assert summary2["total_checks"] == summary["total_checks"]
    assert summary2["passed_count"] == summary["passed_count"]

    # 4. Get verification results via GET
    get_res = client.get(f"/api/v1/verification/image/{image_id}")
    assert get_res.status_code == 200
    assert get_res.json()["image_id"] == image_id

    # 5. Get signed download URL
    url_res = client.get(f"/api/v1/images/{image_id}/download-url")
    assert url_res.status_code == 200
    assert "download_url" in url_res.json()


def test_zero_final_risk_score_created_in_phase4():
    """Verify that Phase 4 verification signals have weight = 0 and no 0-100 risk score is computed."""
    img_bytes = _create_synthetic_solar_panel_image_bytes()
    summary = image_verification_service.run_image_verification(
        image_id="IMG-TEST-SCORE-001",
        case_id="CAS-2026-001",
        filename="panel.jpg",
        file_bytes=img_bytes,
        mime_type="image/jpeg"
    )
    for signal in summary.signals_generated:
        assert signal["weight"] == 0
        assert "score" not in signal
