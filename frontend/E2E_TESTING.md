# Playwright E2E Testing Guide

Complete guide for end-to-end testing of the Vividly frontend application using Playwright.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

Vividly uses [Playwright](https://playwright.dev/) for end-to-end testing. Playwright provides:

- **Cross-browser testing**: Chromium, Firefox, and WebKit
- **Mobile emulation**: Test on various mobile devices
- **Auto-waiting**: Waits for elements to be actionable before performing actions
- **Network interception**: Mock API responses for testing
- **Visual testing**: Screenshot and video capture
- **Debugging tools**: UI mode, trace viewer, and inspector

### Test Coverage

Our E2E tests cover:

- ✅ **Authentication flows**: Login, registration, password reset
- ✅ **Student dashboard**: Interests, progress tracking, class enrollment, video playback
- ✅ **Teacher dashboard**: Class management, roster management, student account requests
- ✅ **Accessibility**: Keyboard navigation, ARIA labels, screen reader support
- ✅ **Responsive design**: Desktop, tablet, and mobile viewports

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Frontend application running on `http://localhost:5173`
- Backend API running (for integration tests)

### Installation

Playwright is already installed as a dev dependency. If you need to reinstall:

```bash
npm install -D @playwright/test@latest
```

### Install Browsers

Install Playwright browsers (Chromium, Firefox, WebKit):

```bash
npx playwright install
```

For Chromium only (faster):

```bash
npx playwright install chromium
```

## Test Structure

```
frontend/
├── e2e/
│   ├── auth/              # Authentication tests
│   │   └── login.spec.ts
│   ├── student/           # Student flow tests
│   │   └── dashboard.spec.ts
│   ├── teacher/           # Teacher flow tests
│   │   └── dashboard.spec.ts
│   ├── fixtures/          # Test fixtures and data
│   │   └── auth.fixture.ts
│   ├── pages/             # Page Object Models
│   │   ├── LoginPage.ts
│   │   ├── StudentDashboardPage.ts
│   │   └── TeacherDashboardPage.ts
│   └── utils/             # Helper utilities
│       └── helpers.ts
├── playwright.config.ts   # Playwright configuration
└── playwright-report/     # Test reports (generated)
```

### File Naming Convention

- Test files: `*.spec.ts`
- Page Objects: `<PageName>Page.ts`
- Fixtures: `*.fixture.ts`
- Utilities: `helpers.ts`, `constants.ts`

## Running Tests

### Run All Tests

```bash
npm run test:e2e
```

### Run Tests in UI Mode (Recommended for Development)

Interactive mode with visual test runner:

```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode

See the browser while tests run:

```bash
npm run test:e2e:headed
```

### Debug Tests

Step through tests with Playwright Inspector:

```bash
npm run test:e2e:debug
```

### Run Specific Browser

```bash
# Chromium only
npm run test:e2e:chromium

# Firefox only
npm run test:e2e:firefox

# WebKit (Safari) only
npm run test:e2e:webkit
```

### Run Mobile Tests

```bash
npm run test:e2e:mobile
```

### Run Specific Test File

```bash
npx playwright test e2e/auth/login.spec.ts
```

### Run Specific Test

```bash
npx playwright test -g "should login student successfully"
```

### View Test Report

```bash
npm run test:e2e:report
```

## Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/path');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await page.fill('input[name="email"]', 'test@example.com');

    // Act
    await page.click('button[type="submit"]');

    // Assert
    await expect(page).toHaveURL('/dashboard');
  });
});
```

### Using Page Objects

```typescript
import { LoginPage } from '../pages/LoginPage';

test('should login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password');

  await expect(await loginPage.isLoggedIn()).toBe(true);
});
```

### Using Custom Fixtures

```typescript
import { studentTest } from '../fixtures/auth.fixture';

studentTest('should view dashboard', async ({ authenticatedStudent }) => {
  // authenticatedStudent is already logged in as a student
  await expect(authenticatedStudent).toHaveURL(/\/student\/dashboard/);
});
```

### Using Helpers

```typescript
import { waitForToast, generateTestEmail } from '../utils/helpers';

test('should show success message', async ({ page }) => {
  const email = generateTestEmail('student');

  // Perform action
  await page.fill('input[name="email"]', email);
  await page.click('button[type="submit"]');

  // Wait for toast notification
  const toast = await waitForToast(page);
  await expect(toast).toContainText('Success');
});
```

## Best Practices

### 1. Use Data Test IDs

Add `data-testid` attributes to your components for reliable selectors:

```tsx
<button data-testid="submit-button">Submit</button>
```

```typescript
await page.click('[data-testid="submit-button"]');
```

### 2. Use Page Object Models

Encapsulate page interactions in Page Object classes:

```typescript
// LoginPage.ts
export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[name="email"]');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    // ...
  }
}
```

### 3. Use Custom Fixtures for Authentication

Create authenticated contexts for testing protected routes:

```typescript
export const studentTest = base.extend<StudentFixtures>({
  authenticatedStudent: async ({ page }, use) => {
    await loginUser(page, testUsers.student.email, testUsers.student.password);
    await use(page);
  },
});
```

### 4. Isolate Tests

Each test should be independent and not rely on previous tests:

```typescript
test.beforeEach(async ({ page }) => {
  // Reset state before each test
  await clearLocalStorage(page);
  await page.goto('/');
});
```

### 5. Use Auto-Waiting

Playwright auto-waits for elements. Avoid manual waits:

```typescript
// ❌ Bad
await page.waitForTimeout(3000);
await page.click('button');

// ✅ Good
await page.click('button'); // Playwright waits automatically
```

### 6. Handle Network Requests

Mock API responses for predictable tests:

```typescript
await page.route('**/api/classes', (route) => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({ classes: [] }),
  });
});
```

### 7. Test Accessibility

Include accessibility checks in your tests:

```typescript
test('should be accessible', async ({ page }) => {
  // Check ARIA labels
  await expect(page.locator('[role="main"]')).toBeVisible();

  // Test keyboard navigation
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
});
```

### 8. Use Descriptive Test Names

```typescript
// ❌ Bad
test('test 1', async ({ page }) => { ... });

// ✅ Good
test('should display validation error for invalid email', async ({ page }) => { ... });
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        run: npm run test:e2e

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

### Environment Variables

Set environment variables for different test environments:

```bash
# .env.test
PLAYWRIGHT_BASE_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
```

## Debugging

### Visual Debugging

Use UI mode for visual debugging:

```bash
npm run test:e2e:ui
```

### Playwright Inspector

Step through tests:

```bash
npm run test:e2e:debug
```

### Trace Viewer

View detailed traces of test execution:

```bash
npx playwright show-trace trace.zip
```

### Screenshots and Videos

Configure in `playwright.config.ts`:

```typescript
use: {
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
}
```

### Console Logs

Capture browser console logs:

```typescript
page.on('console', (msg) => console.log('BROWSER:', msg.text()));
```

## Test Code Generation

Generate tests by recording your actions:

```bash
npm run test:e2e:codegen
```

This opens a browser and records your interactions as Playwright test code.

## Troubleshooting

### Tests Failing Locally But Passing in CI

- Check for timing issues (use proper waits instead of `setTimeout`)
- Verify environment variables are set correctly
- Check if data dependencies are met

### Flaky Tests

- Use `test.retry()` for retries
- Add proper waits for async operations
- Check for race conditions

### Slow Tests

- Run tests in parallel: `workers: 4` in config
- Use headed mode only when debugging
- Mock API responses to avoid network delays

### Browser Not Launching

- Reinstall browsers: `npx playwright install`
- Check system dependencies: `npx playwright install --with-deps`

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices Guide](https://playwright.dev/docs/best-practices)
- [Test Generator](https://playwright.dev/docs/codegen)
- [Trace Viewer](https://playwright.dev/docs/trace-viewer)
- [VS Code Extension](https://playwright.dev/docs/getting-started-vscode)

## Support

For issues or questions:

1. Check the [Playwright documentation](https://playwright.dev)
2. Review test examples in `e2e/` directory
3. Ask in the team Slack channel
4. Create an issue in the repository

---

**Happy Testing!** 🎭
