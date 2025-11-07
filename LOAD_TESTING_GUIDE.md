# Vividly Content Worker - Load Testing Guide

**Systematic Approach to Concurrent Request Validation**

---

## Philosophy: Andrew Ng's Engineering Approach

**"Don't assume it works under load - measure and validate systematically."**

This guide follows systematic engineering principles:
1. **Define Success Criteria** - What does "handles concurrent requests" mean?
2. **Design Measurable Tests** - Quantitative metrics, not gut feelings
3. **Start Small, Scale Gradually** - 10 → 50 → 100 → 1000 requests
4. **Measure Everything** - Latency, throughput, errors, resource usage
5. **Iterate Based on Data** - Fix bottlenecks, re-test, validate improvements

---

## Test Design

### Success Criteria

**Primary Metrics:**
1. **Processing Rate:** All published messages must be processed
2. **Success Rate:** >95% of messages complete successfully
3. **No Crashes:** Worker exits with code 0
4. **No Data Loss:** Every message either succeeds or goes to DLQ
5. **Graceful Degradation:** System handles failures without cascading

**Performance Benchmarks:**
- **Throughput:** Target >2 messages/second (conservative baseline)
- **Latency:** <30s per message end-to-end (with mock mode)
- **Error Rate:** <5% under normal conditions
- **Resource Usage:** <2GB memory, <1 vCPU per task

---

## Test Scenarios

### Scenario 1: Basic Concurrency (10 Messages)

**Purpose:** Validate worker handles multiple messages without errors

**Configuration:**
- Concurrent requests: 10
- Message variety: 10 different queries/interests
- Expected duration: ~60s
- Success threshold: 100% processed

**Command:**
```bash
./scripts/test_concurrent_requests.sh
```

**What We're Testing:**
- Pub/Sub message ordering
- Worker pulls multiple messages
- No message collision/duplication
- Proper message acknowledgment
- Database connection pooling

---

### Scenario 2: Medium Load (50 Messages)

**Purpose:** Stress test database and Pub/Sub subscription

**Configuration:**
- Concurrent requests: 50
- Expected duration: ~3-5 minutes
- Success threshold: >95% processed

**Command:**
```bash
# Edit script: NUM_CONCURRENT_REQUESTS=50
./scripts/test_concurrent_requests.sh
```

**What We're Testing:**
- Database connection limits
- Pub/Sub throughput
- Worker task count scaling
- Memory pressure under load
- Retry logic effectiveness

---

### Scenario 3: High Load (100+ Messages)

**Purpose:** Find system limits and bottlenecks

**Configuration:**
- Concurrent requests: 100-1000
- Expected duration: 10-30 minutes
- Success threshold: >90% processed

**Command:**
```bash
# Edit script: NUM_CONCURRENT_REQUESTS=100
./scripts/test_concurrent_requests.sh
```

**What We're Testing:**
- Maximum throughput
- Queue saturation behavior
- DLQ routing under pressure
- Cloud Run scaling limits
- Cost at scale

---

## Test Script Architecture

### File: `scripts/test_concurrent_requests.sh`

**Design Principles:**
1. **Reproducible** - Timestamped runs, saved logs
2. **Observable** - Detailed metrics, clear reporting
3. **Automated** - Single command, no manual steps
4. **Comprehensive** - Tests full pipeline end-to-end

**Test Flow:**
```
1. Publish Messages (parallel)
   ├─ Generate diverse test data
   ├─ Publish to Pub/Sub concurrently
   └─ Record message IDs

2. Execute Worker
   ├─ Trigger Cloud Run job
   ├─ Wait for completion
   └─ Capture execution logs

3. Analyze Results
   ├─ Count processed vs published
   ├─ Calculate success/failure rates
   ├─ Identify error patterns
   └─ Measure throughput

4. Generate Report
   ├─ Summary statistics
   ├─ Performance metrics
   └─ Pass/fail determination
```

---

## Metrics Collected

### Message Processing Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Published** | Messages sent to Pub/Sub | N (test size) |
| **Processed** | Messages worker attempted | = Published |
| **Successful** | Messages completed without errors | >95% of Published |
| **Failed** | Messages that errored out | <5% of Published |
| **Throughput** | Messages/second | >2 msg/s |

### System Health Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Errors** | ERROR level log entries | <10 per run |
| **Warnings** | WARNING level log entries | <50 per run |
| **Timeouts** | Messages that timed out | 0 |
| **DB Errors** | Database connection/query failures | 0 |
| **API Errors** | Vertex AI API errors | Expected (mock mode) |

### Resource Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Duration** | Worker execution time | <N*3 seconds |
| **Memory** | Peak memory usage | <2GB |
| **CPU** | Peak CPU utilization | <100% |
| **Tasks** | Concurrent worker tasks | Auto-scaled |

---

## Expected Behavior

### With Mock Mode (Current State)

**Flow:**
```
Message → Worker → NLU (gemini-1.5-flash attempt) → 404
                → Fallback to mock
                → Script Gen (gemini-1.5-flash attempt) → 404
                → Fallback to mock
                → Interest Match → Mock fallback
                → Success ✅
```

**Expected Results:**
- ✅ All messages processed
- ⚠️ Vertex AI errors (expected - API not enabled)
- ✅ Mock mode activated for all AI calls
- ✅ Exit code 0
- ✅ No crashes or unhandled exceptions

**Log Patterns:**
```
Gemini API error (attempt 1/3): 404 Publisher Model `gemini-1.5-flash` was not found
Gemini API error (attempt 2/3): 404 Publisher Model `gemini-1.5-flash` was not found
Gemini API error (attempt 3/3): 404 Publisher Model `gemini-1.5-flash` was not found
Vertex AI not available: Running in mock mode
```

---

### With Real API (Future State)

**Flow:**
```
Message → Worker → NLU (gemini-1.5-flash) → Success
                → Script Gen (gemini-1.5-flash) → Success
                → Interest Match (gemini-1.5-flash) → Success
                → Database save
                → Message ACK
                → Success ✅
```

**Expected Results:**
- ✅ All messages processed
- ✅ Real AI responses
- ✅ Higher latency (AI calls take 1-2s each)
- ✅ Exit code 0
- ✅ No mock mode fallbacks

**Performance Impact:**
- Latency: +4-6s per message (3 AI calls)
- Throughput: ~0.5-1 msg/s (AI latency bound)
- Cost: $0.000625 per message (gemini-1.5-flash pricing)

---

## Interpreting Results

### Success Indicators ✅

```
Messages processed: 10 / 10
Successful: 10
Failed: 0
Errors logged: 30  (3 retries × 10 messages, expected)
Warnings logged: 10  (mock mode warnings, expected)
Throughput: 2.5 messages/second

✓ Vertex AI API not available: 30 calls (expected)
⚠ Mock mode active: 30 instances (expected)
✓ No database errors
✓ No timeouts

✓ LOAD TEST PASSED
```

**Interpretation:** System working perfectly. Mock mode activated as expected.

---

### Partial Success Indicators ⚠️

```
Messages processed: 8 / 10
Successful: 8
Failed: 2
Errors logged: 45
Throughput: 1.5 messages/second

⚠ LOAD TEST PARTIAL SUCCESS
```

**Interpretation:** Some messages failed. Investigate error logs for patterns.

**Action Items:**
1. Check DLQ for failed messages
2. Review error logs for specific failures
3. Identify if failures are transient or systematic
4. Re-run test to check reproducibility

---

### Failure Indicators ❌

```
Messages processed: 0 / 10
Successful: 0
Failed: 10
Errors logged: 150
Database errors: 10

✗ LOAD TEST FAILED
```

**Interpretation:** Systematic failure. Worker not operational.

**Action Items:**
1. Check worker deployment status
2. Verify database connectivity
3. Check Pub/Sub subscription configuration
4. Review Cloud Run logs for startup errors
5. Validate environment variables and secrets

---

## Troubleshooting Common Issues

### Issue 1: Low Throughput (<1 msg/s)

**Symptoms:**
- Worker taking >30s per message
- Throughput far below baseline

**Possible Causes:**
1. Database connection pooling too small
2. Worker task count set to 1 (no parallelism)
3. AI API latency very high
4. Network latency to dependencies

**Diagnosis:**
```bash
# Check worker configuration
gcloud run jobs describe dev-vividly-content-worker \
  --region=us-central1 --project=vividly-dev-rich

# Look for:
# - task_count: Should be 1-10
# - parallelism: Should match expected concurrent messages
```

**Fix:**
```bash
# Increase task count for parallel processing
gcloud run jobs update dev-vividly-content-worker \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --tasks=10 \
  --parallelism=10
```

---

### Issue 2: Database Connection Errors

**Symptoms:**
```
database.*error
could not connect to server
too many connections
```

**Possible Causes:**
1. Connection pool exhausted
2. Database max_connections limit reached
3. Connection leaks (not closing connections)

**Diagnosis:**
```bash
# Check active connections
gcloud sql operations list --instance=vividly-dev-db \
  --project=vividly-dev-rich

# Check Cloud SQL proxy status
gcloud sql instances describe vividly-dev-db \
  --project=vividly-dev-rich | grep -i connection
```

**Fix:**
```python
# In app/core/database.py
# Increase pool size
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from default
    max_overflow=10,
    pool_pre_ping=True,  # Validate connections
    pool_recycle=3600,  # Recycle every hour
)
```

---

### Issue 3: Messages Not Being Pulled

**Symptoms:**
- Worker executes but processes 0 messages
- Messages remain in Pub/Sub queue

**Possible Causes:**
1. Subscription configuration incorrect
2. Message acknowledgment timeout too short
3. Worker polling interval too long

**Diagnosis:**
```bash
# Check subscription configuration
gcloud pubsub subscriptions describe content-requests-dev-sub \
  --project=vividly-dev-rich

# Check message backlog
gcloud pubsub subscriptions pull content-requests-dev-sub \
  --project=vividly-dev-rich \
  --limit=5 \
  --auto-ack
```

**Fix:**
```python
# In worker.py - Increase timeout
subscription_path = subscriber.subscription_path(
    project_id, subscription_id
)

streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=process_message,
    flow_control=pubsub_v1.types.FlowControl(
        max_messages=10,
        max_lease_duration=600,  # Increase from 300s
    ),
)
```

---

### Issue 4: Messages Going to DLQ

**Symptoms:**
- High failure rate
- Messages appearing in DLQ topic

**Possible Causes:**
1. Persistent processing errors
2. Validation failures
3. Retry limit exceeded

**Diagnosis:**
```bash
# Inspect DLQ messages
gcloud pubsub subscriptions pull content-requests-dev-dlq \
  --project=vividly-dev-rich \
  --limit=10 \
  --format=json

# Look for patterns in failed messages
```

**Fix:**
1. Review message format validation
2. Check for missing required fields
3. Verify database schema matches expectations
4. Update retry logic to handle transient failures

---

## Scaling Considerations

### Current Architecture Limits

| Resource | Limit | Implication |
|----------|-------|-------------|
| **Cloud Run Tasks** | Max 1000 | Can process 1000 messages concurrently |
| **Pub/Sub Throughput** | 10K msg/s | Not a bottleneck |
| **Database Connections** | 100 (Cloud SQL) | May bottleneck at high concurrency |
| **Gemini API Rate Limit** | 60 RPM (free tier) | ~1 req/s max |
| **Worker Memory** | 2GB default | May need increase for large payloads |

### Recommended Scaling Path

**Phase 1: 0-100 messages/minute**
- Current configuration sufficient
- Single worker task
- Mock mode for testing

**Phase 2: 100-1000 messages/minute**
- Increase worker tasks to 10-20
- Enable real Gemini API
- Monitor database connection pool
- Consider database read replicas

**Phase 3: 1000+ messages/minute**
- Implement worker autoscaling
- Use Pub/Sub push subscriptions
- Shard database by student_id
- Implement request batching for Gemini
- Add caching layer (Redis)

---

## Continuous Testing Strategy

### Pre-Deployment Tests

**Before every deployment:**
1. Run 10-message load test
2. Verify 100% success rate
3. Check for new error patterns
4. Validate performance within SLA

**Command:**
```bash
./scripts/test_concurrent_requests.sh || exit 1
```

---

### Post-Deployment Validation

**After every deployment:**
1. Run smoke test (5 messages)
2. Monitor for 5 minutes
3. Check error rates
4. Verify throughput maintains baseline

**Command:**
```bash
# Quick smoke test
NUM_CONCURRENT_REQUESTS=5 ./scripts/test_concurrent_requests.sh
```

---

### Weekly Load Tests

**Every Monday (automated):**
1. Run 100-message load test
2. Compare to baseline metrics
3. Generate trend reports
4. Alert on degradation >10%

**Scheduled via Cloud Scheduler:**
```bash
gcloud scheduler jobs create http weekly-load-test \
  --schedule="0 9 * * 1" \
  --uri="https://TRIGGER_URL" \
  --http-method=POST
```

---

## Test Data Design

### Message Variety

**Why Variety Matters:**
- Different topics stress NLU differently
- Different interests affect personalization
- Different grade levels test content appropriation
- Varied message sizes test parsing/serialization

**Current Test Data:**
```bash
QUERIES=(
  "Explain photosynthesis using basketball"     # Biology + Sports
  "What are Newton's laws using soccer"         # Physics + Sports
  "Explain cellular respiration with baseball"  # Biology + Sports
  "Describe water cycle using football"         # Earth Science + Sports
  ...
)

INTERESTS=("basketball" "soccer" "baseball" ...)
GRADE_LEVELS=(9 10 11 12)
```

**Coverage:**
- ✅ Multiple science domains
- ✅ Multiple sports interests
- ✅ All grade levels
- ✅ Query length variety

---

## Future Enhancements

### 1. Performance Profiling

**Add detailed timing metrics:**
```python
# In worker
import time

start = time.time()
topic = await nlu_service.extract_topic(query, grade)
nlu_duration = time.time() - start
logger.info(f"NLU duration: {nlu_duration}s")

# Aggregate in test script
# Report p50, p95, p99 latencies
```

---

### 2. Cost Tracking

**Measure cost per message:**
```bash
# In test script
GEMINI_COST_PER_1K_CHARS=0.000125
AVG_CHARS_PER_REQUEST=500
TOTAL_COST=$(echo "$MESSAGES_PROCESSED * $AVG_CHARS_PER_REQUEST * $GEMINI_COST_PER_1K_CHARS / 1000" | bc -l)
echo "Total cost: \$${TOTAL_COST}"
```

---

### 3. Chaos Engineering

**Test failure scenarios:**
```bash
# Kill database mid-test
# Inject Pub/Sub delays
# Simulate API outages
# Test with malformed messages
```

---

### 4. Load Test Automation

**CI/CD Integration:**
```yaml
# .github/workflows/load-test.yml
name: Load Test
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Load Test
        run: ./scripts/test_concurrent_requests.sh
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: /tmp/vividly_load_test_*
```

---

## Conclusion

Load testing is not a one-time activity. It's a continuous practice that:

1. **Validates** system works under real-world conditions
2. **Identifies** bottlenecks before they impact users
3. **Quantifies** system capacity and limits
4. **Informs** scaling decisions with data
5. **Prevents** production incidents through proactive testing

**"In God we trust. All others must bring data."** — W. Edwards Deming

---

## Quick Reference

### Run Basic Load Test
```bash
./scripts/test_concurrent_requests.sh
```

### Check Results
```bash
# Latest test results
ls -lt /tmp/vividly_load_test_* | head -1

# View summary
cat /tmp/vividly_load_test_*/summary.txt
```

### Cleanup
```bash
# Remove old test results (>7 days)
find /tmp -name "vividly_load_test_*" -mtime +7 -exec rm -rf {} \;
```

---

**Last Updated:** November 4, 2025
**Test Script:** `scripts/test_concurrent_requests.sh`
**Maintained By:** Engineering Team
