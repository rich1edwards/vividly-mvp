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

# Get password
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p')

export PGPASSWORD="$DB_PASSWORD"

# Test connection
echo "Testing connection to $DB_IP..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" || exit 1

echo ""
echo "Running Feature Flags migration..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_feature_flags.sql

echo ""
echo "Running Request Tracking migration..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_request_tracking.sql

echo ""
echo "Running Phase 2 Indexes migration..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_phase2_indexes.sql

echo ""
echo "Verifying migrations..."
FF_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs)
STAGE_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs)
INDEX_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%';" 2>/dev/null | xargs)

echo "Feature Flags: $FF_COUNT"
echo "Pipeline Stages: $STAGE_COUNT"
echo "Custom Indexes: $INDEX_COUNT"
echo ""
echo "Migrations completed successfully!"
