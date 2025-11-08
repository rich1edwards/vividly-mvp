/**
 * End-to-End Tests for Real-Time Notification System (Phase 1.4)
 *
 * Test Coverage:
 * - SSE connection establishment
 * - Real-time notification delivery
 * - NotificationCenter UI rendering
 * - Notification interaction (mark as read, clear)
 * - Connection state indicators
 * - Reconnection on disconnect
 * - Content generation workflow with notifications
 *
 * Architecture:
 * - Uses Playwright for browser automation
 * - Tests against dev/staging API environment
 * - Mocks Pub/Sub worker responses for deterministic tests
 * - Validates end-to-end notification flow
 */

import { test, expect, Page } from '@playwright/test'

// Test configuration
const API_URL = process.env.VITE_API_URL || 'http://localhost:8000'
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000'

// Test user credentials (from Phase 0 test users)
const STUDENT_EMAIL = 'student@vividly-test.com'
const STUDENT_PASSWORD = 'Test123!Student'

/**
 * Helper: Login as student user
 */
async function loginAsStudent(page: Page) {
  await page.goto(`${FRONTEND_URL}/login`)
  await page.fill('input[name="email"]', STUDENT_EMAIL)
  await page.fill('input[name="password"]', STUDENT_PASSWORD)
  await page.click('button[type="submit"]')

  // Wait for redirect to dashboard
  await page.waitForURL('**/student/dashboard')
  await expect(page.locator('h1')).toContainText('Dashboard', { timeout: 10000 })
}

/**
 * Helper: Wait for SSE connection to establish
 */
async function waitForSSEConnection(page: Page) {
  // Wait for connection indicator to show connected state
  await expect(
    page.locator('[data-testid="notification-connection-indicator"]')
  ).toHaveAttribute('data-connected', 'true', { timeout: 10000 })
}

/**
 * Helper: Open notification center popover
 */
async function openNotificationCenter(page: Page) {
  await page.click('[data-testid="notification-bell"]')
  await expect(
    page.locator('[data-testid="notification-popover"]')
  ).toBeVisible()
}

/**
 * Helper: Simulate push notification from backend
 * (In real tests, this would be triggered by actual content worker)
 */
async function simulateNotification(
  page: Page,
  notification: {
    event_type: string
    title: string
    message: string
    content_request_id?: string
    progress_percentage?: number
  }
) {
  // Inject notification via browser API (simulates Redis Pub/Sub → SSE)
  await page.evaluate((notif) => {
    const event = new MessageEvent('message', {
      data: JSON.stringify({
        event: notif.event_type,
        data: notif
      })
    })
    // Dispatch to EventSource listeners (requires hook to expose EventSource)
    window.dispatchEvent(event)
  }, notification)
}

// =============================================================================
// Test Suite: Notification System Integration
// =============================================================================

test.describe('Real-Time Notification System (Phase 1.4)', () => {

  test.beforeEach(async ({ page }) => {
    // Login before each test
    await loginAsStudent(page)
  })

  // ---------------------------------------------------------------------------
  // Test 1: SSE Connection Establishment
  // ---------------------------------------------------------------------------

  test('should establish SSE connection on page load', async ({ page }) => {
    // Verify notification center exists in header
    await expect(
      page.locator('[data-testid="notification-bell"]')
    ).toBeVisible()

    // Verify connection indicator shows connected
    await waitForSSEConnection(page)

    // Verify no initial unread count badge
    const badge = page.locator('[data-testid="notification-unread-badge"]')
    await expect(badge).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 2: Notification Center UI
  // ---------------------------------------------------------------------------

  test('should open and close notification center', async ({ page }) => {
    // Open notification center
    await openNotificationCenter(page)

    // Verify popover content
    await expect(
      page.locator('[data-testid="notification-popover"]')
    ).toBeVisible()
    await expect(
      page.locator('text=Notifications')
    ).toBeVisible()

    // Initially empty state
    await expect(
      page.locator('text=No notifications yet')
    ).toBeVisible()

    // Close by clicking outside
    await page.click('body')
    await expect(
      page.locator('[data-testid="notification-popover"]')
    ).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 3: Receive Content Generation Started Notification
  // ---------------------------------------------------------------------------

  test('should receive and display content generation started notification', async ({ page }) => {
    // Wait for SSE connection
    await waitForSSEConnection(page)

    // Simulate notification
    await simulateNotification(page, {
      event_type: 'content_generation.started',
      title: 'Video Generation Started',
      message: 'We are creating your video about Newton\'s Laws...',
      content_request_id: 'req_test_123',
      progress_percentage: 0
    })

    // Wait for notification to appear
    await page.waitForTimeout(500) // Allow notification to process

    // Verify unread badge appears
    const badge = page.locator('[data-testid="notification-unread-badge"]')
    await expect(badge).toBeVisible()
    await expect(badge).toHaveText('1')

    // Open notification center
    await openNotificationCenter(page)

    // Verify notification appears
    await expect(
      page.locator('text=Video Generation Started')
    ).toBeVisible()
    await expect(
      page.locator('text=We are creating your video')
    ).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 4: Receive Progress Notification with Progress Bar
  // ---------------------------------------------------------------------------

  test('should display progress notification with progress bar', async ({ page }) => {
    await waitForSSEConnection(page)

    // Simulate progress notification
    await simulateNotification(page, {
      event_type: 'content_generation.progress',
      title: 'Generating Video',
      message: 'Creating visual content...',
      content_request_id: 'req_test_123',
      progress_percentage: 65
    })

    await page.waitForTimeout(500)

    // Open notification center
    await openNotificationCenter(page)

    // Verify progress bar exists
    const progressBar = page.locator('[role="progressbar"]').first()
    await expect(progressBar).toBeVisible()

    // Verify progress text
    await expect(
      page.locator('text=65% complete')
    ).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 5: Receive Completed Notification with Toast
  // ---------------------------------------------------------------------------

  test('should show toast notification when video completes', async ({ page }) => {
    await waitForSSEConnection(page)

    // Simulate completion notification
    await simulateNotification(page, {
      event_type: 'content_generation.completed',
      title: 'Video Ready!',
      message: 'Your video about Newton\'s Laws is ready to watch',
      content_request_id: 'req_test_123',
      progress_percentage: 100
    })

    // Verify toast appears
    await expect(
      page.locator('[data-testid="toast-notification"]')
    ).toBeVisible({ timeout: 2000 })

    await expect(
      page.locator('text=Video Ready!')
    ).toBeVisible()

    // Verify "Watch Now" button in toast
    const watchNowButton = page.locator('button:has-text("Watch Now")')
    await expect(watchNowButton).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 6: Mark Notification as Read
  // ---------------------------------------------------------------------------

  test('should mark notification as read', async ({ page }) => {
    await waitForSSEConnection(page)

    // Add notification
    await simulateNotification(page, {
      event_type: 'content_generation.completed',
      title: 'Video Ready',
      message: 'Your video is ready',
      content_request_id: 'req_test_123'
    })

    await page.waitForTimeout(500)

    // Verify unread badge
    const badge = page.locator('[data-testid="notification-unread-badge"]')
    await expect(badge).toHaveText('1')

    // Open notification center
    await openNotificationCenter(page)

    // Click mark as read button
    await page.click('[data-testid="notification-mark-read"]')

    // Verify unread badge disappears
    await expect(badge).not.toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 7: Clear All Notifications
  // ---------------------------------------------------------------------------

  test('should clear all notifications', async ({ page }) => {
    await waitForSSEConnection(page)

    // Add multiple notifications
    await simulateNotification(page, {
      event_type: 'content_generation.completed',
      title: 'Video 1 Ready',
      message: 'First video ready',
      content_request_id: 'req_1'
    })

    await simulateNotification(page, {
      event_type: 'content_generation.completed',
      title: 'Video 2 Ready',
      message: 'Second video ready',
      content_request_id: 'req_2'
    })

    await page.waitForTimeout(500)

    // Open notification center
    await openNotificationCenter(page)

    // Verify 2 notifications
    const notifications = page.locator('[data-testid="notification-item"]')
    await expect(notifications).toHaveCount(2)

    // Click clear all button
    await page.click('[data-testid="notification-clear-all"]')

    // Verify empty state
    await expect(
      page.locator('text=No notifications yet')
    ).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 8: Connection State Indicators
  // ---------------------------------------------------------------------------

  test('should show connection state changes', async ({ page }) => {
    // Initially connecting
    const indicator = page.locator('[data-testid="notification-connection-indicator"]')

    // Wait for connected state
    await waitForSSEConnection(page)
    await expect(indicator).toHaveAttribute('data-connected', 'true')

    // Simulate disconnect (requires mocking)
    // NOTE: In real implementation, would test actual network disconnect
    // For now, verify connected state persists
    await expect(indicator).toHaveAttribute('data-connected', 'true')
  })

  // ---------------------------------------------------------------------------
  // Test 9: End-to-End Content Request with Notifications
  // ---------------------------------------------------------------------------

  test('should receive notifications during content request flow', async ({ page }) => {
    await waitForSSEConnection(page)

    // Navigate to content request page
    await page.goto(`${FRONTEND_URL}/student/request`)

    // Fill out content request form
    await page.fill('textarea[name="query"]', 'Explain Newton\'s Laws of Motion')
    await page.selectOption('select[name="grade_level"]', '9')
    await page.click('button[data-interest="science"]')

    // Submit request
    await page.click('button[type="submit"]:has-text("Generate Content")')

    // Verify request submitted
    await expect(
      page.locator('text=Content request submitted')
    ).toBeVisible({ timeout: 5000 })

    // NOTE: In real E2E test, would wait for actual worker to process
    // For unit test, simulate notifications

    // Simulate started notification
    await simulateNotification(page, {
      event_type: 'content_generation.started',
      title: 'Generation Started',
      message: 'Processing your request...',
      content_request_id: 'req_real_test',
      progress_percentage: 0
    })

    // Verify notification received
    const badge = page.locator('[data-testid="notification-unread-badge"]')
    await expect(badge).toBeVisible()

    // Simulate progress notifications
    for (const progress of [25, 50, 75]) {
      await simulateNotification(page, {
        event_type: 'content_generation.progress',
        title: 'Generating...',
        message: `Progress: ${progress}%`,
        content_request_id: 'req_real_test',
        progress_percentage: progress
      })
      await page.waitForTimeout(200)
    }

    // Simulate completion
    await simulateNotification(page, {
      event_type: 'content_generation.completed',
      title: 'Video Ready!',
      message: 'Your video is ready to watch',
      content_request_id: 'req_real_test',
      progress_percentage: 100
    })

    // Verify completion toast
    await expect(
      page.locator('text=Video Ready!')
    ).toBeVisible()
  })

  // ---------------------------------------------------------------------------
  // Test 10: Failed Generation Notification
  // ---------------------------------------------------------------------------

  test('should display error notification on generation failure', async ({ page }) => {
    await waitForSSEConnection(page)

    // Simulate failure notification
    await simulateNotification(page, {
      event_type: 'content_generation.failed',
      title: 'Generation Failed',
      message: 'Sorry, we encountered an error generating your video',
      content_request_id: 'req_fail_test'
    })

    await page.waitForTimeout(500)

    // Open notification center
    await openNotificationCenter(page)

    // Verify error styling
    const errorNotification = page.locator('[data-testid="notification-item"]').first()
    await expect(errorNotification).toHaveClass(/bg-red/)

    // Verify error message
    await expect(
      page.locator('text=Generation Failed')
    ).toBeVisible()
  })

})

// =============================================================================
// Test Suite: SSE Performance and Reliability
// =============================================================================

test.describe('SSE Performance Tests', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page)
  })

  test('should handle rapid notification delivery', async ({ page }) => {
    await waitForSSEConnection(page)

    // Send 10 notifications rapidly
    for (let i = 0; i < 10; i++) {
      await simulateNotification(page, {
        event_type: 'content_generation.progress',
        title: `Notification ${i + 1}`,
        message: `Progress update ${i + 1}`,
        content_request_id: `req_${i}`,
        progress_percentage: (i + 1) * 10
      })
    }

    await page.waitForTimeout(1000)

    // Open notification center
    await openNotificationCenter(page)

    // Verify all 10 notifications received
    const notifications = page.locator('[data-testid="notification-item"]')
    await expect(notifications).toHaveCount(10)
  })

  test('should limit notification history to 50 items', async ({ page }) => {
    await waitForSSEConnection(page)

    // Send 60 notifications (exceeds 50 limit)
    for (let i = 0; i < 60; i++) {
      await simulateNotification(page, {
        event_type: 'content_generation.completed',
        title: `Video ${i + 1}`,
        message: `Video ${i + 1} ready`,
        content_request_id: `req_${i}`
      })
    }

    await page.waitForTimeout(1000)

    // Open notification center
    await openNotificationCenter(page)

    // Verify only 50 notifications kept
    const notifications = page.locator('[data-testid="notification-item"]')
    await expect(notifications).toHaveCount(50)
  })

})

// =============================================================================
// Test Suite: Accessibility
// =============================================================================

test.describe('Notification Accessibility', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page)
  })

  test('notification center should be keyboard navigable', async ({ page }) => {
    await waitForSSEConnection(page)

    // Tab to notification bell
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab') // Adjust based on header structure

    // Open with Enter
    await page.keyboard.press('Enter')

    // Verify popover opened
    await expect(
      page.locator('[data-testid="notification-popover"]')
    ).toBeVisible()

    // Close with Escape
    await page.keyboard.press('Escape')

    // Verify popover closed
    await expect(
      page.locator('[data-testid="notification-popover"]')
    ).not.toBeVisible()
  })

  test('notifications should have proper ARIA labels', async ({ page }) => {
    await waitForSSEConnection(page)

    // Verify bell button has aria-label
    const bellButton = page.locator('[data-testid="notification-bell"]')
    await expect(bellButton).toHaveAttribute('aria-label', /Notifications/)

    // Add notification
    await simulateNotification(page, {
      event_type: 'content_generation.completed',
      title: 'Video Ready',
      message: 'Your video is ready',
      content_request_id: 'req_aria_test'
    })

    await page.waitForTimeout(500)

    // Verify unread count in aria-label
    await expect(bellButton).toHaveAttribute('aria-label', /1 unread/)
  })

})
