import io
import logging
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image
import numpy as np

import torch
import torchvision.models as models
import torchvision.transforms as transforms

from app.verification.models import (
    VerificationCheckItem,
    CheckTypeEnum,
    CheckStatusEnum,
    CheckSeverityEnum,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "resnet18"
EMBEDDING_MODEL_VERSION = "1.0"
EMBEDDING_DIMENSION = 512
DEFAULT_EMBEDDING_THRESHOLD = 0.85


class ImageEmbeddingGenerator:
    """
    Singleton deep visual feature embedding generator using lightweight local ResNet-18 (512-dim).
    Runs 100% locally on CPU with zero external APIs.
    """
    _instance: Optional["ImageEmbeddingGenerator"] = None
    _model: Optional[torch.nn.Module] = None
    _preprocess: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageEmbeddingGenerator, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        try:
            logger.info("Initializing local ResNet-18 deep visual feature extractor...")
            # Load pretrained ResNet-18
            base_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
            # Remove classification head to output raw 512-dim feature vector
            base_model.fc = torch.nn.Identity()
            base_model.eval()
            self._model = base_model

            # Standard ImageNet preprocessing pipeline
            self._preprocess = transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.CenterCrop((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            logger.info("ResNet-18 feature extractor loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ResNet-18 model: {e}")
            self._model = None
            self._preprocess = None

    @property
    def is_available(self) -> bool:
        return self._model is not None and self._preprocess is not None

    def extract_embedding(self, img: Image.Image) -> Optional[List[float]]:
        """
        Extract L2-normalized 512-dimensional deep visual feature vector from PIL Image.
        """
        if not self.is_available:
            self._initialize_model()
            if not self.is_available:
                return None

        try:
            rgb_img = img.convert("RGB")
            tensor = self._preprocess(rgb_img).unsqueeze(0)

            with torch.no_grad():
                features = self._model(tensor)
                # L2-normalization ensuring unit sphere vector
                norm_features = features / torch.norm(features, p=2, dim=-1, keepdim=True)

            vector = norm_features.squeeze(0).cpu().numpy().tolist()
            return vector
        except Exception as e:
            logger.warning(f"Error during embedding inference: {e}")
            return None


_embedding_generator = ImageEmbeddingGenerator()


def generate_embedding_from_bytes(file_bytes: bytes) -> Optional[List[float]]:
    """
    Generate 512-dim visual feature vector from image bytes.
    """
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            return _embedding_generator.extract_embedding(img)
    except Exception as e:
        logger.warning(f"Could not open image bytes for embedding generation: {e}")
        return None


def generate_embedding_from_image(img: Image.Image) -> Optional[List[float]]:
    """
    Generate 512-dim visual feature vector directly from a PIL Image.
    """
    return _embedding_generator.extract_embedding(img)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate mathematically exact cosine similarity between two feature vectors:
    cos(A, B) = (A · B) / (||A|| * ||B||)
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    dot = np.dot(a, b)
    similarity = float(dot / (norm_a * norm_b))
    # Clamp to [-1.0, 1.0] for precision safety
    return max(-1.0, min(1.0, similarity))


def find_top_k_similar_embeddings(
    current_image_id: str,
    current_case_id: str,
    current_embedding: Optional[List[float]],
    candidate_images: List[Dict[str, Any]],
    top_k: int = 5,
    threshold: Optional[float] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Search candidate images by cosine similarity.
    Returns (cross_case_matches, same_case_matches) sorted descending by similarity.
    """
    sim_threshold = threshold if threshold is not None else getattr(settings, "EMBEDDING_SIMILARITY_THRESHOLD", DEFAULT_EMBEDDING_THRESHOLD)

    if not current_embedding or len(current_embedding) != EMBEDDING_DIMENSION:
        return [], []

    cross_case_candidates = []
    same_case_candidates = []

    for cand in candidate_images:
        cand_id = cand.get("id")
        cand_case_id = cand.get("case_id")
        cand_emb = cand.get("embedding")

        if not cand_emb or cand_id == current_image_id or len(cand_emb) != EMBEDDING_DIMENSION:
            continue

        sim = cosine_similarity(current_embedding, cand_emb)

        match_item = {
            "candidate_image_id": cand_id,
            "candidate_case_id": cand_case_id,
            "similarity": round(sim, 4),
            "threshold": sim_threshold,
            "is_above_threshold": sim >= sim_threshold,
            "match_type": "cross_case" if cand_case_id != current_case_id else "same_case",
            "model": EMBEDDING_MODEL_NAME,
            "model_version": EMBEDDING_MODEL_VERSION,
            "dimension": EMBEDDING_DIMENSION,
            "created_at": cand.get("created_at")
        }

        if cand_case_id == current_case_id:
            same_case_candidates.append(match_item)
        else:
            cross_case_candidates.append(match_item)

    # Sort descending by similarity
    cross_case_candidates.sort(key=lambda x: x["similarity"], reverse=True)
    same_case_candidates.sort(key=lambda x: x["similarity"], reverse=True)

    return cross_case_candidates[:top_k], same_case_candidates[:top_k]


def check_embedding_visual_similarity(
    current_image_id: str,
    current_case_id: str,
    current_embedding: Optional[List[float]],
    cross_case_matches: List[Dict[str, Any]],
    threshold: Optional[float] = None
) -> VerificationCheckItem:
    """
    Produce structured VerificationCheckItem for IMAGE_EMBEDDING_SIMILARITY.
    Evaluates deep visual feature similarity without claiming fraud.
    """
    sim_limit = threshold if threshold is not None else getattr(settings, "EMBEDDING_SIMILARITY_THRESHOLD", DEFAULT_EMBEDDING_THRESHOLD)

    if not current_embedding:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY,
            check_name="Deep Visual Feature Embedding Cross-Case Similarity",
            status=CheckStatusEnum.INCONCLUSIVE,
            severity=CheckSeverityEnum.INFO,
            message="No visual feature embedding available for deep similarity search.",
            evidence={"embedding_available": False, "model": EMBEDDING_MODEL_NAME}
        )

    if not cross_case_matches:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY,
            check_name="Deep Visual Feature Embedding Cross-Case Similarity",
            status=CheckStatusEnum.PASS,
            severity=CheckSeverityEnum.INFO,
            message=f"No visually similar installation images detected in database (provisional threshold: cos >= {sim_limit:.2f}).",
            evidence={
                "model": EMBEDDING_MODEL_NAME,
                "dimension": EMBEDDING_DIMENSION,
                "top_similarity": 0.0,
                "threshold": sim_limit,
                "matches_found": 0
            }
        )

    top_match = cross_case_matches[0]
    top_sim = top_match["similarity"]

    evidence_payload = {
        "current_image_id": current_image_id,
        "current_case_id": current_case_id,
        "matching_image_id": top_match["candidate_image_id"],
        "matching_case_id": top_match["candidate_case_id"],
        "cosine_similarity": top_sim,
        "provisional_threshold": sim_limit,
        "model": EMBEDDING_MODEL_NAME,
        "model_version": EMBEDDING_MODEL_VERSION,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "top_matches": cross_case_matches[:3],
        "registry_scope": "internal_lender_records"
    }

    if top_sim >= sim_limit:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY,
            check_name="Deep Visual Feature Embedding Cross-Case Similarity",
            status=CheckStatusEnum.ANOMALY,
            severity=CheckSeverityEnum.HIGH,
            message=f"High deep visual feature similarity ({top_sim:.4f}) detected with installation image from case #{top_match['candidate_case_id']}. Requires underwriter review.",
            evidence=evidence_payload
        )
    else:
        return VerificationCheckItem(
            check_type=CheckTypeEnum.IMAGE_EMBEDDING_SIMILARITY,
            check_name="Deep Visual Feature Embedding Cross-Case Similarity",
            status=CheckStatusEnum.PASS,
            severity=CheckSeverityEnum.INFO,
            message=f"Visual feature similarity ({top_sim:.4f}) is below provisional review threshold ({sim_limit:.2f}).",
            evidence=evidence_payload
        )
