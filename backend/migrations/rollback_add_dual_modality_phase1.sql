-- ===================================
-- PHASE 1A: DUAL MODALITY SUPPORT
-- ROLLBACK Migration
-- ===================================
-- Date: 2025-11-03
-- Purpose: Rollback dual content modality changes
-- Impact: Removes 29 columns, 5 indexes, 2 views, 1 trigger, 4 pipeline stages
-- Safety: Backs up data before deletion
-- Forward: See add_dual_modality_phase1.sql
-- ===================================

BEGIN;

-- ===================================
-- SECTION 1: BACKUP DATA (OPTIONAL)
-- Create backup tables before dropping
-- ===================================

-- Backup modality data from content_requests
CREATE TABLE IF NOT EXISTS content_requests_modality_backup AS
SELECT
    id,
    requested_modalities,
    preferred_modality,
    modality_preferences,
    output_formats
FROM content_requests
WHERE requested_modalities IS NOT NULL;

-- Backup modality data from content_metadata
CREATE TABLE IF NOT EXISTS content_metadata_modality_backup AS
SELECT
    content_id,
    modality_type,
    text_content,
    text_language,
    audio_url,
    audio_language,
    audio_duration_seconds,
    captions_url,
    captions_format,
    image_urls,
    supported_formats
FROM content_metadata
WHERE modality_type IS NOT NULL;

-- Backup user preferences
CREATE TABLE IF NOT EXISTS users_modality_backup AS
SELECT
    user_id,
    content_modality_preferences,
    accessibility_settings,
    language_preference
FROM users
WHERE content_modality_preferences IS NOT NULL;

RAISE NOTICE 'Backup tables created successfully';

-- ===================================
-- SECTION 2: DROP TRIGGERS
-- ===================================

DROP TRIGGER IF EXISTS trigger_update_content_request_output_formats ON content_metadata;
DROP FUNCTION IF EXISTS update_content_request_output_formats();

RAISE NOTICE 'Triggers dropped';

-- ===================================
-- SECTION 3: DROP VIEWS
-- ===================================

DROP VIEW IF EXISTS content_modality_usage_summary;
DROP VIEW IF EXISTS user_modality_preferences_summary;

RAISE NOTICE 'Views dropped';

-- ===================================
-- SECTION 4: DROP INDEXES
-- ===================================

DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_requested_modalities_gin;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_modality_status;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_metadata_modality_type;
DROP INDEX CONCURRENTLY IF EXISTS idx_users_language_preference;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_metadata_supported_formats_gin;

RAISE NOTICE 'Indexes dropped';

-- ===================================
-- SECTION 5: REMOVE PIPELINE STAGES
-- ===================================

DELETE FROM pipeline_stage_definitions WHERE stage_name IN (
    'text_generation',
    'audio_synthesis',
    'image_generation',
    'format_conversion'
);

RAISE NOTICE 'Pipeline stages removed';

-- ===================================
-- SECTION 6: DROP COLUMNS - REQUEST_METRICS
-- ===================================

ALTER TABLE request_metrics
    DROP COLUMN IF EXISTS text_request_count,
    DROP COLUMN IF EXISTS audio_request_count,
    DROP COLUMN IF EXISTS video_request_count,
    DROP COLUMN IF EXISTS image_request_count,
    DROP COLUMN IF EXISTS avg_text_duration_seconds,
    DROP COLUMN IF EXISTS avg_audio_duration_seconds,
    DROP COLUMN IF EXISTS avg_video_duration_seconds,
    DROP COLUMN IF EXISTS avg_image_duration_seconds;

RAISE NOTICE 'Request metrics columns dropped';

-- ===================================
-- SECTION 7: DROP COLUMNS - USERS
-- ===================================

ALTER TABLE users
    DROP COLUMN IF EXISTS content_modality_preferences,
    DROP COLUMN IF EXISTS accessibility_settings,
    DROP COLUMN IF EXISTS language_preference;

RAISE NOTICE 'User modality columns dropped';

-- ===================================
-- SECTION 8: DROP COLUMNS - CONTENT_METADATA
-- ===================================

ALTER TABLE content_metadata
    DROP COLUMN IF EXISTS modality_type,
    DROP COLUMN IF EXISTS text_content,
    DROP COLUMN IF EXISTS text_language,
    DROP COLUMN IF EXISTS audio_url,
    DROP COLUMN IF EXISTS audio_language,
    DROP COLUMN IF EXISTS audio_duration_seconds,
    DROP COLUMN IF EXISTS captions_url,
    DROP COLUMN IF EXISTS captions_format,
    DROP COLUMN IF EXISTS image_urls,
    DROP COLUMN IF EXISTS supported_formats;

RAISE NOTICE 'Content metadata modality columns dropped';

-- ===================================
-- SECTION 9: DROP COLUMNS - CONTENT_REQUESTS
-- ===================================

-- Drop CHECK constraint first
ALTER TABLE content_requests
    DROP CONSTRAINT IF EXISTS check_preferred_modality_valid;

-- Drop columns
ALTER TABLE content_requests
    DROP COLUMN IF EXISTS requested_modalities,
    DROP COLUMN IF EXISTS preferred_modality,
    DROP COLUMN IF EXISTS modality_preferences,
    DROP COLUMN IF EXISTS output_formats;

RAISE NOTICE 'Content request modality columns dropped';

-- ===================================
-- SECTION 10: VERIFICATION
-- ===================================

DO $$
BEGIN
    -- Verify columns removed
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'content_requests' AND column_name = 'requested_modalities') THEN
        RAISE EXCEPTION 'Rollback failed: requested_modalities still exists';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'content_metadata' AND column_name = 'modality_type') THEN
        RAISE EXCEPTION 'Rollback failed: modality_type still exists';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'content_modality_preferences') THEN
        RAISE EXCEPTION 'Rollback failed: content_modality_preferences still exists';
    END IF;

    RAISE NOTICE 'Rollback validation: All columns removed successfully';
END $$;

-- ===================================
-- ROLLBACK COMPLETE
-- ===================================

DO $$
BEGIN
    RAISE NOTICE '====================================';
    RAISE NOTICE 'PHASE 1A ROLLBACK COMPLETE';
    RAISE NOTICE 'Date: %', NOW();
    RAISE NOTICE 'Changes rolled back:';
    RAISE NOTICE '  - Removed 4 columns from content_requests';
    RAISE NOTICE '  - Removed 10 columns from content_metadata';
    RAISE NOTICE '  - Removed 3 columns from users';
    RAISE NOTICE '  - Removed 8 columns from request_metrics';
    RAISE NOTICE '  - Dropped 5 indexes';
    RAISE NOTICE '  - Removed 4 pipeline stages';
    RAISE NOTICE '  - Dropped 2 analytics views';
    RAISE NOTICE '  - Dropped 1 trigger';
    RAISE NOTICE '  ';
    RAISE NOTICE 'Backup tables created:';
    RAISE NOTICE '  - content_requests_modality_backup';
    RAISE NOTICE '  - content_metadata_modality_backup';
    RAISE NOTICE '  - users_modality_backup';
    RAISE NOTICE '====================================';
END $$;

COMMIT;
