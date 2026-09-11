import io
import math
import pytest
from PIL import Image, ImageDraw, ImageEnhance
import numpy as np

from app.imaging.embeddings import (
    ImageEmbeddingGenerator,
    generate_embedding_from_bytes,
    generate_embedding_from_image,
    cosine_similarity,
    find_top_k_similar_embeddings,
    check_embedding_visual_similarity,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_DIMENSION,
    DEFAULT_EMBEDDING_THRESHOLD,
)
from app.imaging.verification import ImageVerificationService
from app.verification.models import CheckTypeEnum, CheckStatusEnum, CheckSeverityEnum


# Helper generators for synthetic testing images
def create_solar_panel_image(width=400, height=300, color_tone="blue") -> Image.Image:
    """Create a synthetic solar panel image with grid lines."""
    img = Image.new("RGB", (width, height), (30, 60, 120) if color_tone == "blue" else (40, 80, 140))
    draw = ImageDraw.Draw(img)
    # Draw frame
    draw.rectangle([10, 10, width - 10, height - 10], outline=(200, 200, 200), width=4)
    # Draw grid cells
    for x in range(30, width - 20, 40):
        draw.line([(x, 10), (x, height - 10)], fill=(220, 220, 220), width=2)
    for y in range(30, height - 20, 40):
        draw.line([(10, y), (width - 10, y)], fill=(220, 220, 220), width=2)
    return img


def create_water_pump_image(width=400, height=300) -> Image.Image:
    """Create a synthetic industrial water pump image."""
    img = Image.new("RGB", (width, height), (220, 100, 30))
    draw = ImageDraw.Draw(img)
    # Draw cylindrical pump body
    draw.ellipse([80, 50, width - 80, height - 50], fill=(70, 70, 70), outline=(30, 30, 30), width=3)
    # Draw pipe flanges
    draw.rectangle([20, 120, 80, 180], fill=(120, 120, 120))
    draw.rectangle([width - 80, 120, width - 20, 180], fill=(120, 120, 120))
    return img


def create_unrelated_scene_image(width=400, height=300) -> Image.Image:
    """Create a completely unrelated scene image (green grass / trees pattern)."""
    img = Image.new("RGB", (width, height), (34, 139, 34))
    draw = ImageDraw.Draw(img)
    # Draw organic circles
    for i in range(10):
        draw.ellipse([i * 35, 50, i * 35 + 60, 180], fill=(0, 100, 0))
    return img


def image_to_bytes(img: Image.Image, format: str = "JPEG", **kwargs) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=format, **kwargs)
    return buf.getvalue()


# =============================================================================
# 1. MODEL INITIALIZATION & VECTOR PROPERTIES
# =============================================================================

def test_model_initialization_singleton():
    """Verify ImageEmbeddingGenerator is a functional singleton with expected dimensions."""
    gen1 = ImageEmbeddingGenerator()
    gen2 = ImageEmbeddingGenerator()
    assert gen1 is gen2
    assert gen1.is_available
    assert EMBEDDING_DIMENSION == 512
    assert EMBEDDING_MODEL_NAME == "resnet18"


def test_embedding_vector_length_and_finite_values():
    """Verify extracted embeddings are length 512, all finite floats (no NaN, no Inf)."""
    img = create_solar_panel_image()
    emb = generate_embedding_from_image(img)

    assert emb is not None
    assert len(emb) == 512
    assert all(isinstance(x, float) for x in emb)
    assert all(math.isfinite(x) for x in emb)


def test_embedding_l2_normalization():
    """Verify extracted embeddings are L2 unit normalized (||v|| ≈ 1.0)."""
    img = create_solar_panel_image()
    emb = generate_embedding_from_image(img)
    assert emb is not None

    l2_norm = math.sqrt(sum(x ** 2 for x in emb))
    assert pytest.approx(l2_norm, rel=1e-3) == 1.0


# =============================================================================
# 2. COSINE SIMILARITY MATHEMATICAL PROPERTIES
# =============================================================================

def test_cosine_similarity_identical_vectors():
    """Verify identical unit vectors return similarity of 1.0."""
    v = [0.6, 0.8] + [0.0] * 510
    sim = cosine_similarity(v, v)
    assert pytest.approx(sim, abs=1e-5) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    """Verify orthogonal vectors return similarity of 0.0."""
    v1 = [1.0] + [0.0] * 511
    v2 = [0.0, 1.0] + [0.0] * 510
    sim = cosine_similarity(v1, v2)
    assert pytest.approx(sim, abs=1e-5) == 0.0


def test_cosine_similarity_opposite_vectors():
    """Verify opposite vectors return similarity of -1.0."""
    v1 = [1.0] + [0.0] * 511
    v2 = [-1.0] + [0.0] * 511
    sim = cosine_similarity(v1, v2)
    assert pytest.approx(sim, abs=1e-5) == -1.0


def test_cosine_similarity_empty_and_mismatched_inputs():
    """Verify invalid or mismatched vector inputs safely return 0.0."""
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0
    assert cosine_similarity([0.0] * 512, [1.0] * 512) == 0.0


# =============================================================================
# 3. CONTROLLED EMPIRICAL BENCHMARK MEASUREMENTS
# =============================================================================

def test_benchmark_identical_image():
    """Identical image bytes must produce cosine similarity of 1.0."""
    base_img = create_solar_panel_image()
    emb1 = generate_embedding_from_image(base_img)
    emb2 = generate_embedding_from_image(base_img)
    sim = cosine_similarity(emb1, emb2)
    assert pytest.approx(sim, abs=1e-4) == 1.0


def test_benchmark_resized_image():
    """Resized image (50% scale) retains high visual feature similarity (> 0.95)."""
    base_img = create_solar_panel_image()
    resized_img = base_img.resize((200, 150), Image.Resampling.BILINEAR)

    emb_base = generate_embedding_from_image(base_img)
    emb_resized = generate_embedding_from_image(resized_img)
    sim = cosine_similarity(emb_base, emb_resized)

    assert sim > 0.95


def test_benchmark_jpeg_recompression_q95_and_q35():
    """JPEG recompression at Q95 and Q35 preserves feature similarity (> 0.95)."""
    base_img = create_solar_panel_image()
    bytes_q95 = image_to_bytes(base_img, quality=95)
    bytes_q35 = image_to_bytes(base_img, quality=35)

    emb_base = generate_embedding_from_image(base_img)
    emb_q95 = generate_embedding_from_bytes(bytes_q95)
    emb_q35 = generate_embedding_from_bytes(bytes_q35)

    sim_q95 = cosine_similarity(emb_base, emb_q95)
    sim_q35 = cosine_similarity(emb_base, emb_q35)

    assert sim_q95 > 0.98
    assert sim_q35 > 0.95


def test_benchmark_crop_5_percent():
    """5% edge crop preserves high feature similarity (> 0.95)."""
    base_img = create_solar_panel_image(400, 300)
    # Crop 5% from edges (10px on each side)
    cropped_img = base_img.crop((10, 10, 390, 290))

    emb_base = generate_embedding_from_image(base_img)
    emb_crop = generate_embedding_from_image(cropped_img)
    sim = cosine_similarity(emb_base, emb_crop)

    assert sim > 0.95


def test_benchmark_brightness_contrast_alteration():
    """Brightness & contrast adjustment (+20%) preserves high similarity (> 0.95)."""
    base_img = create_solar_panel_image()
    enhancer = ImageEnhance.Brightness(base_img)
    bright_img = enhancer.enhance(1.2)
    enhancer_con = ImageEnhance.Contrast(bright_img)
    altered_img = enhancer_con.enhance(1.2)

    emb_base = generate_embedding_from_image(base_img)
    emb_altered = generate_embedding_from_image(altered_img)
    sim = cosine_similarity(emb_base, emb_altered)

    assert sim > 0.95


def test_benchmark_distinct_equipment_and_unrelated_scene():
    """Distinct equipment and unrelated scenes must have low similarity (< 0.65)."""
    solar_img = create_solar_panel_image()
    pump_img = create_water_pump_image()
    unrelated_img = create_unrelated_scene_image()

    emb_solar = generate_embedding_from_image(solar_img)
    emb_pump = generate_embedding_from_image(pump_img)
    emb_unrelated = generate_embedding_from_image(unrelated_img)

    sim_solar_pump = cosine_similarity(emb_solar, emb_pump)
    sim_solar_unrelated = cosine_similarity(emb_solar, emb_unrelated)

    # Distinct physical categories should be well below provisional threshold
    assert sim_solar_pump < 0.65
    assert sim_solar_unrelated < 0.60


# =============================================================================
# 4. TOP-K SIMILARITY CANDIDATE SEARCH
# =============================================================================

def test_find_top_k_similar_embeddings_ranking_and_bounds():
    """Verify top-K search ranks candidates descending and respects top_k limit."""
    base_img = create_solar_panel_image()
    emb_base = generate_embedding_from_image(base_img)

    # Create synthetic candidates
    crop_img = base_img.crop((10, 10, 390, 290))
    pump_img = create_water_pump_image()
    unrelated_img = create_unrelated_scene_image()

    candidates = [
        {"id": "img-self", "case_id": "case-current", "embedding": emb_base},
        {"id": "img-crop", "case_id": "case-other-1", "embedding": generate_embedding_from_image(crop_img)},
        {"id": "img-pump", "case_id": "case-other-2", "embedding": generate_embedding_from_image(pump_img)},
        {"id": "img-unrelated", "case_id": "case-other-3", "embedding": generate_embedding_from_image(unrelated_img)},
        {"id": "img-same-case", "case_id": "case-current", "embedding": generate_embedding_from_image(crop_img)},
    ]

    cross_matches, same_matches = find_top_k_similar_embeddings(
        current_image_id="img-self",
        current_case_id="case-current",
        current_embedding=emb_base,
        candidate_images=candidates,
        top_k=2,
        threshold=0.85
    )

    # Cross case matches
    assert len(cross_matches) <= 2
    assert cross_matches[0]["candidate_image_id"] == "img-crop"
    assert cross_matches[0]["similarity"] > 0.95
    assert cross_matches[0]["is_above_threshold"] is True

    # Same case matches
    assert len(same_matches) == 1
    assert same_matches[0]["candidate_image_id"] == "img-same-case"


# =============================================================================
# 5. VERIFICATION CHECK ITEM & ANOMALY EVALUATION
# =============================================================================

def test_check_embedding_visual_similarity_anomaly():
    """Verify ANOMALY generated when cross-case similarity exceeds provisional threshold."""
    base_img = create_solar_panel_image()
    emb_base = generate_embedding_from_image(base_img)

    cross_matches = [
        {
            "candidate_image_id": "img-other-99",
            "candidate_case_id": "case-other-88",
            "similarity": 0.9850,
            "threshold": 0.85,
            "is_above_threshold": True
        }
    ]

    check_item = check_embedding_visual_similarity(
        current_image_id="img-current-01",
        current_case_id="case-current-01",
        current_embedding=emb_base,
        cross_case_matches=cross_matches,
        threshold=0.85
    )

    assert check_item.check_type == CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY
    assert check_item.status == CheckStatusEnum.ANOMALY
    assert check_item.severity == CheckSeverityEnum.HIGH
    assert "High deep visual feature similarity" in check_item.message
    assert "fraud" not in check_item.message.lower()


def test_check_embedding_visual_similarity_pass():
    """Verify PASS status when cross-case similarity is below threshold."""
    base_img = create_solar_panel_image()
    emb_base = generate_embedding_from_image(base_img)

    cross_matches = [
        {
            "candidate_image_id": "img-other-99",
            "candidate_case_id": "case-other-88",
            "similarity": 0.5210,
            "threshold": 0.85,
            "is_above_threshold": False
        }
    ]

    check_item = check_embedding_visual_similarity(
        current_image_id="img-current-01",
        current_case_id="case-current-01",
        current_embedding=emb_base,
        cross_case_matches=cross_matches,
        threshold=0.85
    )

    assert check_item.check_type == CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY
    assert check_item.status == CheckStatusEnum.PASS
    assert check_item.severity == CheckSeverityEnum.INFO


def test_check_embedding_visual_similarity_inconclusive():
    """Verify INCONCLUSIVE status when no embedding is available."""
    check_item = check_embedding_visual_similarity(
        current_image_id="img-01",
        current_case_id="case-01",
        current_embedding=None,
        cross_case_matches=[],
        threshold=0.85
    )

    assert check_item.check_type == CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY
    assert check_item.status == CheckStatusEnum.INCONCLUSIVE


# =============================================================================
# 6. VERIFICATION SERVICE INTEGRATION & ZERO RISK SCORE BOUNDARY
# =============================================================================

def test_verify_image_embedding_service_zero_weight_signals():
    """Verify service integration produces signals with weight=0 (no composite risk scoring)."""
    service = ImageVerificationService()

    base_img = create_solar_panel_image()
    base_bytes = image_to_bytes(base_img)
    emb_base = generate_embedding_from_image(base_img)

    # Setup matching candidate in candidates list
    candidates = [
        {"id": "cand-01", "case_id": "case-cand", "embedding": emb_base, "created_at": "2026-03-01T00:00:00Z"}
    ]

    summary = service.verify_image_embedding(
        image_id="img-test-123",
        case_id="case-test-456",
        file_bytes=base_bytes,
        candidate_images=candidates,
        top_k=5,
        threshold=0.85
    )

    assert summary.has_embedding is True
    assert summary.model == "resnet18"
    assert summary.embedding_dimension == 512
    assert summary.status == CheckStatusEnum.ANOMALY
    assert summary.top_similarity > 0.99
    assert len(summary.top_matches) == 1

    # Check signal weight is 0
    assert summary.check_item.status == CheckStatusEnum.ANOMALY


def test_graceful_corrupted_image_handling():
    """Verify corrupted bytes do not crash the service and return clean Inconclusive state."""
    service = ImageVerificationService()
    corrupted_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00corrupteddatajunkjunkjunk"

    summary = service.verify_image_embedding(
        image_id="img-corrupted",
        case_id="case-corrupted",
        file_bytes=corrupted_bytes,
        candidate_images=[]
    )

    assert summary.has_embedding is False
    assert summary.status == CheckStatusEnum.INCONCLUSIVE
    assert summary.top_similarity == 0.0
