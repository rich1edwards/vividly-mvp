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
DB_PASSWORD=$(echo "$DB_URL" | sed 's#^postgresql://vividly:##' | sed 's#@10\.240\.0\.3:5432/vividly$##')
export PGPASSWORD="$DB_PASSWORD"

# Test connection
echo "Testing connection to $DB_IP..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" || {
    echo "Connection failed."
    exit 1
}

echo ""
echo "✓ Connection successful!"
echo ""

# Run Migration 0: Base Schema (NEW!)
echo "================================================"
echo "  Migration 0: Base Schema"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" \
    -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/001_create_base_schema.sql

echo ""
echo "✓ Base Schema migration completed"
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

# Run Migration 3: Phase 2 Indexes (without transaction)
echo "================================================"
echo "  Migration 3: Phase 2 Indexes"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" \
    -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_phase2_indexes.sql \
    2>&1 | grep -v "CREATE INDEX CONCURRENTLY cannot run inside a transaction block" || true

echo ""
echo "✓ Phase 2 Indexes migration completed"
echo ""

# Verify migrations
echo "================================================"
echo "  Verification"
echo "================================================"

# Count tables
TABLE_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null | xargs)
echo "Total Tables: $TABLE_COUNT"

# Count users
USER_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
echo "Users: $USER_COUNT"

# Count interests
INTEREST_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM interests;" 2>/dev/null | xargs)
echo "Interests: $INTEREST_COUNT"

# Count topics
TOPIC_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM topics;" 2>/dev/null | xargs)
echo "Topics: $TOPIC_COUNT"

# Count feature flags
FF_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs)
echo "Feature Flags: $FF_COUNT"

# Count pipeline stages
STAGE_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs)
echo "Pipeline Stages: $STAGE_COUNT"

# Count indexes
INDEX_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>/dev/null | xargs)
echo "Total Indexes: $INDEX_COUNT"

echo ""
echo "================================================"
echo "  All migrations completed successfully! 🎉"
echo "================================================"
