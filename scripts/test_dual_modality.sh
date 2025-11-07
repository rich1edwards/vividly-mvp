#!/bin/bash
# ===================================
# Dual Modality Test Script
# ===================================
# Tests Phase 1B dual modality implementation:
# 1. Backward compatibility (no modality params)
# 2. Text-only requests (new functionality)
# 3. Explicit video requests
# ===================================

set -e

PROJECT_ID="vividly-dev-rich"
API_BASE_URL="https://dev-vividly-api-758727113555.us-central1.run.app"
TEST_STUDENT_ID="test_student_dual_modality_$(date +%s)"

echo "===================================="
echo "DUAL MODALITY TEST SUITE"
echo "===================================="
echo "Project: $PROJECT_ID"
echo "API Base: $API_BASE_URL"
echo "Test Student: $TEST_STUDENT_ID"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local json_payload=$2
    local expected_behavior=$3

    echo "------------------------------------"
    echo "TEST: $test_name"
    echo "------------------------------------"
    echo "Payload:"
    echo "$json_payload" | jq '.'
    echo ""

    TESTS_RUN=$((TESTS_RUN + 1))

    # Make API request
    response=$(curl -s -X POST "$API_BASE_URL/api/v1/content/generate" \
        -H "Content-Type: application/json" \
        -d "$json_payload")

    echo "Response:"
    echo "$response" | jq '.'
    echo ""

    # Extract request_id for tracking
    request_id=$(echo "$response" | jq -r '.request_id // empty')
    correlation_id=$(echo "$response" | jq -r '.correlation_id // empty')

    if [ -n "$request_id" ]; then
        echo "${GREEN}✓${NC} Request created successfully"
        echo "  Request ID: $request_id"
        echo "  Correlation ID: $correlation_id"
        echo ""
        echo "Expected behavior: $expected_behavior"
        echo ""
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "${RED}✗${NC} Request failed"
        echo "  Error: $(echo "$response" | jq -r '.detail // .message // "Unknown error"')"
        echo ""
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Return request_id for monitoring
    echo "$request_id"
}

# ===================================
# TEST 1: Backward Compatibility
# ===================================
# Existing API clients don't send modality params
# Expected: Video should be generated (default behavior)
# ===================================

echo ""
echo "${YELLOW}[TEST 1] BACKWARD COMPATIBILITY${NC}"
echo "Testing existing API behavior (no modality parameters)"
echo ""

test1_payload=$(cat <<EOF
{
  "student_query": "Explain photosynthesis for basketball fans",
  "student_id": "${TEST_STUDENT_ID}_test1",
  "grade_level": 10
}
EOF
)

test1_request_id=$(run_test \
    "Backward Compatibility (No Modality Params)" \
    "$test1_payload" \
    "Should generate VIDEO (default behavior)")

# ===================================
# TEST 2: Text-Only Request
# ===================================
# New API clients request text-only
# Expected: NO video generation, cost savings logged
# ===================================

echo ""
echo "${YELLOW}[TEST 2] TEXT-ONLY REQUEST${NC}"
echo "Testing new text-only functionality"
echo ""

test2_payload=$(cat <<EOF
{
  "student_query": "Explain cellular respiration for soccer fans",
  "student_id": "${TEST_STUDENT_ID}_test2",
  "grade_level": 10,
  "requested_modalities": ["text"],
  "preferred_modality": "text"
}
EOF
)

test2_request_id=$(run_test \
    "Text-Only Request (New Functionality)" \
    "$test2_payload" \
    "Should SKIP video generation, save \$0.183")

# ===================================
# TEST 3: Explicit Video Request
# ===================================
# New API clients explicitly request video
# Expected: Video generated (same as default)
# ===================================

echo ""
echo "${YELLOW}[TEST 3] EXPLICIT VIDEO REQUEST${NC}"
echo "Testing explicit video modality"
echo ""

test3_payload=$(cat <<EOF
{
  "student_query": "Explain Newton's laws for football fans",
  "student_id": "${TEST_STUDENT_ID}_test3",
  "grade_level": 10,
  "requested_modalities": ["video"],
  "preferred_modality": "video"
}
EOF
)

test3_request_id=$(run_test \
    "Explicit Video Request" \
    "$test3_payload" \
    "Should generate VIDEO (explicit request)")

# ===================================
# SUMMARY
# ===================================

echo ""
echo "===================================="
echo "TEST SUMMARY"
echo "===================================="
echo "Tests Run: $TESTS_RUN"
echo "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo "${RED}Tests Failed: $TESTS_FAILED${NC}"
else
    echo "Tests Failed: $TESTS_FAILED"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Monitor worker logs for processing"
    echo "2. Check for cost tracking logs:"
    echo "   gcloud logging read 'resource.type=\"cloud_run_job\" \"COST SAVINGS\"' \\"
    echo "     --project=$PROJECT_ID --limit=50"
    echo ""
    echo "3. Verify content generation status:"
    echo "   Test 1 (Video): Request ID = $test1_request_id"
    echo "   Test 2 (Text):  Request ID = $test2_request_id"
    echo "   Test 3 (Video): Request ID = $test3_request_id"
    exit 0
else
    echo "${RED}✗ SOME TESTS FAILED${NC}"
    echo "Check API logs for errors"
    exit 1
fi
