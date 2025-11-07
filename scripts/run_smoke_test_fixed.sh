#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
export CLOUDSDK_CONFIG="$HOME/.gcloud"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.gcloud/application_default_credentials.json"

PROJECT_ID="vividly-dev-rich"
DB_IP="34.56.211.136"
DB_USER="vividly"
DB_NAME="vividly"
PSQL="/opt/homebrew/Cellar/postgresql@15/15.14/bin/psql"

# Get DB password
echo -e "${BLUE}📋 Retrieving database credentials...${NC}"
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#^postgresql://[^:]*:\([^@]*\)@.*#\1#p')
export PGPASSWORD="$DB_PASSWORD"

# Generate IDs (UUID v4 format)
REQUEST_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
STUDENT_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
CORRELATION_ID="smoke-test-$(date +%s)"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Content Worker End-to-End Smoke Test                 ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Test Configuration:${NC}"
echo -e "  Request ID (UUID):   ${YELLOW}${REQUEST_ID}${NC}"
echo -e "  Student ID (UUID):   ${YELLOW}${STUDENT_ID}${NC}"
echo -e "  Correlation ID:      ${YELLOW}${CORRELATION_ID}${NC}"
echo ""

# Step 1: Create test user
echo -e "${BLUE}📝 Step 1: Creating test user in database...${NC}"

"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF
-- Create test user if not exists
INSERT INTO users (
    id,
    email,
    name,
    created_at,
    updated_at
) VALUES (
    '${STUDENT_ID}',
    'smoke-test@vividly.test',
    'Smoke Test User',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test user created/verified${NC}"
else
    echo -e "${RED}✗ Failed to create test user${NC}"
    exit 1
fi

# Step 2: Create ContentRequest record
echo -e "${BLUE}📝 Step 2: Creating ContentRequest database record...${NC}"

"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<EOF
INSERT INTO content_requests (
    id,
    correlation_id,
    student_id,
    topic,
    grade_level,
    duration_minutes,
    status,
    progress_percentage,
    current_stage,
    created_at
) VALUES (
    '${REQUEST_ID}',
    '${CORRELATION_ID}',
    '${STUDENT_ID}',
    'Explain the process of photosynthesis for 8th grade students',
    '8',
    3,
    'pending',
    0,
    'Request queued for processing',
    NOW()
);
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ContentRequest record created${NC}"
else
    echo -e "${RED}✗ Failed to create ContentRequest record${NC}"
    exit 1
fi

# Verify
echo -e "${BLUE}🔍 Verifying database record...${NC}"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
SELECT
    id,
    correlation_id,
    status,
    progress_percentage,
    current_stage,
    topic
FROM content_requests
WHERE id = '${REQUEST_ID}';
"

echo ""

# Step 3: Publish Pub/Sub message
echo -e "${BLUE}📤 Step 3: Publishing message to Pub/Sub...${NC}"

MESSAGE_JSON=$(cat <<EOF
{
  "request_id": "${REQUEST_ID}",
  "correlation_id": "${CORRELATION_ID}",
  "student_id": "${STUDENT_ID}",
  "student_query": "Explain the process of photosynthesis for 8th grade students",
  "grade_level": "8",
  "duration_minutes": 3
}
EOF
)

echo -e "${BLUE}Message:${NC}"
echo "$MESSAGE_JSON" | jq '.'

PUBSUB_RESULT=$(gcloud pubsub topics publish content-generation-requests \
  --project="$PROJECT_ID" \
  --message="$MESSAGE_JSON" \
  2>&1)

if [ $? -eq 0 ]; then
    MESSAGE_ID=$(echo "$PUBSUB_RESULT" | grep -o 'messageIds:' -A 1 | tail -n 1 | tr -d ' -')
    echo -e "${GREEN}✓ Message published${NC}"
    echo -e "  Message ID: ${YELLOW}${MESSAGE_ID}${NC}"
else
    echo -e "${RED}✗ Failed to publish message${NC}"
    echo "$PUBSUB_RESULT"
    exit 1
fi

echo ""

# Step 4: Execute Cloud Run Job
echo -e "${BLUE}🚀 Step 4: Executing Cloud Run Job...${NC}"
echo -e "${YELLOW}⏳ This will take 10-15 minutes for full content generation${NC}"
echo ""

gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 \
  --project="$PROJECT_ID" \
  --async \
  2>&1 | tee /tmp/job_exec.log

EXECUTION_NAME=$(grep -o 'dev-vividly-content-worker-[a-z0-9]*' /tmp/job_exec.log | head -1)

if [ -z "$EXECUTION_NAME" ]; then
    echo -e "${RED}✗ Failed to get execution name${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Worker execution started${NC}"
echo -e "  Execution: ${YELLOW}${EXECUTION_NAME}${NC}"
echo ""

# Step 5: Monitor progress
echo -e "${BLUE}📊 Step 5: Monitoring progress...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""

MONITOR_START=$(date +%s)
MONITOR_TIMEOUT=900
CHECK_INTERVAL=10
LAST_STATUS=""
LAST_PERCENTAGE=0

while true; do
    ELAPSED=$(($(date +%s) - MONITOR_START))

    if [ $ELAPSED -gt $MONITOR_TIMEOUT ]; then
        echo ""
        echo -e "${YELLOW}⏱  Monitoring timeout (15 min)${NC}"
        break
    fi

    # Query database
    DB_STATUS=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -A -F'|' -c "
        SELECT
            status,
            progress_percentage,
            current_stage,
            error_message,
            video_url
        FROM content_requests
        WHERE id = '${REQUEST_ID}';
    " 2>/dev/null)

    if [ -n "$DB_STATUS" ]; then
        STATUS=$(echo "$DB_STATUS" | cut -d'|' -f1)
        PERCENTAGE=$(echo "$DB_STATUS" | cut -d'|' -f2)
        STAGE=$(echo "$DB_STATUS" | cut -d'|' -f3)
        ERROR=$(echo "$DB_STATUS" | cut -d'|' -f4)
        VIDEO_URL=$(echo "$DB_STATUS" | cut -d'|' -f5)

        # Print if changed
        if [ "$STATUS" != "$LAST_STATUS" ] || [ "$PERCENTAGE" != "$LAST_PERCENTAGE" ]; then
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

            if [ "$STATUS" = "completed" ]; then
                STATUS_COLOR=$GREEN
            elif [ "$STATUS" = "failed" ]; then
                STATUS_COLOR=$RED
            else
                STATUS_COLOR=$BLUE
            fi

            echo -e "${TIMESTAMP} | Status: ${STATUS_COLOR}${STATUS}${NC} | ${PERCENTAGE}% | ${STAGE}"

            LAST_STATUS="$STATUS"
            LAST_PERCENTAGE="$PERCENTAGE"
        fi

        # Check completion
        if [ "$STATUS" = "completed" ]; then
            echo ""
            echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║                🎉 TEST COMPLETED SUCCESSFULLY! 🎉             ║${NC}"
            echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo -e "${GREEN}✓ Content generation completed${NC}"
            echo -e "  Video URL: ${YELLOW}${VIDEO_URL}${NC}"
            echo ""

            echo -e "${BLUE}📊 Final Record:${NC}"
            "$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
                SELECT
                    id,
                    correlation_id,
                    status,
                    progress_percentage,
                    video_url,
                    script_text,
                    created_at,
                    completed_at
                FROM content_requests
                WHERE id = '${REQUEST_ID}';
            "

            exit 0
        fi

        # Check failure
        if [ "$STATUS" = "failed" ]; then
            echo ""
            echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${RED}║                     ✗ TEST FAILED ✗                          ║${NC}"
            echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo -e "${RED}✗ Content generation failed${NC}"
            echo -e "  Error: ${YELLOW}${ERROR}${NC}"

            exit 1
        fi
    fi

    sleep $CHECK_INTERVAL
done

# Timeout - show status
echo ""
echo -e "${YELLOW}⚠  Monitoring stopped (worker may still be running)${NC}"
echo -e "${BLUE}Current Status:${NC}"
"$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT id, correlation_id, status, progress_percentage, current_stage
    FROM content_requests WHERE id = '${REQUEST_ID}';
"
