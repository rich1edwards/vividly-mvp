# Vividly Development Setup Guide

**Version:** 1.0
**Last Updated:** October 27, 2025
**Estimated Setup Time:** 60-90 minutes

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GCP Project Setup](#gcp-project-setup)
3. [Local Environment Setup](#local-environment-setup)
4. [Database Setup](#database-setup)
5. [Vector Database Setup](#vector-database-setup)
6. [Backend Setup](#backend-setup)
7. [Frontend Setup](#frontend-setup)
8. [Running the Application](#running-the-application)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11+ | Backend services |
| **Node.js** | 18+ | Frontend development |
| **npm** | 9+ | Package management |
| **Docker** | 24+ | Local PostgreSQL |
| **Docker Compose** | 2.20+ | Multi-container orchestration |
| **gcloud CLI** | Latest | GCP interaction |
| **Git** | 2.40+ | Version control |
| **psql** | 15+ | Database client |

### Install Prerequisites (macOS)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 node postgresql docker docker-compose git

# Install gcloud CLI
brew install --cask google-cloud-sdk

# Verify installations
python3 --version  # Should be 3.11+
node --version     # Should be v18+
docker --version   # Should be 24+
gcloud --version   # Should be latest
```

### Install Prerequisites (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker
sudo apt install docker.io docker-compose

# Install PostgreSQL client
sudo apt install postgresql-client-15

# Install gcloud CLI
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt update && sudo apt install google-cloud-cli
```

### Required Accounts

1. **Google Cloud Platform Account**
   - Free tier available ($300 credit for new users)
   - Billing must be enabled for Vertex AI
   - Project quota: At least 1 project available

2. **Nano Banana API Account** (for video generation)
   - Sign up at https://nanobanana.ai
   - Obtain API key
   - Minimum balance: $10

---

## GCP Project Setup

### 1. Create GCP Project

```bash
# Set project ID (use lowercase, numbers, hyphens only)
export PROJECT_ID="vividly-dev-$(whoami)"

# Create project
gcloud projects create $PROJECT_ID --name="Vividly Development"

# Set as default project
gcloud config set project $PROJECT_ID

# Link billing account (replace with your billing account ID)
gcloud billing projects link $PROJECT_ID --billing-account=ABCDEF-123456-GHIJKL
```

### 2. Enable Required APIs

```bash
# Enable all required Google Cloud APIs
gcloud services enable \
    compute.googleapis.com \
    cloudrun.googleapis.com \
    cloudfunctions.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    pubsub.googleapis.com \
    cloudtasks.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    texttospeech.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    clouderrorreporting.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

### 3. Set Up Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set up application default credentials
gcloud auth application-default login

# Create service account for local development
gcloud iam service-accounts create vividly-dev-sa \
    --display-name="Vividly Development Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:vividly-dev-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/editor"

# Download service account key
gcloud iam service-accounts keys create ~/vividly-dev-key.json \
    --iam-account=vividly-dev-sa@${PROJECT_ID}.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/vividly-dev-key.json
```

### 4. Create GCS Buckets

```bash
# Set region
export REGION="us-central1"

# Create buckets
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-scripts
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-audio
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-videos
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-uploads
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-vector-db

# Set lifecycle policy for uploads bucket (delete after 7 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://${PROJECT_ID}-uploads
rm lifecycle.json

# Enable uniform bucket-level access
for bucket in scripts audio videos uploads vector-db; do
    gsutil uniformbucketlevelaccess set on gs://${PROJECT_ID}-${bucket}
done
```

### 5. Set Up Pub/Sub Topics

```bash
# Create topics
gcloud pubsub topics create generate-script
gcloud pubsub topics create generate-audio
gcloud pubsub topics create generate-video
gcloud pubsub topics create content-ready

# Create dead letter queues
gcloud pubsub topics create dlq-script
gcloud pubsub topics create dlq-audio
gcloud pubsub topics create dlq-video

# Create subscriptions
gcloud pubsub subscriptions create script-worker-sub \
    --topic=generate-script \
    --ack-deadline=600 \
    --dead-letter-topic=dlq-script \
    --max-delivery-attempts=5

gcloud pubsub subscriptions create audio-worker-sub \
    --topic=generate-audio \
    --ack-deadline=600 \
    --dead-letter-topic=dlq-audio \
    --max-delivery-attempts=5

gcloud pubsub subscriptions create video-worker-sub \
    --topic=generate-video \
    --ack-deadline=600 \
    --dead-letter-topic=dlq-video \
    --max-delivery-attempts=5

gcloud pubsub subscriptions create content-ready-sub \
    --topic=content-ready \
    --ack-deadline=60
```

---

## Local Environment Setup

### 1. Clone Repository

```bash
# Clone repository
git clone https://github.com/vividly/vividly-mvp.git
cd vividly-mvp

# Create development branch
git checkout -b dev-$(whoami)
```

### 2. Create Environment Files

```bash
# Create .env file for backend
cat > backend/.env << 'EOF'
# GCP Configuration
GCP_PROJECT_ID=vividly-dev-yourname
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/vividly-dev-key.json

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vividly_dev
DB_USER=vividly_dev
DB_PASSWORD=dev_password_change_me

# Cloud Storage Buckets
GCS_BUCKET_SCRIPTS=vividly-dev-yourname-scripts
GCS_BUCKET_AUDIO=vividly-dev-yourname-audio
GCS_BUCKET_VIDEOS=vividly-dev-yourname-videos
GCS_BUCKET_UPLOADS=vividly-dev-yourname-uploads

# Pub/Sub Topics
PUBSUB_TOPIC_SCRIPT=generate-script
PUBSUB_TOPIC_AUDIO=generate-audio
PUBSUB_TOPIC_VIDEO=generate-video
PUBSUB_TOPIC_CONTENT_READY=content-ready

# JWT Configuration
JWT_SECRET=dev_jwt_secret_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Nano Banana API
NANO_BANANA_API_KEY=your_nano_banana_api_key_here
NANO_BANANA_API_URL=https://api.nanobanana.ai/v1

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_EMBEDDING_MODEL=text-embedding-gecko@003
VERTEX_AI_LLM_MODEL=gemini-1.5-pro

# Development Settings
DEBUG=True
LOG_LEVEL=DEBUG
ENVIRONMENT=development
EOF

# Create .env file for frontend
cat > webapp/.env << 'EOF'
VITE_API_BASE_URL=http://localhost:8000
VITE_ENVIRONMENT=development
EOF
```

### 3. Update Environment Variables

```bash
# Replace placeholders with actual values
nano backend/.env  # or use your preferred editor

# Key values to update:
# - GCP_PROJECT_ID: your actual project ID
# - GOOGLE_APPLICATION_CREDENTIALS: path to your service account key
# - NANO_BANANA_API_KEY: your actual API key
# - DB_PASSWORD: choose a secure password
```

---

## Database Setup

### Option 1: Docker PostgreSQL (Recommended for Development)

```bash
# Create docker-compose.yml for PostgreSQL
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: vividly-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: vividly_dev
      POSTGRES_USER: vividly_dev
      POSTGRES_PASSWORD: dev_password_change_me
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vividly_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
EOF

# Start PostgreSQL
docker-compose up -d postgres

# Verify PostgreSQL is running
docker-compose ps

# Test connection
psql -h localhost -U vividly_dev -d vividly_dev -c "SELECT version();"
```

### Option 2: Cloud SQL (For Cloud Development)

```bash
# Create Cloud SQL instance
gcloud sql instances create vividly-dev-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password=choose_strong_password

# Create database
gcloud sql databases create vividly_dev --instance=vividly-dev-db

# Create user
gcloud sql users create vividly_dev \
    --instance=vividly-dev-db \
    --password=choose_user_password

# Connect via Cloud SQL Proxy
cloud_sql_proxy -instances=${PROJECT_ID}:${REGION}:vividly-dev-db=tcp:5432
```

### Database Migrations

```bash
# Navigate to backend
cd backend

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations
alembic upgrade head

# Verify tables were created
psql -h localhost -U vividly_dev -d vividly_dev -c "\dt"

# Seed initial data
python scripts/seed_data.py
```

---

## Vector Database Setup

### 1. Create Vertex AI Vector Search Index

```bash
# Navigate to scripts directory
cd backend/scripts

# Run index creation script
python create_vector_index.py

# Expected output:
# ✓ Created index: projects/vividly-dev-yourname/locations/us-central1/indexes/123456789
# ✓ Index is being built (this may take 30-60 minutes)
```

### 2. Ingest Sample OER Content

```bash
# Download sample OpenStax content
./download_openstax_samples.sh

# Process and embed content
python ingest_oer.py --source data/openstax/physics_sample.docx --topic-id topic_phys_newton_3

# Monitor ingestion progress
python check_ingestion_status.py

# Expected output:
# ✓ Processed 45 chunks
# ✓ Generated embeddings
# ✓ Uploaded to Vector Search
# ✓ Stored metadata in PostgreSQL
```

### 3. Deploy Vector Search Endpoint

```bash
# Deploy endpoint (can take 15-30 minutes)
python deploy_vector_endpoint.py

# Test endpoint
python test_vector_search.py --query "explain newton's third law"

# Expected output:
# ✓ Query successful
# ✓ Retrieved 10 chunks
# ✓ Top result similarity: 0.87
```

---

## Backend Setup

### 1. Install Python Dependencies

```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Verify installation
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
```

### 2. Run Tests

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests (requires running database)
pytest tests/integration -v

# Run with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 3. Start Backend Services

```bash
# Start API Gateway (main backend)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In separate terminals, start worker services:

# NLU Service (Cloud Function locally)
functions-framework --target=nlu_handler --port=8001

# Script Worker
functions-framework --target=script_worker --port=8002

# Audio Worker
functions-framework --target=audio_worker --port=8003

# Video Worker
functions-framework --target=video_worker --port=8004
```

---

## Frontend Setup

### 1. Install Node Dependencies

```bash
cd webapp

# Install dependencies
npm install

# Verify installation
npm list react react-dom typescript
```

### 2. Start Development Server

```bash
# Start Vite dev server
npm run dev

# Server will start at http://localhost:5173
# Open in browser
```

### 3. Run Frontend Tests

```bash
# Run unit tests
npm test

# Run E2E tests (requires backend running)
npm run test:e2e

# Run linter
npm run lint

# Format code
npm run format
```

---

## Running the Application

### Full Stack Development

```bash
# Terminal 1: Start PostgreSQL (if using Docker)
docker-compose up postgres

# Terminal 2: Start backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 3: Start frontend
cd webapp
npm run dev

# Open browser to http://localhost:5173
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc
- **PostgreSQL**: localhost:5432

### Test Credentials

Default development users (created by seed script):

| Role | Email | Password |
|------|-------|----------|
| Student | student@test.vividly.education | student123 |
| Teacher | teacher@test.vividly.education | teacher123 |
| Admin | admin@test.vividly.education | admin123 |

---

## Troubleshooting

### Common Issues

#### Issue: PostgreSQL connection refused

```bash
# Check if PostgreSQL is running
docker-compose ps

# If not running, start it
docker-compose up -d postgres

# Check logs
docker-compose logs postgres
```

#### Issue: GCP authentication errors

```bash
# Verify credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Re-authenticate
gcloud auth application-default login

# Verify project is set
gcloud config get-value project
```

#### Issue: ModuleNotFoundError in Python

```bash
# Verify virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: Port already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --reload --port 8001
```

#### Issue: Vertex AI quota exceeded

```bash
# Check quota usage
gcloud alpha services quotas list \
    --service=aiplatform.googleapis.com \
    --consumer=projects/$PROJECT_ID

# Request quota increase in GCP Console:
# IAM & Admin > Quotas > Vertex AI
```

### Reset Development Environment

```bash
# Stop all services
docker-compose down

# Remove database (WARNING: destroys data)
docker volume rm vividly-mvp_postgres_data

# Recreate database
docker-compose up -d postgres

# Re-run migrations
cd backend
alembic upgrade head
python scripts/seed_data.py
```

---

## Next Steps

1. **Review Architecture**: Read [ARCHITECTURE.md](./ARCHITECTURE.md)
2. **Explore API**: Visit http://localhost:8000/docs
3. **Run Tests**: Ensure all tests pass before development
4. **Check Contributing Guide**: Read [CONTRIBUTING.md](./CONTRIBUTING.md)
5. **Join Development Slack**: [Link to team Slack]

---

## Development Resources

- **API Documentation**: http://localhost:8000/docs
- **Database Migrations**: `backend/migrations/`
- **Test Data**: `backend/scripts/test_data/`
- **Design Mockups**: `design/figma/` (link to Figma)
- **Team Wiki**: [Link to Confluence/Notion]

---

**Document Control**
- **Owner**: DevOps Team
- **Last Updated**: October 27, 2025
- **Next Review**: Monthly
- **Support**: dev-support@vividly.education
