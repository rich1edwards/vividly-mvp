# Request Tracking Integration Guide

Complete guide for integrating the request tracking system into the Vividly content generation pipeline.

## Overview

The request tracking system provides end-to-end visibility into content generation requests as they flow through the pipeline:

1. **Student submits request** → Validation
2. **RAG retrieval** → Vector Search for OER content
3. **Script generation** → Gemini API call
4. **Video generation** → Nano Banana API call
5. **Video processing** → CDN upload
6. **Notification** → Email student

## Table of Contents

- [Setup](#setup)
- [Basic Integration](#basic-integration)
- [Complete Pipeline Example](#complete-pipeline-example)
- [Error Handling](#error-handling)
- [Monitoring Dashboard](#monitoring-dashboard)
- [Best Practices](#best-practices)

---

## Setup

### 1. Run Database Migration

```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f backend/migrations/add_request_tracking.sql
```

### 2. Import Required Modules

```python
from app.services.request_tracker import RequestTracker
from app.services.circuit_breaker import nano_banana_breaker, gemini_breaker
from sqlalchemy.orm import Session
```

---

## Basic Integration

### Creating a Request

```python
from app.services.request_tracker import RequestTracker

def create_content_request(
    db: Session,
    student_id: str,
    topic: str,
    learning_objective: str,
):
    """Create and track a new content request."""
    tracker = RequestTracker(db)

    # Create request with tracking
    request_id, correlation_id = tracker.create_request(
        student_id=student_id,
        topic=topic,
        learning_objective=learning_objective,
        grade_level="10",
        duration_minutes=5,
        metadata={
            "user_agent": request.headers.get("User-Agent"),
            "source": "web_app",
        }
    )

    # Mark as started
    tracker.start_request(request_id)

    # Log initial event
    tracker.log_event(
        request_id,
        "request_submitted",
        f"Student {student_id} requested content on {topic}",
        severity="info"
    )

    return request_id, correlation_id
```

### Tracking a Stage

```python
def track_stage_example(db: Session, request_id: str):
    """Example of tracking a pipeline stage."""
    tracker = RequestTracker(db)

    # Start stage
    tracker.start_stage(request_id, "rag_retrieval")

    try:
        # Do work
        results = perform_rag_retrieval(topic="Photosynthesis")

        # Complete stage with output
        tracker.complete_stage(
            request_id,
            "rag_retrieval",
            output_data={
                "chunks_retrieved": len(results),
                "sources": [r["source"] for r in results],
            }
        )

    except Exception as e:
        # Mark stage as failed
        tracker.fail_stage(
            request_id,
            "rag_retrieval",
            error_message=str(e),
            error_details={
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
            is_retryable=True
        )
        raise
```

### Using Context Manager (Recommended)

```python
def track_with_context_manager(db: Session, request_id: str):
    """Automatic stage tracking with context manager."""
    tracker = RequestTracker(db)

    # Automatically handles start, complete, and errors
    with tracker.track_stage(request_id, "script_generation"):
        script = generate_script_with_gemini(topic="Photosynthesis")
        return script
```

---

## Complete Pipeline Example

### Content Generation Worker

```python
"""
content_worker.py

Background worker for processing content generation requests.
"""

import time
from app.services.request_tracker import RequestTracker
from app.services.circuit_breaker import nano_banana_breaker, gemini_breaker
from app.services.cache_service import CacheService

def process_content_request(db: Session, request_id: str):
    """
    Process a content generation request through the entire pipeline.

    Pipeline stages:
    1. Validation
    2. RAG retrieval
    3. Script generation
    4. Video generation
    5. Video processing
    6. Notification
    """
    tracker = RequestTracker(db)
    cache = CacheService()

    try:
        # ==================== STAGE 1: Validation ====================
        with tracker.track_stage(request_id, "validation"):
            # Get request details
            status = tracker.get_request_status(request_id)
            topic = status["topic"]
            learning_objective = status["learning_objective"]

            # Validate inputs
            if not topic or len(topic) < 3:
                raise ValueError("Topic must be at least 3 characters")

            tracker.log_event(
                request_id,
                "validation_passed",
                "Request validation successful",
                stage_name="validation",
                severity="info"
            )

        # ==================== STAGE 2: RAG Retrieval ====================
        with tracker.track_stage(request_id, "rag_retrieval"):
            tracker.log_event(
                request_id,
                "api_call",
                "Querying Vector Search for OER content",
                stage_name="rag_retrieval",
                severity="info"
            )

            # Check cache first
            cache_key = f"rag_results:{topic}"
            cached_results = cache.get(cache_key)

            if cached_results:
                rag_results = cached_results
                tracker.log_event(
                    request_id,
                    "cache_hit",
                    "Retrieved results from cache",
                    stage_name="rag_retrieval",
                    severity="info"
                )
            else:
                # Perform RAG retrieval
                rag_results = retrieve_oer_content(
                    topic=topic,
                    learning_objective=learning_objective,
                    top_k=5
                )

                # Cache for 1 hour
                cache.set(cache_key, rag_results, ttl=3600)

                tracker.log_event(
                    request_id,
                    "rag_completed",
                    f"Retrieved {len(rag_results)} content chunks",
                    stage_name="rag_retrieval",
                    severity="info",
                    event_data={"chunks": len(rag_results)}
                )

        # ==================== STAGE 3: Script Generation ====================
        tracker.start_stage(request_id, "script_generation")

        try:
            tracker.log_event(
                request_id,
                "api_call",
                "Calling Gemini API for script generation",
                stage_name="script_generation",
                severity="info"
            )

            # Call Gemini with circuit breaker protection
            @gemini_breaker
            def generate_script():
                return call_gemini_api(
                    topic=topic,
                    learning_objective=learning_objective,
                    context=rag_results,
                )

            script = generate_script()

            tracker.complete_stage(
                request_id,
                "script_generation",
                output_data={
                    "script_length": len(script),
                    "word_count": len(script.split()),
                }
            )

            tracker.log_event(
                request_id,
                "script_generated",
                f"Generated {len(script.split())} word script",
                stage_name="script_generation",
                severity="info"
            )

        except CircuitBreakerError as e:
            tracker.fail_stage(
                request_id,
                "script_generation",
                "Gemini API circuit breaker open",
                error_details={"circuit_breaker": "gemini_api"}
            )
            raise

        # ==================== STAGE 4: Video Generation ====================
        tracker.start_stage(request_id, "video_generation")

        try:
            tracker.log_event(
                request_id,
                "api_call",
                "Calling Nano Banana API for video generation",
                stage_name="video_generation",
                severity="info"
            )

            # Call Nano Banana with circuit breaker
            @nano_banana_breaker
            def generate_video():
                return call_nano_banana_api(
                    script=script,
                    duration_minutes=5,
                    style="educational",
                )

            video_job_id = generate_video()

            # Poll for completion (simplified)
            max_wait = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                video_status = check_nano_banana_status(video_job_id)

                if video_status["status"] == "completed":
                    video_url = video_status["video_url"]
                    break
                elif video_status["status"] == "failed":
                    raise Exception(f"Video generation failed: {video_status['error']}")

                tracker.log_event(
                    request_id,
                    "video_progress",
                    f"Video generation progress: {video_status['progress']}%",
                    stage_name="video_generation",
                    severity="info"
                )

                time.sleep(10)  # Poll every 10 seconds

            tracker.complete_stage(
                request_id,
                "video_generation",
                output_data={
                    "video_url": video_url,
                    "job_id": video_job_id,
                }
            )

        except CircuitBreakerError:
            tracker.fail_stage(
                request_id,
                "video_generation",
                "Nano Banana API circuit breaker open",
                error_details={"circuit_breaker": "nano_banana_api"}
            )
            raise

        # ==================== STAGE 5: Video Processing ====================
        with tracker.track_stage(request_id, "video_processing"):
            # Download video
            video_data = download_video(video_url)

            # Upload to Cloud Storage + CDN
            cdn_url = upload_to_cdn(
                video_data,
                filename=f"{request_id}.mp4"
            )

            # Generate thumbnail
            thumbnail_url = generate_thumbnail(video_data)

            tracker.log_event(
                request_id,
                "video_uploaded",
                f"Video uploaded to CDN: {cdn_url}",
                stage_name="video_processing",
                severity="info"
            )

        # ==================== STAGE 6: Notification ====================
        with tracker.track_stage(request_id, "notification"):
            # Send email to student
            send_email(
                to=student_email,
                template="content_ready",
                context={
                    "topic": topic,
                    "video_url": cdn_url,
                }
            )

            tracker.log_event(
                request_id,
                "notification_sent",
                f"Email sent to student",
                stage_name="notification",
                severity="info"
            )

        # ==================== Complete Request ====================
        tracker.complete_request(
            request_id,
            video_url=cdn_url,
            script_text=script,
            thumbnail_url=thumbnail_url,
        )

        print(f"✅ Request {request_id} completed successfully")

    except Exception as e:
        # Mark entire request as failed
        current_stage = tracker.get_request_status(request_id).get("current_stage", "unknown")

        tracker.fail_request(
            request_id,
            error_message=str(e),
            error_stage=current_stage,
            error_details={
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }
        )

        print(f"❌ Request {request_id} failed at {current_stage}: {e}")

        # Send error notification to student
        send_error_notification(student_id, topic, error=str(e))

        raise
```

---

## Error Handling

### Retry Failed Stages

```python
def retry_failed_request(db: Session, request_id: str):
    """Retry a failed request from the failed stage."""
    tracker = RequestTracker(db)

    status = tracker.get_request_status(request_id)

    if status["status"] != "failed":
        raise ValueError("Request is not in failed state")

    error_stage = status["error_stage"]

    # Check if retry is allowed
    if not tracker.retry_stage(request_id, error_stage):
        print(f"Max retries exceeded for {error_stage}")
        return False

    # Process from failed stage onwards
    process_content_request_from_stage(db, request_id, error_stage)
    return True
```

### Circuit Breaker Integration

```python
from app.services.circuit_breaker import CircuitBreakerError, nano_banana_breaker

def safe_api_call_with_tracking(db: Session, request_id: str):
    """API call with circuit breaker and request tracking."""
    tracker = RequestTracker(db)

    tracker.start_stage(request_id, "video_generation")

    try:
        @nano_banana_breaker
        def call_api():
            return external_api_call()

        result = call_api()

        tracker.complete_stage(request_id, "video_generation")
        return result

    except CircuitBreakerError as e:
        # Circuit is open
        tracker.fail_stage(
            request_id,
            "video_generation",
            "API circuit breaker is open",
            error_details={
                "circuit_breaker_state": "OPEN",
                "service": "nano_banana_api",
            },
            is_retryable=True  # Can retry later when circuit closes
        )

        # Log for monitoring
        tracker.log_event(
            request_id,
            "circuit_breaker_open",
            "Circuit breaker prevented API call",
            stage_name="video_generation",
            severity="warning"
        )

        raise
```

---

## Monitoring Dashboard

### Access the Dashboard

The monitoring dashboard is available at:

```
https://your-app.com/monitoring/dashboard
```

**Permissions:**
- Teachers can view requests from their organization
- Admins can view all requests

### API Endpoints

```python
# Get overview stats
GET /api/v1/monitoring/dashboard

# List active requests
GET /api/v1/monitoring/requests?status=active&limit=20

# Get request details
GET /api/v1/monitoring/requests/{request_id}

# Get event log
GET /api/v1/monitoring/requests/{request_id}/events

# Get metrics (hourly buckets)
GET /api/v1/monitoring/metrics?hours=24

# Real-time SSE stream
GET /api/v1/monitoring/stream
```

### Example: Query API from Code

```python
import requests

def get_request_status_api(request_id: str, token: str):
    """Get request status via API."""
    response = requests.get(
        f"https://api.vividly.edu/api/v1/monitoring/requests/{request_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.ok:
        return response.json()
    else:
        raise Exception(f"API error: {response.status_code}")
```

---

## Best Practices

### 1. Always Use Context Managers

```python
# ✅ Good - automatic error handling
with tracker.track_stage(request_id, "script_generation"):
    script = generate_script()

# ❌ Bad - manual error handling required
tracker.start_stage(request_id, "script_generation")
try:
    script = generate_script()
    tracker.complete_stage(request_id, "script_generation")
except Exception as e:
    tracker.fail_stage(request_id, "script_generation", str(e))
    raise
```

### 2. Log Important Events

```python
# Log API calls
tracker.log_event(
    request_id,
    "api_call",
    "Calling Gemini API",
    severity="info",
    event_data={"model": "gemini-1.5-pro"}
)

# Log performance metrics
tracker.log_event(
    request_id,
    "performance",
    f"Script generation took {duration}s",
    severity="info" if duration < 30 else "warning",
    event_data={"duration_seconds": duration}
)
```

### 3. Include Detailed Error Information

```python
tracker.fail_stage(
    request_id,
    "video_generation",
    error_message="Nano Banana API timeout",
    error_details={
        "status_code": 504,
        "response_body": response.text,
        "request_duration_seconds": duration,
        "retry_count": retry_count,
    },
    is_retryable=True
)
```

### 4. Use Correlation IDs for Distributed Tracing

```python
# Pass correlation ID to external services
headers = {
    "X-Correlation-ID": correlation_id,
    "Authorization": f"Bearer {api_key}",
}

response = requests.post(
    "https://api.nanobana.com/generate",
    headers=headers,
    json=payload
)
```

### 5. Monitor Circuit Breaker State

```python
from app.services.circuit_breaker import get_all_circuit_breaker_stats

def check_external_services_health():
    """Check if external services are healthy."""
    stats = get_all_circuit_breaker_stats()

    for service_name, breaker_stats in stats.items():
        if breaker_stats["state"] == "open":
            # Circuit is open - service is down
            send_alert(f"{service_name} circuit breaker is OPEN")

        failure_rate = (
            breaker_stats["total_failures"] / breaker_stats["total_calls"]
            if breaker_stats["total_calls"] > 0
            else 0
        )

        if failure_rate > 0.1:  # More than 10% failures
            send_warning(f"{service_name} failure rate is {failure_rate:.1%}")
```

---

## Summary

The request tracking system provides:

✅ **End-to-end visibility** - Track requests from submission to completion
✅ **Real-time monitoring** - Live dashboard with Server-Sent Events
✅ **Detailed event logs** - Debug issues with comprehensive event timeline
✅ **Performance metrics** - Measure duration at each stage
✅ **Error tracking** - Identify failure points and patterns
✅ **Circuit breaker integration** - Monitor external API health

**Result**: Complete observability into your content generation pipeline with clear identification of failures and bottlenecks.
