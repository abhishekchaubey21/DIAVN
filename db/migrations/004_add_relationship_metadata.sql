-- ============================================================================
-- DIAVN Database Schema Migration: 004_add_relationship_metadata.sql
-- Project: Dealer Integrity & Asset Verification Network (DIAVN)
-- Phase 7: Additive Relationship Metadata, Policy Versioning, & Query Indexes
-- ============================================================================

DO $$
BEGIN
    -- 1. Additive columns to entity_relationships table if not present
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'entity_relationships' AND column_name = 'policy_version'
    ) THEN
        ALTER TABLE entity_relationships ADD COLUMN policy_version VARCHAR(50) DEFAULT 'relationship-v1';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'entity_relationships' AND column_name = 'category'
    ) THEN
        ALTER TABLE entity_relationships ADD COLUMN category VARCHAR(50) DEFAULT 'structural';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'entity_relationships' AND column_name = 'strength'
    ) THEN
        ALTER TABLE entity_relationships ADD COLUMN strength NUMERIC(5, 2) DEFAULT 1.00;
    END IF;
END $$;

-- 2. Additive indexing for relationship query performance
CREATE INDEX IF NOT EXISTS idx_entity_rel_case_id ON entity_relationships(case_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_source ON entity_relationships(source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_target ON entity_relationships(target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_rel_type ON entity_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_entity_rel_category ON entity_relationships(category);
