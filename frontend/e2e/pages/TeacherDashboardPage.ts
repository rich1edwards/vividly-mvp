import type { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Teacher Dashboard
 */
export class TeacherDashboardPage {
  readonly page: Page;
  readonly createClassButton: Locator;
  readonly classNameInput: Locator;
  readonly subjectInput: Locator;
  readonly gradeLevelsSelect: Locator;
  readonly classList: Locator;
  readonly studentRoster: Locator;
  readonly addStudentButton: Locator;
  readonly studentRequestButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createClassButton = page.locator('button:has-text("Create Class")');
    this.classNameInput = page.locator('input[name="className"]');
    this.subjectInput = page.locator('input[name="subject"]');
    this.gradeLevelsSelect = page.locator('select[name="gradeLevels"]');
    this.classList = page.locator('[data-testid="class-list"]');
    this.studentRoster = page.locator('[data-testid="student-roster"]');
    this.addStudentButton = page.locator('button:has-text("Add Student")');
    this.studentRequestButton = page.locator('button:has-text("Request Student Account")');
  }

  async goto() {
    await this.page.goto('/teacher/dashboard');
  }

  async createClass(name: string, subject: string, gradeLevels: number[]) {
    await this.createClassButton.click();
    await this.classNameInput.fill(name);
    await this.subjectInput.fill(subject);

    // Select multiple grade levels
    for (const grade of gradeLevels) {
      await this.page.click(`option[value="${grade}"]`, { modifiers: ['Meta'] }); // Cmd/Ctrl for multi-select
    }

    await this.page.click('button[type="submit"]');
  }

  async getClasses() {
    return this.classList.locator('[data-testid="class-card"]').all();
  }

  async viewClassRoster(className: string) {
    await this.page.click(`[data-testid="class-${className}"]`);
    await this.page.click('text=View Roster');
  }

  async getStudentsInRoster() {
    return this.studentRoster.locator('[data-testid="student-row"]').all();
  }

  async requestStudentAccount(email: string, firstName: string, lastName: string, gradeLevel: number) {
    await this.studentRequestButton.click();
    await this.page.fill('input[name="email"]', email);
    await this.page.fill('input[name="firstName"]', firstName);
    await this.page.fill('input[name="lastName"]', lastName);
    await this.page.selectOption('select[name="gradeLevel"]', gradeLevel.toString());
    await this.page.click('button[type="submit"]');
  }

  async getClassCode(className: string) {
    await this.page.click(`[data-testid="class-${className}"]`);
    const classCode = await this.page.locator('[data-testid="class-code"]').textContent();
    return classCode;
  }

  async removeStudentFromClass(studentEmail: string) {
    await this.page.click(`[data-testid="remove-student-${studentEmail}"]`);
    await this.page.click('button:has-text("Confirm")');
  }
}
