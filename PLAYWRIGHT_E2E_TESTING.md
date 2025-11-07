# Playwright End-to-End Testing for RAG System

**Purpose**: Test the complete RAG content generation flow from frontend to production deployment on Google Cloud.

---

## Overview

This Playwright test suite validates:

1. **Frontend → Backend** - User creates content request
2. **Backend → Pub/Sub** - Request published to message queue
3. **Content Worker** - Picks up message from Pub/Sub
4. **RAG Service** - Retrieves relevant OER content with embeddings
5. **Content Generation** - Creates script using RAG-grounded content
6. **Frontend Display** - User sees generated content

---

## Test Architecture

### Three Testing Modes

#### 1. **Local Development Testing**
- Run against local frontend (http://localhost:3000)
- Local backend API (http://localhost:8080)
- **Best for**: Development and debugging

#### 2. **Cloud Testing (Recommended)**
- Run Playwright tests as Cloud Run Job
- Test against production Cloud Run services
- **Best for**: Production validation and CI/CD

#### 3. **Hybrid Testing**
- Run Playwright locally
- Point at production Cloud Run endpoints
- **Best for**: Quick production validation

---

## Quick Start

### Option 1: Run Locally Against Production

```bash
# Set environment variables
export TEST_BASE_URL="https://your-frontend.web.app"
export TEST_API_URL="https://dev-vividly-api-abc123.run.app"

# Install dependencies
cd /Users/richedwards/AI-Dev-Projects/Vividly/tests/e2e
npm install

# Install Playwright browsers
npx playwright install

# Run tests
npx playwright test

# View report
npx playwright show-report
```

### Option 2: Run on Cloud Run (Production Testing)

```bash
# Build Playwright Docker image
cd /Users/richedwards/AI-Dev-Projects/Vividly/tests/e2e

docker build -f Dockerfile.playwright \
  -t us-central1-docker.pkg.dev/vividly-dev-rich/vividly/e2e-tests:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/vividly-dev-rich/vividly/e2e-tests:latest

# Create Cloud Run Job (one-time setup)
gcloud run jobs create vividly-e2e-tests \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/e2e-tests:latest \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --set-env-vars="TEST_BASE_URL=https://your-frontend.web.app,TEST_API_URL=https://dev-vividly-api-abc123.run.app" \
  --max-retries=0 \
  --task-timeout=5m

# Execute tests
gcloud run jobs execute vividly-e2e-tests \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --wait

# View test results in logs
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=vividly-e2e-tests" \
  --project=vividly-dev-rich \
  --limit=100 \
  --format=json
```

---

## Test Coverage

### 1. RAG Content Generation E2E (`test_rag_content_generation.spec.ts`)

**Test: "should generate content with RAG-grounded educational material"**

Steps:
1. Navigate to content creation page
2. Fill form:
   - Topic: Newton's Third Law
   - Interest: basketball
   - Grade level: 10
3. Submit request
4. Wait for async generation (up to 2 minutes)
5. Verify generated content contains:
   - Physics concepts from OER (force, motion, Newton, etc.)
   - Personalization with "basketball"

**What This Validates**:
- ✓ Frontend form works
- ✓ Backend API processes request
- ✓ Pub/Sub message published
- ✓ Content worker picks up message
- ✓ RAG service loads embeddings
- ✓ RAG retrieves relevant OER content
- ✓ Content generation uses RAG context
- ✓ Results stored and returned to frontend

### 2. RAG Quality Metrics (`test_rag_content_generation.spec.ts`)

**Test: "should show RAG retrieval quality metrics"**

Validates that RAG quality metrics are visible in admin dashboard:
- Similarity scores
- Number of chunks retrieved
- Relevance indicators

### 3. Graceful Failure Handling (`test_rag_content_generation.spec.ts`)

**Test: "should handle RAG failure gracefully"**

Validates system behavior when RAG fails:
- Invalid topics don't crash system
- Fallback to mock data works
- User sees appropriate feedback

### 4. Health Checks (`test_rag_content_generation.spec.ts`)

**Test: "should verify RAG service is operational"**

Direct API health checks:
- `/health` endpoint responds
- RAG service status available
- Embeddings loaded confirmation

---

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TEST_BASE_URL` | Frontend URL to test | `https://vividly-dev.web.app` |
| `TEST_API_URL` | Backend API URL | `https://dev-vividly-api-abc.run.app` |
| `CHECK_LOGS` | Enable GCP log checking | `true` or `false` |
| `CI` | Running in CI environment | `true` or `false` |

### Playwright Configuration (`playwright.config.ts`)

Key settings:
- **Timeout**: 120 seconds (for async content generation)
- **Retries**: 2 (in CI), 0 (local)
- **Workers**: 1 (for sequential testing)
- **Reporters**: List, HTML, JSON
- **Browsers**: Chromium (default)

---

## Integration with CI/CD

### Cloud Build Integration

Add to `cloudbuild.yaml`:

```yaml
# Run E2E tests after deployment
- name: 'gcr.io/cloud-builders/gcloud'
  id: 'run-e2e-tests'
  args:
    - 'run'
    - 'jobs'
    - 'execute'
    - 'vividly-e2e-tests'
    - '--region=us-central1'
    - '--project=${PROJECT_ID}'
    - '--wait'
  waitFor: ['deploy-backend', 'deploy-frontend']

# Check test results
- name: 'gcr.io/cloud-builders/gcloud'
  id: 'check-test-results'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      # Get test execution status
      gcloud logging read \
        "resource.type=cloud_run_job AND resource.labels.job_name=vividly-e2e-tests" \
        --limit=1 \
        --format="value(jsonPayload.message)" \
        --project=${PROJECT_ID}
  waitFor: ['run-e2e-tests']
```

### GitHub Actions Integration

```yaml
name: E2E Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        working-directory: tests/e2e
        run: npm ci

      - name: Install Playwright browsers
        working-directory: tests/e2e
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        working-directory: tests/e2e
        env:
          TEST_BASE_URL: ${{ secrets.TEST_BASE_URL }}
          TEST_API_URL: ${{ secrets.TEST_API_URL }}
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

---

## Debugging Tests

### Run Tests in Headed Mode

```bash
# See browser while tests run
npx playwright test --headed

# Run specific test
npx playwright test -g "should generate content with RAG"

# Run in debug mode
npx playwright test --debug
```

### View Test Reports

```bash
# Open HTML report
npx playwright show-report

# View trace for failed test
npx playwright show-trace trace.zip
```

### Check Cloud Run Job Logs

```bash
# View latest execution logs
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=vividly-e2e-tests" \
  --project=vividly-dev-rich \
  --limit=100 \
  --format=json \
  | less

# Filter for test failures
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=vividly-e2e-tests" \
  --project=vividly-dev-rich \
  --limit=100 \
  | grep -i "fail\|error"
```

---

## What to Test for RAG Validation

### Critical RAG Validations

1. **Embeddings Load Successfully**
   - Check: Health endpoint shows embeddings loaded
   - Verify: 3,783 chunks loaded

2. **Query Embeddings Work**
   - Check: Vertex AI authentication succeeds
   - Verify: Not using mock embeddings

3. **Retrieval Quality**
   - Check: Similarity scores >0.65 for matching topics
   - Verify: Retrieved content is relevant to topic + interest

4. **Content Uses RAG Context**
   - Check: Generated script mentions concepts from retrieved chunks
   - Verify: Not just using mock data fallback

5. **Performance**
   - Check: RAG retrieval completes in <2 seconds
   - Verify: Total content generation in <30 seconds

---

## Expected Test Results

### Pass Criteria

✅ **All tests pass** - RAG system is fully operational:
- Frontend submission works
- Backend processes requests
- Content worker receives messages
- RAG retrieves relevant content
- Generated content uses OER material
- Performance meets SLAs

### Partial Pass (Acceptable for MVP)

⚠️ **Core tests pass, advanced tests skip**:
- Content generation works
- RAG retrieves content (even if relevance is low)
- System doesn't crash
- User experience is functional

### Failure Scenarios

❌ **Critical failures requiring investigation**:
- Frontend can't submit requests
- Backend returns 500 errors
- Content worker doesn't pick up messages
- RAG service can't load embeddings
- No content generated after 2 minutes

---

## Test Data

### Sample Test Cases

| Test Case | Topic | Interest | Grade | Expected RAG Content |
|-----------|-------|----------|-------|---------------------|
| Physics + Sports | Newton's 3rd Law | basketball | 10 | Force, motion, jumping, action-reaction |
| Chemistry + Cooking | Chemical reactions | cooking | 9 | Molecular changes, heat, ingredients |
| Biology + Nature | Photosynthesis | gardening | 8 | Plants, sunlight, chlorophyll, energy |
| Math + Finance | Quadratic equations | investing | 11 | Parabolas, optimization, graphs |

---

## Cost Considerations

### Cloud Run Job Pricing

- **Free Tier**: 180,000 vCPU-seconds/month, 360,000 GiB-seconds/month
- **E2E Test Usage**: ~1 minute per run = 60 vCPU-seconds
- **Monthly Runs**: Can run ~3,000 times/month within free tier

### Cost Optimization

1. **Run on Demand**: Only execute when needed (post-deployment, nightly)
2. **Use Free Tier**: Keep within free tier limits
3. **Parallel Testing**: Run multiple tests in single execution
4. **Cache Browsers**: Use Docker layer caching

---

## Troubleshooting

### Issue: "Timeout waiting for content generation"

**Cause**: Content worker not processing messages

**Solutions**:
1. Check Pub/Sub subscription exists
2. Verify Cloud Run Job has Pub/Sub permissions
3. Check worker logs for errors
4. Verify database connection

### Issue: "Content doesn't include RAG material"

**Cause**: RAG fallback to mock data

**Solutions**:
1. Check embeddings are in Docker image (`ls /app/scripts/oer_ingestion/data/embeddings/`)
2. Verify Vertex AI authentication works
3. Check query embeddings aren't using mock fallback
4. Review logs for RAG retrieval errors

### Issue: "Tests fail with authentication errors"

**Cause**: Missing credentials in test environment

**Solutions**:
1. Ensure Cloud Run Job has service account with proper IAM roles
2. For local testing, run `gcloud auth application-default login`
3. Verify service account has:
   - `roles/run.invoker` (to call API)
   - `roles/aiplatform.user` (for Vertex AI)
   - `roles/logging.logWriter` (for test logging)

---

## Next Steps

### Immediate Actions

1. **Set up package.json** with Playwright dependencies
2. **Test locally** against development environment
3. **Deploy to Cloud Run** for production testing
4. **Integrate with CI/CD** for automated testing

### Future Enhancements

1. **Visual Regression Testing**: Screenshot comparisons
2. **Performance Testing**: Load testing with multiple concurrent users
3. **Accessibility Testing**: WCAG compliance validation
4. **Mobile Testing**: Test on mobile browsers
5. **API Contract Testing**: Validate API responses match schema

---

## Summary

**Status**: ✅ Playwright E2E testing framework ready

**What's Provided**:
- ✓ Complete test suite (`test_rag_content_generation.spec.ts`)
- ✓ Dockerfile for Cloud Run (`Dockerfile.playwright`)
- ✓ Playwright configuration (`playwright.config.ts`)
- ✓ Comprehensive documentation (this file)

**What to Do Next**:
1. Review test cases and adjust for your frontend structure
2. Set up `package.json` with dependencies
3. Run tests locally first
4. Deploy to Cloud Run for production testing
5. Integrate with CI/CD pipeline

**Key Benefit**: Full end-to-end validation of RAG system from user interaction to content delivery, running on Google Cloud infrastructure.

---

**Document Created**: 2025-11-03
**Status**: Ready for implementation
**Next Action**: Set up package.json and run first test
