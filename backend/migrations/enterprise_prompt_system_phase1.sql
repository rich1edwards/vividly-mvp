-- Enterprise Prompt Management System - Phase 1 Migration
-- Following Andrew Ng's principle: "Build it right, think about the future"
-- Created: 2025-11-06
-- Description: Database-driven prompt templates with versioning, guardrails, and A/B testing support

-- ============================================================================
-- Table 1: prompt_templates
-- Purpose: Store prompt templates with versioning and A/B test support
-- ============================================================================

CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template identity
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),  -- e.g., 'nlu', 'clarification', 'script_generation'

    -- Template content
    template_text TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,  -- Array of required variable names

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    parent_version_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT false,

    -- A/B Testing
    ab_test_group VARCHAR(50),  -- e.g., 'control', 'variant_a', 'variant_b'
    traffic_percentage INTEGER DEFAULT 0 CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100),
    ab_test_start_date TIMESTAMP,
    ab_test_end_date TIMESTAMP,

    -- Performance metrics (updated by execution logs)
    total_executions INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    avg_token_count INTEGER,
    avg_cost_usd NUMERIC(10, 6),

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),
    deactivated_at TIMESTAMP,
    deactivated_by VARCHAR(255),

    -- Ensure only one active version per name (unless A/B testing)
    CONSTRAINT unique_active_template UNIQUE (name, is_active, ab_test_group)
);

-- Index for fast active template lookup
CREATE INDEX idx_prompt_templates_active ON prompt_templates(name, is_active)
WHERE is_active = true;

-- Index for A/B test queries
CREATE INDEX idx_prompt_templates_ab_test ON prompt_templates(name, ab_test_group, traffic_percentage)
WHERE ab_test_group IS NOT NULL;

-- Index for versioning queries
CREATE INDEX idx_prompt_templates_version ON prompt_templates(name, version);

-- Index for performance analytics
CREATE INDEX idx_prompt_templates_performance ON prompt_templates(category, avg_response_time_ms, success_count);

-- ============================================================================
-- Table 2: prompt_executions
-- Purpose: Audit log for every prompt execution with metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS prompt_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template reference
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    template_name VARCHAR(255) NOT NULL,
    template_version INTEGER NOT NULL,
    ab_test_group VARCHAR(50),

    -- Execution context
    user_id VARCHAR(255),
    request_id UUID,  -- Links to content_requests table
    session_id VARCHAR(255),

    -- Input/Output
    input_variables JSONB NOT NULL,
    rendered_prompt TEXT NOT NULL,
    model_response TEXT,

    -- Performance metrics
    execution_time_ms INTEGER,
    token_count INTEGER,
    cost_usd NUMERIC(10, 6),

    -- Status
    status VARCHAR(50) NOT NULL,  -- 'success', 'failure', 'partial'
    error_message TEXT,
    error_type VARCHAR(100),

    -- Guardrails
    guardrail_violations JSONB DEFAULT '[]'::jsonb,
    guardrail_action VARCHAR(50),  -- 'allow', 'block', 'warn'

    -- Metadata
    executed_at TIMESTAMP DEFAULT NOW(),
    environment VARCHAR(50)  -- 'dev', 'staging', 'production'
);

-- Index for template performance analytics
CREATE INDEX idx_prompt_executions_template ON prompt_executions(template_id, status, executed_at);

-- Index for user activity tracking
CREATE INDEX idx_prompt_executions_user ON prompt_executions(user_id, executed_at);

-- Index for request correlation
CREATE INDEX idx_prompt_executions_request ON prompt_executions(request_id);

-- Index for error analysis
CREATE INDEX idx_prompt_executions_errors ON prompt_executions(template_id, status, error_type)
WHERE status = 'failure';

-- Index for guardrail analysis
CREATE INDEX idx_prompt_executions_guardrails ON prompt_executions(template_id, guardrail_action)
WHERE jsonb_array_length(guardrail_violations) > 0;

-- ============================================================================
-- Table 3: prompt_guardrails
-- Purpose: Configure safety rules for prompts
-- ============================================================================

CREATE TABLE IF NOT EXISTS prompt_guardrails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Guardrail identity
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    guardrail_type VARCHAR(100) NOT NULL,  -- 'pii_detection', 'toxic_content', 'prompt_injection', 'content_policy'

    -- Configuration
    is_active BOOLEAN DEFAULT true,
    severity VARCHAR(50) NOT NULL,  -- 'critical', 'high', 'medium', 'low'
    action VARCHAR(50) NOT NULL,  -- 'block', 'warn', 'log'

    -- Rule definition (flexible JSON structure)
    config JSONB NOT NULL,  -- e.g., {"patterns": ["\\b\\d{3}-\\d{2}-\\d{4}\\b"], "entity_types": ["SSN"]}

    -- Applicability
    applies_to_templates VARCHAR(255)[] DEFAULT ARRAY[]::VARCHAR[],  -- Empty array = applies to all
    applies_to_categories VARCHAR(100)[] DEFAULT ARRAY[]::VARCHAR[],

    -- Performance
    total_checks INTEGER DEFAULT 0,
    violation_count INTEGER DEFAULT 0,
    false_positive_count INTEGER DEFAULT 0,

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for active guardrails lookup
CREATE INDEX idx_prompt_guardrails_active ON prompt_guardrails(is_active)
WHERE is_active = true;

-- Index for template-specific guardrails
CREATE INDEX idx_prompt_guardrails_templates ON prompt_guardrails USING GIN(applies_to_templates);

-- Index for category-specific guardrails
CREATE INDEX idx_prompt_guardrails_categories ON prompt_guardrails USING GIN(applies_to_categories);

-- Index for performance analysis
CREATE INDEX idx_prompt_guardrails_performance ON prompt_guardrails(guardrail_type, violation_count);

-- ============================================================================
-- Table 4: ab_test_experiments
-- Purpose: Manage A/B test experiments with statistical tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS ab_test_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Experiment identity
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    template_name VARCHAR(255) NOT NULL,  -- Which template is being tested

    -- Experiment status
    status VARCHAR(50) NOT NULL,  -- 'draft', 'active', 'paused', 'completed', 'cancelled'

    -- Experiment configuration
    control_template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE RESTRICT,
    variant_template_ids UUID[] NOT NULL,  -- Array of variant template IDs

    -- Traffic allocation
    traffic_allocation JSONB NOT NULL,  -- e.g., {"control": 50, "variant_a": 25, "variant_b": 25}

    -- Success metrics
    primary_metric VARCHAR(100) NOT NULL,  -- e.g., 'success_rate', 'avg_response_time_ms', 'user_satisfaction'
    target_improvement_percentage FLOAT,
    minimum_sample_size INTEGER DEFAULT 1000,

    -- Statistical tracking
    total_executions INTEGER DEFAULT 0,
    control_executions INTEGER DEFAULT 0,
    variant_executions JSONB DEFAULT '{}'::jsonb,  -- {"variant_a": 500, "variant_b": 500}

    control_metric_value FLOAT,
    variant_metric_values JSONB DEFAULT '{}'::jsonb,  -- {"variant_a": 0.85, "variant_b": 0.90}

    statistical_significance FLOAT,  -- p-value
    confidence_level FLOAT DEFAULT 0.95,

    -- Winner declaration
    winner_variant VARCHAR(50),
    winner_declared_at TIMESTAMP,
    winner_declared_by VARCHAR(255),

    -- Timeline
    scheduled_start_date TIMESTAMP,
    actual_start_date TIMESTAMP,
    scheduled_end_date TIMESTAMP,
    actual_end_date TIMESTAMP,

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for active experiments lookup
CREATE INDEX idx_ab_test_experiments_active ON ab_test_experiments(status, template_name)
WHERE status = 'active';

-- Index for experiment timeline
CREATE INDEX idx_ab_test_experiments_timeline ON ab_test_experiments(actual_start_date, actual_end_date);

-- Index for statistical analysis
CREATE INDEX idx_ab_test_experiments_stats ON ab_test_experiments(template_name, statistical_significance, winner_variant);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function: Update template statistics after each execution
CREATE OR REPLACE FUNCTION update_template_statistics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE prompt_templates
    SET
        total_executions = total_executions + 1,
        success_count = CASE WHEN NEW.status = 'success' THEN success_count + 1 ELSE success_count END,
        failure_count = CASE WHEN NEW.status = 'failure' THEN failure_count + 1 ELSE failure_count END,
        avg_response_time_ms = (
            COALESCE(avg_response_time_ms * total_executions, 0) + COALESCE(NEW.execution_time_ms, 0)
        ) / (total_executions + 1),
        avg_token_count = (
            COALESCE(avg_token_count * total_executions, 0) + COALESCE(NEW.token_count, 0)
        ) / (total_executions + 1),
        avg_cost_usd = (
            COALESCE(avg_cost_usd * total_executions, 0) + COALESCE(NEW.cost_usd, 0)
        ) / (total_executions + 1)
    WHERE id = NEW.template_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update statistics after prompt execution
CREATE TRIGGER trigger_update_template_statistics
AFTER INSERT ON prompt_executions
FOR EACH ROW
EXECUTE FUNCTION update_template_statistics();

-- Function: Update A/B test statistics after each execution
CREATE OR REPLACE FUNCTION update_ab_test_statistics()
RETURNS TRIGGER AS $$
DECLARE
    experiment_record RECORD;
BEGIN
    -- Find active experiment for this template
    SELECT * INTO experiment_record
    FROM ab_test_experiments
    WHERE template_name = NEW.template_name
      AND status = 'active'
    LIMIT 1;

    IF FOUND THEN
        -- Update total executions
        UPDATE ab_test_experiments
        SET total_executions = total_executions + 1
        WHERE id = experiment_record.id;

        -- Update control or variant counts
        IF NEW.ab_test_group = 'control' THEN
            UPDATE ab_test_experiments
            SET control_executions = control_executions + 1
            WHERE id = experiment_record.id;
        ELSIF NEW.ab_test_group IS NOT NULL THEN
            UPDATE ab_test_experiments
            SET variant_executions = jsonb_set(
                variant_executions,
                ARRAY[NEW.ab_test_group],
                to_jsonb(COALESCE((variant_executions->NEW.ab_test_group)::int, 0) + 1)
            )
            WHERE id = experiment_record.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update A/B test statistics after prompt execution
CREATE TRIGGER trigger_update_ab_test_statistics
AFTER INSERT ON prompt_executions
FOR EACH ROW
EXECUTE FUNCTION update_ab_test_statistics();

-- Function: Enforce single active template per name (unless A/B testing)
CREATE OR REPLACE FUNCTION enforce_single_active_template()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = true AND NEW.ab_test_group IS NULL THEN
        -- Deactivate all other templates with the same name
        UPDATE prompt_templates
        SET is_active = false, deactivated_at = NOW()
        WHERE name = NEW.name
          AND id != NEW.id
          AND ab_test_group IS NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Enforce single active template
CREATE TRIGGER trigger_enforce_single_active_template
BEFORE INSERT OR UPDATE ON prompt_templates
FOR EACH ROW
WHEN (NEW.is_active = true)
EXECUTE FUNCTION enforce_single_active_template();

-- ============================================================================
-- Seed Data: Core Prompts from Existing Codebase
-- ============================================================================

-- NLU Prompt Template
INSERT INTO prompt_templates (
    name,
    description,
    category,
    template_text,
    variables,
    version,
    is_active,
    created_by
) VALUES (
    'nlu_topic_extraction',
    'Extract educational topics from student queries using structured JSON',
    'nlu',
    'You are an educational content assistant. Analyze the student''s query and extract relevant topics.

Student Query: {{ student_query }}

{% if interests %}
Student Interests: {{ interests|join(", ") }}
{% endif %}

Return a JSON object with this structure:
{
  "topics": ["topic1", "topic2"],
  "subject_area": "subject",
  "grade_level": "grade",
  "learning_objectives": ["objective1"]
}',
    '["student_query", "interests"]'::jsonb,
    1,
    true,
    'system'
);

-- Clarification Prompt Template
INSERT INTO prompt_templates (
    name,
    description,
    category,
    template_text,
    variables,
    version,
    is_active,
    created_by
) VALUES (
    'clarification_question_generation',
    'Generate clarifying questions when student query is vague',
    'clarification',
    'You are an educational assistant helping students refine vague queries.

Student Query: {{ student_query }}

{% if interests %}
Student Interests: {{ interests|join(", ") }}
{% endif %}

The query is too vague. Generate 3 clarifying questions to help narrow the focus.

Return JSON:
{
  "questions": [
    "Question 1?",
    "Question 2?",
    "Question 3?"
  ],
  "reasoning": "Why these questions help"
}',
    '["student_query", "interests"]'::jsonb,
    1,
    true,
    'system'
);

-- Script Generation Prompt Template
INSERT INTO prompt_templates (
    name,
    description,
    category,
    template_text,
    variables,
    version,
    is_active,
    created_by
) VALUES (
    'educational_script_generation',
    'Generate engaging educational script based on topics and RAG context',
    'script_generation',
    'You are an expert educational content creator. Generate an engaging, accurate educational script.

Topics: {{ topics|join(", ") }}
{% if rag_context %}
Reference Material: {{ rag_context }}
{% endif %}

Student Grade Level: {{ grade_level }}
Content Length: {{ duration_seconds }} seconds

{% if interests %}
Personalization: Relate to student interests: {{ interests|join(", ") }}
{% endif %}

Requirements:
- Accurate, curriculum-aligned content
- Engaging narrative style
- Age-appropriate language
- Include real-world examples
- Clear learning objectives

Generate the educational script.',
    '["topics", "rag_context", "grade_level", "duration_seconds", "interests"]'::jsonb,
    1,
    true,
    'system'
);

-- ============================================================================
-- Seed Data: Core Guardrails
-- ============================================================================

-- PII Detection Guardrail
INSERT INTO prompt_guardrails (
    name,
    description,
    guardrail_type,
    is_active,
    severity,
    action,
    config,
    created_by
) VALUES (
    'pii_detection_basic',
    'Detect common PII patterns (SSN, credit cards, phone numbers)',
    'pii_detection',
    true,
    'critical',
    'block',
    '{
        "patterns": [
            "\\b\\d{3}-\\d{2}-\\d{4}\\b",
            "\\b\\d{3}\\s\\d{2}\\s\\d{4}\\b",
            "\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b",
            "\\b\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b"
        ],
        "entity_types": ["SSN", "CREDIT_CARD", "PHONE_NUMBER"],
        "redaction_mode": "block_request"
    }'::jsonb,
    'system'
);

-- Toxic Content Guardrail
INSERT INTO prompt_guardrails (
    name,
    description,
    guardrail_type,
    is_active,
    severity,
    action,
    config,
    created_by
) VALUES (
    'toxic_content_filter',
    'Detect and block toxic, harmful, or inappropriate content',
    'toxic_content',
    true,
    'high',
    'block',
    '{
        "toxicity_threshold": 0.7,
        "categories": ["profanity", "hate_speech", "violence", "sexual_content"],
        "allow_educational_context": true
    }'::jsonb,
    'system'
);

-- Prompt Injection Guardrail
INSERT INTO prompt_guardrails (
    name,
    description,
    guardrail_type,
    is_active,
    severity,
    action,
    config,
    created_by
) VALUES (
    'prompt_injection_detection',
    'Detect attempts to manipulate system prompts',
    'prompt_injection',
    true,
    'critical',
    'block',
    '{
        "patterns": [
            "ignore previous instructions",
            "disregard all",
            "system:",
            "new instructions:",
            "override",
            "jailbreak"
        ],
        "case_sensitive": false
    }'::jsonb,
    'system'
);

-- ============================================================================
-- Views for Analytics
-- ============================================================================

-- View: Template performance summary
CREATE OR REPLACE VIEW v_template_performance AS
SELECT
    pt.id,
    pt.name,
    pt.category,
    pt.version,
    pt.is_active,
    pt.ab_test_group,
    pt.total_executions,
    pt.success_count,
    pt.failure_count,
    CASE
        WHEN pt.total_executions > 0
        THEN ROUND((pt.success_count::numeric / pt.total_executions * 100), 2)
        ELSE 0
    END AS success_rate_percentage,
    pt.avg_response_time_ms,
    pt.avg_token_count,
    pt.avg_cost_usd,
    pt.created_at,
    pt.updated_at
FROM prompt_templates pt
ORDER BY pt.total_executions DESC;

-- View: Recent executions with errors
CREATE OR REPLACE VIEW v_recent_execution_errors AS
SELECT
    pe.id,
    pe.template_name,
    pe.template_version,
    pe.error_type,
    pe.error_message,
    pe.executed_at,
    pe.user_id,
    pe.request_id
FROM prompt_executions pe
WHERE pe.status = 'failure'
ORDER BY pe.executed_at DESC
LIMIT 100;

-- View: Guardrail violations summary
CREATE OR REPLACE VIEW v_guardrail_violations_summary AS
SELECT
    pe.template_name,
    pg.name AS guardrail_name,
    pg.guardrail_type,
    COUNT(*) AS violation_count,
    COUNT(DISTINCT pe.user_id) AS affected_users,
    MAX(pe.executed_at) AS last_violation
FROM prompt_executions pe
CROSS JOIN LATERAL jsonb_array_elements(pe.guardrail_violations) AS violation
JOIN prompt_guardrails pg ON pg.name = (violation->>'guardrail_name')::text
GROUP BY pe.template_name, pg.name, pg.guardrail_type
ORDER BY violation_count DESC;

-- View: Active A/B test experiments with metrics
CREATE OR REPLACE VIEW v_active_ab_tests AS
SELECT
    ae.id,
    ae.name,
    ae.template_name,
    ae.status,
    ae.total_executions,
    ae.control_executions,
    ae.variant_executions,
    ae.primary_metric,
    ae.control_metric_value,
    ae.variant_metric_values,
    ae.statistical_significance,
    ae.winner_variant,
    ae.actual_start_date,
    ae.scheduled_end_date,
    CASE
        WHEN ae.total_executions >= ae.minimum_sample_size
        THEN 'sufficient'
        ELSE 'collecting'
    END AS sample_status
FROM ab_test_experiments ae
WHERE ae.status = 'active'
ORDER BY ae.actual_start_date DESC;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- Grant permissions to application service account
-- (Assumes service account will be configured in application)

GRANT SELECT, INSERT, UPDATE ON prompt_templates TO PUBLIC;
GRANT SELECT, INSERT ON prompt_executions TO PUBLIC;
GRANT SELECT ON prompt_guardrails TO PUBLIC;
GRANT SELECT, UPDATE ON ab_test_experiments TO PUBLIC;

GRANT SELECT ON v_template_performance TO PUBLIC;
GRANT SELECT ON v_recent_execution_errors TO PUBLIC;
GRANT SELECT ON v_guardrail_violations_summary TO PUBLIC;
GRANT SELECT ON v_active_ab_tests TO PUBLIC;

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- Insert migration record
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    description TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description)
VALUES (
    'enterprise_prompt_system_phase1',
    'Enterprise Prompt Management System - Database-driven templates with versioning, guardrails, and A/B testing support'
);

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✅ Enterprise Prompt System Phase 1 migration completed successfully';
    RAISE NOTICE '   - 4 core tables created (prompt_templates, prompt_executions, prompt_guardrails, ab_test_experiments)';
    RAISE NOTICE '   - 3 seed prompts inserted (nlu, clarification, script_generation)';
    RAISE NOTICE '   - 3 seed guardrails inserted (pii, toxic_content, prompt_injection)';
    RAISE NOTICE '   - 4 analytics views created';
    RAISE NOTICE '   - 3 triggers configured for auto-updates';
    RAISE NOTICE '   - System ready for PromptManagementService integration';
END $$;
