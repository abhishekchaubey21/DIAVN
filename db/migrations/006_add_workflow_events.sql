-- =============================================================================
-- Migration 006: Workflow Events Outbox for Phase 9 Alerts & Automation
-- =============================================================================

CREATE TABLE IF NOT EXISTS workflow_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(64) NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    event_version VARCHAR(16) NOT NULL DEFAULT 'event-v1',
    case_id VARCHAR(64) NOT NULL,
    pipeline_run_id VARCHAR(64),
    payload JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, PROCESSING, DELIVERED, FAILED, RETRY_PENDING
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_attempt_at TIMESTAMPTZ DEFAULT NOW(),
    locked_at TIMESTAMPTZ,
    locked_by VARCHAR(64),
    last_attempt_at TIMESTAMPTZ,
    last_error TEXT,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for case-specific event lookups
CREATE INDEX IF NOT EXISTS idx_workflow_events_case_id ON workflow_events(case_id);

-- Index for fast outbox polling and atomic worker claims
CREATE INDEX IF NOT EXISTS idx_workflow_events_dispatch_queue ON workflow_events(status, next_attempt_at) WHERE status IN ('PENDING', 'RETRY_PENDING');

-- Unique lookup by event_id
CREATE INDEX IF NOT EXISTS idx_workflow_events_event_id ON workflow_events(event_id);
