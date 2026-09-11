# DIAVN - Dealer Integrity & Asset Verification Network
## Phase 2: Invoice Ingestion & Evidence Extraction Architecture

### 1. Ingestion Pipeline Flow
```
User (Lender / Underwriter)
      │
      ▼ [multipart/form-data]
POST /api/v1/invoices
      │
      ├── 1. StorageService.validate_file (MIME & Size check)
      ├── 2. StorageService.upload_invoice_file (Private bucket 'invoices')
      ├── 3. InvoiceService.create_invoice_record (Status: 'processing')
      │
      └── BackgroundTasks: InvoiceService.process_extraction
               │
               ▼
      InvoiceExtractor (google-genai SDK, model: gemini-2.5-flash)
               │
               ▼ [Structured JSON via response_schema]
      InvoiceExtraction (Pydantic validation)
               │
               ▼
      Database Population:
      - 'invoices' record updated (Status: 'completed', confidence, invoice_number)
      - 'invoice_line_items' populated with product name, unit price, quantity, serials
```

### 2. Core Security & Isolation Principles
- **Private Storage Bucket**: Uploaded invoice documents are stored in the private bucket `invoices`. Public access is disabled.
- **Signed URLs**: The frontend accesses original documents solely through time-limited signed URLs (`/api/v1/invoices/{id}/download-url`).
- **Credential Isolation**: `SUPABASE_SERVICE_ROLE_KEY` and `GEMINI_API_KEY` are consumed exclusively by the backend service layer and never sent to client applications.
- **No Hallucination Policy**: Extraction schema sets missing document fields to `null`.
- **Extraction vs. Verification Distinction**: Extracted invoices have an extraction status (`completed`), while the verification status remains `pending_verification` until deterministic rules evaluate the evidence in subsequent phases.
- **Free Tier Policy**: Gemini 2.5 Flash is used through the available Google Gemini API Free Tier. Actual RPM/TPM/RPD limits are project-, model-, and account-dependent and must be checked in Google AI Studio. Paid APIs are not part of the MVP.

---

## Phase 3: Deterministic Invoice Verification Engine Architecture

### 1. Verification Layer Objective
Phase 2 answers: *"What does the invoice claim?"*  
Phase 3 answers: *"Do the extracted invoice claims pass deterministic consistency checks against the database?"*

> **Mandatory Underwriting Principle**:
> **"An anomaly is an evidence-based inconsistency requiring review. It is not a determination of fraud."**
> The system strictly identifies anomalies and verification signals. It never calculates fraud probabilities or labels borrowers/dealers as fraudulent.

### 2. Zero External API Rule
All Phase 3 verification routines run 100% locally against PostgreSQL / Supabase tables:
- `ZERO` Gemini calls during verification
- `ZERO` GST / MCA / OEM / KYC APIs
- `ZERO` paid or geocoding APIs
- Verification runs solely against `product_price_benchmarks`, `registered_assets`, `dealers`, `cases`, `invoices`, and `invoice_line_items`.

### 3. Separation of Concerns & Processing Pipeline
```
               Extracted Invoice JSON (From Phase 2)
                                 │
                                 ▼
                     Untrusted Input Validation
             (Types, bounds, negative numbers sanitization)
                                 │
                                 ▼
             Deterministic Verification Engine (service.py)
   ┌─────────────────────────────┼─────────────────────────────┐
   │                             │                             │
   ▼                             ▼                             ▼
Price Benchmark Checks    Serial Number Checks       Consistency & Completeness
- Benchmark lookup        - Presence & Format        - Case vs Invoice entities
- Tolerance band eval     - Intra-invoice duplicate  - Arithmetic line items & tax
- Missing benchmark       - Internal asset registry  - Required evidence fields
  → INCONCLUSIVE            duplicate check            completeness
   │                             │                             │
   └─────────────────────────────┼─────────────────────────────┘
                                 │
                                 ▼
                    VerificationResult Aggregate
              (Status: PASS | ANOMALY | INCONCLUSIVE)
                                 │
                                 ▼
           Idempotent Risk Signal Generation (risk_signals)
          - PRICE_ANOMALY, DUPLICATE_SERIAL, ARITHMETIC_MISMATCH
          - Zero score calculation in Phase 3 (score = NULL / 0)
```

### 4. Deterministic Checks Implemented

| Check Type | Database / Rule Source | Pass Condition | Anomaly Condition | Inconclusive Condition |
|---|---|---|---|---|
| **Price Benchmark** | `product_price_benchmarks` | Unit price within `[P*(1-T/100), P*(1+T/100)]` | Price exceeds bounds | No benchmark configured for product |
| **Serial Presence & Format** | Format regex + Suspicious keyword list | Valid alphanumeric, length >= 4 | Suspicious format, placeholder (`UNKNOWN`, `TEST`, `123456`, `N/A`) | Serial not extracted on serializable item |
| **Internal Duplicate Serial** | `registered_assets.serial_number` | Serial not registered to another case | Serial already associated with another active case in internal database | Serial missing / untracked |
| **Intra-Invoice Duplicate** | Current line items | All line item serials unique | Duplicate serial detected across line items in same invoice | No serials |
| **Case Entity Consistency** | `cases` (dealer, customer, asset) | Normalized entity names match case application | Substantial mismatch between invoice parties and case application | Entity names missing on either side |
| **Invoice Arithmetic** | Line item math & totals | `qty * rate ≈ line_total` and `subtotal + tax ≈ total` | Arithmetic discrepancy > rounding threshold | Subtotal or tax missing |
| **Required Evidence** | Extraction completeness | `invoice_number`, `date`, `dealer`, `customer`, `total`, `line_items` present | — | Any required underwriting field absent |

### 5. Idempotency & Lifecycle States
- **Idempotency**: Running verification multiple times deterministically replaces previously generated signals for the target invoice.
- **Explicit Lifecycle Separation**:
  1. *AI Evidence Extraction*: `COMPLETED`
  2. *Deterministic Verification*: `COMPLETED` (Pass / Anomaly / Inconclusive breakdown)
  3. *Composite Risk Score (0–100)*: `NOT YET COMPUTED` (Preserved for future Risk Engine phase).

---

## Phase 4: Installation Image Forensics & Telemetry Engine

### 1. Objective & Philosophy
Phase 4 implements deterministic installation-image forensics to evaluate equipment photo evidence without external paid APIs:
- Image file container and magic bytes integrity
- EXIF camera telemetry extraction and sanitization
- GPS coordinate validation and Haversine distance verification vs reference site coordinates
- Chronological timestamp consistency vs invoice/application timeline
- 64-bit Perceptual Hashing (pHash) for cross-case visual reuse detection and same-case redundancy tracking

> **Mandatory Underwriting Principles**:
> - **"Missing EXIF metadata does not prove image manipulation."** (Classified as `INCONCLUSIVE`).
> - **"Image similarity indicates potential evidence reuse; it is not proof of fraudulent activity."** (Classified as `ANOMALY` for human underwriter review).
> - **"GPS mismatch indicates inconsistency with the supplied reference location; it does not prove GPS spoofing."** (Classified as `ANOMALY` when distance exceeds threshold).
> - **"Image reuse detection is limited to images available in the internal DIAVN database."**

### 2. Zero External / Paid APIs Policy
- **ZERO Gemini API calls** during image forensics (Pillow, piexif, and imagehash run 100% locally).
- **ZERO paid CV or forensics APIs** (No Google Vision, AWS Rekognition, Azure Vision, or paid OCR).
- **ZERO paid geocoding APIs** (Distance is evaluated purely deterministically against case reference coordinates).

### 3. Pipeline Flow
```
                 Installation Image Upload (Multipart)
                                   │
                                   ▼
                  File Integrity & Magic Bytes Check
          (JPEG: FF D8 FF | PNG: 89 50 4E 47 | WEBP: RIFF..WEBP)
                                   │
                                   ▼
                   Private Storage (installation-images)
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                              │                              │
    ▼                              ▼                              ▼
EXIF Telemetry             Site GPS Consistency           64-bit Perceptual Hash
- Camera make/model        - Boundary validation          - DCT 64-bit pHash
- Capture timestamp        - Haversine distance vs        - Hamming distance (0-64)
- Sanitization & PII         reference site coordinates   - Exact reuse (d = 0)
- Missing -> INCONCLUSIVE  - Missing ref -> INCONCLUSIVE  - Near reuse (d <= 6)
    │                              │                              │
    └──────────────────────────────┼──────────────────────────────┘
                                   │
                                   ▼
                   ImageVerificationSummary Aggregate
                 (PASS | ANOMALY | INCONCLUSIVE breakdown)
                                   │
                                   ▼
               Idempotent Risk Signal Generation (weight = 0)
```

### 4. Empirical pHash Distance Measurements & Provisional Threshold Selection

Under controlled synthetic benchmark testing on physical equipment images:
- **Identical Image**: $d = 0$
- **Resized Image (50% scale)**: $d = 4$
- **Recompressed JPEG (Quality 95)**: $d = 2$
- **Recompressed JPEG (Quality 35)**: $d = 4$
- **5% Border Crop**: $d = 8$
- **Contrast / Brightness +20%**: $d = 6$
- **Distinct Physical Equipment (Solar vs Pump)**: $d = 38$
- **Unrelated Geometric Scene**: $d = 38$

**Selected Provisional Threshold**: **Hamming Distance $d \le 6$ (configurable)**.  
*Dataset Limitations & Validation Notes*:
- $d \le 6$ is a **provisional, configurable baseline threshold**.
- The measured test dataset is small and synthetic.
- These controlled measurements do **not** establish real-world false-positive or false-negative operational rates.
- The threshold must be validated and calibrated on a larger, representative multi-equipment dataset in a future phase.

### 5. Deterministic Image Checks Implemented

| Check Type | Rule / Methodology | Pass Condition | Anomaly Condition | Inconclusive Condition |
|---|---|---|---|---|
| **IMAGE_FILE_INTEGRITY** | Magic byte signatures & Pillow container decode | Decodes cleanly, valid dimensions ($W, H > 0$) | Corrupted bytes, invalid dimensions | — |
| **EXIF_METADATA** | EXIF parsing & sanitization | Useful camera telemetry extracted | — | No EXIF present in photo |
| **GPS_COORDINATE_VALIDITY** | Boundary checks | Latitude $\in [-90, 90]$, Longitude $\in [-180, 180]$ | Invalid coordinate boundaries | Coordinates missing |
| **GPS_LOCATION_CONSISTENCY** | Great-circle Haversine formula | Distance to claimed site $\le 1.0$ km | Distance to claimed site $> 1.0$ km | Photo or reference site GPS missing |
| **IMAGE_TIMESTAMP_CONSISTENCY** | Date chronology math | Valid timeline or pre-invoice staging note | Impossible/uncalibrated date (e.g. year < 2010) | Capture date or reference date missing |
| **IMAGE_PHASH_REUSE** | Bitwise Hamming distance across cases | No cross-case image with $d \le 6$ | Cross-case image match with $d \le 6$ | pHash unavailable |
| **IMAGE_SAME_CASE_DUPLICATE** | Intra-case image comparison | Unique image in case | Repeated image in same case (`INFO`/`PASS`) | — |
| **IMAGE_EMBEDDING_SIMILARITY** | ResNet-18 512-dim cosine similarity | No cross-case image with $\cos \ge 0.85$ | Cross-case image match with $\cos \ge 0.85$ | Embedding unavailable / model failure |

---

## Phase 5: Local Deep Visual Feature Embeddings & Advanced Visual Similarity

### 1. Core Objective & Scope
Phase 5 introduces a secondary local visual similarity engine using continuous deep visual feature representations extracted by a lightweight local convolutional neural network (ResNet-18).
- **Core Question**: "Do these installation images share high deep visual feature similarity across different loan cases in our internal lender database?"
- **Underwriting Purpose**: "Deep visual feature similarity is evidence of visual similarity and may indicate potentially related evidence requiring review. It does not determine fraud."

### 2. Zero External / Paid APIs Policy
- **ZERO Gemini Vision API calls** (ResNet-18 runs 100% locally on CPU via PyTorch and torchvision).
- **ZERO paid SaaS or embedding databases** (No OpenAI CLIP, Pinecone, Weaviate, Milvus cloud, AWS Rekognition, Google Cloud Vision, or Azure Computer Vision).
- **Additive Database Compatibility**: Uses the existing PostgreSQL `installation_images.embedding vector(512)` column without destructive schema mutations.

### 3. Model Architecture & Extraction Details
- **Architecture**: Deep Residual Network (ResNet-18), 18 layers deep.
- **Weights**: Pretrained on ImageNet-1K (`ResNet18_Weights.DEFAULT` / PyTorch torchvision).
- **Parameters**: 11,176,512 parameters (~44.7 MB memory footprint).
- **Feature Extraction**: Final 1000-class fully connected classification layer replaced with `torch.nn.Identity()`, extracting raw 512-dimensional feature maps from the adaptive average pooling layer.
- **Vector Normalization**: L2-normalization ensuring unit sphere vectors:
  $$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}, \quad \|\hat{\mathbf{v}}\|_2 = 1.0$$
- **Preprocessing Pipeline**:
  1. Convert to RGB
  2. Bilinear resize to $256 \times 256$
  3. Center crop to $224 \times 224$
  4. Standard ImageNet channel normalization: Mean = `[0.485, 0.456, 0.406]`, Std = `[0.229, 0.224, 0.225]`

### 4. Controlled Empirical Benchmark Measurements

| Test Transformation / Scenario | Measured Cosine Similarity | Anomaly Status (Provisional: 0.85) | Rationale |
|---|---|---|---|
| **Identical Image** | `1.0000` | ANOMALY | Exact identical image |
| **Resized Image (50% scale)** | `0.9967` | ANOMALY | High visual feature retention |
| **JPEG Recompression (Q95)** | `0.9989` | ANOMALY | Invariant to slight compression |
| **JPEG Recompression (Q35)** | `0.9932` | ANOMALY | Invariant to aggressive compression |
| **5% Edge Crop** | `0.9836` | ANOMALY | Invariant to slight framing shifts |
| **Brightness & Contrast (+20%)** | `0.9940` | ANOMALY | Invariant to illumination changes |
| **Same Scene (Changed Framing)** | `0.9653` | ANOMALY | Retains core visual subject matter |
| **Distinct Equipment (Solar vs Pump)** | `0.5038` | PASS | Clearly separated physical categories |
| **Unrelated Geometric Scene** | `0.4652` | PASS | Clearly separated non-equipment visual scene |

> [!IMPORTANT]
> **Empirical Benchmark Disclaimer**: The measurements above were obtained using a controlled synthetic benchmark dataset. Because the dataset is small and synthetic, these measurements do **NOT** establish real-world operational false-positive or false-negative rates. The 0.85 threshold is provisional and configurable.

### 5. Multi-Layer Visual Forensics Diagnostic: pHash vs Deep Feature Embeddings

```
                        Multi-Layer Visual Forensics Strategy
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
Layer 1: Perceptual Hashing (pHash)             Layer 2: Deep Feature Embeddings (ResNet-18)
├── 64-bit DCT binary hash                      ├── 512-dim continuous feature vector
├── $O(1)$ Hamming distance comparison           ├── Cosine similarity on unit hypersphere
├── Invariant to exact re-uploads, crops        ├── Invariant to lighting, framing, resolution
└── Fast rejection filter (< 2 ms)              └── In-depth visual feature comparison (~14-114 ms)
```

---

## Phase 6: Explainable Deterministic Risk Engine

### 1. Core Principles & Philosophy
- **Deterministic Evaluation**: Same database state + active risk signals $\to$ exact same score, risk band, and breakdown. Zero randomness. Zero LLM/AI dependency during score computation.
- **Evidence Traceability**: Every numeric contribution originates from an active `risk_signals` record and is linked to the originating evidence payload (e.g. invoice line item variance, duplicate serial number, or cross-case image match).
- **Anti-Double-Counting**: Signals referring to the same underlying condition are deduplicated and grouped under evidence group caps (e.g. pHash + embedding reuse capped at 25).
- **Legal Compliance Standard**: The final score represents an **evidence-based verification risk index**, **NOT** a probability of fraud.

### 2. Initial Policy Weights, Evidence Groups, & Caps

| Group Name | Canonical Signal Type | Initial Policy Weight | Group Max Cap | Rationale |
|---|---|---|---|---|
| **`SERIAL`** | `DUPLICATE_SERIAL` | +35 | **35** | High-significance internal duplicate serial check |
| **`INVOICE_PRICE`** | `INVOICE_PRICE_ANOMALY` | +20 | **25** | Price benchmark variance exceeds regional model average |
| **`IMAGE_REUSE`** | `IMAGE_PHASH_REUSE` | +20 | **25** | Perceptual 64-bit DCT exact/near match ($d \le 6$) |
| **`IMAGE_REUSE`** | `IMAGE_EMBEDDING_SIMILARITY` | +15 | **25** | Continuous deep visual feature similarity ($\cos \ge 0.85$) |
| **`LOCATION`** | `GPS_MISMATCH` | +12 | **20** | Photo geotag Haversine distance $> 1.0$ km from claimed site |
| **`DEALER`** | `DEALER_RELATIONSHIP_ANOMALY` | +15 | **25** | Multi-case shared attributes / borrower overlap |
| **`METADATA`** | `MISSING_EXIF` | +8 | **10** | Stripped/missing camera telemetry (low significance) |
| **`EXTRACTION`** | `LOW_EXTRACTION_CONFIDENCE` | +5 | **15** | OCR/extraction clarity below baseline |

### 3. Risk Bands & Workflow Recommendations

- **LOW (0–39)**: `"No immediate additional verification indicated by the configured DIAVN rules."`
- **MEDIUM (40–69)**: `"Additional document/evidence review recommended."`
- **HIGH (70–100)**: `"Field verification recommended."`

> [!IMPORTANT]
> **Risk Score & Underwriting Compliance Mandate**:
> - The DIAVN risk score is an explainable policy-based verification risk score, not a statistical probability of fraud.
> - Risk weights are policy assumptions and are not calibrated fraud probabilities.
> - The DIAVN score does not independently approve, reject, or disburse a financing application.

### 4. Mathematical Definition

$$\text{Raw Score} = \sum_{g \in \text{Groups}} \sum_{s \in g} W(s)$$
$$\text{Group Capped Score} = \sum_{g \in \text{Groups}} \min\left(\sum_{s \in g} W(s), \text{Cap}(g)\right)$$
$$\text{Overall Risk Score} = \min(\text{Group Capped Score}, 100)$$

where:
- $W(s)$ is the policy weight for active signal $s$.
- $\text{Cap}(g)$ is the maximum permitted contribution for evidence group $g$.

---

## Phase 7: Dealer Relationship & Entity-Link Analysis

### 1. Categorized Relationship Taxonomy
All entity connections in DIAVN are formally divided into three distinct categories:
- **Category A (Structural Relationships)**: Standard operational entity linkages (`DEALER_SERVES_CUSTOMER`, `CUSTOMER_ASSOCIATED_CASE`, `DEALER_ORIGINATED_CASE`, `CASE_CONTAINS_INVOICE`, `CASE_CONTAINS_ASSET`, `SERIAL_ASSOCIATED_CASE`). Contextual only; zero risk.
- **Category B (Evidence Relationships)**: Observed shared attributes or cross-case linkages (`SHARED_CUSTOMER_PHONE`, `SHARED_CUSTOMER_EMAIL`, `SHARED_CUSTOMER_ADDRESS`, `DEALER_CUSTOMER_SHARED_ADDRESS`, `DEALER_CUSTOMER_SHARED_PHONE`, `CROSS_CASE_SERIAL_LINK`, `CROSS_CASE_IMAGE_LINK`). Status: `INFO`, risk weight $0.00$.
- **Category C (Potential Anomalies)**: `DEALER_RELATIONSHIP_ANOMALY`, triggered only when conservative combination conditions are met.

### 2. Conservative Deterministic Anomaly Triggers (`relationship-v1`)
- **Condition A (Cluster Contact Overlap)**: Same dealer + $\ge 2$ distinct customers sharing normalized phone/email + $\ge 2$ distinct cases.
- **Condition B (Multi-Factor Dimension Correlation)**: Same dealer + observed evidence link (shared contact/address) + at least 1 independent active verification anomaly (price variance, duplicate serial, image reuse) on the analyzed case.

### 3. Privacy & Anti-Double-Counting Standards
- **Masking**: Contact phones and emails are masked in UI and API payloads (e.g. `+91-98****0001`, `r***a@example.synthetic`).
- **Zero Risk Weight in Phase 7**: All relationship links and signals emitted in Phase 7 have $\text{risk\_weight} = 0.00$, preserving the frozen Phase 6 risk scoring architecture.
- **Zero External APIs & Zero Graph SaaS**: Deterministic SQL queries and local in-memory graph projections. Zero ML/LLMs.

---

## Phase 8: Case-Level Verification Pipeline & Orchestration

### 1. Sequential Dependency Pipeline
Coordinates all existing DIAVN verification modules in strict dependency order:
1. `INVOICE_EXTRACTION` (Phase 2)
2. `INVOICE_VERIFICATION` (Phase 3)
3. `IMAGE_PROCESSING` (Phase 4 & 5)
4. `RELATIONSHIP_ANALYSIS` (Phase 7)
5. `RISK_CALCULATION` (Phase 6)
6. `VERIFICATION_TASK_DISPATCH`

### 2. Core Operational Constraints
- **Zero Logic Duplication**: Reuses existing Phase 2–7 service classes directly.
- **Phase 6 Sole Risk Authority**: Consumes the 0–100 risk score and risk band from Phase 6. Does not create a secondary risk engine.
- **Database-Enforced Concurrency Lock**: Unique partial index `idx_active_pipeline_run_per_case` on `verification_pipeline_runs(case_id) WHERE status IN ('QUEUED', 'PROCESSING')` prevents duplicate concurrent runs.
- **Idempotency & History**: Reruns generate new historical records while updating active signals and task records.

---

## Phase 9: Alerts & Workflow Automation with n8n

### 1. Critical Architectural Boundary
> **FastAPI & DIAVN Database = Sole Source of Truth**  
> **n8n = Workflow / Automation Layer Only**
>
> n8n is strictly an external workflow automation tool and is **NOT** the source of truth for DIAVN verification, risk scores, or fraud decisions.

### 2. Event-Driven Outbox Architecture
- **Durable Outbox**: `workflow_events` table stores all events (`PENDING`, `PROCESSING`, `DELIVERED`, `FAILED`, `RETRY_PENDING`).
- **Atomic Worker Claiming**: Database-level lock leasing (`locked_at`, `locked_by`, `SELECT ... FOR UPDATE SKIP LOCKED`) prevents concurrent duplicate dispatches across workers and restarts.
- **Bounded Retries**: Maximum 3 attempts with exponential backoff (+30s, +120s) before transitioning to `FAILED`.
- **Fault Isolation**: n8n outages never block pipeline execution, risk scoring, or task creation in DIAVN.

### 3. Canonical Webhook Security & Signing
- **Canonical Input**: `HMAC_SHA256(timestamp + "." + raw_request_body, secret)`
- **Header**: `X-DIAVN-Signature: sha256=<hex_digest>`
- **Header**: `X-DIAVN-Timestamp: <iso_utc_timestamp>`
- **Constant-Time Verification**: `hmac.compare_digest` with 5-minute (300s) replay window enforcement.
- **SSRF Whitelist**: Webhooks only dispatch to configured `N8N_WEBHOOK_URL`.

### 4. Policy Language & Notification Content
- **HIGH-Risk Alert**: Sent only for `CASE_VERIFICATION_HIGH_RISK` (`overall_score >= 70`).
- **Approved Terminology**: *"Multiple/high-significance verification anomalies detected; field verification recommended."*
- **Forbidden Phrases**: Zero occurrences of *"fraud detected"*, *"fraud confirmed"*, or *"fraud probability"*.
- **LOW / MEDIUM Cases**: No urgent alerts dispatched; remain accessible via DIAVN case view.
