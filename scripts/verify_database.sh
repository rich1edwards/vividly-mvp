#!/bin/bash
set -e

# Configuration
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:/opt/homebrew/Cellar/postgresql@15/15.14/bin:$PATH"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

PROJECT_ID="vividly-dev-rich"
DB_IP="34.56.211.136"
DB_USER="vividly"
DB_NAME="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

# Get password
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed 's#^postgresql://vividly:##' | sed 's#@10\.240\.0\.3:5432/vividly$##')
export PGPASSWORD="$DB_PASSWORD"

echo "=========================================="
echo "  Vividly Database Verification"
echo "=========================================="
echo ""

echo "Tables:"
echo "-------"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;"

echo ""
echo "Sample Data Counts:"
echo "-------------------"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT
  'Interests: ' || COUNT(*) FROM interests
UNION ALL
SELECT 'Topics: ' || COUNT(*) FROM topics
UNION ALL
SELECT 'Feature Flags: ' || COUNT(*) FROM feature_flags
UNION ALL
SELECT 'Pipeline Stages: ' || COUNT(*) FROM pipeline_stage_definitions
UNION ALL
SELECT 'Organizations: ' || COUNT(*) FROM organizations
UNION ALL
SELECT 'Schools: ' || COUNT(*) FROM schools;"

echo ""
echo "Index Count:"
echo "------------"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT COUNT(*) || ' indexes'
FROM pg_indexes
WHERE schemaname = 'public';"

echo ""
echo "Database Types:"
echo "---------------"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT typname
FROM pg_type
WHERE typtype = 'e'
ORDER BY typname;"

echo ""
echo "=========================================="
echo "  Verification Complete"
echo "=========================================="
