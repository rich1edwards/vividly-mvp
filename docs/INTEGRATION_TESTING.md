# Integration Testing Documentation

This document describes the integration testing framework for the Vividly application, specifically designed to catch configuration issues between the frontend and backend deployments.

## Overview

The integration testing framework validates that:
1. Frontend and backend services are correctly deployed
2. CORS configuration allows frontend-backend communication
3. Authentication flow works end-to-end
4. API endpoints are accessible and functional
5. Traffic is routed to the correct service revisions

## Test Script

Location: `scripts/verify-deployment.sh`

This is a comprehensive bash script that performs 11 different tests across backend, frontend, and integration layers.

### Running the Tests Locally

```bash
./scripts/verify-deployment.sh \
  --frontend-url https://dev-vividly-frontend-758727113555.us-central1.run.app \
  --backend-url https://dev-vividly-api-758727113555.us-central1.run.app \
  --environment dev \
  --test-email john.doe.11@student.hillsboro.edu \
  --test-password Student123!
```

### Test Coverage

#### Backend Tests
1. **Health endpoint check** - Verifies `/health` returns 200
2. **API base path** - Confirms API routes are accessible
3. **CORS preflight from frontend** - Tests that OPTIONS requests from the frontend origin are accepted
4. **CORS rejection from unknown origins** - Ensures unauthorized origins are blocked

#### Frontend Tests
5. **Homepage accessibility** - Verifies frontend serves HTML
6. **HTML content validation** - Checks response is valid HTML

#### Integration Tests
7. **End-to-end login flow** - Tests complete login with email/password
8. **Authenticated requests** - Verifies JWT tokens work for protected endpoints
9. **Backend CORS configuration** - Validates CORS_ORIGINS environment variable includes frontend URL
10. **Traffic routing** - Confirms latest revision is serving traffic

## CI/CD Integration

### GitHub Actions Workflows

The integration tests are automatically run in the following scenarios:

#### 1. Post-Deployment Testing (`.github/workflows/deploy-dev.yml`)

After each deployment to the development environment, the integration tests run automatically:

```yaml
- name: Run integration tests
  env:
    FRONTEND_URL: ${{ steps.urls.outputs.frontend_url }}
    BACKEND_URL: ${{ steps.urls.outputs.api_url }}
  run: |
    chmod +x scripts/verify-deployment.sh
    ./scripts/verify-deployment.sh \
      --frontend-url "$FRONTEND_URL" \
      --backend-url "$BACKEND_URL" \
      --environment dev \
      --test-email "${{ secrets.TEST_USER_EMAIL }}" \
      --test-password "${{ secrets.TEST_USER_PASSWORD }}"
```

#### 2. Standalone Integration Test Workflow (`.github/workflows/integration-tests.yml`)

Can be triggered:
- Manually via GitHub Actions UI
- After successful completion of deployment workflows
- On a schedule (if configured)

### Required Secrets

The following GitHub Secrets must be configured:

- `TEST_USER_EMAIL` - Email address of test user (e.g., `john.doe.11@student.hillsboro.edu`)
- `TEST_USER_PASSWORD` - Password for test user
- `WIF_PROVIDER` - Workload Identity Federation provider for GCP auth
- `WIF_SERVICE_ACCOUNT` - Service account for GCP operations

## Common Issues and Solutions

### Issue: CORS Preflight Failure

**Symptom:** Test fails with "Backend accepts CORS preflight from frontend origin"

**Cause:** Backend `CORS_ORIGINS` environment variable doesn't include the frontend URL

**Solution:**
```bash
gcloud run services update dev-vividly-api \
  --region=us-central1 \
  --update-env-vars='^@^CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","https://dev-vividly-frontend-758727113555.us-central1.run.app"]'
```

### Issue: Traffic Not Routed to Latest Revision

**Symptom:** Test fails with "Backend traffic routed to latest revision"

**Cause:** Cloud Run is serving an older revision instead of the latest deployment

**Solution:**
```bash
# Get latest revision name
LATEST_REVISION=$(gcloud run revisions list \
  --service=dev-vividly-api \
  --region=us-central1 \
  --limit=1 \
  --format="value(metadata.name)")

# Route 100% traffic to latest
gcloud run services update-traffic dev-vividly-api \
  --region=us-central1 \
  --to-revisions=$LATEST_REVISION=100
```

### Issue: Login Fails with Invalid Credentials

**Symptom:** Test fails with "Incorrect email or password"

**Cause:** Test user doesn't exist or password is incorrect

**Solution:**
1. Verify test user exists in the database
2. Update GitHub Secrets with correct credentials
3. Or create a dedicated test user in each environment

## Test Results Interpretation

### Success Output
```
==========================================
Test Results
==========================================
Total Tests: 10
Passed: 10
Failed: 0

✓ All tests passed! Deployment is verified.
```

### Failure Output
```
==========================================
Test Results
==========================================
Total Tests: 10
Passed: 7
Failed: 3

✗ Some tests failed. Please review the deployment.
```

The script exits with code 0 on success and code 1 on failure, allowing CI/CD pipelines to fail the build if tests don't pass.

## Extending the Tests

To add new integration tests:

1. Add a new test function in `scripts/verify-deployment.sh`
2. Use the `print_result` function to report success/failure
3. Increment the `TOTAL_TESTS` counter
4. Document the new test in this file

Example:
```bash
# Test 12: Check new feature
response=$(curl -s "$BACKEND_URL/api/v1/new-feature")
if echo "$response" | grep -q "expected_value"; then
  print_result "New feature works correctly" 0
else
  print_result "New feature works correctly" 1 "Expected value not found"
fi
```

## Monitoring and Alerts

When integration tests fail in CI/CD:

1. **GitHub Actions** - The workflow will fail and send notifications
2. **Issue Creation** - The `integration-tests.yml` workflow automatically creates a GitHub issue on failure
3. **Logs** - Detailed test output is available in GitHub Actions logs
4. **Step Summary** - Results are posted to the GitHub Actions summary page

## Best Practices

1. **Run tests before merging** - Always run integration tests on pull requests
2. **Keep test credentials secure** - Never commit test passwords to the repository
3. **Monitor test duration** - Integration tests should complete within 2-3 minutes
4. **Update tests with features** - When adding new endpoints, add corresponding integration tests
5. **Test in all environments** - Run integration tests in dev, staging, and production

## Related Documentation

- [Deployment Guide](./DEPLOYMENT.md)
- [CORS Configuration](./CORS_CONFIG.md)
- [CI/CD Pipelines](./CICD.md)
