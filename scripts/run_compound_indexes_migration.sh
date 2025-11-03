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
# Extract password from URL: postgresql://user:password@host/db
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#^postgresql://[^:]*:\([^@]*\)@.*#\1#p')
export PGPASSWORD="$DB_PASSWORD"

echo "Extracted credentials (password length: ${#DB_PASSWORD})"

# Test connection
echo "Testing connection to $DB_IP..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" || {
    echo "Connection failed."
    exit 1
}

echo ""
echo "✓ Connection successful!"
echo ""

# Check if content_requests table exists
echo "================================================"
echo "  Checking Prerequisites"
echo "================================================"
TABLE_EXISTS=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'content_requests');" 2>/dev/null | xargs)

if [ "$TABLE_EXISTS" != "t" ]; then
    echo "ERROR: content_requests table does not exist!"
    echo "Please run the request_tracking migration first."
    exit 1
fi

echo "✓ content_requests table exists"
echo ""

# Check existing indexes before migration
echo "================================================"
echo "  Current Indexes on content_requests"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'content_requests'
  AND schemaname = 'public'
ORDER BY indexname;
"

echo ""
echo "================================================"
echo "  Running Compound Indexes Migration"
echo "================================================"
echo "This migration uses CREATE INDEX CONCURRENTLY which:"
echo "  - Does not block reads or writes"
echo "  - Safe for production use"
echo "  - May take several seconds per index"
echo ""

# Run the migration
# Note: Must run outside transaction block for CONCURRENTLY to work
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" \
    -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_compound_indexes_content_requests.sql \
    2>&1 | grep -v "CREATE INDEX CONCURRENTLY cannot run inside a transaction block" || true

echo ""
echo "✓ Compound Indexes migration completed"
echo ""

# Verify indexes were created
echo "================================================"
echo "  Verification - New Indexes"
echo "================================================"

EXPECTED_INDEXES=(
    "idx_content_requests_correlation_status"
    "idx_content_requests_student_status_created"
    "idx_content_requests_status_created"
    "idx_content_requests_org_status_created"
    "idx_content_requests_failed_debugging"
)

echo "Checking for expected indexes:"
for index_name in "${EXPECTED_INDEXES[@]}"; do
    INDEX_EXISTS=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'content_requests' AND indexname = '$index_name');" 2>/dev/null | xargs)

    if [ "$INDEX_EXISTS" = "t" ]; then
        echo "  ✓ $index_name"
    else
        echo "  ✗ $index_name (MISSING!)"
    fi
done

echo ""

# Show final index list with sizes
echo "================================================"
echo "  All Indexes on content_requests (with sizes)"
echo "================================================"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
SELECT
    indexrelname AS indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS times_used
FROM pg_stat_user_indexes
WHERE tablename = 'content_requests'
ORDER BY indexrelname;
"

echo ""
echo "================================================"
echo "  Compound Indexes Migration Complete! 🎉"
echo "================================================"
echo ""
echo "Next Steps:"
echo "  1. Rebuild worker Docker image with model fixes"
echo "  2. Deploy updated Cloud Run Job via Terraform"
echo "  3. Test worker processing"
echo ""
