-- ============================================================================
-- DIAVN Database Schema Migration: 001_initial_schema.sql
-- Project: Dealer Integrity & Asset Verification Network (DIAVN)
-- Database Engine: PostgreSQL 14+ / Supabase
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension (for future free image/text embeddings)
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- 1. USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'risk_officer' CHECK (role IN ('admin', 'risk_officer', 'field_agent', 'auditor', 'viewer')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. DEALERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS dealers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dealer_code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    gstin VARCHAR(15) UNIQUE,
    pan VARCHAR(10),
    cin VARCHAR(21),
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'under_review', 'flagged', 'suspended')),
    risk_tier VARCHAR(50) NOT NULL DEFAULT 'low' CHECK (risk_tier IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 3. CUSTOMERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_code VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(255),
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    id_proof_type VARCHAR(50) DEFAULT 'AADHAAR_SYNTHETIC',
    id_proof_number_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. CASES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_number VARCHAR(50) NOT NULL UNIQUE,
    dealer_id UUID NOT NULL REFERENCES dealers(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    asset_type VARCHAR(100) NOT NULL,
    claimed_installation_address TEXT NOT NULL,
    claimed_lat NUMERIC(10, 7),
    claimed_lng NUMERIC(10, 7),
    loan_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'verification_pending', 'under_review', 'flagged', 'verified', 'rejected')),
    risk_level VARCHAR(50) NOT NULL DEFAULT 'unknown' CHECK (risk_level IN ('low', 'medium', 'high', 'critical', 'requires_verification', 'unknown')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 5. INVOICES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    dealer_id UUID REFERENCES dealers(id) ON DELETE SET NULL,
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    tax_amount NUMERIC(15, 2) DEFAULT 0.00,
    file_path TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    verification_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (verification_status IN ('pending', 'pending_verification', 'verified', 'anomaly_detected', 'inconclusive')),
    extracted_json JSONB DEFAULT '{}'::jsonb,
    extraction_confidence NUMERIC(5, 2) DEFAULT 0.00,
    ocr_raw_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 6. INVOICE LINE ITEMS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS invoice_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    item_description TEXT NOT NULL,
    hsn_code VARCHAR(20),
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 1.00,
    unit_price NUMERIC(15, 2) NOT NULL,
    total_amount NUMERIC(15, 2) NOT NULL,
    serial_numbers TEXT[], -- Array of serial numbers listed in invoice
    benchmark_variance_pct NUMERIC(6, 2), -- Variance from price benchmark
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 7. INSTALLATION IMAGES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS installation_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    image_type VARCHAR(50) NOT NULL DEFAULT 'installation_wide' CHECK (image_type IN ('installation_wide', 'nameplate', 'geo_tag', 'serial_barcode', 'inverter_screen', 'field_context')),
    file_path TEXT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100) DEFAULT 'image/jpeg',
    phash VARCHAR(64), -- Perceptual hash for near-duplicate image detection
    exif_timestamp TIMESTAMPTZ,
    exif_lat NUMERIC(10, 7),
    exif_lng NUMERIC(10, 7),
    exif_device_model VARCHAR(100),
    embedding vector(512), -- Optional pgvector visual embedding column (prepared for Phase 2)
    verification_status VARCHAR(50) NOT NULL DEFAULT 'uploaded' CHECK (verification_status IN ('uploaded', 'analyzed', 'suspicious_metadata', 'duplicate_detected', 'verified')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 8. PRODUCT PRICE BENCHMARKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS product_price_benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_category VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    model_name VARCHAR(150) NOT NULL,
    specifications TEXT,
    benchmark_min_price NUMERIC(15, 2) NOT NULL,
    benchmark_max_price NUMERIC(15, 2) NOT NULL,
    benchmark_avg_price NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 9. REGISTERED ASSETS (Cross-Case Registry) TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS registered_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    serial_number VARCHAR(150) NOT NULL UNIQUE,
    asset_type VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    model_name VARCHAR(150) NOT NULL,
    original_dealer_id UUID REFERENCES dealers(id) ON DELETE RESTRICT,
    original_case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    installation_lat NUMERIC(10, 7),
    installation_lng NUMERIC(10, 7),
    installed_at DATE,
    registration_status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (registration_status IN ('active', 'decommissioned', 'flagged_duplicate', 'disputed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 10. RISK SIGNALS (Deterministic Evidence & Anomalies) TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS risk_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL CHECK (category IN ('price', 'image', 'geo', 'dealer_network', 'serial_asset', 'document')),
    signal_name VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence_score NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    evidence_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 11. RISK SCORES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL UNIQUE REFERENCES cases(id) ON DELETE CASCADE,
    overall_score INT NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    risk_level VARCHAR(50) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical', 'requires_verification')),
    price_anomaly_score INT NOT NULL DEFAULT 0 CHECK (price_anomaly_score >= 0 AND price_anomaly_score <= 100),
    image_anomaly_score INT NOT NULL DEFAULT 0 CHECK (image_anomaly_score >= 0 AND image_anomaly_score <= 100),
    dealer_network_score INT NOT NULL DEFAULT 0 CHECK (dealer_network_score >= 0 AND dealer_network_score <= 100),
    serial_anomaly_score INT NOT NULL DEFAULT 0 CHECK (serial_anomaly_score >= 0 AND serial_anomaly_score <= 100),
    summary_reasoning TEXT NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 12. ENTITY RELATIONSHIPS (Graph Node / Edge Registry) TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    source_entity_type VARCHAR(50) NOT NULL CHECK (source_entity_type IN ('dealer', 'customer', 'asset', 'phone', 'address', 'pincode', 'gstin')),
    source_entity_id VARCHAR(255) NOT NULL,
    target_entity_type VARCHAR(50) NOT NULL CHECK (target_entity_type IN ('dealer', 'customer', 'asset', 'phone', 'address', 'pincode', 'gstin')),
    target_entity_id VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL, -- e.g., 'shared_address', 'shared_phone', 'dealer_customer_overlap'
    risk_weight NUMERIC(5, 2) DEFAULT 0.00,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 13. VERIFICATION TASKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS verification_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('physical_site_visit', 'oem_serial_check', 'telephonic_verification', 'gst_cross_check', 'document_reupload')),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    assigned_to VARCHAR(255),
    instructions TEXT,
    findings TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ============================================================================
-- 14. AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_dealers_code ON dealers(dealer_code);
CREATE INDEX IF NOT EXISTS idx_dealers_risk_tier ON dealers(risk_tier);
CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code);
CREATE INDEX IF NOT EXISTS idx_cases_dealer ON cases(dealer_id);
CREATE INDEX IF NOT EXISTS idx_cases_customer ON cases(customer_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_risk_level ON cases(risk_level);
CREATE INDEX IF NOT EXISTS idx_invoices_case ON invoices(case_id);
CREATE INDEX IF NOT EXISTS idx_invoices_dealer ON invoices(dealer_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_line_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_images_case ON installation_images(case_id);
CREATE INDEX IF NOT EXISTS idx_images_phash ON installation_images(phash);
CREATE INDEX IF NOT EXISTS idx_registered_assets_serial ON registered_assets(serial_number);
CREATE INDEX IF NOT EXISTS idx_risk_signals_case ON risk_signals(case_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_case ON risk_scores(case_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_case ON entity_relationships(case_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_source ON entity_relationships(source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_target ON entity_relationships(target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_verification_tasks_case ON verification_tasks(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
