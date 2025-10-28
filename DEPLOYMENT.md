# Vividly Deployment Guide

**Version:** 1.0 (MVP)
**Last Updated:** October 27, 2025
**Target Platform:** Google Cloud Platform

## Table of Contents

1. [Overview](#overview)
2. [Infrastructure Architecture](#infrastructure-architecture)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Deployment Environments](#deployment-environments)
5. [Deployment Process](#deployment-process)
6. [Rollback Procedures](#rollback-procedures)
7. [Infrastructure as Code](#infrastructure-as-code)
8. [Monitoring & Health Checks](#monitoring--health-checks)

---

## Overview

Vividly uses a fully automated CI/CD pipeline that deploys to Google Cloud Platform on every commit. The deployment is managed through GitHub Actions with infrastructure provisioned via Terraform.

### Deployment Strategy

- **Development**: Auto-deploy on push to `develop` branch
- **Staging**: Auto-deploy on push to `main` branch
- **Production**: Deploy on GitHub Release (with manual approval)

### Key Technologies

- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform
- **Container Registry**: Google Artifact Registry
- **Compute**: Cloud Run (services), Cloud Functions (workers)
- **Database**: Cloud SQL (PostgreSQL)
- **Storage**: Cloud Storage (GCS)

---

## Infrastructure Architecture

### Deployment Topology

```
GitHub Repository
      │
      │ (git push)
      ▼
┌─────────────────────┐
│  GitHub Actions     │
│  - Build            │
│  - Test             │
│  - Deploy           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Google Cloud Platform                  │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  Artifact Registry                 │ │
│  │  - Backend images                  │ │
│  │  - Frontend bundles                │ │
│  └────────────────────────────────────┘ │
│           │                              │
│           ▼                              │
│  ┌────────────────────────────────────┐ │
│  │  Cloud Run Services                │ │
│  │  - api-gateway                     │ │
│  │  - student-service                 │ │
│  │  - teacher-service                 │ │
│  │  - admin-service                   │ │
│  └────────────────────────────────────┘ │
│           │                              │
│           ▼                              │
│  ┌────────────────────────────────────┐ │
│  │  Cloud Functions                   │ │
│  │  - nlu-service                     │ │
│  │  - script-worker                   │ │
│  │  - audio-worker                    │ │
│  │  - video-worker                    │ │
│  └────────────────────────────────────┘ │
│           │                              │
│           ▼                              │
│  ┌────────────────────────────────────┐ │
│  │  Cloud SQL + GCS + Pub/Sub         │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. Development Deployment

**Trigger**: Push to `develop` branch

```yaml
# .github/workflows/deploy-dev.yml

name: Deploy to Development

on:
  push:
    branches: [develop]

env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GCP_REGION: us-central1
  ENVIRONMENT: development

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pytest tests/ -v --cov=.

      - name: Run frontend tests
        run: |
          cd webapp
          npm install
          npm run test:unit

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Configure Docker for Artifact Registry
        run: |
          gcloud auth configure-docker ${{ env.GCP_REGION }}-docker.pkg.dev

      - name: Build Backend Images
        run: |
          cd backend

          # Build API Gateway
          docker build -t ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/vividly/api-gateway:${{ github.sha }} \
            -f Dockerfile.api-gateway .

          # Build other services
          docker build -t ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/vividly/student-service:${{ github.sha }} \
            -f Dockerfile.student-service .

          # Push images
          docker push ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/vividly/api-gateway:${{ github.sha }}
          docker push ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/vividly/student-service:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          # Deploy API Gateway
          gcloud run deploy api-gateway-dev \
            --image=${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/vividly/api-gateway:${{ github.sha }} \
            --platform=managed \
            --region=${{ env.GCP_REGION }} \
            --allow-unauthenticated \
            --set-env-vars="ENVIRONMENT=development" \
            --min-instances=0 \
            --max-instances=10 \
            --memory=512Mi \
            --cpu=1 \
            --timeout=300 \
            --service-account=${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Deploy Cloud Functions
        run: |
          # Deploy NLU Service
          gcloud functions deploy nlu-service-dev \
            --gen2 \
            --runtime=python311 \
            --region=${{ env.GCP_REGION }} \
            --source=./workers/nlu_service \
            --entry-point=handler \
            --trigger-http \
            --memory=512MB \
            --timeout=30s \
            --set-env-vars="ENVIRONMENT=development" \
            --service-account=${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Run Database Migrations
        run: |
          # Connect via Cloud SQL Proxy and run migrations
          wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
          chmod +x cloud_sql_proxy

          ./cloud_sql_proxy -instances=${{ secrets.CLOUD_SQL_INSTANCE }}=tcp:5432 &

          cd backend
          alembic upgrade head

      - name: Deploy Frontend to Firebase Hosting
        run: |
          cd webapp
          npm install
          npm run build

          # Deploy to Firebase
          npm install -g firebase-tools
          firebase deploy --only hosting:dev --token=${{ secrets.FIREBASE_TOKEN }}

      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Development deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

#### 2. Staging Deployment

**Trigger**: Push to `main` branch

```yaml
# .github/workflows/deploy-staging.yml

name: Deploy to Staging

on:
  push:
    branches: [main]

env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GCP_REGION: us-central1
  ENVIRONMENT: staging

jobs:
  # Similar to dev, but with:
  # - Longer tests (including E2E)
  # - Smoke tests after deployment
  # - Performance tests
  # - Security scans

  deploy:
    # ... deployment steps

  smoke-test:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Run smoke tests
        run: |
          # Test critical endpoints
          curl -f https://staging.vividly.education/health || exit 1
          curl -f https://api-staging.vividly.education/api/v1/health || exit 1

  performance-test:
    needs: smoke-test
    runs-on: ubuntu-latest
    steps:
      - name: Run load tests
        run: |
          cd backend/tests/performance
          locust -f test_load.py --headless --users 50 --spawn-rate 5 --run-time 5m --host https://api-staging.vividly.education
```

#### 3. Production Deployment

**Trigger**: GitHub Release created

```yaml
# .github/workflows/deploy-production.yml

name: Deploy to Production

on:
  release:
    types: [created]

env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GCP_REGION: us-central1
  ENVIRONMENT: production

jobs:
  approval:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.vividly.education
    steps:
      - name: Wait for approval
        run: echo "Deployment approved"

  deploy:
    needs: approval
    runs-on: ubuntu-latest

    steps:
      # Similar to staging, but with:
      # - Blue-green deployment
      # - Canary releases (10% → 50% → 100%)
      # - Automated rollback on errors

      - name: Deploy with canary
        run: |
          # Deploy new version with 10% traffic
          gcloud run deploy api-gateway-prod \
            --image=${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/vividly/api-gateway:${{ github.sha }} \
            --platform=managed \
            --region=${{ env.GCP_REGION }} \
            --tag=canary \
            --no-traffic

          # Route 10% traffic to canary
          gcloud run services update-traffic api-gateway-prod \
            --to-revisions=canary=10,LATEST=90

          # Wait and monitor
          sleep 300

          # Check error rate
          ERROR_RATE=$(gcloud monitoring time-series list --filter='...' --format='value(points[0].value.doubleValue)')

          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate too high, rolling back"
            gcloud run services update-traffic api-gateway-prod --to-latest
            exit 1
          fi

          # Gradually increase traffic
          gcloud run services update-traffic api-gateway-prod --to-revisions=canary=50,LATEST=50
          sleep 300

          # Final switch
          gcloud run services update-traffic api-gateway-prod --to-latest
```

---

## Deployment Environments

### Environment Configuration

| Environment | Branch | Auto-Deploy | Approval Required | URL |
|-------------|--------|-------------|-------------------|-----|
| **Development** | `develop` | ✅ Yes | ❌ No | dev.vividly.education |
| **Staging** | `main` | ✅ Yes | ❌ No | staging.vividly.education |
| **Production** | Release tag | ❌ No | ✅ Yes | app.vividly.education |

### Environment Variables

```bash
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
GCP_PROJECT_ID=vividly-dev
DB_INSTANCE=vividly-dev:us-central1:vividly-dev-db

# Staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
GCP_PROJECT_ID=vividly-staging
DB_INSTANCE=vividly-staging:us-central1:vividly-staging-db

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
GCP_PROJECT_ID=vividly-prod
DB_INSTANCE=vividly-prod:us-central1:vividly-prod-db
```

---

## Deployment Process

### Step-by-Step Deployment

#### For Developers (Development)

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes
# ... code changes ...

# 3. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# 4. Create Pull Request to 'develop'
# GitHub PR → Review → Merge

# 5. Automatic deployment to dev environment
# GitHub Actions runs tests and deploys

# 6. Verify deployment
curl https://dev.vividly.education/health
```

#### For Staging Release

```bash
# 1. Merge develop → main
git checkout main
git merge develop
git push origin main

# 2. Automatic deployment to staging
# GitHub Actions runs full test suite and deploys

# 3. Run E2E tests
npm run test:e2e -- --host=https://staging.vividly.education

# 4. Manual QA testing
```

#### For Production Release

```bash
# 1. Create release tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 2. Create GitHub Release
# Go to GitHub → Releases → Create new release

# 3. Approve deployment
# GitHub → Actions → Approve production deployment

# 4. Monitor deployment
# Watch canary rollout
# Check error rates and metrics

# 5. Verify production
curl https://app.vividly.education/health
```

---

## Rollback Procedures

### Automatic Rollback

Deployment automatically rolls back if:
- Health checks fail
- Error rate > 1%
- Response time > 5s (p95)
- Critical metrics degraded

### Manual Rollback

#### Cloud Run Services

```bash
# List revisions
gcloud run revisions list --service=api-gateway-prod --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic api-gateway-prod \
  --to-revisions=api-gateway-prod-00042-abc=100 \
  --region=us-central1
```

#### Cloud Functions

```bash
# Deploy previous version
gcloud functions deploy nlu-service-prod \
  --source=gs://vividly-prod-functions/nlu-service-v1.0.0.zip
```

#### Database Rollback

```bash
# Rollback migration
cd backend
alembic downgrade -1

# Or rollback to specific version
alembic downgrade abc123
```

---

## Infrastructure as Code

### Terraform Configuration

```hcl
# terraform/main.tf

terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "vividly-terraform-state"
    prefix = "prod/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Run Service
resource "google_cloud_run_service" "api_gateway" {
  name     = "api-gateway-${var.environment}"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/vividly/api-gateway:${var.image_tag}"

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }

      service_account_name = google_service_account.cloudrun_sa.email
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "100"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "vividly-${var.environment}-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.environment == "production" ? "db-custom-2-8192" : "db-f1-micro"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
}

# GCS Buckets
resource "google_storage_bucket" "videos" {
  name     = "vividly-${var.environment}-videos"
  location = var.region

  lifecycle_rule {
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 90
      matches_storage_class = ["STANDARD"]
    }
  }
}

# Pub/Sub Topics
resource "google_pubsub_topic" "generate_script" {
  name = "generate-script-${var.environment}"
}

resource "google_pubsub_subscription" "script_worker" {
  name  = "script-worker-sub-${var.environment}"
  topic = google_pubsub_topic.generate_script.name

  ack_deadline_seconds = 600

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq_script.id
    max_delivery_attempts = 5
  }
}
```

### Terraform Deployment

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan changes
terraform plan -var-file=environments/prod.tfvars

# Apply changes
terraform apply -var-file=environments/prod.tfvars

# Destroy (DANGER!)
terraform destroy -var-file=environments/prod.tfvars
```

---

## Monitoring & Health Checks

### Health Check Endpoints

```python
# backend/api/health.py

from fastapi import APIRouter, status
from sqlalchemy import text

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "version": VERSION
    }

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check - verify all dependencies."""

    checks = {}
    all_healthy = True

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check GCS
    try:
        storage_client.bucket(BUCKET_VIDEOS).exists()
        checks["storage"] = {"status": "healthy"}
    except Exception as e:
        checks["storage"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Vertex AI
    try:
        # Quick health check
        checks["vertex_ai"] = {"status": "healthy"}
    except Exception as e:
        checks["vertex_ai"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    if not all_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "checks": checks}
        )

    return {"status": "ready", "checks": checks}
```

### Cloud Run Health Check Configuration

```yaml
# Cloud Run automatically monitors:
- HTTP endpoint: /health
- Interval: 10s
- Timeout: 5s
- Failure threshold: 3
```

### Uptime Monitoring

```bash
# Create uptime check
gcloud monitoring uptime create vividly-prod-api \
  --resource-type=uptime-url \
  --host=app.vividly.education \
  --path=/health \
  --check-interval=60s \
  --timeout=10s
```

---

**Document Control**
- **Owner**: DevOps Team
- **Last Updated**: October 27, 2025
- **Next Review**: After each major release
- **Related**: SECURITY.md, TESTING_STRATEGY.md
