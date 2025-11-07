# Session 11 Part 17: Build #5 Monitoring & Post-Migration Plan

## Current Status

**Build ID**: `019a66fe-1e49-4ecb-a079-9f90a427a58e`
**Status**: RUNNING (uploading source ~ 1.1 GiB)
**Started**: 2025-11-06 ~22:24 UTC
**Expected Duration**: 5-10 minutes

**Root Cause Fixed**: DATABASE_URL secret updated to version 5 with private IP format

---

## Build #5 Configuration

### Secret Update Applied
```
OLD: postgresql://vividly:***@/vividly?host=/cloudsql/vividly-dev-rich:us-central1:dev-vividly-db
NEW: postgresql://vividly:***@10.240.0.3:5432/vividly
```

### Build Steps
1. **build-image**: Build backend Docker image with migration runner
2. **push-image**: Push to `us-central1-docker.pkg.dev/vividly-dev-rich/vividly/backend-api:migration`
3. **run-migration**: Execute Cloud Run Job with DATABASE_URL from Secret Manager
4. **cleanup-migration-job**: Delete ephemeral migration job

### Expected Behavior
```python
# run_migration.py will now correctly parse:
parsed = urlparse("postgresql://vividly:***@10.240.0.3:5432/vividly")
# Result:
#   parsed.hostname = "10.240.0.3" ✓
#   parsed.port = 5432 ✓

# psycopg2 will connect via TCP/IP:
conn = psycopg2.connect(
    host="10.240.0.3",  # Correct
    port=5432,          # Correct
    database="vividly",
    user="vividly",
    password="***"
)
```

---

## Post-Build Verification Plan

### Step 1: Verify Build Success

**Command**:
```bash
export CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud builds describe \
  019a66fe-1e49-4ecb-a079-9f90a427a58e \
  --project=vividly-dev-rich \
  --format="value(status,timing.BUILD.startTime,timing.BUILD.endTime)"
```

**Expected Output**: `SUCCESS ...timestamps...`

### Step 2: Check Migration Job Logs

**Command**:
```bash
export CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"
/opt/homebrew/share/google-cloud-sdk/bin/gcloud logging read \
  'resource.type="cloud_run_job" AND
   labels."run.googleapis.com/job_name"=~"dev-prompt-migration-019a66fe.*"' \
  --limit=100 \
  --project=vividly-dev-rich \
  --format="table(timestamp,severity,textPayload)"
```

**Expected Key Log Lines**:
```
[Migration] Connecting to database...
  Host: 10.240.0.3
  Port: 5432
  Database: vividly
  User: vividly
[Migration] Connection successful!
[Migration] Executing migration: migrations/enterprise_prompt_system_phase1.sql
[Migration] Migration completed successfully
```

### Step 3: Run Database Verification Script

**Command**:
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
export DATABASE_URL=$(/opt/homebrew/share/google-cloud-sdk/bin/gcloud secrets versions access latest \
  --secret="database-url-dev" --project=vividly-dev-rich)
python verify_prompt_system_migration.py
```

**Expected Output**:
```
======================================================================
Enterprise Prompt System Migration - Verification Script
======================================================================

1. Verifying Tables
✓ Table 'prompt_templates' exists
✓ Table 'prompt_executions' exists
✓ Table 'prompt_guardrails' exists
✓ Table 'ab_test_experiments' exists
✓ Table 'schema_migrations' exists

2. Verifying Indexes
✓ Index 'idx_prompt_templates_active' exists
✓ Index 'idx_prompt_templates_ab_test' exists
✓ Index 'idx_prompt_templates_version' exists
... (13 more indexes)

3. Verifying Seed Data
✓ Seed prompt 'nlu_topic_extraction' found
✓ Seed prompt 'clarification_question_generation' found
✓ Seed prompt 'educational_script_generation' found
✓ Seed guardrail 'pii_detection_basic' found
✓ Seed guardrail 'toxic_content_filter' found
✓ Seed guardrail 'prompt_injection_detection' found

4. Verifying Analytics Views
✓ View 'v_template_performance' exists and is queryable
✓ View 'v_recent_execution_errors' exists and is queryable
✓ View 'v_guardrail_violations_summary' exists and is queryable
✓ View 'v_active_ab_tests' exists and is queryable

5. Verifying Triggers
✓ Trigger 'trigger_update_template_statistics' exists on table 'prompt_executions'
✓ Trigger 'trigger_update_ab_test_statistics' exists on table 'prompt_executions'
✓ Trigger 'trigger_enforce_single_active_template' exists on table 'prompt_templates'

6. Verifying Migration Record
✓ Migration record 'enterprise_prompt_system_phase1' found
   Description: Enterprise Prompt Template Management System - Phase 1
   Executed at: 2025-11-06 22:XX:XX

7. Testing Database Functionality
✓ Query active templates: 3 templates found
   - nlu_topic_extraction (v1, nlu)
   - clarification_question_generation (v1, content)
   - educational_script_generation (v1, content)
✓ Query active guardrails: 3 guardrails found
   - pii_detection_basic (critical, block)
   - toxic_content_filter (high, warn)
   - prompt_injection_detection (high, warn)
✓ Query v_template_performance view: 0 rows

======================================================================
VERIFICATION SUMMARY
======================================================================
Tables:           ✓ PASS
Indexes:          ✓ PASS
Seed Data:        ✓ PASS
Views:            ✓ PASS
Triggers:         ✓ PASS
Migration Record: ✓ PASS
Functionality:    ✓ PASS

======================================================================
✓ ALL VERIFICATION CHECKS PASSED
  Enterprise Prompt System Migration: SUCCESS
======================================================================
```

### Step 4: Run Backwards Compatibility Tests

**Command**:
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
export DATABASE_URL=$(/opt/homebrew/share/google-cloud-sdk/bin/gcloud secrets versions access latest \
  --secret="database-url-dev" --project=vividly-dev-rich)
DATABASE_URL=$DATABASE_URL \
  SECRET_KEY=test_secret_key_12345 \
  PYTHONPATH=/Users/richedwards/AI-Dev-Projects/Vividly/backend \
  /Users/richedwards/AI-Dev-Projects/Vividly/backend/venv_test/bin/python -m pytest \
  tests/test_prompt_backwards_compatibility.py -v
```

**Expected Test Results**:
```
tests/test_prompt_backwards_compatibility.py::TestHardcodedPromptsFallback::test_nlu_topic_extraction_hardcoded_exists PASSED
tests/test_prompt_backwards_compatibility.py::TestHardcodedPromptsFallback::test_clarification_question_hardcoded_exists PASSED
tests/test_prompt_backwards_compatibility.py::TestHardcodedPromptsFallback::test_script_generation_hardcoded_exists PASSED
tests/test_prompt_backwards_compatibility.py::TestDatabasePromptRetrieval::test_get_active_prompt_by_name PASSED
tests/test_prompt_backwards_compatibility.py::TestDatabasePromptRetrieval::test_get_latest_version PASSED
tests/test_prompt_backwards_compatibility.py::TestDatabasePromptRetrieval::test_prompt_has_required_metadata PASSED
... (23 more tests)

========================= 29 passed in 1.2s =========================
```

### Step 5: Database Schema Inspection

**Commands**:
```bash
# Connect to database and inspect prompt_templates table
export DATABASE_URL=$(/opt/homebrew/share/google-cloud-sdk/bin/gcloud secrets versions access latest \
  --secret="database-url-dev" --project=vividly-dev-rich)

# Use Python to query database
python3 <<EOF
import os
from urllib.parse import urlparse
import psycopg2

database_url = os.environ['DATABASE_URL']
parsed = urlparse(database_url)

conn = psycopg2.connect(
    host=parsed.hostname,
    port=parsed.port or 5432,
    database=parsed.path[1:],
    user=parsed.username,
    password=parsed.password
)

cur = conn.cursor()

# Check prompt_templates count
cur.execute("SELECT COUNT(*) FROM prompt_templates;")
print(f"Total prompts: {cur.fetchone()[0]}")

# Check active prompts
cur.execute("SELECT name, version, is_active FROM prompt_templates ORDER BY name;")
for row in cur.fetchall():
    print(f"  - {row[0]} (v{row[1]}) active={row[2]}")

# Check guardrails count
cur.execute("SELECT COUNT(*) FROM prompt_guardrails;")
print(f"Total guardrails: {cur.fetchone()[0]}")

# Check schema_migrations
cur.execute("SELECT version, executed_at FROM schema_migrations ORDER BY executed_at DESC LIMIT 1;")
row = cur.fetchone()
print(f"Latest migration: {row[0]} at {row[1]}")

conn.close()
EOF
```

---

## Troubleshooting Plan

### If Build #5 Fails

**Investigation Steps**:
1. Retrieve full build logs:
   ```bash
   export CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"
   /opt/homebrew/share/google-cloud-sdk/bin/gcloud builds log 019a66fe-1e49-4ecb-a079-9f90a427a58e \
     --project=vividly-dev-rich
   ```

2. Check Cloud Run job execution logs:
   ```bash
   /opt/homebrew/share/google-cloud-sdk/bin/gcloud run jobs executions list \
     --job=dev-prompt-migration-019a66fe-1e49-4ecb-a079-9f90a427a58e \
     --region=us-central1 \
     --project=vividly-dev-rich
   ```

3. Verify DATABASE_URL secret version is correct:
   ```bash
   /opt/homebrew/share/google-cloud-sdk/bin/gcloud secrets versions list \
     database-url-dev --project=vividly-dev-rich
   # Should show version 5 as "enabled"
   ```

4. Test database connectivity from local machine:
   ```bash
   export DATABASE_URL=$(/opt/homebrew/share/google-cloud-sdk/bin/gcloud secrets versions access latest \
     --secret="database-url-dev" --project=vividly-dev-rich)
   python3 -c "from urllib.parse import urlparse; import psycopg2; parsed = urlparse('$DATABASE_URL'); conn = psycopg2.connect(host=parsed.hostname, port=parsed.port or 5432, database=parsed.path[1:], user=parsed.username, password=parsed.password); print('Connection successful!')"
   ```

### Common Failure Scenarios

| Error | Probable Cause | Fix |
|-------|---------------|-----|
| "connection to server on socket..." | DATABASE_URL still using Unix socket format | Re-verify secret version 5 is enabled and being used |
| "could not connect to server" | VPC connector issue | Check connector status, verify it's attached to job |
| "permission denied for schema public" | Service account permissions | Grant `cloudsql.client` role to service account |
| "relation 'prompt_templates' does not exist" | Migration SQL didn't execute | Check migration file path, verify SQL syntax |

---

## Success Metrics

After Build #5 completes successfully, we will have achieved:

1. **Infrastructure**: ✅ All components working
   - VPC connector: `dev-cloud-run-connector`
   - Cloud SQL private IP: `10.240.0.3`
   - DATABASE_URL secret: version 5 (private IP format)
   - Docker image: built and pushed
   - Cloud Run Job: executed successfully

2. **Database Migration**: ✅ 689 lines of SQL executed
   - 5 tables created
   - 16 indexes created
   - 3 seed prompts inserted
   - 3 seed guardrails inserted
   - 4 analytics views created
   - 3 triggers installed
   - 1 migration record logged

3. **Testing**: ✅ All verification passed
   - Schema verification: ✓
   - Seed data verification: ✓
   - Backwards compatibility tests: ✓
   - Database functionality tests: ✓

4. **Documentation**: ✅ Comprehensive records
   - Root cause analysis documented
   - Fix implementation documented
   - Verification procedures documented
   - Troubleshooting guides created

---

## Next Steps After Verification

### Immediate (Today)
1. Document Build #5 success
2. Update `SESSION_11_PART_16_DATABASE_URL_FIX_AND_MIGRATION_RETRY.md` with final results
3. Create summary document: `SESSION_11_PROMPT_SYSTEM_SUCCESS.md`

### Short-term (Next Session)
1. Update backend code to use database-driven prompts
2. Create `PromptTemplateService` in `backend/app/services/`
3. Replace hardcoded prompts in:
   - `nlu_service.py`
   - `clarification_service.py`
   - `script_generation_service.py`
4. Add prompt execution logging

### Medium-term (Next 1-2 Sessions)
1. Deploy updated backend to dev environment
2. Run integration tests
3. Create first custom prompt via database
4. Test A/B testing functionality
5. Validate guardrail enforcement

### Long-term (Future)
1. Build admin UI for prompt management
2. Enable production guardrails (move from warning to blocking)
3. Set up analytics dashboards
4. Create prompt versioning workflow
5. Document prompt engineering best practices

---

## Build History Summary

| Build | ID | Status | Issue | Resolution |
|-------|----|---------| ------|-----------|
| #1 | 146dec83... | FAILURE | Missing docker push | Added Step #1 |
| #2 | f6476f98... | FAILURE | Missing docker push | Added Step #1 |
| #3 | 5d4e25cd... | FAILURE | VPC connector missing | Created connector |
| #4a | 4a26bed8... | FAILURE | Migration file not found | Fixed path: `migrations/...` |
| #4b | 0e4a8f4e... | FAILURE | Database connection (Unix socket) | Updated DATABASE_URL format |
| #5 | 019a66fe... | RUNNING | - | Expected to succeed |

---

## Lessons Learned Summary

### Technical Insights

1. **Connection String Format Matters**
   - Cloud SQL Proxy uses Unix socket format
   - VPC private IP requires TCP/IP format with explicit host/port
   - Python's `urlparse()` cannot parse Unix socket format correctly

2. **Infrastructure Dependencies**
   - VPC connector is required for Cloud Run to access Cloud SQL via private IP
   - Service account needs proper IAM roles
   - Secret Manager must contain correct format for connection method

3. **Testing is Critical**
   - Should have tested DATABASE_URL parsing locally before deployment
   - Need unit tests for connection string parsing
   - Backwards compatibility tests prevent breaking changes

### Process Improvements

1. **Build Right**
   - Verify connection string format matches infrastructure
   - Test configuration changes locally before deploying
   - Use reusable patterns (created script template for updating secrets)

2. **Test Everything**
   - Created comprehensive verification script (400+ lines)
   - Created backwards compatibility test suite (350+ lines)
   - Integrated tests into CI/CD pipeline

3. **Think About the Future**
   - Documented patterns for future use
   - Created reusable verification infrastructure
   - Built automated testing framework

---

**Status**: ⏳ Build #5 monitoring in progress
**Expected Resolution**: Build completion in ~5-10 minutes
**Next Action**: Wait for build completion, then run verification
**Session**: 11 Part 17 - Build #5 Monitoring & Post-Migration Plan
**Date**: 2025-11-06
