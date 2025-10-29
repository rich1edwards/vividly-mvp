import type { Page } from '@playwright/test';

/**
 * Utility helpers for Playwright tests
 */

/**
 * Wait for API call to complete
 */
export async function waitForAPICall(page: Page, urlPattern: string | RegExp) {
  return page.waitForResponse((response) => {
    const url = response.url();
    if (typeof urlPattern === 'string') {
      return url.includes(urlPattern);
    }
    return urlPattern.test(url);
  });
}

/**
 * Mock API response
 */
export async function mockAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  responseData: any,
  status = 200
) {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(responseData),
    });
  });
}

/**
 * Wait for toast notification
 */
export async function waitForToast(page: Page, message?: string) {
  const toast = page.locator('[data-testid="toast"]');
  await toast.waitFor({ state: 'visible', timeout: 5000 });

  if (message) {
    await toast.locator(`text=${message}`).waitFor({ state: 'visible' });
  }

  return toast;
}

/**
 * Fill form field and validate
 */
export async function fillField(page: Page, selector: string, value: string) {
  const field = page.locator(selector);
  await field.fill(value);
  await field.blur(); // Trigger validation
}

/**
 * Take screenshot with timestamp
 */
export async function takeTimestampedScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({
    path: `screenshots/${name}-${timestamp}.png`,
    fullPage: true,
  });
}

/**
 * Wait for loading state to finish
 */
export async function waitForLoadingComplete(page: Page) {
  const loader = page.locator('[data-testid="loading-spinner"], [aria-label="Loading"]');

  // Check if loader exists
  const loaderCount = await loader.count();

  if (loaderCount > 0) {
    await loader.waitFor({ state: 'hidden', timeout: 30000 });
  }
}

/**
 * Scroll element into view
 */
export async function scrollIntoView(page: Page, selector: string) {
  await page.evaluate((sel) => {
    const element = document.querySelector(sel);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, selector);
}

/**
 * Check if element is visible in viewport
 */
export async function isInViewport(page: Page, selector: string): Promise<boolean> {
  return page.evaluate((sel) => {
    const element = document.querySelector(sel);
    if (!element) return false;

    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }, selector);
}

/**
 * Get local storage value
 */
export async function getLocalStorage(page: Page, key: string): Promise<string | null> {
  return page.evaluate((storageKey) => {
    return localStorage.getItem(storageKey);
  }, key);
}

/**
 * Set local storage value
 */
export async function setLocalStorage(page: Page, key: string, value: string) {
  await page.evaluate(
    ({ storageKey, storageValue }) => {
      localStorage.setItem(storageKey, storageValue);
    },
    { storageKey: key, storageValue: value }
  );
}

/**
 * Clear local storage
 */
export async function clearLocalStorage(page: Page) {
  await page.evaluate(() => {
    localStorage.clear();
  });
}

/**
 * Generate random email for testing
 */
export function generateTestEmail(prefix = 'test'): string {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  return `${prefix}.${timestamp}.${random}@test.vividly.com`;
}

/**
 * Generate random class code
 */
export function generateClassCode(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = 'TEST-';
  for (let i = 0; i < 3; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  code += '-';
  for (let i = 0; i < 3; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

/**
 * Wait for navigation and ensure page is loaded
 */
export async function navigateAndWait(page: Page, url: string) {
  await page.goto(url);
  await page.waitForLoadState('networkidle');
  await waitForLoadingComplete(page);
}

/**
 * Assert no console errors
 */
export async function assertNoConsoleErrors(page: Page) {
  const consoleErrors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  return consoleErrors;
}
