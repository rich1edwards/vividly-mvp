#!/bin/bash

# Run Playwright E2E Tests for RAG Content Generation
#
# Usage:
#   ./scripts/run_e2e_tests.sh [local|cloud|production]
#
# Modes:
#   local      - Run against local dev environment (default)
#   cloud      - Deploy and run on Cloud Run
#   production - Run locally against production endpoints

set -e

MODE="${1:-local}"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-vividly-dev-rich}"
REGION="us-central1"

echo "=========================================="
echo "Playwright E2E Tests for RAG System"
echo "=========================================="
echo "Mode: $MODE"
echo "Project: $PROJECT_ID"
echo ""

case "$MODE" in
  local)
    echo "Running tests against local environment..."
    echo ""

    # Set environment variables
    export TEST_BASE_URL="http://localhost:3000"
    export TEST_API_URL="http://localhost:8080"

    # Check if servers are running
    if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
      echo "❌ Backend API not running on http://localhost:8080"
      echo "Start it with: cd backend && uvicorn app.main:app --reload"
      exit 1
    fi

    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
      echo "❌ Frontend not running on http://localhost:3000"
      echo "Start it with: cd frontend && npm run dev"
      exit 1
    fi

    echo "✓ Backend API: $TEST_API_URL"
    echo "✓ Frontend: $TEST_BASE_URL"
    echo ""

    # Install dependencies if needed
    if [ ! -d "tests/e2e/node_modules" ]; then
      echo "Installing Playwright dependencies..."
      cd tests/e2e
      npm install
      npx playwright install
      cd ../..
    fi

    # Run tests
    echo "Running Playwright tests..."
    cd tests/e2e
    npm test

    # Show report
    echo ""
    echo "Opening test report..."
    npm run report
    ;;

  cloud)
    echo "Deploying and running tests on Cloud Run..."
    echo ""

    # Get production URLs
    BACKEND_URL=$(gcloud run services describe dev-vividly-api \
      --region=$REGION \
      --project=$PROJECT_ID \
      --format="value(status.url)" 2>/dev/null || echo "")

    if [ -z "$BACKEND_URL" ]; then
      echo "❌ Backend service not found"
      echo "Deploy it first: cd terraform && terraform apply"
      exit 1
    fi

    FRONTEND_URL="${FRONTEND_URL:-https://vividly-dev.web.app}"

    echo "✓ Backend API: $BACKEND_URL"
    echo "✓ Frontend: $FRONTEND_URL"
    echo ""

    # Build Docker image
    echo "Building Playwright Docker image..."
    cd tests/e2e
    docker build -f Dockerfile.playwright \
      -t $REGION-docker.pkg.dev/$PROJECT_ID/vividly/e2e-tests:latest .

    # Push to Artifact Registry
    echo "Pushing to Artifact Registry..."
    docker push $REGION-docker.pkg.dev/$PROJECT_ID/vividly/e2e-tests:latest

    # Create/update Cloud Run Job
    echo "Creating/updating Cloud Run Job..."
    if gcloud run jobs describe vividly-e2e-tests \
      --region=$REGION \
      --project=$PROJECT_ID > /dev/null 2>&1; then
      echo "Updating existing job..."
      gcloud run jobs update vividly-e2e-tests \
        --image=$REGION-docker.pkg.dev/$PROJECT_ID/vividly/e2e-tests:latest \
        --region=$REGION \
        --project=$PROJECT_ID \
        --set-env-vars="TEST_BASE_URL=$FRONTEND_URL,TEST_API_URL=$BACKEND_URL"
    else
      echo "Creating new job..."
      gcloud run jobs create vividly-e2e-tests \
        --image=$REGION-docker.pkg.dev/$PROJECT_ID/vividly/e2e-tests:latest \
        --region=$REGION \
        --project=$PROJECT_ID \
        --set-env-vars="TEST_BASE_URL=$FRONTEND_URL,TEST_API_URL=$BACKEND_URL" \
        --max-retries=0 \
        --task-timeout=5m
    fi

    # Execute tests
    echo ""
    echo "Executing E2E tests on Cloud Run..."
    gcloud run jobs execute vividly-e2e-tests \
      --region=$REGION \
      --project=$PROJECT_ID \
      --wait

    # Show results
    echo ""
    echo "Test execution complete. Viewing logs..."
    gcloud logging read \
      "resource.type=cloud_run_job AND resource.labels.job_name=vividly-e2e-tests" \
      --project=$PROJECT_ID \
      --limit=50 \
      --format=json \
      | python3 -c "
import sys, json
logs = [json.loads(line) for line in sys.stdin if line.strip()]
for log in logs:
    msg = log.get('textPayload', '')
    if msg:
        print(msg)
"
    ;;

  production)
    echo "Running tests locally against production..."
    echo ""

    # Get production URLs
    BACKEND_URL=$(gcloud run services describe dev-vividly-api \
      --region=$REGION \
      --project=$PROJECT_ID \
      --format="value(status.url)" 2>/dev/null || echo "")

    if [ -z "$BACKEND_URL" ]; then
      echo "❌ Backend service not found"
      exit 1
    fi

    FRONTEND_URL="${FRONTEND_URL:-https://vividly-dev.web.app}"

    # Set environment variables
    export TEST_BASE_URL="$FRONTEND_URL"
    export TEST_API_URL="$BACKEND_URL"

    echo "✓ Backend API: $TEST_API_URL"
    echo "✓ Frontend: $TEST_BASE_URL"
    echo ""

    # Install dependencies if needed
    if [ ! -d "tests/e2e/node_modules" ]; then
      echo "Installing Playwright dependencies..."
      cd tests/e2e
      npm install
      npx playwright install
      cd ../..
    fi

    # Run tests
    echo "Running Playwright tests..."
    cd tests/e2e
    npm test

    # Show report
    echo ""
    echo "Opening test report..."
    npm run report
    ;;

  *)
    echo "❌ Unknown mode: $MODE"
    echo ""
    echo "Usage: $0 [local|cloud|production]"
    echo ""
    echo "Modes:"
    echo "  local      - Run against local dev environment (default)"
    echo "  cloud      - Deploy and run on Cloud Run"
    echo "  production - Run locally against production endpoints"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "✓ E2E Tests Complete"
echo "=========================================="
