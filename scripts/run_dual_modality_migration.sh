#!/bin/bash
# ===================================
# Run Dual Modality Migration (Minimal)
# ===================================
# This script applies the minimal dual modality migration
# to the content_requests table in the dev database.
#
# Prerequisites:
# - Cloud SQL Proxy installed or direct connection to database
# - psql client installed
# - Appropriate database credentials
# ===================================

set -e  # Exit on error

PROJECT_ID="vividly-dev-rich"
INSTANCE_NAME="dev-vividly-db"
DATABASE_NAME="vividly"
MIGRATION_FILE="../backend/migrations/add_dual_modality_minimal.sql"

echo "===================================="
echo "Dual Modality Migration Script"
echo "===================================="
echo "Project: $PROJECT_ID"
echo "Instance: $INSTANCE_NAME"
echo "Database: $DATABASE_NAME"
echo "Migration: $MIGRATION_FILE"
echo ""

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "ERROR: Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "Migration file found. Contents:"
echo "---"
head -20 "$MIGRATION_FILE"
echo "... (truncated)"
echo "---"
echo ""

# Prompt for confirmation
read -p "Apply this migration to $INSTANCE_NAME/$DATABASE_NAME? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Migration cancelled."
    exit 0
fi

echo ""
echo "Connecting to Cloud SQL instance via gcloud sql connect..."
echo "Running migration..."
echo ""

# Run migration via gcloud sql connect
gcloud sql connect "$INSTANCE_NAME" \
    --user=postgres \
    --database="$DATABASE_NAME" \
    --project="$PROJECT_ID" \
    < "$MIGRATION_FILE"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "===================================="
    echo "MIGRATION SUCCESSFUL!"
    echo "===================================="
    echo "Dual modality columns added to content_requests table."
    echo "Next step: Deploy updated code with modality support."
else
    echo "===================================="
    echo "MIGRATION FAILED!"
    echo "===================================="
    echo "Exit code: $EXIT_CODE"
    echo "Check error messages above."
    echo "Rollback: Use rollback_add_dual_modality_minimal.sql if needed."
    exit $EXIT_CODE
fi
