#!/bin/bash
# ===================================
# Dual Modality Pub/Sub Test Script
# ===================================
# Tests Phase 1B implementation by publishing messages
# directly to Pub/Sub, bypassing API authentication.
#
# This tests the worker's handling of modality parameters
# across the full async pipeline.
# ===================================

set -e

PROJECT_ID="vividly-dev-rich"
TOPIC="content-generation-requests"
TEST_STUDENT_ID="test_student_dual_$(date +%s)"

echo "===================================="
echo "DUAL MODALITY PUB/SUB TEST"
echo "===================================="
echo "Project: $PROJECT_ID"
echo "Topic: $TOPIC"
echo "Test Student: $TEST_STUDENT_ID"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test function
publish_message() {
    local test_name=$1
    local message=$2

    echo "------------------------------------"
    echo "TEST: $test_name"
    echo "------------------------------------"
    echo "Message:"
    echo "$message" | jq '.'
    echo ""

    # Publish to Pub/Sub
    message_id=$(gcloud pubsub topics publish "$TOPIC" \
        --project="$PROJECT_ID" \
        --message="$message" \
        --format="value(messageId)")

    if [ -n "$message_id" ]; then
        echo "${GREEN}✓${NC} Message published successfully"
        echo "  Message ID: $message_id"
        echo ""
    else
        echo "${RED}✗${NC} Failed to publish message"
        echo ""
    fi
}

# ===================================
# TEST 1: Backward Compatibility
# ===================================
# Message WITHOUT modality params
# Expected: Worker applies defaults, video generated
# ===================================

echo ""
echo "${YELLOW}[TEST 1] BACKWARD COMPATIBILITY${NC}"
echo "Message without modality parameters (old format)"
echo ""

# Generate valid UUID for test1
TEST1_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

test1_message=$(cat <<EOF
{
  "request_id": "${TEST1_UUID}",
  "correlation_id": "req_test1",
  "student_id": "test_student_dual_1762208763_test1",
  "student_query": "Explain photosynthesis for basketball fans",
  "grade_level": 10,
  "interest": "basketball",
  "environment": "dev"
}
EOF
)

publish_message "Backward Compatibility" "$test1_message"

# ===================================
# TEST 2: Text-Only Request
# ===================================
# Message WITH text-only modality
# Expected: Video generation SKIPPED, cost savings logged
# ===================================

echo ""
echo "${YELLOW}[TEST 2] TEXT-ONLY REQUEST${NC}"
echo "Message with text-only modality (NEW format)"
echo ""

# Generate valid UUID for test2
TEST2_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

test2_message=$(cat <<EOF
{
  "request_id": "${TEST2_UUID}",
  "correlation_id": "req_test2",
  "student_id": "test_student_dual_1762208763_test2",
  "student_query": "Explain cellular respiration for soccer fans",
  "grade_level": 10,
  "interest": "soccer",
  "environment": "dev",
  "requested_modalities": ["text"],
  "preferred_modality": "text"
}
EOF
)

publish_message "Text-Only Request" "$test2_message"

# ===================================
# TEST 3: Explicit Video Request
# ===================================
# Message WITH video modality
# Expected: Video generated (same as default)
# ===================================

echo ""
echo "${YELLOW}[TEST 3] EXPLICIT VIDEO REQUEST${NC}"
echo "Message with explicit video modality"
echo ""

# Generate valid UUID for test3
TEST3_UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

test3_message=$(cat <<EOF
{
  "request_id": "${TEST3_UUID}",
  "correlation_id": "req_test3",
  "student_id": "test_student_dual_1762208763_test3",
  "student_query": "Explain Newton's laws for football fans",
  "grade_level": 10,
  "interest": "football",
  "environment": "dev",
  "requested_modalities": ["video"],
  "preferred_modality": "video"
}
EOF
)

publish_message "Explicit Video Request" "$test3_message"

# ===================================
# SUMMARY
# ===================================

echo ""
echo "===================================="
echo "TEST MESSAGES PUBLISHED"
echo "===================================="
echo "3 test messages sent to Pub/Sub"
echo ""
echo "Next Steps:"
echo ""
echo "1. Check worker execution logs:"
echo "   gcloud logging read 'resource.type=\"cloud_run_job\"' \\"
echo "     --project=$PROJECT_ID --limit=100 --format=json \\"
echo "     | jq -r '.[] | select(.textPayload | contains(\"test_student_dual\")) | .textPayload'"
echo ""
echo "2. Check for cost savings logs:"
echo "   gcloud logging read 'resource.type=\"cloud_run_job\" \"COST SAVINGS\"' \\"
echo "     --project=$PROJECT_ID --limit=20"
echo ""
echo "3. Expected results:"
echo "   ${GREEN}Test 1${NC}: Should log \"Video generation (requested)\" - default behavior"
echo "   ${GREEN}Test 2${NC}: Should log \"Video generation SKIPPED\" and \"COST SAVINGS: \$0.183\""
echo "   ${GREEN}Test 3${NC}: Should log \"Video generation (requested)\" - explicit request"
echo ""
echo "4. Monitor worker executions:"
echo "   gcloud run jobs executions list \\"
echo "     --job=dev-vividly-content-worker \\"
echo "     --region=us-central1 \\"
echo "     --project=$PROJECT_ID \\"
echo "     --limit=10"
