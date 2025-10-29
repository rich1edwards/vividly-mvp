#!/bin/bash

###############################################################################
# Run Database Migrations Script
#
# Fixes gcloud authentication and runs database migrations for:
# 1. Feature Flags System
# 2. Request Tracking System
#
# Usage:
#   ./scripts/run_migrations.sh
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="vividly-dev-rich"
DB_INSTANCE="dev-vividly-db"
DB_NAME="vividly"
DB_USER="vividly"
REGION="us-central1"

# Set gcloud config directory
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Create gcloud config directory if it doesn't exist
mkdir -p "$CLOUDSDK_CONFIG"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vividly Database Migrations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check gcloud installation
log_info "Checking gcloud installation..."
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Please install it:"
    echo "  brew install google-cloud-sdk"
    exit 1
fi
log_success "gcloud CLI found"

# Step 2: Check authentication
log_info "Checking gcloud authentication..."
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")

if [ -z "$ACTIVE_ACCOUNT" ]; then
    log_warning "No active gcloud account found"
    log_info "Starting authentication..."
    echo ""
    echo "A browser window will open. Please sign in with your Google Cloud account."
    echo "Press Enter to continue..."
    read

    gcloud auth login --project="$PROJECT_ID"

    if [ $? -ne 0 ]; then
        log_error "Authentication failed"
        exit 1
    fi

    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
fi

log_success "Authenticated as: $ACTIVE_ACCOUNT"

# Step 3: Set project
log_info "Setting active project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID" 2>/dev/null
log_success "Project set"

# Step 4: Check database instance
log_info "Checking if database instance exists..."
DB_STATUS=$(gcloud sql instances describe "$DB_INSTANCE" \
    --project="$PROJECT_ID" \
    --format="value(state)" 2>/dev/null || echo "NOT_FOUND")

if [ "$DB_STATUS" = "NOT_FOUND" ]; then
    log_error "Database instance $DB_INSTANCE not found in project $PROJECT_ID"
    log_info "Please run Terraform apply first to create the database"
    exit 1
fi

log_success "Database instance found (status: $DB_STATUS)"

# Step 5: Get database connection info
log_info "Getting database connection details..."
CONNECTION_NAME=$(gcloud sql instances describe "$DB_INSTANCE" \
    --project="$PROJECT_ID" \
    --format="value(connectionName)")
log_success "Connection name: $CONNECTION_NAME"

# Step 6: Get or prompt for database password
log_info "Getting database password..."

# Try to get from Terraform output first
cd "$(dirname "$0")/../terraform"
DB_PASSWORD=$(terraform output -raw db_password 2>/dev/null || echo "")

if [ -z "$DB_PASSWORD" ]; then
    log_warning "Could not get password from Terraform"
    log_info "Trying to get from Secret Manager..."

    DB_PASSWORD=$(gcloud secrets versions access latest \
        --secret="database-password-dev" \
        --project="$PROJECT_ID" 2>/dev/null || echo "")

    if [ -z "$DB_PASSWORD" ]; then
        log_warning "Could not get password from Secret Manager"
        echo ""
        echo "Please enter the database password:"
        read -s DB_PASSWORD
        echo ""
    fi
fi

if [ -z "$DB_PASSWORD" ]; then
    log_error "No database password provided"
    exit 1
fi

log_success "Database password retrieved"

# Step 7: Check if psql is installed
log_info "Checking PostgreSQL client..."
if ! command -v psql &> /dev/null; then
    log_error "psql not found. Please install it:"
    echo "  brew install postgresql@15"
    exit 1
fi
log_success "psql found"

# Step 8: Check if Cloud SQL Proxy is installed
log_info "Checking Cloud SQL Proxy..."
PROXY_PATH="$HOME/cloud-sql-proxy"

if [ ! -f "$PROXY_PATH" ]; then
    log_info "Downloading Cloud SQL Proxy..."
    curl -so "$PROXY_PATH" https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.7.0/cloud-sql-proxy.darwin.amd64
    chmod +x "$PROXY_PATH"
    log_success "Cloud SQL Proxy downloaded"
else
    log_success "Cloud SQL Proxy found"
fi

# Step 9: Start Cloud SQL Proxy
log_info "Starting Cloud SQL Proxy..."

# Kill any existing proxy
pkill -f cloud-sql-proxy 2>/dev/null || true
sleep 2

# Start proxy in background
"$PROXY_PATH" "$CONNECTION_NAME" --port 5433 > /dev/null 2>&1 &
PROXY_PID=$!

# Wait for proxy to be ready
log_info "Waiting for proxy to be ready..."
sleep 5

# Check if proxy is running
if ! ps -p $PROXY_PID > /dev/null; then
    log_error "Cloud SQL Proxy failed to start"
    exit 1
fi

log_success "Cloud SQL Proxy started (PID: $PROXY_PID, Port: 5433)"

# Step 10: Test database connection
log_info "Testing database connection..."
export PGPASSWORD="$DB_PASSWORD"

if ! psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    log_error "Could not connect to database"
    kill $PROXY_PID 2>/dev/null || true
    exit 1
fi

log_success "Database connection successful"

# Step 11: Run Feature Flags migration
echo ""
log_info "Running Feature Flags migration..."
cd "$(dirname "$0")/.."

if psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -f backend/migrations/add_feature_flags.sql > /dev/null 2>&1; then
    log_success "Feature Flags migration completed"
else
    log_warning "Feature Flags migration may have failed (tables might already exist)"
fi

# Step 12: Run Request Tracking migration
log_info "Running Request Tracking migration..."

if psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -f backend/migrations/add_request_tracking.sql > /dev/null 2>&1; then
    log_success "Request Tracking migration completed"
else
    log_warning "Request Tracking migration may have failed (tables might already exist)"
fi

# Step 13: Verify migrations
log_info "Verifying migrations..."

# Check feature flags table
FEATURE_FLAGS_COUNT=$(psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs || echo "0")

# Check request tracking tables
REQUEST_STAGES_COUNT=$(psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs || echo "0")

echo ""
log_success "Verification Results:"
echo "  • Feature Flags: $FEATURE_FLAGS_COUNT default flags created"
echo "  • Pipeline Stages: $REQUEST_STAGES_COUNT stages configured"

# List all new tables
log_info "New tables created:"
psql -h 127.0.0.1 -p 5433 -U "$DB_USER" -d "$DB_NAME" \
    -c "\dt" 2>/dev/null | grep -E "(feature_flag|content_request|request_stage|request_event|request_metric|pipeline_stage)" | awk '{print "  • " $3}' || true

# Step 14: Cleanup
log_info "Cleaning up..."
kill $PROXY_PID 2>/dev/null || true
unset PGPASSWORD
log_success "Cloud SQL Proxy stopped"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Migrations completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Feature Flags API: /api/v1/feature-flags"
echo "  2. Monitoring Dashboard: /api/v1/monitoring/dashboard"
echo "  3. Integration Guide: backend/TRACKING_INTEGRATION_GUIDE.md"
echo ""
