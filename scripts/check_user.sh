#!/bin/bash
set -e

export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:/opt/homebrew/Cellar/postgresql@15/15.14/bin:$PATH"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

PROJECT_ID="vividly-dev-rich"
DB_IP="34.56.211.136"
DB_USER="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

# Get password
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed 's#^postgresql://vividly:##' | sed 's#@/vividly?host=/cloudsql/.*##')
export PGPASSWORD="$DB_PASSWORD"

echo "Checking for john.doe users..."
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d vividly -c "SELECT email, role, status FROM users WHERE email LIKE '%john.doe%';"
