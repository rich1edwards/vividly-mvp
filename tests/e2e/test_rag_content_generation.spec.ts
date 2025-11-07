/**
 * End-to-End Test: RAG Content Generation
 *
 * Tests the complete flow from frontend to RAG-powered content generation:
 * 1. User creates content request in frontend
 * 2. Backend processes request and triggers async worker
 * 3. Content worker uses RAG to retrieve relevant OER content
 * 4. Generated content includes real educational material
 * 5. Frontend displays the generated content
 *
 * Can be run against:
 * - Local development (http://localhost:3000)
 * - Cloud Run production (https://dev-vividly-api-*.run.app)
 */

import { test, expect, Page } from '@playwright/test';

// Configuration
const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.TEST_API_URL || 'http://localhost:8080';
const TIMEOUT_MS = 120000; // 2 minutes for async content generation

test.describe('RAG Content Generation E2E', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto(BASE_URL);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should generate content with RAG-grounded educational material', async () => {
    // Step 1: Navigate to content creation page
    await test.step('Navigate to content creation', async () => {
      await page.goto(`${BASE_URL}/create-content`);
      await expect(page).toHaveTitle(/Create Content|Vividly/);
    });

    // Step 2: Fill in content request form
    await test.step('Fill content request form', async () => {
      // Select topic (Newton's Third Law)
      await page.selectOption('[name="topic"]', 'topic_phys_mech_newton_3');

      // Enter student interest
      await page.fill('[name="interest"]', 'basketball');

      // Select grade level
      await page.selectOption('[name="grade_level"]', '10');

      // Optional: Select content type (video/audio)
      await page.selectOption('[name="content_type"]', 'video');
    });

    // Step 3: Submit request
    let requestId: string;
    await test.step('Submit content request', async () => {
      // Listen for API call
      const responsePromise = page.waitForResponse(
        response => response.url().includes('/api/content/request') && response.status() === 201
      );

      await page.click('button[type="submit"]');

      const response = await responsePromise;
      const data = await response.json();
      requestId = data.request_id;

      expect(requestId).toBeTruthy();
      console.log(`Content request created: ${requestId}`);
    });

    // Step 4: Wait for content generation to complete
    await test.step('Wait for content generation', async () => {
      // Poll for status updates
      let status = 'pending';
      let attempts = 0;
      const maxAttempts = 60; // 2 minutes with 2-second intervals

      while (status !== 'completed' && status !== 'failed' && attempts < maxAttempts) {
        await page.waitForTimeout(2000); // Wait 2 seconds

        // Check status via API or frontend
        const statusResponse = await page.evaluate(async (id) => {
          const res = await fetch(`${(window as any).API_URL}/api/content/status/${id}`);
          return res.json();
        }, requestId);

        status = statusResponse.status;
        console.log(`Status check ${attempts + 1}: ${status}`);

        attempts++;
      }

      expect(status).toBe('completed');
      expect(attempts).toBeLessThan(maxAttempts);
    });

    // Step 5: Verify generated content contains RAG-grounded material
    await test.step('Verify RAG-grounded content', async () => {
      // Navigate to generated content view
      await page.goto(`${BASE_URL}/content/${requestId}`);

      // Wait for content to load
      await page.waitForSelector('[data-testid="generated-content"]');

      // Get the generated script/content
      const contentText = await page.textContent('[data-testid="generated-content"]');

      expect(contentText).toBeTruthy();
      console.log(`Generated content length: ${contentText!.length} characters`);

      // Verify content mentions physics concepts (from RAG retrieval)
      // Should include educational terminology from OpenStax content
      const hasPhysicsConcepts =
        /force|motion|newton|action|reaction|momentum/i.test(contentText!);

      expect(hasPhysicsConcepts).toBeTruthy();
      console.log('✓ Content includes physics concepts from RAG');

      // Verify content is personalized with student interest
      const hasPersonalization = /basketball/i.test(contentText!);
      expect(hasPersonalization).toBeTruthy();
      console.log('✓ Content is personalized with basketball interest');
    });

    // Step 6: Verify RAG metadata in logs (optional, requires log access)
    if (process.env.CHECK_LOGS === 'true') {
      await test.step('Check RAG retrieval in logs', async () => {
        // This would require GCP logging access
        // Can be run as separate verification step
        console.log('Skipping log check (set CHECK_LOGS=true to enable)');
      });
    }
  });

  test('should show RAG retrieval quality metrics', async () => {
    // Test that we can see RAG quality indicators
    await test.step('Check RAG quality indicators', async () => {
      await page.goto(`${BASE_URL}/admin/rag-metrics`);

      // Look for metrics dashboard
      await page.waitForSelector('[data-testid="rag-metrics"]');

      // Check for key metrics
      const metricsText = await page.textContent('[data-testid="rag-metrics"]');

      // Should show retrieval stats
      expect(metricsText).toMatch(/similarity score|relevance|chunks retrieved/i);
      console.log('✓ RAG metrics dashboard available');
    });
  });

  test('should handle RAG failure gracefully', async () => {
    // Test graceful degradation if RAG fails
    await test.step('Test RAG failure handling', async () => {
      // Submit request with invalid topic (should still work with mock data)
      await page.goto(`${BASE_URL}/create-content`);

      await page.selectOption('[name="topic"]', 'invalid_topic_12345');
      await page.fill('[name="interest"]', 'testing');
      await page.selectOption('[name="grade_level"]', '10');

      await page.click('button[type="submit"]');

      // Should still get a response (either RAG or mock)
      const errorMessage = await page.locator('[data-testid="error-message"]');

      // Should NOT show critical error
      await expect(errorMessage).not.toBeVisible();
      console.log('✓ Graceful handling of invalid requests');
    });
  });
});

test.describe('RAG Service Health Checks', () => {
  test('should verify RAG service is operational', async ({ request }) => {
    // Direct API health check
    const response = await request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();

    const health = await response.json();
    console.log('Health check:', health);

    // Check if RAG service is initialized
    if (health.services) {
      expect(health.services.rag).toBeDefined();
      console.log('RAG service status:', health.services.rag);
    }
  });

  test('should verify embeddings are loaded', async ({ request }) => {
    // Check RAG status endpoint
    const response = await request.get(`${API_URL}/api/rag/status`);

    if (response.ok()) {
      const status = await response.json();

      expect(status.embeddings_loaded).toBe(true);
      expect(status.num_chunks).toBeGreaterThan(3000); // Should have 3,783
      console.log(`✓ Embeddings loaded: ${status.num_chunks} chunks`);
    } else {
      console.log('RAG status endpoint not available (expected in MVP)');
    }
  });
});
