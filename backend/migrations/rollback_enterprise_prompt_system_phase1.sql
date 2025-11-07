-- Rollback Enterprise Prompt Management System - Phase 1
-- Created: 2025-11-06
-- Purpose: Clean rollback of all Phase 1 database changes

-- ============================================================================
-- Drop Views
-- ============================================================================

DROP VIEW IF EXISTS v_active_ab_tests;
DROP VIEW IF EXISTS v_guardrail_violations_summary;
DROP VIEW IF EXISTS v_recent_execution_errors;
DROP VIEW IF EXISTS v_template_performance;

-- ============================================================================
-- Drop Triggers
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_enforce_single_active_template ON prompt_templates;
DROP TRIGGER IF EXISTS trigger_update_ab_test_statistics ON prompt_executions;
DROP TRIGGER IF EXISTS trigger_update_template_statistics ON prompt_executions;

-- ============================================================================
-- Drop Functions
-- ============================================================================

DROP FUNCTION IF EXISTS enforce_single_active_template();
DROP FUNCTION IF EXISTS update_ab_test_statistics();
DROP FUNCTION IF EXISTS update_template_statistics();

-- ============================================================================
-- Drop Tables (in reverse dependency order)
-- ============================================================================

DROP TABLE IF EXISTS ab_test_experiments CASCADE;
DROP TABLE IF EXISTS prompt_guardrails CASCADE;
DROP TABLE IF EXISTS prompt_executions CASCADE;
DROP TABLE IF EXISTS prompt_templates CASCADE;

-- ============================================================================
-- Remove Migration Record
-- ============================================================================

DELETE FROM schema_migrations WHERE version = 'enterprise_prompt_system_phase1';

-- Log completion
DO $$
BEGIN
    RAISE NOTICE '✅ Enterprise Prompt System Phase 1 rollback completed successfully';
    RAISE NOTICE '   - All tables dropped';
    RAISE NOTICE '   - All views dropped';
    RAISE NOTICE '   - All triggers dropped';
    RAISE NOTICE '   - All functions dropped';
    RAISE NOTICE '   - Migration record removed';
END $$;
