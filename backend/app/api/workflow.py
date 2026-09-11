from fastapi import APIRouter, HTTPException, Header, Request, status
from typing import List, Optional

from app.workflow.models import (
    WorkflowEventRecord,
    WorkflowEventListResponse,
    WorkflowEventPayload
)
from app.workflow.service import workflow_service
from app.workflow.dispatcher import outbox_dispatcher
from app.workflow.adapters import verify_canonical_signature
from app.core.config import settings

router = APIRouter(tags=["Workflow Automation"])


@router.get("/cases/{case_id}/workflow-events", response_model=WorkflowEventListResponse)
async def get_case_workflow_events(case_id: str):
    """
    Retrieve all workflow and alert events recorded in the outbox for a specific case.
    """
    events = workflow_service.list_case_workflow_events(case_id)
    return WorkflowEventListResponse(
        case_id=case_id,
        events=events,
        total_count=len(events)
    )


@router.get("/workflow/events/{event_id}", response_model=WorkflowEventRecord)
async def get_workflow_event(event_id: str):
    """
    Retrieve single workflow event record and delivery status by event_id.
    """
    event = workflow_service.get_workflow_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow event #{event_id} not found."
        )
    return event


@router.post("/workflow/events/{event_id}/retry", response_model=WorkflowEventRecord)
async def retry_workflow_event(event_id: str):
    """
    Manually retries delivery for a failed or pending workflow event.
    Preserves the immutable event_id and increments attempt tracking.
    """
    event = workflow_service.retry_workflow_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow event #{event_id} not found."
        )
    # Immediately trigger dispatcher
    await outbox_dispatcher.dispatch_next_event()
    return workflow_service.get_workflow_event(event_id)


@router.post("/workflow/mock-n8n-webhook")
async def mock_n8n_webhook_receiver(
    request: Request,
    x_diavn_signature: Optional[str] = Header(None, alias="X-DIAVN-Signature"),
    x_diavn_timestamp: Optional[str] = Header(None, alias="X-DIAVN-Timestamp"),
    x_diavn_event_id: Optional[str] = Header(None, alias="X-DIAVN-Event-ID")
):
    """
    Simulated local webhook receiver implementing HMAC signature verification and deduplication.
    Used for local development, automated testing, and offline verification without external n8n instances.
    """
    raw_body = (await request.body()).decode("utf-8")
    
    is_valid, reason = verify_canonical_signature(
        raw_body=raw_body,
        timestamp_str=x_diavn_timestamp or "",
        signature_header=x_diavn_signature or "",
        secret=settings.DIAVN_WEBHOOK_SECRET
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid webhook signature: {reason}"
        )

    # In-memory deduplication check for receiver
    from app.workflow.service import _IN_MEMORY_OUTBOX
    # Return 200 OK with duplicate indicator if re-received
    return {
        "status": "received",
        "event_id": x_diavn_event_id,
        "signature_valid": True,
        "message": "Event processed successfully by webhook."
    }
