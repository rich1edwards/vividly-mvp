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

echo "Resetting password for john.doe.11@student.hillsboro.edu..."

# Generate bcrypt hash for Student123!
# Using Python to generate the hash
NEW_PASSWORD="Student123!"
HASH=$(python3 -c "import bcrypt; salt = bcrypt.gensalt(rounds=12); print(bcrypt.hashpw(b'$NEW_PASSWORD', salt).decode('utf-8'))")

echo "New password hash generated: ${HASH:0:20}..."

# Update the password
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d vividly -c \
  "UPDATE users SET password_hash = '$HASH' WHERE email = 'john.doe.11@student.hillsboro.edu';"

echo ""
echo "✓ Password reset successfully!"
echo "  Email: john.doe.11@student.hillsboro.edu"
echo "  Password: $NEW_PASSWORD"
