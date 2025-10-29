import { test, expect } from '@playwright/test';
import { teacherTest } from '../fixtures/auth.fixture';
import { TeacherDashboardPage } from '../pages/TeacherDashboardPage';
import { waitForLoadingComplete, waitForToast, generateTestEmail } from '../utils/helpers';

/**
 * Teacher Dashboard Tests
 *
 * Tests teacher dashboard functionality including class management,
 * student roster, and account requests
 */

teacherTest.describe('Teacher Dashboard - Basic', () => {
  let dashboardPage: TeacherDashboardPage;

  teacherTest.beforeEach(async ({ authenticatedTeacher }) => {
    dashboardPage = new TeacherDashboardPage(authenticatedTeacher);
    await dashboardPage.goto();
    await waitForLoadingComplete(authenticatedTeacher);
  });

  teacherTest('should display dashboard', async ({ authenticatedTeacher }) => {
    await expect(authenticatedTeacher.locator('h1')).toContainText('Teacher Dashboard');
  });

  teacherTest('should display create class button', async ({ authenticatedTeacher }) => {
    await expect(dashboardPage.createClassButton).toBeVisible();
  });

  teacherTest('should display class list', async ({ authenticatedTeacher }) => {
    await expect(dashboardPage.classList).toBeVisible();
  });
});

teacherTest.describe('Teacher Dashboard - Class Management', () => {
  let dashboardPage: TeacherDashboardPage;

  teacherTest.beforeEach(async ({ authenticatedTeacher }) => {
    dashboardPage = new TeacherDashboardPage(authenticatedTeacher);
    await dashboardPage.goto();
  });

  teacherTest('should create new class', async ({ authenticatedTeacher }) => {
    const className = `Physics 101 - ${Date.now()}`;
    const subject = 'Physics';
    const gradeLevels = [9, 10];

    await dashboardPage.createClass(className, subject, gradeLevels);

    // Should show success message
    const toast = await waitForToast(authenticatedTeacher);
    await expect(toast).toContainText('Class created successfully');

    // Class should appear in list
    await expect(authenticatedTeacher.locator(`text=${className}`)).toBeVisible();
  });

  teacherTest('should generate unique class code', async ({ authenticatedTeacher }) => {
    const className = `Chemistry 101 - ${Date.now()}`;

    await dashboardPage.createClass(className, 'Chemistry', [10, 11]);

    // Get class code
    const classCode = await dashboardPage.getClassCode(className);
    expect(classCode).toMatch(/^[A-Z]{4}-[A-Z0-9]{3}-[A-Z0-9]{3}$/);
  });

  teacherTest('should validate class creation form', async ({ authenticatedTeacher }) => {
    await dashboardPage.createClassButton.click();

    // Try to submit empty form
    await authenticatedTeacher.click('button[type="submit"]');

    // Should show validation errors
    await expect(authenticatedTeacher.locator('text=Class name is required')).toBeVisible();
    await expect(authenticatedTeacher.locator('text=Subject is required')).toBeVisible();
  });

  teacherTest('should view class details', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      await classes[0].click();

      // Should navigate to class details
      await expect(authenticatedTeacher).toHaveURL(/\/teacher\/class\//);
      await expect(authenticatedTeacher.locator('[data-testid="class-details"]')).toBeVisible();
    }
  });

  teacherTest('should update class information', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      await classes[0].click();
      await authenticatedTeacher.click('[data-testid="edit-class"]');

      // Update description
      const newDescription = `Updated description ${Date.now()}`;
      await authenticatedTeacher.fill('textarea[name="description"]', newDescription);
      await authenticatedTeacher.click('button:has-text("Save")');

      // Should show success message
      await expect(authenticatedTeacher.locator('text=Class updated')).toBeVisible();
    }
  });

  teacherTest('should archive class', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      await classes[0].click();
      await authenticatedTeacher.click('[data-testid="archive-class"]');
      await authenticatedTeacher.click('button:has-text("Confirm")');

      // Should show success message
      await expect(authenticatedTeacher.locator('text=Class archived')).toBeVisible();

      // Should redirect to dashboard
      await expect(authenticatedTeacher).toHaveURL(/\/teacher\/dashboard/);
    }
  });
});

teacherTest.describe('Teacher Dashboard - Student Management', () => {
  let dashboardPage: TeacherDashboardPage;

  teacherTest.beforeEach(async ({ authenticatedTeacher }) => {
    dashboardPage = new TeacherDashboardPage(authenticatedTeacher);
    await dashboardPage.goto();
  });

  teacherTest('should view class roster', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      const className = await classes[0].textContent();
      await dashboardPage.viewClassRoster(className || '');

      // Should display student roster
      await expect(dashboardPage.studentRoster).toBeVisible();
    }
  });

  teacherTest('should display student count', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      await classes[0].click();

      const studentCount = authenticatedTeacher.locator('[data-testid="student-count"]');
      await expect(studentCount).toBeVisible();
    }
  });

  teacherTest('should show student progress', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      const className = await classes[0].textContent();
      await dashboardPage.viewClassRoster(className || '');

      const students = await dashboardPage.getStudentsInRoster();

      if (students.length > 0) {
        await students[0].click();

        // Should show student progress details
        await expect(authenticatedTeacher.locator('[data-testid="student-progress"]')).toBeVisible();
      }
    }
  });

  teacherTest('should remove student from class', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      const className = await classes[0].textContent();
      await dashboardPage.viewClassRoster(className || '');

      const students = await dashboardPage.getStudentsInRoster();

      if (students.length > 0) {
        const studentEmail = await students[0].getAttribute('data-student-email');

        if (studentEmail) {
          await dashboardPage.removeStudentFromClass(studentEmail);

          // Should show success message
          await expect(authenticatedTeacher.locator('text=Student removed')).toBeVisible();
        }
      }
    }
  });
});

teacherTest.describe('Teacher Dashboard - Student Account Requests', () => {
  let dashboardPage: TeacherDashboardPage;

  teacherTest.beforeEach(async ({ authenticatedTeacher }) => {
    dashboardPage = new TeacherDashboardPage(authenticatedTeacher);
    await dashboardPage.goto();
  });

  teacherTest('should request single student account', async ({ authenticatedTeacher }) => {
    const email = generateTestEmail('student');
    const firstName = 'John';
    const lastName = 'Doe';
    const gradeLevel = 10;

    await dashboardPage.requestStudentAccount(email, firstName, lastName, gradeLevel);

    // Should show success message
    const toast = await waitForToast(authenticatedTeacher);
    await expect(toast).toContainText('Student account request submitted');
  });

  teacherTest('should validate student account request form', async ({ authenticatedTeacher }) => {
    await dashboardPage.studentRequestButton.click();

    // Try to submit empty form
    await authenticatedTeacher.click('button[type="submit"]');

    // Should show validation errors
    await expect(authenticatedTeacher.locator('text=Email is required')).toBeVisible();
    await expect(authenticatedTeacher.locator('text=First name is required')).toBeVisible();
    await expect(authenticatedTeacher.locator('text=Last name is required')).toBeVisible();
  });

  teacherTest('should bulk request student accounts', async ({ authenticatedTeacher }) => {
    await authenticatedTeacher.click('[data-testid="bulk-request"]');

    // Upload CSV file
    const fileInput = authenticatedTeacher.locator('input[type="file"]');

    // Create test CSV content
    const csvContent = `email,firstName,lastName,gradeLevel
${generateTestEmail()},Student,One,9
${generateTestEmail()},Student,Two,10
${generateTestEmail()},Student,Three,11`;

    // Upload file (this would need actual file handling in real tests)
    await fileInput.setInputFiles({
      name: 'students.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent),
    });

    await authenticatedTeacher.click('button:has-text("Upload")');

    // Should show success message
    await expect(authenticatedTeacher.locator('text=3 student accounts requested')).toBeVisible();
  });

  teacherTest('should limit bulk requests to 50 students', async ({ authenticatedTeacher }) => {
    await authenticatedTeacher.click('[data-testid="bulk-request"]');

    // Try to upload file with >50 students
    let csvContent = 'email,firstName,lastName,gradeLevel\n';
    for (let i = 0; i < 51; i++) {
      csvContent += `${generateTestEmail()},Student,${i},10\n`;
    }

    const fileInput = authenticatedTeacher.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'students.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent),
    });

    await authenticatedTeacher.click('button:has-text("Upload")');

    // Should show error
    await expect(authenticatedTeacher.locator('text=Maximum 50 students per request')).toBeVisible();
  });

  teacherTest('should view pending requests', async ({ authenticatedTeacher }) => {
    await authenticatedTeacher.click('[data-testid="view-requests"]');

    // Should display requests list
    await expect(authenticatedTeacher.locator('[data-testid="requests-list"]')).toBeVisible();
  });

  teacherTest('should filter requests by status', async ({ authenticatedTeacher }) => {
    await authenticatedTeacher.click('[data-testid="view-requests"]');

    // Filter by pending
    await authenticatedTeacher.selectOption('select[name="statusFilter"]', 'pending');

    // Should show only pending requests
    const statusBadges = authenticatedTeacher.locator('[data-testid="request-status"]');
    const count = await statusBadges.count();

    for (let i = 0; i < count; i++) {
      await expect(statusBadges.nth(i)).toContainText('Pending');
    }
  });
});

teacherTest.describe('Teacher Dashboard - Analytics', () => {
  let dashboardPage: TeacherDashboardPage;

  teacherTest.beforeEach(async ({ authenticatedTeacher }) => {
    dashboardPage = new TeacherDashboardPage(authenticatedTeacher);
    await dashboardPage.goto();
  });

  teacherTest('should display class statistics', async ({ authenticatedTeacher }) => {
    const stats = authenticatedTeacher.locator('[data-testid="class-stats"]');
    await expect(stats).toBeVisible();

    // Should show total classes
    await expect(authenticatedTeacher.locator('[data-testid="total-classes"]')).toBeVisible();

    // Should show total students
    await expect(authenticatedTeacher.locator('[data-testid="total-students"]')).toBeVisible();
  });

  teacherTest('should show student engagement metrics', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      await classes[0].click();

      // Should display engagement metrics
      await expect(authenticatedTeacher.locator('[data-testid="avg-completion"]')).toBeVisible();
      await expect(authenticatedTeacher.locator('[data-testid="avg-watch-time"]')).toBeVisible();
    }
  });

  teacherTest('should export class roster', async ({ authenticatedTeacher }) => {
    const classes = await dashboardPage.getClasses();

    if (classes.length > 0) {
      const className = await classes[0].textContent();
      await dashboardPage.viewClassRoster(className || '');

      // Start waiting for download before clicking
      const downloadPromise = authenticatedTeacher.waitForEvent('download');

      await authenticatedTeacher.click('[data-testid="export-roster"]');

      // Wait for download to complete
      const download = await downloadPromise;

      // Verify filename
      expect(download.suggestedFilename()).toMatch(/roster.*\.csv$/);
    }
  });
});
