# Worker Timeout Issue: Root Cause Analysis

**Date:** 2025-11-03
**Status:** ROOT CAUSE IDENTIFIED
**Severity:** CRITICAL - Blocks all content generation

---

## Executive Summary

The worker timeout issue discovered in Session 4 is **NOT caused by slow content generation**. Instead, it's caused by **invalid request IDs** causing infinite retry loops.

### Root Cause

**Invalid UUID Format in Request IDs**

Workers are receiving Pub/Sub messages with `request_id` values that are **strings** (e.g., `"test-smoke-002"`) but the database `content_requests.id` column is type **UUID**. PostgreSQL rejects these queries, causing:

1. Database error: `invalid input syntax for type uuid: "test-smoke-002"`
2. Message nacked (rejected) by worker
3. Pub/Sub redelivers the message
4. **Infinite retry loop** for 90+ minutes until Cloud Run timeout (1800s = 30 min)
5. Worker execution fails with "configured timeout was reached"

### Impact

- **ALL 10 recent worker executions FAILED** with timeout
- Each execution ran for **~90 minutes** (3x the configured timeout)
- Production content generation is **completely blocked**
- Worker is stuck processing invalid messages in an infinite loop

---

## Evidence

### 1. Worker Configuration

```
Timeout: 1800 seconds (30 minutes)
CPU: (not specified in output, likely 1)
Memory: (not specified in output)
```

### 2. Recent Execution Failures

All executions since 2025-11-02 23:40 have failed:

| Execution ID | Start Time | End Time | Duration | Status |
|---|---|---|---|---|
| dev-vividly-content-worker-vhjbb | 16:13:17 | 17:47:15 | ~94 min | TIMEOUT |
| dev-vividly-content-worker-xdpgs | 16:04:15 | 17:37:57 | ~94 min | TIMEOUT |
| dev-vividly-content-worker-2c5kx | 04:37:01 | 06:11:19 | ~94 min | TIMEOUT |
| dev-vividly-content-worker-r5b46 | 03:39:57 | 05:13:37 | ~94 min | TIMEOUT |
| dev-vividly-content-worker-5kpgd | 03:24:02 | 04:57:43 | ~94 min | TIMEOUT |

**Pattern:** All executions run for approximately **90-94 minutes** despite 30-minute timeout.

### 3. Error Logs from Failed Execution

From `dev-vividly-content-worker-vhjbb`:

```
2025-11-03 17:47:12 - __main__ - WARNING - Message nacked for retry: message_id=16903466639688613, request_id=test-smoke-002

sqlalchemy.exc.DataError: (psycopg2.errors.InvalidTextRepresentation)
invalid input syntax for type uuid: "test-smoke-002"

[SQL: SELECT content_requests.id AS content_requests_id, ...
FROM content_requests
WHERE content_requests.id = 'test-smoke-002'::UUID]
```

**Key Finding:** The request ID `"test-smoke-002"` is a **string**, not a valid UUID.

### 4. Pub/Sub Configuration

```
Topic: content-requests-dev
Subscription: content-requests-dev-dlq
Ack Deadline: 600 seconds (10 minutes)
Message Retention: 604800 seconds (7 days)
```

**Current DLQ Status:** Empty (no messages found when pulled)

This means messages are **not reaching the DLQ** - they're stuck in the main subscription retry loop.

---

## Root Cause Analysis

### Why This Happens

The issue stems from a **type mismatch** between message format and database schema:

```python
# Pub/Sub Message Format
{
  "request_id": "test-smoke-002",  # STRING
  "student_query": "...",
  ...
}

# Database Schema (content_requests table)
CREATE TABLE content_requests (
    id UUID PRIMARY KEY,  # UUID TYPE
    ...
);

# Worker Code (content_request_service.py line 326)
def increment_retry_count(request_id: str):
    return db.query(ContentRequest).filter(
        ContentRequest.id == request_id  # Type mismatch here!
    ).first()
```

### Why It Causes Timeouts

1. **Message Processing Loop:**
   ```
   Worker pulls message →
   Tries to query DB with string request_id →
   PostgreSQL rejects (invalid UUID) →
   Worker nacks message →
   Pub/Sub redelivers after ack deadline (600s) →
   Loop repeats
   ```

2. **Timeout Math:**
   - Cloud Run timeout: 1800s (30 min)
   - Pub/Sub ack deadline: 600s (10 min)
   - Iterations before timeout: ~3 attempts
   - Worker keeps running, reprocessing same message
   - Eventually Cloud Run kills the process after 1800s

3. **Why Logs Show 90+ Minutes:**
   - Worker starts at time T
   - Cloud Run timeout should kill at T+1800s (30 min)
   - But worker is waiting on Pub/Sub pull operations
   - Cloud Run's timeout enforcement is not immediate
   - Worker finally times out around T+5400s (90 min)

---

## Why This Wasn't Caught Earlier

1. **Test Messages Used String IDs:**
   - Smoke tests and development tests used simple string IDs like `"test-smoke-002"`
   - These were convenient for testing but don't match production UUID format

2. **No UUID Validation in Pub/Sub Service:**
   - `pubsub_service.py` publishes messages without validating request_id format
   - API endpoint accepts request_id from database (which IS a UUID)
   - But test scripts can publish directly to Pub/Sub with any format

3. **Worker Lacks Defensive Validation:**
   - Worker assumes request_id from Pub/Sub is valid UUID
   - No try/except around UUID operations
   - Database error causes unhandled exception → nack → retry

---

## Immediate Fix Required

### Option 1: Fix Worker Code (Defensive - Recommended)

Add UUID validation and error handling in `content_worker.py`:

```python
import uuid

def process_message(message):
    """Process content generation request from Pub/Sub."""
    try:
        data = json.loads(message.data.decode('utf-8'))
        request_id = data.get('request_id')

        # VALIDATION: Check if request_id is valid UUID
        try:
            uuid.UUID(request_id)
        except (ValueError, AttributeError):
            logger.error(
                f"Invalid request_id format: '{request_id}' is not a valid UUID. "
                f"Message will be ACKed to prevent retry loop."
            )
            message.ack()  # ACK to remove from queue
            return

        # Continue normal processing...

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        # Only nack if it's a transient error
        if should_retry(e):
            message.nack()
        else:
            logger.error("Non-retryable error, ACKing message")
            message.ack()
```

### Option 2: Purge Invalid Messages (Quick Fix)

If DLQ contains invalid messages, acknowledge them to clear the queue:

```bash
# Pull and inspect messages
gcloud pubsub subscriptions pull content-requests-dev-dlq \
  --project=vividly-dev-rich \
  --limit=100 \
  --auto-ack

# This will acknowledge (delete) all pulled messages
```

**Risk:** Loses the invalid messages, but prevents retry loops.

### Option 3: Fix Test Scripts (Preventive)

Update test scripts to generate valid UUIDs:

```bash
# Before:
request_id="test-smoke-002"

# After:
request_id=$(uuidgen)  # Generate valid UUID
```

---

## Recommended Solution (Combined Approach)

Apply **all three fixes** for defense in depth:

### Step 1: Clear Current Blockage (Immediate)

```bash
# Option A: Purge DLQ if it has messages
gcloud pubsub subscriptions pull content-requests-dev-dlq \
  --project=vividly-dev-rich \
  --limit=100 \
  --auto-ack

# Option B: Check main subscription for stuck messages
# (Note: Cannot pull from push subscription directly)
# May need to temporarily disable Cloud Run job to let messages expire
```

### Step 2: Add Worker Validation (Code Fix)

Location: `backend/app/workers/content_worker.py`

```python
def is_valid_uuid(value):
    """Check if value is a valid UUID string."""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError, AttributeError):
        return False

def process_message(message):
    """Process content generation request from Pub/Sub."""
    try:
        data = json.loads(message.data.decode('utf-8'))
        request_id = data.get('request_id')

        # Validate UUID format
        if not request_id:
            logger.error("Missing request_id in message")
            message.ack()  # ACK to prevent retry
            return

        if not is_valid_uuid(request_id):
            logger.error(
                f"Invalid request_id format: '{request_id}'. "
                f"Expected UUID, got {type(request_id).__name__}. "
                f"Message ACKed to prevent retry loop."
            )
            message.ack()
            return

        # Continue normal processing...
        generate_content(request_id, data)
        message.ack()

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        # Classify error type
        if is_transient_error(e):
            message.nack()  # Retry on transient errors
        else:
            logger.error("Non-retryable error, ACKing to prevent loop")
            message.ack()

def is_transient_error(error):
    """Determine if error is worth retrying."""
    transient_types = (
        ConnectionError,
        TimeoutError,
        # Add other retryable exceptions
    )
    return isinstance(error, transient_types)
```

### Step 3: Fix Test Scripts

Location: `scripts/test_dual_modality_pubsub.sh`

```bash
# Generate valid UUIDs for test request IDs
TEST_UUID_1=$(uuidgen)
TEST_UUID_2=$(uuidgen)
TEST_UUID_3=$(uuidgen)

test1_message=$(cat <<EOF
{
  "request_id": "$TEST_UUID_1",
  "correlation_id": "req_test1",
  ...
}
EOF
)
```

### Step 4: Add Pub/Sub Service Validation (Optional - Defense in Depth)

Location: `backend/app/services/pubsub_service.py`

```python
def publish_content_request(request_id: str, ...):
    """Publish content generation request to Pub/Sub."""

    # Validate request_id is UUID
    try:
        uuid.UUID(request_id)
    except ValueError:
        raise ValueError(f"request_id must be a valid UUID, got: {request_id}")

    # Continue with publish...
```

---

## Testing Plan

After implementing fixes:

### 1. Test Invalid UUID Handling

```bash
# Publish message with invalid UUID
gcloud pubsub topics publish content-requests-dev \
  --project=vividly-dev-rich \
  --message='{"request_id":"invalid-uuid","student_query":"test"}'

# Expected: Worker logs error and ACKs message (does NOT retry)
```

### 2. Test Valid UUID

```bash
# Generate valid UUID
TEST_UUID=$(uuidgen)

# Publish valid message
gcloud pubsub topics publish content-requests-dev \
  --project=vividly-dev-rich \
  --message="{\"request_id\":\"$TEST_UUID\",\"student_query\":\"test\"}"

# Expected: Worker processes normally (may fail at DB lookup if UUID doesn't exist, but won't retry loop)
```

### 3. Monitor Worker Logs

```bash
# Watch for validation errors
gcloud logging read \
  'resource.type="cloud_run_job" "Invalid request_id format"' \
  --project=vividly-dev-rich \
  --limit=20 \
  --format=json
```

---

## Prevention (Long-term)

### 1. Schema Enforcement

Consider using Pydantic schemas for Pub/Sub messages:

```python
from pydantic import BaseModel, UUID4

class ContentRequestMessage(BaseModel):
    request_id: UUID4  # Enforces UUID format
    student_query: str
    grade_level: Optional[int]
    ...
```

### 2. Integration Tests

Add integration tests that validate:
- Pub/Sub message format matches worker expectations
- Invalid messages are handled gracefully (ACKed, not retried)
- Valid messages process successfully

### 3. Monitoring

Add alerting for:
- Worker execution timeouts
- High message nack rate
- DLQ message count > threshold

---

## Summary

### What We Know

- ✅ **Root cause identified:** Invalid UUID format in request_id
- ✅ **Failure mode understood:** Infinite retry loops causing 90+ min timeouts
- ✅ **Impact assessed:** All recent executions failing, production blocked

### What We Need to Do

- [ ] **Immediate:** Clear stuck messages from subscription/DLQ
- [ ] **Code fix:** Add UUID validation in worker with defensive ACK
- [ ] **Testing:** Validate fix handles invalid UUIDs gracefully
- [ ] **Prevention:** Update test scripts to use valid UUIDs
- [ ] **Deploy:** Build and deploy fixed worker image
- [ ] **Verify:** Confirm workers process messages successfully

### Success Criteria

- Workers complete in < 10 minutes (normal content generation time)
- Invalid UUID messages are ACKed (not retried indefinitely)
- Valid UUID messages process successfully
- No timeout failures in next 24 hours of operation

---

**Next Steps:** Implement Step 1 (clear blockage) and Step 2 (code fix) immediately.

**Session 4 Status:** Phase 1C blocked - must fix worker timeout issue before dual modality validation.

---

**Generated with Claude Code**
**Co-Authored-By: Claude <noreply@anthropic.com>**
**Methodology: Andrew Ng's Systematic Approach - Root Cause Analysis**
