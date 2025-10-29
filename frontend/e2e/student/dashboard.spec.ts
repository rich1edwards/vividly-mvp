import { test, expect } from '@playwright/test';
import { studentTest } from '../fixtures/auth.fixture';
import { StudentDashboardPage } from '../pages/StudentDashboardPage';
import { waitForLoadingComplete, generateClassCode } from '../utils/helpers';

/**
 * Student Dashboard Tests
 *
 * Tests student dashboard functionality including interests,
 * progress tracking, and class enrollment
 */

studentTest.describe('Student Dashboard - Basic', () => {
  let dashboardPage: StudentDashboardPage;

  studentTest.beforeEach(async ({ authenticatedStudent }) => {
    dashboardPage = new StudentDashboardPage(authenticatedStudent);
    await dashboardPage.goto();
    await waitForLoadingComplete(authenticatedStudent);
  });

  studentTest('should display welcome message', async ({ authenticatedStudent }) => {
    await expect(dashboardPage.welcomeMessage).toBeVisible();
    await expect(dashboardPage.welcomeMessage).toContainText('Welcome');
  });

  studentTest('should display interests section', async ({ authenticatedStudent }) => {
    await expect(dashboardPage.interestsSection).toBeVisible();
  });

  studentTest('should display progress section', async ({ authenticatedStudent }) => {
    await expect(dashboardPage.progressSection).toBeVisible();
  });

  studentTest('should display enrolled classes', async ({ authenticatedStudent }) => {
    await expect(dashboardPage.classesSection).toBeVisible();
  });
});

studentTest.describe('Student Dashboard - Interests', () => {
  let dashboardPage: StudentDashboardPage;

  studentTest.beforeEach(async ({ authenticatedStudent }) => {
    dashboardPage = new StudentDashboardPage(authenticatedStudent);
    await dashboardPage.goto();
  });

  studentTest('should allow selecting interests', async ({ authenticatedStudent }) => {
    // Click on interests section
    await authenticatedStudent.click('[data-testid="edit-interests"]');

    // Select 3 interests
    await dashboardPage.selectInterest('basketball');
    await dashboardPage.selectInterest('coding');
    await dashboardPage.selectInterest('music');

    // Save interests
    await authenticatedStudent.click('button:has-text("Save Interests")');

    // Should show success message
    await expect(authenticatedStudent.locator('text=Interests updated')).toBeVisible();
  });

  studentTest('should enforce 1-5 interest limit', async ({ authenticatedStudent }) => {
    await authenticatedStudent.click('[data-testid="edit-interests"]');

    // Try to select 6 interests
    const interests = ['basketball', 'coding', 'music', 'art', 'science', 'history'];

    for (const interest of interests) {
      await dashboardPage.selectInterest(interest);
    }

    // 6th interest should not be selectable
    await expect(authenticatedStudent.locator('[data-testid="interest-history"][data-selected="true"]')).not.toBeVisible();
  });

  studentTest('should show personalized content based on interests', async ({ authenticatedStudent }) => {
    // Select basketball interest
    await authenticatedStudent.click('[data-testid="edit-interests"]');
    await dashboardPage.selectInterest('basketball');
    await authenticatedStudent.click('button:has-text("Save Interests")');

    // Wait for content to update
    await waitForLoadingComplete(authenticatedStudent);

    // Should show basketball-related topics
    await expect(authenticatedStudent.locator('text=Physics in Basketball')).toBeVisible();
  });
});

studentTest.describe('Student Dashboard - Class Enrollment', () => {
  let dashboardPage: StudentDashboardPage;

  studentTest.beforeEach(async ({ authenticatedStudent }) => {
    dashboardPage = new StudentDashboardPage(authenticatedStudent);
    await dashboardPage.goto();
  });

  studentTest('should join class with valid code', async ({ authenticatedStudent }) => {
    const validClassCode = 'PHYS-ABC-123'; // This should exist in test data

    await dashboardPage.joinClass(validClassCode);

    // Should show success message
    await expect(authenticatedStudent.locator('text=Successfully joined class')).toBeVisible();

    // Class should appear in enrolled classes
    const classes = await dashboardPage.getEnrolledClasses();
    expect(classes.length).toBeGreaterThan(0);
  });

  studentTest('should show error for invalid class code', async ({ authenticatedStudent }) => {
    await dashboardPage.joinClass('INVALID-CODE');

    // Should show error message
    await expect(authenticatedStudent.locator('text=Class not found')).toBeVisible();
  });

  studentTest('should not join same class twice', async ({ authenticatedStudent }) => {
    const classCode = 'PHYS-ABC-123';

    // Join class first time
    await dashboardPage.joinClass(classCode);
    await expect(authenticatedStudent.locator('text=Successfully joined')).toBeVisible();

    // Try to join again
    await dashboardPage.joinClass(classCode);

    // Should show already enrolled error
    await expect(authenticatedStudent.locator('text=Already enrolled')).toBeVisible();
  });

  studentTest('should not join archived class', async ({ authenticatedStudent }) => {
    const archivedClassCode = 'ARCH-OLD-999';

    await dashboardPage.joinClass(archivedClassCode);

    // Should show error
    await expect(authenticatedStudent.locator('text=This class is no longer accepting students')).toBeVisible();
  });
});

studentTest.describe('Student Dashboard - Learning Progress', () => {
  let dashboardPage: StudentDashboardPage;

  studentTest.beforeEach(async ({ authenticatedStudent }) => {
    dashboardPage = new StudentDashboardPage(authenticatedStudent);
    await dashboardPage.goto();
  });

  studentTest('should display progress statistics', async ({ authenticatedStudent }) => {
    const progressPercentage = await dashboardPage.getProgressPercentage();
    expect(progressPercentage).toBeGreaterThanOrEqual(0);
    expect(progressPercentage).toBeLessThanOrEqual(100);
  });

  studentTest('should show learning streak', async ({ authenticatedStudent }) => {
    const streakElement = authenticatedStudent.locator('[data-testid="learning-streak"]');
    await expect(streakElement).toBeVisible();
  });

  studentTest('should display recent activity', async ({ authenticatedStudent }) => {
    const activitySection = authenticatedStudent.locator('[data-testid="recent-activity"]');
    await expect(activitySection).toBeVisible();
  });

  studentTest('should navigate to topic from recent activity', async ({ authenticatedStudent }) => {
    await authenticatedStudent.click('[data-testid="activity-item"]:first-child');

    // Should navigate to topic page
    await expect(authenticatedStudent).toHaveURL(/\/topic\//);
  });
});

studentTest.describe('Student Dashboard - Video Player', () => {
  let dashboardPage: StudentDashboardPage;

  studentTest.beforeEach(async ({ authenticatedStudent }) => {
    dashboardPage = new StudentDashboardPage(authenticatedStudent);
    await dashboardPage.goto();

    // Navigate to a topic with video
    await dashboardPage.viewTopic('newtons-first-law');
  });

  studentTest('should load and play video', async ({ authenticatedStudent }) => {
    await expect(dashboardPage.videoPlayer).toBeVisible();

    // Click play button
    await authenticatedStudent.click('[data-testid="play-button"]');

    // Video should be playing
    const isPlaying = await authenticatedStudent.evaluate(() => {
      const video = document.querySelector('video') as HTMLVideoElement;
      return !video?.paused;
    });

    expect(isPlaying).toBe(true);
  });

  studentTest('should track watch progress', async ({ authenticatedStudent }) => {
    await authenticatedStudent.click('[data-testid="play-button"]');

    // Wait for some video playback
    await authenticatedStudent.waitForTimeout(5000);

    // Pause video
    await authenticatedStudent.click('[data-testid="pause-button"]');

    // Progress should be saved
    const progressBar = authenticatedStudent.locator('[data-testid="video-progress"]');
    const progress = await progressBar.getAttribute('value');
    expect(parseInt(progress || '0')).toBeGreaterThan(0);
  });

  studentTest('should resume from last position', async ({ authenticatedStudent }) => {
    // Play video for a bit
    await authenticatedStudent.click('[data-testid="play-button"]');
    await authenticatedStudent.waitForTimeout(3000);

    // Navigate away
    await dashboardPage.goto();

    // Go back to video
    await dashboardPage.viewTopic('newtons-first-law');

    // Video should resume from last position
    const currentTime = await authenticatedStudent.evaluate(() => {
      const video = document.querySelector('video') as HTMLVideoElement;
      return video?.currentTime;
    });

    expect(currentTime).toBeGreaterThan(0);
  });

  studentTest('should support fullscreen mode', async ({ authenticatedStudent }) => {
    await authenticatedStudent.click('[data-testid="fullscreen-button"]');

    // Should enter fullscreen
    const isFullscreen = await authenticatedStudent.evaluate(() => {
      return document.fullscreenElement !== null;
    });

    expect(isFullscreen).toBe(true);
  });
});

studentTest.describe('Student Dashboard - Accessibility', () => {
  let dashboardPage: StudentDashboardPage;

  studentTest.beforeEach(async ({ authenticatedStudent }) => {
    dashboardPage = new StudentDashboardPage(authenticatedStudent);
    await dashboardPage.goto();
  });

  studentTest('should be keyboard navigable', async ({ authenticatedStudent }) => {
    // Tab through elements
    await authenticatedStudent.keyboard.press('Tab');
    await authenticatedStudent.keyboard.press('Tab');
    await authenticatedStudent.keyboard.press('Tab');

    // Should be able to activate elements with Enter
    await authenticatedStudent.keyboard.press('Enter');
  });

  studentTest('should have proper ARIA labels', async ({ authenticatedStudent }) => {
    const mainContent = authenticatedStudent.locator('main');
    await expect(mainContent).toHaveAttribute('role', 'main');

    const navigation = authenticatedStudent.locator('nav');
    await expect(navigation).toHaveAttribute('role', 'navigation');
  });

  studentTest('should support screen reader announcements', async ({ authenticatedStudent }) => {
    const liveRegion = authenticatedStudent.locator('[aria-live="polite"]');
    await expect(liveRegion).toBeAttached();
  });
});
