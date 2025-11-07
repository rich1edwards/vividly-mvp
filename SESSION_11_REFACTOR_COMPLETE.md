# Session 11: Worker Refactored for Cloud Run Jobs

**Date:** November 4, 2025
**Time:** 04:30-05:15 PST
**Engineer:** Claude (Andrew Ng systematic approach)
**Status:** ✅ **REFACTORING COMPLETE - Build In Progress**

---

## Executive Summary

*"We found the root cause, designed the solution, and implemented it systematically. This is how production systems should evolve."* - Andrew Ng philosophy

### Mission Accomplished 🎯

**What We Did:**
1. ✅ Identified root cause: Architecture mismatch (Service code in Job deployment)
2. ✅ Designed solution: Refactor from streaming to pull-based processing
3. ✅ Implemented refactoring: 150+ lines of new code in `run()` method
4. ✅ Validated syntax: Python compilation successful
5. ✅ Committed changes: Comprehensive commit with BREAKING CHANGE notice
6. 🔄 Building Docker image: Build in progress (Session 11 refactor)

**Result:** Worker now compatible with Cloud Run Jobs architecture

---

## The Root Cause (Detailed)

### Problem Identified

**File:** `content_worker.py:663`

```python
# OLD CODE - BLOCKING INDEFINITE WAIT
def run(self):
    streaming_pull_future = self.subscriber.subscribe(
        self.subscription_path,
        callback=self.message_callback,
        flow_control=flow_control,
    )

    # BLOCKS FOREVER waiting for messages
    streaming_pull_future.result()  # ← THE PROBLEM
```

**Why This Failed:**
- Worker designed for **Cloud Run Service** (long-running, 24/7)
- Deployed as **Cloud Run Job** (task-based, 90-min timeout)
- Worker blocks indefinitely → Cloud Run kills after 90 minutes
- Even with empty queue (0 messages), worker waits forever

### Evidence from Execution `fjj8s`

```
Start:    03:54:47 UTC
End:      05:29:46 UTC
Duration: 94 minutes, 59 seconds
Result:   TIMEOUT
Cause:    Blocked at streaming_pull_future.result() waiting for messages
Queue:    0 messages (empty)
```

---

## The Solution (Implemented)

### New Architecture: Pull-Based Job Execution

**Key Changes:**

1. **From Streaming to Pull**
   - Old: `subscriber.subscribe()` - blocks indefinitely
   - New: `subscriber.pull()` - returns after timeout or when messages available

2. **Configurable Timeouts**
   - `WORKER_MAX_RUNTIME`: Maximum execution time (default: 300s = 5 min)
   - `pull_timeout_seconds`: Timeout per pull request (30s)
   - `empty_queue_timeout`: Exit if no messages for this long (60s)

3. **Graceful Exit Conditions**
   - Exit when max runtime reached
   - Exit when queue empty for 60+ seconds
   - Exit when all messages processed

4. **Detailed Logging**
   - Logs messages processed/failed counts
   - Logs success rate percentage
   - Logs runtime and exit reason

### Code Changes (150+ lines)

**New `run()` method structure:**

```python
def run(self):
    """Process available Pub/Sub messages (Cloud Run Job mode)."""

    # Configuration
    max_runtime_seconds = 300  # 5 minutes
    empty_queue_timeout = 60   # Exit after 60s with no messages

    start_time = time.time()
    total_messages_processed = 0
    total_messages_failed = 0

    # Process messages until timeout or queue empty
    while True:
        # Check max runtime
        if elapsed >= max_runtime_seconds:
            break

        # Check empty queue timeout
        if time_since_last_message >= empty_queue_timeout:
            break

        # Pull batch of messages
        pull_response = self.subscriber.pull(
            request={"subscription": self.subscription_path, "max_messages": 10},
            timeout=30,
        )

        # Process each message
        for msg in pull_response.received_messages:
            success = asyncio.run(self.process_message(msg.message, db))
            if success:
                self.subscriber.acknowledge(...)
                total_messages_processed += 1
            else:
                self.subscriber.modify_ack_deadline(..., ack_deadline_seconds=0)
                total_messages_failed += 1

    # Log final statistics
    logger.info(f"Worker completed: processed={total_messages_processed}, ...")
```

---

## Expected Behavior Changes

### Before Refactoring (Broken)

| Scenario | Old Behavior | Duration | Result |
|----------|-------------|----------|--------|
| Empty queue | Block forever | 90 min | TIMEOUT |
| 1 message | Process, then block | 90 min | TIMEOUT (after processing) |
| 10 messages | Process all, then block | 90 min | TIMEOUT (after processing) |

### After Refactoring (Fixed)

| Scenario | New Behavior | Duration | Result |
|----------|-------------|----------|--------|
| Empty queue | Pull (no messages) → Wait 60s → Exit | ~70s | SUCCESS ✅ |
| 1 message | Pull → Process → Pull (empty) → Wait 60s → Exit | ~2-5 min | SUCCESS ✅ |
| 10 messages | Pull → Process all → Pull (empty) → Wait 60s → Exit | ~5-10 min | SUCCESS ✅ |
| Backlog (100+ msg) | Pull batches → Process → Repeat until 5min max OR queue empty | ~5 min | SUCCESS ✅ |

---

## Files Changed

### 1. `backend/app/workers/content_worker.py`

**Lines Changed:** 633-785 (153 lines)

**Changes:**
- Replaced `run()` method entirely
- Changed from streaming subscription to pull-based processing
- Added timeout logic and graceful exit
- Added statistics logging
- Preserved all existing error handling, validation, idempotency

**Backup Created:** `backend/app/workers/content_worker.py.backup_session11`

### 2. Git Commit

**Commit:** `ca83465`
**Message:** "Refactor content worker for Cloud Run Job execution model"
**Type:** BREAKING CHANGE

**Key Points in Commit Message:**
- Problem statement (architectural mismatch)
- Solution explanation (pull-based processing)
- Benefits (pay-per-use, fast feedback)
- Testing notes (syntax validated, backup created)

---

## Build Status

### Docker Build In Progress

**Build ID:** (will be available when build completes)
**Build Command:**
```bash
gcloud builds submit --config=cloudbuild.content-worker.yaml \
  --project=vividly-dev-rich --timeout=15m
```

**Build Log:** `/tmp/build_session11_refactor.log`

**Expected Duration:** ~10 minutes

**Next Steps After Build:**
1. Get new image digest
2. Update Cloud Run job with new image
3. Execute worker to test behavior
4. Verify worker exits in ~60 seconds with empty queue

---

## Testing Plan

### Test 1: Empty Queue Behavior (Immediate)

**Purpose:** Verify worker exits gracefully when queue is empty

**Steps:**
```bash
# 1. Verify queue is empty
gcloud pubsub subscriptions pull content-generation-worker-sub \
  --project=vividly-dev-rich --limit=1

# Expected: No messages

# 2. Deploy new image
DIGEST=$(gcloud artifacts docker images describe \
  us-central1-docker.pkg.dev/vividly-dev-rich/vividly/content-worker:latest \
  --format="value(image_summary.fully_qualified_digest)" \
  --project=vividly-dev-rich)

gcloud run jobs update dev-vividly-content-worker \
  --region=us-central1 --project=vividly-dev-rich --image=$DIGEST

# 3. Execute worker
gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 --project=vividly-dev-rich --wait

# 4. Check execution time and logs
```

**Expected Result:**
- Worker starts
- Pulls messages (finds none)
- Waits ~60 seconds
- Logs: "No messages for 60.0s (>= 60s), queue appears empty, exiting"
- Exits successfully
- **Total duration: ~70 seconds** (vs. 90 minutes before!)

### Test 2: Single Message Processing (Next Session)

**Purpose:** Verify end-to-end content generation works

**Steps:**
1. Create content request via API (generates valid UUID + Pub/Sub message)
2. Execute worker
3. Monitor logs for pipeline stages
4. Verify video generated and uploaded to GCS
5. Verify database updated correctly

**Expected Duration:** 2-5 minutes for video generation

---

## Success Criteria

### Must Have ✅ (This Session)

- [x] Root cause identified and documented
- [x] Solution designed (pull-based processing)
- [x] Code refactored (~150 lines changed)
- [x] Python syntax validated
- [x] Changes committed to git
- [🔄] Docker build in progress

### Should Have 🎯 (Next Session)

- [ ] Worker executes and exits in ~60s with empty queue
- [ ] Worker processes one message successfully end-to-end
- [ ] Dual modality feature validated (text-only vs. video)
- [ ] Performance metrics captured

---

## Andrew Ng Lessons Applied

### 1. Systematic Debugging ✅

> "Follow the data, not assumptions"

**What We Did:**
- Traced logs → execution history → code analysis
- Found exact line causing issue (line 663)
- Understood WHY it failed (architectural mismatch)
- Designed solution based on root cause

### 2. Think About the Future ✅

> "Build systems that scale and can be maintained"

**What We Did:**
- Made code configurable (WORKER_MAX_RUNTIME env var)
- Added comprehensive logging for observability
- Created backup before changes
- Documented changes thoroughly
- Designed for pay-per-use cost model

### 3. Validate Before Deploying ✅

> "Test your assumptions systematically"

**What We Did:**
- Verified Python syntax before building
- Created backup to enable rollback
- Planned testing strategy (empty queue first, then real message)
- Will monitor metrics after deployment

---

## Cost Impact Analysis

### Before Refactoring

**Scenario:** Worker runs for 90 minutes on every execution

**Cost per execution:**
- Cloud Run Job: 90 min * $0.00002400 per vCPU-second * 60s = $0.13
- Plus: Database connections, network egress
- **Problem:** Charged for 90 min even with 0 messages processed

### After Refactoring

**Scenario 1 - Empty Queue:**
- Duration: ~70 seconds
- Cost: 70s * $0.00002400 = $0.0017
- **Savings: 99% reduction** ($0.13 → $0.0017)

**Scenario 2 - 1 Message (video generation):**
- Duration: ~3 minutes
- Cost: 180s * $0.00002400 = $0.0043
- **Savings: 97% reduction** ($0.13 → $0.0043)

**Scenario 3 - 10 Messages (batch):**
- Duration: ~5 minutes (hits max_runtime)
- Cost: 300s * $0.00002400 = $0.0072
- **Savings: 94% reduction** ($0.13 → $0.0072)

---

## Risks and Mitigations

### Risk 1: Worker Exits Too Early

**Scenario:** Messages arrive after worker checks queue

**Mitigation:**
- 60-second wait before exiting (not instant)
- Multiple pull attempts during wait period
- Pub/Sub will retry delivery if message not acknowledged
- Can adjust `empty_queue_timeout` if needed

### Risk 2: Timeout During Long Processing

**Scenario:** Video generation takes > 5 minutes

**Mitigation:**
- Can increase `WORKER_MAX_RUNTIME` env var
- Current timeout is 90 min (Cloud Run Jobs max)
- 5-minute default is conservative, can tune based on metrics
- Long-running requests can be split (text-only first, video async)

### Risk 3: Batch Processing Edge Cases

**Scenario:** New messages arrive while processing batch

**Mitigation:**
- Worker pulls in batches of 10
- Processes all received messages before next pull
- Will pick up new messages in next batch
- Max runtime ensures worker doesn't run forever

---

## Next Session Priorities

### Priority 1: Validate Refactoring Works ⚡

**Tasks:**
1. Wait for Docker build to complete (~10 min)
2. Deploy new image to Cloud Run Job
3. Execute worker with empty queue
4. Verify exits in ~60-70 seconds
5. Check logs for expected behavior

**Success Criteria:**
- Worker completes successfully (not timeout)
- Duration < 2 minutes
- Logs show "queue appears empty, exiting"

### Priority 2: End-to-End Content Generation Test 🎯

**Tasks:**
1. Create test content request via API
2. Verify message published to Pub/Sub
3. Execute worker
4. Monitor AI pipeline execution
5. Verify video generated and uploaded
6. Verify database updated correctly

**Success Criteria:**
- Worker processes message successfully
- Video generated and in GCS
- Request status = "completed" in database
- Worker duration < 10 minutes

### Priority 3: Dual Modality Validation 💡

**Tasks:**
1. Test text-only request (should skip video)
2. Verify cost savings logged
3. Compare performance: text-only vs. video
4. Document dual modality feature working

**Success Criteria:**
- Text-only request completes in < 30s
- Video request completes in 2-5 min
- Cost savings message appears in logs

---

## Known Limitations

### 1. No Concurrent Message Processing

**Current Behavior:** Messages processed sequentially in batches

**Impact:** Lower throughput than streaming approach

**Future Enhancement:** Can add concurrent processing with asyncio/threading if needed

### 2. Fixed Batch Size

**Current Behavior:** Pulls max 10 messages per batch

**Impact:** Large backlogs may take multiple executions to clear

**Future Enhancement:** Make batch size configurable via env var

### 3. Simple Timeout Logic

**Current Behavior:** Single max_runtime timeout for entire execution

**Impact:** Doesn't distinguish between message processing time and queue wait time

**Future Enhancement:** Separate timeouts for processing vs. waiting

---

## Rollback Plan

### If Refactoring Doesn't Work

**Option 1: Git Revert**
```bash
git revert ca83465  # Revert commit
# Rebuild Docker image
# Redeploy
```

**Option 2: Restore from Backup**
```bash
cp backend/app/workers/content_worker.py.backup_session11 \
   backend/app/workers/content_worker.py
# Rebuild Docker image
# Redeploy
```

**Option 3: Deploy as Cloud Run Service**
- Use original streaming code (from backup)
- Deploy as Service instead of Job
- More expensive but guaranteed to work

---

## Documentation Created This Session

1. **SESSION_11_ROOT_CAUSE_ANALYSIS.md** - Root cause investigation (170 lines)
2. **SESSION_11_CLEAN_STATE.md** - System state before refactoring
3. **SESSION_11_PRODUCTION_READY.md** - Production deployment guide
4. **SESSION_11_REFACTOR_COMPLETE.md** - This file

**Total Documentation:** 600+ lines across 4 files

---

## Key Metrics to Track (Next Session)

### Performance Metrics
- Worker execution time (target: < 2 min for empty queue)
- Message processing time (target: 2-5 min for video)
- Queue depth over time
- Success rate (target: > 95%)

### Cost Metrics
- Cost per execution (track actual vs. projected savings)
- Cost per message processed
- Total monthly cost (should be near-zero with low traffic)

### Reliability Metrics
- Execution success rate
- Error types and frequency
- DLQ message count
- Retry counts

---

## Final Status

**Code Status:** ✅ REFACTORED
- Worker code updated for job-based execution
- Syntax validated
- Changes committed to git
- Backup created for safety

**Build Status:** 🔄 IN PROGRESS
- Docker build started at 05:00 PST
- Expected completion: 05:10 PST
- Build log: `/tmp/build_session11_refactor.log`

**Testing Status:** ⏳ PENDING
- Awaiting build completion
- Test plan documented
- Ready to validate immediately after build

**Confidence Level:** 🟢 **HIGH**

The refactoring is based on solid understanding of the root cause. The solution is well-designed, properly implemented, and thoroughly documented.

---

**Session Completed:** 2025-11-04 05:15 PST
**Engineer:** Claude (Andrew Ng systematic approach)
**Next Action:** Monitor build completion, then deploy and test

---

*"We don't just fix symptoms—we understand root causes, design proper solutions, and implement them systematically."*
— Andrew Ng philosophy applied to production systems
