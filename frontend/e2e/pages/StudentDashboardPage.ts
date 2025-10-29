import type { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Student Dashboard
 */
export class StudentDashboardPage {
  readonly page: Page;
  readonly welcomeMessage: Locator;
  readonly interestsSection: Locator;
  readonly progressSection: Locator;
  readonly classesSection: Locator;
  readonly joinClassButton: Locator;
  readonly classCodeInput: Locator;
  readonly videoPlayer: Locator;
  readonly topicList: Locator;

  constructor(page: Page) {
    this.page = page;
    this.welcomeMessage = page.locator('[data-testid="welcome-message"]');
    this.interestsSection = page.locator('[data-testid="interests-section"]');
    this.progressSection = page.locator('[data-testid="progress-section"]');
    this.classesSection = page.locator('[data-testid="classes-section"]');
    this.joinClassButton = page.locator('button:has-text("Join Class")');
    this.classCodeInput = page.locator('input[name="classCode"]');
    this.videoPlayer = page.locator('[data-testid="video-player"]');
    this.topicList = page.locator('[data-testid="topic-list"]');
  }

  async goto() {
    await this.page.goto('/student/dashboard');
  }

  async getWelcomeText() {
    return this.welcomeMessage.textContent();
  }

  async selectInterest(interestName: string) {
    await this.page.click(`[data-testid="interest-${interestName}"]`);
  }

  async joinClass(classCode: string) {
    await this.joinClassButton.click();
    await this.classCodeInput.fill(classCode);
    await this.page.click('button[type="submit"]');
  }

  async getEnrolledClasses() {
    return this.classesSection.locator('[data-testid="class-card"]').all();
  }

  async viewTopic(topicName: string) {
    await this.page.click(`[data-testid="topic-${topicName}"]`);
  }

  async getProgressPercentage() {
    const progressText = await this.progressSection.locator('[data-testid="progress-value"]').textContent();
    return parseInt(progressText || '0');
  }
}
