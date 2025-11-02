# Async Content Generation Architecture

## Overview

This document describes the asynchronous content generation architecture implemented using Google Cloud Pub/Sub. This architecture decouples long-running video generation tasks (5-15 minutes) from API requests, preventing timeout errors and enabling horizontal scaling.

## Problem Statement

**Original Issue**: The `/api/v1/content/generate` endpoint called the content generation pipeline synchronously. Since video generation takes 5-15 minutes and Cloud Run has a 60-second request timeout, all content generation requests failed.

**Solution**: Transform to async architecture where:
- API creates tracking record and publishes to Pub/Sub (< 1 second)
- Returns 202 Accepted immediately with `request_id`
- Worker processes asynchronously in background
- Frontend polls status endpoint for real-time progress updates

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       │ POST /api/v1/content/generate
       │ {student_query, grade_level, interest}
       ▼
┌──────────────────────────────────────────────────────────────┐
│  API Gateway (Cloud Run)                                     │
│  app/api/v1/endpoints/content.py:generate_content()         │
│                                                              │
│  1. Create ContentRequest record (status: pending)          │
│  2. Publish message to Pub/Sub                              │
│  3. Return 202 Accepted with request_id                     │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Pub/Sub Message: {request_id, student_query, ...}
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Google Cloud Pub/Sub                                        │
│  Topic: content-requests-{environment}                       │
│  Subscription: content-worker-sub-{environment}              │
│                                                              │
│  - Message retention: 7 days                                │
│  - Ack deadline: 10 minutes                                 │
│  - Max delivery attempts: 10                                │
│  - Exactly-once delivery enabled                            │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Streaming Pull (max 10 concurrent)
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Content Worker (Cloud Run Job)                             │
│  app/workers/content_worker.py                               │
│                                                              │
│  1. Receive message from Pub/Sub                            │
│  2. Update status: validating (5%)                          │
│  3. Update status: generating (10%)                         │
│  4. Run AI pipeline: NLU → RAG → Script → TTS → Video      │
│  5. Update status: uploading (90%)                          │
│  6. Store results in ContentRequest table                   │
│  7. Update status: completed (100%)                         │
│  8. Ack message (success) or Nack (retry)                   │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ DB Updates
       ▼
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL (Cloud SQL)                                      │
│  Table: content_requests                                     │
│                                                              │
│  - request_id (UUID, PK)                                    │
│  - status (pending/validating/generating/completed/failed)  │
│  - progress_percentage (0-100)                              │
│  - current_stage (description)                              │
│  - video_url, script_text, thumbnail_url (results)         │
│  - error_message, error_stage (if failed)                   │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ Poll every 3 seconds
       ▲
┌──────┴──────┐
│   Frontend  │  GET /api/v1/content/request/{request_id}/status
│   Polling   │  → {status, progress_percentage, current_stage, ...}
└─────────────┘
```

## Data Flow Sequence

### 1. API Request (< 1 second)

**Endpoint**: `POST /api/v1/content/generate`

**Request Body**:
```json
{
  "student_id": "student_123",
  "student_query": "Explain Newton's Third Law with basketball",
  "grade_level": 10,
  "interest": "basketball"
}
```

**API Logic** (`app/api/v1/endpoints/content.py:698-865`):
```python
@router.post("/generate", response_model=ContentGenerationResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def generate_content(request, current_user, db):
    # Generate correlation ID for distributed tracing
    correlation_id = f"req_{uuid.uuid4().hex[:16]}"

    # Interest matching (if not provided)
    interest_to_use = request.interest
    if not interest_to_use and current_user.role == "student":
        interest_match = await interest_service.match_interest_to_request(...)
        interest_to_use = interest_match.get("interest_name")

    # 1. Create ContentRequest record
    content_req_service = ContentRequestService()
    content_request = content_req_service.create_request(
        db=db,
        student_id=request.student_id,
        topic=request.student_query,
        grade_level=str(request.grade_level),
        correlation_id=correlation_id
    )

    # 2. Publish to Pub/Sub
    pubsub_service = get_pubsub_service()
    publish_result = await pubsub_service.publish_content_request(
        request_id=str(content_request.id),
        correlation_id=correlation_id,
        student_id=request.student_id,
        student_query=request.student_query,
        grade_level=request.grade_level,
        interest=interest_to_use
    )

    # 3. Return 202 Accepted immediately
    return ContentGenerationResponse(
        status="pending",
        request_id=str(content_request.id),
        correlation_id=correlation_id,
        message="Content generation started. Poll /api/v1/content/request/{request_id}/status for progress.",
        estimated_completion_seconds=180  # 3 minutes
    )
```

**Response** (202 Accepted):
```json
{
  "status": "pending",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req_abc123def456",
  "message": "Content generation started. Poll /api/v1/content/request/{request_id}/status for progress.",
  "estimated_completion_seconds": 180
}
```

### 2. Pub/Sub Message Publishing

**Service**: `app/services/pubsub_service.py`

**Message Format**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req_abc123def456",
  "student_id": "student_123",
  "student_query": "Explain Newton's Third Law with basketball",
  "grade_level": 10,
  "interest": "basketball",
  "environment": "dev"
}
```

**Message Attributes** (for filtering/routing):
```python
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "student_id": "student_123",
    "environment": "dev"
}
```

**Pub/Sub Configuration** (`terraform/pubsub.tf`):
- **Topic**: `content-requests-{environment}`
- **Subscription**: `content-worker-sub-{environment}`
- **Ack Deadline**: 600 seconds (10 minutes)
- **Retry Policy**: Exponential backoff (10s to 10min)
- **Dead Letter Queue**: After 10 failed attempts → `content-requests-dlq-{environment}`
- **Exactly-Once Delivery**: Enabled (prevents duplicate processing)
- **Message Ordering**: Enabled (preserve order for same student_id)

### 3. Content Worker Processing (5-15 minutes)

**Worker**: `app/workers/content_worker.py`

**Initialization**:
```python
class ContentWorker:
    def __init__(self):
        # Services
        self.content_service = ContentGenerationService()
        self.request_service = ContentRequestService()

        # Database
        engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=engine)

        # Pub/Sub subscriber
        self.project_id = os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.subscription_name = f"content-worker-sub-{self.environment}"
        self.subscription_path = f"projects/{self.project_id}/subscriptions/{self.subscription_name}"
        self.subscriber = pubsub_v1.SubscriberClient()
```

**Message Processing Flow**:
```python
async def process_message(self, message: pubsub_v1.types.PubsubMessage, db: Session) -> bool:
    # Parse message
    message_data = json.loads(message.data.decode("utf-8"))
    request_id = message_data.get("request_id")

    # Validate required fields
    required_fields = ["request_id", "student_id", "student_query", "grade_level"]
    missing_fields = [f for f in required_fields if not message_data.get(f)]
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        return False  # Don't retry, send to DLQ

    # Stage 1: Validating (5%)
    self.request_service.update_status(
        db=db, request_id=request_id, status="validating",
        progress_percentage=5, current_stage="Validating request parameters"
    )

    # Stage 2: Generating (10%)
    self.request_service.update_status(
        db=db, request_id=request_id, status="generating",
        progress_percentage=10, current_stage="Starting content generation pipeline"
    )

    # Stage 3: AI Pipeline (10% → 90%)
    # This is the long-running part: NLU → RAG → Script → TTS → Video
    result = await self.content_service.generate_content_from_query(
        student_query=message_data["student_query"],
        student_id=message_data["student_id"],
        grade_level=message_data["grade_level"],
        interest=message_data.get("interest")
    )

    # Stage 4: Uploading (90%)
    self.request_service.update_status(
        db=db, request_id=request_id, progress_percentage=90,
        current_stage="Finalizing video and uploading to storage"
    )

    # Stage 5: Complete (100%)
    if result.get("status") == "completed":
        self.request_service.set_results(
            db=db, request_id=request_id,
            video_url=result.get("video_url"),
            script_text=result.get("script_text", ""),
            thumbnail_url=result.get("thumbnail_url")
        )
        self.request_service.update_status(
            db=db, request_id=request_id, status="completed",
            progress_percentage=100, current_stage="Complete"
        )
        return True  # Success - ack message
    else:
        # Handle errors
        self.request_service.set_error(...)
        return False  # Failure - nack for retry
```

**Ack/Nack Logic**:
```python
def message_callback(self, message: pubsub_v1.types.PubsubMessage):
    db = None
    try:
        db = self.SessionLocal()  # Thread-safe DB session
        success = asyncio.run(self.process_message(message, db))

        if success:
            message.ack()  # Success - remove from queue
            logger.info(f"Message acknowledged: {message.message_id}")
        else:
            message.nack()  # Failure - retry with exponential backoff
            logger.warning(f"Message nacked for retry: {message.message_id}")
    except Exception as e:
        logger.error(f"Callback failed: {e}", exc_info=True)
        message.nack()  # Retry on any error
    finally:
        if db:
            db.close()
```

**Streaming Pull**:
```python
def run(self):
    # Configure flow control
    flow_control = pubsub_v1.types.FlowControl(
        max_messages=10,  # Process up to 10 messages concurrently
        max_bytes=10 * 1024 * 1024  # 10 MB
    )

    # Start streaming pull (blocking call)
    streaming_pull_future = self.subscriber.subscribe(
        self.subscription_path,
        callback=self.message_callback,
        flow_control=flow_control
    )

    logger.info("Worker is listening for messages...")
    streaming_pull_future.result()  # Block until shutdown
```

### 4. Status Polling (Frontend)

**Endpoint**: `GET /api/v1/content/request/{request_id}/status`

**Polling Strategy**:
- Poll every 3 seconds
- Stop polling when status is "completed" or "failed"
- Show progress bar with `progress_percentage` (0-100)
- Display `current_stage` description

**API Logic** (`app/api/v1/endpoints/content.py:875-995`):
```python
@router.get("/request/{request_id}/status", response_model=dict)
async def get_request_status(request_id, current_user, db):
    content_req_service = ContentRequestService()
    status_data = content_req_service.get_request_status(db, request_id)

    if not status_data:
        raise HTTPException(status_code=404, detail="Request not found")

    # Authorization check
    content_request = content_req_service.get_request_by_id(db, request_id)
    if current_user.role == "student":
        if str(content_request.student_id) != str(current_user.user_id):
            raise HTTPException(status_code=403, detail="Not authorized")

    return status_data
```

**Response Examples**:

**Pending State**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req_abc123def456",
  "status": "pending",
  "progress_percentage": 0,
  "current_stage": null,
  "created_at": "2025-11-01T12:00:00Z",
  "started_at": null,
  "completed_at": null
}
```

**Generating State**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req_abc123def456",
  "status": "generating",
  "progress_percentage": 45,
  "current_stage": "Generating video from script and audio",
  "created_at": "2025-11-01T12:00:00Z",
  "started_at": "2025-11-01T12:00:01Z",
  "completed_at": null
}
```

**Completed State**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req_abc123def456",
  "status": "completed",
  "progress_percentage": 100,
  "current_stage": "Complete",
  "created_at": "2025-11-01T12:00:00Z",
  "started_at": "2025-11-01T12:00:01Z",
  "completed_at": "2025-11-01T12:03:45Z",
  "video_url": "gs://vividly-dev-rich-dev-generated-content/videos/550e8400-e29b-41d4-a716-446655440000.mp4",
  "script_text": "Imagine you're shooting a basketball...",
  "thumbnail_url": "gs://vividly-dev-rich-dev-generated-content/thumbnails/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

**Failed State**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "req_abc123def456",
  "status": "failed",
  "progress_percentage": 35,
  "current_stage": "Generating script with Gemini",
  "created_at": "2025-11-01T12:00:00Z",
  "started_at": "2025-11-01T12:00:01Z",
  "completed_at": null,
  "failed_at": "2025-11-01T12:02:30Z",
  "error_message": "Gemini API quota exceeded",
  "error_stage": "script_generation",
  "error_details": {
    "exception_type": "QuotaExceededError",
    "correlation_id": "req_abc123def456"
  }
}
```

## Database Schema

### content_requests Table

**Purpose**: Track async content generation requests and their progress.

**Schema** (`app/models/request_tracking.py`):
```python
class ContentRequest(Base):
    __tablename__ = "content_requests"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Tracing
    correlation_id = Column(String(64), unique=True, index=True)

    # Request details
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    topic = Column(Text, nullable=False)  # Student's query
    learning_objective = Column(Text)
    grade_level = Column(String(10), nullable=False)
    duration_minutes = Column(Integer, default=3)

    # Status tracking
    status = Column(String(50), nullable=False, index=True)
    # Valid statuses: pending, validating, generating, completed, failed

    progress_percentage = Column(Integer, default=0)  # 0-100
    current_stage = Column(String(255))  # Human-readable stage description

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))

    # Results (populated on completion)
    video_url = Column(String(2048))
    script_text = Column(Text)
    thumbnail_url = Column(String(2048))

    # Error tracking
    error_message = Column(Text)
    error_stage = Column(String(100))
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)
```

**Indexes**:
```sql
CREATE INDEX idx_content_requests_status ON content_requests(status);
CREATE INDEX idx_content_requests_correlation_id ON content_requests(correlation_id);
CREATE INDEX idx_content_requests_student_id ON content_requests(student_id);
CREATE INDEX idx_content_requests_created_at ON content_requests(created_at DESC);
```

## Key Services

### 1. PubSubService (`app/services/pubsub_service.py`)

**Purpose**: Publish content generation requests to Pub/Sub.

**Key Methods**:
```python
class PubSubService:
    async def publish_content_request(
        self, request_id, correlation_id, student_id,
        student_query, grade_level, interest=None
    ) -> Dict[str, Any]:
        """Publish content request to Pub/Sub topic."""
        pass

    def health_check(self) -> Dict[str, Any]:
        """Check if Pub/Sub service is healthy."""
        pass
```

### 2. ContentRequestService (`app/services/content_request_service.py`)

**Purpose**: CRUD operations for ContentRequest table.

**Key Methods**:
```python
class ContentRequestService:
    @staticmethod
    def create_request(db, student_id, topic, grade_level, ...) -> ContentRequest:
        """Create new content generation request."""
        pass

    @staticmethod
    def update_status(db, request_id, status, progress_percentage, current_stage) -> bool:
        """Update request status and progress."""
        pass

    @staticmethod
    def set_results(db, request_id, video_url, script_text, thumbnail_url) -> bool:
        """Set result URLs for completed request."""
        pass

    @staticmethod
    def set_error(db, request_id, error_message, error_stage, error_details) -> bool:
        """Set error information for failed request."""
        pass

    @staticmethod
    def get_request_status(db, request_id) -> Optional[Dict[str, Any]]:
        """Get request status for API response."""
        pass
```

## Error Handling & Retry Logic

### Retry Strategy

**Pub/Sub Retry Policy** (`terraform/pubsub.tf`):
```terraform
retry_policy {
  minimum_backoff = "10s"     # Start with 10 seconds
  maximum_backoff = "600s"    # Cap at 10 minutes
}

dead_letter_policy {
  dead_letter_topic = google_pubsub_topic.content_requests_dlq.id
  max_delivery_attempts = 10  # After 10 retries, send to DLQ
}
```

**Exponential Backoff Calculation**:
```
Attempt 1: 10 seconds
Attempt 2: 20 seconds
Attempt 3: 40 seconds
Attempt 4: 80 seconds
Attempt 5: 160 seconds (2.67 minutes)
Attempt 6: 320 seconds (5.33 minutes)
Attempt 7: 600 seconds (10 minutes, capped)
Attempt 8: 600 seconds
Attempt 9: 600 seconds
Attempt 10: 600 seconds
→ Send to Dead Letter Queue
```

### Error Categories

**1. Non-Retryable Errors** (send to DLQ immediately):
- Invalid JSON in message
- Missing required fields
- Malformed request_id

**Worker Logic**:
```python
# JSON decode error
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in message: {e}")
    return False  # Don't retry - send to DLQ

# Missing fields
if missing_fields:
    logger.error(f"Missing required fields: {missing_fields}")
    return False  # Don't retry - send to DLQ
```

**2. Retryable Errors** (retry with exponential backoff):
- Gemini API errors (quota, rate limit)
- TTS API errors
- Video rendering failures
- Network timeouts
- Database connection errors

**Worker Logic**:
```python
except Exception as e:
    logger.error(f"Request {request_id} failed: {e}", exc_info=True)
    self.request_service.set_error(
        db=db, request_id=request_id,
        error_message=str(e), error_stage="content_generation"
    )
    return False  # Retry with exponential backoff
```

### Dead Letter Queue Monitoring

**DLQ Topic**: `content-requests-dlq-{environment}`

**Purpose**: Messages that fail after 10 retry attempts.

**Monitoring**:
```bash
# View messages in DLQ
gcloud pubsub subscriptions pull content-requests-dlq-dev-sub \
  --limit=10 \
  --format=json

# Alert if DLQ has > 10 messages
```

**Investigation Process**:
1. Pull messages from DLQ
2. Analyze error patterns
3. Fix root cause (code bug, API quota, etc.)
4. Manually re-publish to main topic if recoverable

## Infrastructure (Terraform)

### Pub/Sub Resources (`terraform/pubsub.tf`)

**1. Main Topic**:
```terraform
resource "google_pubsub_topic" "content_requests" {
  name = "content-requests-${var.environment}"
  message_retention_duration = "604800s"  # 7 days
}
```

**2. Dead Letter Queue Topic**:
```terraform
resource "google_pubsub_topic" "content_requests_dlq" {
  name = "content-requests-dlq-${var.environment}"
  message_retention_duration = "604800s"  # 7 days
}
```

**3. Subscription**:
```terraform
resource "google_pubsub_subscription" "content_worker" {
  name  = "content-worker-sub-${var.environment}"
  topic = google_pubsub_topic.content_requests.name

  ack_deadline_seconds = 600  # 10 minutes
  message_retention_duration = "604800s"  # 7 days

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic = google_pubsub_topic.content_requests_dlq.id
    max_delivery_attempts = 10
  }

  enable_exactly_once_delivery = true
  enable_message_ordering = true

  filter = "attributes.environment = \"${var.environment}\""
}
```

**4. IAM Permissions**:
```terraform
# API gateway can publish
resource "google_pubsub_topic_iam_member" "api_publisher" {
  topic  = google_pubsub_topic.content_requests.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.api_gateway.email}"
}

# Content worker can subscribe
resource "google_pubsub_subscription_iam_member" "content_worker_subscriber" {
  subscription = google_pubsub_subscription.content_worker.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.content_worker.email}"
}
```

## Deployment

### 1. API Gateway (Cloud Run Service)

**Dockerfile**: `Dockerfile`

**Environment Variables**:
```bash
DATABASE_URL=postgresql://...
GCP_PROJECT_ID=vividly-dev-rich
ENVIRONMENT=dev
SECRET_KEY=...
GEMINI_API_KEY=...
```

**Deploy**:
```bash
gcloud run deploy dev-vividly-api \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/backend-api:latest \
  --region=us-central1 \
  --service-account=api-gateway@vividly-dev-rich.iam.gserviceaccount.com
```

### 2. Content Worker (Cloud Run Job)

**Dockerfile**: `Dockerfile.content-worker`

**Environment Variables**:
```bash
DATABASE_URL=postgresql://...
GCP_PROJECT_ID=vividly-dev-rich
ENVIRONMENT=dev
GEMINI_API_KEY=...
GCS_BUCKET_GENERATED_CONTENT=vividly-dev-rich-dev-generated-content
```

**Deploy**:
```bash
# Build and push image
docker build -t us-central1-docker.pkg.dev/vividly-dev-rich/vividly/content-worker:latest \
  -f Dockerfile.content-worker .
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/content-worker:latest

# Create/update Cloud Run Job
gcloud run jobs create dev-vividly-content-worker \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/content-worker:latest \
  --region=us-central1 \
  --service-account=content-worker@vividly-dev-rich.iam.gserviceaccount.com \
  --max-retries=3 \
  --task-timeout=15m
```

**Run Worker**:
```bash
# Execute job (long-running subscriber)
gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 \
  --wait
```

## Monitoring & Observability

### Key Metrics

**1. API Metrics**:
- `/generate` endpoint latency (should be < 1 second)
- 202 response rate (should be 100%)
- Pub/Sub publish success rate

**2. Pub/Sub Metrics**:
- Oldest unacked message age (alert if > 15 minutes)
- Undelivered message count (alert if > 50)
- DLQ message count (alert if > 10)
- Subscription backlog (alert if > 100)

**3. Worker Metrics**:
- Message processing time (avg: 3-5 minutes)
- Success rate (target: > 95%)
- Ack rate vs nack rate
- Concurrent message processing count

**4. Database Metrics**:
- ContentRequest creation rate
- Status distribution (pending/generating/completed/failed)
- Average time to completion
- Failed request rate

### Logging Strategy

**Correlation ID Tracing**:
```python
# API generates correlation_id
correlation_id = f"req_{uuid.uuid4().hex[:16]}"

# Pass to Pub/Sub message
message_data = {
    "request_id": request_id,
    "correlation_id": correlation_id,
    ...
}

# Worker logs with correlation_id
logger.info(f"Processing message: correlation_id={correlation_id}")
```

**Log Queries** (Cloud Logging):
```
# Trace single request end-to-end
jsonPayload.correlation_id="req_abc123def456"

# Find failed requests
jsonPayload.status="failed"
severity>=ERROR

# Find slow requests
jsonPayload.processing_time_seconds>300
```

### Alerts

**1. High Failure Rate**:
```
Condition: failed_requests / total_requests > 0.05 (5%) for 5 minutes
Action: Alert on-call engineer
```

**2. Pub/Sub Backlog**:
```
Condition: subscription_backlog > 100 messages for 10 minutes
Action: Scale up workers or investigate processing delays
```

**3. DLQ Messages**:
```
Condition: dlq_message_count > 10
Action: Investigate and fix root cause
```

## Performance Characteristics

### Latency

**API Response Time**: < 1 second
- Create DB record: ~50ms
- Publish to Pub/Sub: ~200ms
- Return 202 response: <1 second total

**Content Generation Time**: 3-15 minutes
- NLU + RAG: 10-30 seconds
- Script generation: 30-60 seconds
- TTS: 20-40 seconds
- Video rendering: 2-10 minutes
- Upload to GCS: 10-30 seconds

**Status Polling**: < 100ms
- Simple DB query with index
- No complex joins

### Throughput

**API Gateway**:
- Cloud Run autoscaling: 0-1000 instances
- Each instance: 80 concurrent requests
- Max throughput: ~80,000 requests/second
- Realistic load: 10-100 requests/second

**Content Worker**:
- Flow control: 10 concurrent messages per instance
- Processing time: 3-15 minutes per message
- Throughput per instance: 4-20 videos/hour
- Scale workers based on queue depth

**Example Scaling**:
```
Scenario: 100 concurrent content generation requests
- API handles 100 POST /generate in < 1 second
- Pub/Sub queues 100 messages
- Workers process 10 concurrent messages per instance
- Need: 10 worker instances (100 / 10)
- Total time: ~10 minutes for all 100 videos
```

## Cost Optimization

### 1. Pub/Sub Costs

**Pricing**:
- First 10 GB/month: Free
- Additional: $0.04/GB

**Typical Message Size**: ~1 KB (JSON payload)

**Monthly Cost Example** (1000 videos/day):
```
Messages: 1000 videos/day × 30 days = 30,000 messages/month
Size: 30,000 × 1 KB = 30 MB/month
Cost: Free (under 10 GB)
```

### 2. Cloud Run Costs

**API Gateway** (always running):
- Cost: Based on CPU/memory allocation and request count
- Autoscaling: 0-1000 instances based on traffic

**Content Worker** (on-demand):
- Cost: Based on execution time
- Optimization: Process multiple messages per instance (flow control)

**Cost Savings vs Synchronous**:
- Synchronous: API timeout after 60s, wasted compute
- Asynchronous: API responds in <1s, worker runs exactly as long as needed
- Savings: ~98% reduction in API compute costs

### 3. Database Costs

**Cloud SQL**: Based on instance size and storage

**Optimization**:
- Index on `(status, created_at)` for fast polling queries
- Archive old completed requests (> 30 days) to cold storage
- Clean up failed requests after investigation

## Security Considerations

### 1. Authentication & Authorization

**API Gateway**:
- JWT token authentication (app/core/auth.py)
- Role-based access control (student can only see their own requests)

**Status Endpoint Authorization**:
```python
# Check ownership
if current_user.role == "student":
    if str(content_request.student_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
```

### 2. Pub/Sub Security

**IAM Permissions**:
- API Gateway: `roles/pubsub.publisher` (can only publish)
- Content Worker: `roles/pubsub.subscriber` (can only subscribe)
- Principle of least privilege

**Message Filtering**:
```terraform
filter = "attributes.environment = \"${var.environment}\""
```
- Ensures dev/staging/prod isolation
- Prevents cross-environment message leakage

### 3. Data Privacy

**PII in Messages**:
- Avoid passing sensitive data in Pub/Sub messages
- Use `request_id` to look up data from database
- Encrypt database connections (Cloud SQL Proxy)

**GCS Security**:
- Generated videos stored in private GCS buckets
- Signed URLs for temporary access
- IAM roles for bucket access control

## Testing Strategy

### 1. Unit Tests

**Test ContentRequestService**:
```python
def test_create_request():
    """Test creating new content request."""
    pass

def test_update_status():
    """Test updating request status."""
    pass

def test_get_request_status():
    """Test retrieving request status."""
    pass
```

**Test PubSubService**:
```python
def test_publish_content_request(mock_publisher):
    """Test publishing message to Pub/Sub."""
    pass

def test_health_check():
    """Test Pub/Sub health check."""
    pass
```

### 2. Integration Tests

**Test End-to-End Flow**:
```python
@pytest.mark.integration
async def test_async_content_generation_flow():
    """Test complete async flow: API → Pub/Sub → Worker → DB."""
    # 1. POST /generate
    response = await client.post("/api/v1/content/generate", json={...})
    assert response.status_code == 202
    request_id = response.json()["request_id"]

    # 2. Poll status (wait for completion)
    for _ in range(60):  # Max 3 minutes
        status = await client.get(f"/api/v1/content/request/{request_id}/status")
        if status.json()["status"] == "completed":
            break
        await asyncio.sleep(3)

    # 3. Verify results
    assert status.json()["status"] == "completed"
    assert status.json()["video_url"] is not None
```

### 3. Load Tests

**Simulate High Traffic**:
```python
# Load test with Locust
class ContentGenerationUser(HttpUser):
    @task
    def generate_content(self):
        self.client.post("/api/v1/content/generate", json={
            "student_id": "test_student",
            "student_query": "Explain photosynthesis",
            "grade_level": 10
        })
```

**Metrics to Track**:
- API response time (should stay < 1 second)
- Pub/Sub publish success rate (should be 100%)
- Worker processing queue depth
- Database connection pool exhaustion

## Future Enhancements

### 1. Priority Queues

**Use Case**: Premium users get faster processing.

**Implementation**:
- Create separate subscriptions with different priorities
- Route premium requests to high-priority subscription
- Scale workers based on subscription backlog

### 2. Batch Processing

**Use Case**: Process multiple requests together to optimize costs.

**Implementation**:
- Batch similar requests (same topic + grade level)
- Generate content once, serve to multiple students
- Requires content caching strategy (see `.claude/content-caching-strategy.md`)

### 3. Progress Streaming (Server-Sent Events)

**Use Case**: Real-time progress updates without polling.

**Implementation**:
```python
@router.get("/request/{request_id}/stream")
async def stream_progress(request_id):
    async def event_generator():
        while True:
            status = get_request_status(request_id)
            yield f"data: {json.dumps(status)}\n\n"
            if status["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(3)

    return EventSourceResponse(event_generator())
```

### 4. Circuit Breaker

**Use Case**: Prevent cascading failures when external services (Gemini, TTS) are down.

**Implementation**:
- Track failure rate for external services
- If failure rate > 50% for 5 minutes, open circuit
- Return cached content or error immediately
- Close circuit after health check succeeds

## Related Documentation

- **RAG Pipeline**: `.claude/rag-pipeline-architecture.md`
- **Content Caching**: `.claude/content-caching-strategy.md`
- **Database Migrations**: `alembic/versions/`
- **Terraform Infrastructure**: `terraform/`

## Last Updated

2025-11-01
