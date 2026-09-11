-- ============================================================================
-- DIAVN Database Schema Migration: 005_add_pipeline_orchestration.sql
-- Project: Dealer Integrity & Asset Verification Network (DIAVN)
-- Phase 8: Additive Case-Level Verification Pipeline Runs, Stages, & DB Locking
-- ============================================================================

-- 1. Verification Pipeline Runs Table
CREATE TABLE IF NOT EXISTS verification_pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'QUEUED' CHECK (status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'PARTIAL', 'FAILED')),
    current_stage VARCHAR(100),
    pipeline_version VARCHAR(50) NOT NULL DEFAULT 'pipeline-v1',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    total_duration_ms BIGINT DEFAULT 0,
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Verification Pipeline Stage Execution Records Table
CREATE TABLE IF NOT EXISTS verification_pipeline_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_run_id UUID NOT NULL REFERENCES verification_pipeline_runs(id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'SKIPPED', 'INCONCLUSIVE', 'FAILED')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms BIGINT DEFAULT 0,
    result_summary JSONB DEFAULT '{}'::jsonb,
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Database-Enforced Concurrency Guard (Unique Partial Index on Active Pipeline Runs)
-- Prevents race conditions from simultaneous requests creating duplicate active pipeline runs per case.
CREATE UNIQUE INDEX IF NOT EXISTS idx_active_pipeline_run_per_case 
ON verification_pipeline_runs(case_id) 
WHERE status IN ('QUEUED', 'PROCESSING');

-- 4. Query Acceleration Indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_case_id ON verification_pipeline_runs(case_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON verification_pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_stages_run_id ON verification_pipeline_stages(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_stages_case_id ON verification_pipeline_stages(case_id);
