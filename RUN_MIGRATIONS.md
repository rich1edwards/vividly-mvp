# Running Database Migrations

Complete guide for running the new database migrations on your Cloud SQL instance.

## Migrations to Run

We have **2 new migration files** ready:

1. **Feature Flags System** (`backend/migrations/add_feature_flags.sql`)
   - Adds feature flag tables
   - Enables controlled rollouts
   - Includes audit trail

2. **Request Tracking System** (`backend/migrations/add_request_tracking.sql`)
   - Adds request tracking tables
   - Enables end-to-end monitoring
   - Includes real-time dashboard support

---

## Option 1: Using Cloud SQL Proxy (Recommended)

### Step 1: Get Database Password

```bash
cd terraform

# Get the database password from Terraform state
terraform output -raw db_password
```

### Step 2: Start Cloud SQL Proxy

```bash
# Download Cloud SQL Proxy if not installed
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.7.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Get connection name
export CONNECTION_NAME=$(gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich \
  --format="value(connectionName)")

# Start proxy in background
./cloud-sql-proxy $CONNECTION_NAME &

# Proxy will listen on localhost:5432
```

### Step 3: Run Migrations

```bash
# Set environment variables
export PGPASSWORD="<password-from-step-1>"
export PGHOST="127.0.0.1"
export PGPORT="5432"
export PGUSER="vividly"
export PGDATABASE="vividly"

# Run feature flags migration
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -f backend/migrations/add_feature_flags.sql

# Run request tracking migration
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE \
  -f backend/migrations/add_request_tracking.sql
```

### Step 4: Verify Migrations

```bash
# Check that tables were created
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "\dt"

# Should see these new tables:
# - feature_flags
# - feature_flag_overrides
# - feature_flag_audit
# - content_requests
# - request_stages
# - request_events
# - request_metrics
# - pipeline_stage_definitions
```

### Step 5: Stop Cloud SQL Proxy

```bash
# Find and kill the proxy process
pkill -f cloud-sql-proxy
```

---

## Option 2: Using gcloud sql connect

```bash
# Get password
export DB_PASSWORD=$(cd terraform && terraform output -raw db_password)

# Connect and run migrations
gcloud sql connect dev-vividly-db \
  --project=vividly-dev-rich \
  --user=vividly \
  --database=vividly \
  <<EOF
\i backend/migrations/add_feature_flags.sql
\i backend/migrations/add_request_tracking.sql
\q
EOF
```

When prompted, enter the password from `$DB_PASSWORD`.

---

## Option 3: Manual Steps (If Terraform State Not Available)

### Step 1: Get Database Connection Info

```bash
# Get connection name
gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich \
  --format="value(connectionName)"

# Get private IP (if using VPC)
gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich \
  --format="value(ipAddresses[0].ipAddress)"
```

### Step 2: Get Database Password

```bash
# Password is stored in Secret Manager
gcloud secrets versions access latest \
  --secret="database-password-dev" \
  --project=vividly-dev-rich
```

### Step 3: Run Migrations

Use Option 1 (Cloud SQL Proxy) or Option 2 (gcloud sql connect) above with the retrieved credentials.

---

## Verification Steps

After running migrations, verify the setup:

### Check Feature Flags

```sql
-- Connect to database
psql -h 127.0.0.1 -U vividly -d vividly

-- Check feature flags table
SELECT key, name, enabled, rollout_percentage
FROM feature_flags;

-- Should see default flags:
-- - video_generation (enabled, 100%)
-- - advanced_analytics (enabled, 0%)
-- - social_features (disabled, 0%)
-- - gamification (disabled, 0%)
-- etc.
```

### Check Request Tracking

```sql
-- Check pipeline stage definitions
SELECT stage_name, display_name, stage_order, estimated_duration_seconds
FROM pipeline_stage_definitions
ORDER BY stage_order;

-- Should see 6 stages:
-- 1. validation (2s)
-- 2. rag_retrieval (10s)
-- 3. script_generation (30s)
-- 4. video_generation (120s)
-- 5. video_processing (20s)
-- 6. notification (2s)

-- Check views
SELECT * FROM active_requests_dashboard LIMIT 1;
SELECT * FROM request_metrics_summary LIMIT 1;
```

---

## Troubleshooting

### "psql: command not found"

Install PostgreSQL client:

**macOS**:
```bash
brew install postgresql@15
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
```

**Ubuntu/Debian**:
```bash
sudo apt-get install postgresql-client-15
```

### "Connection refused"

Make sure Cloud SQL Proxy is running:
```bash
ps aux | grep cloud-sql-proxy
```

### "Password authentication failed"

Double-check password from Terraform:
```bash
cd terraform
terraform output db_password
```

### "Database does not exist"

Create the database first:
```bash
gcloud sql databases create vividly \
  --instance=dev-vividly-db \
  --project=vividly-dev-rich
```

---

## Post-Migration Tasks

### 1. Update Application Environment Variables

Add to your `.env` or environment configuration:

```bash
# Feature flags are now available
# Enable in your FastAPI app:
# from app.services.feature_flag_service import FeatureFlagService

# Request tracking is ready
# Start using in your content pipeline:
# from app.services.request_tracker import RequestTracker
```

### 2. Test Feature Flags API

```bash
# Get access token
export TOKEN="your-jwt-token"

# List all feature flags
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api.com/api/v1/feature-flags

# Check specific flag
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api.com/api/v1/feature-flags/check/video_generation
```

### 3. Test Request Tracking

```python
# In your Python code
from app.services.request_tracker import RequestTracker
from sqlalchemy.orm import Session

def test_request_tracking(db: Session):
    tracker = RequestTracker(db)

    # Create test request
    request_id, correlation_id = tracker.create_request(
        student_id="test-student-id",
        topic="Test Topic",
        learning_objective="Test learning"
    )

    print(f"Created request: {request_id}")
    print(f"Correlation ID: {correlation_id}")

    # Check status
    status = tracker.get_request_status(request_id)
    print(f"Status: {status}")
```

---

## Summary

**Quick Commands** (assuming gcloud is authenticated):

```bash
# 1. Get password
export PGPASSWORD=$(cd terraform && terraform output -raw db_password)

# 2. Connect via gcloud
gcloud sql connect dev-vividly-db \
  --project=vividly-dev-rich \
  --user=vividly \
  --database=vividly

# 3. Run migrations (in psql)
\i backend/migrations/add_feature_flags.sql
\i backend/migrations/add_request_tracking.sql

# 4. Verify
\dt
SELECT COUNT(*) FROM feature_flags;
SELECT COUNT(*) FROM pipeline_stage_definitions;

# 5. Exit
\q
```

**Result**:
- ✅ Feature flags system ready for controlled rollouts
- ✅ Request tracking system ready for monitoring dashboard
- ✅ Real-time pipeline visibility enabled
- ✅ 8 new tables created with proper indexes and triggers

---

## Next Steps After Migrations

1. **Integrate Feature Flags** - Start using flags in your code
2. **Integrate Request Tracking** - Add tracker calls to content pipeline
3. **Deploy Monitoring Dashboard** - Make dashboard accessible to teachers/admins
4. **Test End-to-End** - Submit a test content request and watch it flow through the system

**Documentation**:
- Feature Flags: See item #14 in `MVP_COMPLETION_STATUS.md`
- Request Tracking: See `REQUEST_TRACKING_SYSTEM.md` and `TRACKING_INTEGRATION_GUIDE.md`
