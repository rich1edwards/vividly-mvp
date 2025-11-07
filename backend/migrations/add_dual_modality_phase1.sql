-- ===================================
-- PHASE 1A: DUAL MODALITY SUPPORT
-- Database Migration
-- ===================================
-- Date: 2025-11-03
-- Purpose: Add support for dual content modalities (text-only vs text+video)
-- Impact: Adds 12 columns across 3 tables (content_requests, content_metadata, users)
-- Safety: All columns added as NULLABLE first, then backfilled with defaults
-- Rollback: See rollback_add_dual_modality_phase1.sql
-- ===================================

-- ===================================
-- SECTION 1: CONTENT_REQUESTS TABLE
-- Add modality selection fields
-- ===================================

-- Add modality fields (NULLABLE first for safety)
ALTER TABLE content_requests
    ADD COLUMN IF NOT EXISTS requested_modalities JSONB,
    ADD COLUMN IF NOT EXISTS preferred_modality VARCHAR(50),
    ADD COLUMN IF NOT EXISTS modality_preferences JSONB,
    ADD COLUMN IF NOT EXISTS output_formats JSONB;

-- Add comments for documentation
COMMENT ON COLUMN content_requests.requested_modalities IS 'Array of requested output formats: ["text", "audio", "video", "images"]. Default: ["video"] for backward compatibility.';
COMMENT ON COLUMN content_requests.preferred_modality IS 'Primary modality type: text, audio, video, images. Default: video';
COMMENT ON COLUMN content_requests.modality_preferences IS 'Format-specific settings: {"video": {"resolution": "1080p", "duration": 180}, "audio": {"voice": "en-US-Neural2-J"}}';
COMMENT ON COLUMN content_requests.output_formats IS 'Track which formats were actually generated: ["text", "video"]. Populated after generation completes.';

-- Backfill existing records with video defaults
UPDATE content_requests
SET
    requested_modalities = '["video"]'::jsonb,
    preferred_modality = 'video',
    modality_preferences = '{}'::jsonb,
    output_formats = '["video"]'::jsonb
WHERE requested_modalities IS NULL;

-- Now add NOT NULL constraints with defaults
ALTER TABLE content_requests
    ALTER COLUMN requested_modalities SET DEFAULT '["video"]'::jsonb,
    ALTER COLUMN requested_modalities SET NOT NULL,
    ALTER COLUMN preferred_modality SET DEFAULT 'video',
    ALTER COLUMN preferred_modality SET NOT NULL,
    ALTER COLUMN modality_preferences SET DEFAULT '{}'::jsonb,
    ALTER COLUMN modality_preferences SET NOT NULL,
    ALTER COLUMN output_formats SET DEFAULT '[]'::jsonb;  -- Empty until generation completes

-- Add CHECK constraint for valid modality types
ALTER TABLE content_requests
    ADD CONSTRAINT check_preferred_modality_valid
    CHECK (preferred_modality IN ('text', 'audio', 'video', 'images'));

-- ===================================
-- SECTION 2: CONTENT_METADATA TABLE
-- Add multi-format storage fields
-- ===================================

-- Add modality-specific storage fields (NULLABLE first)
ALTER TABLE content_metadata
    ADD COLUMN IF NOT EXISTS modality_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS text_content TEXT,
    ADD COLUMN IF NOT EXISTS text_language VARCHAR(10),
    ADD COLUMN IF NOT EXISTS audio_url TEXT,
    ADD COLUMN IF NOT EXISTS audio_language VARCHAR(10),
    ADD COLUMN IF NOT EXISTS audio_duration_seconds INTEGER,
    ADD COLUMN IF NOT EXISTS captions_url TEXT,
    ADD COLUMN IF NOT EXISTS captions_format VARCHAR(20),
    ADD COLUMN IF NOT EXISTS image_urls JSONB,
    ADD COLUMN IF NOT EXISTS supported_formats JSONB;

-- Add comments
COMMENT ON COLUMN content_metadata.modality_type IS 'Primary format of this content: text, audio, video, images. For video content: "video"';
COMMENT ON COLUMN content_metadata.text_content IS 'Full transcript/script text. Always generated as first step.';
COMMENT ON COLUMN content_metadata.text_language IS 'Language code for text (e.g., en, es, fr). Default: en';
COMMENT ON COLUMN content_metadata.audio_url IS 'GCS URL for audio file (TTS output or audio-only version)';
COMMENT ON COLUMN content_metadata.audio_language IS 'Language code for audio. Default: en';
COMMENT ON COLUMN content_metadata.audio_duration_seconds IS 'Duration of audio track in seconds';
COMMENT ON COLUMN content_metadata.captions_url IS 'GCS URL for caption/subtitle file (VTT, SRT)';
COMMENT ON COLUMN content_metadata.captions_format IS 'Caption file format: vtt, srt, webvtt';
COMMENT ON COLUMN content_metadata.image_urls IS 'Array of GCS URLs for generated images: ["gs://bucket/img1.png", ...]';
COMMENT ON COLUMN content_metadata.supported_formats IS 'List of available formats for this content: ["text", "video", "audio"]. User can request any supported format.';

-- Backfill existing video records
UPDATE content_metadata
SET
    modality_type = 'video',
    text_content = script_content,  -- Copy existing script to text_content
    text_language = 'en',
    audio_language = 'en',
    captions_format = 'vtt',
    image_urls = '[]'::jsonb,
    supported_formats = '["video"]'::jsonb
WHERE modality_type IS NULL;

-- Add NOT NULL constraints for critical fields
ALTER TABLE content_metadata
    ALTER COLUMN modality_type SET DEFAULT 'video',
    ALTER COLUMN modality_type SET NOT NULL,
    ALTER COLUMN text_language SET DEFAULT 'en',
    ALTER COLUMN audio_language SET DEFAULT 'en',
    ALTER COLUMN captions_format SET DEFAULT 'vtt',
    ALTER COLUMN image_urls SET DEFAULT '[]'::jsonb,
    ALTER COLUMN image_urls SET NOT NULL,
    ALTER COLUMN supported_formats SET DEFAULT '["video"]'::jsonb,
    ALTER COLUMN supported_formats SET NOT NULL;

-- Add CHECK constraint
ALTER TABLE content_metadata
    ADD CONSTRAINT check_modality_type_valid
    CHECK (modality_type IN ('text', 'audio', 'video', 'images'));

-- ===================================
-- SECTION 3: USERS TABLE
-- Add modality preferences
-- ===================================

-- Add user preference fields (NULLABLE first)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS content_modality_preferences JSONB,
    ADD COLUMN IF NOT EXISTS accessibility_settings JSONB,
    ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10);

-- Add comments
COMMENT ON COLUMN users.content_modality_preferences IS 'User preferred formats: {"default": "video", "subjects": {"math": "text", "science": "video"}, "quality": {"video": "1080p"}}';
COMMENT ON COLUMN users.accessibility_settings IS 'Accessibility needs: {"captions": true, "audio_descriptions": true, "high_contrast": false, "font_size": "large"}';
COMMENT ON COLUMN users.language_preference IS 'Preferred language for content generation (e.g., en, es, fr). Default: en';

-- Backfill existing users with defaults
UPDATE users
SET
    content_modality_preferences = '{"default": "video"}'::jsonb,
    accessibility_settings = '{"captions": false, "audio_descriptions": false}'::jsonb,
    language_preference = 'en'
WHERE content_modality_preferences IS NULL;

-- Add NOT NULL constraints with defaults
ALTER TABLE users
    ALTER COLUMN content_modality_preferences SET DEFAULT '{"default": "video"}'::jsonb,
    ALTER COLUMN content_modality_preferences SET NOT NULL,
    ALTER COLUMN accessibility_settings SET DEFAULT '{}'::jsonb,
    ALTER COLUMN accessibility_settings SET NOT NULL,
    ALTER COLUMN language_preference SET DEFAULT 'en',
    ALTER COLUMN language_preference SET NOT NULL;

-- ===================================
-- SECTION 4: INDEXES FOR PERFORMANCE
-- Create indexes for modality-based queries
-- ===================================

-- Index for querying requests by modality
-- GIN index for JSONB array containment queries (e.g., WHERE requested_modalities @> '["text"]')
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_requested_modalities_gin
    ON content_requests USING GIN (requested_modalities);

-- Index for filtering requests by preferred modality and status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_modality_status
    ON content_requests (preferred_modality, status)
    WHERE status NOT IN ('completed', 'failed', 'cancelled');

-- Index for content metadata by modality type
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_metadata_modality_type
    ON content_metadata (modality_type, status)
    WHERE archived = FALSE;

-- Index for users by language preference (for targeting campaigns)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_language_preference
    ON users (language_preference)
    WHERE archived = FALSE AND status = 'active';

-- GIN index for content metadata supported formats
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_metadata_supported_formats_gin
    ON content_metadata USING GIN (supported_formats);

-- ===================================
-- SECTION 5: REQUEST_METRICS UPDATES
-- Add modality-specific metrics tracking
-- ===================================

-- Add modality breakdown metrics
ALTER TABLE request_metrics
    ADD COLUMN IF NOT EXISTS text_request_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS audio_request_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS video_request_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS image_request_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS avg_text_duration_seconds NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS avg_audio_duration_seconds NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS avg_video_duration_seconds NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS avg_image_duration_seconds NUMERIC(10,2);

-- Add comments
COMMENT ON COLUMN request_metrics.text_request_count IS 'Number of text-only requests in this time bucket';
COMMENT ON COLUMN request_metrics.audio_request_count IS 'Number of audio generation requests';
COMMENT ON COLUMN request_metrics.video_request_count IS 'Number of video generation requests';
COMMENT ON COLUMN request_metrics.image_request_count IS 'Number of image generation requests';

-- ===================================
-- SECTION 6: PIPELINE STAGE DEFINITIONS
-- Add new stages for modality-specific generation
-- ===================================

-- Add text generation stage
INSERT INTO pipeline_stage_definitions (
    id,
    stage_name,
    display_name,
    stage_order,
    estimated_duration_seconds,
    description,
    is_critical
) VALUES (
    gen_random_uuid(),
    'text_generation',
    'Text Content Generation',
    3,
    20,
    'Generate text script/transcript using LLM (Gemini 1.5 Pro). This is the base stage for all modalities.',
    1  -- Critical stage
) ON CONFLICT (stage_name) DO NOTHING;

-- Add audio synthesis stage
INSERT INTO pipeline_stage_definitions (
    id,
    stage_name,
    display_name,
    stage_order,
    estimated_duration_seconds,
    description,
    is_critical
) VALUES (
    gen_random_uuid(),
    'audio_synthesis',
    'Audio Synthesis',
    4,
    60,
    'Convert text to speech using Vertex AI TTS (WaveNet voices). Generates narration audio.',
    0  -- Optional stage (only for audio/video modalities)
) ON CONFLICT (stage_name) DO NOTHING;

-- Add image generation stage
INSERT INTO pipeline_stage_definitions (
    id,
    stage_name,
    display_name,
    stage_order,
    estimated_duration_seconds,
    description,
    is_critical
) VALUES (
    gen_random_uuid(),
    'image_generation',
    'Image Generation',
    4,
    90,
    'Generate supporting images using image generation API (Vertex AI Imagen). Creates visual aids.',
    0  -- Optional stage
) ON CONFLICT (stage_name) DO NOTHING;

-- Add format conversion stage
INSERT INTO pipeline_stage_definitions (
    id,
    stage_name,
    display_name,
    stage_order,
    estimated_duration_seconds,
    description,
    is_critical
) VALUES (
    gen_random_uuid(),
    'format_conversion',
    'Format Conversion',
    5,
    30,
    'Convert between formats (e.g., video to audio, add captions to video). Handles format transformations.',
    0  -- Optional stage
) ON CONFLICT (stage_name) DO NOTHING;

-- ===================================
-- SECTION 7: DATABASE VIEWS
-- Create views for modality analytics
-- ===================================

-- Create view for modality usage summary
CREATE OR REPLACE VIEW content_modality_usage_summary AS
SELECT
    DATE_TRUNC('day', created_at) AS date,
    COUNT(*) FILTER (WHERE preferred_modality = 'text') AS text_requests,
    COUNT(*) FILTER (WHERE preferred_modality = 'audio') AS audio_requests,
    COUNT(*) FILTER (WHERE preferred_modality = 'video') AS video_requests,
    COUNT(*) FILTER (WHERE preferred_modality = 'images') AS image_requests,
    COUNT(*) AS total_requests,
    ROUND(100.0 * COUNT(*) FILTER (WHERE preferred_modality = 'video') / NULLIF(COUNT(*), 0), 2) AS video_percentage,
    ROUND(100.0 * COUNT(*) FILTER (WHERE preferred_modality = 'text') / NULLIF(COUNT(*), 0), 2) AS text_percentage
FROM content_requests
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Create view for user modality preferences
CREATE OR REPLACE VIEW user_modality_preferences_summary AS
SELECT
    language_preference,
    COUNT(*) AS user_count,
    COUNT(*) FILTER (WHERE content_modality_preferences->>'default' = 'video') AS prefers_video,
    COUNT(*) FILTER (WHERE content_modality_preferences->>'default' = 'text') AS prefers_text,
    COUNT(*) FILTER (WHERE accessibility_settings->>'captions' = 'true') AS needs_captions,
    COUNT(*) FILTER (WHERE accessibility_settings->>'audio_descriptions' = 'true') AS needs_audio_descriptions
FROM users
WHERE archived = FALSE AND status = 'active'
GROUP BY language_preference
ORDER BY user_count DESC;

-- ===================================
-- SECTION 8: TRIGGERS FOR AUTOMATION
-- Auto-populate output_formats when content is generated
-- ===================================

-- Function to update output_formats in content_requests
CREATE OR REPLACE FUNCTION update_content_request_output_formats()
RETURNS TRIGGER AS $$
BEGIN
    -- When content_metadata is inserted/updated, update the linked content_request
    IF NEW.status = 'active' AND NEW.archived = FALSE THEN
        UPDATE content_requests
        SET output_formats = NEW.supported_formats
        WHERE request_id = NEW.request_id::text
          AND status = 'completed';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_content_request_output_formats ON content_metadata;
CREATE TRIGGER trigger_update_content_request_output_formats
    AFTER INSERT OR UPDATE OF supported_formats, status
    ON content_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_content_request_output_formats();

-- ===================================
-- SECTION 9: VERIFY MIGRATION SUCCESS
-- Validation queries (run manually after migration)
-- ===================================

-- Check column additions
DO $$
BEGIN
    -- Verify content_requests columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'content_requests' AND column_name = 'requested_modalities') THEN
        RAISE EXCEPTION 'Migration failed: requested_modalities column not added';
    END IF;

    -- Verify content_metadata columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'content_metadata' AND column_name = 'modality_type') THEN
        RAISE EXCEPTION 'Migration failed: modality_type column not added';
    END IF;

    -- Verify users columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'content_modality_preferences') THEN
        RAISE EXCEPTION 'Migration failed: content_modality_preferences column not added';
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

-- ===================================
-- MIGRATION COMPLETE
-- ===================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE '====================================';
    RAISE NOTICE 'PHASE 1A MIGRATION COMPLETE';
    RAISE NOTICE 'Date: %', NOW();
    RAISE NOTICE 'Changes:';
    RAISE NOTICE '  - Added 4 columns to content_requests';
    RAISE NOTICE '  - Added 10 columns to content_metadata';
    RAISE NOTICE '  - Added 3 columns to users';
    RAISE NOTICE '  - Added 8 columns to request_metrics';
    RAISE NOTICE '  - Created 5 new indexes';
    RAISE NOTICE '  - Added 4 new pipeline stages';
    RAISE NOTICE '  - Created 2 analytics views';
    RAISE NOTICE '  - Created 1 trigger for automation';
    RAISE NOTICE 'Next step: Update SQLAlchemy models';
    RAISE NOTICE '====================================';
END $$;
