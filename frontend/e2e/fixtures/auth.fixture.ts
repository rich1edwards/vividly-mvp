import { test as base, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * Test Fixtures for Authentication
 *
 * Provides reusable authentication states and test data
 */

// Test user data
export const testUsers = {
  student: {
    email: 'test.student@mnps.edu',
    password: 'TestPass123!',
    firstName: 'Test',
    lastName: 'Student',
    role: 'student',
    gradeLevel: 10,
  },
  teacher: {
    email: 'test.teacher@mnps.edu',
    password: 'TeacherPass123!',
    firstName: 'Test',
    lastName: 'Teacher',
    role: 'teacher',
  },
  admin: {
    email: 'test.admin@vividly.com',
    password: 'AdminPass123!',
    firstName: 'Test',
    lastName: 'Admin',
    role: 'admin',
  },
};

/**
 * Helper to login a user
 */
export async function loginUser(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for navigation after login
  await page.waitForURL(/\/(dashboard|student|teacher)/, { timeout: 10000 });
}

/**
 * Helper to register a new user
 */
export async function registerUser(
  page: Page,
  userData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    role: string;
    gradeLevel?: number;
  }
) {
  await page.goto('/register');
  await page.fill('input[name="email"]', userData.email);
  await page.fill('input[name="password"]', userData.password);
  await page.fill('input[name="firstName"]', userData.firstName);
  await page.fill('input[name="lastName"]', userData.lastName);
  await page.selectOption('select[name="role"]', userData.role);

  if (userData.gradeLevel) {
    await page.selectOption('select[name="gradeLevel"]', userData.gradeLevel.toString());
  }

  await page.click('button[type="submit"]');

  // Wait for successful registration
  await page.waitForURL(/\/(dashboard|student|teacher)/, { timeout: 10000 });
}

/**
 * Helper to logout
 */
export async function logout(page: Page) {
  // Click user menu
  await page.click('[data-testid="user-menu"]');
  // Click logout button
  await page.click('[data-testid="logout-button"]');
  // Wait for redirect to login
  await page.waitForURL('/login', { timeout: 5000 });
}

/**
 * Custom fixture that provides authenticated student context
 */
type StudentFixtures = {
  authenticatedStudent: Page;
};

export const studentTest = base.extend<StudentFixtures>({
  authenticatedStudent: async ({ page }, use) => {
    await loginUser(page, testUsers.student.email, testUsers.student.password);
    await use(page);
  },
});

/**
 * Custom fixture that provides authenticated teacher context
 */
type TeacherFixtures = {
  authenticatedTeacher: Page;
};

export const teacherTest = base.extend<TeacherFixtures>({
  authenticatedTeacher: async ({ page }, use) => {
    await loginUser(page, testUsers.teacher.email, testUsers.teacher.password);
    await use(page);
  },
});

export { expect };
