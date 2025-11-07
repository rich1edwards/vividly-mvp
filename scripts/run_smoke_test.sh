#!/bin/bash
set -e

# ============================================================================
# Content Worker End-to-End Smoke Test
# ============================================================================
# This script performs a complete smoke test of the async content worker:
# 1. Creates a ContentRequest database record
# 2. Publishes message to Pub/Sub
# 3. Executes Cloud Run Job worker
# 4. Monitors progress in database
# 5. Verifies successful completion
#
# Usage: ./scripts/run_smoke_test.sh
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

PROJECT_ID="vividly-dev-rich"
DB_IP="34.56.211.136"
DB_USER="vividly"
DB_NAME="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

# Get database password from secret
echo -e "${BLUE}📋 Retrieving database credentials...${NC}"
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#^postgresql://[^:]*:\([^@]*\)@.*#\1#p')
export PGPASSWORD="$DB_PASSWORD"

# Generate test request ID
TEST_REQUEST_ID="smoke-test-$(date +%s)"
STUDENT_ID="test-student-$(date +%s)"
CORRELATION_ID="correlation-${TEST_REQUEST_ID}"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Content Worker End-to-End Smoke Test                 ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Test Configuration:${NC}"
echo -e "  Request ID:      ${YELLOW}${TEST_REQUEST_ID}${NC}"
echo -e "  Student ID:      ${YELLOW}${STUDENT_ID}${NC}"
echo -e "  Correlation ID:  ${YELLOW}${CORRELATION_ID}${NC}"
echo -e "  Database:        ${YELLOW}${DB_IP}${NC}"
echo -e "  Project:         ${YELLOW}${PROJECT_ID}${NC}"
echo ""

# ============================================================================
# STEP 1: Insert ContentRequest database record
# ============================================================================
echo -e "${BLUE}📝 Step 1: Creating ContentRequest database record...${NC}"

"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF
INSERT INTO content_requests (
    request_id,
    student_id,
    correlation_id,
    student_query,
    grade_level,
    duration_minutes,
    status,
    progress_percentage,
    current_stage,
    created_at,
    updated_at
) VALUES (
    '${TEST_REQUEST_ID}',
    '${STUDENT_ID}',
    '${CORRELATION_ID}',
    'Explain the process of photosynthesis for 8th grade students',
    '8',
    3,
    'pending',
    0,
    'Request queued for processing',
    NOW(),
    NOW()
);
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database record created successfully${NC}"
else
    echo -e "${RED}✗ Failed to create database record${NC}"
    exit 1
fi

# Verify record was created
echo -e "${BLUE}🔍 Verifying database record...${NC}"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
SELECT
    request_id,
    status,
    progress_percentage,
    current_stage,
    created_at
FROM content_requests
WHERE request_id = '${TEST_REQUEST_ID}';
"

echo ""

# ============================================================================
# STEP 2: Publish message to Pub/Sub
# ============================================================================
echo -e "${BLUE}📤 Step 2: Publishing message to Pub/Sub...${NC}"

MESSAGE_JSON=$(cat <<EOF
{
  "request_id": "${TEST_REQUEST_ID}",
  "student_id": "${STUDENT_ID}",
  "student_query": "Explain the process of photosynthesis for 8th grade students",
  "grade_level": "8",
  "duration_minutes": 3
}
EOF
)

PUBSUB_RESULT=$(gcloud pubsub topics publish content-generation-requests \
  --project="$PROJECT_ID" \
  --message="$MESSAGE_JSON" \
  2>&1)

if [ $? -eq 0 ]; then
    MESSAGE_ID=$(echo "$PUBSUB_RESULT" | grep -o 'messageIds:' -A 1 | tail -n 1 | tr -d ' -')
    echo -e "${GREEN}✓ Message published successfully${NC}"
    echo -e "  Message ID: ${YELLOW}${MESSAGE_ID}${NC}"
else
    echo -e "${RED}✗ Failed to publish message to Pub/Sub${NC}"
    echo "$PUBSUB_RESULT"
    exit 1
fi

echo ""

# ============================================================================
# STEP 3: Execute Cloud Run Job
# ============================================================================
echo -e "${BLUE}🚀 Step 3: Executing Cloud Run Job worker...${NC}"
echo -e "${YELLOW}⏳ This will take 10-15 minutes for complete content generation${NC}"
echo ""

# Execute in background and capture execution name
gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 \
  --project="$PROJECT_ID" \
  --async \
  2>&1 | tee /tmp/job_execute.log

EXECUTION_NAME=$(grep -o 'dev-vividly-content-worker-[a-z0-9]*' /tmp/job_execute.log | head -1)

if [ -z "$EXECUTION_NAME" ]; then
    echo -e "${RED}✗ Failed to get execution name${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Cloud Run Job execution started${NC}"
echo -e "  Execution: ${YELLOW}${EXECUTION_NAME}${NC}"
echo ""

# ============================================================================
# STEP 4: Monitor progress
# ============================================================================
echo -e "${BLUE}📊 Step 4: Monitoring worker progress...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring (worker will continue running)${NC}"
echo ""

# Monitor database for 15 minutes (900 seconds)
MONITOR_START=$(date +%s)
MONITOR_TIMEOUT=900
CHECK_INTERVAL=10
LAST_STATUS=""
LAST_PERCENTAGE=0

while true; do
    ELAPSED=$(($(date +%s) - MONITOR_START))

    if [ $ELAPSED -gt $MONITOR_TIMEOUT ]; then
        echo ""
        echo -e "${YELLOW}⏱  Monitoring timeout reached (15 minutes)${NC}"
        break
    fi

    # Query database for current status
    DB_STATUS=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -A -F'|' -c "
        SELECT
            status,
            progress_percentage,
            current_stage,
            error_message,
            video_url
        FROM content_requests
        WHERE request_id = '${TEST_REQUEST_ID}';
    " 2>/dev/null)

    if [ -n "$DB_STATUS" ]; then
        STATUS=$(echo "$DB_STATUS" | cut -d'|' -f1)
        PERCENTAGE=$(echo "$DB_STATUS" | cut -d'|' -f2)
        STAGE=$(echo "$DB_STATUS" | cut -d'|' -f3)
        ERROR=$(echo "$DB_STATUS" | cut -d'|' -f4)
        VIDEO_URL=$(echo "$DB_STATUS" | cut -d'|' -f5)

        # Only print if status changed
        if [ "$STATUS" != "$LAST_STATUS" ] || [ "$PERCENTAGE" != "$LAST_PERCENTAGE" ]; then
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

            # Color code by status
            if [ "$STATUS" = "completed" ]; then
                STATUS_COLOR=$GREEN
            elif [ "$STATUS" = "failed" ]; then
                STATUS_COLOR=$RED
            elif [ "$STATUS" = "generating" ] || [ "$STATUS" = "processing" ]; then
                STATUS_COLOR=$BLUE
            else
                STATUS_COLOR=$YELLOW
            fi

            echo -e "${TIMESTAMP} | Status: ${STATUS_COLOR}${STATUS}${NC} | Progress: ${PERCENTAGE}% | ${STAGE}"

            LAST_STATUS="$STATUS"
            LAST_PERCENTAGE="$PERCENTAGE"
        fi

        # Check for completion
        if [ "$STATUS" = "completed" ]; then
            echo ""
            echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║                  🎉 TEST COMPLETED SUCCESSFULLY! 🎉           ║${NC}"
            echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo -e "${GREEN}✓ Content generation completed${NC}"
            echo -e "  Video URL: ${YELLOW}${VIDEO_URL}${NC}"
            echo ""

            # Show final database record
            echo -e "${BLUE}📊 Final Database Record:${NC}"
            "$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
                SELECT
                    request_id,
                    status,
                    progress_percentage,
                    current_stage,
                    video_url,
                    script_url,
                    audio_url,
                    created_at,
                    updated_at,
                    processing_duration_ms
                FROM content_requests
                WHERE request_id = '${TEST_REQUEST_ID}';
            "

            exit 0
        fi

        # Check for failure
        if [ "$STATUS" = "failed" ]; then
            echo ""
            echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${RED}║                     ✗ TEST FAILED ✗                          ║${NC}"
            echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo -e "${RED}✗ Content generation failed${NC}"
            echo -e "  Error: ${YELLOW}${ERROR}${NC}"
            echo ""

            # Show logs
            echo -e "${BLUE}📋 Checking worker logs...${NC}"
            gcloud logging read \
                "resource.type=cloud_run_job AND labels.\"run.googleapis.com/execution_name\"=\"${EXECUTION_NAME}\"" \
                --project="$PROJECT_ID" \
                --limit=50 \
                --format="table(timestamp,severity,textPayload)" \
                2>&1 | grep -i error | head -20

            exit 1
        fi
    fi

    sleep $CHECK_INTERVAL
done

# If we timeout, show final status
echo ""
echo -e "${YELLOW}⚠  Monitoring stopped, but worker may still be processing${NC}"
echo ""
echo -e "${BLUE}Current Status:${NC}"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT
        request_id,
        status,
        progress_percentage,
        current_stage,
        created_at,
        updated_at
    FROM content_requests
    WHERE request_id = '${TEST_REQUEST_ID}';
"

echo ""
echo -e "${BLUE}To check status later, run:${NC}"
echo -e "  ${YELLOW}psql -h $DB_IP -U $DB_USER -d $DB_NAME -c \"SELECT * FROM content_requests WHERE request_id = '${TEST_REQUEST_ID}';\"${NC}"
echo ""
echo -e "${BLUE}To check worker logs:${NC}"
echo -e "  ${YELLOW}gcloud logging read 'resource.type=cloud_run_job AND labels.\"run.googleapis.com/execution_name\"=\"${EXECUTION_NAME}\"' --project=$PROJECT_ID --limit=100${NC}"
echo ""
