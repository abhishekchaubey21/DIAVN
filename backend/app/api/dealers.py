from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime, timezone
import uuid

from app.schemas.dealer import DealerCreate, DealerResponse, DealerDetailResponse

router = APIRouter(tags=["Dealers"])

# Synthetic dealers for Phase 1 stub data
_dealers_store = {
    "DLR-001": DealerResponse(
        id="DLR-001",
        dealer_code="APX-SLR-001",
        name="Apex Solar Equipment Pvt Ltd",
        business_name="Apex Solar Solutions",
        gstin="27AAACA1234A1Z5",
        pan="AAACA1234A",
        cin="U40106MH2018PTC309812",
        address="Plot 45, MIDC Industrial Area, Phase II",
        city="Pune",
        state="Maharashtra",
        pincode="411019",
        contact_email="compliance@apexsolar.synthetic",
        contact_phone="+91-9823000001",
        status="active",
        risk_tier="low",
        total_cases=14,
        flagged_cases=0,
        created_at=datetime.now(timezone.utc)
    ),
    "DLR-002": DealerResponse(
        id="DLR-002",
        dealer_code="SUN-PWR-002",
        name="SunPower Retail & Infra Solutions",
        business_name="SunPower Infra",
        gstin="24BBBCB5678B1Z2",
        pan="BBBCB5678B",
        cin="U40300GJ2020PTC412098",
        address="12, Commercial Hub, Ring Road",
        city="Surat",
        state="Gujarat",
        pincode="395002",
        contact_email="accounts@sunpowerinfra.synthetic",
        contact_phone="+91-9823000002",
        status="under_review",
        risk_tier="medium",
        total_cases=9,
        flagged_cases=3,
        created_at=datetime.now(timezone.utc)
    ),
    "DLR-003": DealerResponse(
        id="DLR-003",
        dealer_code="RAD-AGR-003",
        name="Radiant AgroTech Distributions",
        business_name="Radiant Agro Dist",
        gstin="29CCCC09876C1Z9",
        pan="CCCC09876C",
        cin="U01100KA2022PTC567432",
        address="88, Agro Yard Extension, Hebbal",
        city="Bengaluru",
        state="Karnataka",
        pincode="560024",
        contact_email="ops@radiantagrotech.synthetic",
        contact_phone="+91-9823000003",
        status="flagged",
        risk_tier="high",
        total_cases=18,
        flagged_cases=8,
        created_at=datetime.now(timezone.utc)
    )
}


@router.get("/dealers", response_model=List[DealerResponse])
async def list_dealers():
    """
    List all registered dealers with their risk profile and verification summary.
    """
    return list(_dealers_store.values())


@router.get("/dealers/{dealer_id}", response_model=DealerDetailResponse)
async def get_dealer(dealer_id: str):
    """
    Get detailed dealer record with associated case and asset counts.
    """
    dealer = _dealers_store.get(dealer_id)
    if not dealer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dealer {dealer_id} not found."
        )
    return DealerDetailResponse(
        **dealer.model_dump(),
        active_cases=[],
        registered_assets=[],
        entity_relationships=[]
    )
