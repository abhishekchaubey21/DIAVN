# DIAVN Phase D — n8n Operational Workflow Integration

This directory contains the production-ready n8n workflow definitions for the **DIAVN (Dealer Integrity & Asset Verification Network)** event outbox automation subsystem.

---

## 1. Purpose
Converts authoritative Phase 6 **HIGH verification risk assessments** (`risk_score >= 70`) into operational field-verification actions:
1. Receives signed outbox events from the FastAPI backend.
2. Validates the **HMAC-SHA256 signature** and enforces a **5-minute replay window**.
3. Deduplicates events persistently using `event_id` to prevent double-dispatch.
4. Generates an operational field investigation dispatch package linking directly to the case dossier and the mobile capture interface (`/field/capture`).

---

## 2. Trigger Specification
- **HTTP Method:** `POST`
- **Path:** `/webhook/diavn-events` (or `/webhook-test/diavn-events` during testing)
- **Headers Required:**
  - `Content-Type: application/json`
  - `X-DIAVN-Signature: sha256=<canonical_hmac_sha256_hex>`
  - `X-DIAVN-Timestamp: <iso_8601_utc_timestamp>`
  - `X-DIAVN-Event-ID: <deterministic_event_id>`

---

## 3. Expected Payload Schema (`event-v1`)

```json
{
  "event_id": "EVT-CAS-2026-007-RUN8F1E-HIGH-RISK",
  "event_type": "CASE_VERIFICATION_HIGH_RISK",
  "event_version": "event-v1",
  "case_id": "55555555-5555-5555-5555-555555555507",
  "case_number": "CAS-2026-007",
  "pipeline_run_id": "8f1e92a1-3b4c-4d5e-6f7a-8b9c0d1e2f3a",
  "risk_score": 92,
  "risk_band": "HIGH",
  "recommended_action": "Multiple/high-significance verification anomalies detected; field verification recommended.",
  "top_anomalies": [
    "+35 Duplicate Serial (Serial number MIC-2025-0019 already registered in case CAS-2026-001)",
    "+20 Invoice Price Anomaly (Unit price exceeds benchmark by 26.0%)",
    "+25 Image Reuse Group (Exact pHash and deep visual embedding match with CAS-2026-001)",
    "+12 GPS Mismatch (Installation photo GPS distance exceeds 1.0 km threshold)"
  ],
  "verification_task_id": "TSK-CAS-2026-007-01",
  "case_url": "http://localhost:3000/cases/CAS-2026-007",
  "timestamp": "2026-09-11T23:50:00.000000Z"
}
```

---

## 4. Workflow Nodes Breakdown

| Node Name | Node Type | Purpose |
| :--- | :--- | :--- |
| **DIAVN Webhook Receiver** | `n8n-nodes-base.webhook` | Ingests signed POST event payload from FastAPI outbox dispatcher. |
| **Validate HMAC & Timestamp** | `n8n-nodes-base.function` | Computes canonical HMAC-SHA256 over `timestamp + "." + JSON.stringify(body)` and checks $\le 300\text{s}$ replay tolerance. |
| **Durable Deduplication** | `n8n-nodes-base.function` | Reads persistent `getWorkflowStaticData('global').processedEvents[eventId]` to prevent duplicate actions. |
| **Is High Risk & Not Duplicate?** | `n8n-nodes-base.if` | Routes events with `event_type == "CASE_VERIFICATION_HIGH_RISK"` and `risk_score >= 70` to operational queue. |
| **Dispatch Field Verification Task** | `n8n-nodes-base.function` | Packages field instructions, target coordinates, and direct `/field/capture?caseId=CAS-2026-007` mobile URL. |
| **Audit Log Only** | `n8n-nodes-base.function` | Records completed/low-risk or duplicate lifecycle events without alerting. |

---

## 5. Security & HMAC Verification

### Canonical Signature Formula
```
signature = HMAC_SHA256(timestamp + "." + raw_json_body, DIAVN_WEBHOOK_SECRET)
```

- **Environment Variable:** `DIAVN_WEBHOOK_SECRET` (default: `diavn-default-shared-secret-for-n8n-auth` in dev).
- **Replay Protection:** Rejects any request where $|t_{\text{server}} - t_{\text{header}}| > 300\text{ seconds}$.
- **Zero Raw PII:** Payload excludes customer personal identifiers (PII), bank details, or unmasked credentials.

---

## 6. How to Run & Import into Self-Hosted n8n

### Option A: Local Docker Compose (Community Edition)
```bash
# Start self-hosted n8n instance on port 5678
docker-compose -f docker-compose.n8n.yml up -d
```
1. Open `http://localhost:5678` in your browser.
2. Navigate to **Workflows → Import from File**.
3. Select `n8n/diavn_high_risk_field_verification.json`.
4. Click **Activate Workflow**.

### Option B: Test via FastAPI Built-in Receiver & Python Test Suite
The FastAPI test suite validates the exact HMAC signing and delivery pipeline:
```bash
python -m pytest backend/tests/test_phase9_workflow_automation.py -v
```

---

## 7. End-to-End Execution Trace for `CAS-2026-007`

1. **Risk Engine:** Phase 6 calculates authoritative score **`92`** (`HIGH`).
2. **Outbox Enqueue:** `WorkflowService.record_and_enqueue_event` creates `EVT-CAS-2026-007-...-HIGH-RISK`.
3. **Dispatcher Delivery:** `WebhookNotificationAdapter` computes HMAC-SHA256 signature and POSTs to `/webhook/diavn-events`.
4. **n8n Processing:**
   - Signature: **VALID** (`X-DIAVN-Signature` matched).
   - Replay Window: **VALID** ($< 1\text{s}$ age).
   - Deduplication: **NEW** (`event_id` not in static data).
   - Condition: **PASSED** (`event_type == "CASE_VERIFICATION_HIGH_RISK"`, `risk_score == 92 >= 70`).
5. **Operational Output:**
   ```json
   {
     "status": "field_verification_enqueued",
     "dispatch_id": "DISPATCH-CAS-2026-007-XYZ",
     "case_number": "CAS-2026-007",
     "task_id": "TSK-CAS-2026-007-01",
     "priority": "CRITICAL_HIGH",
     "field_capture_url": "http://localhost:3000/field/capture?caseId=CAS-2026-007",
     "workflow_stage": "PHYSICAL_INSPECTION_PENDING"
   }
   ```
