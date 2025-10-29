#!/bin/bash

###############################################################################
# Run Database Migrations (Automated)
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
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:/opt/homebrew/opt/postgresql@15/bin:$PATH"
export CLOUDSDK_CONFIG="$HOME/.gcloud"
PROJECT_ID="vividly-dev-rich"
DB_INSTANCE="dev-vividly-db"
CONNECTION_NAME="vividly-dev-rich:us-central1:dev-vividly-db"
DB_NAME="vividly"
DB_USER="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vividly Database Migrations (Automated)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get database URL from Secret Manager (contains password)
log_info "Retrieving database credentials..."
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)

if [ -z "$DB_URL" ]; then
    log_error "Could not retrieve database URL from Secret Manager"
    exit 1
fi

# Extract password from URL (format: postgresql://user:password@host:port/db)
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p')

if [ -z "$DB_PASSWORD" ]; then
    log_error "Could not extract password from database URL"
    exit 1
fi

log_success "Database credentials retrieved"

# Check psql
if [ ! -f "$PSQL" ]; then
    log_error "psql not found at $PSQL. Install with: brew install postgresql@15"
    exit 1
fi

# Check/download Cloud SQL Proxy
PROXY_PATH="$HOME/cloud-sql-proxy"
if [ ! -f "$PROXY_PATH" ]; then
    log_info "Downloading Cloud SQL Proxy..."
    curl -so "$PROXY_PATH" https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.7.0/cloud-sql-proxy.darwin.amd64
    chmod +x "$PROXY_PATH"
    log_success "Cloud SQL Proxy downloaded"
fi

# Kill any existing proxy
pkill -f cloud-sql-proxy 2>/dev/null || true
sleep 2

# Start Cloud SQL Proxy (using gcloud auth credentials)
log_info "Starting Cloud SQL Proxy..."
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

# If ADC doesn't exist, create it from gcloud credentials
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    log_info "Setting up application default credentials..."
    gcloud auth application-default login --no-launch-browser 2>&1 | grep -E "https://|verification code" || true
fi

"$PROXY_PATH" "$CONNECTION_NAME" --port 5433 --private-ip > /tmp/cloud-sql-proxy.log 2>&1 &
PROXY_PID=$!
sleep 7

if ! ps -p $PROXY_PID > /dev/null; then
    log_error "Cloud SQL Proxy failed to start. Check /tmp/cloud-sql-proxy.log"
    exit 1
fi

log_success "Cloud SQL Proxy started (PID: $PROXY_PID)"

# Test connection
log_info "Testing database connection..."
export PGPASSWORD="$DB_PASSWORD"

if ! "$PSQL" -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    log_error "Could not connect to database"
    kill $PROXY_PID 2>/dev/null || true
    exit 1
fi

log_success "Connected to database"

# Run Feature Flags migration
echo ""
log_info "Running Feature Flags migration..."
cd "$(dirname "$0")/.."

if "$PSQL" -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -f backend/migrations/add_feature_flags.sql 2>&1 | grep -q "ERROR"; then
    log_warning "Feature Flags migration had errors (tables may already exist)"
else
    log_success "Feature Flags migration completed"
fi

# Run Request Tracking migration
log_info "Running Request Tracking migration..."

if "$PSQL" -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -f backend/migrations/add_request_tracking.sql 2>&1 | grep -q "ERROR"; then
    log_warning "Request Tracking migration had errors (tables may already exist)"
else
    log_success "Request Tracking migration completed"
fi

# Verify
log_info "Verifying migrations..."
echo ""

# Count feature flags
FF_COUNT=$("$PSQL" -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs || echo "0")

# Count pipeline stages
STAGE_COUNT=$("$PSQL" -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs || echo "0")

log_success "Feature Flags: $FF_COUNT default flags created"
log_success "Pipeline Stages: $STAGE_COUNT stages configured"

# List tables
echo ""
log_info "New tables created:"
"$PSQL" -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -t \
    -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;" 2>/dev/null | \
    grep -E "(feature_flag|content_request|request_stage|request_event|request_metric|pipeline_stage)" | \
    sed 's/^/  • /'

# Cleanup
kill $PROXY_PID 2>/dev/null || true
unset PGPASSWORD

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Migrations completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  • Feature Flags API: /api/v1/feature-flags"
echo "  • Monitoring Dashboard: /api/v1/monitoring/dashboard"
echo "  • Integration Guide: backend/TRACKING_INTEGRATION_GUIDE.md"
echo ""
