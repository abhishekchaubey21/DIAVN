import hmac
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.workflow.models import WorkflowEventPayload, DeliveryResult

logger = logging.getLogger(__name__)


def compute_canonical_signature(raw_body: str, timestamp: str, secret: str) -> str:
    """
    Computes canonical HMAC-SHA256 signature for DIAVN webhooks.
    Canonical format: HMAC_SHA256(timestamp + "." + raw_body, secret)
    """
    signing_input = f"{timestamp}.{raw_body}".encode("utf-8")
    key = secret.encode("utf-8")
    return hmac.new(key, signing_input, hashlib.sha256).hexdigest()


def verify_canonical_signature(
    raw_body: str,
    timestamp_str: str,
    signature_header: str,
    secret: str,
    max_age_seconds: int = 300
) -> Tuple[bool, Optional[str]]:
    """
    Verifies canonical HMAC signature using constant-time comparison and 5-minute replay window check.
    Returns (is_valid, error_reason).
    """
    if not signature_header or not timestamp_str:
        return False, "Missing signature or timestamp header."

    # Parse and validate timestamp
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = abs((now - ts).total_seconds())
        if age > max_age_seconds:
            return False, f"Timestamp is outside acceptable replay window ({age:.1f}s > {max_age_seconds}s)."
    except Exception as e:
        return False, f"Invalid timestamp format: {e}"

    # Extract signature digest
    expected_prefix = "sha256="
    provided_sig = signature_header
    if provided_sig.startswith(expected_prefix):
        provided_sig = provided_sig[len(expected_prefix):]

    expected_sig = compute_canonical_signature(raw_body, timestamp_str, secret)
    if not hmac.compare_digest(provided_sig, expected_sig):
        return False, "Signature mismatch."

    return True, None


class BaseNotificationAdapter(ABC):
    """Abstract interface for dispatching notification events."""
    
    @abstractmethod
    async def dispatch_event(self, event_payload: WorkflowEventPayload) -> DeliveryResult:
        pass


class WebhookNotificationAdapter(BaseNotificationAdapter):
    """
    Dispatches signed HMAC-SHA256 HTTP POST requests to configured n8n webhook URL.
    """
    def __init__(self, webhook_url: Optional[str] = None, secret: Optional[str] = None, timeout_sec: float = 3.0):
        self.webhook_url = webhook_url or settings.N8N_WEBHOOK_URL
        self.secret = secret or settings.DIAVN_WEBHOOK_SECRET
        self.timeout_sec = timeout_sec

    async def dispatch_event(self, event_payload: WorkflowEventPayload) -> DeliveryResult:
        if not self.webhook_url:
            logger.info("No webhook URL configured; skipping HTTP dispatch.")
            return DeliveryResult(
                success=True,
                status_code=200,
                response_body='{"status": "skipped", "message": "No webhook URL configured"}'
            )

        raw_body = json.dumps(event_payload.model_dump(), default=str)
        timestamp = event_payload.timestamp or datetime.now(timezone.utc).isoformat()
        signature = compute_canonical_signature(raw_body, timestamp, self.secret)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DIAVN-Workflow-Dispatcher/1.0",
            "X-DIAVN-Signature": f"sha256={signature}",
            "X-DIAVN-Timestamp": timestamp,
            "X-DIAVN-Event-ID": event_payload.event_id,
            "X-DIAVN-Event-Type": event_payload.event_type.value
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(self.webhook_url, content=raw_body, headers=headers)
                
                resp_text = resp.text
                is_duplicate = False
                try:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("status") == "duplicate_suppressed":
                        is_duplicate = True
                except Exception:
                    pass

                if 200 <= resp.status_code < 300:
                    return DeliveryResult(
                        success=True,
                        status_code=resp.status_code,
                        response_body=resp_text,
                        is_duplicate=is_duplicate
                    )
                else:
                    return DeliveryResult(
                        success=False,
                        status_code=resp.status_code,
                        response_body=resp_text,
                        error_message=f"HTTP {resp.status_code}: {resp_text[:200]}"
                    )
        except httpx.ConnectError as e:
            logger.warning(f"Connection failed to n8n webhook at {self.webhook_url}: {e}")
            return DeliveryResult(
                success=False,
                error_message=f"Webhook connection error: {str(e)}"
            )
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout calling n8n webhook at {self.webhook_url}: {e}")
            return DeliveryResult(
                success=False,
                error_message=f"Webhook timeout ({self.timeout_sec}s exceeded)"
            )
        except Exception as e:
            logger.error(f"Unexpected error dispatching to n8n webhook: {e}")
            return DeliveryResult(
                success=False,
                error_message=f"Unexpected dispatch error: {str(e)}"
            )


class ConsoleNotificationAdapter(BaseNotificationAdapter):
    """Zero-cost local console & structured logger adapter."""

    async def dispatch_event(self, event_payload: WorkflowEventPayload) -> DeliveryResult:
        logger.info(
            f"[DIAVN OPERATIONAL ALERT] Case: {event_payload.case_number} | "
            f"Score: {event_payload.risk_score} ({event_payload.risk_band}) | "
            f"Action: {event_payload.recommended_action} | "
            f"URL: {event_payload.case_url}"
        )
        return DeliveryResult(
            success=True,
            status_code=200,
            response_body='{"status": "logged_to_console"}'
        )


class MockEmailNotificationAdapter(BaseNotificationAdapter):
    """
    Generates structured RFC 822 format notification message for offline/local demonstration.
    """
    def __init__(self):
        self.sent_messages = []

    async def dispatch_event(self, event_payload: WorkflowEventPayload) -> DeliveryResult:
        subject = f"[DIAVN ALERT] Case {event_payload.case_number}: Verification Review Required"
        body = (
            f"To: underwriting-desk@diavn.internal\n"
            f"From: notifications@diavn.internal\n"
            f"Subject: {subject}\n"
            f"Date: {event_payload.timestamp}\n\n"
            f"Case: {event_payload.case_number}\n"
            f"Risk Score: {event_payload.risk_score}/100 (Band: {event_payload.risk_band})\n"
            f"Status: {event_payload.recommended_action}\n"
            f"Anomalies: {', '.join(event_payload.top_anomalies) if event_payload.top_anomalies else 'None'}\n"
            f"Verification Task: {event_payload.verification_task_id or 'N/A'}\n"
            f"Review URL: {event_payload.case_url}\n"
        )
        self.sent_messages.append({"subject": subject, "body": body, "event_id": event_payload.event_id})
        return DeliveryResult(
            success=True,
            status_code=200,
            response_body=json.dumps({"status": "mock_email_rendered", "subject": subject})
        )
