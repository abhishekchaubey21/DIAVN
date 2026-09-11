-- ============================================================================
-- DIAVN: Phase 5 Additive Migration - Embedding Model Metadata
-- Adds model versioning columns to installation_images table without destructive changes
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'installation_images' AND column_name = 'embedding_model'
    ) THEN
        ALTER TABLE installation_images ADD COLUMN embedding_model VARCHAR(50) DEFAULT 'resnet18';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'installation_images' AND column_name = 'embedding_model_version'
    ) THEN
        ALTER TABLE installation_images ADD COLUMN embedding_model_version VARCHAR(50) DEFAULT '1.0';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'installation_images' AND column_name = 'embedding_dimension'
    ) THEN
        ALTER TABLE installation_images ADD COLUMN embedding_dimension INT DEFAULT 512;
    END IF;
END $$;
