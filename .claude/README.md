# Vividly Architecture Documentation

This directory contains comprehensive architecture documentation for the Vividly platform.

## Overview

Vividly is an AI-powered educational platform that generates personalized video content for students. The system combines:
- Natural Language Understanding (NLU)
- Retrieval-Augmented Generation (RAG) from OpenStax content
- Large Language Models (Gemini 1.5 Pro) for script generation
- Text-to-Speech (Google Cloud TTS) for narration
- Video rendering and assembly
- Async processing with Pub/Sub for scalability

## Architecture Documents

### 1. [Async Content Generation Architecture](./async-content-generation-architecture.md)

**Purpose**: Describes the asynchronous content generation system using Google Cloud Pub/Sub.

**Key Topics**:
- Problem statement: Why async? (API timeout prevention)
- Complete data flow: API → Pub/Sub → Worker → Database → Status Polling
- Pub/Sub configuration: Topics, subscriptions, retry policies, DLQ
- Content Worker implementation: Streaming pull, ack/nack logic, flow control
- Database schema: `content_requests` table for progress tracking
- Error handling: Retry strategies, exponential backoff
- Monitoring & observability: Metrics, logging, alerting
- Deployment: Cloud Run Service (API) + Cloud Run Job (Worker)
- Performance characteristics: Latency, throughput, scaling
- Security: IAM, authentication, data privacy

**When to Reference**:
- Implementing new async workflows
- Debugging timeout issues
- Understanding Pub/Sub message flow
- Scaling workers based on load
- Investigating failed content generation requests

### 2. [RAG Pipeline Architecture](./rag-pipeline-architecture.md)

**Purpose**: Describes the educational content pipeline from OpenStax ingestion to personalized video generation.

**Key Topics**:
- Source content ingestion: OpenStax.org scraping and storage
- Content processing: Chunking, embedding generation
- Vector search: Semantic similarity for relevant content retrieval
- Student query flow: NLU → RAG → Script Generation → TTS → Video
- Interest selection strategy: LLM selects best interest for each topic
- Content caching: Reuse generated content across students
- Database tables: Topics, ContentMetadata, StudentProgress
- Missing infrastructure: Chunking service, vector DB setup

**When to Reference**:
- Understanding content generation pipeline
- Implementing RAG retrieval logic
- Setting up vector database
- Designing content chunking strategy
- Understanding interest-based personalization

### 3. [Content Caching Strategy](./content-caching-strategy.md)

**Purpose**: Detailed caching strategy that enables content reuse while maintaining personalization.

**Key Topics**:
- Composite cache key: `topic_id + grade_level + selected_interest`
- Cache lookup flow: Check before generation, store after generation
- Interest selection: LLM picks single best interest per topic
- Database schema: `content_metadata` table with composite index
- Cache metrics: Hit rate, interest distribution, grade-level patterns
- Content lifecycle: Cold start → Cache hit → Mature state
- Cost optimization: Generate once, serve to many students
- Trade-offs: Storage cost vs generation cost savings

**When to Reference**:
- Implementing content caching logic
- Optimizing generation costs
- Understanding cache key design
- Monitoring cache performance
- Debugging cache miss issues

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  - Student query input                                           │
│  - Progress tracking with polling                                │
│  - Video player                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ HTTPS (JWT Auth)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   API GATEWAY (Cloud Run)                        │
│  POST /api/v1/content/generate                                   │
│    → Create ContentRequest                                       │
│    → Publish to Pub/Sub                                          │
│    → Return 202 Accepted                                         │
│                                                                  │
│  GET /api/v1/content/request/{id}/status                        │
│    → Query ContentRequest table                                  │
│    → Return status + progress                                    │
└────────┬────────────────────────────────┬────────────────────────┘
         │                                │
         │ Pub/Sub Publish                │ PostgreSQL
         ▼                                ▼
┌─────────────────────┐          ┌──────────────────────┐
│  Google Cloud       │          │  Cloud SQL           │
│  Pub/Sub            │          │  (PostgreSQL)        │
│                     │          │                      │
│  Topic: content-    │          │  Tables:             │
│    requests-dev     │          │  - content_requests  │
│  Subscription:      │          │  - content_metadata  │
│    content-worker-  │          │  - topics            │
│    sub-dev          │          │  - users             │
│                     │          │  - interests         │
│  DLQ: content-      │          │  - student_progress  │
│    requests-dlq-dev │          │                      │
└────────┬────────────┘          └──────────▲───────────┘
         │                                  │
         │ Streaming Pull                   │ Update status
         ▼                                  │
┌─────────────────────────────────────────┴────────────────┐
│              CONTENT WORKER (Cloud Run Job)              │
│  app/workers/content_worker.py                           │
│                                                           │
│  Message Processing:                                     │
│  1. Validate message                                     │
│  2. Update status: validating (5%)                       │
│  3. Update status: generating (10%)                      │
│  4. Run AI pipeline ↓                                    │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ AI Pipeline
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AI CONTENT PIPELINE                           │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. NLU Service (app/services/nlu_service.py)         │      │
│  │    → Extract topic intent, key concepts              │      │
│  └─────────────────────┬─────────────────────────────────┘      │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 2. RAG Service (app/services/rag_service.py)         │      │
│  │    → Semantic search in vector DB                    │      │
│  │    → Retrieve relevant educational content           │      │
│  └─────────────────────┬─────────────────────────────────┘      │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 3. Script Generation (Gemini 1.5 Pro)                │      │
│  │    → Select best interest for topic                  │      │
│  │    → Generate personalized script                    │      │
│  └─────────────────────┬─────────────────────────────────┘      │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 4. Text-to-Speech (Google Cloud TTS)                 │      │
│  │    → Convert script to natural narration             │      │
│  └─────────────────────┬─────────────────────────────────┘      │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 5. Video Rendering (app/services/video_service.py)   │      │
│  │    → Combine audio + visuals                         │      │
│  │    → Add captions, diagrams                          │      │
│  └─────────────────────┬─────────────────────────────────┘      │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 6. Upload to GCS                                      │      │
│  │    → Store video, audio, thumbnail                   │      │
│  │    → Generate signed URLs                            │      │
│  └─────────────────────┬─────────────────────────────────┘      │
│                        ▼                                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 7. Cache in Database                                  │      │
│  │    → Store in content_metadata table                 │      │
│  │    → Enable reuse across students                    │      │
│  └───────────────────────────────────────────────────────┘      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Async Processing with Pub/Sub

**Decision**: Use Google Cloud Pub/Sub for async content generation instead of synchronous API calls.

**Rationale**:
- Video generation takes 5-15 minutes, exceeds Cloud Run 60s timeout
- Decouples API from long-running tasks
- Enables horizontal scaling of workers
- Provides built-in retry and error handling
- Allows frontend to poll for progress updates

**Trade-offs**:
- Added complexity: Pub/Sub setup, worker deployment, status polling
- Eventual consistency: Results not immediately available
- Benefits: No timeouts, better UX with progress tracking, cost-efficient

### 2. LLM-Based Interest Selection

**Decision**: Pass ALL student interests to LLM, let it select the single best interest for each topic.

**Rationale**:
- LLM has context awareness: Can pick most natural connection
- Enables content caching: Same content for students with same interest
- Better quality: Human-like judgment vs rigid rules
- Flexibility: Works across diverse topics and interests

**Alternative Considered**: Keyword matching or embedding similarity
**Why Rejected**: Less contextual awareness, harder to maintain rules

### 3. Composite Cache Key: Topic + Grade + Interest

**Decision**: Cache content by `(topic_id, grade_level, selected_interest)` composite key.

**Rationale**:
- Balances personalization with reuse
- Grade-appropriate content (same topic, different complexity)
- Interest-based personalization (basketball vs music examples)
- Enables sharing across students with matching criteria

**Trade-offs**:
- Storage: Multiple variants per topic (~5-7 interests × 4 grades = 20-30 variants)
- Cache hit rate: Improves over time as popular combinations are generated
- Cost: Storage cost < Generation cost savings

### 4. Request Tracking with ContentRequest Table

**Decision**: Create `content_requests` table to track async job progress.

**Rationale**:
- Provides single source of truth for request status
- Enables status polling without querying worker directly
- Persists results even if worker restarts
- Supports audit trail and analytics

**Alternative Considered**: Store state in Pub/Sub message attributes
**Why Rejected**: Limited visibility, no query capability, lost on DLQ

## Common Workflows

### Workflow 1: Generate New Content (Happy Path)

1. Student submits query via frontend
2. API creates `ContentRequest` (status: pending)
3. API publishes message to Pub/Sub topic
4. API returns 202 Accepted with `request_id`
5. Frontend starts polling `GET /request/{id}/status` every 3 seconds
6. Worker receives message via streaming pull
7. Worker updates status to "validating" (5%)
8. Worker updates status to "generating" (10%)
9. Worker runs AI pipeline: NLU → RAG → Script → TTS → Video
10. Worker updates status to "uploading" (90%)
11. Worker stores results in `content_requests` table
12. Worker updates status to "completed" (100%)
13. Worker acks message (removes from queue)
14. Frontend receives completed status with `video_url`
15. Frontend displays video player

### Workflow 2: Generate Content with Cache Hit

1. Student submits query via frontend
2. API creates `ContentRequest` (status: pending)
3. API publishes message to Pub/Sub
4. Worker receives message
5. Worker checks cache: Query `content_metadata` for matching `(topic_id, grade_level, ANY(student_interests))`
6. **Cache hit**: Found existing content with matching interest
7. Worker immediately sets results from cache
8. Worker updates status to "completed (cache hit)" (100%)
9. Worker acks message
10. Total time: < 5 seconds vs 5-15 minutes

### Workflow 3: Handle Failed Generation

1. Worker receives message
2. Worker starts processing (status: generating)
3. **Error occurs**: Gemini API quota exceeded
4. Worker logs error with correlation_id
5. Worker updates `content_requests` with error details
6. Worker updates status to "failed"
7. Worker returns False (nacks message)
8. Pub/Sub retries with exponential backoff (10s → 20s → 40s → ...)
9. After 10 failed attempts, message sent to Dead Letter Queue
10. Alert triggered for DLQ messages
11. Engineer investigates and fixes root cause

### Workflow 4: Monitor System Health

```bash
# Check Pub/Sub subscription backlog
gcloud pubsub subscriptions describe content-worker-sub-dev \
  --format="value(numUndeliveredMessages)"

# Check DLQ for failed messages
gcloud pubsub subscriptions pull content-requests-dlq-dev-sub \
  --limit=10 --format=json

# Query database for failed requests
psql -c "SELECT * FROM content_requests WHERE status='failed' ORDER BY created_at DESC LIMIT 10"

# Check worker logs
gcloud logging read "resource.type=cloud_run_job AND jsonPayload.worker=content_worker" \
  --limit=50 --format=json

# View cache hit rate
psql -c "
  SELECT
    COUNT(*) FILTER (WHERE current_stage LIKE '%cache hit%') * 100.0 / COUNT(*) as cache_hit_rate_pct
  FROM content_requests
  WHERE status = 'completed'
  AND created_at > NOW() - INTERVAL '7 days'
"
```

## Infrastructure Components

### Google Cloud Platform

**Project**: `vividly-dev-rich` (dev environment)

**Regions**: `us-central1` (primary)

**Services Used**:
- **Cloud Run**: API Gateway (always-on service)
- **Cloud Run Jobs**: Content Worker (on-demand processing)
- **Cloud SQL**: PostgreSQL database (persistent storage)
- **Cloud Storage**: GCS buckets (video/audio storage)
- **Pub/Sub**: Message queue (async processing)
- **Cloud Build**: CI/CD pipelines
- **Artifact Registry**: Docker image storage
- **Secret Manager**: API keys and credentials
- **Cloud Logging**: Centralized logging
- **Cloud Monitoring**: Metrics and alerting

### Terraform Infrastructure (`/terraform`)

**Main Files**:
- `main.tf`: Core infrastructure (Cloud SQL, GCS buckets, service accounts)
- `pubsub.tf`: Pub/Sub topics and subscriptions
- `cloud_run.tf`: Cloud Run services and jobs
- `variables.tf`: Environment-specific variables
- `environments/dev.tfvars`: Dev environment configuration

**Deployment**:
```bash
cd terraform
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

## Database Schema

### Core Tables

**users**: Student and teacher accounts
- `user_id` (UUID, PK)
- `email`, `full_name`, `role`
- `grade_level` (for students)

**interests**: Available interests for personalization
- `interest_id` (UUID, PK)
- `name`, `description`, `category`

**student_interests**: Many-to-many relationship
- `student_id` (FK → users)
- `interest_id` (FK → interests)

**topics**: Educational curriculum structure
- `topic_id` (String, PK)
- `name`, `subject`, `grade_level`
- Hierarchical: subject → chapter → section

**content_requests**: Async job tracking (NEW)
- `id` (UUID, PK)
- `correlation_id` (String, unique)
- `student_id`, `topic`, `grade_level`
- `status`, `progress_percentage`, `current_stage`
- `video_url`, `script_text`, `thumbnail_url` (results)
- `error_message`, `error_stage` (if failed)
- Timestamps: `created_at`, `started_at`, `completed_at`, `failed_at`

**content_metadata**: Content cache
- `content_id` (UUID, PK)
- `topic_id` (FK → topics)
- `grade_level` (Integer) - **TO BE ADDED**
- `interest_id` (FK → interests)
- `video_url`, `audio_url`, `script_content`
- `view_count`, `completion_count`

**student_progress**: Watch tracking
- `progress_id` (UUID, PK)
- `student_id`, `content_id`
- `watch_percentage`, `completed`

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- Google Cloud SDK (`gcloud`)
- Terraform
- PostgreSQL (for local development)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/vividly"
export SECRET_KEY="your-secret-key"
export GEMINI_API_KEY="your-gemini-key"
export GCP_PROJECT_ID="vividly-dev-rich"
export ENVIRONMENT="dev"

# Run database migrations
alembic upgrade head

# Start API server (local dev)
uvicorn app.main:app --reload --port 8000

# Run Content Worker (local dev)
python -m app.workers.content_worker
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export VITE_API_URL="http://localhost:8000"

# Start dev server
npm run dev
```

### Testing

```bash
# Backend unit tests
cd backend
pytest tests/ -v

# Backend integration tests
pytest tests/integration/ -v

# Security tests
./scripts/run-security-tests.sh

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Monitoring & Alerting

### Key Metrics to Monitor

**API Gateway**:
- Request latency (p50, p95, p99)
- Error rate (5xx responses)
- 202 Accepted rate for `/generate` endpoint

**Pub/Sub**:
- Subscription backlog (undelivered messages)
- Oldest unacked message age
- DLQ message count
- Publish success rate

**Content Worker**:
- Message processing time (avg, p95)
- Success rate (completed / total)
- Ack rate vs nack rate
- Concurrent message processing count

**Database**:
- Connection pool utilization
- Query latency
- ContentRequest creation rate
- Status distribution (pending/generating/completed/failed)

**GCS**:
- Storage usage
- Egress bandwidth (signed URL downloads)

### Alerts

**Critical**:
- DLQ message count > 10
- Worker failure rate > 10% for 5 minutes
- API error rate > 5% for 3 minutes
- Database connection pool exhausted

**Warning**:
- Pub/Sub backlog > 100 messages for 10 minutes
- Oldest unacked message > 15 minutes
- Cache hit rate < 30% (after initial ramp-up)

## Security

### Authentication

**JWT Tokens**: API Gateway validates JWT tokens for all endpoints
- Token generation: `/api/v1/auth/login`
- Token validation: `app/core/auth.py`
- Role-based access: Student, Teacher, Admin

### Authorization

**Resource Access**: Students can only access their own content
```python
# Example: Status endpoint
if current_user.role == "student":
    if content_request.student_id != current_user.user_id:
        raise HTTPException(status_code=403)
```

### Data Privacy

**PII Protection**:
- Student queries and videos stored securely in GCS
- Database connections encrypted (Cloud SQL Proxy)
- Signed URLs with expiration for video access
- No PII in Pub/Sub messages (only IDs)

**GCP IAM**:
- Principle of least privilege
- Service accounts per component (API Gateway, Worker)
- IAM roles: Publisher (API), Subscriber (Worker)

## Troubleshooting

### Issue: Content generation timeout

**Symptom**: API returns 504 Gateway Timeout

**Solution**: This should not happen with async architecture. If it does:
1. Check if Pub/Sub publish succeeded
2. Verify ContentRequest was created in database
3. Check worker logs for processing errors

### Issue: Worker not processing messages

**Symptom**: Pub/Sub backlog increasing, no completed requests

**Checks**:
```bash
# Is worker running?
gcloud run jobs executions list --job=dev-vividly-content-worker

# Check worker logs
gcloud logging read "resource.type=cloud_run_job" --limit=50

# Check subscription backlog
gcloud pubsub subscriptions describe content-worker-sub-dev
```

**Solutions**:
- Restart worker: `gcloud run jobs execute dev-vividly-content-worker`
- Check IAM permissions: Worker needs `roles/pubsub.subscriber`
- Check database connectivity: Worker needs Cloud SQL connection

### Issue: All requests failing with same error

**Symptom**: High failure rate, similar error messages in logs

**Common Causes**:
- **Gemini API quota exceeded**: Increase quota or implement rate limiting
- **GCS permission denied**: Check service account IAM roles
- **Database connection pool exhausted**: Increase max connections

**Investigation**:
```bash
# Check error patterns
gcloud logging read "severity>=ERROR AND jsonPayload.worker=content_worker" \
  --limit=50 --format=json | jq '.[] | .jsonPayload.error_message' | sort | uniq -c

# Check DLQ
gcloud pubsub subscriptions pull content-requests-dlq-dev-sub --limit=10
```

### Issue: Low cache hit rate

**Symptom**: Cache hit rate < 30% after weeks of usage

**Checks**:
```sql
-- Check cache hit rate
SELECT
  COUNT(*) FILTER (WHERE current_stage LIKE '%cache%') * 100.0 / COUNT(*) as cache_hit_rate_pct
FROM content_requests
WHERE status = 'completed' AND created_at > NOW() - INTERVAL '7 days';

-- Check interest distribution
SELECT interest_id, COUNT(*) as variant_count
FROM content_metadata
GROUP BY interest_id
ORDER BY variant_count DESC;
```

**Solutions**:
- Ensure `grade_level` is set in `content_metadata` table
- Verify cache lookup logic includes student interests
- Check if interest selection is working (not always picking same interest)

## Contributing

### Code Review Checklist

- [ ] All tests passing
- [ ] Type hints added for new functions
- [ ] Docstrings for public APIs
- [ ] Error handling with proper logging
- [ ] Security review (no PII in logs, proper auth)
- [ ] Performance impact assessed
- [ ] Documentation updated

### Architecture Decision Process

1. **Identify Problem**: What are we solving?
2. **Research Options**: Survey existing patterns, libraries
3. **Evaluate Trade-offs**: Cost, complexity, maintainability
4. **Document Decision**: Update architecture docs
5. **Implement**: Build with monitoring and testing
6. **Measure**: Track metrics, validate assumptions

## Support

### Internal Documentation

- Architecture docs: `.claude/`
- API docs: `backend/docs/`
- Database migrations: `backend/alembic/versions/`
- Terraform docs: `terraform/README.md`

### External Resources

- Google Cloud Pub/Sub: https://cloud.google.com/pubsub/docs
- Cloud Run: https://cloud.google.com/run/docs
- FastAPI: https://fastapi.tiangolo.com/
- Gemini API: https://ai.google.dev/docs

## Last Updated

2025-11-01
