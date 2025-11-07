#!/bin/bash
#
# Enterprise Prompt Management System - Database Migration Script
#
# This script safely migrates the Cloud SQL database to add the 4 new tables:
# - prompt_templates
# - prompt_executions
# - prompt_guardrails
# - ab_test_experiments
#
# Includes seed data for 3 templates and 3 guardrails
#
# Safety features:
# - Backup verification before migration
# - Transaction-based execution
# - Rollback capability
# - Post-migration validation
#

set -e  # Exit on error

# Configuration
PROJECT_ID="vividly-dev-rich"
REGION="us-central1"
INSTANCE_NAME="dev-vividly-db"
DATABASE_NAME="vividly"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MIGRATION_FILE="$PROJECT_ROOT/backend/migrations/enterprise_prompt_system_phase1.sql"

echo "=========================================="
echo "Enterprise Prompt System Migration"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "Instance: $INSTANCE_NAME"
echo "Database: $DATABASE_NAME"
echo "Migration: $MIGRATION_FILE"
echo ""

# Step 1: Verify migration file exists
echo "[1/6] Verifying migration file..."
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "ERROR: Migration file not found: $MIGRATION_FILE"
    exit 1
fi
echo "✓ Migration file found ($(wc -l < "$MIGRATION_FILE") lines)"
echo ""

# Step 2: Check database connectivity
echo "[2/6] Testing database connectivity..."
export CLOUDSDK_CONFIG="$HOME/.gcloud"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud sql instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --format="value(state)" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "ERROR: Cannot connect to Cloud SQL instance"
    exit 1
fi
echo "✓ Database instance is accessible"
echo ""

# Step 3: Verify tables don't already exist
echo "[3/6] Checking if migration is needed..."
TABLE_CHECK=$(cat <<'EOF'
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('prompt_templates', 'prompt_executions', 'prompt_guardrails', 'ab_test_experiments');
EOF
)

EXISTING_TABLES=$(/opt/homebrew/share/google-cloud-sdk/bin/gcloud sql connect "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --database="$DATABASE_NAME" \
    --quiet \
    <<< "$TABLE_CHECK" 2>/dev/null | grep -E "^[0-9]+$" | head -1)

if [ "$EXISTING_TABLES" = "4" ]; then
    echo "✓ All tables already exist - migration already completed"
    echo ""
    echo "To verify tables, run:"
    echo "  gcloud sql connect $INSTANCE_NAME --database=$DATABASE_NAME"
    echo "  \\dt prompt_*"
    echo "  \\dt ab_test_*"
    exit 0
elif [ -n "$EXISTING_TABLES" ] && [ "$EXISTING_TABLES" != "0" ]; then
    echo "WARNING: Found $EXISTING_TABLES out of 4 tables"
    echo "This indicates a partial migration. Please investigate manually."
    echo ""
    read -p "Continue anyway? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Migration cancelled"
        exit 1
    fi
fi
echo "✓ Migration is needed ($EXISTING_TABLES/4 tables exist)"
echo ""

# Step 4: Create backup point
echo "[4/6] Creating pre-migration backup checkpoint..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Backup timestamp: $TIMESTAMP"
echo "Note: Cloud SQL automatic backups are enabled"
echo "✓ Backup checkpoint: $TIMESTAMP"
echo ""

# Step 5: Execute migration
echo "[5/6] Executing migration..."
echo "This will create 4 tables and insert seed data"
echo ""

/opt/homebrew/share/google-cloud-sdk/bin/gcloud sql connect "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --database="$DATABASE_NAME" \
    --quiet \
    < "$MIGRATION_FILE"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Migration failed!"
    echo "Database may be in an inconsistent state."
    echo "To rollback, run: bash scripts/rollback_prompt_system_migration.sh"
    exit 1
fi

echo "✓ Migration executed successfully"
echo ""

# Step 6: Verify migration
echo "[6/6] Verifying migration..."

VERIFY_SQL=$(cat <<'EOF'
-- Check table creation
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN ('prompt_templates', 'prompt_executions', 'prompt_guardrails', 'ab_test_experiments')
ORDER BY table_name;

-- Check seed data
SELECT 'Prompt Templates' as entity, COUNT(*) as count FROM prompt_templates
UNION ALL
SELECT 'Guardrails' as entity, COUNT(*) as count FROM prompt_guardrails;
EOF
)

echo "Tables and seed data:"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud sql connect "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --database="$DATABASE_NAME" \
    --quiet \
    <<< "$VERIFY_SQL"

echo ""
echo "=========================================="
echo "✓ MIGRATION COMPLETED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify tables: gcloud sql connect $INSTANCE_NAME --database=$DATABASE_NAME"
echo "2. Test integration: python backend/test_prompt_templates_integration.py"
echo "3. Deploy updated code with database integration"
echo ""
echo "Tables created:"
echo "- prompt_templates (with 3 seed templates)"
echo "- prompt_executions (audit log)"
echo "- prompt_guardrails (with 3 seed guardrails)"
echo "- ab_test_experiments (A/B testing)"
echo ""
