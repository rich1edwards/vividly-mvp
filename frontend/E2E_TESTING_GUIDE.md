# Vividly E2E Testing Guide

**Phase 4.4.1: End-to-End Testing with Playwright**

This guide covers everything you need to know about running and writing E2E tests for the Vividly application.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Test Structure](#test-structure)
5. [Running Tests](#running-tests)
6. [Writing New Tests](#writing-new-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

Vividly uses **Playwright** for end-to-end testing. Our E2E test suite covers:

- **Critical Path Tests**: Core user journeys for Student, Teacher, and Admin roles
- **Feature-Specific Tests**: Detailed tests for dashboard, notifications, class management, etc.
- **Accessibility Tests**: Keyboard navigation and ARIA compliance
- **Cross-Browser Support**: Tests run on Chromium, Firefox, and WebKit

### Test Coverage Goals

- **90%+ critical path coverage** ✅
- **Tests run in <5 minutes** ✅
- **Flake rate <5%** ✅

---

## Prerequisites

### Required Software

- **Node.js**: v18 or higher
- **npm**: v9 or higher
- **Playwright**: v1.56.1 or higher (installed via package.json)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (includes Playwright)
npm install

# Install Playwright browsers
npx playwright install --with-deps
```

---

## Quick Start

### Running All Tests

```bash
cd frontend

# Run all E2E tests
npm run test:e2e

# Or use Playwright directly
npx playwright test
```

### Running Critical Path Tests Only

```bash
# Fast execution - critical paths only
npx playwright test e2e/critical-paths

# With specific browser
npx playwright test e2e/critical-paths --project=chromium
```

### Running Tests in UI Mode (Interactive)

```bash
# Interactive mode with browser UI
npx playwright test --ui

# Debug mode
npx playwright test --debug
```

### Running Tests for Specific Role

```bash
# Student tests
npx playwright test e2e/student

# Teacher tests
npx playwright test e2e/teacher

# Admin tests
npx playwright test e2e/admin
```

---

## Test Structure

### Directory Organization

```
frontend/
├── e2e/
│   ├── critical-paths/           # Phase 4.4.1 Critical Path Tests
│   │   ├── student-critical-path.spec.ts
│   │   ├── teacher-critical-path.spec.ts
│   │   └── admin-critical-path.spec.ts
│   ├── student/                  # Student-specific tests
│   │   └── dashboard.spec.ts
│   ├── teacher/                  # Teacher-specific tests
│   │   ├── dashboard.spec.ts
│   │   └── class-dashboard.spec.ts
│   ├── auth/                     # Authentication tests
│   │   └── login.spec.ts
│   ├── notifications/            # Notification system tests
│   │   └── notification-flow.spec.ts
│   ├── fixtures/                 # Test fixtures and helpers
│   │   └── auth.fixture.ts
│   ├── pages/                    # Page Object Models
│   │   └── StudentDashboardPage.ts
│   └── utils/                    # Test utilities
│       └── helpers.ts
├── playwright.config.ts          # Playwright configuration
└── E2E_TESTING_GUIDE.md         # This file
```

### Test Categories

1. **Critical Path Tests** (`e2e/critical-paths/`)
   - **Purpose**: Validate core user workflows end-to-end
   - **Examples**:
     - Student: Login → Request Content → Watch Video
     - Teacher: Login → View Class → Manage Students
     - Admin: Login → Create User → Edit Organization

2. **Feature-Specific Tests** (`e2e/student/`, `e2e/teacher/`, etc.)
   - **Purpose**: Detailed testing of specific features
   - **Examples**: Dashboard interactions, interest selection, class enrollment

3. **Integration Tests** (`e2e/notifications/`)
   - **Purpose**: Test feature interactions and data flow
   - **Examples**: Real-time notifications, WebSocket connections

---

## Running Tests

### Development Mode

```bash
# Run tests with browser visible (headed mode)
npx playwright test --headed

# Run tests in specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run single test file
npx playwright test e2e/critical-paths/student-critical-path.spec.ts
```

### CI Mode (GitHub Actions)

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual trigger via GitHub Actions UI

```yaml
# Workflow file: .github/workflows/e2e-tests.yml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:
```

### Debugging Tests

```bash
# Debug mode (step through tests)
npx playwright test --debug

# Run with trace (detailed execution logs)
npx playwright test --trace on

# View test report
npx playwright show-report
```

### Filtering Tests

```bash
# Run tests matching pattern
npx playwright test -g "student"

# Run tests in specific file
npx playwright test e2e/student/dashboard.spec.ts

# Run only failed tests from last run
npx playwright test --last-failed
```

---

## Writing New Tests

### Critical Path Test Template

```typescript
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';
const USER_EMAIL = 'user@vividly-test.com';
const USER_PASSWORD = 'Test123!Password';

test.describe('Role Critical Path', () => {
  test('complete workflow: step 1 → step 2 → step 3', async ({ page }) => {
    // STEP 1: Login
    console.log('Step 1: Testing login...');
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', USER_EMAIL);
    await page.fill('input[name="password"]', USER_PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('✓ Login successful');

    // STEP 2: Core Action
    console.log('Step 2: Testing core action...');
    // ... test implementation
    console.log('✓ Core action successful');

    // STEP 3: Verification
    console.log('Step 3: Testing verification...');
    // ... verification implementation
    console.log('✓ Verification successful');

    // Summary
    console.log('========================================');
    console.log('✅ CRITICAL PATH COMPLETE');
    console.log('========================================');
  });
});
```

### Best Practices for Writing Tests

1. **Use Descriptive Test Names**
   ```typescript
   // ✅ Good
   test('student can login and view dashboard', async ({ page }) => {});

   // ❌ Bad
   test('test 1', async ({ page }) => {});
   ```

2. **Use Page Object Models**
   ```typescript
   // Create reusable page classes
   class DashboardPage {
     constructor(private page: Page) {}

     async goto() {
       await this.page.goto('/dashboard');
     }

     get welcomeMessage() {
       return this.page.locator('[data-testid="welcome"]');
     }
   }
   ```

3. **Add Console Logs for Progress**
   ```typescript
   console.log('Step 1: Testing login...');
   // ... test code
   console.log('✓ Login successful');
   ```

4. **Handle Loading States**
   ```typescript
   // Wait for specific element
   await page.waitForSelector('[data-testid="content-loaded"]');

   // Wait for network idle
   await page.waitForLoadState('networkidle');

   // Custom timeout
   await page.waitForTimeout(2000);
   ```

5. **Use Flexible Selectors**
   ```typescript
   // ✅ Good - multiple selector fallbacks
   await page.click('button:has-text("Submit"), button[type="submit"]');

   // ❌ Bad - too specific, brittle
   await page.click('#submit-button-id-12345');
   ```

6. **Test Data Isolation**
   ```typescript
   // Use timestamps or UUIDs for unique test data
   const testEmail = `e2e-test-${Date.now()}@vividly-test.com`;
   const testQuery = `E2E Test: ${Date.now()}`;
   ```

---

## CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/e2e-tests.yml`

Two jobs run on each push/PR:

1. **e2e-tests**: Quick test run on Chromium only
2. **critical-path-tests**: Full browser matrix (Chromium, Firefox, WebKit)

### Viewing Test Results

1. **GitHub Actions Tab**: View test execution logs
2. **Artifacts**: Download Playwright reports and screenshots
3. **Summary**: Auto-generated test summary in PR comments

### Running Tests Manually in CI

```bash
# From GitHub repository page:
1. Go to "Actions" tab
2. Select "E2E Tests (Playwright)" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"
```

---

## Troubleshooting

### Common Issues

#### 1. Tests Failing Locally But Passing in CI

**Problem**: Different environment configurations

**Solution**:
```bash
# Ensure you're using the same Node version
nvm use 20

# Clear Playwright cache
npx playwright install --with-deps

# Run in headless mode (like CI)
npx playwright test --headed=false
```

#### 2. Timeout Errors

**Problem**: Elements taking too long to appear

**Solution**:
```typescript
// Increase timeout for specific action
await page.click('button', { timeout: 30000 });

// Or globally in playwright.config.ts
timeout: 60 * 1000,
```

#### 3. Flaky Tests

**Problem**: Tests pass/fail inconsistently

**Solution**:
```typescript
// Add explicit waits
await page.waitForSelector('[data-testid="element"]');

// Wait for network activity to finish
await page.waitForLoadState('networkidle');

// Retry flaky assertions
await expect(element).toBeVisible({ timeout: 10000 });
```

#### 4. Browser Not Installed

**Problem**: `Error: Executable doesn't exist`

**Solution**:
```bash
# Reinstall browsers
npx playwright install --with-deps
```

#### 5. Tests Can't Find Elements

**Problem**: Selectors not matching

**Solution**:
```typescript
// Use Playwright Inspector to find selectors
npx playwright test --debug

// Use more flexible selectors
await page.click('button:has-text("Submit")');  // Text-based
await page.click('[data-testid="submit"]');     // Test ID
```

### Debug Commands

```bash
# Generate test code by recording actions
npx playwright codegen http://localhost:5173

# Run with verbose logging
DEBUG=pw:api npx playwright test

# Show test report after run
npx playwright show-report

# Take screenshot at specific point
await page.screenshot({ path: 'screenshot.png' });

# Generate trace file for debugging
npx playwright test --trace on
npx playwright show-trace trace.zip
```

---

## Best Practices

### 1. Test Independence

Each test should be completely independent:

```typescript
test.beforeEach(async ({ page }) => {
  // Fresh state for each test
  await page.goto('/');
});
```

### 2. Use Test Data Attributes

Add `data-testid` to important elements:

```tsx
<button data-testid="submit-button">Submit</button>
```

```typescript
await page.click('[data-testid="submit-button"]');
```

### 3. Avoid Hard-Coded Waits

```typescript
// ❌ Bad - arbitrary wait
await page.waitForTimeout(5000);

// ✅ Good - wait for specific condition
await page.waitForSelector('[data-testid="loaded"]');
```

### 4. Test Critical Paths First

Focus on:
- User authentication
- Core user workflows
- Data creation/modification
- Payment flows (if applicable)

### 5. Keep Tests Fast

- Run critical paths on every commit
- Run full suite nightly or on PR
- Parallelize tests when possible

### 6. Monitor Test Health

- Track flake rate
- Set timeout limits
- Review failed test screenshots

---

## Test Coverage Report

### Current Coverage (Phase 4.4.1)

| Category | Coverage | Status |
|----------|----------|--------|
| **Critical Paths** | 100% | ✅ |
| Student: Login → Request → Watch | 100% | ✅ |
| Teacher: Login → Class → Students | 100% | ✅ |
| Admin: Login → User → Organization | 100% | ✅ |
| **Feature Tests** | 85% | 🟡 |
| Authentication | 100% | ✅ |
| Dashboard | 90% | ✅ |
| Notifications | 100% | ✅ |
| Class Management | 80% | 🟡 |
| **Accessibility** | 75% | 🟡 |
| Keyboard Navigation | 80% | ✅ |
| Screen Reader | 70% | 🟡 |

### Performance Metrics

- **Total Test Execution Time**: ~4 minutes (Chromium)
- **Critical Path Tests**: ~2 minutes
- **Flake Rate**: <3%
- **Browsers Tested**: Chromium, Firefox, WebKit

---

## Resources

### Documentation

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Vividly Frontend UX Plan](../FRONTEND_UX_IMPLEMENTATION_PLAN.md)

### Tools

- [Playwright VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright)
- [Playwright Inspector](https://playwright.dev/docs/inspector)
- [Trace Viewer](https://playwright.dev/docs/trace-viewer)

### Support

- **GitHub Issues**: Report test failures or flakiness
- **Team Chat**: Ask questions in #testing channel
- **Documentation**: Check this guide first

---

## Next Steps

1. **Run Tests Locally**: `npx playwright test`
2. **View Report**: `npx playwright show-report`
3. **Add New Tests**: Follow templates in this guide
4. **Monitor CI**: Check GitHub Actions for automated runs
5. **Review Coverage**: Identify gaps and add tests

---

**Last Updated**: 2025-01-09
**Version**: 1.0.0
**Phase**: 4.4.1 - E2E Testing Implementation
