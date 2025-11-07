# Cloud Run Job Worker Deployment Plan

**Date:** 2025-11-01
**Task:** Deploy Content Worker as Cloud Run Job
**Status:** PLANNING COMPLETE - READY FOR EXECUTION

## Executive Summary

This document outlines the step-by-step deployment plan for the Content Worker Cloud Run Job in the dev environment. The worker processes async content generation requests from Pub/Sub and must have access to Cloud SQL via VPC.

## Prerequisites Verification

### Infrastructure Requirements ✅
- [x] GCP Project: `vividly-dev-rich`
- [x] Cloud SQL instance with private IP
- [x] Pub/Sub topic: `content-generation-requests`
- [x] Pub/Sub subscription: `content-generation-sub`
- [x] Dead Letter Queue: `content-generation-dlq`
- [x] VPC Connector for Cloud SQL access
- [x] Artifact Registry for Docker images
- [x] Service Account with appropriate permissions

### Code Requirements ✅
- [x] Dockerfile.content-worker exists
- [x] cloudbuild.content-worker.yaml exists
- [x] cloud_run_jobs.tf Terraform configuration exists
- [x] Worker application code (ready from previous tasks)

### Database Requirements
- [ ] Database migration for compound indexes run
- [ ] content_requests table exists
- [ ] Database connection string available

## Deployment Steps

### Phase 1: Pre-Deployment Checks

**Step 1.1: Verify Current Infrastructure State**
```bash
# Check existing Cloud Run Jobs
gcloud run jobs list --region=us-central1 --project=vividly-dev-rich

# Check Pub/Sub topics
gcloud pubsub topics list --project=vividly-dev-rich

# Check Pub/Sub subscriptions
gcloud pubsub subscriptions list --project=vividly-dev-rich

# Check VPC Connector
gcloud compute networks vpc-access connectors list --region=us-central1 --project=vividly-dev-rich

# Check Cloud SQL instances
gcloud sql instances list --project=vividly-dev-rich
```

**Step 1.2: Verify Database Schema**
```bash
# Connect to Cloud SQL and verify table exists
gcloud sql connect <instance-name> --user=postgres --database=vividly_dev

# Once connected:
\dt content_requests
\d content_requests
```

**Step 1.3: Check Docker Image Registry**
```bash
# List existing images
gcloud artifacts docker images list us-central1-docker.pkg.dev/vividly-dev-rich/vividly \
  --include-tags
```

### Phase 2: Build and Push Worker Image

**Step 2.1: Build Docker Image**
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

# Build image
docker build -t us-central1-docker.pkg.dev/vividly-dev-rich/vividly/content-worker:latest \
  -f Dockerfile.content-worker .
```

**Step 2.2: Authenticate Docker to Artifact Registry**
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
```

**Step 2.3: Push Image to Artifact Registry**
```bash
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/content-worker:latest
```

**Alternative: Use Cloud Build (Recommended)**
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

gcloud builds submit \
  --config=cloudbuild.content-worker.yaml \
  --project=vividly-dev-rich \
  --timeout=15m
```

### Phase 3: Run Database Migration

**Step 3.1: Apply Compound Indexes Migration**
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

# Get Cloud SQL connection details
export DB_INSTANCE=$(gcloud sql instances describe <instance-name> --format="value(name)")
export DB_CONNECTION_NAME=$(gcloud sql instances describe <instance-name> --format="value(connectionName)")

# Run migration via Cloud SQL Proxy or direct connection
psql "host=<host> dbname=vividly_dev user=postgres" \
  -f migrations/add_compound_indexes_content_requests.sql
```

### Phase 4: Deploy Cloud Run Job via Terraform

**Step 4.1: Navigate to Terraform Directory**
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/terraform
```

**Step 4.2: Initialize Terraform (if needed)**
```bash
terraform init
```

**Step 4.3: Review Terraform Plan**
```bash
terraform plan \
  -var-file=environments/dev.tfvars \
  -out=tfplan
```

**Step 4.4: Apply Terraform Configuration**
```bash
terraform apply tfplan
```

**Alternative: Target specific resource**
```bash
terraform apply \
  -var-file=environments/dev.tfvars \
  -target=google_cloud_run_v2_job.content_worker \
  -auto-approve
```

### Phase 5: Verify Deployment

**Step 5.1: Check Job Created Successfully**
```bash
gcloud run jobs describe dev-vividly-content-worker \
  --region=us-central1 \
  --project=vividly-dev-rich
```

**Step 5.2: Test Manual Job Execution**
```bash
# Execute job manually to test
gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 \
  --project=vividly-dev-rich
```

**Step 5.3: Monitor Job Execution**
```bash
# Get execution ID from previous command, then:
gcloud run jobs executions describe <execution-id> \
  --region=us-central1 \
  --project=vividly-dev-rich

# View logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=dev-vividly-content-worker" \
  --project=vividly-dev-rich \
  --limit=50 \
  --format=json
```

### Phase 6: Test Message Processing

**Step 6.1: Publish Test Message to Pub/Sub**
```bash
# Create test message
gcloud pubsub topics publish content-generation-requests \
  --project=vividly-dev-rich \
  --message='{"correlation_id": "test-001", "student_id": "test-student", "topic": "Python Basics", "grade_level": "9th Grade"}'
```

**Step 6.2: Verify Worker Processes Message**
```bash
# Check Cloud Run Job executions
gcloud run jobs executions list \
  --job=dev-vividly-content-worker \
  --region=us-central1 \
  --project=vividly-dev-rich

# Check logs for message processing
gcloud logging read "resource.type=cloud_run_job AND jsonPayload.correlation_id=test-001" \
  --project=vividly-dev-rich \
  --limit=50
```

**Step 6.3: Verify Database Record Created**
```bash
# Connect to database
psql "host=<host> dbname=vividly_dev user=postgres"

# Check content_requests table
SELECT id, correlation_id, status, created_at, retry_count
FROM content_requests
WHERE correlation_id = 'test-001';
```

## Rollback Plan

### If Deployment Fails

**Option 1: Destroy Job via Terraform**
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/terraform

terraform destroy \
  -var-file=environments/dev.tfvars \
  -target=google_cloud_run_v2_job.content_worker \
  -auto-approve
```

**Option 2: Delete Job via gcloud**
```bash
gcloud run jobs delete dev-vividly-content-worker \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --quiet
```

### If Migration Fails

**Rollback Database Migration**
```bash
# Run rollback commands from migration file
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_correlation_status;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_student_status_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_status_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_org_status_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_content_requests_failed_debugging;
```

## Environment Variables Required

The Cloud Run Job requires these environment variables (configured in Terraform):

```
DATABASE_URL=<Cloud SQL connection string>
GOOGLE_CLOUD_PROJECT=vividly-dev-rich
PUBSUB_SUBSCRIPTION=content-generation-sub
PUBSUB_TOPIC=content-generation-requests
SECRET_KEY=<from Secret Manager>
ALGORITHM=HS256
DEBUG=True
CORS_ORIGINS=http://localhost:3000
```

## Success Criteria

- [ ] Cloud Run Job created and visible in GCP Console
- [ ] Job executes successfully when triggered manually
- [ ] Worker pulls messages from Pub/Sub subscription
- [ ] Worker creates records in content_requests table
- [ ] Worker increments retry_count on failures
- [ ] Worker nacks messages to DLQ after max retries
- [ ] Worker logs appear in Cloud Logging
- [ ] Health check endpoint responds (if configured)
- [ ] No errors in Cloud Logging

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Job Execution Success Rate**
```bash
# Query metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/job/completed_execution_count"' \
  --project=vividly-dev-rich
```

2. **Pub/Sub Subscription Lag**
```bash
# Check subscription backlog
gcloud pubsub subscriptions describe content-generation-sub \
  --project=vividly-dev-rich \
  --format="value(messageRetentionDuration, numUndeliveredMessages)"
```

3. **Database Connection Pool**
- Monitor Cloud SQL connections
- Check for connection leaks

4. **Error Rate**
- Monitor DLQ message count
- Check Cloud Logging for errors

### Alert Policies (Already in Terraform)

- ✅ Pub/Sub subscription lag > 100 messages
- ✅ Pub/Sub old messages > 5 minutes
- ✅ Cloud Run Job failures
- ✅ Database connection errors

## Post-Deployment Tasks

1. **Update Documentation**
   - Document worker deployment process
   - Update runbook with troubleshooting steps
   - Document monitoring queries

2. **Create Operational Runbook**
   - How to scale worker (adjust concurrency)
   - How to view logs
   - How to trigger manual execution
   - How to check DLQ messages

3. **Set Up Continuous Deployment**
   - Update CI/CD pipeline to deploy worker
   - Add automated tests
   - Configure staging → production promotion

## Risk Assessment

### Low Risk ✅
- Worker is isolated (Cloud Run Job)
- Can be stopped/deleted without affecting API
- Database migration uses CONCURRENTLY (non-blocking)
- Rollback is straightforward

### Medium Risk ⚠️
- First deployment - may have configuration issues
- Database connection pooling settings may need tuning
- Pub/Sub message processing rate unknown

### Mitigation Strategies
- Deploy to dev environment first (current plan)
- Monitor closely for first 24 hours
- Have rollback plan ready
- Start with low message volume
- Gradually increase traffic

## Timeline

**Estimated Duration:** 2-3 hours

| Phase | Duration | Notes |
|-------|----------|-------|
| Pre-checks | 15 min | Verify infrastructure |
| Build & Push | 10 min | Build Docker image |
| DB Migration | 10 min | Apply indexes |
| Terraform Apply | 15 min | Deploy Cloud Run Job |
| Verification | 30 min | Test end-to-end |
| Monitoring Setup | 20 min | Configure dashboards |
| Documentation | 30 min | Update runbooks |

## Next Steps After Deployment

1. **Task 19:** Verify monitoring alerts fire correctly
2. **Task 20:** Update documentation with production deployment procedures
3. **Production Deployment:** Apply same process to staging → production

## Contact Information

**Deployment Lead:** Claude (AI Assistant)
**Project:** Vividly MVP
**Environment:** Dev (vividly-dev-rich)
**Date:** 2025-11-01

---

## Execution Checklist

Use this checklist during actual deployment:

### Pre-Deployment
- [ ] All background processes checked/cleared
- [ ] Current infrastructure state documented
- [ ] Database schema verified
- [ ] Terraform state is clean

### Deployment
- [ ] Docker image built successfully
- [ ] Docker image pushed to Artifact Registry
- [ ] Database migration applied
- [ ] Terraform plan reviewed
- [ ] Terraform apply completed
- [ ] Cloud Run Job created

### Verification
- [ ] Manual job execution succeeds
- [ ] Test message published to Pub/Sub
- [ ] Worker processes test message
- [ ] Database record created
- [ ] Logs show successful processing
- [ ] No errors in Cloud Logging

### Post-Deployment
- [ ] Monitoring dashboards configured
- [ ] Alert policies tested
- [ ] Documentation updated
- [ ] Team notified of deployment
- [ ] Runbook created/updated

---

**Status:** ✅ PLAN COMPLETE - READY FOR EXECUTION

This deployment plan has been carefully thought through following the "build it right, not fast" methodology requested by the user.
