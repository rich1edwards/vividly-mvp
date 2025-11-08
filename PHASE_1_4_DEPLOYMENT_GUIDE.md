# Phase 1.4: Real-Time Notifications - Deployment Guide

**Status**: Ready for Deployment
**Created**: 2025-11-08
**Last Updated**: 2025-11-08
**Prerequisites**: Terraform 1.5+, gcloud CLI, Node.js 18+, Python 3.9+

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Verification & Testing](#verification--testing)
7. [Monitoring & Observability](#monitoring--observability)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Phase 1.4 introduces real-time push notifications using Server-Sent Events (SSE) and Redis Pub/Sub for notifying students when their video content generation is complete.

### Architecture Components

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Student   │ ◄─SSE──►│  Cloud Run   │◄─Redis─►│Push Worker  │
│  Browser    │         │  API Server  │  Pub/Sub│  (Content)  │
└─────────────┘         └──────────────┘         └─────────────┘
                               │                        │
                               ▼                        ▼
                        ┌──────────────┐         ┌──────────────┐
                        │Cloud         │         │  Pub/Sub     │
                        │Memorystore   │         │  Topics      │
                        │(Redis)       │         │              │
                        └──────────────┘         └──────────────┘
```

### What's Being Deployed

1. **Infrastructure** (Terraform):
   - Cloud Memorystore (Redis) for Pub/Sub messaging
   - VPC Serverless Connector for Cloud Run → Redis access
   - VPC Network with firewall rules
   - Secret Manager entries for Redis connection details
   - Cloud Monitoring alerts and dashboard

2. **Backend** (Python/FastAPI):
   - NotificationService with Redis Pub/Sub integration
   - SSE streaming endpoint (`/api/v1/notifications/stream`)
   - Updated push_worker to publish notifications
   - Health check and monitoring endpoints

3. **Frontend** (React/TypeScript):
   - `useNotifications` hook for SSE connection management
   - `NotificationCenter` component in header
   - Toast notifications for completed videos
   - Notification history with localStorage persistence

---

## Pre-Deployment Checklist

### 1. Code Verification

- [x] All backend tests pass (28/28 notification tests)
- [x] Backend NotificationService has 80% code coverage
- [x] Frontend components implemented and integrated
- [ ] E2E tests pass (Playwright notifications.spec.ts)
- [ ] No TypeScript compilation errors
- [ ] No linting errors

```bash
# Run backend tests
cd backend
env DATABASE_URL="sqlite:///:memory:" SECRET_KEY="test" \
  pytest tests/test_notification_service.py -v

# Run frontend type check
cd frontend
npm run type-check

# Run frontend E2E tests
npm run test:e2e
```

### 2. Environment Variables

**Backend (.env)**:
```bash
# Required for Phase 1.4
REDIS_URL=redis://10.x.x.x:6379/0  # Set after Redis deployment
SSE_HEARTBEAT_INTERVAL=30
SSE_CONNECTION_TIMEOUT=300
SSE_MAX_BACKLOG_MESSAGES=100
```

**Frontend (.env.local)**:
```bash
VITE_API_URL=https://dev-vividly-api-rm2v4spyrq-uc.a.run.app
VITE_ENABLE_NOTIFICATIONS=true
```

### 3. Terraform State

```bash
# Verify Terraform state is backed up
cd terraform
terraform state list

# Backup current state before changes
terraform state pull > backups/state-before-phase-1.4.json
```

### 4. GCP Project Setup

```bash
# Verify correct project
gcloud config get-value project
# Should output: vividly-dev-rich

# Verify required APIs are enabled
gcloud services list --enabled | grep -E 'redis|vpcaccess|secretmanager'
```

---

## Infrastructure Deployment

### Step 1: Review Terraform Configuration

```bash
cd terraform

# Review redis.tf configuration
cat redis.tf | head -100

# Review variables
cat terraform/environments/dev.tfvars
```

### Step 2: Initialize Terraform

```bash
# Initialize with dev backend
terraform init -backend-config=backend-dev.hcl

# Verify provider versions
terraform version
```

### Step 3: Plan Infrastructure Changes

```bash
# Generate plan
terraform plan \
  -var-file=environments/dev.tfvars \
  -out=phase-1.4-plan.tfplan

# Review plan output carefully
# Expected new resources:
#  + google_redis_instance.notifications_redis
#  + google_vpc_access_connector.serverless_to_redis
#  + google_compute_network.redis_network
#  + google_compute_subnetwork.redis_subnet
#  + google_compute_firewall.allow_redis_from_serverless
#  + google_secret_manager_secret.redis_host
#  + google_secret_manager_secret.redis_port
#  + google_monitoring_alert_policy.redis_high_memory
#  + google_monitoring_dashboard.redis_dashboard
```

### Step 4: Apply Infrastructure

```bash
# Apply with approval
terraform apply phase-1.4-plan.tfplan

# Monitor progress
# Expected duration: 5-10 minutes
```

### Step 5: Retrieve Redis Connection Details

```bash
# Get Redis host IP
gcloud redis instances describe dev-vividly-notifications-redis \
  --region=us-central1 \
  --format="value(host)"

# Example output: 10.10.0.3

# Get Redis port (should be 6379)
gcloud redis instances describe dev-vividly-notifications-redis \
  --region=us-central1 \
  --format="value(port)"

# Verify Redis is READY
gcloud redis instances describe dev-vividly-notifications-redis \
  --region=us-central1 \
  --format="value(state)"
```

### Step 6: Update Secret Manager

```bash
# Store Redis connection details
REDIS_HOST=$(gcloud redis instances describe dev-vividly-notifications-redis \
  --region=us-central1 --format="value(host)")

echo -n "$REDIS_HOST" | gcloud secrets versions add redis-host \
  --data-file=- \
  --project=vividly-dev-rich

echo -n "6379" | gcloud secrets versions add redis-port \
  --data-file=- \
  --project=vividly-dev-rich
```

---

## Backend Deployment

### Step 1: Update Backend Environment Variables

```bash
cd backend

# Update .env with Redis connection
echo "REDIS_URL=redis://${REDIS_HOST}:6379/0" >> .env
echo "SSE_HEARTBEAT_INTERVAL=30" >> .env
echo "SSE_CONNECTION_TIMEOUT=300" >> .env
```

### Step 2: Run Backend Tests

```bash
# Run full test suite
DATABASE_URL="sqlite:///:memory:" SECRET_KEY="test" \
  pytest tests/ -v --cov=app --cov-report=html

# Verify notification tests pass
DATABASE_URL="sqlite:///:memory:" SECRET_KEY="test" \
  pytest tests/test_notification_service.py \
  tests/integration/test_sse_notifications.py \
  tests/unit/test_push_worker_notifications.py \
  -v
```

### Step 3: Build Docker Image

```bash
# Build API server image
docker build -t us-central1-docker.pkg.dev/vividly-dev-rich/vividly/dev-api:phase-1.4 \
  -f Dockerfile.api .

# Build push worker image
docker build -t us-central1-docker.pkg.dev/vividly-dev-rich/vividly/dev-worker:phase-1.4 \
  -f Dockerfile.worker .
```

### Step 4: Push to Artifact Registry

```bash
# Authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push images
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/dev-api:phase-1.4
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/dev-worker:phase-1.4
```

### Step 5: Deploy API Server with VPC Connector

```bash
# Get VPC connector name
VPC_CONNECTOR=$(gcloud compute networks vpc-access connectors list \
  --region=us-central1 --format="value(name)" | grep redis)

# Deploy API server
gcloud run deploy dev-vividly-api \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/dev-api:phase-1.4 \
  --platform=managed \
  --region=us-central1 \
  --vpc-connector=$VPC_CONNECTOR \
  --vpc-egress=private-ranges-only \
  --set-env-vars="REDIS_URL=redis://${REDIS_HOST}:6379/0,SSE_HEARTBEAT_INTERVAL=30,SSE_CONNECTION_TIMEOUT=300" \
  --set-secrets="SECRET_KEY=vividly-secret-key:latest,DATABASE_URL=database-url:latest" \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=2 \
  --concurrency=80 \
  --max-instances=10 \
  --min-instances=1 \
  --timeout=300s

# Note: timeout increased to 300s for long-lived SSE connections
```

### Step 6: Deploy Push Worker with Redis Access

```bash
# Deploy push worker (Cloud Run Service for Pub/Sub push)
gcloud run deploy dev-vividly-content-worker \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/dev-worker:phase-1.4 \
  --platform=managed \
  --region=us-central1 \
  --vpc-connector=$VPC_CONNECTOR \
  --vpc-egress=private-ranges-only \
  --set-env-vars="REDIS_URL=redis://${REDIS_HOST}:6379/0" \
  --set-secrets="SECRET_KEY=vividly-secret-key:latest,DATABASE_URL=database-url:latest" \
  --no-allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --concurrency=1 \
  --max-instances=10 \
  --timeout=900s
```

### Step 7: Verify Backend Health

```bash
# Check API health
curl https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/health

# Check notification service health
curl https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/api/v1/notifications/health

# Expected response:
# {
#   "status": "healthy",
#   "redis_connected": true,
#   "active_connections": 0,
#   "service_metrics": {
#     "notifications_published": 0,
#     "notifications_delivered": 0,
#     "connections_established": 0,
#     "connections_closed": 0,
#     "publish_errors": 0,
#     "subscribe_errors": 0
#   }
# }
```

---

## Frontend Deployment

### Step 1: Update Frontend Environment

```bash
cd frontend

# Update .env.production
cat > .env.production <<EOF
VITE_API_URL=https://dev-vividly-api-rm2v4spyrq-uc.a.run.app
VITE_ENABLE_NOTIFICATIONS=true
EOF
```

### Step 2: Build Frontend

```bash
# Install dependencies
npm install

# Type check
npm run type-check

# Build production bundle
npm run build

# Verify build output
ls -lh dist/
```

### Step 3: Deploy to Cloud Storage + CDN

```bash
# Upload to GCS bucket
gsutil -m rsync -r -d dist/ gs://vividly-dev-rich-dev-frontend

# Set cache headers
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" \
  gs://vividly-dev-rich-dev-frontend/**/*.js

gsutil -m setmeta -h "Cache-Control:public, max-age=3600" \
  gs://vividly-dev-rich-dev-frontend/**/*.css

# Set index.html with no-cache
gsutil setmeta -h "Cache-Control:no-cache, no-store, must-revalidate" \
  gs://vividly-dev-rich-dev-frontend/index.html
```

### Step 4: Invalidate CDN Cache (if using Cloud CDN)

```bash
# If using Cloud CDN
gcloud compute url-maps invalidate-cdn-cache vividly-dev-lb \
  --path="/*" \
  --async
```

---

## Verification & Testing

### 1. Manual SSE Connection Test

```bash
# Get access token (login as test student)
TOKEN=$(curl -X POST https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@vividly-test.com","password":"Test123!Student"}' \
  | jq -r .access_token)

# Connect to SSE endpoint (should stream events)
curl -N -H "Authorization: Bearer $TOKEN" \
  https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/api/v1/notifications/stream

# Expected output:
# event: connection.established
# data: {"connection_id":"conn_abc123","message":"Connected to notification service","timestamp":"2025-11-08T10:30:00Z"}
#
# event: heartbeat
# data: {"timestamp":"2025-11-08T10:30:30Z"}
#
# ... (heartbeats every 30 seconds)
```

### 2. End-to-End Content Request Flow

```bash
# 1. Login to frontend as student@vividly-test.com
# 2. Navigate to /student/request
# 3. Open browser DevTools → Network tab
# 4. Filter for "stream" to see SSE connection
# 5. Fill out content request form
# 6. Submit request
# 7. Observe notifications in NotificationCenter
# 8. Verify toast appears when generation completes
```

### 3. Run E2E Tests

```bash
cd frontend

# Run Playwright tests
npm run test:e2e -- tests/e2e/notifications.spec.ts

# Expected: All 10+ tests pass
```

### 4. Load Testing

```bash
# Install Locust
pip install locust

# Run load test (from .github/workflows test config)
locust -f tests/load/notification_load_test.py \
  --host=https://dev-vividly-api-rm2v4spyrq-uc.a.run.app \
  --users=50 \
  --spawn-rate=10 \
  --run-time=2m \
  --headless

# Expected: <50ms notification delivery latency
```

---

## Monitoring & Observability

### 1. Cloud Monitoring Dashboard

Access: https://console.cloud.google.com/monitoring/dashboards

Dashboard Name: `Phase 1.4 - Redis Notification System`

**Key Metrics**:
- Redis memory usage (%)
- Connected clients
- Commands processed (rate)
- Network traffic (bytes/sec)
- SSE active connections (custom metric)
- Notification delivery latency (custom metric)

### 2. Alerts

**Configured Alerts**:

1. **Redis High Memory Usage**
   - Condition: Memory usage > 80% for 5 minutes
   - Notification Channel: Email to ops team

2. **Redis High Connection Count**
   - Condition: Connections > 90% of max for 5 minutes
   - Notification Channel: Email to ops team

3. **SSE Connection Failures** (to be added)
   - Condition: Connection error rate > 5% for 2 minutes
   - Notification Channel: PagerDuty

### 3. Logging

**Cloud Logging Filters**:

```
# View SSE connections
resource.type="cloud_run_revision"
resource.labels.service_name="dev-vividly-api"
jsonPayload.message=~"SSE connection"

# View notification publishes
resource.type="cloud_run_revision"
resource.labels.service_name="dev-vividly-content-worker"
jsonPayload.message=~"Published notification"

# View errors
resource.type="cloud_run_revision"
severity>=ERROR
jsonPayload.message=~"notification|SSE|Redis"
```

### 4. Performance Monitoring

**Target SLIs**:
- SSE connection establishment: < 200ms (p95)
- Notification publish latency: < 10ms (p95)
- Notification delivery latency: < 50ms (p95)
- Redis memory usage: < 70% (avg)
- Redis connection utilization: < 70% (avg)

**Monitoring Commands**:

```bash
# Check active SSE connections (admin endpoint)
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/api/v1/notifications/connections

# Check notification service metrics
curl https://dev-vividly-api-rm2v4spyrq-uc.a.run.app/api/v1/notifications/health
```

---

## Rollback Procedures

### Emergency Rollback (if critical issues)

```bash
# 1. Rollback API server to previous revision
gcloud run services update-traffic dev-vividly-api \
  --to-revisions=REVISION_BEFORE_PHASE_1_4=100 \
  --region=us-central1

# 2. Rollback push worker
gcloud run services update-traffic dev-vividly-content-worker \
  --to-revisions=REVISION_BEFORE_PHASE_1_4=100 \
  --region=us-central1

# 3. Rollback frontend
gsutil -m rsync -r -d dist-previous/ gs://vividly-dev-rich-dev-frontend

# 4. Destroy Redis infrastructure (optional, saves costs)
cd terraform
terraform destroy \
  -target=google_redis_instance.notifications_redis \
  -var-file=environments/dev.tfvars
```

### Partial Rollback (disable notifications only)

```bash
# Disable SSE endpoint without full rollback
# Set environment variable to disable notifications
gcloud run services update dev-vividly-api \
  --set-env-vars="ENABLE_NOTIFICATIONS=false" \
  --region=us-central1

# Frontend will gracefully handle unavailable SSE endpoint
```

---

## Troubleshooting

### Issue: SSE Connection Fails with 503

**Symptoms**: `/api/v1/notifications/stream` returns 503 Service Unavailable

**Diagnosis**:
```bash
# Check Redis connectivity from Cloud Run
gcloud run services describe dev-vividly-api \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Verify VPC connector is attached
gcloud run services describe dev-vividly-api \
  --region=us-central1 \
  --format="value(spec.template.spec.vpcAccess.connector)"

# Test Redis from Cloud Run (requires debugging container)
gcloud run services update dev-vividly-api --command=redis-cli --args="-h,$REDIS_HOST,PING"
```

**Resolution**:
1. Verify VPC connector is attached to Cloud Run service
2. Verify Redis firewall rules allow traffic from serverless connector subnet
3. Check Redis instance is in READY state
4. Verify REDIS_URL environment variable is correct

### Issue: Notifications Not Delivered

**Symptoms**: SSE connection established but no notifications received

**Diagnosis**:
```bash
# Check push worker logs for notification publishes
gcloud logging read "resource.type=cloud_run_revision \
  resource.labels.service_name=dev-vividly-content-worker \
  jsonPayload.message=~'Published notification'" \
  --limit=20 \
  --format=json

# Check if Redis Pub/Sub channels have subscribers
# (requires Redis CLI access)
redis-cli -h $REDIS_HOST PUBSUB NUMSUB notifications:channel:USER_ID
```

**Resolution**:
1. Verify push_worker is publishing notifications after content generation
2. Check Redis Pub/Sub channel names match (notifications:channel:{user_id})
3. Verify SSE generator loop is running and listening for messages
4. Check for errors in API server logs

### Issue: High Memory Usage on Redis

**Symptoms**: Redis memory usage alert triggered

**Diagnosis**:
```bash
# Check Redis memory usage
gcloud redis instances describe dev-vividly-notifications-redis \
  --region=us-central1 \
  --format="value(currentLocationId,memorySizeGb,persistenceIamIdentity)"

# Check active connections
# (requires Redis CLI access)
redis-cli -h $REDIS_HOST INFO clients
redis-cli -h $REDIS_HOST CLIENT LIST
```

**Resolution**:
1. Review connection tracking logic in NotificationService
2. Implement stale connection cleanup (already in code)
3. Adjust maxmemory-policy in Redis config
4. Scale up Redis instance size if needed

### Issue: Frontend NotificationCenter Not Appearing

**Symptoms**: Bell icon missing from header

**Diagnosis**:
```bash
# Check frontend build includes NotificationCenter
grep -r "NotificationCenter" dist/assets/*.js

# Check DashboardLayout imports NotificationCenter
grep "NotificationCenter" frontend/src/components/DashboardLayout.tsx
```

**Resolution**:
1. Verify `NotificationCenter` is imported in `DashboardLayout.tsx`
2. Check browser console for JavaScript errors
3. Verify `useNotifications` hook is initializing correctly
4. Check VITE_API_URL is set correctly in frontend environment

---

## Post-Deployment Validation Checklist

- [ ] Infrastructure deployed successfully (Terraform apply)
- [ ] Redis instance in READY state
- [ ] VPC Serverless Connector READY
- [ ] Secret Manager secrets created
- [ ] Backend API server deployed with VPC connector
- [ ] Push worker deployed with Redis access
- [ ] Frontend deployed with NotificationCenter
- [ ] Health checks passing (/health, /api/v1/notifications/health)
- [ ] Manual SSE connection test successful
- [ ] Test user can receive notifications end-to-end
- [ ] E2E tests passing
- [ ] Cloud Monitoring dashboard accessible
- [ ] Alerts configured and active
- [ ] Logging filters created
- [ ] Documentation updated (this guide)
- [ ] Team notified of deployment

---

## Success Criteria

Phase 1.4 deployment is considered successful when:

1. ✅ **Infrastructure**: Redis, VPC connector, monitoring all operational
2. ✅ **Backend**: All 28 notification tests pass, health check shows `redis_connected: true`
3. ✅ **Frontend**: NotificationCenter visible in header, SSE connection establishes
4. ✅ **End-to-End**: Submit content request → receive progress notifications → completion toast
5. ✅ **Performance**: <10ms publish latency, <50ms delivery latency, <200ms connection time
6. ✅ **Reliability**: System handles 50+ concurrent SSE connections without errors
7. ✅ **Monitoring**: Dashboard shows real-time metrics, alerts trigger correctly

---

## Next Steps (Post-Deployment)

1. **Monitor for 24 hours**: Watch for errors, performance degradation, memory leaks
2. **Gather user feedback**: Test with real students and teachers
3. **Optimize as needed**: Tune Redis config, adjust heartbeat intervals
4. **Document runbooks**: Create operational guides for support team
5. **Plan Phase 2 enhancements**:
   - Notification history persistence in database
   - Browser push notifications (service worker)
   - Email digest of notifications
   - Notification preferences UI

---

**Deployment Guide Version**: 1.0
**Last Updated**: 2025-11-08
**Maintained By**: Vividly Engineering Team
