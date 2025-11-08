# Vividly Deployment Guide

**Last Updated**: 2025-01-08
**Status**: Production-Ready Infrastructure
**Environments**: Dev (Ready), Staging (Configured), Production (Configured)

---

## Table of Contents

1. [Overview](#overview)
2. [Infrastructure Architecture](#infrastructure-architecture)
3. [Prerequisites](#prerequisites)
4. [Environment Setup](#environment-setup)
5. [Development Environment Deployment](#development-environment-deployment)
6. [Staging Environment Deployment](#staging-environment-deployment)
7. [Production Environment Deployment](#production-environment-deployment)
8. [Frontend Deployment](#frontend-deployment)
9. [Monitoring and Alerts](#monitoring-and-alerts)
10. [Rollback Procedures](#rollback-procedures)
11. [Troubleshooting](#troubleshooting)

---

## Overview

Vividly uses a multi-tier cloud infrastructure on Google Cloud Platform (GCP) with:

- **Infrastructure as Code**: Terraform manages all cloud resources
- **CI/CD**: GitHub Actions automates testing and deployment
- **Multi-Environment**: Dev, Staging, and Production environments
- **Microservices**: Backend API (Cloud Run), Workers (Cloud Run Jobs), Frontend (GCS + CDN)
- **Real-Time Features**: Redis Pub/Sub for notifications via Server-Sent Events (SSE)
- **AI/ML**: Vertex AI Matching Engine for content recommendations
- **Database**: Cloud SQL (PostgreSQL)
- **Monitoring**: Cloud Monitoring with automated alerts

---

## Infrastructure Architecture

### Backend Services
- **Cloud Run (API)**: FastAPI backend with auto-scaling
- **Cloud Run Jobs (Workers)**: Content generation, matching, processing
- **Cloud SQL**: PostgreSQL database (HA in production)
- **Redis/Memorystore**: Real-time notifications (SSE) and caching
- **Pub/Sub**: Asynchronous job queuing
- **Vertex AI Matching Engine**: Content similarity matching

### Frontend
- **Google Cloud Storage (GCS)**: Static React app hosting
- **Cloud CDN**: Global content delivery network
- **Load Balancer**: HTTPS termination and routing
- **Managed SSL Certificates**: Automatic SSL for custom domains

### Networking
- **VPC**: Private network for all services
- **VPC Connector**: Serverless-to-VPC bridge for Redis access
- **Cloud NAT**: Outbound internet access for private services

---

## Prerequisites

### Required Tools

1. **Google Cloud SDK** (gcloud)
   ```bash
   # Install via Homebrew (macOS)
   brew install google-cloud-sdk

   # Or download from https://cloud.google.com/sdk/docs/install
   ```

2. **Terraform** (>= 1.0)
   ```bash
   brew install terraform
   ```

3. **Node.js** (>= 18)
   ```bash
   brew install node@18
   ```

4. **Docker**
   ```bash
   brew install --cask docker
   ```

5. **GitHub CLI** (optional, for PR workflows)
   ```bash
   brew install gh
   ```

### GCP Access

1. **GCP Projects**: Create projects for each environment
   - Dev: `vividly-dev-rich` (already exists)
   - Staging: `vividly-staging` (TODO: create)
   - Production: `vividly-prod` (TODO: create)

2. **Billing Account**: Link all projects to a billing account

3. **IAM Permissions**: Ensure you have the following roles:
   - `roles/owner` or `roles/editor`
   - `roles/iam.serviceAccountAdmin`
   - `roles/resourcemanager.projectIamAdmin`

4. **Authenticate**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

### GitHub Secrets

Add the following secrets to your GitHub repository:

**Development**:
- `GCP_SA_KEY_DEV`: Service account JSON key for dev environment

**Staging**:
- `GCP_SA_KEY_STAGING`: Service account JSON key for staging

**Production**:
- `GCP_SA_KEY_PROD`: Service account JSON key for production

**Backend Environment Variables** (for each environment):
- `DATABASE_URL`: Cloud SQL connection string
- `SECRET_KEY`: JWT secret key
- `REDIS_URL`: Redis connection string
- `GEMINI_API_KEY`: Google AI API key
- `CORS_ORIGINS`: Comma-separated allowed origins

---

## Environment Setup

### 1. Create GCP Projects (Staging & Production)

```bash
# Set billing account ID (find yours with: gcloud billing accounts list)
BILLING_ACCOUNT_ID="YOUR_BILLING_ACCOUNT_ID"

# Create staging project
gcloud projects create vividly-staging \
  --name="Vividly Staging" \
  --organization=YOUR_ORG_ID  # Optional: add --organization if using GCP org

gcloud billing projects link vividly-staging \
  --billing-account=$BILLING_ACCOUNT_ID

# Create production project
gcloud projects create vividly-prod \
  --name="Vividly Production" \
  --organization=YOUR_ORG_ID

gcloud billing projects link vividly-prod \
  --billing-account=$BILLING_ACCOUNT_ID
```

### 2. Enable Required APIs

```bash
# For each project (dev/staging/prod)
for PROJECT in vividly-dev-rich vividly-staging vividly-prod; do
  gcloud config set project $PROJECT

  gcloud services enable \
    compute.googleapis.com \
    cloudrun.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    pubsub.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com \
    servicenetworking.googleapis.com \
    cloudmonitoring.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com
done
```

### 3. Create Service Accounts

```bash
# Development service account
gcloud iam service-accounts create dev-cloud-run-sa \
  --display-name="Development Cloud Run Service Account" \
  --project=vividly-dev-rich

# Grant necessary roles
gcloud projects add-iam-policy-binding vividly-dev-rich \
  --member="serviceAccount:dev-cloud-run-sa@vividly-dev-rich.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding vividly-dev-rich \
  --member="serviceAccount:dev-cloud-run-sa@vividly-dev-rich.iam.gserviceaccount.com" \
  --role="roles/redis.editor"

# Repeat for staging and prod...
```

### 4. Create Service Account Keys (for GitHub Actions)

```bash
# Development
gcloud iam service-accounts keys create dev-sa-key.json \
  --iam-account=dev-cloud-run-sa@vividly-dev-rich.iam.gserviceaccount.com \
  --project=vividly-dev-rich

# Add to GitHub secrets as GCP_SA_KEY_DEV
cat dev-sa-key.json | base64
```

---

## Development Environment Deployment

### Step 1: Configure Terraform Variables

The dev environment is already configured in `terraform/environments/dev.tfvars`. Review and update if needed:

```bash
cat terraform/environments/dev.tfvars
```

### Step 2: Initialize Terraform

```bash
cd terraform

# Initialize Terraform (downloads providers)
terraform init

# Validate configuration
terraform validate
```

### Step 3: Plan Infrastructure

```bash
# Create execution plan
terraform plan -var-file=environments/dev.tfvars -out=dev.tfplan

# Review the plan carefully
```

### Step 4: Apply Infrastructure

```bash
# Apply the plan
terraform apply dev.tfplan

# This will create:
# - VPC network and subnets
# - Cloud SQL instance (PostgreSQL)
# - Redis/Memorystore instance
# - VPC Connector for serverless
# - Pub/Sub topics and subscriptions
# - Artifact Registry repository
# - Cloud Run services (placeholder)
# - Monitoring alerts
# - GCS bucket for frontend
```

**Expected Duration**: 15-20 minutes (Cloud SQL takes longest)

### Step 5: Import Existing Resources (if needed)

If you already have resources created manually, import them:

```bash
# Example: Import existing Artifact Registry
terraform import \
  -var-file=environments/dev.tfvars \
  google_artifact_registry_repository.vividly \
  projects/vividly-dev-rich/locations/us-central1/repositories/vividly
```

### Step 6: Run Database Migrations

```bash
# Connect to Cloud SQL and run migrations
./scripts/run_migrations_auto.sh dev
```

### Step 7: Deploy Backend

```bash
# Trigger GitHub Actions deployment
git push origin main

# Or manually trigger:
gh workflow run deploy-dev.yml
```

### Step 8: Deploy Frontend

```bash
# Trigger frontend deployment
gh workflow run deploy-frontend.yml -f environment=dev
```

### Step 9: Verify Deployment

```bash
# Check backend health
curl https://dev-vividly-api-2ufowb4fxa-uc.a.run.app/api/v1/health

# Check notification system
curl https://dev-vividly-api-2ufowb4fxa-uc.a.run.app/api/v1/notifications/health

# Check frontend (GCS)
curl -I https://storage.googleapis.com/vividly-dev-rich-frontend-dev/index.html
```

---

## Staging Environment Deployment

### Step 1: Update Configuration

```bash
# Review and update staging configuration
vim terraform/environments/staging.tfvars

# Update:
# - project_id (if different)
# - domain (staging.vividly.mnps.edu)
# - notification_channels (after creating them in GCP)
```

### Step 2: Set Staging Project

```bash
gcloud config set project vividly-staging
```

### Step 3: Deploy Infrastructure

```bash
cd terraform

# Plan
terraform plan -var-file=environments/staging.tfvars -out=staging.tfplan

# Apply
terraform apply staging.tfplan
```

### Step 4: Configure DNS

After Terraform creates the frontend infrastructure, configure DNS:

```bash
# Get the external IP from Terraform output
terraform output -var-file=environments/staging.tfvars frontend_external_ip

# Add A record to your DNS:
# staging.vividly.mnps.edu -> <EXTERNAL_IP>
```

Wait for DNS propagation (5-60 minutes).

### Step 5: Deploy Backend

```bash
# Trigger staging deployment (requires approval)
gh workflow run deploy-staging.yml
```

### Step 6: Deploy Frontend

```bash
gh workflow run deploy-frontend.yml -f environment=staging
```

### Step 7: Verify

```bash
# Check backend
curl https://api-staging.vividly.mnps.edu/api/v1/health

# Check frontend
curl -I https://staging.vividly.mnps.edu
```

---

## Production Environment Deployment

### Prerequisites

- [ ] All tests passing in CI/CD
- [ ] Staging deployment verified
- [ ] Load testing completed
- [ ] Security audit completed
- [ ] Backup strategy documented
- [ ] Incident response plan ready
- [ ] Monitoring alerts configured
- [ ] DNS records prepared

### Step 1: Update Configuration

```bash
vim terraform/environments/prod.tfvars

# Update:
# - project_id
# - domain (vividly.mnps.edu)
# - notification_channels (Slack, PagerDuty, email)
# - alert thresholds
```

### Step 2: Deploy Infrastructure

```bash
gcloud config set project vividly-prod

cd terraform

# Plan
terraform plan -var-file=environments/prod.tfvars -out=prod.tfplan

# Review carefully! Production deployment!
less prod.tfplan

# Apply
terraform apply prod.tfplan
```

**Expected Duration**: 20-30 minutes (HA Cloud SQL + Redis STANDARD_HA)

### Step 3: Configure DNS

```bash
# Get frontend external IP
terraform output -var-file=environments/prod.tfvars frontend_external_ip

# Add DNS records:
# vividly.mnps.edu -> <EXTERNAL_IP>
# www.vividly.mnps.edu -> <EXTERNAL_IP>
```

### Step 4: Create Cloud Monitoring Notification Channels

```bash
# Email notification
gcloud alpha monitoring channels create \
  --display-name="Production Alerts - Email" \
  --type=email \
  --channel-labels=email_address=ops@vividly.mnps.edu \
  --project=vividly-prod

# Slack notification (requires Slack webhook)
gcloud alpha monitoring channels create \
  --display-name="Production Alerts - Slack" \
  --type=slack \
  --channel-labels=url=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  --project=vividly-prod

# Update prod.tfvars with notification channel IDs
```

### Step 5: Deploy Backend (with Approval)

```bash
# Trigger production deployment (REQUIRES MANUAL APPROVAL)
gh workflow run deploy-production.yml

# GitHub will pause for manual approval in the "prod" environment
# Approve in GitHub Actions UI
```

### Step 6: Deploy Frontend

```bash
gh workflow run deploy-frontend.yml -f environment=prod

# This requires manual approval in GitHub
```

### Step 7: Smoke Tests

```bash
# Backend health
curl https://api.vividly.mnps.edu/api/v1/health

# Notification system
curl https://api.vividly.mnps.edu/api/v1/notifications/health

# Frontend
curl -I https://vividly.mnps.edu

# Test login
curl -X POST https://api.vividly.mnps.edu/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### Step 8: Monitor Deployment

```bash
# Watch Cloud Run logs
gcloud run services logs tail prod-vividly-api \
  --project=vividly-prod \
  --region=us-central1

# Check monitoring dashboard
gcloud monitoring dashboards list --project=vividly-prod
```

---

## Frontend Deployment

### Automatic Deployment (Dev)

Frontend automatically deploys to dev on push to `main`:

```bash
git push origin main
# GitHub Actions will build and deploy to GCS
```

### Manual Deployment (Staging/Prod)

```bash
# Staging
gh workflow run deploy-frontend.yml -f environment=staging

# Production (requires approval)
gh workflow run deploy-frontend.yml -f environment=prod
```

### Local Build and Deploy

```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Deploy to dev manually
gsutil -m rsync -r -d dist/ gs://vividly-dev-rich-frontend-dev/

# Set cache headers
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" \
  'gs://vividly-dev-rich-frontend-dev/assets/**'

gsutil -m setmeta -h "Cache-Control:public, max-age=0, must-revalidate" \
  'gs://vividly-dev-rich-frontend-dev/index.html'
```

### Invalidate CDN Cache

```bash
# After deploying to staging/prod
gcloud compute url-maps invalidate-cdn-cache \
  prod-vividly-frontend-urlmap \
  --path "/*" \
  --project=vividly-prod
```

---

## Monitoring and Alerts

### Cloud Monitoring Dashboards

Access dashboards in GCP Console:

```
https://console.cloud.google.com/monitoring/dashboards?project=vividly-prod
```

**Key Metrics**:
- Cloud Run: Request count, latency, error rate, CPU/memory usage
- Cloud SQL: Connections, query time, disk usage
- Redis: Memory usage, connections, hit rate, pub/sub throughput
- Load Balancer: Request rate, SSL cert expiry

### Health Check Endpoints

```bash
# Backend health
curl https://api.vividly.mnps.edu/api/v1/health

# Notification system health
curl https://api.vividly.mnps.edu/api/v1/notifications/health

# Response:
{
  "status": "healthy",
  "redis": {"connected": true, "latency_ms": 1.2},
  "database": {"connected": true},
  "metrics": {
    "published": 1250,
    "delivered": 1248,
    "failed": 2
  },
  "active_connections": 42
}
```

### Automated Health Checks

GitHub Actions runs health checks every 30 minutes (Mon-Fri 8am-8pm UTC):

- Backend API health
- SSE connection tests
- Redis connection tests
- Error rate monitoring

See `.github/workflows/notification-health-check.yml`

### Alert Policies

Configured alerts (Terraform `redis.tf`):

1. **Redis High Memory Usage** (>80%)
2. **Redis High Connection Count** (>80% of max)
3. **High Error Rate** (>5% of requests)
4. **Cloud Run High CPU** (>80%)
5. **Cloud SQL Disk Full** (>90%)

Alerts send to notification channels configured in `*.tfvars`.

---

## Rollback Procedures

### Backend Rollback

```bash
# List recent revisions
gcloud run revisions list \
  --service=prod-vividly-api \
  --region=us-central1 \
  --project=vividly-prod

# Rollback to previous revision
gcloud run services update-traffic prod-vividly-api \
  --to-revisions=prod-vividly-api-00042-abc=100 \
  --region=us-central1 \
  --project=vividly-prod
```

### Frontend Rollback

```bash
# List frontend backups
gsutil ls gs://vividly-prod-frontend-prod-backups/

# Restore from backup
BACKUP_TIMESTAMP="20250108-143000"
gsutil -m rsync -r -d \
  gs://vividly-prod-frontend-prod-backups/$BACKUP_TIMESTAMP/ \
  gs://vividly-prod-frontend-prod/

# Invalidate CDN cache
gcloud compute url-maps invalidate-cdn-cache \
  prod-vividly-frontend-urlmap \
  --path "/*" \
  --project=vividly-prod
```

### Database Rollback

```bash
# Cloud SQL automatic backups (retained for 7 days)
gcloud sql backups list \
  --instance=vividly-prod-db \
  --project=vividly-prod

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=vividly-prod-db \
  --backup-project=vividly-prod
```

**WARNING**: Database rollback will cause data loss. Only use in emergencies.

### Terraform Rollback

```bash
# Revert to previous Terraform state
cd terraform

# List state versions (if using remote state)
gsutil ls gs://vividly-prod-terraform-state/

# Restore previous state
gsutil cp \
  gs://vividly-prod-terraform-state/default.tfstate.backup \
  gs://vividly-prod-terraform-state/default.tfstate

# Apply previous configuration
terraform apply -var-file=environments/prod.tfvars
```

---

## Troubleshooting

### Common Issues

#### 1. Terraform Apply Fails: "VPC Connector quota exceeded"

**Problem**: Serverless VPC connector quota reached (default: 1 per region)

**Solution**:
```bash
# Request quota increase
gcloud compute project-info describe --project=vividly-prod | grep -A5 "vpc-access"

# Or delete unused connectors
gcloud compute networks vpc-access connectors list --region=us-central1
gcloud compute networks vpc-access connectors delete OLD_CONNECTOR --region=us-central1
```

#### 2. Cloud Run Can't Connect to Redis

**Problem**: VPC connector not attached or misconfigured

**Solution**:
```bash
# Verify VPC connector
gcloud compute networks vpc-access connectors describe \
  dev-redis-connector \
  --region=us-central1 \
  --project=vividly-dev-rich

# Check Cloud Run service
gcloud run services describe dev-vividly-api \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --format="value(spec.template.spec.containers[0].env)"

# Redeploy with VPC connector
gcloud run services update dev-vividly-api \
  --vpc-connector=dev-redis-connector \
  --region=us-central1
```

#### 3. Frontend 404s on Refresh (SPA Routing)

**Problem**: GCS bucket not serving `index.html` for 404s

**Solution**:
```bash
# Set website configuration
gsutil web set -m index.html -e index.html gs://vividly-prod-frontend-prod/
```

#### 4. SSL Certificate Provisioning Failed

**Problem**: DNS not properly configured or domain not verified

**Solution**:
```bash
# Check certificate status
gcloud compute ssl-certificates describe \
  prod-vividly-frontend-cert \
  --global \
  --project=vividly-prod

# Verify DNS
dig vividly.mnps.edu +short

# Domain verification (if needed)
gcloud domains verify vividly.mnps.edu
```

#### 5. Database Migration Fails

**Problem**: Cloud SQL not accessible or credentials wrong

**Solution**:
```bash
# Test connection
gcloud sql connect vividly-dev-db \
  --user=vividly_user \
  --project=vividly-dev-rich

# Check secrets
gcloud secrets versions access latest \
  --secret=database-url \
  --project=vividly-dev-rich

# Run migrations manually
export DATABASE_URL=$(gcloud secrets versions access latest --secret=database-url)
cd backend
alembic upgrade head
```

#### 6. High Redis Memory Usage

**Problem**: Redis cache not evicting old data

**Solution**:
```bash
# Check Redis config
gcloud redis instances describe dev-vividly-redis \
  --region=us-central1 \
  --project=vividly-dev-rich

# Update eviction policy
gcloud redis instances update dev-vividly-redis \
  --region=us-central1 \
  --set-redis-config maxmemory-policy=allkeys-lru
```

### Debug Commands

```bash
# Cloud Run logs
gcloud run services logs tail SERVICE_NAME \
  --project=PROJECT_ID \
  --region=us-central1

# Cloud SQL logs
gcloud sql operations list \
  --instance=INSTANCE_NAME \
  --project=PROJECT_ID

# Redis metrics
gcloud redis instances describe INSTANCE_NAME \
  --region=us-central1 \
  --project=PROJECT_ID

# VPC connector status
gcloud compute networks vpc-access connectors describe CONNECTOR_NAME \
  --region=us-central1 \
  --project=PROJECT_ID

# Terraform state
terraform show
terraform state list
terraform state show RESOURCE_NAME
```

### Get Help

- **GCP Support**: https://cloud.google.com/support
- **Terraform Docs**: https://www.terraform.io/docs
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Redis Docs**: https://cloud.google.com/memorystore/docs/redis

---

## Cost Estimates

### Development Environment (~$280/month)

- Cloud Run API: $20
- Cloud Run Jobs: $10
- Cloud SQL (1 vCPU): $50
- Redis (1 GB): $30
- GCS Frontend: $5
- Networking: $10
- Cloud Monitoring: $5
- Vertex AI Matching Engine: $150

### Production Environment (~$1,500/month)

- Cloud Run API: $100
- Cloud Run Jobs: $50
- Cloud SQL (4 vCPU, HA): $400
- Redis (5 GB, HA): $200
- GCS Frontend: $20
- Cloud CDN: $100
- Load Balancer: $50
- Networking: $100
- Cloud Monitoring: $30
- Vertex AI Matching Engine: $450

**Note**: Costs vary based on usage. Use [GCP Pricing Calculator](https://cloud.google.com/products/calculator) for accurate estimates.

---

## Maintenance Tasks

### Weekly

- [ ] Review Cloud Monitoring alerts
- [ ] Check error logs in Cloud Run
- [ ] Verify backup completion
- [ ] Review security advisories

### Monthly

- [ ] Update dependencies (`npm audit`, `pip audit`)
- [ ] Review and optimize Cloud SQL queries
- [ ] Check disk usage on Cloud SQL
- [ ] Review cost reports and optimize resources
- [ ] Update SSL certificates (if manual)

### Quarterly

- [ ] Load testing
- [ ] Security penetration testing
- [ ] Disaster recovery drill
- [ ] Review and update documentation
- [ ] Infrastructure optimization review

---

## Next Steps

After completing initial deployment:

1. **Configure Monitoring Dashboards**: Create custom dashboards for your use cases
2. **Set Up Alerting**: Configure PagerDuty/Slack for production alerts
3. **Load Testing**: Use Locust to test backend under load
4. **Security Audit**: Run security scans (see `SECURITY_TESTING.md`)
5. **Documentation**: Update internal runbooks
6. **Training**: Train team on deployment procedures

---

## Additional Resources

- [INFRASTRUCTURE_AUDIT.md](./INFRASTRUCTURE_AUDIT.md) - Complete infrastructure inventory
- [FRONTEND_UX_IMPLEMENTATION_PLAN.md](./FRONTEND_UX_IMPLEMENTATION_PLAN.md) - Feature implementation roadmap
- [SECURITY_TESTING.md](./SECURITY_TESTING.md) - Security testing procedures
- [Terraform Documentation](https://www.terraform.io/docs)
- [GCP Best Practices](https://cloud.google.com/docs/enterprise/best-practices-for-enterprise-organizations)
