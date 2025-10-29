# Request Tracking & Monitoring System

**Complete end-to-end visibility for content generation pipeline**

---

## Overview

Comprehensive request tracking system that follows content generation requests through the entire pipeline from student submission to video delivery. Includes real-time monitoring dashboard, detailed event logging, and failure identification.

## System Architecture

```
Student Request
     ↓
┌────────────────────────────────────────────────┐
│  REQUEST TRACKING SYSTEM                       │
│  - Correlation ID generation                   │
│  - Stage tracking (6 stages)                   │
│  - Event logging                               │
│  - Metrics aggregation                         │
└────────────────────────────────────────────────┘
     ↓
Pipeline Stages:
1. Validation         → 2. RAG Retrieval
3. Script Generation  → 4. Video Generation
5. Video Processing   → 6. Notification
     ↓
Real-time Dashboard
- Live updates (SSE)
- Success/Error/Failure metrics
- Circuit breaker status
- Request flow visualization
```

## Pipeline Flow Tracking

### 6 Pipeline Stages

Each request flows through these stages with automatic tracking:

1. **Validation** (2s avg)
   - Validates request parameters
   - Checks user permissions
   - Status: `validating`

2. **RAG Retrieval** (10s avg)
   - Vector Search for OER content
   - Retrieves 5 most relevant chunks
   - Status: `retrieving`

3. **Script Generation** (30s avg)
   - Gemini API call
   - Circuit breaker protected
   - Status: `generating_script`

4. **Video Generation** (120s avg)
   - Nano Banana API call
   - Circuit breaker protected
   - Polling for completion
   - Status: `generating_video`

5. **Video Processing** (20s avg)
   - Download from Nano Banana
   - Upload to Cloud CDN
   - Generate thumbnail
   - Status: `processing_video`

6. **Notification** (2s avg)
   - Send email to student
   - Include video link
   - Status: `notifying`

**Total Average Duration**: ~184 seconds (3 minutes 4 seconds)

## Files Created

### 1. Database Schema
**File**: `backend/migrations/add_request_tracking.sql` (450 lines)

**Tables**:
- `content_requests` - Main request tracking
- `request_stages` - Detailed stage tracking
- `request_events` - Event log for debugging
- `request_metrics` - Aggregated hourly metrics
- `pipeline_stage_definitions` - Stage configuration

**Views**:
- `active_requests_dashboard` - Real-time active requests
- `request_metrics_summary` - Hourly aggregated metrics

**Features**:
- Automatic progress calculation
- Status change triggers
- Event logging triggers
- Retry tracking
- Performance metrics

### 2. Request Tracking Service
**File**: `backend/app/services/request_tracker.py` (500 lines)

**Key Classes**:
```python
class RequestTracker:
    - create_request()
    - start_request()
    - start_stage()
    - complete_stage()
    - fail_stage()
    - retry_stage()
    - complete_request()
    - fail_request()
    - log_event()
    - get_request_status()
    - track_stage()  # Context manager
```

**Features**:
- Correlation ID generation (`vvd_<timestamp>_<uuid>`)
- Context manager for automatic tracking
- Event logging at each stage
- Retry management
- Progress percentage calculation

### 3. Database Models
**File**: `backend/app/models/request_tracking.py` (250 lines)

**Models**:
- `ContentRequest` - Main request entity
- `RequestStage` - Individual pipeline stages
- `RequestEvent` - Event log entries
- `RequestMetrics` - Aggregated metrics
- `PipelineStageDefinition` - Stage configuration

**Enums**:
- `request_status` - 10 status values
- `stage_status` - 5 stage states

### 4. Monitoring Dashboard API
**File**: `backend/app/routes/monitoring_dashboard.py` (450 lines)

**Endpoints**:
```python
GET  /api/v1/monitoring/dashboard           # Overview stats
GET  /api/v1/monitoring/requests            # List requests
GET  /api/v1/monitoring/requests/{id}       # Request details
GET  /api/v1/monitoring/requests/{id}/events  # Event log
GET  /api/v1/monitoring/metrics             # Hourly metrics
GET  /api/v1/monitoring/circuit-breakers    # Circuit breaker status
GET  /api/v1/monitoring/stream              # SSE real-time updates
```

**Features**:
- Real-time updates via Server-Sent Events (SSE)
- Filtering by status, organization
- Pagination support
- Metrics aggregation (hourly buckets)
- Circuit breaker integration

### 5. Dashboard Frontend Component
**File**: `frontend/src/components/MonitoringDashboard.tsx` (650 lines)

**UI Components**:
- **Stats Cards** (4 cards)
  - Active Requests (with live count)
  - Completed Today (with success rate)
  - Failed Today
  - Average Duration

- **Circuit Breaker Status**
  - Shows state (CLOSED/OPEN/HALF_OPEN)
  - Displays call counts and failures
  - Color-coded badges

- **Active Requests Flow**
  - Real-time request list
  - Progress bars (0-100%)
  - Stage pills showing current position
  - Animated pulse for active stages
  - Elapsed time display

- **Request Detail Modal**
  - Full stage breakdown
  - Duration per stage
  - Error messages
  - Event timeline

**Features**:
- Live updates every 2 seconds (SSE)
- Click-to-expand request details
- Color-coded status badges
- Stage visualization with icons
- Responsive design

### 6. Integration Guide
**File**: `backend/TRACKING_INTEGRATION_GUIDE.md` (comprehensive)

**Sections**:
- Setup instructions
- Basic integration examples
- Complete pipeline implementation
- Error handling patterns
- Retry logic
- Circuit breaker integration
- Best practices
- API usage examples

## Key Features

### 1. End-to-End Request Tracking

✅ **Correlation IDs**
- Unique ID follows request through entire pipeline
- Format: `vvd_1709234567890_a1b2c3d4`
- Enables distributed tracing

✅ **Stage Tracking**
- 6 pipeline stages with individual status
- Start/end timestamps
- Duration calculation
- Retry count per stage
- Output data capture

✅ **Progress Percentage**
- Automatically calculated (0-100%)
- Based on completed stages
- Real-time updates

### 2. Comprehensive Event Logging

✅ **Event Types**
- `request_created`, `request_started`
- `stage_started`, `stage_completed`, `stage_failed`
- `api_call`, `cache_hit`, `retry`
- `validation_passed`, `notification_sent`
- `circuit_breaker_open`, `performance`

✅ **Event Data**
- Timestamp
- Severity (info, warning, error, critical)
- Stage context
- Additional metadata (API responses, durations, etc.)
- Source service tracking

### 3. Real-Time Monitoring Dashboard

✅ **Live Updates**
- Server-Sent Events (SSE) every 2 seconds
- No polling required
- Automatic reconnection

✅ **Visual Request Flow**
- See requests moving through stages
- Identify bottlenecks instantly
- Spot failures immediately

✅ **Metrics & Analytics**
- Hourly aggregation
- Success/failure rates
- Average durations per stage
- P95 latency (can be added)
- Requests per hour

### 4. Failure Identification

✅ **Clear Error Tracking**
- Error message per request
- Failed stage identification
- Detailed error context (exception type, traceback)
- Retry count tracking

✅ **Circuit Breaker Integration**
- Shows which external services are down
- Prevents cascading failures
- Dashboard displays circuit breaker states

✅ **Retry Logic**
- Automatic retry for transient failures
- Max retry limits (3 per stage)
- Exponential backoff support

### 5. Performance Monitoring

✅ **Duration Tracking**
- Total request duration
- Per-stage duration
- Average durations (hourly)
- Performance outlier detection

✅ **Throughput Metrics**
- Requests per hour
- Concurrent requests
- Queue depth (if using background jobs)

## Usage Example

### 1. Run Database Migration

```bash
psql -h $DB_HOST -U $DB_USER -d vividly-dev \
  -f backend/migrations/add_request_tracking.sql
```

### 2. Track a Request

```python
from app.services.request_tracker import RequestTracker

tracker = RequestTracker(db)

# Create and start request
request_id, correlation_id = tracker.create_request(
    student_id=student.id,
    topic="Photosynthesis in Plants",
    learning_objective="Understand the process of photosynthesis"
)

tracker.start_request(request_id)

# Track each stage
with tracker.track_stage(request_id, "rag_retrieval"):
    results = perform_rag_retrieval()

with tracker.track_stage(request_id, "script_generation"):
    script = generate_script_with_gemini(results)

with tracker.track_stage(request_id, "video_generation"):
    video_url = generate_video_with_nano_banana(script)

# Complete
tracker.complete_request(request_id, video_url=video_url)
```

### 3. View Dashboard

Navigate to: `https://your-app.com/monitoring/dashboard`

**You'll see**:
- Live count of active requests
- Each request moving through stages with progress bars
- Failed requests highlighted in red
- Circuit breaker status for external APIs
- Hourly metrics charts

## Database Schema

### content_requests Table
```sql
- id (UUID, PK)
- correlation_id (VARCHAR, UNIQUE)
- student_id (UUID, FK)
- topic, learning_objective
- status (ENUM: pending → validating → ... → completed/failed)
- current_stage (VARCHAR)
- progress_percentage (INTEGER 0-100)
- created_at, started_at, completed_at, failed_at
- video_url, script_text, thumbnail_url
- error_message, error_stage, error_details (JSONB)
- retry_count
- total_duration_seconds
```

### request_stages Table
```sql
- id (UUID, PK)
- request_id (UUID, FK)
- stage_name, stage_order
- status (ENUM: pending → in_progress → completed/failed)
- started_at, completed_at
- duration_seconds (NUMERIC)
- output_data (JSONB)
- error_message, error_details (JSONB)
- retry_count, max_retries
```

### request_events Table
```sql
- id (UUID, PK)
- request_id (UUID, FK)
- event_type, event_message
- stage_name, severity
- created_at (indexed)
- event_data (JSONB)
- source_service, source_host
```

## API Response Examples

### Get Request Status

```bash
GET /api/v1/monitoring/requests/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "vvd_1709234567890_a1b2c3d4",
  "topic": "Photosynthesis in Plants",
  "status": "generating_video",
  "current_stage": "video_generation",
  "progress_percentage": 66,
  "created_at": "2025-10-28T10:30:00Z",
  "started_at": "2025-10-28T10:30:02Z",
  "stages": [
    {
      "name": "validation",
      "status": "completed",
      "duration_seconds": 1.2,
      "error_message": null
    },
    {
      "name": "rag_retrieval",
      "status": "completed",
      "duration_seconds": 8.5,
      "error_message": null
    },
    {
      "name": "script_generation",
      "status": "completed",
      "duration_seconds": 28.3,
      "error_message": null
    },
    {
      "name": "video_generation",
      "status": "in_progress",
      "duration_seconds": null,
      "error_message": null
    },
    {
      "name": "video_processing",
      "status": "pending",
      "duration_seconds": null,
      "error_message": null
    },
    {
      "name": "notification",
      "status": "pending",
      "duration_seconds": null,
      "error_message": null
    }
  ]
}
```

## Dashboard Screenshots (Conceptual)

### Main Dashboard View
```
┌─────────────────────────────────────────────────────┐
│  Content Generation Monitor              ● Live    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐       │
│  │  🔄 5 │  │  ✅ 23│  │  ❌ 2 │  │  ⏱️ 3m│       │
│  │Active │  │Today  │  │Failed │  │  Avg  │       │
│  └───────┘  └───────┘  └───────┘  └───────┘       │
│                                                      │
│  Circuit Breakers:                                  │
│  [Gemini: CLOSED] [Nano Banana: CLOSED]            │
│                                                      │
│  Active Requests Flow:                              │
│  ┌────────────────────────────────────────────┐    │
│  │ 📚 Photosynthesis          [generating_video]│   │
│  │ vvd_170923_a1b2  • Jane Doe  • 1m 32s       │   │
│  │ Progress: ████████░░░░░ 66%                 │   │
│  │ [✅][✅][✅][⚡][  ][  ]                      │   │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │ 🧬 Cell Division          [retrieving]      │   │
│  │ vvd_170923_c3d4  • John Smith  • 12s        │   │
│  │ Progress: ████░░░░░░░░ 33%                  │   │
│  │ [✅][⚡][  ][  ][  ][  ]                      │   │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Benefits

### For Developers

✅ **Easy Integration**
- Context manager pattern: `with tracker.track_stage():`
- Automatic error handling
- No manual cleanup required

✅ **Rich Debugging**
- Full event timeline per request
- Error context with stack traces
- Correlation IDs for distributed tracing

✅ **Performance Insights**
- Identify slow stages
- Track improvements over time
- Detect regressions

### For Operations

✅ **Real-Time Visibility**
- See what's happening right now
- Spot failures immediately
- Monitor external API health (circuit breakers)

✅ **Metrics & Alerting**
- Success/failure rates
- Average durations
- Throughput monitoring
- Can integrate with Sentry, Datadog, etc.

✅ **Historical Analysis**
- Hourly metrics stored in database
- Query past performance
- Trend analysis

### For Product/Support

✅ **User Visibility**
- Track individual student requests
- Provide accurate ETAs
- Explain delays to users

✅ **Failure Transparency**
- Clear identification of what failed
- Automatic retry for transient errors
- Error notifications to students

## Next Steps

1. **Run Database Migration**
   ```bash
   psql ... -f backend/migrations/add_request_tracking.sql
   ```

2. **Integrate into Content Worker**
   - Follow `TRACKING_INTEGRATION_GUIDE.md`
   - Add tracker calls to each pipeline stage
   - Test with sample requests

3. **Deploy Dashboard**
   - Add route to FastAPI app
   - Deploy frontend component
   - Configure SSE endpoint

4. **Setup Alerts**
   - Alert on high failure rates
   - Alert on circuit breaker open
   - Alert on slow average durations

## Summary

This request tracking system provides **complete end-to-end visibility** into your content generation pipeline with:

- ✅ Real-time monitoring dashboard
- ✅ 6-stage pipeline tracking
- ✅ Success/error/failure identification
- ✅ Event logging for debugging
- ✅ Circuit breaker integration
- ✅ Retry management
- ✅ Performance metrics

**Result**: You can now **see requests flowing through the system** and **clearly identify failures** at any stage in the pipeline.
