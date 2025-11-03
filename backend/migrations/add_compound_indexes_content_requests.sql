-- Add Compound Indexes for Content Requests
-- Optimizes common query patterns for production performance
--
-- Context:
-- This migration adds compound (multi-column) indexes to the content_requests table
-- to optimize frequently executed queries in the async content generation system.
--
-- Query Patterns Optimized:
-- 1. Worker Idempotency: correlation_id + status (check for duplicate processing)
-- 2. Status Polling: student_id + status + created_at (list active requests for user)
-- 3. Admin Dashboard: status + created_at (list all requests by status and time)
-- 4. Performance Monitoring: organization_id + status + created_at (org-level metrics)
--
-- Run: psql -h HOST -U USER -d DATABASE -f add_compound_indexes_content_requests.sql
--
-- Author: Generated for production readiness Sprint 3
-- Date: 2025-11-01

-- ============================================================================
-- Idempotency Checks (Worker Performance)
-- ============================================================================

-- Used by: ContentWorker.process_message() idempotency check
-- Query Pattern: WHERE correlation_id = ? AND status NOT IN ('completed', 'failed')
-- Impact: Prevents duplicate processing of same request
-- Expected Usage: ~10-100 qps per worker instance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_correlation_status
ON content_requests(correlation_id, status);

COMMENT ON INDEX idx_content_requests_correlation_status IS
'Optimizes worker idempotency checks by correlation_id and status';

-- ============================================================================
-- Student Status Queries (Frontend Performance)
-- ============================================================================

-- Used by: Frontend polling, ContentStatusTracker component
-- Query Pattern: WHERE student_id = ? AND status IN ('pending', 'generating', ...) ORDER BY created_at DESC
-- Impact: Fast retrieval of active requests for student dashboard
-- Expected Usage: ~1-10 qps per active student
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_student_status_created
ON content_requests(student_id, status, created_at DESC);

COMMENT ON INDEX idx_content_requests_student_status_created IS
'Optimizes student dashboard queries filtering by status and sorted by creation time';

-- ============================================================================
-- Admin Dashboard Queries (Monitoring Performance)
-- ============================================================================

-- Used by: Admin dashboard, monitoring tools, RequestMonitoring component
-- Query Pattern: WHERE status = ? ORDER BY created_at DESC LIMIT 50
-- Impact: Fast retrieval of requests in specific states (pending, failed, etc.)
-- Expected Usage: ~0.1-1 qps from admin users
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_status_created
ON content_requests(status, created_at DESC);

COMMENT ON INDEX idx_content_requests_status_created IS
'Optimizes admin queries for requests by status ordered by creation time';

-- ============================================================================
-- Organization Metrics Queries (Analytics Performance)
-- ============================================================================

-- Used by: Organization-level analytics, billing, usage tracking
-- Query Pattern: WHERE organization_id = ? AND status = ? AND created_at BETWEEN ? AND ?
-- Impact: Fast aggregation of org-level request metrics
-- Expected Usage: ~0.01-0.1 qps for analytics queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_org_status_created
ON content_requests(organization_id, status, created_at DESC)
WHERE organization_id IS NOT NULL;

COMMENT ON INDEX idx_content_requests_org_status_created IS
'Optimizes organization-level analytics queries with partial index (only non-null org_id)';

-- ============================================================================
-- Performance-Critical Queries (Error Investigation)
-- ============================================================================

-- Used by: Error debugging, DLQ investigation, support tickets
-- Query Pattern: WHERE status = 'failed' AND error_stage = ? ORDER BY failed_at DESC
-- Impact: Fast retrieval of failed requests for debugging
-- Expected Usage: ~0.01-0.1 qps from ops team
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_requests_failed_debugging
ON content_requests(status, error_stage, failed_at DESC)
WHERE status = 'failed';

COMMENT ON INDEX idx_content_requests_failed_debugging IS
'Partial index for failed requests to optimize error debugging queries';

-- ============================================================================
-- Index Analysis and Verification
-- ============================================================================

-- Query to check index sizes and usage (run post-deployment for monitoring)
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
--     idx_scan AS times_used,
--     idx_tup_read AS tuples_read,
--     idx_tup_fetch AS tuples_fetched
-- FROM pg_stat_user_indexes
-- WHERE tablename = 'content_requests'
-- ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- Migration Notes
-- ============================================================================

-- CONCURRENTLY: All indexes created with CONCURRENTLY to avoid table locking
-- This allows index creation without blocking production writes
--
-- Partial Indexes: Used for filtered queries (organization_id, failed status)
-- to reduce index size and improve write performance
--
-- Descending Indexes: created_at DESC for efficient ORDER BY DESC queries
-- without requiring reverse scans
--
-- Future Considerations:
-- 1. Monitor index usage with pg_stat_user_indexes
-- 2. Drop unused single-column indexes if compound indexes provide full coverage
-- 3. Consider index-only scans by adding INCLUDE columns for hot queries
-- 4. Adjust maintenance_work_mem before running in production for faster builds
--
-- Rollback:
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_correlation_status;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_student_status_created;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_status_created;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_org_status_created;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_failed_debugging;
