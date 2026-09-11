from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class InvoiceLineItem(BaseModel):
    id: Optional[str] = None
    item_description: str
    hsn_code: Optional[str] = None
    quantity: float
    unit_price: float
    total_amount: float
    serial_numbers: Optional[List[str]] = None


class InvoiceBase(BaseModel):
    case_id: str
    dealer_id: str
    invoice_number: str
    invoice_date: datetime
    total_amount: float
    tax_amount: Optional[float] = None


class InvoiceCreate(InvoiceBase):
    file_path: Optional[str] = None
    line_items: List[InvoiceLineItem] = []


class InvoiceResponse(InvoiceBase):
    id: str
    file_path: Optional[str] = None
    verification_status: str = "pending"
    created_at: datetime
    line_items: List[InvoiceLineItem] = []

    model_config = {"from_attributes": True}


class ImageBase(BaseModel):
    case_id: str
    image_type: str  # e.g., 'installation_wide', 'nameplate', 'geo_tag', 'serial_barcode'


class ImageCreate(ImageBase):
    file_path: str
    original_filename: str
    file_size_bytes: Optional[int] = None


class ImageResponse(ImageBase):
    id: str
    file_path: str
    original_filename: str
    file_size_bytes: Optional[int] = None
    status: str = "uploaded"
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskSignalResponse(BaseModel):
    id: str
    case_id: str
    category: str
    signal_name: str
    severity: str
    confidence_score: float
    evidence_payload: Dict[str, Any]
    description: str
    created_at: datetime


class RiskScoreResponse(BaseModel):
    id: str
    case_id: str
    overall_score: int  # 0 - 100
    risk_level: str
    price_anomaly_score: int
    image_anomaly_score: int
    dealer_network_score: int
    serial_anomaly_score: int
    summary_reasoning: str
    calculated_at: datetime


class VerificationTaskCreate(BaseModel):
    case_id: str
    task_type: str
    assigned_to: Optional[str] = None
    instructions: Optional[str] = None


class VerificationTaskUpdate(BaseModel):
    status: Optional[str] = None
    findings: Optional[str] = None
    completed_at: Optional[datetime] = None


class VerificationTaskResponse(BaseModel):
    id: str
    case_id: str
    task_type: str
    status: str
    assigned_to: Optional[str] = None
    instructions: Optional[str] = None
    findings: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class PipelineRunRequest(BaseModel):
    case_id: str
    modules: Optional[List[str]] = ["all"]


class PipelineStatusResponse(BaseModel):
    case_id: str
    status: str
    current_stage: Optional[str] = None
    completed_stages: List[str] = []
    message: str
