# Vividly Database Connection Guide

## Quick Reference

### Connection Details
- **Instance**: `dev-vividly-db`
- **Project**: `vividly-dev-rich`
- **Public IP**: `34.56.211.136`
- **Private IP**: `10.240.0.3`
- **Database**: `vividly`
- **User**: `vividly`
- **Port**: `5432`
- **Authorized IP**: `162.239.0.122/32` (your public IP)

### Password Retrieval
Password is stored in Google Cloud Secret Manager:
```bash
gcloud secrets versions access latest --secret="database-url-dev" --project="vividly-dev-rich"
```

**Important**: Password contains special characters including `@@`, so extraction must be done carefully:
```bash
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="vividly-dev-rich" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed 's#^postgresql://vividly:##' | sed 's#@10\.240\.0\.3:5432/vividly$##')
```

Full connection string format: `postgresql://vividly:PASSWORD@10.240.0.3:5432/vividly`

## Ready-to-Use Scripts

### 1. Quick psql Connection
```bash
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:/opt/homebrew/Cellar/postgresql@15/15.14/bin:$PATH"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

PROJECT_ID="vividly-dev-rich"
DB_IP="34.56.211.136"
DB_USER="vividly"
DB_NAME="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed 's#^postgresql://vividly:##' | sed 's#@10\.240\.0\.3:5432/vividly$##')
export PGPASSWORD="$DB_PASSWORD"

"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME"
```

### 2. Run Single Query
```bash
# Same setup as above, then:
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM users;"
```

### 3. Run SQL File
```bash
# Same setup as above, then:
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -f path/to/migration.sql
```

## Available Helper Scripts

All scripts located in `/Users/richedwards/AI-Dev-Projects/Vividly/scripts/`:

### `reset_database.sh`
Drops and recreates the database (clean slate):
```bash
bash scripts/reset_database.sh
```

### `run_all_migrations_final.sh`
Runs all 4 migrations sequentially:
1. Base schema (14 tables)
2. Feature flags (3 tables)
3. Request tracking (5 tables)
4. Phase 2 indexes (127 total indexes)

```bash
bash scripts/run_all_migrations_final.sh
```

### `verify_database.sh`
Shows current database state (tables, data counts, indexes):
```bash
bash scripts/verify_database.sh
```

## Common Database Operations

### List All Tables
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

### Check Table Structure
```sql
\d table_name
```

### Count Records in Key Tables
```sql
SELECT
  'Users' as table, COUNT(*) as count FROM users
UNION ALL
SELECT 'Interests', COUNT(*) FROM interests
UNION ALL
SELECT 'Topics', COUNT(*) FROM topics
UNION ALL
SELECT 'Feature Flags', COUNT(*) FROM feature_flags;
```

### View All Indexes
```sql
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### Check Index Usage
```sql
SELECT schemaname, tablename, indexname, idx_scan as scans
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

## Connection Methods Comparison

### 1. Public IP (Current - Fastest)
- ✅ Direct connection from local machine
- ✅ Fastest (no proxy overhead)
- ⚠️ Requires IP whitelist (162.239.0.122/32)
- ⚠️ IP must be updated if it changes

**When to use**: Development work, running migrations, quick queries

### 2. Cloud Shell (Always Available)
- ✅ No IP restrictions
- ✅ Always works
- ❌ Slower (browser-based)
- ❌ Manual file uploads required

**When to use**: When public IP access isn't working, or IP has changed

### 3. Cloud SQL Proxy (Not Currently Set Up)
- ✅ Secure IAM-based auth
- ✅ Works from any IP
- ❌ Requires proxy setup
- ❌ Additional process to manage

## Troubleshooting

### Connection Refused
```bash
# Check database status
gcloud sql instances describe dev-vividly-db --project=vividly-dev-rich
```

### Password Authentication Failed
- Password contains `@@` - ensure sed extraction is correct
- Use the exact extraction pattern shown above

### Public IP Changed
```bash
# Get new public IP
curl https://api.ipify.org

# Update authorized networks
gcloud sql instances patch dev-vividly-db \
  --project=vividly-dev-rich \
  --authorized-networks=NEW_IP/32
```

### Database State Issues
```bash
# Reset to clean state
bash scripts/reset_database.sh

# Run all migrations
bash scripts/run_all_migrations_final.sh

# Verify
bash scripts/verify_database.sh
```

## Current Database Schema

### Tables (22 total)
1. **Base Schema (14)**:
   - organizations, schools, users
   - classes, class_student
   - interests, student_interest
   - topics, student_progress, student_activity
   - content_metadata
   - sessions, password_reset, student_request

2. **Feature Flags (3)**:
   - feature_flags, feature_flag_overrides, feature_flag_audit

3. **Request Tracking (5)**:
   - content_requests, request_stages, request_events
   - request_metrics, pipeline_stage_definitions

### Sample Data Preloaded
- 14 interests (basketball, coding, music, etc.)
- 5 Physics topics (Newton's Laws)
- 8 feature flags (video_generation, analytics, etc.)
- 6 pipeline stages (validation → RAG → script → video → upload → notify)
- 1 organization (Metropolitan Nashville Public Schools)
- 1 school (Hillsboro High School)

### Performance
- 127 indexes for query optimization
- Expected login time: < 50ms
- Expected profile queries: < 100ms
- Expected list queries: < 200ms

## Migration Files

Located in `/Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/`:

1. `001_create_base_schema.sql` - Foundation (14 tables, 65 indexes)
2. `add_feature_flags.sql` - Feature flag system (3 tables)
3. `add_request_tracking.sql` - Content pipeline tracking (5 tables)
4. `add_phase2_indexes.sql` - Performance optimization (62 indexes)

## Notes

- PostgreSQL version: 15.14
- All passwords hashed with bcrypt (cost: 12)
- JWT tokens: 24h access, 30d refresh
- Soft deletes enabled (archived/deleted flags)
- JSONB fields for flexible schema evolution
- All migrations are idempotent (safe to re-run)
