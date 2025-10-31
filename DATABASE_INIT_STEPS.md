# Complete Step-by-Step Guide: Initialize Database on GCP

## Overview
This guide will walk you through initializing the Vividly database with all required tables and test data on Google Cloud Platform.

---

## Current Status

### ✅ Already Deployed (No Action Needed)
- Backend API: `dev-vividly-api` (Cloud Run Service)
- Content Worker: `dev-vividly-content-worker` (Cloud Run Job)
- Pub/Sub: topic `content-generation-requests` + subscription `content-generation-worker-sub`
- Vertex AI: Enabled with IAM permissions
- Database: PostgreSQL on Cloud SQL (private IP: 10.240.0.3)
- Secrets: All stored in Secret Manager
- Docker Images: `backend-api:latest` and `content-worker:latest` in Artifact Registry

### ❌ Needs to Be Done
- Create database tables
- Seed test data (users, topics, interests)

---

## Option 1: Using Cloud Run Job (Recommended - Most Secure)

This approach runs the init script inside GCP's private network where it can access the database.

### Step 1: Authenticate and Set Up

```bash
# Navigate to backend directory
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

# Set up gcloud
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_CONFIG="$HOME/.gcloud"

# Configure gcloud for the project
gcloud config set project vividly-dev-rich

# Authenticate Docker (may require interactive login)
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 2: Push the Database Init Image

The image has already been built locally: `us-central1-docker.pkg.dev/vividly-dev-rich/vividly/db-init:latest`

```bash
# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/db-init:latest
```

### Step 3: Create Cloud Run Job

```bash
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
```

**What this does:**
- Creates a Cloud Run Job named `dev-vividly-db-init`
- Connects to the private VPC (where the database is)
- Uses the compute service account (already has Cloud SQL client permissions)
- Injects DATABASE_URL from Secret Manager
- Times out after 10 minutes (init should take < 1 minute)

### Step 4: Execute the Job

```bash
gcloud run jobs execute dev-vividly-db-init \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --wait
```

**Expected output:**
```
✓ Creating execution... Done.
✓ Routing traffic... Done.
============================================================
Database Initialization Script
============================================================
INFO: Creating database tables...
INFO: ✓ Database tables created successfully
INFO: Creating test users...
INFO:   ✓ Created student: student1@test.com (password: password123)
INFO:   ✓ Created teacher: teacher1@test.com (password: password123)
INFO: Creating sample topics...
INFO:   ✓ Created topic: Photosynthesis (science, Grade 8)
INFO:   ✓ Created topic: Newton's Laws of Motion (science, Grade 9)
...
INFO: ✓ Database initialization completed successfully!
```

### Step 5: Verify Initialization

```bash
# Check job execution logs
gcloud run jobs executions list \
  --job=dev-vividly-db-init \
  --region=us-central1 \
  --project=vividly-dev-rich

# View detailed logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=dev-vividly-db-init" \
  --limit=50 \
  --project=vividly-dev-rich \
  --format=json
```

### Step 6: Test the API (Optional)

Once initialization completes, test that you can authenticate:

```bash
# Test login with the created test student account
curl -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student1@test.com",
    "password": "password123"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "...",
    "email": "student1@test.com",
    "role": "student",
    ...
  }
}
```

---

## Option 2: Using Cloud SQL Proxy (Alternative - Local Execution)

This approach creates a secure tunnel from your local machine to the database.

### Step 1: Install Cloud SQL Proxy

```bash
# Download Cloud SQL Proxy for Mac (ARM64)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64

# Make it executable
chmod +x cloud-sql-proxy

# Move to a directory in your PATH (optional)
sudo mv cloud-sql-proxy /usr/local/bin/
```

### Step 2: Start the Proxy

```bash
# Start Cloud SQL Proxy (keep this terminal open)
cloud-sql-proxy --port 5432 vividly-dev-rich:us-central1:vividly-dev-postgres
```

**Expected Output:**
```
Listening on 127.0.0.1:5432
The proxy has started successfully and is ready for new connections!
```

### Step 3: Run Init Script Locally

Open a **NEW terminal** (keep proxy running in the first one):

```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

# Activate virtual environment
source venv_test/bin/activate

# Get database password from Secret Manager
export DB_PASSWORD=$(gcloud secrets versions access latest --secret="database-url-dev" --project=vividly-dev-rich | grep -oP '(?<=:)[^@]+(?=@)')

# Set environment variables (pointing to localhost via proxy)
export DATABASE_URL="postgresql://vividly:${DB_PASSWORD}@localhost:5432/vividly"
export SECRET_KEY="test_secret_key_12345"
export PYTHONPATH=/Users/richedwards/AI-Dev-Projects/Vividly/backend

# Run the initialization script
python scripts/init_db_and_test_data.py
```

### Step 4: Verify Success

Same as Option 1, Step 6.

---

## Option 3: Using gcloud sql connect (Simplest - Interactive)

### Step 1: Connect to Database

```bash
gcloud sql connect vividly-dev-postgres \
  --user=vividly \
  --database=vividly \
  --project=vividly-dev-rich
```

**Enter password when prompted** (retrieve from Secret Manager if needed).

### Step 2: Manually Create Tables

You'll be in a PostgreSQL shell (`vividly=>`). You can run SQL commands directly, but this is more error-prone than using the automated script.

**This option is NOT recommended** because you'd need to manually execute all CREATE TABLE statements and INSERT test data.

---

## What Gets Created

### Database Tables
- `users` - Student and teacher accounts
- `topics` - Educational topics (Photosynthesis, Newton's Laws, etc.)
- `interests` - Student interests (Basketball, Soccer, Video Games, etc.)
- `student_interest` - Junction table linking students to interests
- `classes` - Class/course information
- `class_student` - Students enrolled in classes
- `content_metadata` - Generated content metadata
- `progress` - Student progress tracking
- `feature_flags` - Feature toggle management
- `request_tracking` - API request tracking
- `sessions` - User session management

### Test Accounts Created
| Email | Password | Role | Grade Level |
|-------|----------|------|-------------|
| student1@test.com | password123 | student | 8 |
| teacher1@test.com | password123 | teacher | N/A |

### Sample Topics Created
1. Photosynthesis (Science, Grade 8)
2. Newton's Laws of Motion (Science, Grade 9)
3. The Water Cycle (Science, Grade 6)
4. Fractions and Decimals (Math, Grade 7)
5. The American Revolution (History, Grade 8)

### Sample Interests Created
1. Basketball (sports)
2. Soccer (sports)
3. Video Games (technology)
4. Cooking (arts)
5. Music (arts)
6. Animals (nature)
7. Space (science)
8. Movies (entertainment)

---

## Troubleshooting

### Error: "Connection refused" or "No such file or directory"
**Cause**: Cannot reach database (it's in a private VPC)
**Solution**: Use Option 1 (Cloud Run Job) or Option 2 (Cloud SQL Proxy)

### Error: "permission denied" or "authentication failed"
**Cause**: Incorrect database credentials
**Solution**: Verify DATABASE_URL secret in Secret Manager:
```bash
gcloud secrets versions access latest --secret="database-url-dev" --project=vividly-dev-rich
```

### Error: "Table already exists"
**Cause**: Database has already been initialized
**Solution**: This is OK! The script is idempotent - it will skip existing tables and data.

### Error: "Cloud Run Job failed"
**Solution**: Check logs:
```bash
gcloud logging read "resource.type=cloud_run_job" \
  --limit=100 \
  --project=vividly-dev-rich
```

---

## After Initialization

### Next Steps
1. ✅ Database initialized with tables and test data
2. Test content generation API:
   ```bash
   # Get JWT token
   TOKEN=$(curl -X POST https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/auth/login \
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

3. Set up monitoring and alerts (see PHASE3_DEPLOYMENT_COMPLETE.md)
4. Configure CDN for content delivery (optional)
5. Move to staging/production environments

---

## Files Reference

- **Init Script**: `/Users/richedwards/AI-Dev-Projects/Vividly/backend/scripts/init_db_and_test_data.py`
- **Dockerfile**: `/Users/richedwards/AI-Dev-Projects/Vividly/backend/Dockerfile.init-db`
- **Deployment Docs**: `/Users/richedwards/AI-Dev-Projects/Vividly/PHASE3_DEPLOYMENT_COMPLETE.md`
- **Local Docker Image**: `us-central1-docker.pkg.dev/vividly-dev-rich/vividly/db-init:latest`

---

## Summary

**Recommended Approach**: **Option 1 (Cloud Run Job)**

This is the most secure and GCP-native way to initialize the database. The job runs inside Google's private network with proper IAM permissions, and you can track execution through Cloud Logging.

Total time: **~5 minutes** (mostly waiting for job to execute)

---

*Last Updated: October 30, 2025*
*Created by: Claude Code*
