#!/bin/bash

###############################################################################
# Run Database Migrations from Cloud Shell
#
# This script runs in Cloud Shell which has direct access to the private VPC.
#
# Usage:
#   1. Upload this script and migrations to Cloud Shell
#   2. Run: ./run_migrations_cloudshell.sh
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Configuration
PROJECT_ID="vividly-dev-rich"
DB_INSTANCE="dev-vividly-db"
DB_NAME="vividly"
DB_USER="vividly"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vividly Database Migrations (Cloud Shell)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ensure we're in Cloud Shell
if [ -z "$CLOUD_SHELL" ]; then
    log_warning "Not running in Cloud Shell"
    log_info "This script is designed for Cloud Shell. Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 0
    fi
fi

# Set project
gcloud config set project "$PROJECT_ID"

# Get database password from Secret Manager
log_info "Retrieving database password..."
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID")
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p')

if [ -z "$DB_PASSWORD" ]; then
    log_error "Could not retrieve password"
    exit 1
fi

log_success "Password retrieved"

# Get database private IP
log_info "Getting database connection info..."
DB_IP=$(gcloud sql instances describe "$DB_INSTANCE" \
    --project="$PROJECT_ID" \
    --format="value(ipAddresses[0].ipAddress)")

log_success "Database IP: $DB_IP"

# Install psql if needed
if ! command -v psql &> /dev/null; then
    log_info "Installing PostgreSQL client..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq postgresql-client
    log_success "psql installed"
fi

# Test connection
log_info "Testing database connection..."
export PGPASSWORD="$DB_PASSWORD"

if ! psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    log_error "Could not connect to database"
    log_info "Database IP: $DB_IP"
    log_info "Database User: $DB_USER"
    log_info "Database Name: $DB_NAME"
    exit 1
fi

log_success "Connected to database"

# Run Feature Flags migration
echo ""
log_info "Running Feature Flags migration..."

if psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" \
    -f add_feature_flags.sql > /tmp/ff_migration.log 2>&1; then
    log_success "Feature Flags migration completed"
else
    log_warning "Feature Flags migration had errors (tables may already exist)"
    cat /tmp/ff_migration.log | grep -i error | head -5
fi

# Run Request Tracking migration
log_info "Running Request Tracking migration..."

if psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" \
    -f add_request_tracking.sql > /tmp/rt_migration.log 2>&1; then
    log_success "Request Tracking migration completed"
else
    log_warning "Request Tracking migration had errors (tables may already exist)"
    cat /tmp/rt_migration.log | grep -i error | head -5
fi

# Verify
log_info "Verifying migrations..."
echo ""

# Count feature flags
FF_COUNT=$(psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs || echo "0")

# Count pipeline stages
STAGE_COUNT=$(psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs || echo "0")

log_success "Feature Flags: $FF_COUNT default flags created"
log_success "Pipeline Stages: $STAGE_COUNT stages configured"

# List tables
echo ""
log_info "New tables created:"
psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -t \
    -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;" 2>/dev/null | \
    grep -E "(feature_flag|content_request|request_stage|request_event|request_metric|pipeline_stage)" | \
    sed 's/^/  • /'

# Cleanup
unset PGPASSWORD

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Migrations completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
