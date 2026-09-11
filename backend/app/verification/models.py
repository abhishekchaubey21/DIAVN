from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CheckStatusEnum(str, Enum):
    PASS = "PASS"
    ANOMALY = "ANOMALY"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_CHECKED = "NOT_CHECKED"


class CheckSeverityEnum(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CheckTypeEnum(str, Enum):
    # Phase 3 Invoice Checks
    PRICE_BENCHMARK = "PRICE_BENCHMARK"
    SERIAL_PRESENCE_AND_FORMAT = "SERIAL_PRESENCE_AND_FORMAT"
    SERIAL_INTERNAL_DUPLICATE = "SERIAL_INTERNAL_DUPLICATE"
    SERIAL_SAME_INVOICE_DUPLICATE = "SERIAL_SAME_INVOICE_DUPLICATE"
    CASE_ENTITY_CONSISTENCY = "CASE_ENTITY_CONSISTENCY"
    INVOICE_ARITHMETIC = "INVOICE_ARITHMETIC"
    REQUIRED_EVIDENCE_FIELDS = "REQUIRED_EVIDENCE_FIELDS"
    
    # Phase 4 Installation Image Forensics Checks
    IMAGE_FILE_INTEGRITY = "IMAGE_FILE_INTEGRITY"
    EXIF_METADATA = "EXIF_METADATA"
    GPS_COORDINATE_VALIDITY = "GPS_COORDINATE_VALIDITY"
    GPS_LOCATION_CONSISTENCY = "GPS_LOCATION_CONSISTENCY"
    IMAGE_TIMESTAMP_CONSISTENCY = "IMAGE_TIMESTAMP_CONSISTENCY"
    IMAGE_PHASH_REUSE = "IMAGE_PHASH_REUSE"
    IMAGE_SAME_CASE_DUPLICATE = "IMAGE_SAME_CASE_DUPLICATE"
    
    # Phase 5 Deep Visual Feature Embedding Checks
    IMAGE_EMBEDDING_SIMILARITY = "IMAGE_EMBEDDING_SIMILARITY"


class VerificationCheckItem(BaseModel):
    check_type: CheckTypeEnum
    check_name: str
    status: CheckStatusEnum
    severity: CheckSeverityEnum = CheckSeverityEnum.INFO
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvoiceVerificationSummary(BaseModel):
    invoice_id: str
    case_id: str
    extraction_status: str
    verification_status: str  # e.g., 'completed'
    total_checks: int
    passed_count: int
    anomaly_count: int
    inconclusive_count: int
    checks: List[VerificationCheckItem] = []
    signals_generated: List[Dict[str, Any]] = []
    verified_at: datetime
    notes: str = "Deterministic consistency checks completed. Final composite risk scoring not yet computed."


class ImageVerificationSummary(BaseModel):
    image_id: str
    case_id: str
    original_filename: str
    image_type: str = "installation_wide"
    verification_status: str = "completed"
    total_checks: int
    passed_count: int
    anomaly_count: int
    inconclusive_count: int
    checks: List[VerificationCheckItem] = []
    signals_generated: List[Dict[str, Any]] = []
    exif_summary: Dict[str, Any] = Field(default_factory=dict)
    phash: Optional[str] = None
    embedding_summary: Optional[Dict[str, Any]] = None
    verified_at: datetime
    notes: str = "Deterministic installation image forensics completed. Final composite risk score not yet computed."


class EmbeddingVerificationSummary(BaseModel):
    image_id: str
    case_id: str
    model: str = "resnet18"
    model_version: str = "1.0"
    embedding_dimension: int = 512
    has_embedding: bool
    status: CheckStatusEnum
    top_similarity: float = 0.0
    threshold: float = 0.85
    top_matches: List[Dict[str, Any]] = []
    check_item: Optional[VerificationCheckItem] = None
    verified_at: datetime
    notes: str = "Deep visual feature similarity is evidence of visual similarity, not proof of fraudulent activity."
