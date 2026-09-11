# DIAVN: Dealer Integrity & Asset Verification Network

**DIAVN** is an open-source, enterprise-grade verification and risk intelligence platform built for banks, non-banking financial companies (NBFCs), and clean-energy lenders. It verifies distributed physical equipment (solar installations, water pumps, micro-irrigation systems, farm machinery) financed through dealer networks.

> **Core Philosophy**: LLMs interpret raw unstructured evidence (invoices, nameplate photos, documentation); deterministic code enforces verification and calculates risk signals. The platform surfaces risk metrics, anomalies, and verification tasks—it **never** claims that fraud has been definitively proven.

> **Free-First Policy**: All external APIs are optional dependencies and must use free tiers or free/open-source alternatives. Zero billing or paid subscriptions required.

> **AI Architecture Role**: Gemini is used ONLY for evidence extraction and interpretation. It does NOT determine fraud, does NOT assign risk points, does NOT calculate fraud probabilities, and does NOT make lending decisions.

---

## Phase 2 Architecture: Invoice Evidence Ingestion Pipeline

```
   ┌─────────────────────────────────────────────────────────────┐
   │                    Invoice Upload (UI)                      │
   │           PDF / PNG / JPG / WEBP (Max 10 MB)                │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ multipart/form-data
   ┌──────────────────────────────▼──────────────────────────────┐
   │                   FastAPI /api/v1/invoices                  │
   │  ├── Validate Case & File Type/Size (StorageService)        │
   │  ├── Store Original in Private Supabase Storage Bucket      │
   │  ├── Create Invoice Record (Status: 'processing')           │
   │  └── Dispatch Async BackgroundTasks Worker                  │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ File Bytes
   ┌──────────────────────────────▼──────────────────────────────┐
   │         Gemini Free Tier Extractor (google-genai)           │
   │  ├── Model: gemini-2.5-flash (Zero-temperature extraction)  │
   │  ├── Controlled Extraction System Prompt (Factual only)     │
   │  └── Structured JSON Output via response_schema             │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ Structured Extraction JSON
   ┌──────────────────────────────▼──────────────────────────────┐
   │             Pydantic Validation & DB Storage                │
   │  ├── InvoiceExtraction Schema (Missing fields -> null)      │
   │  ├── Populate 'invoices' & 'invoice_line_items' tables      │
   │  └── Set Status: 'completed' (Extraction != Verification)   │
   └─────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
diavn/
│
├── frontend/                     # Next.js 16 App Router, TypeScript, Tailwind CSS
│   ├── src/
│   │   ├── app/                  # Routes (/dashboard, /cases, /cases/new, /cases/[id], /dealers, /dealers/[id])
│   │   ├── components/           # Reusable UI components (InvoiceEvidenceCard, RiskScoreCard, CaseTable, etc.)
│   │   ├── lib/                  # API client with real invoice upload & fallback mock datasets
│   │   └── types/                # TypeScript schema definitions
│   └── package.json
│
├── backend/                      # FastAPI Modular Monolith
│   ├── app/
│   │   ├── api/                  # REST endpoints (/invoices, /cases, /dealers, /pipeline, /risk)
│   │   ├── core/                 # App configuration (Pydantic settings)
│   │   ├── schemas/              # Pydantic validation schemas (InvoiceExtraction, Case, Dealer, etc.)
│   │   ├── db/                   # Supabase client factory (isolated service_role key) & session stubs
│   │   ├── services/             # StorageService (private bucket, signed URLs) & InvoiceService
│   │   ├── ai/                   # GeminiClient & InvoiceExtractor (gemini-2.5-flash Free Tier)
│   │   ├── pipeline/             # Multi-stage verification pipeline stubs
│   │   ├── risk_engine/          # Deterministic risk scoring & anomaly rules (Phases 3+)
│   │   ├── imaging/              # Local image processing (EXIF, pHash - Phase 3)
│   │   ├── graph/                # Entity collusion graph logic (Phase 5)
│   │   └── workers/              # Background tasks orchestration
│   ├── tests/                    # Pytest test suites (17 integration and contract tests)
│   ├── requirements.txt
│   └── .env.example
│
├── db/                           # Database Schema & Migrations
│   ├── migrations/
│   │   └── 001_initial_schema.sql # 14 PostgreSQL/Supabase tables + pgvector
│   └── seed/
│       └── 001_synthetic_seed.sql # Synthetic test dataset (4 core scenarios)
│
├── n8n/                          # Self-hosted automation workflow definitions
│   └── README.md
│
├── docs/                         # Specifications and architecture docs
│   └── architecture.md
│
├── .env.example                  # Root environment variable template
└── README.md
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **PostgreSQL 14+** or a **Free Supabase Project**
- **Google AI Studio API Key** (Free Tier)

### 2. Backend Setup (FastAPI)

```bash
# Navigate to backend
cd backend

# Install dependencies
python -m pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and supply GEMINI_API_KEY (optional, fallback available)
# SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (optional, local storage fallback available)

# Run FastAPI server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Frontend Setup (Next.js)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

- Dashboard: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- New Case with Invoice Ingestion: [http://localhost:3000/cases/new](http://localhost:3000/cases/new)

---

## Environment Variables

| Variable | Required In Phase 2 | Purpose | Free Tier / Security Notes |
|---|---|---|---|
| `ENVIRONMENT` | Yes | App runtime mode (`development` / `production`) | Standard config |
| `DEBUG` | Yes | Enable debug logging & docs | Standard config |
| `PORT` | Yes | Backend listening port (default: `8000`) | Standard config |
| `SUPABASE_URL` | Optional | Supabase project URL | Free tier project |
| `SUPABASE_ANON_KEY` | Optional | Supabase public anonymous key | Free tier |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | Supabase backend admin key | **BACKEND ONLY** (Never expose to frontend) |
| `SUPABASE_INVOICE_BUCKET` | Optional | Private storage bucket name (default: `invoices`) | Private bucket with signed URLs |
| `MAX_UPLOAD_SIZE_BYTES` | Optional | Upload limit in bytes (default: `10485760` / 10MB) | DoS protection |
| `GEMINI_API_KEY` | Optional | Google Gemini API Key | Free Tier from Google AI Studio |
| `GEMINI_MODEL` | Optional | Gemini model identifier (default: `gemini-2.5-flash`) | Available Google Gemini API Free Tier |

> **Free Tier & Quota Policy**: Gemini 2.5 Flash is used through the available Google Gemini API Free Tier. Actual RPM/TPM/RPD limits are project-, model-, and account-dependent and must be checked in Google AI Studio.

> **Graceful Fallback**: If `SUPABASE_SERVICE_ROLE_KEY` or `GEMINI_API_KEY` are omitted during local development or testing, the system automatically uses secure local storage and graceful offline state without crashing.

---

## Testing & Validation

Run the complete backend test suite:
```bash
python -m pytest backend/tests
```

Test coverage includes:
1. `test_invalid_file_type_rejected` (Rejects `.exe`, `.bat`, etc.)
2. `test_oversized_file_rejected` (Rejects files > 10MB)
3. `test_missing_case_rejected` (Returns 404 for invalid case ID)
4. `test_invoice_upload_and_record_creation` (Validates upload lifecycle)
5. `test_extraction_schema_validation` (Validates `InvoiceExtraction` Pydantic model)
6. `test_missing_fields_become_null` (Ensures zero hallucinated values)
7. `test_malformed_ai_response_handled_safely` (Handles broken JSON safely)
8. `test_gemini_api_failure_handled_safely` (Handles rate limits/exceptions without crashing)
9. `test_mocked_full_extraction_flow` (End-to-end extraction and line items creation)
10. `test_api_does_not_expose_service_role_key` (Verifies key isolation)
11. `test_price_within_tolerance_passes` & `test_price_outside_tolerance_anomaly`
12. `test_missing_benchmark_is_inconclusive` (Critical: missing benchmark != anomaly)
13. `test_serial_format_valid` & `test_serial_format_invalid_placeholder`
14. `test_duplicate_serial_across_internal_cases` & `test_duplicate_serial_within_invoice`
15. `test_dealer_customer_asset_consistency` (Normalized entity matching)
16. `test_arithmetic_consistency_valid_and_invalid`
17. `test_idempotent_verification_and_no_score_calculated`
18. `test_image_integrity_valid_jpeg_png_webp` & `test_corrupt_image_handled_safely`
19. `test_exif_extraction_with_valid_metadata` & `test_missing_exif_is_strictly_inconclusive`
20. `test_haversine_gps_within_and_outside_threshold` & `test_missing_reference_gps_inconclusive`
21. `test_phash_computation_deterministic` & `test_exact_and_near_phash_cross_case_duplicate`
22. `test_same_case_duplicate_image_is_pass_info` & `test_timestamp_consistency_and_anomaly`

---

## Phase 5 Architecture: Local Deep Visual Feature Embeddings & Similarity

```
   ┌─────────────────────────────────────────────────────────────┐
   │             Installation Image Upload / Pipeline            │
   │               JPEG / PNG / WEBP File Stream                 │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ file_bytes
   ┌──────────────────────────────▼──────────────────────────────┐
   │      Local ResNet-18 Deep Visual Feature Extractor (CPU)    │
   │  ├── PyTorch / Torchvision `resnet18` (11.17M parameters)   │
   │  ├── ImageNet Preprocessing: Resize(256), CenterCrop(224)  │
   │  ├── Normalized [0.485, 0.456, 0.406] / [0.229, 0.224, 0.225]│
   │  ├── Classification Head Replaced: `model.fc = Identity()`  │
   │  └── L2 Normalization: Unit Sphere 512-dim Vector           │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ 512-dim Float Vector
   ┌──────────────────────────────▼──────────────────────────────┐
   │        Internal Visual Similarity Engine & Postgres         │
   │  ├── Candidate Vectors Query (Cross-Case Registry)          │
   │  ├── Exact Cosine Similarity Calculation: cos(A, B)         │
   │  ├── Top-K Nearest Match Ranking (Descending Order)         │
   │  ├── Evaluation vs Provisional Threshold (Candidate: 0.85)  │
   │  └── Storage in `installation_images.embedding vector(512)` │
   └─────────────────────────────────────────────────────────────┘
```

### Empirical Benchmark Measurements (Synthetic Dataset)

| Test Transformation / Scenario | Measured Cosine Similarity | Anomaly Status (Threshold: 0.85) | Visual Interpretation |
|---|---|---|---|
| **Identical Image** | `1.0000` | ANOMALY (Exact match) | Same physical equipment photo |
| **Resized Image (50% scale)** | `0.9967` | ANOMALY (Near match) | Resolution change retains deep features |
| **JPEG Recompression (Q95)** | `0.9989` | ANOMALY (Near match) | High quality compression invariant |
| **JPEG Recompression (Q35)** | `0.9932` | ANOMALY (Near match) | Low quality compression invariant |
| **5% Edge Crop** | `0.9836` | ANOMALY (Near match) | Framing shift retains deep features |
| **Brightness & Contrast (+20%)** | `0.9940` | ANOMALY (Near match) | Exposure shift invariant |
| **Same Scene (Changed Framing)**| `0.9653` | ANOMALY (Near match) | Similar scene angle / lighting |
| **Distinct Equipment (Solar vs Pump)** | `0.5038` | PASS (No match) | Correctly separated physical category |
| **Unrelated Geometric Scene** | `0.4652` | PASS (No match) | Unrelated visual environment |

> [!IMPORTANT]
> **Controlled Benchmark Disclaimer**: The benchmark above was conducted on a controlled synthetic image dataset. Because the dataset is small and synthetic, these measurements do **NOT** establish real-world false-positive or false-negative rates. The 0.85 threshold is provisional and configurable. Deep visual feature similarity is evidence of visual similarity and may indicate potentially related evidence requiring review; it does **NOT** determine fraud.

### Multi-Layer Visual Forensics Diagnostic: pHash vs Deep Feature Embeddings

| Dimension | 1. Perceptual Hash (pHash) | 2. Deep Visual Feature Embeddings (ResNet-18) |
|---|---|---|
| **Underlying Mechanism** | 64-bit DCT frequency-domain binary hash | 512-dimensional continuous learned feature vector |
| **Distance Metric** | Hamming distance ($d \in [0, 64]$) | Cosine similarity ($\cos \in [-1.0, 1.0]$) |
| **Computational Footprint** | Extremely fast ($< 2\text{ ms}$ on CPU) | Fast local inference (~$14\text{–}114\text{ ms}$ on CPU) |
| **Primary Strength** | Exact copy-paste, exact crops, recompression | Lighting variation, minor angle changes, scale |
| **Scope & Privacy** | 100% local, zero external APIs | 100% local, zero external APIs |

---

## Phase 6 Architecture: Explainable Deterministic Risk Engine

```
   ┌─────────────────────────────────────────────────────────────────────────┐
   │                   Active Deterministic Risk Signals                     │
   │  ├── Invoice Price Anomaly (+20)                                        │
   │  ├── Internal Serial Number Duplication (+35)                           │
   │  ├── Perceptual Image Reuse pHash (+20)                                 │
   │  ├── Deep Visual Feature Similarity Embedding (+15)                     │
   │  ├── Site GPS Distance Haversine Mismatch (+12)                         │
   │  └── Missing EXIF Metadata (+8, if configured)                          │
   └────────────────────────────────────┬────────────────────────────────────┘
                                        │ Raw Signals List
   ┌────────────────────────────────────▼────────────────────────────────────┐
   │                   Signal Deduplication & Grouping                       │
   │  ├── Deduplicate identical conditions (e.g., same serial across items)  │
   │  ├── Evidence Groups: SERIAL, INVOICE_PRICE, IMAGE_REUSE, LOCATION, ...│
   │  └── Apply Group Caps (Anti-Double-Counting):                           │
   │      - IMAGE_REUSE_GROUP_MAX = 25 (pHash + Embedding capped at 25)      │
   │      - SERIAL_GROUP_MAX = 35                                            │
   │      - INVOICE_PRICE_GROUP_MAX = 25                                     │
   └────────────────────────────────────┬────────────────────────────────────┘
                                        │ Group Capped Contributions
   ┌────────────────────────────────────▼────────────────────────────────────┐
   │             Deterministic Score & Categorical Risk Band                 │
   │  ├── Overall Score = min(Sum of Capped Contributions, 100)              │
   │  ├── Risk Bands:                                                        │
   │  │   - LOW: 0–39   (Action: "No immediate additional verification indicated by the configured DIAVN rules.") │
   │  │   - MEDIUM: 40–69 (Action: "Additional document/evidence review recommended.") │
   │  │   - HIGH: 70–100 (Action: "Field verification recommended.")          │
   │  └── Traceable Component Breakdown with Underlying Evidence Payloads    │
   └─────────────────────────────────────────────────────────────────────────┘
```

### Initial Policy Weights & Evidence Group Caps

| Evidence Group | Signal Name | Policy Weight | Group Maximum Cap | Underwriting Rationale |
|---|---|---|---|---|
| **SERIAL** | `DUPLICATE_SERIAL` | +35 | **35** | High-significance internal duplicate serial check |
| **INVOICE_PRICE** | `INVOICE_PRICE_ANOMALY` | +20 | **25** | Price exceeds established regional model benchmark |
| **IMAGE_REUSE** | `IMAGE_PHASH_REUSE` | +20 | **25** | Exact/near 64-bit DCT perceptual image match |
| **IMAGE_REUSE** | `IMAGE_EMBEDDING_SIMILARITY` | +15 | **25** | High deep visual feature similarity (ResNet-18) |
| **LOCATION** | `GPS_MISMATCH` | +12 | **20** | Photo geotag > 1.0 km from claimed installation site |
| **DEALER** | `DEALER_RELATIONSHIP_ANOMALY` | +15 | **25** | Shared attributes across distinct borrower applications |
| **METADATA** | `MISSING_EXIF` | +8 | **10** | Stripped/missing camera telemetry (low significance) |
| **EXTRACTION** | `LOW_EXTRACTION_CONFIDENCE` | +5 | **15** | Invoice OCR/extraction clarity below baseline |

> [!IMPORTANT]
> **Risk Engine Standards & Legal Compliance**:
> 1. The DIAVN risk score is an explainable policy-based verification risk score, not a statistical probability of fraud.
> 2. Risk weights are policy assumptions and are not calibrated fraud probabilities.
> 3. The DIAVN score does not independently approve, reject, or disburse a financing application.
> 4. Scores are 100% deterministic (same input signals $\to$ same score). Zero LLM calls or external SaaS dependencies during scoring.

---

## Phase 7 Architecture: Dealer Relationship & Entity-Link Analysis

```
   ┌─────────────────────────────────────────────────────────────────────────┐
   │                   Categorized Entity Linkage Engine                     │
   │  ├── Category A (Structural): Dealer-Customer, Customer-Case, Invoices  │
   │  ├── Category B (Evidence): Shared phone/email/address, Cross-case links│
   │  └── Category C (Potential Anomaly): Multi-factor combination rules     │
   └────────────────────────────────────┬────────────────────────────────────┘
                                        │
   ┌────────────────────────────────────▼────────────────────────────────────┐
   │                   Privacy & Normalization Pipeline                      │
   │  ├── Deterministic Phone, Email, Address, Serial Normalization          │
   │  ├── Internal SHA-256 Digest Hashing (Audit Traceability)               │
   │  └── Strict UI Masking: '+91-98****0001', 'r***a@example.synthetic'     │
   └────────────────────────────────────┬────────────────────────────────────┘
                                        │
   ┌────────────────────────────────────▼────────────────────────────────────┐
   │             Conservative Multi-Factor Anomaly Evaluation                │
   │  ├── Condition A: Same dealer + >=2 distinct customers + shared contact │
   │  ├── Condition B: Same dealer + evidence link + independent case anomaly│
   │  └── Phase 7 Constraint: Emitted signals have weight = 0.00             │
   └─────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Relationship Governance & Compliance Notice**:
> 1. DIAVN relationship analysis identifies repeated or unusual relationships within the internal DIAVN dataset. It does **NOT** prove collusion, fraudulent intent, or dealer misconduct.
> 2. "Cross-case" strictly refers to cases present within the internal DIAVN database; it does not imply cross-lender verification.
> 3. Zero external APIs, zero graph databases (PostgreSQL/Supabase native), and zero ML/LLMs used during relationship analysis.

---

## Phase Roadmap

- [x] **Phase 1**: Architecture Foundation, Database Schema (14 tables), Synthetic Seed Data, Next.js Lender Dashboard.
- [x] **Phase 2**: Real Invoice Evidence Ingestion Pipeline (Supabase Storage, Gemini Free Tier Extraction, Pydantic Validation, Database Population, Case UI Evidence Display).
- [x] **Phase 3**: Real Deterministic Verification Engine (Price Benchmark Matching, Internal Duplicate Serial Check, Arithmetic Verification, Case Entity Consistency, Zero External APIs, No Composite Risk Scoring).
- [x] **Phase 4**: Deterministic Installation Image Forensics (EXIF Telemetry, Site GPS Haversine Distance, 64-bit pHash Cross-Case Visual Reuse Detection, Zero External APIs, No Composite Risk Scoring).
- [x] **Phase 5**: Local Image Embeddings & Advanced Visual Similarity (ResNet-18 512-dim Feature Vectors, Top-K Cosine Similarity, Multi-Layer Visual Diagnostics, Zero External APIs, Zero Composite Risk Scoring).
- [x] **Phase 6**: Explainable Deterministic Risk Engine (0–100 Case-Level Risk Scoring, Anti-Double-Counting Group Caps, Traceable Component Breakdown, LOW/MEDIUM/HIGH Risk Bands, Deterministic Underwriting Directives).
- [x] **Phase 7**: Dealer Relationship & Entity-Link Analysis (Categorized Structural/Evidence/Anomaly Taxonomy, Multi-Factor Conservative Anomaly Rules, Privacy Masking, Zero Risk Weight, Deterministic SVG Graphs).
- [ ] **Phase 8**: Automated Multi-Channel Alerting & Verification Dispatch (Next phase).



