# Vividly Integration Points

**Version:** 1.0 (MVP)
**Last Updated:** October 27, 2025

## Table of Contents

1. [Overview](#overview)
2. [Google Cloud Platform Services](#google-cloud-platform-services)
3. [Nano Banana Video API](#nano-banana-video-api)
4. [Future Integrations](#future-integrations)
5. [Monitoring & Health Checks](#monitoring--health-checks)
6. [Error Handling Patterns](#error-handling-patterns)

---

## Overview

Vividly integrates with multiple third-party services to deliver its core functionality. This document specifies all external integration points, including authentication, rate limits, error handling, and monitoring requirements.

### Integration Summary

| Service | Provider | Purpose | Criticality |
|---------|----------|---------|-------------|
| Vertex AI (LLM) | Google Cloud | NLU, Script Generation | **Critical** |
| Vertex AI (Embeddings) | Google Cloud | Text embeddings for RAG | **Critical** |
| Vertex AI Vector Search | Google Cloud | Semantic search in OER content | **Critical** |
| Cloud Text-to-Speech | Google Cloud | Audio generation | **Critical** |
| Cloud Storage (GCS) | Google Cloud | Asset storage | **Critical** |
| Cloud SQL | Google Cloud | PostgreSQL database | **Critical** |
| Pub/Sub | Google Cloud | Message queue | **Critical** |
| Cloud Run | Google Cloud | Service hosting | **Critical** |
| Cloud Functions | Google Cloud | Serverless workers | **Critical** |
| Secret Manager | Google Cloud | Secrets storage | **Critical** |
| Cloud Logging | Google Cloud | Centralized logging | High |
| Cloud Monitoring | Google Cloud | Metrics & alerts | High |
| Nano Banana | External | Video generation | **Critical** |

---

## Google Cloud Platform Services

### 1. Vertex AI - Generative AI

#### Purpose
- Natural Language Understanding (topic extraction)
- Script generation using LearnLM/Gemini
- Text embeddings for semantic search

#### Authentication
```python
from google.oauth2 import service_account
from vertexai import init

# Initialize with service account
credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account-key.json'
)

init(
    project=PROJECT_ID,
    location=LOCATION,
    credentials=credentials
)
```

#### Models Used

**Gemini 1.5 Pro (gemini-1.5-pro)**
- **Purpose**: NLU and Script Generation
- **Input Limits**: 1M tokens
- **Output Limits**: 8K tokens
- **Rate Limits**: 60 requests/minute (default)
- **Cost**: $0.00125/1K input tokens, $0.005/1K output tokens

**Text Embeddings (text-embedding-gecko@003)**
- **Purpose**: Generate embeddings for RAG
- **Dimensions**: 768
- **Input Limits**: 3,072 tokens per request
- **Batch Size**: 250 texts per request
- **Rate Limits**: 1,500 requests/minute
- **Cost**: $0.00001/1K characters

#### API Example: Text Generation

```python
from vertexai.generative_models import GenerativeModel

model = GenerativeModel("gemini-1.5-pro")

response = model.generate_content(
    prompt,
    generation_config={
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 4096,
        "response_mime_type": "application/json"
    },
    safety_settings={
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE"
    }
)

return response.text
```

#### API Example: Embeddings

```python
from vertexai.language_models import TextEmbeddingModel

model = TextEmbeddingModel.from_pretrained("text-embedding-gecko@003")

# Batch processing
texts = ["text 1", "text 2", ...]
embeddings = model.get_embeddings(texts)

# Access individual embeddings
for embedding in embeddings:
    vector = embedding.values  # 768-dimensional vector
    print(f"Vector length: {len(vector)}")
```

#### Error Handling

```python
from google.api_core import exceptions
from google.api_core import retry

@retry.Retry(
    initial=1.0,
    maximum=60.0,
    multiplier=2.0,
    predicate=retry.if_exception_type(
        exceptions.ResourceExhausted,
        exceptions.ServiceUnavailable,
        exceptions.DeadlineExceeded
    )
)
def generate_with_retry(model, prompt):
    try:
        return model.generate_content(prompt)

    except exceptions.ResourceExhausted as e:
        logger.error(f"Quota exceeded: {e}")
        raise

    except exceptions.InvalidArgument as e:
        logger.error(f"Invalid request: {e}")
        raise

    except exceptions.FailedPrecondition as e:
        logger.error(f"Safety filter triggered: {e}")
        # Content blocked by safety filters
        raise ContentSafetyError("Generated content blocked by safety filters")
```

#### Rate Limiting Strategy

```python
import time
from collections import deque

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute=60):
        self.rate = requests_per_minute
        self.bucket_size = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
        self.requests = deque()

    def acquire(self):
        """Block until request is allowed."""
        now = time.time()

        # Refill tokens
        elapsed = now - self.last_update
        self.tokens = min(
            self.bucket_size,
            self.tokens + elapsed * (self.rate / 60)
        )
        self.last_update = now

        # Wait if no tokens available
        if self.tokens < 1:
            wait_time = (1 - self.tokens) * (60 / self.rate)
            time.sleep(wait_time)
            self.tokens = 0
        else:
            self.tokens -= 1

# Global rate limiters
gemini_limiter = RateLimiter(requests_per_minute=60)
embedding_limiter = RateLimiter(requests_per_minute=1500)

def generate_content(prompt):
    gemini_limiter.acquire()
    return model.generate_content(prompt)
```

#### Monitoring

```python
from google.cloud import monitoring_v3

def track_vertex_ai_metrics():
    """Track Vertex AI API usage and performance."""

    metrics_to_track = [
        "aiplatform.googleapis.com/prediction/online/response_count",
        "aiplatform.googleapis.com/prediction/online/error_count",
        "aiplatform.googleapis.com/prediction/online/prediction_latencies"
    ]

    # Set up alerts
    alert_policies = {
        "high_error_rate": {
            "condition": "error_count / response_count > 0.05",
            "threshold": 0.05,
            "duration": "5m"
        },
        "high_latency": {
            "condition": "prediction_latencies.p95 > 10000",  # 10s
            "threshold": 10000,
            "duration": "5m"
        }
    }
```

---

### 2. Vertex AI Vector Search

#### Purpose
Semantic search over embedded OER content for RAG retrieval.

#### Configuration

```python
INDEX_CONFIG = {
    "display_name": "vividly-oer-embeddings-index",
    "metadata": {
        "contentsDeltaUri": "gs://vividly-mvp-vector-db/embeddings",
        "config": {
            "dimensions": 768,
            "approximateNeighborsCount": 150,
            "distanceMeasureType": "COSINE_DISTANCE",
            "algorithmConfig": {
                "treeAhConfig": {
                    "leafNodeEmbeddingCount": 1000,
                    "leafNodesToSearchPercent": 7
                }
            }
        }
    }
}

ENDPOINT_CONFIG = {
    "display_name": "vividly-oer-endpoint",
    "public_endpoint_enabled": False,  # VPC-only
    "deployed_index": {
        "dedicated_resources": {
            "machine_type": "e2-standard-2",
            "min_replica_count": 1,
            "max_replica_count": 3
        }
    }
}
```

#### API Usage

```python
from google.cloud import aiplatform

def search_similar_chunks(query_embedding, topic_id, k=10):
    """Query Vector Search index."""

    # Initialize client
    index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=ENDPOINT_NAME
    )

    # Search with filters
    response = index_endpoint.find_neighbors(
        deployed_index_id=DEPLOYED_INDEX_ID,
        queries=[query_embedding],
        num_neighbors=k,
        filter=[
            {
                "namespace": "topic",
                "allow_list": [topic_id]
            }
        ]
    )

    # Extract results
    neighbors = response[0]
    chunk_ids = [neighbor.id for neighbor in neighbors]
    distances = [neighbor.distance for neighbor in neighbors]

    return chunk_ids, distances
```

#### Rate Limits
- **Queries**: 1,000 QPS per endpoint
- **Index Updates**: 1 concurrent update
- **Batch Import**: 50 GB/hour

#### Cost
- **Deployed Index**: $0.80/hour per replica (e2-standard-2)
- **Query**: $0.45 per 1M queries
- **Index Storage**: $0.30/GB/month

---

### 3. Cloud Text-to-Speech

#### Purpose
Convert script narration to natural-sounding audio.

#### Authentication

```python
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()
```

#### Voices Used

**Primary Voice: en-US-Neural2-J**
- **Type**: Neural2 (WaveNet successor)
- **Gender**: Male
- **Style**: Young adult, conversational
- **Quality**: High

**Alternative Voice: en-US-Neural2-F**
- **Type**: Neural2
- **Gender**: Female
- **Style**: Young adult, friendly

#### API Example

```python
def synthesize_speech(text, voice_name="en-US-Neural2-J"):
    """Generate audio from text using Cloud TTS."""

    # Build SSML for better control
    ssml = f"""
    <speak>
        <prosody rate="0.95" pitch="0.0st">
            {text}
        </prosody>
    </speak>
    """

    # Configure voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name
    )

    # Configure audio
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.95,
        pitch=0.0,
        effects_profile_id=["small-bluetooth-speaker-class-device"],
        sample_rate_hertz=24000
    )

    # Synthesize
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content  # bytes
```

#### Rate Limits
- **Standard**: 300 requests/minute/project
- **Neural2**: 100 requests/minute/project
- **Concurrent**: 10 requests

#### Cost
- **Neural2**: $16 per 1M characters
- **Average cost per video**: ~$0.006 (200 chars per script)

#### Error Handling

```python
from google.api_core import exceptions

def synthesize_with_fallback(text):
    """Synthesize with fallback to standard voice if Neural2 fails."""

    try:
        # Try Neural2 first
        return synthesize_speech(text, voice_name="en-US-Neural2-J")

    except exceptions.ResourceExhausted:
        logger.warning("Neural2 quota exceeded, using standard voice")
        return synthesize_speech(text, voice_name="en-US-Standard-D")

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise
```

---

### 4. Cloud Storage (GCS)

#### Purpose
Storage for generated scripts, audio, and video files.

#### Buckets

| Bucket | Purpose | Lifecycle | Public Access |
|--------|---------|-----------|---------------|
| `{project}-scripts` | JSON storyboards | None | No |
| `{project}-audio` | MP3 audio files | None | Signed URLs |
| `{project}-videos` | MP4 video files | None | Signed URLs |
| `{project}-uploads` | Temp CSV uploads | Delete after 7 days | No |
| `{project}-vector-db` | Vector embeddings | None | No |

#### API Usage

```python
from google.cloud import storage

def upload_to_gcs(bucket_name, blob_path, content, content_type):
    """Upload content to GCS bucket."""

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Upload
    blob.upload_from_string(
        content,
        content_type=content_type
    )

    # Set cache control
    blob.cache_control = "public, max-age=31536000"  # 1 year
    blob.patch()

    return blob

def generate_signed_url(bucket_name, blob_path, expiration=900):
    """Generate signed URL for private blob (15 min default)."""

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(seconds=expiration),
        method="GET"
    )

    return url
```

#### Naming Convention

```
# Scripts
{cache_key}/script.json

# Audio
{cache_key}/audio.mp3

# Videos
{cache_key}/video.mp4
{cache_key}/thumbnail.jpg

# Uploads (temporary)
uploads/{upload_id}/{filename}

# Example
SHA256(topic_phys_newton_3|int_basketball|conversational)/
  ├── script.json
  ├── audio.mp3
  ├── video.mp4
  └── thumbnail.jpg
```

#### Rate Limits
- **Write**: 1 request/second per object
- **Read**: 5,000 requests/second
- **Bandwidth**: No limit

#### Cost
- **Storage**: $0.020/GB/month (Standard)
- **Operations**: $0.05 per 10K writes, $0.004 per 10K reads
- **Bandwidth**: $0.12/GB egress (to internet)

---

### 5. Cloud Pub/Sub

#### Purpose
Asynchronous job queue for content generation pipeline.

#### Topics

| Topic | Purpose | Subscribers |
|-------|---------|-------------|
| `generate-script` | Trigger script generation | script-worker |
| `generate-audio` | Trigger audio generation | audio-worker |
| `generate-video` | Trigger video generation | video-worker |
| `content-ready` | Notify content completion | notification-service |
| `dlq-script` | Script generation failures | manual-review |
| `dlq-audio` | Audio generation failures | manual-review |
| `dlq-video` | Video generation failures | manual-review |

#### API Usage

```python
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()

def publish_message(topic_name, data, **attributes):
    """Publish message to Pub/Sub topic."""

    topic_path = publisher.topic_path(PROJECT_ID, topic_name)

    # Serialize data
    message_bytes = json.dumps(data).encode('utf-8')

    # Publish
    future = publisher.publish(
        topic_path,
        message_bytes,
        **attributes
    )

    message_id = future.result(timeout=30)
    logger.info(f"Published message {message_id} to {topic_name}")

    return message_id

# Example: Trigger script generation
publish_message(
    "generate-script",
    {
        "request_id": "req_abc123",
        "topic_id": "topic_phys_newton_3",
        "interest_id": "int_basketball",
        "style": "conversational"
    },
    priority="high"
)
```

#### Subscription Configuration

```python
subscriber = pubsub_v1.SubscriberClient()

SUBSCRIPTION_CONFIG = {
    "ack_deadline_seconds": 600,  # 10 minutes
    "message_retention_duration": "7d",
    "retry_policy": {
        "minimum_backoff": "10s",
        "maximum_backoff": "600s"
    },
    "dead_letter_policy": {
        "dead_letter_topic": f"projects/{PROJECT_ID}/topics/dlq-script",
        "max_delivery_attempts": 5
    }
}
```

#### Rate Limits
- **Publishing**: 10,000 messages/second/topic
- **Subscribing**: No limit
- **Message Size**: 10 MB

#### Cost
- **Throughput**: $40 per TiB of message data
- **Typical cost**: ~$0.01 per 1,000 messages

---

## Nano Banana Video API

### Overview

**Provider**: Nano Banana (nano-banana.ai)
**Purpose**: Convert storyboard + audio into animated educational video
**Criticality**: **Critical** (no fallback for MVP)

### Authentication

```python
import requests

NANO_BANANA_API_KEY = os.getenv("NANO_BANANA_API_KEY")
NANO_BANANA_BASE_URL = "https://api.nanobanana.ai/v1"

headers = {
    "Authorization": f"Bearer {NANO_BANANA_API_KEY}",
    "Content-Type": "application/json"
}
```

### API Endpoints

#### 1. Create Video Job

**Endpoint**: `POST /generate`

**Request**:
```json
{
  "scenes": [
    {
      "duration": 15,
      "visual": "Animated basketball player preparing to jump",
      "visual_type": "animated_character",
      "background": "basketball_court",
      "text_overlay": "Newton's Third Law",
      "annotations": [
        {
          "type": "arrow",
          "start": {"x": 100, "y": 200},
          "end": {"x": 100, "y": 300},
          "label": "Force",
          "color": "red"
        }
      ]
    }
  ],
  "audio_url": "https://storage.googleapis.com/vividly-audio/abc123.mp3",
  "style": "educational_animated",
  "resolution": "1920x1080",
  "fps": 30,
  "format": "mp4",
  "metadata": {
    "topic_id": "topic_phys_newton_3",
    "client": "vividly",
    "request_id": "req_abc123"
  }
}
```

**Response**:
```json
{
  "job_id": "nb_job_xyz789",
  "status": "queued",
  "estimated_time_seconds": 45,
  "created_at": "2025-10-27T14:30:00Z"
}
```

#### 2. Check Job Status

**Endpoint**: `GET /jobs/{job_id}`

**Response (Processing)**:
```json
{
  "job_id": "nb_job_xyz789",
  "status": "processing",
  "progress_percent": 65,
  "estimated_completion": "2025-10-27T14:31:00Z"
}
```

**Response (Completed)**:
```json
{
  "job_id": "nb_job_xyz789",
  "status": "completed",
  "video_url": "https://cdn.nanobanana.ai/videos/xyz789.mp4",
  "thumbnail_url": "https://cdn.nanobanana.ai/thumbnails/xyz789.jpg",
  "duration_seconds": 180,
  "file_size_bytes": 45678901,
  "completed_at": "2025-10-27T14:31:15Z"
}
```

**Response (Failed)**:
```json
{
  "job_id": "nb_job_xyz789",
  "status": "failed",
  "error": {
    "code": "INVALID_AUDIO_URL",
    "message": "Audio URL returned 404"
  },
  "failed_at": "2025-10-27T14:30:30Z"
}
```

### Implementation

```python
class NanoBananaClient:
    """Client for Nano Banana Video API."""

    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def create_video(self, storyboard, audio_url):
        """Submit video generation job."""

        # Convert storyboard to Nano Banana format
        payload = self._format_payload(storyboard, audio_url)

        response = self.session.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        return response.json()["job_id"]

    def poll_status(self, job_id, timeout=600, poll_interval=5):
        """Poll job status until completion or timeout."""

        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{self.base_url}/jobs/{job_id}",
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            status = data["status"]

            if status == "completed":
                return data

            elif status == "failed":
                raise VideoGenerationError(
                    f"Video generation failed: {data['error']['message']}"
                )

            # Exponential backoff
            wait_time = min(30, poll_interval * 1.5 ** (
                (time.time() - start_time) // 30
            ))
            time.sleep(wait_time)

        raise TimeoutError(f"Video generation timed out after {timeout}s")

    def download_video(self, video_url, output_path):
        """Download generated video."""

        response = self.session.get(video_url, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
```

### Rate Limits

- **Job Submission**: 10 requests/minute
- **Status Polling**: 60 requests/minute
- **Concurrent Jobs**: 5 (per account)
- **Monthly Video Minutes**: 1,000 (starter plan)

### Cost

- **Per Video Minute**: $0.10
- **Average 3-minute video**: $0.30
- **Estimated monthly cost** (3,000 videos): $900

### Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `INVALID_AUDIO_URL` | Audio file not accessible | Verify GCS URL is public/signed |
| `AUDIO_TOO_LONG` | Audio exceeds max duration | Reduce script length |
| `INVALID_SCENE_FORMAT` | Scene data malformed | Validate storyboard schema |
| `QUOTA_EXCEEDED` | Monthly quota exceeded | Upgrade plan or wait |
| `GENERATION_TIMEOUT` | Video took too long | Retry with simpler scenes |

### Webhook Configuration (Optional)

```python
# Register webhook for completion notifications
webhook_payload = {
    "url": "https://api.vividly.education/api/v1/webhooks/nano-banana",
    "events": ["video.completed", "video.failed"],
    "secret": "webhook_secret_12345"
}

response = client.session.post(
    f"{client.base_url}/webhooks",
    json=webhook_payload
)
```

### Webhook Handler

```python
from fastapi import Request, HTTPException
import hmac
import hashlib

@app.post("/api/v1/webhooks/nano-banana")
async def handle_nano_banana_webhook(request: Request):
    """Handle Nano Banana webhook notifications."""

    # Verify signature
    signature = request.headers.get("X-Nano-Banana-Signature")
    body = await request.body()

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process event
    event = await request.json()

    if event["event"] == "video.completed":
        # Download and save video
        job_id = event["video_id"]
        video_url = event["video_url"]

        # Update database
        update_content_with_video(job_id, video_url)

        # Notify student
        notify_student_video_ready(job_id)

    return {"received": True}
```

---

## Future Integrations

### Post-MVP Planned Integrations

#### 1. Single Sign-On (SSO)

**Google Workspace**
- OAuth 2.0 integration
- Automatic user provisioning
- Domain verification

**Clever**
- K-12 SSO standard
- Automated rostering
- Secure data sharing

**ClassLink**
- Alternative K-12 SSO
- Rostering integration

#### 2. Student Information Systems (SIS)

**OneRoster API**
- Standardized rostering format
- Automated student/class sync
- Grade passback

#### 3. Learning Management Systems (LMS)

**Google Classroom**
- Assignment integration
- Grade sync
- Deep linking

**Canvas LMS**
- LTI 1.3 integration
- Assignment submission
- Grade passback

#### 4. Payment Processing

**Stripe**
- Subscription management
- Usage-based billing
- Invoice generation

---

## Monitoring & Health Checks

### Health Check Endpoints

```python
@app.get("/health")
def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/detailed")
def detailed_health_check():
    """Detailed health check for all integrations."""

    checks = {
        "vertex_ai": check_vertex_ai_health(),
        "cloud_sql": check_database_health(),
        "gcs": check_storage_health(),
        "pubsub": check_pubsub_health(),
        "nano_banana": check_nano_banana_health()
    }

    all_healthy = all(check["healthy"] for check in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

def check_nano_banana_health():
    """Check Nano Banana API availability."""
    try:
        response = requests.get(
            f"{NANO_BANANA_BASE_URL}/health",
            headers={"Authorization": f"Bearer {NANO_BANANA_API_KEY}"},
            timeout=5
        )
        return {
            "healthy": response.status_code == 200,
            "latency_ms": response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}
```

### Metrics to Track

```python
# Custom metrics
from google.cloud import monitoring_v3

metrics_to_track = {
    "vertex_ai_requests": "Custom/VertexAI/Requests",
    "vertex_ai_errors": "Custom/VertexAI/Errors",
    "vertex_ai_latency": "Custom/VertexAI/Latency",
    "tts_requests": "Custom/TTS/Requests",
    "tts_characters": "Custom/TTS/Characters",
    "nano_banana_jobs": "Custom/NanoBanana/Jobs",
    "nano_banana_success_rate": "Custom/NanoBanana/SuccessRate",
    "gcs_uploads": "Custom/GCS/Uploads",
    "gcs_downloads": "Custom/GCS/Downloads"
}
```

---

## Error Handling Patterns

### Circuit Breaker Pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_nano_banana_api(payload):
    """Call Nano Banana with circuit breaker."""
    response = requests.post(
        f"{NANO_BANANA_BASE_URL}/generate",
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.json()
```

### Retry with Exponential Backoff

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError
    ))
)
def call_external_api(url, payload):
    """Call external API with retry logic."""
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()
```

### Fallback Strategy

```python
def generate_content_with_fallback(topic_id, interest_id):
    """Generate content with multiple fallback strategies."""

    try:
        # Primary: Full pipeline
        return generate_full_content(topic_id, interest_id)

    except NanoBananaError:
        logger.warning("Nano Banana unavailable, serving audio-only")
        # Fallback: Audio only (Vivid Now)
        return generate_audio_content(topic_id, interest_id)

    except VertexAIError:
        logger.error("Vertex AI unavailable, serving cached content")
        # Fallback: Serve cached generic content
        return get_cached_generic_content(topic_id)

    except Exception as e:
        logger.critical(f"All generation methods failed: {e}")
        raise ServiceUnavailableError("Content generation temporarily unavailable")
```

---

## Integration Testing

### Test Checklist

- [ ] Vertex AI authentication works
- [ ] Gemini generates valid JSON responses
- [ ] Embeddings API returns 768-dimensional vectors
- [ ] Vector Search returns relevant results
- [ ] TTS generates valid MP3 files
- [ ] GCS uploads/downloads work
- [ ] Pub/Sub messages are delivered
- [ ] Nano Banana job submission succeeds
- [ ] Nano Banana polling detects completion
- [ ] Webhooks are verified and processed
- [ ] Rate limiters prevent quota errors
- [ ] Circuit breakers open on failures
- [ ] Retries succeed after transient errors
- [ ] Health checks report accurate status

---

**Document Control**
- **Owner**: Platform Engineering Team
- **Last Updated**: October 27, 2025
- **Next Review**: After each API version change
