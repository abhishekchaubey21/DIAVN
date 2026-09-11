import asyncio
import logging
from typing import Optional

from app.core.config import settings
from app.workflow.models import WorkflowEventPayload, DeliveryResult
from app.workflow.service import workflow_service, WorkflowService

logger = logging.getLogger(__name__)


class OutboxDispatcher:
    """
    Lightweight, durable outbox dispatcher.
    Polls workflow_events outbox, atomically claims pending records,
    and dispatches signed events to n8n webhook without blocking DIAVN core.
    """
    def __init__(self, service: Optional[WorkflowService] = None):
        self.service = service or workflow_service
        self._is_running = False

    async def dispatch_next_event(self) -> bool:
        """
        Claims and dispatches a single pending or retry-pending event.
        Returns True if an event was processed, False if the queue was empty.
        """
        record = self.service.claim_next_pending_event()
        if not record:
            return False

        try:
            # Reconstruct strongly typed payload from outbox dictionary
            payload = WorkflowEventPayload(**record.payload)
            delivery_result = await self.service.adapter.dispatch_event(payload)
            self.service.update_event_status(record.event_id, delivery_result)
            return True
        except Exception as e:
            logger.error(f"Error during event {record.event_id} dispatch: {e}")
            self.service.update_event_status(
                record.event_id,
                DeliveryResult(success=False, error_message=str(e))
            )
            return True

    async def drain_pending_queue(self, max_batch: int = 50) -> int:
        """
        Drains all currently eligible events in the outbox up to max_batch.
        Used for restart recovery and deterministic test executions.
        """
        processed_count = 0
        for _ in range(max_batch):
            did_process = await self.dispatch_next_event()
            if not did_process:
                break
            processed_count += 1
        return processed_count

    async def start_polling_loop(self, poll_interval_sec: Optional[float] = None):
        """
        Background polling loop for FastAPI lifespan.
        """
        interval = poll_interval_sec or settings.WORKFLOW_POLL_INTERVAL_SEC
        self._is_running = True
        logger.info(f"Started workflow outbox dispatcher (interval: {interval}s)")

        # Initial recovery sweep on startup
        try:
            recovered = await self.drain_pending_queue()
            if recovered > 0:
                logger.info(f"Recovered and processed {recovered} pending outbox events on startup.")
        except Exception as e:
            logger.warning(f"Startup outbox recovery note: {e}")

        while self._is_running:
            try:
                await self.dispatch_next_event()
            except Exception as e:
                logger.debug(f"Dispatcher polling error: {e}")
            await asyncio.sleep(interval)

    def stop_polling_loop(self):
        self._is_running = False


outbox_dispatcher = OutboxDispatcher()
