from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime, timezone
import uuid

from app.schemas.case import CaseCreate, CaseResponse, CaseDetailResponse, RiskLevelEnum, CaseStatusEnum

router = APIRouter(tags=["Cases"])

# In-memory storage stub for Phase 1 (replaced with DB/Supabase in later phases)
_cases_store = {}


@router.get("/cases", response_model=List[CaseResponse])
async def list_cases():
    """
    List all asset verification cases.
    Returns list of cases with risk indicators and verification status.
    """
    return list(_cases_store.values())


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(case_in: CaseCreate):
    """
    Create a new asset verification case.
    Initial status is set to SUBMITTED with UNKNOWN risk until verification pipeline runs.
    """
    case_id = str(uuid.uuid4())
    case_number = f"CAS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(_cases_store)+1:03d}"
    
    new_case = CaseResponse(
        id=case_id,
        case_number=case_number,
        dealer_id=case_in.dealer_id,
        customer_id=case_in.customer_id,
        asset_type=case_in.asset_type,
        claimed_installation_address=case_in.claimed_installation_address,
        loan_amount=case_in.loan_amount,
        notes=case_in.notes,
        status=CaseStatusEnum.SUBMITTED,
        risk_level=RiskLevelEnum.UNKNOWN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    _cases_store[case_id] = new_case
    return new_case


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: str):
    """
    Retrieve full case details, evidence items, and risk breakdown.
    """
    if case_id not in _cases_store:
        # Provide clean placeholder response for seeded/known IDs or 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found."
        )
    base_case = _cases_store[case_id]
    from app.services.invoice_service import invoice_service
    invoices = invoice_service.list_invoices_for_case(case_id)
    return CaseDetailResponse(
        **base_case.model_dump(),
        invoices=invoices,
        installation_images=[],
        risk_signals=[],
        risk_score=None,
        verification_tasks=[]
    )
