#!/bin/bash
# Concurrent Request Load Test for Vividly Content Worker
# Tests system behavior under concurrent load

set -e

# Configuration
PROJECT_ID="vividly-dev-rich"
REGION="us-central1"
TOPIC="content-requests-dev"
NUM_CONCURRENT_REQUESTS=10
WORKER_JOB="dev-vividly-content-worker"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Vividly Concurrent Request Load Test"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Topic: $TOPIC"
echo "  Concurrent Requests: $NUM_CONCURRENT_REQUESTS"
echo "  Worker Job: $WORKER_JOB"
echo ""

# Test data variations
QUERIES=(
  "Explain photosynthesis using basketball"
  "What are Newton's laws of motion using soccer"
  "Explain cellular respiration with baseball"
  "Describe the water cycle using football"
  "What is mitosis explained through hockey"
  "Explain gravity using tennis"
  "What is DNA replication with volleyball"
  "Describe the carbon cycle using cricket"
  "What is photosynthesis using rugby"
  "Explain protein synthesis with lacrosse"
)

INTERESTS=(
  "basketball"
  "soccer"
  "baseball"
  "football"
  "hockey"
  "tennis"
  "volleyball"
  "cricket"
  "rugby"
  "lacrosse"
)

GRADE_LEVELS=(9 10 11 12)

# Generate timestamp for this test run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/tmp/vividly_load_test_${TIMESTAMP}"
mkdir -p "$LOG_DIR"

echo -e "${GREEN}[1/4] Publishing $NUM_CONCURRENT_REQUESTS concurrent messages...${NC}"
echo ""

# Array to store message IDs
declare -a MESSAGE_IDS

# Publish messages concurrently
for i in $(seq 1 $NUM_CONCURRENT_REQUESTS); do
  # Select random test data
  QUERY_IDX=$((i % ${#QUERIES[@]}))
  INTEREST_IDX=$((i % ${#INTERESTS[@]}))
  GRADE_IDX=$((i % ${#GRADE_LEVELS[@]}))

  QUERY="${QUERIES[$QUERY_IDX]}"
  INTEREST="${INTERESTS[$INTEREST_IDX]}"
  GRADE="${GRADE_LEVELS[$GRADE_IDX]}"

  REQUEST_ID="load_test_${TIMESTAMP}_${i}"

  # Build message payload
  MESSAGE=$(cat <<EOF
{
  "request_id": "$REQUEST_ID",
  "student_id": "student_load_test_${i}",
  "student_query": "$QUERY",
  "interest": "$INTEREST",
  "grade_level": $GRADE
}
EOF
)

  # Publish message in background
  (
    echo "  [Msg $i] Publishing: $REQUEST_ID"
    RESULT=$(/opt/homebrew/share/google-cloud-sdk/bin/gcloud pubsub topics publish $TOPIC \
      --project=$PROJECT_ID \
      --message="$MESSAGE" 2>&1)

    # Extract message ID
    MSG_ID=$(echo "$RESULT" | grep -oE "messageIds:\s*-\s*'[0-9]+'" | grep -oE "[0-9]+")
    echo "$MSG_ID" >> "$LOG_DIR/message_ids.txt"
    echo "  [Msg $i] Published with ID: $MSG_ID"
  ) &
done

# Wait for all publishes to complete
wait

echo ""
echo -e "${GREEN}✓ All messages published${NC}"
echo ""

# Count published messages
NUM_PUBLISHED=$(wc -l < "$LOG_DIR/message_ids.txt" | tr -d ' ')
echo "Published: $NUM_PUBLISHED messages"
echo ""

echo -e "${YELLOW}[2/4] Waiting 5 seconds for messages to propagate...${NC}"
sleep 5
echo ""

echo -e "${GREEN}[3/4] Executing worker to process messages...${NC}"
echo ""

# Execute worker and capture execution details
EXECUTION_START=$(date +%s)

/opt/homebrew/share/google-cloud-sdk/bin/gcloud run jobs execute $WORKER_JOB \
  --region=$REGION \
  --project=$PROJECT_ID \
  --wait 2>&1 | tee "$LOG_DIR/worker_execution.log"

EXECUTION_END=$(date +%s)
EXECUTION_DURATION=$((EXECUTION_END - EXECUTION_START))

echo ""
echo -e "${GREEN}✓ Worker execution completed${NC}"
echo "Execution duration: ${EXECUTION_DURATION}s"
echo ""

echo -e "${GREEN}[4/4] Analyzing results...${NC}"
echo ""

# Extract execution ID from logs
EXECUTION_ID=$(grep -oE "dev-vividly-content-worker-[a-z0-9]+" "$LOG_DIR/worker_execution.log" | head -1)

if [ -z "$EXECUTION_ID" ]; then
  echo -e "${RED}Failed to extract execution ID${NC}"
  exit 1
fi

echo "Execution ID: $EXECUTION_ID"
echo ""

# Fetch worker logs
echo "Fetching worker logs..."
/opt/homebrew/share/google-cloud-sdk/bin/gcloud run jobs logs read $WORKER_JOB \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=500 > "$LOG_DIR/worker_logs.txt"

# Analyze logs
echo ""
echo "=========================================="
echo "Load Test Results"
echo "=========================================="
echo ""

# Count processed messages
MESSAGES_PROCESSED=$(grep -c "Processing message: request_id=load_test_${TIMESTAMP}" "$LOG_DIR/worker_logs.txt" || echo "0")
echo "Messages processed: $MESSAGES_PROCESSED / $NUM_PUBLISHED"

# Count successful completions
MESSAGES_SUCCESS=$(grep -c "Message processing completed successfully" "$LOG_DIR/worker_logs.txt" || echo "0")
echo "Successful: $MESSAGES_SUCCESS"

# Count failures
MESSAGES_FAILED=$(grep -c "Message processing failed" "$LOG_DIR/worker_logs.txt" || echo "0")
echo "Failed: $MESSAGES_FAILED"

# Check for errors
ERRORS=$(grep -c "ERROR" "$LOG_DIR/worker_logs.txt" || echo "0")
echo "Errors logged: $ERRORS"

# Check for warnings
WARNINGS=$(grep -c "WARNING" "$LOG_DIR/worker_logs.txt" || echo "0")
echo "Warnings logged: $WARNINGS"

# Calculate throughput
if [ $MESSAGES_PROCESSED -gt 0 ] && [ $EXECUTION_DURATION -gt 0 ]; then
  THROUGHPUT=$(echo "scale=2; $MESSAGES_PROCESSED / $EXECUTION_DURATION" | bc)
  echo "Throughput: ${THROUGHPUT} messages/second"
fi

echo ""
echo "=========================================="
echo "Performance Metrics"
echo "=========================================="
echo ""

# Check for Vertex AI errors (expected with mock mode)
VERTEX_ERRORS=$(grep -c "Vertex AI not available" "$LOG_DIR/worker_logs.txt" || echo "0")
if [ $VERTEX_ERRORS -gt 0 ]; then
  echo -e "${YELLOW}⚠ Vertex AI API not available: $VERTEX_ERRORS calls${NC}"
  echo "  Worker using mock mode (expected)"
else
  echo -e "${GREEN}✓ Vertex AI API available${NC}"
fi

# Check for mock mode usage
MOCK_MODE=$(grep -c "mock mode" "$LOG_DIR/worker_logs.txt" || echo "0")
if [ $MOCK_MODE -gt 0 ]; then
  echo -e "${YELLOW}⚠ Mock mode active: $MOCK_MODE instances${NC}"
else
  echo -e "${GREEN}✓ Real AI mode active${NC}"
fi

# Check for database errors
DB_ERRORS=$(grep -c "database.*error" "$LOG_DIR/worker_logs.txt" | tr -d ' ' || echo "0")
if [ "$DB_ERRORS" != "0" ]; then
  echo -e "${RED}✗ Database errors: $DB_ERRORS${NC}"
else
  echo -e "${GREEN}✓ No database errors${NC}"
fi

# Check for timeout issues
TIMEOUTS=$(grep -c "timeout\|timed out" "$LOG_DIR/worker_logs.txt" | tr -d ' ' || echo "0")
if [ "$TIMEOUTS" != "0" ]; then
  echo -e "${RED}✗ Timeouts detected: $TIMEOUTS${NC}"
else
  echo -e "${GREEN}✓ No timeouts${NC}"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""

# Overall status
if [ $MESSAGES_PROCESSED -eq $NUM_PUBLISHED ] && [ $MESSAGES_SUCCESS -eq $NUM_PUBLISHED ]; then
  echo -e "${GREEN}✓ LOAD TEST PASSED${NC}"
  echo "  All messages processed successfully"
  EXIT_CODE=0
elif [ $MESSAGES_PROCESSED -gt 0 ]; then
  echo -e "${YELLOW}⚠ LOAD TEST PARTIAL SUCCESS${NC}"
  echo "  Some messages processed successfully"
  EXIT_CODE=1
else
  echo -e "${RED}✗ LOAD TEST FAILED${NC}"
  echo "  No messages processed successfully"
  EXIT_CODE=2
fi

echo ""
echo "Logs saved to: $LOG_DIR"
echo "  - message_ids.txt: Published message IDs"
echo "  - worker_execution.log: Worker execution output"
echo "  - worker_logs.txt: Detailed worker logs"
echo ""

# Save summary
cat > "$LOG_DIR/summary.txt" <<EOF
Vividly Concurrent Request Load Test Summary
============================================

Test Configuration:
  Timestamp: $TIMESTAMP
  Concurrent Requests: $NUM_CONCURRENT_REQUESTS
  Project: $PROJECT_ID
  Topic: $TOPIC
  Worker: $WORKER_JOB

Results:
  Published: $NUM_PUBLISHED
  Processed: $MESSAGES_PROCESSED
  Successful: $MESSAGES_SUCCESS
  Failed: $MESSAGES_FAILED
  Errors: $ERRORS
  Warnings: $WARNINGS

Performance:
  Duration: ${EXECUTION_DURATION}s
  Throughput: ${THROUGHPUT:-N/A} msg/s

Status: $([ $EXIT_CODE -eq 0 ] && echo "PASSED" || echo "FAILED")
EOF

echo "Summary saved to: $LOG_DIR/summary.txt"
echo ""

exit $EXIT_CODE
