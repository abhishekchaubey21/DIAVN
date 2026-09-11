# DIAVN Data Provenance & Architecture Audit

## 1. Executive Summary
This document provides the authoritative data provenance audit for the DIAVN frontend platform following the Data Provenance Phase. All silent mock fallbacks have been removed. The application now operates under an explicit data mode architecture where data flows strictly from the backend API:

```
LIVE DATABASE / DEMO DATASET
              │
              ▼
FastAPI Backend (:8000)
              │
              ├── GET /cases (Phase 1)
              ├── GET /dealers (Phase 1)
              ├── GET /api/v1/risk/cases/{case_id} (Phase 6 Authoritative Risk Engine)
              ├── GET /api/v1/verification/invoice/{invoice_id} (Phase 3 Invoices)
              ├── GET /api/v1/images/case/{case_id} (Phase 4 Images)
              ├── GET /api/v1/relationships/cases/{case_id} (Phase 7 Entity Links)
              └── GET /api/v1/cases/{case_id}/workflow-events (Phase 9 Outbox Dispatch)
              │
              ▼
Next.js Frontend Client (src/lib/api.ts)
              │
              ▼
UI Components (Zero Silent Mock Fallbacks)
```

---

## 2. Classification of Remaining Mock / Synthetic Datasets

| Dataset / Symbol | Location | Classification | Usage & Purpose |
|---|---|---|---|
| `MOCK_DEALERS` | `frontend/src/lib/mockData.ts` | **C. Explicit Demo Fixture** | Kept in `mockData.ts` for offline unit testing & benchmark reference only. Not imported by any production dashboard or case detail flow. |
| `MOCK_CUSTOMERS` | `frontend/src/lib/mockData.ts` | **C. Explicit Demo Fixture** | Benchmark customer reference records for offline testing. Not imported by active UI views. |
| `MOCK_CASES` | `frontend/src/lib/mockData.ts` | **C. Explicit Demo Fixture** | Historical baseline specification of demo scenarios (CAS-2026-001 to CAS-2026-010). Unused by `api.ts`. |
| `MOCK_RISK_SCORES` | `frontend/src/lib/mockData.ts` | **A. Removed from UI / Explicit Dev-Only** | Removed from `PriorityCasesTable.tsx`, `DealerRiskOverview.tsx`, `alerts/page.tsx`, `cases/[id]/page.tsx`, and `RiskScoreCard.tsx`. |
| `MOCK_RISK_SIGNALS` | `frontend/src/lib/mockData.ts` | **A. Removed from UI / Explicit Dev-Only** | Removed from `cases/[id]/page.tsx` and `alerts/page.tsx`. Active signals are now derived directly from `GET /api/v1/risk/cases/{id}` (`components`). |
| `MOCK_EVIDENCE_ITEMS` | `frontend/src/lib/mockData.ts` | **A. Removed from UI / Explicit Dev-Only** | Removed from `cases/[id]/page.tsx`. Image evidence is fetched via `GET /api/v1/images/case/{id}`. |
| `MOCK_VERIFICATION_TASKS` | `frontend/src/lib/mockData.ts` | **A. Removed from UI / Explicit Dev-Only** | Removed from `cases/[id]/page.tsx` and `alerts/page.tsx`. Tasks are derived from `GET /api/v1/cases/{id}/workflow-events` and risk assessment recommendations. |

---

## 3. Data Source Mapping for Major Dashboard Components

| Dashboard Visual | Component File | Authoritative Data Source | Fallback Behavior on Backend Failure |
|---|---|---|---|
| **Attention Summary (4 KPI Cards)** | `frontend/src/app/dashboard/page.tsx` | Computed dynamically from `cases` array returned by `GET /cases` | Displays 0 with honest error banner ("Backend API offline") |
| **Priority Verification Cases Table** | `frontend/src/components/PriorityCasesTable.tsx` | `cases` array from `GET /cases`, sorted by `case.risk_level` and `case.risk_score` | Displays empty table state |
| **Requires Attention Panel** | `frontend/src/components/RequiresAttentionPanel.tsx` | Filtered flagged cases from `GET /cases` | Displays "No priority items require immediate attention" |
| **Dealer Risk Overview** | `frontend/src/components/DealerRiskOverview.tsx` | `GET /dealers` and case aggregation from `GET /cases` | Displays empty state |
| **Geographic Verification Map** | `frontend/src/components/GeographicRiskMap.tsx` | Case coordinates from `GET /cases` (`claimed_lat`/`claimed_lng`) and installation image EXIF coordinates from `GET /api/v1/images/case/{id}`. Renders on bundled 31 Indian region vector geometries. | Omits vectors if coordinates missing; renders clean map without fake pins |
| **Relationship Alerts Summary** | `frontend/src/components/RelationshipAlertsSummary.tsx` | `GET /api/v1/relationships/cases/CAS-2026-007` | Displays clean status pill |
| **Recent Verification Activity Timeline** | `frontend/src/components/RecentActivityTimeline.tsx` | Event timestamps and cases from `GET /cases` | Displays "No recent activity" |

---

## 4. Case Detail Workspace Data Isolation (`/cases/[id]`)

| Section | UI Component | Authoritative Endpoint | Isolation Guarantee |
|---|---|---|---|
| **Header Status Banner** | `VerificationResult.tsx` | `GET /cases/{id}` | Displays exact `status` and `risk_level` for the matching case ID. |
| **Underwriting Parameters** | `cases/[id]/page.tsx` | `GET /cases/{id}` | Renders borrower, dealer, claimed address, loan amount for this exact case. |
| **Deterministic Risk Score** | `RiskScoreCard.tsx` | `GET /api/v1/risk/cases/{case_id}` | Direct response from Phase 6 risk engine. If not calculated, renders "Risk Assessment Pending" with `[ Run Risk Calculation ]` trigger. |
| **Active Risk Signals** | `AlertCard.tsx` | `riskScore.components` from `GET /api/v1/risk/cases/{case_id}` | Contains only the exact risk components contributing to this case's score. |
| **Invoice Checks** | `DeterministicVerificationPanel.tsx` | `GET /api/v1/verification/invoice/{invoice_id}` | Checks arithmetic, price benchmarks, and serial consistency for the specific invoice. |
| **Image Forensics** | `ImageVerificationPanel.tsx` | `GET /api/v1/images/case/{case_id}` & `GET /api/v1/verification/image/{image_id}` | EXIF telemetry, pHash, and embedding cosine similarities for images attached to this case. |
| **Relationship Graph** | `RelationshipPanel.tsx` | `GET /api/v1/relationships/cases/{case_id}` | Multi-entity links and shared attributes mapped specifically to this case ID. |
| **Operational Tasks** | `cases/[id]/page.tsx` | `GET /api/v1/cases/{case_id}/workflow-events` | Outbox workflow events and automated audit triggers for this case. |
