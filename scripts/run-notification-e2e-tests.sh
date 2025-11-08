#!/bin/bash

###############################################################################
# Phase 1.4: Run E2E Notification Tests Locally
#
# This script runs the complete E2E test suite for the real-time notification
# system, including:
# - Backend API server
# - Push worker for notifications
# - Frontend development server
# - Playwright E2E tests across all browsers
#
# Prerequisites:
# - Backend dependencies installed (pip install -r requirements.txt)
# - Frontend dependencies installed (npm install in frontend/)
# - Playwright browsers installed (npx playwright install)
# - PostgreSQL running locally
# - Redis running locally
#
# Usage:
#   ./scripts/run-notification-e2e-tests.sh [OPTIONS]
#
# Options:
#   --browser BROWSER    Run tests on specific browser (chromium, firefox, webkit, or all)
#   --headed             Run tests in headed mode (show browser)
#   --debug              Run tests in debug mode (pause on failures)
#   --ui                 Run tests in UI mode (interactive)
#   --help               Show this help message
#
# Examples:
#   ./scripts/run-notification-e2e-tests.sh
#   ./scripts/run-notification-e2e-tests.sh --browser chromium --headed
#   ./scripts/run-notification-e2e-tests.sh --ui
###############################################################################

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0;0m' # No Color

# Default configuration
BROWSER="all"
HEADED=""
DEBUG=""
UI_MODE=""
BACKEND_PORT=8000
FRONTEND_PORT=5173
BACKEND_PID=""
WORKER_PID=""
FRONTEND_PID=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --browser)
      BROWSER="$2"
      shift 2
      ;;
    --headed)
      HEADED="--headed"
      shift
      ;;
    --debug)
      DEBUG="--debug"
      shift
      ;;
    --ui)
      UI_MODE="--ui"
      shift
      ;;
    --help)
      head -n 33 "$0" | tail -n +3
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Run with --help for usage information"
      exit 1
      ;;
  esac
done

# Cleanup function - kills all background processes
cleanup() {
  echo -e "\n${YELLOW}Cleaning up processes...${NC}"

  if [ -n "$FRONTEND_PID" ]; then
    echo "Stopping frontend server (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || true
  fi

  if [ -n "$WORKER_PID" ]; then
    echo "Stopping push worker (PID: $WORKER_PID)..."
    kill $WORKER_PID 2>/dev/null || true
  fi

  if [ -n "$BACKEND_PID" ]; then
    echo "Stopping backend server (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
  fi

  # Also kill any lingering processes on these ports
  lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null || true
  lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

  echo -e "${GREEN}Cleanup complete${NC}"
}

# Register cleanup function to run on script exit
trap cleanup EXIT INT TERM

# Print header
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  Phase 1.4: E2E Notification Tests${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check PostgreSQL
if ! pg_isready -q; then
  echo -e "${RED}PostgreSQL is not running. Please start PostgreSQL and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Check Redis
if ! redis-cli ping &>/dev/null; then
  echo -e "${RED}Redis is not running. Please start Redis and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"

# Check backend dependencies
if [ ! -d "$PROJECT_ROOT/backend/venv" ] && [ ! -d "$PROJECT_ROOT/backend/.venv" ]; then
  echo -e "${YELLOW}Backend virtual environment not found. Creating it now...${NC}"
  cd "$PROJECT_ROOT/backend"
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  cd "$PROJECT_ROOT"
fi
echo -e "${GREEN}✓ Backend dependencies ready${NC}"

# Check frontend dependencies
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
  echo -e "${YELLOW}Frontend dependencies not found. Installing now...${NC}"
  cd "$PROJECT_ROOT/frontend"
  npm install
  cd "$PROJECT_ROOT"
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

# Check Playwright browsers
if ! npx playwright --version &>/dev/null; then
  echo -e "${YELLOW}Playwright not found. Installing Playwright browsers...${NC}"
  cd "$PROJECT_ROOT/frontend"
  npx playwright install
  cd "$PROJECT_ROOT"
fi
echo -e "${GREEN}✓ Playwright browsers ready${NC}"

echo

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/vividly_test"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="test_secret_key_for_local_e2e_testing"
export ALGORITHM="HS256"
export DEBUG="True"
export CORS_ORIGINS="http://localhost:5173,http://localhost:3000"
export VITE_API_URL="http://localhost:$BACKEND_PORT"

# Start backend API server
echo -e "${YELLOW}Starting backend API server on port $BACKEND_PORT...${NC}"
cd "$PROJECT_ROOT/backend"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
elif [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Run migrations
alembic upgrade head 2>/dev/null || echo -e "${YELLOW}Warning: Database migrations may have failed${NC}"

# Start backend server in background
uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/backend-e2e.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo -n "Waiting for backend to be ready"
RETRY_COUNT=0
MAX_RETRIES=30
until curl -s http://localhost:$BACKEND_PORT/health > /dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo -n "."
  sleep 1
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo -e "\n${RED}Backend failed to start. Check logs at /tmp/backend-e2e.log${NC}"
  exit 1
fi
echo -e "\n${GREEN}✓ Backend server is running (PID: $BACKEND_PID)${NC}"

# Start push worker
echo -e "${YELLOW}Starting push worker for notifications...${NC}"
python -m app.workers.push_worker > /tmp/worker-e2e.log 2>&1 &
WORKER_PID=$!
sleep 3  # Give worker time to initialize
echo -e "${GREEN}✓ Push worker is running (PID: $WORKER_PID)${NC}"

# Build and start frontend
echo -e "${YELLOW}Building frontend application...${NC}"
cd "$PROJECT_ROOT/frontend"
npm run build > /tmp/frontend-build-e2e.log 2>&1

echo -e "${YELLOW}Starting frontend server on port $FRONTEND_PORT...${NC}"
npm run preview -- --port $FRONTEND_PORT --host > /tmp/frontend-e2e.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo -n "Waiting for frontend to be ready"
RETRY_COUNT=0
until curl -s http://localhost:$FRONTEND_PORT > /dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo -n "."
  sleep 1
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo -e "\n${RED}Frontend failed to start. Check logs at /tmp/frontend-e2e.log${NC}"
  exit 1
fi
echo -e "\n${GREEN}✓ Frontend server is running (PID: $FRONTEND_PID)${NC}"

echo
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  Running E2E Tests${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo

# Build Playwright command
PLAYWRIGHT_CMD="npx playwright test e2e/notifications/notification-flow.spec.ts"

if [ "$BROWSER" != "all" ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=$BROWSER"
fi

if [ -n "$HEADED" ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD $HEADED"
fi

if [ -n "$DEBUG" ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD $DEBUG"
fi

if [ -n "$UI_MODE" ]; then
  PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD $UI_MODE"
fi

# Run tests
echo -e "${YELLOW}Running: $PLAYWRIGHT_CMD${NC}"
echo

export BASE_URL="http://localhost:$FRONTEND_PORT"
eval $PLAYWRIGHT_CMD

TEST_EXIT_CODE=$?

echo
echo -e "${BLUE}======================================================================${NC}"
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}  ✓ All tests passed!${NC}"
else
  echo -e "${RED}  ✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
  echo -e "${YELLOW}  Check the Playwright HTML report for details:${NC}"
  echo -e "${YELLOW}    npx playwright show-report${NC}"
fi
echo -e "${BLUE}======================================================================${NC}"

# Cleanup will be called automatically by trap

exit $TEST_EXIT_CODE
