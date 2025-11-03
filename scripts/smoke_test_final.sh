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
echo -e "${BLUE}📋 Retrieving credentials...${NC}"
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" --project="$PROJECT_ID" 2>/dev/null)
DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#^postgresql://[^:]*:\([^@]*\)@.*#\1#p')
export PGPASSWORD="$DB_PASSWORD"

# Use existing test student
REQUEST_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
STUDENT_ID="35c3c63f-c6a5-4cfa-a7d0-660c502ca5cb"  # Existing test student
CORRELATION_ID="smoke-$(date +%s)"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Content Worker E2E Smoke Test                        ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Config:${NC}"
echo -e "  Request ID:   ${YELLOW}${REQUEST_ID}${NC}"
echo -e "  Student ID:   ${YELLOW}${STUDENT_ID}${NC}"
echo -e "  Correlation:  ${YELLOW}${CORRELATION_ID}${NC}"
echo ""

# Create ContentRequest
echo -e "${BLUE}📝 Step 1: Creating ContentRequest record...${NC}"

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
    'Explain photosynthesis for 8th grade students',
    '8',
    3,
    'pending',
    0,
    'Queued',
    NOW()
);
EOF

echo -e "${GREEN}✓ Record created${NC}"

# Publish message
echo -e "${BLUE}📤 Step 2: Publishing to Pub/Sub...${NC}"

MSG='{
  "request_id": "'${REQUEST_ID}'",
  "correlation_id": "'${CORRELATION_ID}'",
  "student_id": "'${STUDENT_ID}'",
  "student_query": "Explain photosynthesis for 8th grade students",
  "grade_level": "8",
  "duration_minutes": 3
}'

gcloud pubsub topics publish content-generation-requests \
  --project="$PROJECT_ID" \
  --message="$MSG" > /dev/null

echo -e "${GREEN}✓ Message published${NC}"

# Execute worker
echo -e "${BLUE}🚀 Step 3: Executing worker...${NC}"

gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 \
  --project="$PROJECT_ID" \
  --async 2>&1 | tee /tmp/exec.log > /dev/null

EXEC=$(grep -o 'dev-vividly-content-worker-[a-z0-9]*' /tmp/exec.log | head -1)

echo -e "${GREEN}✓ Worker started: ${YELLOW}${EXEC}${NC}"

# Monitor
echo ""
echo -e "${BLUE}📊 Step 4: Monitoring (15 min timeout)...${NC}"
echo ""

START=$(date +%s)
LAST_ST=""
LAST_PCT=0

while true; do
    ELAPSED=$(($(date +%s) - START))
    [ $ELAPSED -gt 900 ] && break

    DATA=$("$PSQL" -h "$DB_IP" -p 5432 -U "$DB_USER" -d "$DB_NAME" -t -A -F'|' -c "
        SELECT status, progress_percentage, current_stage, error_message, video_url
        FROM content_requests WHERE id = '${REQUEST_ID}';" 2>/dev/null)

    if [ -n "$DATA" ]; then
        ST=$(echo "$DATA" | cut -d'|' -f1)
        PCT=$(echo "$DATA" | cut -d'|' -f2)
        STAGE=$(echo "$DATA" | cut -d'|' -f3)
        ERR=$(echo "$DATA" | cut -d'|' -f4)
        VID=$(echo "$DATA" | cut -d'|' -f5)

        if [ "$ST" != "$LAST_ST" ] || [ "$PCT" != "$LAST_PCT" ]; then
            TS=$(date '+%H:%M:%S')
            [ "$ST" = "completed" ] && COL=$GREEN || COL=$BLUE
            echo -e "${TS} | ${COL}${ST}${NC} | ${PCT}% | ${STAGE}"
            LAST_ST="$ST"
            LAST_PCT="$PCT"
        fi

        if [ "$ST" = "completed" ]; then
            echo ""
            echo -e "${GREEN}═══════════════════════════════════════════${NC}"
            echo -e "${GREEN}  🎉 TEST PASSED - Content Generated! 🎉  ${NC}"
            echo -e "${GREEN}═══════════════════════════════════════════${NC}"
            echo -e "  Video: ${YELLOW}${VID}${NC}"
            exit 0
        fi

        if [ "$ST" = "failed" ]; then
            echo ""
            echo -e "${RED}═══════════════════════════════════════════${NC}"
            echo -e "${RED}          ✗ TEST FAILED ✗                  ${NC}"
            echo -e "${RED}═══════════════════════════════════════════${NC}"
            echo -e "  Error: ${YELLOW}${ERR}${NC}"
            exit 1
        fi
    fi

    sleep 10
done

echo ""
echo -e "${YELLOW}⏱ Timeout reached${NC}"
exit 1
