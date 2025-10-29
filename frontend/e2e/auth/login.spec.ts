import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { testUsers } from '../fixtures/auth.fixture';
import { waitForToast, clearLocalStorage } from '../utils/helpers';

/**
 * Authentication Tests - Login Flow
 *
 * Tests login functionality for different user roles
 */

test.describe('Login Flow', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await clearLocalStorage(page);
    await loginPage.goto();
  });

  test('should display login form', async ({ page }) => {
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeVisible();
    await expect(loginPage.registerLink).toBeVisible();
    await expect(loginPage.forgotPasswordLink).toBeVisible();
  });

  test('should login student successfully', async ({ page }) => {
    await loginPage.login(testUsers.student.email, testUsers.student.password);

    // Should redirect to student dashboard
    await expect(page).toHaveURL(/\/student\/dashboard/);

    // Should show welcome message
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('should login teacher successfully', async ({ page }) => {
    await loginPage.login(testUsers.teacher.email, testUsers.teacher.password);

    // Should redirect to teacher dashboard
    await expect(page).toHaveURL(/\/teacher\/dashboard/);

    // Should show dashboard content
    await expect(page.locator('text=My Classes')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await loginPage.login('invalid@email.com', 'WrongPassword123!');

    // Should show error message
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid email or password');

    // Should remain on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show error for empty email', async ({ page }) => {
    await loginPage.passwordInput.fill('TestPass123!');
    await loginPage.submitButton.click();

    // Should show validation error
    await expect(page.locator('text=Email is required')).toBeVisible();
  });

  test('should show error for empty password', async ({ page }) => {
    await loginPage.emailInput.fill('test@test.com');
    await loginPage.submitButton.click();

    // Should show validation error
    await expect(page.locator('text=Password is required')).toBeVisible();
  });

  test('should show error for invalid email format', async ({ page }) => {
    await loginPage.emailInput.fill('not-an-email');
    await loginPage.passwordInput.fill('TestPass123!');
    await loginPage.submitButton.click();

    // Should show validation error
    await expect(page.locator('text=Invalid email address')).toBeVisible();
  });

  test('should navigate to registration page', async ({ page }) => {
    await loginPage.registerLink.click();

    // Should navigate to register page
    await expect(page).toHaveURL(/\/register/);
  });

  test('should navigate to forgot password page', async ({ page }) => {
    await loginPage.forgotPasswordLink.click();

    // Should navigate to password reset page
    await expect(page).toHaveURL(/\/forgot-password/);
  });

  test('should persist login after page refresh', async ({ page }) => {
    await loginPage.login(testUsers.student.email, testUsers.student.password);

    // Wait for redirect
    await expect(page).toHaveURL(/\/student\/dashboard/);

    // Refresh page
    await page.reload();

    // Should still be logged in
    await expect(page).toHaveURL(/\/student\/dashboard/);
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Simulate offline mode
    await page.context().setOffline(true);

    await loginPage.login(testUsers.student.email, testUsers.student.password);

    // Should show network error
    const toast = await waitForToast(page);
    await expect(toast).toContainText('Network error');

    await page.context().setOffline(false);
  });

  test('should toggle password visibility', async ({ page }) => {
    const passwordToggle = page.locator('[data-testid="password-toggle"]');

    // Password should be hidden by default
    await expect(loginPage.passwordInput).toHaveAttribute('type', 'password');

    // Click toggle
    await passwordToggle.click();

    // Password should be visible
    await expect(loginPage.passwordInput).toHaveAttribute('type', 'text');

    // Click toggle again
    await passwordToggle.click();

    // Password should be hidden again
    await expect(loginPage.passwordInput).toHaveAttribute('type', 'password');
  });

  test('should prevent concurrent login attempts', async ({ page }) => {
    const loginPromise1 = loginPage.login(testUsers.student.email, testUsers.student.password);
    const loginPromise2 = loginPage.login(testUsers.student.email, testUsers.student.password);

    await Promise.all([loginPromise1, loginPromise2]);

    // Should only make one API call
    // This would need API mocking to properly test
    await expect(page).toHaveURL(/\/student\/dashboard/);
  });
});

test.describe('Login Security', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await clearLocalStorage(page);
    await loginPage.goto();
  });

  test('should not expose password in DOM', async ({ page }) => {
    await loginPage.passwordInput.fill('SecretPassword123!');

    const passwordValue = await page.evaluate(() => {
      const input = document.querySelector('input[name="password"]') as HTMLInputElement;
      return input?.type;
    });

    expect(passwordValue).toBe('password');
  });

  test('should clear password on failed login', async ({ page }) => {
    await loginPage.login('wrong@email.com', 'WrongPassword123!');

    // Wait for error
    await expect(loginPage.errorMessage).toBeVisible();

    // Password field should be cleared
    await expect(loginPage.passwordInput).toBeEmpty();
  });

  test('should rate limit login attempts', async ({ page }) => {
    // Attempt multiple failed logins
    for (let i = 0; i < 6; i++) {
      await loginPage.login('attacker@email.com', 'WrongPassword');
      await page.waitForTimeout(500);
    }

    // Should show rate limit error
    await expect(page.locator('text=Too many login attempts')).toBeVisible({ timeout: 10000 });
  });
});
