# Vividly - Quick Start on GCP

## TL;DR - Get Everything Running in 5 Steps

### 1. Authenticate Docker
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_CONFIG="$HOME/.gcloud"
gcloud config set project vividly-dev-rich
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 2. Push Database Init Image
```bash
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/db-init:latest
```

### 3. Create & Run Database Initialization Job
```bash
# Create the job
gcloud run jobs create dev-vividly-db-init \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/db-init:latest \
  --region=us-central1 \
  --memory=2Gi \
  --cpu=1 \
  --max-retries=1 \
  --task-timeout=600s \
  --set-env-vars="SECRET_KEY=test_secret_key_12345" \
  --set-secrets=DATABASE_URL=database-url-dev:latest \
  --service-account=758727113555-compute@developer.gserviceaccount.com \
  --vpc-connector=cloud-run-connector \
  --project=vividly-dev-rich

# Execute it
gcloud run jobs execute dev-vividly-db-init \
  --region=us-central1 \
  --wait
```

### 4. Test Authentication
```bash
curl -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@test.com","password":"password123"}'
```

### 5. Test Content Generation
```bash
# Get token
TOKEN=$(curl -s -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@test.com","password":"password123"}' | jq -r '.access_token')

# Generate content
curl -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "student_query": "Explain photosynthesis using basketball",
    "student_id": "student_123",
    "grade_level": 8,
    "interest": "basketball"
  }'
```

---

## What's Already Running

| Service | Type | Status | URL |
|---------|------|--------|-----|
| Backend API | Cloud Run Service | ✅ Running | https://dev-vividly-api-758727113555.us-central1.run.app |
| Content Worker | Cloud Run Job | ✅ Ready | On-demand execution |
| Database | Cloud SQL PostgreSQL | ✅ Running | Private VPC (10.240.0.3) |
| Pub/Sub | Topic + Subscription | ✅ Active | content-generation-requests |
| Vertex AI | Gemini API | ✅ Enabled | aiplatform.googleapis.com |

---

## Test Accounts

| Email | Password | Role | Access |
|-------|----------|------|--------|
| student1@test.com | password123 | student | Content generation |
| teacher1@test.com | password123 | teacher | Class management |

---

## Key Endpoints

### Health Check
```bash
curl https://dev-vividly-api-758727113555.us-central1.run.app/health
```

### NLU Health (Vertex AI Status)
```bash
curl https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/nlu/health
```

### Login
```bash
curl -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@test.com","password":"password123"}'
```

### Generate Content (Requires Auth)
```bash
curl -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "student_query": "Explain [topic] using [interest]",
    "student_id": "student_123",
    "grade_level": 8,
    "interest": "basketball"
  }'
```

---

## Monitoring & Logs

### View API Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dev-vividly-api" \
  --limit 50 \
  --project=vividly-dev-rich
```

### View Database Init Job Logs
```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=dev-vividly-db-init" \
  --limit 50 \
  --project=vividly-dev-rich
```

### View Vertex AI Logs
```bash
gcloud logging read "resource.type=aiplatform.googleapis.com" \
  --limit 50 \
  --project=vividly-dev-rich
```

### Monitor Costs
```bash
# View current billing
gcloud billing projects describe vividly-dev-rich

# View budget alerts (if configured)
gcloud alpha billing budgets list
```

---

## Infrastructure Details

### GCP Project
- **Name**: vividly-dev-rich
- **Region**: us-central1 (Iowa)
- **Environment**: Development

### Compute Resources
- **Backend API**: 1 vCPU, 1Gi RAM, scale-to-zero
- **Content Worker**: 4 vCPU, 8Gi RAM, 30min timeout
- **Database**: db-f1-micro PostgreSQL 17

### Storage
- `vividly-dev-rich-dev-generated-content` - Generated videos
- `vividly-dev-rich-dev-oer-content` - Open educational resources
- `vividly-dev-rich-dev-temp-files` - Temporary processing files

### Networking
- **VPC Connector**: cloud-run-connector
- **Database IP**: 10.240.0.3 (private)
- **Public Endpoints**: Backend API only (HTTPS)

---

## Cost Estimate

| Service | Monthly Cost (Dev) |
|---------|-------------------|
| Cloud Run API | $5-10 |
| Cloud Run Job | $0 + usage |
| Vertex AI (Gemini) | $100-200 |
| Cloud SQL | $25-50 |
| Cloud Storage | $5-10 |
| Pub/Sub | $0.40 |
| **Total** | **~$135-270** |

**Optimization Notes:**
- Scale-to-zero enabled (no idle costs)
- Use quotas to limit Vertex AI spending
- Database can be paused when not in use

---

## Troubleshooting

### Can't Connect to Database
- ✅ Database is in private VPC (this is correct)
- ✅ Use Cloud Run Job or Cloud SQL Proxy
- ❌ Do NOT try to connect directly

### Authentication Fails
```bash
# Check secrets
gcloud secrets versions access latest --secret="database-url-dev" --project=vividly-dev-rich
gcloud secrets versions access latest --secret="jwt-secret-dev" --project=vividly-dev-rich
```

### Content Generation Fails
```bash
# 1. Check Vertex AI is enabled
gcloud services list --enabled | grep aiplatform

# 2. Check IAM permissions
gcloud projects get-iam-policy vividly-dev-rich \
  --flatten="bindings[].members" \
  --filter="bindings.members:758727113555-compute@developer.gserviceaccount.com"

# 3. Check API logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20
```

---

## Documentation

- **Complete Deployment**: [PHASE3_DEPLOYMENT_COMPLETE.md](./PHASE3_DEPLOYMENT_COMPLETE.md)
- **Database Initialization**: [DATABASE_INIT_STEPS.md](./DATABASE_INIT_STEPS.md)
- **API Documentation**: Check `/health` endpoint for status
- **Architecture**: See `docs/` directory

---

## Next Steps

1. ✅ Initialize database (follow steps above)
2. Test content generation pipeline
3. Set up monitoring and alerts
4. Configure CI/CD for automated deployments
5. Plan staging environment
6. Plan production deployment

---

*Last Updated: October 30, 2025*
*Environment: Development*
