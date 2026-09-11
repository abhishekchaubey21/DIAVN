from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DealerBase(BaseModel):
    name: str
    business_name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str
    contact_email: str
    contact_phone: str


class DealerCreate(DealerBase):
    pass


class DealerResponse(DealerBase):
    id: str
    dealer_code: str
    status: str
    risk_tier: str
    total_cases: int = 0
    flagged_cases: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DealerDetailResponse(DealerResponse):
    active_cases: List[Dict[str, Any]] = []
    registered_assets: List[Dict[str, Any]] = []
    entity_relationships: List[Dict[str, Any]] = []
