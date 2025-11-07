# Cloud SQL Database Connection Guide

This guide documents how to connect to the Vividly Cloud SQL database for running migrations.

## Database Information

- **Project ID**: vividly-dev-rich
- **Instance Name**: dev-vividly-db
- **Connection Name**: vividly-dev-rich:us-central1:dev-vividly-db
- **Database Name**: vividly
- **Region**: us-central1

## Connection Methods Attempted

### Method 1: Direct `gcloud sql connect` (FAILED)
```bash
export CLOUDSDK_CONFIG="$HOME/.gcloud"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud sql connect dev-vividly-db \
    --database=vividly \
    --project=vividly-dev-rich
```

**Issue**: IPv6 network not supported
```
ERROR: HTTPError 400: Invalid request: CloudSQL Second Generation doesn't support
IPv6 networks/subnets: 2600:1004:b30d:937c:f0ea:f336:869b:7b1e
```

### Method 2: Beta `gcloud beta sql connect` with Cloud SQL Proxy (FAILED)
```bash
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud beta sql connect dev-vividly-db \
    --database=vividly \
    --project=vividly-dev-rich
```

**Issues**:
1. Required Cloud SQL Proxy v1 installation (✓ INSTALLED)
2. Required psql client installation (✗ NOT INSTALLED)

### Method 3: Python with Cloud SQL Connector (FAILED)
Using `google.cloud.sql.connector` Python library.

**Issue**: Library not installed in global Python environment

## Recommended Solutions

### Option A: Run Migration from Cloud Shell (RECOMMENDED)
Cloud Shell has all required tools pre-installed and uses IPv4:

```bash
# 1. Open Cloud Shell at https://console.cloud.google.com
# 2. Clone or upload the migration file
# 3. Run migration:
gcloud sql connect dev-vividly-db \
    --database=vividly \
    --project=vividly-dev-rich \
    < backend/migrations/enterprise_prompt_system_phase1.sql
```

### Option B: Install psql Client Locally
Install PostgreSQL client tools:

```bash
# Install via Homebrew
brew install postgresql@15

# Add to PATH
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Then use beta command with Cloud SQL Proxy
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
gcloud beta sql connect dev-vividly-db \
    --database=vividly \
    --project=vividly-dev-rich \
    < backend/migrations/enterprise_prompt_system_phase1.sql
```

### Option C: Use Cloud Build for Migration
Create a Cloud Build job that runs the migration:

```yaml
# cloudbuild.migrate.yaml
steps:
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'sql'
      - 'connect'
      - 'dev-vividly-db'
      - '--database=vividly'
      - '--project=vividly-dev-rich'
    stdin: backend/migrations/enterprise_prompt_system_phase1.sql
```

Run with:
```bash
gcloud builds submit --config=cloudbuild.migrate.yaml
```

### Option D: Use Python Script with Backend Virtual Environment
If the backend has a virtual environment with cloud-sql-python-connector installed:

```bash
# Activate backend venv
cd backend
source venv/bin/activate  # or wherever the venv is

# Run migration script
python ../scripts/run_migration_via_python.py
```

## Environment Configuration

### Required Environment Variables
```bash
# For gcloud commands
export CLOUDSDK_CONFIG="$HOME/.gcloud"

# For Cloud SQL Proxy
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
```

### gcloud Configuration Path
The gcloud SDK is installed at:
```
/opt/homebrew/share/google-cloud-sdk/
```

Binaries are at:
```
/opt/homebrew/share/google-cloud-sdk/bin/
```

Cloud SQL Proxy v1 is installed at:
```
/opt/homebrew/share/google-cloud-sdk/bin/cloud_sql_proxy
```

## Previous Working Patterns

Previous migration scripts successfully used this pattern:
```bash
gcloud sql connect "$INSTANCE_NAME" \
    --database="$DATABASE_NAME" \
    --project="$PROJECT_ID" \
    --quiet \
    <<< "$SQL_QUERY"
```

However, this now fails due to IPv6 network restrictions.

## Migration Files

### Ready to Execute
- **Main Migration**: `/Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/enterprise_prompt_system_phase1.sql`
  - 688 lines
  - Creates 4 tables: prompt_templates, prompt_executions, prompt_guardrails, ab_test_experiments
  - Includes seed data for 3 templates and 3 guardrails

### Migration Scripts
- **Bash Script**: `/Users/richedwards/AI-Dev-Projects/Vividly/scripts/run_prompt_system_migration.sh`
- **Python Script**: `/Users/richedwards/AI-Dev-Projects/Vividly/scripts/run_migration_via_python.py`

## Testing After Migration

After successful migration, test the integration:

```bash
cd backend
python test_prompt_templates_integration.py
```

This should show:
- ✓ File-based fallback works
- ✓ Database integration works
- ✓ All 3 tests pass

## Current Status

**Migration Status**: NOT YET EXECUTED

**Blockers**:
1. Local IPv6 network prevents direct `gcloud sql connect`
2. psql client not installed locally
3. Cloud SQL Python Connector not in global Python environment

**Recommendation**: Use **Option A (Cloud Shell)** for quickest resolution.
