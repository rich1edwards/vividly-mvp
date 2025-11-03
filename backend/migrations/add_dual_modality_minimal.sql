-- ===================================
-- PHASE 1B: DUAL MODALITY SUPPORT (MINIMAL)
-- Database Migration - Content Requests Only
-- ===================================
-- Date: 2025-11-03
-- Purpose: Add minimal modality support to content_requests table only
-- Impact: Adds 3 columns to content_requests table
-- Safety: All columns added as NULLABLE first, then backfilled with defaults
-- Rollback: See rollback_add_dual_modality_minimal.sql
-- ===================================

-- Add modality fields to content_requests (NULLABLE first for safety)
ALTER TABLE content_requests
    ADD COLUMN IF NOT EXISTS requested_modalities JSONB,
    ADD COLUMN IF NOT EXISTS preferred_modality VARCHAR(50),
    ADD COLUMN IF NOT EXISTS modality_preferences JSONB;

-- Add comments for documentation
COMMENT ON COLUMN content_requests.requested_modalities IS 'Array of requested output formats: ["text", "audio", "video", "images"]. Default: ["video"] for backward compatibility.';
COMMENT ON COLUMN content_requests.preferred_modality IS 'Primary modality type: text, audio, video, images. Default: video';
COMMENT ON COLUMN content_requests.modality_preferences IS 'Format-specific settings: {"video": {"resolution": "1080p", "duration": 180}, "audio": {"voice": "en-US-Neural2-J"}}';

-- Backfill existing records with video defaults
UPDATE content_requests
SET
    requested_modalities = '["video"]'::jsonb,
    preferred_modality = 'video',
    modality_preferences = '{}'::jsonb
WHERE requested_modalities IS NULL;

-- Now add NOT NULL constraints with defaults
ALTER TABLE content_requests
    ALTER COLUMN requested_modalities SET DEFAULT '["video"]'::jsonb,
    ALTER COLUMN requested_modalities SET NOT NULL,
    ALTER COLUMN preferred_modality SET DEFAULT 'video',
    ALTER COLUMN preferred_modality SET NOT NULL,
    ALTER COLUMN modality_preferences SET DEFAULT '{}'::jsonb,
    ALTER COLUMN modality_preferences SET NOT NULL;

-- Add CHECK constraint for valid modality types
ALTER TABLE content_requests
    ADD CONSTRAINT check_preferred_modality_valid
    CHECK (preferred_modality IN ('text', 'audio', 'video', 'images'));

-- Create index for querying requests by modality
-- GIN index for JSONB array containment queries (e.g., WHERE requested_modalities @> '["text"]')
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_requested_modalities_gin
    ON content_requests USING GIN (requested_modalities);

-- Index for filtering requests by preferred modality and status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_modality_status
    ON content_requests (preferred_modality, status)
    WHERE status NOT IN ('completed', 'failed', 'cancelled');

-- ===================================
-- VERIFY MIGRATION SUCCESS
-- ===================================

DO $$
BEGIN
    -- Verify columns added
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'content_requests' AND column_name = 'requested_modalities') THEN
        RAISE EXCEPTION 'Migration failed: requested_modalities column not added';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'content_requests' AND column_name = 'preferred_modality') THEN
        RAISE EXCEPTION 'Migration failed: preferred_modality column not added';
    END IF;

    RAISE NOTICE 'Migration validation: All columns added successfully';
END $$;

-- Check data migration
DO $$
DECLARE
    null_count INTEGER;
BEGIN
    -- Check for NULL values in critical fields
    SELECT COUNT(*) INTO null_count
    FROM content_requests
    WHERE requested_modalities IS NULL OR preferred_modality IS NULL;

    IF null_count > 0 THEN
        RAISE WARNING 'Data migration incomplete: % content_requests have NULL modality fields', null_count;
    ELSE
        RAISE NOTICE 'Data migration validation: All existing records migrated successfully';
    END IF;
END $$;

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE '====================================';
    RAISE NOTICE 'PHASE 1B MINIMAL MIGRATION COMPLETE';
    RAISE NOTICE 'Date: %', NOW();
    RAISE NOTICE 'Changes:';
    RAISE NOTICE '  - Added 3 columns to content_requests';
    RAISE NOTICE '  - Added 2 indexes for performance';
    RAISE NOTICE '  - Backfilled existing records with video defaults';
    RAISE NOTICE 'Next step: Deploy updated code';
    RAISE NOTICE '====================================';
END $$;
