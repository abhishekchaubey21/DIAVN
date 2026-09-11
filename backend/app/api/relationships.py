from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.graph.models import (
    CaseRelationshipAnalysisResponse,
    DealerConcentrationSummary,
    RelationshipGraphResponse
)
from app.graph.service import relationship_service

router = APIRouter(prefix="/relationships", tags=["Entity Relationships & Network Analysis"])


@router.get("/cases/{case_id}", response_model=CaseRelationshipAnalysisResponse)
async def get_case_relationships(case_id: str):
    """
    Retrieve deterministic relationship analysis and entity links for a specific case.
    Categorizes results into Structural Links, Observed Evidence Links, and Potential Anomalies.
    """
    try:
        return relationship_service.get_case_relationships(case_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case relationships: {str(e)}"
        )


@router.post("/cases/{case_id}/analyze", response_model=CaseRelationshipAnalysisResponse)
async def analyze_case_relationships(case_id: str):
    """
    Triggers deterministic relationship analysis for the specified case.
    """
    try:
        return relationship_service.analyze_and_persist_case_relationships(case_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze case relationships: {str(e)}"
        )


@router.get("/dealers/{dealer_id}", response_model=DealerConcentrationSummary)
async def get_dealer_relationships(dealer_id: str):
    """
    Retrieve descriptive dealer relationship concentration statistics and shared attribute clusters.
    Does not produce a dealer fraud score.
    """
    try:
        return relationship_service.get_dealer_concentration(dealer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dealer concentration summary: {str(e)}"
        )


@router.get("/cases/{case_id}/graph", response_model=RelationshipGraphResponse)
async def get_case_graph(case_id: str):
    """
    Retrieve node and edge graph projection for interactive frontend network visualization.
    """
    try:
        return relationship_service.get_case_graph(case_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate case graph: {str(e)}"
        )


@router.get("/dealers/{dealer_id}/graph", response_model=RelationshipGraphResponse)
async def get_dealer_graph(dealer_id: str):
    """
    Retrieve dealer-centric node and edge network graph.
    """
    try:
        return relationship_service.get_dealer_graph(dealer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dealer graph: {str(e)}"
        )
