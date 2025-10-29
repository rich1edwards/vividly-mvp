#!/bin/bash
set -e

# Configuration
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:/opt/homebrew/Cellar/postgresql@15/15.14/bin:$PATH"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

PROJECT_ID="vividly-dev-rich"
DB_IP="34.56.211.136"  # Public IP
DB_USER="vividly"
DB_NAME="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

# Get password with correct extraction
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)

# Extract password - everything between "vividly:" and "@10.240"
DB_PASSWORD=$(echo "$DB_URL" | sed 's#^postgresql://vividly:##' | sed 's#@10\.240\.0\.3:5432/vividly$##')

export PGPASSWORD="$DB_PASSWORD"

# Test connection
echo "Testing connection to $DB_IP..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" || {
    echo "Connection failed. Checking database status..."
    gcloud sql instances describe dev-vividly-db --project="$PROJECT_ID" --format="value(state)"
    exit 1
}

echo ""
echo "✓ Connection successful!"
echo ""

# Run Migration 1: Feature Flags
echo "================================================"
echo "  Migration 1: Feature Flags"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" \
    -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_feature_flags.sql

echo ""
echo "✓ Feature Flags migration completed"
echo ""

# Run Migration 2: Request Tracking
echo "================================================"
echo "  Migration 2: Request Tracking"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" \
    -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_request_tracking.sql

echo ""
echo "✓ Request Tracking migration completed"
echo ""

# Run Migration 3: Phase 2 Indexes
echo "================================================"
echo "  Migration 3: Phase 2 Indexes"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" \
    -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_phase2_indexes.sql

echo ""
echo "✓ Phase 2 Indexes migration completed"
echo ""

# Verify migrations
echo "================================================"
echo "  Verification"
echo "================================================"

FF_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs)
STAGE_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs)
INDEX_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%';" 2>/dev/null | xargs)

echo "Feature Flags: $FF_COUNT records"
echo "Pipeline Stages: $STAGE_COUNT records"
echo "Custom Indexes: $INDEX_COUNT indexes"
echo ""

echo "================================================"
echo "  All migrations completed successfully! 🎉"
echo "================================================"
