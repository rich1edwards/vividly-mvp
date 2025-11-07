#!/bin/bash

# Monitor E2E Test Build Progress
# Usage: ./scripts/monitor_e2e_build.sh [BUILD_ID]

set -e

PROJECT_ID="vividly-dev-rich"
REGION="us-central1"

if [ -z "$1" ]; then
    echo "Getting latest build..."
    BUILD_ID=$(gcloud builds list --project=$PROJECT_ID --limit=1 --format="value(id)")
else
    BUILD_ID="$1"
fi

echo "=========================================="
echo "Monitoring E2E Test Build"
echo "=========================================="
echo "Build ID: $BUILD_ID"
echo "Project: $PROJECT_ID"
echo ""

# Function to check build status
check_status() {
    gcloud builds describe $BUILD_ID \
        --project=$PROJECT_ID \
        --format="value(status)" 2>/dev/null || echo "UNKNOWN"
}

# Function to get build progress
get_progress() {
    gcloud builds describe $BUILD_ID \
        --project=$PROJECT_ID \
        --format="table(steps.name,steps.status)" 2>/dev/null
}

# Monitor build
echo "Monitoring build progress..."
echo ""

LAST_STATUS=""
while true; do
    STATUS=$(check_status)

    if [ "$STATUS" != "$LAST_STATUS" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Status: $STATUS"
        LAST_STATUS="$STATUS"

        # Show step progress
        get_progress
        echo ""
    fi

    # Check if build is done
    if [ "$STATUS" = "SUCCESS" ]; then
        echo "=========================================="
        echo "✅ BUILD SUCCEEDED"
        echo "=========================================="
        echo ""

        # Show final logs
        echo "Final Build Steps:"
        get_progress
        echo ""

        # Check if Cloud Run Job was created
        echo "Checking Cloud Run Job..."
        if gcloud run jobs describe vividly-e2e-tests \
            --region=$REGION \
            --project=$PROJECT_ID > /dev/null 2>&1; then
            echo "✅ Cloud Run Job 'vividly-e2e-tests' exists"

            # Get job details
            gcloud run jobs describe vividly-e2e-tests \
                --region=$REGION \
                --project=$PROJECT_ID \
                --format="table(name,lastModified,maxRetries)"
        else
            echo "⚠️  Cloud Run Job not found"
        fi

        exit 0
    elif [ "$STATUS" = "FAILURE" ]; then
        echo "=========================================="
        echo "❌ BUILD FAILED"
        echo "=========================================="
        echo ""

        # Show logs
        echo "Build Steps:"
        get_progress
        echo ""

        echo "Fetching error logs..."
        gcloud builds log $BUILD_ID --project=$PROJECT_ID 2>&1 | tail -50

        exit 1
    elif [ "$STATUS" = "TIMEOUT" ]; then
        echo "=========================================="
        echo "⏱️  BUILD TIMEOUT"
        echo "=========================================="
        exit 1
    elif [ "$STATUS" = "CANCELLED" ]; then
        echo "=========================================="
        echo "🚫 BUILD CANCELLED"
        echo "=========================================="
        exit 1
    fi

    # Wait before checking again
    sleep 10
done
