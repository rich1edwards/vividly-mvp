# Vividly MVP Implementation Master Plan
**Created**: 2025-11-01
**Status**: Active Development
**Approach**: Andrew Ng Methodology - Build Right, Not Fast

---

## Table of Contents
1. [Architecture Philosophy](#architecture-philosophy)
2. [Content Worker Deployment](#content-worker-deployment)
3. [Content Request UI](#content-request-ui)
4. [Vertex AI Integration](#vertex-ai-integration)
5. [Video Status Polling](#video-status-polling)
6. [OER Content Ingestion](#oer-content-ingestion)
7. [UX Enhancements](#ux-enhancements)
8. [Implementation Timeline](#implementation-timeline)

---

## Architecture Philosophy

### Long-Term Design Principles
1. **Separation of Concerns**: API Gateway → Pub/Sub → Workers → Storage
2. **Idempotency**: All operations must be safely retryable
3. **Observability**: Comprehensive logging, tracing, and monitoring
4. **Graceful Degradation**: Fallbacks at every layer
5. **Scalability**: Stateless workers, horizontal scaling
6. **Cost Optimization**: Cache-first, generate-on-miss
7. **Security by Design**: Least privilege, encrypted at rest and in transit

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  - Content Request UI                                            │
│  - Real-time Status Updates (WebSocket/Polling)                 │
│  - Video Player with Progress Tracking                          │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ├─ REST API
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                   API Gateway (Cloud Run)                        │
│  - Authentication & Authorization (JWT)                          │
│  - Rate Limiting & Request Validation                           │
│  - Cache Lookup (fast path)                                     │
│  - Pub/Sub Message Publishing (cache miss)                      │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ├─ Pub/Sub Topic: content-requests
               │
┌──────────────▼──────────────────────────────────────────────────┐
│              Content Worker (Cloud Run Jobs)                     │
│  1. NLU Service → Topic Extraction & Validation                 │
│  2. Cache Service → Check for existing content                  │
│  3. RAG Service → Retrieve educational content from OER         │
│  4. Script Generation → Personalized script via Vertex AI       │
│  5. TTS Service → Audio generation (ElevenLabs)                 │
│  6. Video Service → Video rendering (Nano Banana)               │
│  7. Storage Service → Upload to GCS                             │
│  8. Tracking Service → Update request status                    │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ├─ Results stored in Cloud Storage + PostgreSQL
               │
┌──────────────▼──────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  - PostgreSQL: Request tracking, user data, progress            │
│  - Cloud Storage: Videos, audio, scripts, thumbnails            │
│  - Vector DB (Matching Engine): OER embeddings for RAG          │
│  - Redis (future): Real-time status updates                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Content Worker Deployment

### Current State Analysis
- Worker code exists: `app/workers/content_worker.py` ✅
- Dockerfile exists: `Dockerfile.content-worker` ✅
- Orchestration service implemented: `ContentGenerationService` ✅
- **ISSUE**: Worker not deployed to Cloud Run Jobs
- **ISSUE**: No Pub/Sub trigger configured
- **ISSUE**: No end-to-end testing

### Long-Term Architecture Decisions

#### Why Cloud Run Jobs (Not Cloud Functions)?
- **Long-running tasks**: Video generation can take 5-15 minutes
- **Memory requirements**: Video processing needs 4-8GB RAM
- **GPU support**: Future integration with GPUs for rendering
- **Cost efficiency**: Pay per job execution, not per second

#### Idempotency Strategy
```python
# Every worker operation must be idempotent
# Use request_id as idempotency key in all operations

def process_request(request_data):
    request_id = request_data['request_id']

    # Check if already processed
    if cache.get(f"processed:{request_id}"):
        return {"status": "already_processed"}

    # Process with atomic operations
    result = perform_work(request_data)

    # Mark as processed (with TTL = 7 days)
    cache.set(f"processed:{request_id}", True, ttl=604800)

    return result
```

#### Error Handling & Retry Logic
```python
# Exponential backoff with jitter
MAX_RETRIES = 3
RETRY_DELAYS = [10, 60, 300]  # seconds

for attempt in range(MAX_RETRIES):
    try:
        result = process_content()
        break
    except RetryableError as e:
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[attempt] + random.randint(0, 10)
            await asyncio.sleep(delay)
        else:
            # Move to DLQ for manual investigation
            publish_to_dlq(request_data, error=e)
            raise
    except NonRetryableError as e:
        # Immediate failure, don't retry
        log_error_and_notify(request_data, error=e)
        raise
```

### Implementation Steps

#### Step 1: Enhance Worker for Production
File: `backend/app/workers/content_worker.py`

**Enhancements Needed**:
1. Add comprehensive logging with correlation IDs
2. Implement idempotency checks
3. Add circuit breakers for external services
4. Implement graceful shutdown handling
5. Add health check endpoint
6. Add metrics export (Prometheus format)

```python
import structlog
from opentelemetry import trace
from circuit breaker import CircuitBreaker

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

class ContentWorkerProduction:
    def __init__(self):
        self.content_service = ContentGenerationService()
        self.db = get_database()

        # Circuit breakers for external services
        self.vertex_ai_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            name="vertex_ai"
        )
        self.tts_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30,
            name="tts_service"
        )

    async def process_with_observability(self, request_data):
        correlation_id = request_data.get('correlation_id')

        with tracer.start_as_current_span("content_generation") as span:
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("student_id", request_data['student_id'])

            logger.info(
                "processing_request",
                correlation_id=correlation_id,
                request_id=request_data['request_id']
            )

            # Check idempotency
            if await self.is_already_processed(correlation_id):
                logger.info("request_already_processed", correlation_id=correlation_id)
                return await self.get_cached_result(correlation_id)

            # Process with retry logic
            result = await self.process_with_retries(request_data)

            # Store idempotency marker
            await self.mark_as_processed(correlation_id, result)

            return result
```

#### Step 2: Update Dockerfile for Production
File: `backend/Dockerfile.content-worker`

**Enhancements**:
1. Multi-stage build (already present ✅)
2. Security: Non-root user (already present ✅)
3. Add health check script
4. Optimize layer caching
5. Add labels for versioning

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt requirements-worker.txt ./
RUN pip install --no-cache-dir --user \
    -r requirements.txt \
    -r requirements-worker.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 worker && \
    chown -R worker:worker /app && \
    mkdir -p /tmp/worker && \
    chown worker:worker /tmp/worker

USER worker

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Labels for versioning
LABEL org.opencontainers.image.title="Vividly Content Worker"
LABEL org.opencontainers.image.description="AI content generation worker"
LABEL org.opencontainers.image.version="1.0.0"

# Worker entry point
CMD ["python", "-m", "app.workers.content_worker"]
```

#### Step 3: Create requirements-worker.txt
File: `backend/requirements-worker.txt`

```txt
# Additional dependencies for content worker

# Google Cloud
google-cloud-aiplatform>=1.38.0  # Vertex AI
google-cloud-storage>=2.10.0
google-cloud-pubsub>=2.18.0
google-cloud-logging>=3.5.0

# Video Processing
ffmpeg-python>=0.2.0
pillow>=10.0.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9

# Audio Processing
pydub>=0.25.1

# AI Services
openai>=1.3.0  # For embeddings
elevenlabs>=0.2.0  # TTS service

# Observability
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-fastapi>=0.41b0
opentelemetry-exporter-gcp-trace>=1.5.0
structlog>=23.1.0
python-json-logger>=2.0.7

# Circuit Breaker
circuitbreaker>=1.4.0

# Retry logic
tenacity>=8.2.3
```

#### Step 4: Create Cloud Run Job via Terraform
File: `terraform/content_worker.tf`

```hcl
resource "google_cloud_run_v2_job" "content_worker" {
  name     = "${var.environment}-vividly-content-worker"
  location = var.region
  project  = var.project_id

  template {
    template {
      # Worker configuration
      max_retries = 3
      timeout     = "1800s"  # 30 minutes max

      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/vividly/content-worker:latest"

        # Resource allocation
        resources {
          limits = {
            cpu    = "4"      # 4 vCPU for video processing
            memory = "8Gi"    # 8GB for large video files
          }
        }

        # Environment variables from Secret Manager
        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "VERTEX_AI_PROJECT_ID"
          value = var.project_id
        }

        env {
          name = "VERTEX_AI_LOCATION"
          value = var.region
        }

        env {
          name  = "GCS_BUCKET_GENERATED"
          value = google_storage_bucket.generated_content.name
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
      }

      # Service account with permissions
      service_account = google_service_account.content_worker.email

      # VPC configuration for database access
      vpc_access {
        connector = google_vpc_access_connector.content_worker.name
        egress    = "PRIVATE_RANGES_ONLY"
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }
}

# Pub/Sub trigger for Cloud Run Job
resource "google_cloud_scheduler_job" "trigger_content_worker" {
  name        = "${var.environment}-trigger-content-worker"
  description = "Triggers content worker via Pub/Sub"
  schedule    = "* * * * *"  # Every minute (will be replaced by event-driven)
  region      = var.region
  project     = var.project_id

  pubsub_target {
    topic_name = google_pubsub_topic.content_requests.id
    data       = base64encode(jsonencode({
      trigger = "scheduler"
    }))
  }
}

# VPC Connector for private database access
resource "google_vpc_access_connector" "content_worker" {
  name          = "${var.environment}-content-worker-connector"
  project       = var.project_id
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
}

# IAM bindings for worker
resource "google_project_iam_member" "content_worker_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}

resource "google_project_iam_member" "content_worker_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}

resource "google_project_iam_member" "content_worker_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}
```

#### Step 5: Create Deployment Script
File: `scripts/deploy-content-worker.sh`

```bash
#!/bin/bash
set -euo pipefail

# Deploy Content Worker to Cloud Run Jobs
# Usage: ./scripts/deploy-content-worker.sh [dev|staging|prod]

ENVIRONMENT=${1:-dev}
PROJECT_ID="vividly-${ENVIRONMENT}-rich"
REGION="us-central1"
WORKER_IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/vividly/content-worker:latest"

echo "🚀 Deploying Content Worker to ${ENVIRONMENT}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Step 1: Build Docker image
echo "📦 Building Docker image..."
cd backend
docker build \
  -t "${WORKER_IMAGE}" \
  -f Dockerfile.content-worker \
  .

# Step 2: Push to Artifact Registry
echo "⬆️  Pushing to Artifact Registry..."
docker push "${WORKER_IMAGE}"

# Step 3: Deploy Cloud Run Job via Terraform
echo "🏗️  Deploying via Terraform..."
cd ../terraform
terraform init
terraform plan \
  -var-file="environments/${ENVIRONMENT}.tfvars" \
  -target=google_cloud_run_v2_job.content_worker \
  -out=tfplan

terraform apply tfplan

echo "✅ Content Worker deployed successfully!"
echo ""
echo "Test with:"
echo "  gcloud run jobs execute ${ENVIRONMENT}-vividly-content-worker \\"
echo "    --region=${REGION} \\"
echo "    --project=${PROJECT_ID}"
```

#### Step 6: Create Test Script
File: `scripts/test-content-worker.sh`

```bash
#!/bin/bash
set -euo pipefail

# Test Content Worker end-to-end
# Usage: ./scripts/test-content-worker.sh

ENVIRONMENT="dev"
PROJECT_ID="vividly-dev-rich"
REGION="us-central1"
TOPIC="content-requests-dev"

echo "🧪 Testing Content Worker"
echo ""

# Step 1: Publish test message to Pub/Sub
echo "1. Publishing test message to Pub/Sub..."
TEST_REQUEST=$(cat <<EOF
{
  "request_id": "test_$(date +%s)",
  "correlation_id": "test_correlation_$(date +%s)",
  "student_id": "user_student_test_001",
  "student_query": "Explain Newton's First Law using basketball",
  "grade_level": 10,
  "interest": "basketball",
  "duration_seconds": 180
}
EOF
)

gcloud pubsub topics publish "${TOPIC}" \
  --project="${PROJECT_ID}" \
  --message="${TEST_REQUEST}"

echo "✅ Test message published"
echo ""

# Step 2: Monitor job execution
echo "2. Monitoring job execution..."
echo "Check logs at:"
echo "  https://console.cloud.google.com/run/jobs/details/${REGION}/${ENVIRONMENT}-vividly-content-worker?project=${PROJECT_ID}"
echo ""

# Step 3: Check database for request status
echo "3. Checking request status in database..."
# This would query the database to check if the request was processed
echo "TODO: Implement database status check"
```

---

## 2. Content Request UI

### Design Philosophy
- **Progressive Enhancement**: Works without JavaScript (graceful degradation)
- **Real-time Feedback**: WebSocket or polling for status updates
- **Accessibility**: WCAG 2.1 AA compliant
- **Mobile-first**: Responsive design
- **Error Recovery**: Clear error messages with retry options

### Component Architecture

```
ContentRequestPage
├── RequestForm (input + validation)
├── ClarificationDialog (NLU needs more info)
├── StatusTracker (pipeline progress)
├── VideoPlayer (when ready)
└── FeedbackButtons (complete, simpler, different)
```

### Implementation

#### Step 1: Create API Client
File: `frontend/src/api/contentClient.ts`

```typescript
/**
 * Content Request API Client
 * Handles all content generation requests and status polling
 */

export interface ContentRequest {
  studentQuery: string;
  gradeLevel: number;
  interest?: string;
  durationSeconds?: number;
}

export interface ContentRequestResponse {
  requestId: string;
  correlationId: string;
  status: RequestStatus;
  message?: string;
  clarifyingQuestions?: ClarifyingQuestion[];
}

export type RequestStatus =
  | 'pending'
  | 'validating'
  | 'retrieving'
  | 'generating_script'
  | 'generating_video'
  | 'processing_video'
  | 'notifying'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'needs_clarification';

export interface ClarifyingQuestion {
  question: string;
  options?: string[];
  type: 'multiple_choice' | 'text' | 'confirmation';
}

export interface ContentStatus {
  requestId: string;
  status: RequestStatus;
  progressPercentage: number;
  currentStage?: string;
  videoUrl?: string;
  scriptText?: string;
  thumbnailUrl?: string;
  error?: ErrorDetails;
}

export interface ErrorDetails {
  message: string;
  stage?: string;
  retryable: boolean;
}

class ContentClient {
  private baseUrl: string;
  private wsConnection: WebSocket | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Submit a content generation request
   */
  async submitRequest(
    request: ContentRequest
  ): Promise<ContentRequestResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/content/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.getAuthToken()}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Answer clarifying questions
   */
  async submitClarification(
    requestId: string,
    answers: Record<string, string>
  ): Promise<ContentRequestResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/content/request/${requestId}/clarify`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
        body: JSON.stringify({ answers }),
      }
    );

    if (!response.ok) {
      throw new Error(`Clarification failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Poll for request status
   */
  async getRequestStatus(requestId: string): Promise<ContentStatus> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/content/request/${requestId}/status`,
      {
        headers: {
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Subscribe to real-time status updates via WebSocket
   */
  subscribeToStatus(
    requestId: string,
    onUpdate: (status: ContentStatus) => void,
    onError: (error: Error) => void
  ): () => void {
    const wsUrl = `${this.baseUrl.replace('http', 'ws')}/api/v1/content/request/${requestId}/ws`;

    this.wsConnection = new WebSocket(wsUrl);

    this.wsConnection.onmessage = (event) => {
      try {
        const status: ContentStatus = JSON.parse(event.data);
        onUpdate(status);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.wsConnection.onerror = (event) => {
      onError(new Error('WebSocket connection error'));
    };

    this.wsConnection.onclose = () => {
      console.log('WebSocket connection closed');
    };

    // Return cleanup function
    return () => {
      if (this.wsConnection) {
        this.wsConnection.close();
        this.wsConnection = null;
      }
    };
  }

  /**
   * Cancel a request
   */
  async cancelRequest(requestId: string): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/content/request/${requestId}/cancel`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.getAuthToken()}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Cancel failed: ${response.statusText}`);
    }
  }

  private getAuthToken(): string {
    // Get from localStorage or auth context
    return localStorage.getItem('access_token') || '';
  }
}

export const contentClient = new ContentClient(
  import.meta.env.VITE_API_URL || 'http://localhost:8000'
);
```

#### Step 2: Create Request Form Component
File: `frontend/src/components/ContentRequestForm.tsx`

```typescript
/**
 * Content Request Form
 * Main interface for students to request personalized content
 */

import React, { useState, useEffect } from 'react';
import { contentClient, ContentRequest } from '../api/contentClient';
import { useAuth } from '../hooks/useAuth';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';

interface ContentRequestFormProps {
  onRequestSubmitted: (requestId: string) => void;
}

export const ContentRequestForm: React.FC<ContentRequestFormProps> = ({
  onRequestSubmitted,
}) => {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Load example queries for inspiration
  useEffect(() => {
    const examples = [
      "Explain Newton's First Law using basketball",
      "How does photosynthesis work? Use music production",
      "What is the Pythagorean theorem? Explain with video games",
      "How do chemical reactions work? Use cooking",
    ];
    setSuggestions(examples);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const request: ContentRequest = {
        studentQuery: query,
        gradeLevel: user?.gradeLevel || 10,
        // Interest will be inferred from student profile
      };

      const response = await contentClient.submitRequest(request);

      if (response.status === 'needs_clarification') {
        // Handle clarification in parent component
        onRequestSubmitted(response.requestId);
      } else {
        onRequestSubmitted(response.requestId);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to submit request. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="query"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            What would you like to learn?
          </label>
          <Input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Explain Newton's First Law using basketball"
            disabled={isSubmitting}
            required
            className="w-full"
            aria-label="Content request query"
          />
          <p className="mt-2 text-sm text-gray-500">
            Ask about any topic, and we'll explain it using your interests!
          </p>
        </div>

        {error && (
          <div
            className="p-3 bg-red-50 border border-red-200 rounded-md text-red-800"
            role="alert"
          >
            {error}
          </div>
        )}

        <div className="flex gap-2">
          <Button
            type="submit"
            disabled={isSubmitting || !query.trim()}
            className="flex-1"
          >
            {isSubmitting ? 'Submitting...' : 'Generate Content'}
          </Button>
        </div>

        {suggestions.length > 0 && !query && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">
              Try these examples:
            </p>
            <div className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full text-left p-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-md transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </form>
    </Card>
  );
};
```

This is getting very long. Let me save this comprehensive plan and continue with the remaining sections. This document provides the architectural foundation and first two major components. Would you like me to continue with the remaining sections?
