#!/bin/bash
# ===================================
# PHASE 1A: DUAL MODALITY MIGRATION
# Safe Migration Execution Script
# ===================================
# Date: 2025-11-03
# Purpose: Safely apply Phase 1A dual modality migration to Cloud SQL
# Safety: Pre-flight checks, backups, rollback capability
# ===================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-vividly-dev-rich}"
INSTANCE_NAME="${DB_INSTANCE:-vividly-dev}"
DATABASE_NAME="${DB_NAME:-vividly}"
MIGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function: Print colored message
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function: Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check gcloud installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not installed"
        exit 1
    fi

    # Check psql installed
    if ! command -v psql &> /dev/null; then
        log_error "psql not installed"
        exit 1
    fi

    # Check migration files exist
    if [ ! -f "$MIGRATION_DIR/add_dual_modality_phase1.sql" ]; then
        log_error "Migration file not found: add_dual_modality_phase1.sql"
        exit 1
    fi

    if [ ! -f "$MIGRATION_DIR/rollback_add_dual_modality_phase1.sql" ]; then
        log_error "Rollback file not found: rollback_add_dual_modality_phase1.sql"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Function: Verify database connection
verify_connection() {
    log_info "Verifying database connection..."

    if ! gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" &> /dev/null; then
        log_error "Cloud SQL instance not found: $INSTANCE_NAME"
        exit 1
    fi

    log_success "Database connection verified"
}

# Function: Check if migration already applied
check_migration_status() {
    log_info "Checking if migration already applied..."

    # Create temp file for SQL query
    local check_query=$(cat <<'EOF'
SELECT
    EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'content_requests'
        AND column_name = 'requested_modalities'
    ) as migration_applied;
EOF
)

    local result=$(gcloud sql connect "$INSTANCE_NAME" \
        --database="$DATABASE_NAME" \
        --project="$PROJECT_ID" \
        --quiet \
        <<< "$check_query" 2>/dev/null | grep -E "t|f" | head -1)

    if [ "$result" = "t" ]; then
        log_warning "Migration appears to already be applied!"
        log_warning "Column 'requested_modalities' exists in content_requests table"
        read -p "Continue anyway? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            log_info "Migration cancelled by user"
            exit 0
        fi
    else
        log_success "Migration not yet applied"
    fi
}

# Function: Create database backup
create_backup() {
    log_info "Creating database backup..."

    local backup_name="phase1a-pre-migration-$(date +%Y%m%d-%H%M%S)"

    log_info "Backup name: $backup_name"
    log_info "This will take 2-5 minutes..."

    if gcloud sql backups create \
        --instance="$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --description="Pre-Phase 1A migration backup" 2>&1 | tee /tmp/backup.log; then
        log_success "Backup created successfully"
    else
        log_error "Backup failed"
        cat /tmp/backup.log
        exit 1
    fi
}

# Function: Display migration impact
show_migration_impact() {
    log_info "====================================="
    log_info "MIGRATION IMPACT SUMMARY"
    log_info "====================================="
    echo ""
    echo "Database: $DATABASE_NAME"
    echo "Instance: $INSTANCE_NAME"
    echo "Project: $PROJECT_ID"
    echo ""
    echo "Changes:"
    echo "  - Add 4 columns to content_requests"
    echo "  - Add 10 columns to content_metadata"
    echo "  - Add 3 columns to users"
    echo "  - Add 8 columns to request_metrics"
    echo "  - Create 5 indexes (GIN + B-tree)"
    echo "  - Add 4 pipeline stages"
    echo "  - Create 2 analytics views"
    echo "  - Add 1 trigger for output_formats"
    echo ""
    echo "Estimated duration: 30-60 seconds"
    echo "Downtime: None (online schema change)"
    echo ""
    log_info "====================================="
}

# Function: Apply migration
apply_migration() {
    log_info "Applying Phase 1A migration..."

    if gcloud sql connect "$INSTANCE_NAME" \
        --database="$DATABASE_NAME" \
        --project="$PROJECT_ID" \
        --quiet \
        < "$MIGRATION_DIR/add_dual_modality_phase1.sql"; then
        log_success "Migration applied successfully!"
    else
        log_error "Migration failed!"
        log_error "Database may be in inconsistent state"
        log_error "Run rollback script: ./rollback_phase1a_migration.sh"
        exit 1
    fi
}

# Function: Verify migration success
verify_migration() {
    log_info "Verifying migration success..."

    local verify_query=$(cat <<'EOF'
-- Check content_requests columns
SELECT
    COUNT(*) as request_columns
FROM information_schema.columns
WHERE table_name = 'content_requests'
AND column_name IN ('requested_modalities', 'preferred_modality', 'modality_preferences', 'output_formats');

-- Check content_metadata columns
SELECT
    COUNT(*) as metadata_columns
FROM information_schema.columns
WHERE table_name = 'content_metadata'
AND column_name IN ('modality_type', 'text_content', 'text_language', 'audio_url', 'audio_language',
                     'audio_duration_seconds', 'captions_url', 'captions_format', 'image_urls', 'supported_formats');

-- Check users columns
SELECT
    COUNT(*) as user_columns
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('content_modality_preferences', 'accessibility_settings', 'language_preference');

-- Check indexes
SELECT
    COUNT(*) as indexes
FROM pg_indexes
WHERE indexname LIKE 'idx_%modality%';

-- Check views
SELECT
    COUNT(*) as views
FROM information_schema.views
WHERE table_name IN ('content_modality_usage_summary', 'user_modality_preferences_summary');

-- Check pipeline stages
SELECT
    COUNT(*) as stages
FROM pipeline_stage_definitions
WHERE stage_name IN ('text_generation', 'audio_synthesis', 'image_generation', 'format_conversion');
EOF
)

    gcloud sql connect "$INSTANCE_NAME" \
        --database="$DATABASE_NAME" \
        --project="$PROJECT_ID" \
        --quiet \
        <<< "$verify_query"

    log_success "Verification complete - check counts above"
    log_info "Expected: 4 request_columns, 10 metadata_columns, 3 user_columns, 5 indexes, 2 views, 4 stages"
}

# Function: Main execution
main() {
    echo ""
    log_info "====================================="
    log_info "PHASE 1A MIGRATION EXECUTION"
    log_info "Date: $(date)"
    log_info "====================================="
    echo ""

    # Step 1: Prerequisites
    check_prerequisites

    # Step 2: Verify connection
    verify_connection

    # Step 3: Check migration status
    check_migration_status

    # Step 4: Show impact
    show_migration_impact

    # Step 5: Confirm execution
    log_warning "This will modify the production database schema"
    read -p "Proceed with migration? (yes/NO): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Migration cancelled by user"
        exit 0
    fi

    # Step 6: Create backup
    log_warning "Creating backup first (required for safety)"
    create_backup

    # Step 7: Final confirmation
    log_warning "FINAL CONFIRMATION: Apply migration now?"
    read -p "Type 'APPLY' to proceed: " final_confirm
    if [ "$final_confirm" != "APPLY" ]; then
        log_info "Migration cancelled"
        exit 0
    fi

    # Step 8: Apply migration
    apply_migration

    # Step 9: Verify success
    verify_migration

    echo ""
    log_success "====================================="
    log_success "PHASE 1A MIGRATION COMPLETE"
    log_success "====================================="
    echo ""
    log_info "Next steps:"
    log_info "1. Verify application still works (run smoke tests)"
    log_info "2. Update business logic to use new modality fields"
    log_info "3. Deploy updated services"
    echo ""
    log_info "Rollback available: ./rollback_phase1a_migration.sh"
    echo ""
}

# Execute main function
main "$@"
