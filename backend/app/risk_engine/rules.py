from typing import Dict, Tuple
from app.risk_engine.models import EvidenceGroupEnum, RiskBandEnum

POLICY_VERSION = "risk-v1"

# =============================================================================
# 1. INITIAL POLICY WEIGHTS (Configurable policy baseline, not statistical probabilities)
# =============================================================================
DEFAULT_POLICY_WEIGHTS: Dict[str, int] = {
    # High Significance
    "DUPLICATE_SERIAL": 35,
    "SERIAL_NUMBER_FORMAT": 15,
    "INVOICE_PRICE_ANOMALY": 20,
    "PRICE_BENCHMARK_MATCH": 20,
    "IMAGE_PHASH_REUSE": 20,
    "IMAGE_IMAGE_PHASH_REUSE": 20,
    "IMAGE_EMBEDDING_SIMILARITY": 15,
    
    # Medium Significance
    "GPS_MISMATCH": 12,
    "IMAGE_GPS_LOCATION_CONSISTENCY": 12,
    "DEALER_RELATIONSHIP_ANOMALY": 15,
    "CASE_ENTITY_CONSISTENCY": 15,
    "INVOICE_ARITHMETIC": 15,
    
    # Low / Metadata Significance
    "MISSING_EXIF": 8,
    "IMAGE_EXIF_METADATA": 8,
    "IMAGE_TIMESTAMP_CONSISTENCY": 10,
    "IMAGE_FILE_INTEGRITY": 10,
    "IMAGE_GPS_COORDINATE_VALIDITY": 8,
    "LOW_EXTRACTION_CONFIDENCE": 5,
    "REQUIRED_EVIDENCE_FIELDS": 5,
    
    # Zero Contribution (Non-risk or informational)
    "IMAGE_SAME_CASE_DUPLICATE": 0,
}

# =============================================================================
# 2. EVIDENCE GROUP MAPPING FOR DEDUPLICATION & CAPPING
# =============================================================================
SIGNAL_GROUP_MAPPING: Dict[str, EvidenceGroupEnum] = {
    "DUPLICATE_SERIAL": EvidenceGroupEnum.SERIAL,
    "SERIAL_NUMBER_FORMAT": EvidenceGroupEnum.SERIAL,
    "SERIAL_PRESENCE": EvidenceGroupEnum.SERIAL,
    
    "INVOICE_PRICE_ANOMALY": EvidenceGroupEnum.INVOICE_PRICE,
    "PRICE_BENCHMARK_MATCH": EvidenceGroupEnum.INVOICE_PRICE,
    
    "IMAGE_PHASH_REUSE": EvidenceGroupEnum.IMAGE_REUSE,
    "IMAGE_IMAGE_PHASH_REUSE": EvidenceGroupEnum.IMAGE_REUSE,
    "IMAGE_EMBEDDING_SIMILARITY": EvidenceGroupEnum.IMAGE_REUSE,
    "IMAGE_SAME_CASE_DUPLICATE": EvidenceGroupEnum.IMAGE_REUSE,
    
    "GPS_MISMATCH": EvidenceGroupEnum.LOCATION,
    "IMAGE_GPS_LOCATION_CONSISTENCY": EvidenceGroupEnum.LOCATION,
    "IMAGE_GPS_COORDINATE_VALIDITY": EvidenceGroupEnum.LOCATION,
    
    "MISSING_EXIF": EvidenceGroupEnum.METADATA,
    "IMAGE_EXIF_METADATA": EvidenceGroupEnum.METADATA,
    "IMAGE_TIMESTAMP_CONSISTENCY": EvidenceGroupEnum.METADATA,
    "IMAGE_FILE_INTEGRITY": EvidenceGroupEnum.METADATA,
    
    "LOW_EXTRACTION_CONFIDENCE": EvidenceGroupEnum.EXTRACTION,
    "INVOICE_ARITHMETIC": EvidenceGroupEnum.EXTRACTION,
    "CASE_ENTITY_CONSISTENCY": EvidenceGroupEnum.EXTRACTION,
    "REQUIRED_EVIDENCE_FIELDS": EvidenceGroupEnum.EXTRACTION,
    
    "DEALER_RELATIONSHIP_ANOMALY": EvidenceGroupEnum.DEALER,
}

# =============================================================================
# 3. EVIDENCE GROUP MAXIMUM CONTRIBUTION CAPS (Anti-Double-Counting)
# =============================================================================
DEFAULT_GROUP_CAPS: Dict[EvidenceGroupEnum, int] = {
    EvidenceGroupEnum.SERIAL: 35,          # Duplicate serial condition contributes at most 35
    EvidenceGroupEnum.INVOICE_PRICE: 25,   # Price anomalies capped at 25
    EvidenceGroupEnum.IMAGE_REUSE: 25,     # pHash (20) + embedding (15) capped at 25 to prevent double-counting
    EvidenceGroupEnum.LOCATION: 20,        # Location anomalies capped at 20
    EvidenceGroupEnum.METADATA: 10,        # Metadata / EXIF anomalies capped at 10
    EvidenceGroupEnum.EXTRACTION: 15,      # Extraction / arithmetic anomalies capped at 15
    EvidenceGroupEnum.DEALER: 25,          # Dealer network anomalies capped at 25
    EvidenceGroupEnum.OTHER: 20,
}

# =============================================================================
# 4. TOTAL SCORE CAP & RISK BANDS
# =============================================================================
TOTAL_SCORE_CAP = 100

RISK_BANDS: Dict[RiskBandEnum, Tuple[int, int]] = {
    RiskBandEnum.LOW: (0, 39),
    RiskBandEnum.MEDIUM: (40, 69),
    RiskBandEnum.HIGH: (70, 100),
}

# =============================================================================
# 5. DETERMINISTIC RECOMMENDED ACTIONS
# =============================================================================
RECOMMENDED_ACTIONS: Dict[RiskBandEnum, str] = {
    RiskBandEnum.LOW: "No immediate additional verification indicated by the configured DIAVN rules.",
    RiskBandEnum.MEDIUM: "Additional document/evidence review recommended.",
    RiskBandEnum.HIGH: "Field verification recommended.",
}


def get_risk_band_for_score(score: int) -> RiskBandEnum:
    """
    Map score in [0, 100] to categorical risk band.
    """
    if score >= 70:
        return RiskBandEnum.HIGH
    elif score >= 40:
        return RiskBandEnum.MEDIUM
    else:
        return RiskBandEnum.LOW


def get_recommended_action_for_band(band: RiskBandEnum) -> str:
    """
    Retrieve workflow recommendation for a risk band.
    """
    return RECOMMENDED_ACTIONS.get(band, "Additional document/evidence review recommended.")
