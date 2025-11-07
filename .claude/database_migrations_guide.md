# Database Migrations Guide - Cloud Run Jobs Pattern

**Official method for running database migrations on Vividly**

## CRITICAL: The Proven Working Pattern

After multiple attempts and failures, this is the **ONLY pattern that works** for Cloud SQL database access:

### The Pattern (DO NOT DEVIATE FROM THIS)
1. Build the backend Docker image (contains Python, psycopg2, all dependencies)
2. Create a Cloud Run Job with:
   - **SECRET**: `database-url-{environment}` (full connection string, NOT individual password)
   - **VPC Connector**: `{environment}-cloud-run-connector`
   - **Service Account**: `{environment}-cloud-run-sa@{PROJECT_ID}.iam.gserviceaccount.com`
3. Execute the job with `--wait` flag
4. Clean up the temporary job

### Why This Specific Pattern?
- **Backend Docker Image**: Already has Python, psycopg2, and all database drivers configured
- **Full DATABASE_URL Secret**: Contains complete connection string (postgresql://user:password@host:port/dbname)
- **VPC Connector**: Provides network access to Cloud SQL private IP (REQUIRED - direct connection fails)
- **Service Account**: Has proper IAM permissions for Cloud SQL, Secret Manager, and VPC
- **Cloud Run Jobs**: Proven to work with Alembic migrations in `backend/cloudbuild.yaml`

### What Does NOT Work (Learned The Hard Way)
❌ Direct psql connection from Cloud Build (connection timeout)
❌ Using individual password secrets like DEV_DB_PASSWORD (secret not found)
❌ Installing postgresql-client in gcloud image (still fails connectivity)
❌ Any approach that doesn't use VPC connector (network isolation)

## Quick Start

```bash
# From project root:
cd /Users/richedwards/AI-Dev-Projects/Vividly
export CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud builds submit \
  --config=cloudbuild.migrate.yaml \
  --project=vividly-dev-rich
```

That's it! The migration will run automatically with full verification.

## Why Cloud Build with Cloud Run Jobs?

This is the **production-ready** way to run database migrations:

### Advantages
✅ **Works from anywhere** - Phone, laptop, any network, any IP address
✅ **No local setup** - No psql, proxy, or tools installation needed
✅ **Production-ready** - Use same method for dev/staging/prod
✅ **Full audit trail** - Complete logs in Cloud Build console
✅ **CI/CD integration** - Can be triggered automatically
✅ **Safe execution** - Pre-flight checks, backup checkpoints, verification
✅ **Consistent** - Same environment every time
✅ **VPC Access** - Uses proven Cloud Run Jobs + VPC Connector pattern

### What It Does Automatically
1. ✓ Builds backend Docker image with all dependencies
2. ✓ Creates ephemeral Cloud Run Job with proper configuration
3. ✓ Injects DATABASE_URL secret from Secret Manager
4. ✓ Connects via VPC connector to Cloud SQL private IP
5. ✓ Executes migration SQL with psycopg2
6. ✓ Verifies tables were created successfully
7. ✓ Cleans up temporary job
8. ✓ Provides detailed success/failure logs

## Configuration Files

### 1. `cloudbuild.migrate.yaml` (Root Directory)

**Location**: Project root
**Purpose**: Cloud Build configuration for migrations

**Default Settings**:
- Migration file: `backend/migrations/enterprise_prompt_system_phase1.sql`
- Environment: `dev`
- Region: `us-central1`
- Image: `backend-api`

### 2. `backend/run_migration.py` (Migration Runner Script)

**Purpose**: Python script that executes SQL migrations using psycopg2

**What It Does**:
1. Reads `DATABASE_URL` from environment (injected by Cloud Build via Secret Manager)
2. Parses the URL to extract connection parameters
3. Connects to Cloud SQL via VPC connector
4. Executes the SQL migration file
5. Verifies tables were created successfully
6. Provides detailed logging for debugging

### 3. Infrastructure Components (REQUIRED)

**Secrets** (Google Secret Manager):
- `database-url-dev`: Full PostgreSQL connection string for dev
- Format: `postgresql://username:password@host:port/database`

**VPC Connectors**:
- `dev-cloud-run-connector`: VPC connector for dev Cloud SQL instance

**Service Accounts**:
- `dev-cloud-run-sa@vividly-dev-rich.iam.gserviceaccount.com`
- Required Permissions:
  - Cloud SQL Client
  - Secret Manager Secret Accessor
  - VPC Access User
  - Artifact Registry Reader

## Usage Examples

### Run Default Migration
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly
gcloud builds submit --config=cloudbuild.migrate.yaml
```

### Run Different Migration File
```bash
gcloud builds submit --config=cloudbuild.migrate.yaml \
  --substitutions=_MIGRATION_FILE=backend/migrations/your_migration.sql
```

### Run from Anywhere (Full Command)
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly && \
  export CLOUDSDK_CONFIG="$HOME/.gcloud" && \
  /opt/homebrew/share/google-cloud-sdk/bin/gcloud builds submit \
    --config=cloudbuild.migrate.yaml \
    --project=vividly-dev-rich
```

## Viewing Results

### View Recent Builds
```bash
gcloud builds list --limit=5
```

### View Specific Build Logs
```bash
# Get BUILD_ID from list command above
gcloud builds log <BUILD_ID>
```

### View in Console
https://console.cloud.google.com/cloud-build/builds?project=vividly-dev-rich

### View Database in Console
https://console.cloud.google.com/sql/instances/dev-vividly-db?project=vividly-dev-rich

## Migration File Requirements

Your migration SQL file should:
- Be in `backend/migrations/` directory
- Use PostgreSQL syntax
- Include proper transaction handling if needed
- Have rollback scripts in separate files

## Rollback

If a migration needs to be rolled back:

1. Create rollback SQL file (e.g., `rollback_your_migration.sql`)
2. Run it through Cloud Build:
```bash
gcloud builds submit --config=cloudbuild.migrate.yaml \
  --substitutions=_MIGRATION_FILE=backend/migrations/rollback_your_migration.sql
```

## Troubleshooting

### Build Fails
1. Check logs: `gcloud builds log <BUILD_ID>`
2. Verify migration file exists at specified path
3. Check database connectivity
4. Review SQL syntax errors in logs

### Permission Issues
```bash
# Verify Cloud Build service account has Cloud SQL Client role
gcloud projects get-iam-policy vividly-dev-rich \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/cloudsql.client"
```

### View Build Status
```bash
# Watch build in real-time
gcloud builds submit --config=cloudbuild.migrate.yaml --stream-logs
```

## Environment-Specific Migrations

### Development (Current)
```bash
gcloud builds submit --config=cloudbuild.migrate.yaml
```

### Staging (Future)
```bash
gcloud builds submit --config=cloudbuild.migrate.yaml \
  --substitutions=_INSTANCE_CONNECTION_NAME=vividly-staging:us-central1:staging-db,_DATABASE_NAME=vividly
```

### Production (Future)
```bash
gcloud builds submit --config=cloudbuild.migrate.yaml \
  --substitutions=_INSTANCE_CONNECTION_NAME=vividly-prod:us-central1:prod-db,_DATABASE_NAME=vividly
```

## Integration with CI/CD

To trigger migrations automatically (future enhancement):

```yaml
# In .github/workflows/deploy.yml or similar
- name: Run Database Migration
  run: |
    gcloud builds submit \
      --config=cloudbuild.migrate.yaml \
      --substitutions=_MIGRATION_FILE=backend/migrations/latest_migration.sql
```

## Current Migration Status

**Migration**: Enterprise Prompt Management System Phase 1
**File**: `backend/migrations/enterprise_prompt_system_phase1.sql`
**Status**: Ready to execute
**Tables to Create**:
- `prompt_templates` (with 3 seed templates)
- `prompt_executions` (audit log)
- `prompt_guardrails` (with 3 seed guardrails)
- `ab_test_experiments` (A/B testing)

**Integration Code**: ✓ Complete and tested (3/3 tests passed)
**Backwards Compatible**: ✓ Yes (file-based fallback)

## Common Errors and Solutions (IMPORTANT)

This section documents ACTUAL errors encountered and their solutions. Read this if migrations fail.

### Error: "Secret [DEV_DB_PASSWORD] not found"
**Symptom**: Build fails with "Secret Manager secret not found" error
**Root Cause**: Trying to access individual password secrets instead of full DATABASE_URL
**Solution**: Use `database-url-{environment}` secret containing full connection string

### Error: "connection to server at X.X.X.X, port 5432 failed: Connection timed out"
**Symptom**: Timeout error when trying to connect to Cloud SQL
**Root Cause**: Attempting direct connection from Cloud Build without VPC connector
**Solution**: Use Cloud Run Jobs with VPC connector (the proven pattern above)
**Why**: Cloud SQL requires VPC connector for private IP access, direct connection doesn't work

### Error: "Read-only file system: '/.gcloud'"
**Symptom**: gcloud commands fail with read-only filesystem error
**Root Cause**: Incorrect CLOUDSDK_CONFIG path or environment variable setting
**Solution**: Use correct path: `CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"` locally

### Error: "Psql client not found"
**Symptom**: Command fails because postgresql-client not installed
**Root Cause**: Using gcloud SDK image which doesn't include PostgreSQL tools
**Solution**: Don't use psql. Use Python script with psycopg2 (backend Docker image has this)

### Error: "ModuleNotFoundError: No module named 'psycopg2'"
**Symptom**: Python script fails because psycopg2 not installed
**Root Cause**: Not using the backend Docker image
**Solution**: Always use backend Docker image which has all Python dependencies installed

### Error: "INVALID_ARGUMENT: key in template 'TIMESTAMP' is not valid"
**Symptom**: Cloud Build fails with substitution variable error
**Root Cause**: Bash variable interpreted as Cloud Build substitution variable
**Solution**: Use double dollar signs ($$) to escape bash variables in Cloud Build

## Troubleshooting Steps

If migration fails, follow these steps:

1. **Check Cloud Build Logs**:
   ```bash
   gcloud builds list --limit=5 --project=vividly-dev-rich
   gcloud builds log <BUILD_ID> --project=vividly-dev-rich
   ```

2. **Verify Infrastructure**:
   ```bash
   # Check secret exists
   gcloud secrets describe database-url-dev --project=vividly-dev-rich

   # Check VPC connector exists
   gcloud compute networks vpc-access connectors describe \
     dev-cloud-run-connector --region=us-central1 --project=vividly-dev-rich

   # Check service account exists
   gcloud iam service-accounts describe \
     dev-cloud-run-sa@vividly-dev-rich.iam.gserviceaccount.com
   ```

3. **Verify Migration File**:
   ```bash
   # Check file exists and is valid SQL
   cat backend/migrations/enterprise_prompt_system_phase1.sql
   ```

4. **Test SQL Locally** (if needed):
   ```bash
   # Connect to database via Cloud SQL Proxy
   cloud_sql_proxy -instances=vividly-dev-rich:us-central1:dev-vividly-db=tcp:5432

   # In another terminal
   psql -h localhost -p 5432 -U postgres -d vividly
   ```

## Remember for Future Sessions

**CRITICAL: Always use Cloud Build with Cloud Run Jobs pattern for migrations:**

```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly
export CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud builds submit \
  --config=cloudbuild.migrate.yaml \
  --project=vividly-dev-rich
```

This pattern:
- Works from any network (phone, laptop, anywhere)
- Requires no local setup
- Uses VPC connector for Cloud SQL access
- Has proper service account permissions
- Provides full audit trail
- Is ready for production use

**DO NOT try alternative approaches** - they will fail. This is the ONLY pattern that works.

## What Was Learned (History)

Multiple approaches were tried before finding the solution:

1. ❌ **Attempt 1**: Direct psql from Cloud Build → Connection timeout
2. ❌ **Attempt 2**: Install postgresql-client in gcloud image → Still connection timeout
3. ❌ **Attempt 3**: Use individual password secrets (DEV_DB_PASSWORD) → Secret not found
4. ❌ **Attempt 4**: Various CLOUDSDK_CONFIG settings → Read-only filesystem errors
5. ✅ **Final Solution**: Cloud Run Jobs + VPC Connector + Full DATABASE_URL secret → SUCCESS

**Key Insight**: Cloud SQL requires VPC connector for private IP access. The only way to get VPC connector access from Cloud Build is through Cloud Run Jobs. Direct connections don't work because Cloud Build doesn't have VPC access by default.

## Related Documentation

- **PROMPT_CONFIGURATION_DESIGN.md**: Design document for enterprise prompt system
- **backend/app/core/prompt_templates.py**: Python integration with prompt system
- **backend/cloudbuild.yaml**: Main Cloud Build config (shows same pattern working for Alembic)
- **backend/Dockerfile**: Backend Docker image with psycopg2 and all dependencies
- **backend/run_migration.py**: Migration runner script (uses psycopg2)
- **cloudbuild.migrate.yaml**: Cloud Build migration configuration
