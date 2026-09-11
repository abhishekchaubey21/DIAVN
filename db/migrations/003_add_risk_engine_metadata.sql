-- ============================================================================
-- DIAVN: Phase 6 Additive Migration - Explainable Risk Engine Metadata
-- Adds policy versioning, explainable breakdown, recommended actions, and history
-- Preserves all Phase 1-5 data without destructive schema mutations.
-- ============================================================================

DO $$
BEGIN
    -- 1. Additive columns to risk_scores table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'policy_version'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN policy_version VARCHAR(50) DEFAULT 'risk-v1';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'recommended_action'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN recommended_action VARCHAR(255) DEFAULT 'No immediate additional verification indicated by the configured DIAVN rules.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'raw_score'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN raw_score INT DEFAULT 0;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'breakdown'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN breakdown JSONB DEFAULT '[]'::jsonb;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'group_contributions'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN group_contributions JSONB DEFAULT '{}'::jsonb;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_scores' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE risk_scores ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    -- 2. Additive columns to risk_signals table
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_signals' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE risk_signals ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_signals' AND column_name = 'weight'
    ) THEN
        ALTER TABLE risk_signals ADD COLUMN weight NUMERIC(5, 2) DEFAULT 0.00;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'risk_signals' AND column_name = 'signal_type'
    ) THEN
        ALTER TABLE risk_signals ADD COLUMN signal_type VARCHAR(100);
    END IF;
END $$;

-- 3. Policy-versioned risk score history table for auditable assessments
CREATE TABLE IF NOT EXISTS risk_score_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    policy_version VARCHAR(50) NOT NULL,
    overall_score INT NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    raw_score INT NOT NULL DEFAULT 0,
    risk_level VARCHAR(50) NOT NULL,
    recommended_action VARCHAR(255) NOT NULL,
    price_anomaly_score INT NOT NULL DEFAULT 0,
    image_anomaly_score INT NOT NULL DEFAULT 0,
    dealer_network_score INT NOT NULL DEFAULT 0,
    serial_anomaly_score INT NOT NULL DEFAULT 0,
    breakdown JSONB NOT NULL DEFAULT '[]'::jsonb,
    group_contributions JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary_reasoning TEXT NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_score_history_case ON risk_score_history(case_id);
CREATE INDEX IF NOT EXISTS idx_risk_score_history_policy ON risk_score_history(policy_version);
