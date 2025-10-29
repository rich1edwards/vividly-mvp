# Database Migrations Ready to Run! 🎉

## Status: Authentication Fixed ✅

**Good news**:
- ✅ gcloud authentication is working (`rich1edwards@gmail.com`)
- ✅ Database instance is running (`dev-vividly-db`)
- ✅ Database password retrieved from Secret Manager
- ✅ Migration files are ready

## The Situation

Your database is configured with **private IP only** (no public IP) for security. This means:
- ✅ More secure (best practice)
- ℹ️ Requires VPC access or Cloud Shell to connect

## Recommended Approach: Use Cloud Shell (Easiest! 2 minutes)

Cloud Shell has direct access to your VPC, so migrations will work immediately.

### Step-by-Step Instructions

#### 1. Open Cloud Shell

Go to: https://console.cloud.google.com/?project=vividly-dev-rich

Click the **Cloud Shell** icon (>_) in the top right corner.

#### 2. Upload Migration Files

In Cloud Shell, run:

```bash
# Create directory
mkdir -p vividly-migrations
cd vividly-migrations

# Upload files (use the upload button in Cloud Shell or paste the content)
```

**Files to upload**:
- `backend/migrations/add_feature_flags.sql`
- `backend/migrations/add_request_tracking.sql`

**Or clone from your repo if you have one**:
```bash
# If you have a git repo
git clone YOUR_REPO_URL
cd YOUR_REPO/backend/migrations
```

#### 3. Run This Simple Command

```bash
# Set project
gcloud config set project vividly-dev-rich

# Get database info
DB_IP=$(gcloud sql instances describe dev-vividly-db \
  --format="value(ipAddresses[0].ipAddress)")

DB_PASSWORD=$(gcloud secrets versions access latest \
  --secret="database-url-dev" | \
  sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p')

# Export password
export PGPASSWORD="$DB_PASSWORD"

# Install psql if needed
sudo apt-get install -y postgresql-client

# Run migrations
psql -h $DB_IP -U vividly -d vividly -f add_feature_flags.sql
psql -h $DB_IP -U vividly -d vividly -f add_request_tracking.sql

# Verify
psql -h $DB_IP -U vividly -d vividly -c "SELECT COUNT(*) FROM feature_flags;"
psql -h $DB_IP -U vividly -d vividly -c "SELECT COUNT(*) FROM pipeline_stage_definitions;"
```

#### 4. Success!

You should see:
```
Feature Flags: 8 default flags
Pipeline Stages: 6 stages
```

---

## Alternative: Quick Copy-Paste Script

Create this file in Cloud Shell (`run_migrations.sh`):

```bash
#!/bin/bash
set -e

# Configuration
PROJECT_ID="vividly-dev-rich"
DB_INSTANCE="dev-vividly-db"

# Get database info
echo "Getting database connection info..."
DB_IP=$(gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID --format="value(ipAddresses[0].ipAddress)")
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project=$PROJECT_ID)
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p')

echo "Database IP: $DB_IP"

# Install psql if needed
if ! command -v psql &> /dev/null; then
    echo "Installing psql..."
    sudo apt-get update -qq && sudo apt-get install -y -qq postgresql-client
fi

# Set password
export PGPASSWORD="$DB_PASSWORD"

# Run migrations
echo "Running Feature Flags migration..."
psql -h $DB_IP -U vividly -d vividly -f add_feature_flags.sql

echo "Running Request Tracking migration..."
psql -h $DB_IP -U vividly -d vividly -f add_request_tracking.sql

# Verify
echo ""
echo "Verification:"
echo "Feature Flags: $(psql -h $DB_IP -U vividly -d vividly -t -c 'SELECT COUNT(*) FROM feature_flags;' | xargs)"
echo "Pipeline Stages: $(psql -h $DB_IP -U vividly -d vividly -t -c 'SELECT COUNT(*) FROM pipeline_stage_definitions;' | xargs)"
echo ""
echo "Success! ✓"
```

Then run:
```bash
chmod +x run_migrations.sh
./run_migrations.sh
```

---

## What Gets Created

### Feature Flags System (8 default flags)
1. `video_generation` - Enable AI video generation (enabled, 100%)
2. `advanced_analytics` - Advanced analytics dashboard (enabled, 0%)
3. `social_features` - Student collaboration (disabled)
4. `gamification` - Badges and leaderboards (disabled)
5. `offline_mode` - Offline video viewing (disabled)
6. `ai_tutoring` - AI tutoring chat (disabled)
7. `parent_portal` - Parent access (disabled)
8. `advanced_reporting` - Teacher reporting (enabled, 50%)

### Request Tracking System (6 pipeline stages)
1. `validation` - Request validation (2s avg)
2. `rag_retrieval` - OER content retrieval (10s avg)
3. `script_generation` - AI script generation (30s avg)
4. `video_generation` - Video generation (120s avg)
5. `video_processing` - Video processing & upload (20s avg)
6. `notification` - Student notification (2s avg)

### Database Tables Created (8 tables)
- `feature_flags`
- `feature_flag_overrides`
- `feature_flag_audit`
- `content_requests`
- `request_stages`
- `request_events`
- `request_metrics`
- `pipeline_stage_definitions`

### Views Created (2 views)
- `active_requests_dashboard` - For real-time monitoring
- `request_metrics_summary` - For hourly metrics

---

## After Migrations Complete

### 1. Test Feature Flags API

```python
from app.services.feature_flag_service import FeatureFlagService

service = FeatureFlagService(db)

# Check if feature is enabled
if service.is_enabled("video_generation", user_id="student-123"):
    # Generate video
    pass

# Get all flags for user
flags = service.get_all_flags(user_id="student-123")
# Returns: {'video_generation': True, 'social_features': False, ...}
```

### 2. Test Request Tracking

```python
from app.services.request_tracker import RequestTracker

tracker = RequestTracker(db)

# Create and track request
request_id, correlation_id = tracker.create_request(
    student_id="student-123",
    topic="Photosynthesis"
)

# Track stages
with tracker.track_stage(request_id, "rag_retrieval"):
    results = perform_rag_retrieval()

# Get status
status = tracker.get_request_status(request_id)
```

### 3. Access Monitoring Dashboard

- API Endpoint: `/api/v1/monitoring/dashboard`
- Real-time: `/api/v1/monitoring/stream` (Server-Sent Events)

---

## Troubleshooting

### "Password authentication failed"

The password extraction worked correctly. If you get this error, verify:
```bash
# Check database is running
gcloud sql instances describe dev-vividly-db --project=vividly-dev-rich

# Verify password
gcloud secrets versions access latest --secret="database-url-dev" --project=vividly-dev-rich
```

### "Could not connect to host"

Make sure you're in **Cloud Shell**, not your local terminal. Cloud Shell has VPC access.

### "Table already exists"

This is fine! It means the migrations already ran. You can verify with:
```bash
psql -h $DB_IP -U vividly -d vividly -c "\dt"
```

---

## Summary

**Quick Start (Cloud Shell)**:
1. Open Cloud Shell: https://console.cloud.google.com/?project=vividly-dev-rich
2. Upload migration SQL files
3. Run the script above
4. Done! ✓

**Total Time**: ~2 minutes

**Result**:
- ✅ 8 feature flags ready for A/B testing
- ✅ Request tracking system operational
- ✅ Real-time monitoring dashboard ready
- ✅ Complete pipeline visibility

---

## Documentation

- **Feature Flags**: See `backend/app/services/feature_flag_service.py`
- **Request Tracking**: See `REQUEST_TRACKING_SYSTEM.md`
- **Integration Guide**: See `backend/TRACKING_INTEGRATION_GUIDE.md`
- **Monitoring Dashboard**: See `frontend/src/components/MonitoringDashboard.tsx`

---

**Ready to run!** Just open Cloud Shell and follow the steps above. 🚀
