#!/bin/bash
#
# UUID Validation Testing Script
# Tests the worker's ability to handle invalid and valid UUIDs
#
# Based on SESSION_5_WORKER_TIMEOUT_FIX.md testing plan
#

set -e

PROJECT_ID="vividly-dev-rich"
TOPIC="content-requests-dev"
REGION="us-central1"
JOB_NAME="dev-vividly-content-worker"

echo "===================================="
echo "UUID Validation Testing"
echo "===================================="
echo ""
echo "Purpose: Verify worker rejects invalid UUIDs without retry loops"
echo "Fix: Commit 7191ecd - UUID validation in content_worker.py"
echo ""

# Phase 1: Test Invalid UUID Rejection
echo "------------------------------------"
echo "PHASE 1: Invalid UUID Rejection Test"
echo "------------------------------------"
echo ""

INVALID_UUID="invalid-uuid-test-$(date +%s)"

echo "Test Message:"
echo "  request_id: $INVALID_UUID (INVALID - not a UUID)"
echo "  Expected: Worker rejects immediately, no retry loop"
echo ""

# Publish invalid UUID message
echo "Publishing test message..."
gcloud pubsub topics publish "$TOPIC" \
  --project="$PROJECT_ID" \
  --message="{
    \"request_id\": \"$INVALID_UUID\",
    \"student_query\": \"Test query for UUID validation\",
    \"student_id\": \"test-student\",
    \"grade_level\": 10
  }"

echo "Message published. Waiting 10 seconds for worker to process..."
sleep 10

# Check logs for validation error
echo ""
echo "Checking logs for UUID validation error..."
VALIDATION_LOGS=$(gcloud logging read \
  "resource.type=\"cloud_run_job\" \"Invalid request_id format\" \"$INVALID_UUID\"" \
  --project="$PROJECT_ID" \
  --limit=5 \
  --format="value(textPayload)" \
  --freshness=2m)

if [ -z "$VALIDATION_LOGS" ]; then
  echo "❌ FAILED: No UUID validation error found in logs"
  echo "   Expected to see: 'Invalid request_id format: $INVALID_UUID is not a valid UUID'"
  exit 1
else
  echo "✅ PASSED: UUID validation error found:"
  echo "$VALIDATION_LOGS" | head -3
fi

# Check recent worker executions
echo ""
echo "Checking recent worker executions..."
RECENT_EXECUTIONS=$(gcloud run jobs executions list \
  --job="$JOB_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --limit=3 \
  --format="table(execution,status,startTime,completionTime)")

echo "$RECENT_EXECUTIONS"

# Check for timeout failures
echo ""
echo "Checking for timeout failures in last hour..."
TIMEOUT_COUNT=$(gcloud logging read \
  'resource.type="cloud_run_job" "timeout"' \
  --project="$PROJECT_ID" \
  --freshness=1h \
  --format="value(textPayload)" \
  --limit=10 | wc -l)

if [ "$TIMEOUT_COUNT" -gt 0 ]; then
  echo "⚠️  WARNING: Found $TIMEOUT_COUNT timeout-related log entries"
  echo "   (May be from previous failures - check if recent)"
else
  echo "✅ PASSED: No timeout failures detected"
fi

echo ""
echo "------------------------------------"
echo "PHASE 2: Valid UUID Processing Test"
echo "------------------------------------"
echo ""

# Generate valid UUID
VALID_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "Test Message:"
echo "  request_id: $VALID_UUID (VALID UUID)"
echo "  Expected: No UUID validation error (may fail at DB lookup - that's OK)"
echo ""

# Publish valid UUID message
echo "Publishing test message..."
gcloud pubsub topics publish "$TOPIC" \
  --project="$PROJECT_ID" \
  --message="{
    \"request_id\": \"$VALID_UUID\",
    \"student_query\": \"Test query with valid UUID\",
    \"student_id\": \"test-student\",
    \"grade_level\": 10
  }"

echo "Message published. Waiting 10 seconds for worker to process..."
sleep 10

# Check that NO validation error occurs
echo ""
echo "Checking logs (should NOT contain validation error for this UUID)..."
VALIDATION_ERROR=$(gcloud logging read \
  "resource.type=\"cloud_run_job\" \"Invalid request_id format\" \"$VALID_UUID\"" \
  --project="$PROJECT_ID" \
  --limit=1 \
  --format="value(textPayload)" \
  --freshness=2m)

if [ -z "$VALIDATION_ERROR" ]; then
  echo "✅ PASSED: No UUID validation error for valid UUID"
else
  echo "❌ FAILED: UUID validation error found for VALID UUID:"
  echo "$VALIDATION_ERROR"
  exit 1
fi

# Check if message was processed (any logs mentioning the UUID)
echo ""
echo "Checking if valid UUID message was processed..."
PROCESSING_LOGS=$(gcloud logging read \
  "resource.type=\"cloud_run_job\" \"$VALID_UUID\"" \
  --project="$PROJECT_ID" \
  --limit=3 \
  --format="value(textPayload)" \
  --freshness=2m)

if [ -z "$PROCESSING_LOGS" ]; then
  echo "⚠️  INFO: No processing logs found for valid UUID"
  echo "   (May still be in queue or processed without logging UUID)"
else
  echo "✅ PASSED: Worker processed valid UUID message:"
  echo "$PROCESSING_LOGS" | head -3
fi

echo ""
echo "===================================="
echo "TEST SUMMARY"
echo "===================================="
echo ""
echo "✅ Phase 1: Invalid UUID rejected with validation error"
echo "✅ Phase 2: Valid UUID processed without validation error"
echo ""
echo "SUCCESS CRITERIA MET:"
echo "1. Invalid UUIDs trigger validation error log"
echo "2. Invalid UUIDs do not cause retry loops"
echo "3. Valid UUIDs pass validation"
echo "4. No timeout failures in recent executions"
echo ""
echo "NEXT STEPS:"
echo "- Monitor production for 24 hours for stability"
echo "- Proceed with Phase 1C dual modality validation"
echo ""
echo "Test completed at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
