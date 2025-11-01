# Vividly MVP - Autonomous Development Master Plan
**Adopting Andrew Ng's Systematic ML Engineering Approach**

**Date**: November 1, 2025
**Author**: Claude Code (Andrew Ng Mode)
**Version**: 1.0
**Status**: Active Development Plan

---

## Executive Summary

Following Andrew Ng's proven methodology from deeplearning.ai and Landing AI, this plan establishes a **data-centric, systematic approach** to completing the Vividly MVP. The focus is on **iterative development**, **measurable progress**, and **autonomous execution through clear, detailed prompts**.

### Current State Assessment (November 1, 2025)

**Infrastructure**: ✅ **100% Complete** (14/14 items)
- Authentication, Rate Limiting, Caching, CDN, Monitoring
- Database schema deployed
- GCP infrastructure via Terraform
- Docker Compose dev environment

**API Endpoints**: 🟡 **Code Complete, Testing Incomplete**
- 23 endpoints implemented (auth, students, teachers)
- **21 backend test files** exist
- **0 frontend test files** exist
- **Testing coverage: <20%** (est.)

**Security**: ✅ **Vulnerabilities Remediated**
- All CVEs fixed (pillow, python-jose, python-multipart)
- Security Testing workflow PASSING
- Deploy to Staging: FAILING (test assertions, not vulnerabilities)

**Critical Gaps Identified**:
1. **Test Coverage**: Only 21 test files, target is ~1350 tests
2. **Frontend Tests**: Zero tests written (0/~400 needed)
3. **CI/CD**: Tests failing, blocking deployment
4. **Seed Data**: Not deployed to dev environment
5. **OER Content**: Not ingested (blocked deployment)
6. **End-to-End Testing**: Not implemented
7. **Documentation**: Exists but not synchronized with code state

---

## Andrew Ng's Principles Applied to Vividly

### 1. **Iterative Development with Fast Feedback Loops**
- Each work session produces **testable, deployable increments**
- CI/CD provides immediate feedback on every commit
- Focus on one component at a time until production-ready

### 2. **Data-Centric Approach**
- High-quality test data is as important as code
- Seed data represents real usage patterns
- Test fixtures mirror production scenarios

### 3. **Systematic Error Analysis**
- When tests fail, analyze root cause systematically
- Document patterns in failures
- Fix categories of issues, not individual bugs

### 4. **Measurable Progress**
- Every task has clear **completion criteria**
- Track metrics: test coverage, passing tests, deployment success rate
- Maintain visible progress indicators

### 5. **Autonomous Execution Through Clear Specifications**
- Each prompt is self-contained and executable
- Prompts include: context, requirements, acceptance criteria, test cases
- Future AI can execute prompts without human intervention

---

## Phase-Based MVP Completion Roadmap

### PHASE 1: Stabilize Foundation (Sprint 0) - **CURRENT PRIORITY**
**Goal**: Get CI/CD passing, establish testing baseline
**Duration**: 3-5 days
**Success Criteria**: All tests passing, deployable to staging

#### **Task 1.1: Fix Failing CI/CD Tests**
**Priority**: P0 (Blocking)
**Status**: In Progress
**Estimated Effort**: 4-8 hours

**Objective**: Resolve all failing test assertions in Deploy to Staging workflow.

**Context**:
- Security Testing workflow: ✅ PASSING
- Deploy to Staging workflow: ❌ FAILING
- Failures are in security test assertions (CORS, CSRF, headers, etc.)
- These are **test expectations**, not actual vulnerabilities

**Approach**:
1. Analyze each failing test systematically
2. Categorize failures by root cause
3. Fix infrastructure/code to meet security best practices
4. Update tests where expectations are incorrect
5. Verify fixes don't introduce regressions

**Acceptance Criteria**:
- [ ] All security tests passing
- [ ] All integration tests passing
- [ ] Deploy to Staging workflow: ✅ SUCCESS
- [ ] Zero failing tests in CI/CD
- [ ] Test execution time < 5 minutes

**Next Autonomous Prompt**:
```
TASK: Fix all failing security test assertions in CI/CD pipeline

CONTEXT:
- Run ID: 18998780832 has detailed failure logs
- 18 security tests are failing (test_api_security.py, test_authentication_security.py)
- Root causes likely: missing middleware, incorrect security headers, CORS misconfiguration

REQUIREMENTS:
1. Read failure logs: gh run view 18998780832 --log-failed
2. Categorize failures by type (CORS, CSRF, headers, rate limiting, etc.)
3. For each category:
   - Analyze root cause
   - Implement fix (middleware, headers, config)
   - Run tests locally to verify
4. Ensure fixes follow security best practices
5. Commit with clear explanation of each fix

ACCEPTANCE CRITERIA:
- All security tests in tests/security/ pass locally
- CI/CD Deploy to Staging workflow passes
- No new test failures introduced
- Security headers present in all responses
- CORS properly configured for allowed origins

TEST LOCALLY:
```bash
cd backend
DATABASE_URL="sqlite:///:memory:" SECRET_KEY=test_secret_key_12345 \
  ALGORITHM=HS256 DEBUG=True CORS_ORIGINS=http://localhost \
  PYTHONPATH=/path/to/backend \
  pytest tests/security/ -v
```

COMMIT MESSAGE TEMPLATE:
```
Fix security test failures in CI/CD pipeline

Resolve [N] failing tests by implementing:
- [List specific fixes]

Changes:
- [File path]: [What changed]

Testing:
- All security tests pass locally
- Deploy to Staging workflow verified

Fixes: #[issue-number] (if applicable)
```
```

---

#### **Task 1.2: Establish Testing Baseline**
**Priority**: P0
**Status**: Not Started
**Estimated Effort**: 6-10 hours

**Objective**: Create comprehensive test coverage baseline and fix broken/missing tests.

**Current State**:
- Backend: 21 test files (insufficient for 415 tests target)
- Frontend: 0 test files (need ~400)
- Coverage: Unknown (likely <20%)
- Test strategy document exists but not implemented

**Approach** (Andrew Ng: Measure before optimizing):
1. Run coverage analysis on existing code
2. Identify critical paths with zero coverage
3. Write tests for high-impact, low-coverage areas first
4. Establish coverage CI gate (>= 70% to merge)

**Acceptance Criteria**:
- [ ] Coverage report generated and tracked
- [ ] Minimum 70% coverage on critical paths (auth, content gen)
- [ ] All existing tests passing
- [ ] CI/CD includes coverage reporting
- [ ] Coverage badge in README

**Next Autonomous Prompt**:
```
TASK: Establish comprehensive testing baseline and coverage tracking

CONTEXT:
- 21 backend test files exist in backend/tests/
- 0 frontend test files exist
- Testing strategy documented in TESTING_STRATEGY.md
- Target: 1350 total tests (1000 unit, 300 integration, 50 E2E)
- Current coverage unknown

REQUIREMENTS:
1. Generate coverage report for backend:
   ```bash
   cd backend
   pytest tests/ -v --cov=app --cov-report=html --cov-report=term --cov-report=xml
   ```

2. Analyze coverage gaps:
   - Identify modules with <50% coverage
   - Prioritize: authentication, content generation, data models
   - Document gaps in TESTING_BASELINE.md

3. Write missing critical tests:
   - Auth: Token generation, validation, expiration, RBAC
   - Students: Profile CRUD, interest management, progress tracking
   - Teachers: Class management, roster operations
   - Content: Request lifecycle, cache operations

4. Configure coverage in CI/CD:
   - Add coverage reporting to GitHub Actions
   - Upload to Codecov (or similar)
   - Set minimum threshold: 70%

5. Create frontend test setup:
   - Install Vitest + React Testing Library
   - Create first component test as template
   - Document testing approach in frontend/README.md

ACCEPTANCE CRITERIA:
- Coverage report shows >= 70% for app/ directory
- All critical user flows have tests
- CI/CD includes coverage gate
- Frontend test infrastructure set up
- TESTING_BASELINE.md documents current state

DELIVERABLES:
1. backend/coverage.xml
2. TESTING_BASELINE.md
3. Updated .github/workflows with coverage
4. frontend/vitest.config.ts
5. frontend/src/__tests__/example.test.tsx (template)
```

---

#### **Task 1.3: Deploy Seed Data to Dev Environment**
**Priority**: P1
**Status**: Not Started
**Estimated Effort**: 2-4 hours

**Objective**: Populate development database with realistic test data.

**Current State**:
- Seed script exists: backend/scripts/seed_database.py
- Database schema deployed to GCP CloudSQL
- Seed data NOT deployed (empty database)

**Approach**:
1. Verify database connectivity from local/Cloud Shell
2. Run seed script against dev database
3. Validate data integrity
4. Document seeding process for staging/prod

**Acceptance Criteria**:
- [ ] Dev database contains all seed data
- [ ] Can log in as test users (student, teacher, admin)
- [ ] Seed script idempotent (can run multiple times safely)
- [ ] Documentation updated with seeding instructions

**Next Autonomous Prompt**:
```
TASK: Deploy seed data to development GCP CloudSQL database

CONTEXT:
- Seed script: backend/scripts/seed_database.py
- Database: vividly-dev (GCP CloudSQL PostgreSQL)
- Script creates: 3 admins, 7 teachers, 35 students, classes, topics

REQUIREMENTS:
1. Get database connection details:
   ```bash
   export CLOUDSDK_CONFIG="/Users/richedwards/.gcloud"
   gcloud sql instances describe vividly-dev-db \
     --project=vividly-dev-rich \
     --format="value(connectionName)"
   ```

2. Connect to database:
   - Option A: Cloud SQL Proxy
   - Option B: Authorized networks (if IP whitelisted)
   - Option C: Cloud Shell

3. Run seed script:
   ```bash
   cd backend
   DATABASE_URL="postgresql://user:pass@host/db" \
     python scripts/seed_database.py
   ```

4. Verify data:
   ```sql
   SELECT COUNT(*) FROM users;  -- Should be 45
   SELECT COUNT(*) FROM classes;  -- Should be ~10
   SELECT email, role FROM users LIMIT 5;
   ```

5. Test authentication:
   - Get API endpoint URL
   - Try logging in as test student
   - Verify JWT token works

ACCEPTANCE CRITERIA:
- seed_database.py runs without errors
- Database contains expected record counts
- Can authenticate as test users
- Idempotent (running twice doesn't create duplicates)
- Document connection method in RUN_MIGRATIONS.md

SAFETY:
- Confirm target is 'dev' environment before running
- Take database backup first:
  ```bash
  gcloud sql backups create \
    --instance=vividly-dev-db \
    --project=vividly-dev-rich
  ```
```

---

### PHASE 2: Content Generation Pipeline (Sprint 1)
**Goal**: End-to-end content generation working
**Duration**: 1-2 weeks
**Success Criteria**: Student can request content and receive generated video

#### **Task 2.1: OER Content Ingestion**
**Priority**: P1
**Status**: Not Started
**Dependencies**: Task 1.3 (database seeded)

**Next Autonomous Prompt**: *(See CONTENT_INGESTION_PROMPT.md)*

#### **Task 2.2: Content Request API Integration**
**Priority**: P1
**Status**: Code complete, needs testing

**Next Autonomous Prompt**: *(See CONTENT_API_TESTING_PROMPT.md)*

---

### PHASE 3: Frontend Development (Sprint 2)
**Goal**: Functional student and teacher UIs
**Duration**: 2-3 weeks

#### **Task 3.1: Student Dashboard**
**Next Autonomous Prompt**: *(See STUDENT_DASHBOARD_PROMPT.md)*

#### **Task 3.2: Teacher Class Management**
**Next Autonomous Prompt**: *(See TEACHER_UI_PROMPT.md)*

---

### PHASE 4: Testing & Quality (Sprint 3)
**Goal**: Production-ready quality
**Duration**: 1-2 weeks

#### **Task 4.1: End-to-End Test Suite**
**Next Autonomous Prompt**: *(See E2E_TESTING_PROMPT.md)*

#### **Task 4.2: Performance Testing**
**Next Autonomous Prompt**: *(See PERFORMANCE_TESTING_PROMPT.md)*

---

### PHASE 5: Deployment & Monitoring (Sprint 4)
**Goal**: Live in production with monitoring
**Duration**: 1 week

#### **Task 5.1: Staging Deployment**
**Next Autonomous Prompt**: *(See STAGING_DEPLOYMENT_PROMPT.md)*

#### **Task 5.2: Production Deployment**
**Next Autonomous Prompt**: *(See PRODUCTION_DEPLOYMENT_PROMPT.md)*

---

## Autonomous Prompt Framework

### Prompt Template Structure

Every autonomous development prompt follows this structure:

```markdown
## TASK: [Clear, action-oriented title]

### CONTEXT
[Why this task matters, current state, dependencies]

### REQUIREMENTS
1. [Specific, testable requirement]
2. [Another requirement]
   - Sub-requirement with example
   - Code snippets where helpful

### ACCEPTANCE CRITERIA
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

### TESTING
```bash
# Commands to verify completion
```

### COMMIT MESSAGE TEMPLATE
```
[Type]: [Brief summary]

[Detailed explanation of changes]

Changes:
- [File]: [What changed]

Testing:
- [How tested]

Fixes: #[issue]
```

### NEXT STEPS
[What to do after this task completes]
```

---

## Progress Tracking Mechanisms

### 1. **Daily Status Updates**
**File**: `DAILY_STATUS.md`
**Format**:
```markdown
## [Date]
**Phase**: [Current phase]
**Sprint**: [Current sprint]

### Completed Today
- [x] Task 1.1.2: Fixed CORS middleware
- [x] Task 1.2.1: Added 45 unit tests for auth

### In Progress
- [ ] Task 1.1.3: Implementing CSRF protection (60% complete)

### Blocked
- None

### Metrics
- Tests Passing: 123/145 (85%)
- Coverage: 72% (target: 70%)
- CI/CD: ✅ All workflows passing
```

### 2. **Test Coverage Dashboard**
**File**: `TEST_COVERAGE_REPORT.md` (auto-generated)

### 3. **Feature Completion Matrix**
**File**: `FEATURE_MATRIX.md`

---

## Documentation Maintenance Strategy

### Living Documents (Updated Continuously)
- `MVP_AUTONOMOUS_DEVELOPMENT_PLAN.md` (this file)
- `DAILY_STATUS.md`
- `TEST_COVERAGE_REPORT.md`
- `FEATURE_MATRIX.md`

### Reference Documents (Updated on Major Changes)
- `ARCHITECTURE.md`
- `API_SPECIFICATION.md`
- `DATABASE_SCHEMA.md`
- `TESTING_STRATEGY.md`

### Prompt Library (Grows Over Time)
Location: `docs/prompts/`

Each completed task's prompt is archived for future reference and reuse.

```
docs/
  prompts/
    phase-1/
      fix-ci-cd-tests.md
      establish-testing-baseline.md
      deploy-seed-data.md
    phase-2/
      oer-content-ingestion.md
      content-api-testing.md
    ...
```

---

## Success Metrics & KPIs

### Technical Health Metrics
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Test Coverage | ~20% | 85% | 🔴 |
| Tests Passing | ~80% | 100% | 🟡 |
| CI/CD Success Rate | 0% | 100% | 🔴 |
| Deploy Frequency | 0/week | 5+/week | 🔴 |
| Build Time | ~3min | <5min | 🟢 |

### Feature Completion
| Phase | Complete | Total | % |
|-------|----------|-------|---|
| Phase 1 (Foundation) | 0 | 3 | 0% |
| Phase 2 (Content Gen) | 0 | 5 | 0% |
| Phase 3 (Frontend) | 0 | 8 | 0% |
| Phase 4 (Testing) | 0 | 4 | 0% |
| Phase 5 (Deploy) | 0 | 2 | 0% |
| **Total** | **0** | **22** | **0%** |

### MVP Readiness Checklist
- [ ] All API endpoints tested (23/23)
- [ ] Frontend pages functional (0/8)
- [ ] End-to-end tests passing (0/50)
- [ ] Seed data deployed
- [ ] OER content ingested
- [ ] Staging deployment successful
- [ ] Performance targets met
- [ ] Security audit passed
- [ ] Documentation complete

---

## Risk Management

### High-Risk Areas
1. **AI Content Quality**: Generated content may not meet educational standards
   - **Mitigation**: Human review process, quality metrics, teacher feedback loop

2. **External API Dependencies**: Vertex AI, Nano Banana, ElevenLabs reliability
   - **Mitigation**: Circuit breakers, fallbacks, caching, monitoring

3. **Database Performance**: Complex queries on student progress
   - **Mitigation**: Indexing strategy, query optimization, caching layer

4. **Test Brittleness**: AI-dependent tests may be flaky
   - **Mitigation**: Mock external APIs, use deterministic test data, retry logic

---

## Continuous Improvement Process

Following Andrew Ng's "Build, Measure, Learn" cycle:

1. **Build**: Implement next task from roadmap
2. **Measure**: Run tests, check coverage, deploy to staging
3. **Learn**: Analyze failures, update prompts, improve process
4. **Iterate**: Apply learnings to next task

**Weekly Retrospective**:
- What went well?
- What slowed us down?
- What should we change?
- Update this plan accordingly

---

## Next Immediate Action

**START HERE** (November 1, 2025):

Execute **Task 1.1: Fix Failing CI/CD Tests** using the autonomous prompt provided above.

**Command to Begin**:
```bash
# Read failure details
gh run view 18998780832 --log-failed > ci-failure-analysis.txt

# Analyze and categorize failures
# Then proceed with fixes following the prompt
```

---

**Document Owner**: Claude Code (Andrew Ng Mode)
**Last Updated**: November 1, 2025
**Next Review**: Daily (during active development)
**Version Control**: Track all changes to this plan in git

---

END OF AUTONOMOUS DEVELOPMENT MASTER PLAN
