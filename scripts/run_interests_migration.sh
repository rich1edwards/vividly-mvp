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
echo "Running Expanded Interests with Icons migration..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f /Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_expanded_interests_with_icons.sql

echo ""
echo "Verifying migration..."
INTEREST_COUNT=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM interests;" 2>/dev/null | xargs)
WITH_ICONS=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM interests WHERE icon IS NOT NULL;" 2>/dev/null | xargs)

echo "Total Interests: $INTEREST_COUNT"
echo "Interests with Icons: $WITH_ICONS"
echo ""

# Show sample of interests by category
echo "Sample of interests by category:"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT category, COUNT(*) as count FROM interests GROUP BY category ORDER BY category;"

echo ""
echo "Migration completed successfully!"
