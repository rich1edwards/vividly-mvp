# Contributing to Vividly

Thank you for your interest in contributing to Vividly! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Documentation](#documentation)
9. [Issue Tracking](#issue-tracking)

---

## Code of Conduct

### Our Standards

We are committed to providing a welcoming and inclusive environment for all contributors. We expect all participants to:

- **Be respectful**: Treat everyone with respect and consideration
- **Be collaborative**: Work together towards common goals
- **Be constructive**: Provide helpful feedback and be open to receiving it
- **Be professional**: Focus on the work and maintain professional conduct

### Unacceptable Behavior

The following behaviors are unacceptable:
- Harassment, discrimination, or exclusionary behavior
- Personal attacks or insults
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

### Reporting

If you experience or witness unacceptable behavior, please report it to the project maintainers at conduct@vividly.edu.

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

**Required**:
- **Git** (2.30+)
- **Python** (3.11+)
- **Node.js** (18+) and npm
- **Docker** (20+) and Docker Compose
- **Google Cloud SDK** (`gcloud` CLI)

**Optional but Recommended**:
- **PostgreSQL** (15+) for local database development
- **VS Code** with recommended extensions (see `.vscode/extensions.json`)
- **Postman** or similar for API testing

### Initial Setup

1. **Fork the repository**
   ```bash
   # Navigate to https://github.com/rich1edwards/vividly-mvp
   # Click "Fork" button
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/vividly-mvp.git
   cd vividly-mvp
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/rich1edwards/vividly-mvp.git
   git fetch upstream
   ```

4. **Set up development environment**
   ```bash
   # Run the development setup script
   ./scripts/setup-dev-environment.sh
   ```

   This script will:
   - Create Python virtual environment
   - Install Python dependencies
   - Install Node.js dependencies
   - Set up pre-commit hooks
   - Create local `.env` file from template
   - Set up local database (if PostgreSQL installed)

5. **Configure environment variables**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env with your local configuration
   nano .env
   ```

   Required variables:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/vividly_dev
   GOOGLE_CLOUD_PROJECT=vividly-dev-rich
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   JWT_SECRET=your-dev-secret-key
   NANO_BANANA_API_KEY=your-api-key
   ```

6. **Verify setup**
   ```bash
   # Run backend tests
   cd backend
   pytest

   # Run frontend tests
   cd ../frontend
   npm test

   # Start development servers
   docker-compose up
   ```

---

## Development Workflow

### Branch Strategy

We use **Git Flow** branching model:

```
main (production)
  ↑
  └── staging (pre-production)
       ↑
       └── develop (integration)
            ↑
            ├── feature/feature-name
            ├── bugfix/bug-description
            ├── hotfix/critical-fix
            └── docs/documentation-update
```

**Branches**:
- `main`: Production-ready code. Protected, requires PR + approval.
- `staging`: Pre-production testing. Merges from `develop`, deploys to staging environment.
- `develop`: Integration branch. All features merge here first.
- `feature/*`: New features or enhancements
- `bugfix/*`: Bug fixes for issues in `develop`
- `hotfix/*`: Critical fixes for production issues
- `docs/*`: Documentation-only changes

### Creating a Branch

```bash
# Update your local develop branch
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/add-user-preferences

# Work on your changes
git add .
git commit -m "Add user preference storage"

# Push to your fork
git push origin feature/add-user-preferences
```

### Branch Naming Conventions

Format: `type/short-description`

**Types**:
- `feature/` - New features (e.g., `feature/add-bookmarks`)
- `bugfix/` - Bug fixes (e.g., `bugfix/fix-login-timeout`)
- `hotfix/` - Critical production fixes (e.g., `hotfix/security-patch`)
- `docs/` - Documentation updates (e.g., `docs/update-api-spec`)
- `refactor/` - Code refactoring (e.g., `refactor/simplify-auth-logic`)
- `test/` - Test improvements (e.g., `test/add-integration-tests`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

**Guidelines**:
- Use kebab-case (lowercase with hyphens)
- Keep names concise but descriptive
- Reference issue number if applicable: `feature/123-add-bookmarks`

---

## Coding Standards

### Python (Backend)

**Style Guide**: PEP 8 with Black formatter

**Tools**:
- **Formatter**: Black (line length: 100)
- **Linter**: Flake8, pylint
- **Type Checker**: mypy
- **Import Sorter**: isort

**Configuration** (already in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
strict = true
```

**Best Practices**:
```python
# ✓ Good
def calculate_total_watch_time(student_id: str) -> int:
    """
    Calculate total watch time in seconds for a student.

    Args:
        student_id: Unique identifier for the student

    Returns:
        Total watch time in seconds

    Raises:
        ValueError: If student_id is invalid
    """
    if not student_id:
        raise ValueError("student_id cannot be empty")

    history = get_learning_history(student_id)
    return sum(entry.watch_time_seconds for entry in history)


# ✗ Bad
def calc_time(id):  # Missing type hints, unclear name, no docstring
    h = get_history(id)
    return sum([e.time for e in h])  # Unnecessary list comprehension
```

**Naming Conventions**:
- **Classes**: PascalCase (`StudentProfile`, `ContentRequest`)
- **Functions/methods**: snake_case (`get_user_by_id`, `create_content_request`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private**: Leading underscore (`_internal_helper`, `_validate_input`)

**File Organization**:
```python
"""
Module docstring describing purpose.
"""

# Standard library imports
import os
from typing import List, Dict

# Third-party imports
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local imports
from app.models import User, ContentRequest
from app.database import get_db
from app.services import content_service

# Constants
MAX_CONTENT_REQUESTS_PER_HOUR = 10

# Classes
class ContentGenerator:
    """Docstring"""
    pass

# Functions
def generate_content():
    """Docstring"""
    pass
```

### TypeScript/React (Frontend)

**Style Guide**: Airbnb JavaScript Style Guide + TypeScript

**Tools**:
- **Formatter**: Prettier
- **Linter**: ESLint
- **Type Checker**: TypeScript compiler

**Configuration** (already in `eslintrc.json` and `prettier.config.js`):
```json
{
  "extends": [
    "airbnb",
    "airbnb-typescript",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/function-component-definition": ["error", {
      "namedComponents": "arrow-function"
    }]
  }
}
```

**Best Practices**:
```typescript
// ✓ Good
interface ContentRequest {
  topicId: string;
  interestId?: string;
  query?: string;
  style: 'conversational' | 'formal' | 'simple';
}

const ContentRequestForm: React.FC = () => {
  const [request, setRequest] = useState<ContentRequest>({
    topicId: '',
    style: 'conversational',
  });

  const handleSubmit = async () => {
    try {
      await createContentRequest(request);
    } catch (error) {
      console.error('Failed to create request:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
};

// ✗ Bad
const Form = () => {  // Missing type annotations, unclear name
  const [data, setData] = useState({});  // No type

  const submit = () => {  // Missing async, error handling
    createRequest(data);
  };

  return <form onSubmit={submit}></form>;
};
```

**Naming Conventions**:
- **Components**: PascalCase (`StudentDashboard`, `ContentPlayer`)
- **Functions/hooks**: camelCase (`useAuth`, `formatDuration`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`, `MAX_FILE_SIZE`)
- **Interfaces/Types**: PascalCase (`User`, `ContentRequestPayload`)

**Component Organization**:
```typescript
// StudentDashboard.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Types
interface StudentDashboardProps {
  userId: string;
}

// Component
export const StudentDashboard: React.FC<StudentDashboardProps> = ({ userId }) => {
  // State
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardData | null>(null);

  // Hooks
  const navigate = useNavigate();

  // Effects
  useEffect(() => {
    fetchDashboardData();
  }, [userId]);

  // Handlers
  const handleNavigation = (path: string) => {
    navigate(path);
  };

  // Render
  return (
    <div>
      {/* Component JSX */}
    </div>
  );
};
```

### Database (SQL)

**Naming Conventions**:
- **Tables**: Plural, snake_case (`users`, `content_requests`, `learning_history`)
- **Columns**: snake_case (`user_id`, `created_at`, `completion_percentage`)
- **Indexes**: `idx_<table>_<column>` (`idx_users_email`, `idx_content_topic_id`)
- **Foreign Keys**: `fk_<table>_<column>` (`fk_students_org_id`)

**Migration Files**:
```python
# migrations/versions/001_add_bookmarks_table.py
"""Add bookmarks table

Revision ID: 001_add_bookmarks
Revises: None
Create Date: 2024-01-15 10:00:00

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'bookmarks',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('user_id', sa.String(50), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_id', sa.String(50), sa.ForeignKey('generated_content.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_bookmarks_user_id', 'bookmarks', ['user_id'])

def downgrade():
    op.drop_index('idx_bookmarks_user_id')
    op.drop_table('bookmarks')
```

---

## Testing Requirements

### Test Coverage Requirements

- **Unit tests**: Minimum 80% coverage for business logic
- **Integration tests**: All API endpoints must have tests
- **E2E tests**: Critical user flows must have E2E tests

### Backend Testing (Python)

**Framework**: pytest

**Structure**:
```
backend/tests/
├── unit/               # Fast, isolated tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/        # Tests with database, external services
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_content_generation.py
└── conftest.py         # Shared fixtures
```

**Example Test**:
```python
# tests/unit/test_content_service.py
import pytest
from app.services import content_service

def test_create_content_request_valid():
    """Test creating a valid content request."""
    request_data = {
        "topic_id": "topic_phys_mech_newton_3",
        "interest_id": "int_basketball",
        "student_id": "student_123"
    }

    result = content_service.create_content_request(**request_data)

    assert result.status == "processing"
    assert result.topic_id == request_data["topic_id"]
    assert result.request_id is not None

def test_create_content_request_invalid_topic():
    """Test creating request with invalid topic."""
    with pytest.raises(ValueError, match="Invalid topic_id"):
        content_service.create_content_request(
            topic_id="invalid",
            student_id="student_123"
        )

@pytest.mark.integration
def test_content_generation_end_to_end(db_session):
    """Test full content generation flow."""
    # Create request
    request = content_service.create_content_request(
        topic_id="topic_phys_mech_newton_3",
        student_id="student_123"
    )

    # Process request (mock external APIs)
    with patch('app.services.vertex_ai.generate_script'):
        result = content_service.process_content_request(request.request_id)

    assert result.status == "completed"
    assert result.content_id is not None
```

**Running Tests**:
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/ -m integration

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_content_service.py

# Specific test function
pytest tests/unit/test_content_service.py::test_create_content_request_valid
```

### Frontend Testing (TypeScript/React)

**Frameworks**: Vitest (unit), Playwright (E2E)

**Structure**:
```
frontend/tests/
├── unit/                           # Component unit tests
│   ├── components/
│   │   ├── StudentDashboard.test.tsx
│   │   └── ContentPlayer.test.tsx
│   └── hooks/
│       └── useAuth.test.ts
└── e2e/                            # End-to-end tests
    ├── student-flow.spec.ts
    └── teacher-flow.spec.ts
```

**Example Unit Test**:
```typescript
// tests/unit/components/ContentPlayer.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { ContentPlayer } from '@/components/ContentPlayer';

describe('ContentPlayer', () => {
  it('renders video player with content', async () => {
    const mockContent = {
      id: 'content_123',
      videoUrl: 'https://example.com/video.mp4',
      title: 'Newton\'s Third Law'
    };

    render(<ContentPlayer content={mockContent} />);

    expect(screen.getByText("Newton's Third Law")).toBeInTheDocument();
    expect(screen.getByRole('video')).toBeInTheDocument();
  });

  it('tracks video completion', async () => {
    const onComplete = vi.fn();

    render(<ContentPlayer content={mockContent} onComplete={onComplete} />);

    // Simulate video ending
    const video = screen.getByRole('video');
    fireEvent.ended(video);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith('content_123');
    });
  });
});
```

**Example E2E Test**:
```typescript
// tests/e2e/student-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Student Content Request Flow', () => {
  test('student can request and view personalized content', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'student@test.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Navigate to topic browse
    await page.click('text=Browse Topics');
    await expect(page).toHaveURL('/dashboard/browse');

    // Select topic
    await page.click('text=Newton\'s Third Law');

    // Request content
    await page.click('text=Get Personalized Video');
    await page.click('text=Basketball');  // Select interest
    await page.click('button:has-text("Request Video")');

    // Wait for generation
    await expect(page.locator('text=Creating Your Personalized Video')).toBeVisible();
    await expect(page.locator('text=Your video is ready!')).toBeVisible({ timeout: 15000 });

    // Verify video player
    await expect(page.locator('video')).toBeVisible();
  });
});
```

**Running Tests**:
```bash
# Unit tests
npm test

# E2E tests (requires running application)
npm run test:e2e

# E2E headed mode (see browser)
npm run test:e2e:headed

# Coverage
npm run test:coverage
```

---

## Commit Guidelines

### Commit Message Format

We follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies

**Scope** (optional): Component or area affected
- `api`, `auth`, `content`, `ui`, `db`, `ci`, etc.

**Examples**:
```bash
# Feature
git commit -m "feat(content): add bookmark functionality"

# Bug fix
git commit -m "fix(auth): resolve token expiration issue"

# Documentation
git commit -m "docs(api): update content request endpoint specs"

# With body
git commit -m "feat(ui): add dark mode toggle

Added dark mode toggle to user settings.
Theme preference is saved to user profile and persists across sessions.

Closes #123"
```

### Pre-commit Hooks

We use pre-commit hooks to enforce code quality:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black  # Python formatter

  - repo: https://github.com/pre-commit/mirrors-eslint
    hooks:
      - id: eslint  # JavaScript/TypeScript linter

  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit
        language: system
        pass_filenames: false
```

**Setup**:
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Pull Request Process

### Before Creating a PR

1. **Update your branch**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. **Run tests locally**
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

3. **Check code formatting**
   ```bash
   # Backend
   black backend/ && flake8 backend/

   # Frontend
   npm run lint && npm run format
   ```

4. **Update documentation** (if needed)
   - Update relevant .md files
   - Update API specs if endpoints changed
   - Update README if setup changed

### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push origin your-feature-branch
   ```

2. **Open PR on GitHub**
   - Navigate to https://github.com/rich1edwards/vividly-mvp
   - Click "New Pull Request"
   - Select: `base: develop` ← `compare: your-feature-branch`

3. **Fill PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [x] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [x] Unit tests added/updated
   - [x] Integration tests added/updated
   - [ ] E2E tests added (if applicable)

   ## Checklist
   - [x] Code follows style guidelines
   - [x] Self-review completed
   - [x] Documentation updated
   - [x] No new warnings
   - [x] Tests pass locally

   ## Related Issues
   Closes #123

   ## Screenshots (if applicable)
   [Add screenshots for UI changes]
   ```

### PR Review Process

**Reviewers will check**:
- ✓ Code quality and style compliance
- ✓ Test coverage (>80% for new code)
- ✓ No security vulnerabilities
- ✓ Performance implications
- ✓ Documentation completeness

**Review Timeline**:
- Initial review: Within 2 business days
- Follow-up: Within 1 business day after changes

**Approval Requirements**:
- Minimum 1 approval from core maintainer
- All CI checks must pass
- No unresolved conversations

### After Approval

1. **Squash and merge** (preferred for feature branches)
   - GitHub will squash all commits into one
   - Use clear, descriptive merge commit message

2. **Delete branch** after merge

3. **Update local repository**
   ```bash
   git checkout develop
   git pull upstream develop
   git branch -d your-feature-branch
   ```

---

## Documentation

### Required Documentation

When contributing, update documentation as needed:

**Code Documentation**:
- **Docstrings**: All functions, classes, modules
- **Type hints**: All function parameters and returns (Python)
- **Comments**: Complex logic, non-obvious decisions

**User Documentation**:
- **README.md**: If setup process changes
- **API_SPECIFICATION.md**: If API endpoints change
- **FEATURE_SPECIFICATIONS.md**: If new features added

**Developer Documentation**:
- **ARCHITECTURE.md**: If architectural changes
- **DEVELOPMENT_SETUP.md**: If dev environment changes
- **This file (CONTRIBUTING.md)**: If contribution process changes

### Documentation Style

**Markdown**:
- Use ATX-style headers (`#` not underlines)
- Use code blocks with language specifiers
- Use relative links for internal references
- Keep line length reasonable (~100 chars)

**Code Comments**:
```python
# ✓ Good
def calculate_similarity_score(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors.

    Uses numpy for efficient vector operations. Returns score between 0 and 1,
    where 1 indicates identical vectors.

    Args:
        embedding1: First embedding vector (768-dim)
        embedding2: Second embedding vector (768-dim)

    Returns:
        Similarity score (0.0 to 1.0)

    Raises:
        ValueError: If embeddings have different dimensions
    """
    if len(embedding1) != len(embedding2):
        raise ValueError("Embeddings must have same dimensions")

    # Convert to numpy for efficient computation
    v1 = np.array(embedding1)
    v2 = np.array(embedding2)

    # Cosine similarity: dot product / (magnitude1 * magnitude2)
    dot_product = np.dot(v1, v2)
    magnitude = np.linalg.norm(v1) * np.linalg.norm(v2)

    return dot_product / magnitude if magnitude > 0 else 0.0


# ✗ Bad
def calc(e1, e2):  # No docstring, unclear names
    # calculate
    if len(e1) != len(e2):
        raise ValueError("bad")
    return np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
```

---

## Issue Tracking

### Reporting Bugs

**Template**:
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to...
2. Click on...
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: macOS 13.2
- Browser: Chrome 120
- Version: develop branch, commit abc123

## Screenshots
[If applicable]

## Additional Context
Any other relevant information
```

### Feature Requests

**Template**:
```markdown
## Feature Description
Clear description of the feature

## Use Case
Who needs this and why?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

### Labels

Use appropriate labels:
- `bug` - Something isn't working
- `feature` - New feature request
- `enhancement` - Improvement to existing feature
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority:high` - High priority
- `priority:low` - Low priority
- `wontfix` - Will not be worked on

---

## Additional Resources

### Useful Links

- **Documentation**: All .md files in repository root
- **API Specification**: `/API_SPECIFICATION.md`
- **Architecture**: `/ARCHITECTURE.md`
- **Setup Guide**: `/DEVELOPMENT_SETUP.md`

### Getting Help

- **Slack**: #vividly-dev channel (for team members)
- **Email**: dev@vividly.edu
- **GitHub Discussions**: Ask questions, share ideas

### Development Tools

**Recommended VS Code Extensions**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker",
    "github.copilot"
  ]
}
```

---

## Thank You!

Thank you for contributing to Vividly! Your efforts help make personalized STEM education accessible to all students.

If you have questions about contributing, please reach out to the maintainers.

---

**Document Version**: 1.0
**Last Updated**: 2024-01-16
**Maintained By**: Vividly Engineering Team
