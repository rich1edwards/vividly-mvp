-- Feature Flags Migration
-- Implements feature flags for controlled rollouts and A/B testing
--
-- Features:
-- - Global and organization-specific flags
-- - Percentage rollout (0-100%)
-- - User-specific overrides
-- - Audit trail
--
-- Run: psql -h HOST -U USER -d DATABASE -f add_feature_flags.sql

-- Feature Flags Table
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Flag state
    enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),

    -- Organization-specific (NULL = global)
    organization_id VARCHAR(100) REFERENCES organizations(organization_id) ON DELETE CASCADE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) REFERENCES users(user_id),

    -- Index for fast lookups
    CONSTRAINT unique_flag_per_org UNIQUE (key, organization_id)
);

CREATE INDEX idx_feature_flags_key ON feature_flags(key);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(enabled);
CREATE INDEX idx_feature_flags_org ON feature_flags(organization_id);

COMMENT ON TABLE feature_flags IS 'Feature flags for controlled rollouts and A/B testing';
COMMENT ON COLUMN feature_flags.key IS 'Unique identifier for the flag (e.g., "video_generation_v2")';
COMMENT ON COLUMN feature_flags.rollout_percentage IS 'Percentage of users who should see this feature (0-100)';
COMMENT ON COLUMN feature_flags.organization_id IS 'Organization-specific flag (NULL for global)';


-- Feature Flag Overrides Table (User-specific)
CREATE TABLE IF NOT EXISTS feature_flag_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Override state
    enabled BOOLEAN NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) REFERENCES users(user_id),
    reason TEXT,

    -- Ensure one override per user per flag
    CONSTRAINT unique_override_per_user UNIQUE (flag_id, user_id)
);

CREATE INDEX idx_feature_flag_overrides_user ON feature_flag_overrides(user_id);
CREATE INDEX idx_feature_flag_overrides_flag ON feature_flag_overrides(flag_id);

COMMENT ON TABLE feature_flag_overrides IS 'User-specific feature flag overrides for testing';
COMMENT ON COLUMN feature_flag_overrides.reason IS 'Reason for override (e.g., "Beta tester")';


-- Feature Flag Audit Log
CREATE TABLE IF NOT EXISTS feature_flag_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_id UUID NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,

    -- Change details
    action VARCHAR(50) NOT NULL, -- 'created', 'enabled', 'disabled', 'rollout_changed', 'deleted'
    old_value JSONB,
    new_value JSONB,

    -- Actor
    changed_by VARCHAR(100) REFERENCES users(user_id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Context
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_feature_flag_audit_flag ON feature_flag_audit(flag_id);
CREATE INDEX idx_feature_flag_audit_changed_at ON feature_flag_audit(changed_at DESC);

COMMENT ON TABLE feature_flag_audit IS 'Audit trail for feature flag changes';


-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_feature_flag_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_feature_flags_timestamp
    BEFORE UPDATE ON feature_flags
    FOR EACH ROW
    EXECUTE FUNCTION update_feature_flag_timestamp();


-- Function to log feature flag changes
CREATE OR REPLACE FUNCTION log_feature_flag_change()
RETURNS TRIGGER AS $$
DECLARE
    action_type VARCHAR(50);
    old_val JSONB;
    new_val JSONB;
BEGIN
    -- Determine action type
    IF TG_OP = 'INSERT' THEN
        action_type := 'created';
        old_val := NULL;
        new_val := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.enabled != NEW.enabled THEN
            action_type := CASE WHEN NEW.enabled THEN 'enabled' ELSE 'disabled' END;
        ELSIF OLD.rollout_percentage != NEW.rollout_percentage THEN
            action_type := 'rollout_changed';
        ELSE
            action_type := 'updated';
        END IF;
        old_val := to_jsonb(OLD);
        new_val := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        action_type := 'deleted';
        old_val := to_jsonb(OLD);
        new_val := NULL;
    END IF;

    -- Insert audit record
    INSERT INTO feature_flag_audit (flag_id, action, old_value, new_value, changed_by)
    VALUES (
        COALESCE(NEW.id, OLD.id),
        action_type,
        old_val,
        new_val,
        COALESCE(NEW.created_by, OLD.created_by)
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_feature_flag_changes
    AFTER INSERT OR UPDATE OR DELETE ON feature_flags
    FOR EACH ROW
    EXECUTE FUNCTION log_feature_flag_change();


-- Insert default feature flags for Vividly
INSERT INTO feature_flags (key, name, description, enabled, rollout_percentage) VALUES
    ('video_generation', 'Video Generation', 'Enable AI-powered personalized video generation', true, 100),
    ('advanced_analytics', 'Advanced Analytics', 'Show advanced learning analytics dashboard', true, 0),
    ('social_features', 'Social Features', 'Enable student collaboration and discussion features', false, 0),
    ('gamification', 'Gamification', 'Enable badges, points, and leaderboards', false, 0),
    ('offline_mode', 'Offline Mode', 'Enable offline video viewing', false, 0),
    ('ai_tutoring', 'AI Tutoring', 'Enable AI-powered tutoring chat', false, 0),
    ('parent_portal', 'Parent Portal', 'Enable parent access to student progress', false, 0),
    ('advanced_reporting', 'Advanced Reporting', 'Enable detailed teacher reporting tools', true, 50)
ON CONFLICT (key, organization_id) DO NOTHING;

COMMENT ON TABLE feature_flags IS 'Feature flags for gradual rollout of new Vividly features';


-- Rollback script (save separately as rollback_feature_flags.sql)
-- DROP TRIGGER IF EXISTS log_feature_flag_changes ON feature_flags;
-- DROP TRIGGER IF EXISTS update_feature_flags_timestamp ON feature_flags;
-- DROP FUNCTION IF EXISTS log_feature_flag_change();
-- DROP FUNCTION IF EXISTS update_feature_flag_timestamp();
-- DROP TABLE IF EXISTS feature_flag_audit CASCADE;
-- DROP TABLE IF EXISTS feature_flag_overrides CASCADE;
-- DROP TABLE IF EXISTS feature_flags CASCADE;
