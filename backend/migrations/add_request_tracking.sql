-- Request Tracking System Migration
-- Tracks content generation requests end-to-end through the entire pipeline
--
-- Pipeline Flow:
-- 1. Student submits content request
-- 2. Validation & storage
-- 3. RAG retrieval (Vector Search)
-- 4. Script generation (Gemini)
-- 5. Video generation (Nano Banana)
-- 6. CDN upload & processing
-- 7. Student notification
--
-- Run: psql -h HOST -U USER -d DATABASE -f add_request_tracking.sql

-- Content Request Status Enum (renamed to avoid conflict with student_request.request_status)
CREATE TYPE content_request_status AS ENUM (
    'pending',           -- Request received, not started
    'validating',        -- Validating request parameters
    'retrieving',        -- Retrieving OER content from Vector Search
    'generating_script', -- Generating script with Gemini
    'generating_video',  -- Generating video with Nano Banana
    'processing_video',  -- Processing and uploading to CDN
    'notifying',         -- Sending notification to student
    'completed',         -- Successfully completed
    'failed',            -- Failed at some stage
    'cancelled'          -- Cancelled by user or system
);

-- Content Stage Status Enum
CREATE TYPE content_stage_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'skipped'
);

-- Content Requests Table
CREATE TABLE IF NOT EXISTS content_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Correlation ID for tracing across services
    correlation_id VARCHAR(64) NOT NULL UNIQUE,

    -- Request details
    student_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    topic VARCHAR(500) NOT NULL,
    learning_objective TEXT,
    grade_level VARCHAR(50),
    duration_minutes INTEGER,

    -- Current state
    status content_request_status DEFAULT 'pending' NOT NULL,
    current_stage VARCHAR(100),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,

    -- Results
    video_url TEXT,
    script_text TEXT,
    thumbnail_url TEXT,

    -- Error tracking
    error_message TEXT,
    error_stage VARCHAR(100),
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,

    -- Metadata
    request_metadata JSONB,  -- Original request parameters, user agent, etc.

    -- Performance metrics
    total_duration_seconds INTEGER,

    -- Organization context
    organization_id VARCHAR(100) REFERENCES organizations(organization_id)
);

CREATE INDEX idx_content_requests_correlation ON content_requests(correlation_id);
CREATE INDEX idx_content_requests_student ON content_requests(student_id);
CREATE INDEX idx_content_requests_status ON content_requests(status);
CREATE INDEX idx_content_requests_created ON content_requests(created_at DESC);
CREATE INDEX idx_content_requests_org ON content_requests(organization_id);

COMMENT ON TABLE content_requests IS 'Tracks end-to-end content generation requests';
COMMENT ON COLUMN content_requests.correlation_id IS 'Unique ID for tracing request through all services';
COMMENT ON COLUMN content_requests.progress_percentage IS 'Overall progress 0-100%';


-- Request Stages Table (detailed pipeline tracking)
CREATE TABLE IF NOT EXISTS request_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES content_requests(id) ON DELETE CASCADE,

    -- Stage identification
    stage_name VARCHAR(100) NOT NULL,  -- 'validation', 'rag_retrieval', 'script_generation', etc.
    stage_order INTEGER NOT NULL,

    -- Status
    status content_stage_status DEFAULT 'pending' NOT NULL,

    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Duration
    duration_seconds NUMERIC(10, 3),

    -- Results
    output_data JSONB,

    -- Errors
    error_message TEXT,
    error_details JSONB,

    -- Retries
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Metadata
    stage_metadata JSONB,  -- API response codes, chunk counts, etc.

    CONSTRAINT unique_stage_per_request UNIQUE (request_id, stage_name)
);

CREATE INDEX idx_request_stages_request ON request_stages(request_id, stage_order);
CREATE INDEX idx_request_stages_status ON request_stages(status);

COMMENT ON TABLE request_stages IS 'Detailed tracking of each pipeline stage';
COMMENT ON COLUMN request_stages.stage_order IS 'Order in pipeline (1, 2, 3, ...)';


-- Request Events Table (detailed event log)
CREATE TABLE IF NOT EXISTS request_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES content_requests(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(100) NOT NULL,  -- 'status_change', 'error', 'retry', 'api_call', etc.
    event_message TEXT NOT NULL,

    -- Context
    stage_name VARCHAR(100),
    severity VARCHAR(20),  -- 'info', 'warning', 'error', 'critical'

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Additional data
    event_data JSONB,

    -- Source
    source_service VARCHAR(100),  -- 'api-gateway', 'content-worker', 'nano-banana', etc.
    source_host VARCHAR(255)
);

CREATE INDEX idx_request_events_request ON request_events(request_id, created_at DESC);
CREATE INDEX idx_request_events_type ON request_events(event_type);
CREATE INDEX idx_request_events_severity ON request_events(severity);
CREATE INDEX idx_request_events_created ON request_events(created_at DESC);

COMMENT ON TABLE request_events IS 'Detailed event log for debugging and monitoring';


-- Request Metrics Table (aggregated performance metrics)
CREATE TABLE IF NOT EXISTS request_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Time bucket
    time_bucket TIMESTAMP NOT NULL,  -- Hourly buckets

    -- Aggregation scope
    organization_id VARCHAR(100) REFERENCES organizations(organization_id),

    -- Metrics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    cancelled_requests INTEGER DEFAULT 0,

    -- Average durations (seconds)
    avg_total_duration NUMERIC(10, 2),
    avg_validation_duration NUMERIC(10, 2),
    avg_rag_duration NUMERIC(10, 2),
    avg_script_duration NUMERIC(10, 2),
    avg_video_duration NUMERIC(10, 2),

    -- Error breakdown
    validation_errors INTEGER DEFAULT 0,
    rag_errors INTEGER DEFAULT 0,
    script_errors INTEGER DEFAULT 0,
    video_errors INTEGER DEFAULT 0,
    upload_errors INTEGER DEFAULT 0,

    -- Circuit breaker stats
    circuit_breaker_open_count INTEGER DEFAULT 0,

    -- Metadata
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_metrics_bucket UNIQUE (time_bucket, organization_id)
);

CREATE INDEX idx_request_metrics_time ON request_metrics(time_bucket DESC);
CREATE INDEX idx_request_metrics_org ON request_metrics(organization_id);

COMMENT ON TABLE request_metrics IS 'Aggregated hourly metrics for dashboard';


-- Function to calculate progress percentage
CREATE OR REPLACE FUNCTION calculate_request_progress(req_id UUID)
RETURNS INTEGER AS $$
DECLARE
    total_stages INTEGER;
    completed_stages INTEGER;
    progress INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_stages
    FROM request_stages
    WHERE request_id = req_id;

    SELECT COUNT(*) INTO completed_stages
    FROM request_stages
    WHERE request_id = req_id AND status = 'completed';

    IF total_stages = 0 THEN
        RETURN 0;
    END IF;

    progress := (completed_stages * 100) / total_stages;
    RETURN progress;
END;
$$ LANGUAGE plpgsql;


-- Function to update request progress
CREATE OR REPLACE FUNCTION update_request_progress()
RETURNS TRIGGER AS $$
BEGIN
    -- Update progress percentage in content_requests
    UPDATE content_requests
    SET
        progress_percentage = calculate_request_progress(NEW.request_id),
        current_stage = NEW.stage_name
    WHERE id = NEW.request_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_progress_on_stage_change
    AFTER INSERT OR UPDATE ON request_stages
    FOR EACH ROW
    EXECUTE FUNCTION update_request_progress();


-- Function to log request events automatically
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        INSERT INTO request_events (
            request_id,
            event_type,
            event_message,
            severity,
            event_data
        ) VALUES (
            NEW.id,
            'status_change',
            format('Status changed from %s to %s', OLD.status, NEW.status),
            CASE
                WHEN NEW.status = 'failed' THEN 'error'
                WHEN NEW.status = 'completed' THEN 'info'
                ELSE 'info'
            END,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'current_stage', NEW.current_stage
            )
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_request_status_changes
    AFTER UPDATE ON content_requests
    FOR EACH ROW
    EXECUTE FUNCTION log_status_change();


-- Predefined pipeline stages (insert default configuration)
CREATE TABLE IF NOT EXISTS pipeline_stage_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stage_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    stage_order INTEGER NOT NULL,
    estimated_duration_seconds INTEGER,
    description TEXT,
    is_critical BOOLEAN DEFAULT true  -- If critical, failure means entire request fails
);

INSERT INTO pipeline_stage_definitions (stage_name, display_name, stage_order, estimated_duration_seconds, is_critical) VALUES
    ('validation', 'Request Validation', 1, 2, true),
    ('rag_retrieval', 'OER Content Retrieval', 2, 10, true),
    ('script_generation', 'AI Script Generation', 3, 30, true),
    ('video_generation', 'Video Generation', 4, 120, true),
    ('video_processing', 'Video Processing & Upload', 5, 20, true),
    ('notification', 'Student Notification', 6, 2, false)
ON CONFLICT (stage_name) DO NOTHING;

COMMENT ON TABLE pipeline_stage_definitions IS 'Configuration for pipeline stages';


-- View for dashboard: active requests with stage details
CREATE OR REPLACE VIEW active_requests_dashboard AS
SELECT
    cr.id,
    cr.correlation_id,
    cr.student_id,
    CONCAT(u.first_name, ' ', u.last_name) as student_name,
    cr.topic,
    cr.status,
    cr.current_stage,
    cr.progress_percentage,
    cr.created_at,
    cr.started_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - cr.created_at))::INTEGER as elapsed_seconds,
    cr.retry_count,
    cr.error_message,
    cr.error_stage,
    -- Stage details as JSON array
    (
        SELECT json_agg(
            json_build_object(
                'stage_name', rs.stage_name,
                'status', rs.status,
                'duration_seconds', rs.duration_seconds,
                'error_message', rs.error_message
            ) ORDER BY rs.stage_order
        )
        FROM request_stages rs
        WHERE rs.request_id = cr.id
    ) as stages
FROM content_requests cr
LEFT JOIN users u ON cr.student_id = u.user_id
WHERE cr.status NOT IN ('completed', 'failed', 'cancelled')
ORDER BY cr.created_at DESC;

COMMENT ON VIEW active_requests_dashboard IS 'Real-time view of active requests for dashboard';


-- View for metrics dashboard
CREATE OR REPLACE VIEW request_metrics_summary AS
SELECT
    date_trunc('hour', created_at) as hour,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status = 'completed') as successful,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status IN ('pending', 'validating', 'retrieving', 'generating_script', 'generating_video', 'processing_video', 'notifying')) as in_progress,
    AVG(total_duration_seconds) FILTER (WHERE status = 'completed') as avg_duration,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY total_duration_seconds) FILTER (WHERE status = 'completed') as p95_duration,
    COUNT(*) FILTER (WHERE retry_count > 0) as retried_requests
FROM content_requests
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY date_trunc('hour', created_at)
ORDER BY hour DESC;

COMMENT ON VIEW request_metrics_summary IS 'Hourly aggregated metrics for last 24 hours';


-- Rollback script (save as rollback_request_tracking.sql)
-- DROP VIEW IF EXISTS request_metrics_summary CASCADE;
-- DROP VIEW IF EXISTS active_requests_dashboard CASCADE;
-- DROP TABLE IF EXISTS pipeline_stage_definitions CASCADE;
-- DROP TRIGGER IF EXISTS log_request_status_changes ON content_requests;
-- DROP TRIGGER IF EXISTS update_progress_on_stage_change ON request_stages;
-- DROP FUNCTION IF EXISTS log_status_change();
-- DROP FUNCTION IF EXISTS update_request_progress();
-- DROP FUNCTION IF EXISTS calculate_request_progress(UUID);
-- DROP TABLE IF EXISTS request_metrics CASCADE;
-- DROP TABLE IF EXISTS request_events CASCADE;
-- DROP TABLE IF EXISTS request_stages CASCADE;
-- DROP TABLE IF EXISTS content_requests CASCADE;
-- DROP TYPE IF EXISTS content_stage_status;
-- DROP TYPE IF EXISTS content_request_status;
