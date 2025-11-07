#!/bin/bash
# ===================================
# PHASE 1A: DUAL MODALITY ROLLBACK
# Safe Rollback Execution Script
# ===================================
# Date: 2025-11-03
# Purpose: Safely rollback Phase 1A dual modality migration
# Safety: Creates backups before deletion, verification checks
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

    # Check rollback file exists
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

# Function: Check if migration is applied
check_migration_applied() {
    log_info "Checking if migration is currently applied..."

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

    if [ "$result" = "f" ]; then
        log_warning "Migration does not appear to be applied!"
        log_warning "Column 'requested_modalities' does not exist in content_requests table"
        read -p "Continue with rollback anyway? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
    else
        log_success "Migration is applied - rollback can proceed"
    fi
}

# Function: Display rollback impact
show_rollback_impact() {
    log_warning "====================================="
    log_warning "ROLLBACK IMPACT SUMMARY"
    log_warning "====================================="
    echo ""
    echo "Database: $DATABASE_NAME"
    echo "Instance: $INSTANCE_NAME"
    echo "Project: $PROJECT_ID"
    echo ""
    echo "Changes to be REMOVED:"
    echo "  - Remove 4 columns from content_requests"
    echo "  - Remove 10 columns from content_metadata"
    echo "  - Remove 3 columns from users"
    echo "  - Remove 8 columns from request_metrics"
    echo "  - Drop 5 indexes"
    echo "  - Remove 4 pipeline stages"
    echo "  - Drop 2 analytics views"
    echo "  - Drop 1 trigger"
    echo ""
    echo "BACKUP TABLES CREATED:"
    echo "  - content_requests_modality_backup"
    echo "  - content_metadata_modality_backup"
    echo "  - users_modality_backup"
    echo ""
    echo "Estimated duration: 30-60 seconds"
    echo "Downtime: None (online schema change)"
    echo ""
    log_warning "====================================="
}

# Function: Apply rollback
apply_rollback() {
    log_warning "Applying Phase 1A rollback..."

    if gcloud sql connect "$INSTANCE_NAME" \
        --database="$DATABASE_NAME" \
        --project="$PROJECT_ID" \
        --quiet \
        < "$MIGRATION_DIR/rollback_add_dual_modality_phase1.sql"; then
        log_success "Rollback applied successfully!"
    else
        log_error "Rollback failed!"
        log_error "Database may be in inconsistent state"
        log_error "Contact database administrator immediately"
        exit 1
    fi
}

# Function: Verify rollback success
verify_rollback() {
    log_info "Verifying rollback success..."

    local verify_query=$(cat <<'EOF'
-- Check content_requests columns removed
SELECT
    COUNT(*) as remaining_request_columns
FROM information_schema.columns
WHERE table_name = 'content_requests'
AND column_name IN ('requested_modalities', 'preferred_modality', 'modality_preferences', 'output_formats');

-- Check content_metadata columns removed
SELECT
    COUNT(*) as remaining_metadata_columns
FROM information_schema.columns
WHERE table_name = 'content_metadata'
AND column_name IN ('modality_type', 'text_content', 'text_language', 'audio_url', 'audio_language',
                     'audio_duration_seconds', 'captions_url', 'captions_format', 'image_urls', 'supported_formats');

-- Check users columns removed
SELECT
    COUNT(*) as remaining_user_columns
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('content_modality_preferences', 'accessibility_settings', 'language_preference');

-- Check backup tables exist
SELECT
    COUNT(*) as backup_tables
FROM information_schema.tables
WHERE table_name LIKE '%_modality_backup';
EOF
)

    gcloud sql connect "$INSTANCE_NAME" \
        --database="$DATABASE_NAME" \
        --project="$PROJECT_ID" \
        --quiet \
        <<< "$verify_query"

    log_success "Verification complete - check counts above"
    log_info "Expected: 0 remaining columns, 3 backup_tables"
}

# Function: Main execution
main() {
    echo ""
    log_warning "====================================="
    log_warning "PHASE 1A ROLLBACK EXECUTION"
    log_warning "Date: $(date)"
    log_warning "====================================="
    echo ""

    # Step 1: Prerequisites
    check_prerequisites

    # Step 2: Verify connection
    verify_connection

    # Step 3: Check migration status
    check_migration_applied

    # Step 4: Show impact
    show_rollback_impact

    # Step 5: Confirm execution
    log_error "⚠️  WARNING: This will REMOVE dual modality columns!"
    log_error "⚠️  Data will be backed up to *_modality_backup tables"
    log_error "⚠️  This operation cannot be easily undone"
    echo ""
    read -p "Proceed with rollback? (type 'ROLLBACK' to confirm): " confirm
    if [ "$confirm" != "ROLLBACK" ]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi

    # Step 6: Apply rollback
    apply_rollback

    # Step 7: Verify success
    verify_rollback

    echo ""
    log_success "====================================="
    log_success "PHASE 1A ROLLBACK COMPLETE"
    log_success "====================================="
    echo ""
    log_info "Backup tables created (do NOT delete):"
    log_info "  - content_requests_modality_backup"
    log_info "  - content_metadata_modality_backup"
    log_info "  - users_modality_backup"
    echo ""
    log_info "To restore data later, you can:"
    log_info "1. Re-run forward migration: ./run_phase1a_migration.sh"
    log_info "2. Manually copy data from backup tables"
    echo ""
}

# Execute main function
main "$@"
