-- ===================================
-- ROLLBACK: PHASE 1B DUAL MODALITY (MINIMAL)
-- ===================================
-- Date: 2025-11-03
-- Purpose: Rollback minimal modality columns from content_requests
-- WARNING: This will delete modality preference data
-- ===================================

-- Drop indexes first
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_requested_modalities_gin;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_modality_status;

-- Drop constraint
ALTER TABLE content_requests
    DROP CONSTRAINT IF EXISTS check_preferred_modality_valid;

-- Drop columns
ALTER TABLE content_requests
    DROP COLUMN IF EXISTS requested_modalities,
    DROP COLUMN IF EXISTS preferred_modality,
    DROP COLUMN IF EXISTS modality_preferences;

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE '====================================';
    RAISE NOTICE 'PHASE 1B ROLLBACK COMPLETE';
    RAISE NOTICE 'Date: %', NOW();
    RAISE NOTICE 'Removed modality columns from content_requests';
    RAISE NOTICE '====================================';
END $$;
