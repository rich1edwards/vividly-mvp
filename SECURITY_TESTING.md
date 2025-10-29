# Vividly Security Testing Documentation

## Overview

This document provides comprehensive guidance on the security testing framework for the Vividly platform. Our security testing approach is multi-layered and integrated into the CI/CD pipeline to ensure continuous security validation.

## Table of Contents

- [Security Testing Architecture](#security-testing-architecture)
- [Tools and Technologies](#tools-and-technologies)
- [Running Security Tests Locally](#running-security-tests-locally)
- [Understanding Security Reports](#understanding-security-reports)
- [CI/CD Integration](#cicd-integration)
- [Adding New Security Tests](#adding-new-security-tests)
- [Remediation Guidelines](#remediation-guidelines)
- [Configuration Files](#configuration-files)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Security Testing Architecture

Our security testing framework consists of multiple layers:

### 1. Static Application Security Testing (SAST)
- **Purpose**: Analyze source code for security vulnerabilities without executing it
- **Tools**: Bandit (Python), Semgrep (multi-language), CodeQL (deep analysis)
- **Coverage**: SQL injection, XSS, hardcoded secrets, insecure functions

### 2. Dynamic Application Security Testing (DAST)
- **Purpose**: Test running applications for vulnerabilities
- **Tools**: OWASP ZAP
- **Coverage**: Authentication flaws, session management, security headers, configuration issues

### 3. Dependency Scanning
- **Purpose**: Identify known vulnerabilities in third-party dependencies
- **Tools**: pip-audit (Python), Safety (Python), npm audit (Node.js)
- **Coverage**: CVEs in packages, outdated dependencies, license compliance

### 4. Secret Scanning
- **Purpose**: Detect hardcoded secrets, API keys, credentials
- **Tools**: detect-secrets
- **Coverage**: API keys, passwords, tokens, private keys, connection strings

### 5. Container Security
- **Purpose**: Scan container images and Dockerfiles for vulnerabilities
- **Tools**: Trivy
- **Coverage**: Base image vulnerabilities, Dockerfile misconfigurations

### 6. Infrastructure Security
- **Purpose**: Analyze infrastructure-as-code for security issues
- **Tools**: tfsec
- **Coverage**: Terraform configurations, cloud security best practices

### 7. Custom Security Tests
- **Purpose**: Test application-specific security requirements
- **Tools**: pytest with custom test suites
- **Coverage**: Authentication, authorization, BOLA/IDOR, rate limiting, input validation

## Tools and Technologies

### Bandit (Python SAST)
- **Version**: 1.7.5
- **Configuration**: `backend/.bandit`
- **Command**: `bandit -r app/ -f json -o bandit-report.json`
- **Output**: JSON, SARIF, HTML
- **Severity Levels**: LOW, MEDIUM, HIGH

### Semgrep (Advanced SAST)
- **Version**: 1.45.0
- **Configuration**: Uses `--config=auto` for community rules
- **Command**: `semgrep --config=auto --json app/`
- **Output**: JSON, SARIF
- **Rule Sets**: OWASP Top 10, security best practices

### CodeQL (GitHub Advanced Security)
- **Languages**: Python, JavaScript
- **Configuration**: `.github/workflows/security-testing.yml`
- **Query Pack**: security-extended
- **Integration**: GitHub Security tab

### pip-audit (Python Dependency Scanner)
- **Version**: 2.6.1
- **Command**: `pip-audit --format json`
- **Database**: PyPI Advisory Database
- **Output**: JSON with CVE details

### Safety (Python Security Checker)
- **Version**: 3.0.1
- **Command**: `safety check --json`
- **Database**: Safety DB (commercial database of vulnerabilities)
- **Output**: JSON with vulnerability details

### npm audit (Node.js Dependency Scanner)
- **Built-in**: npm >= 6
- **Command**: `npm audit --json`
- **Database**: npm security advisories
- **Output**: JSON with vulnerability details

### detect-secrets (Secret Scanner)
- **Version**: 1.4.0
- **Command**: `detect-secrets scan --all-files`
- **Output**: JSON baseline file
- **Plugins**: AWS keys, private keys, basic auth, JWT, Slack tokens

### OWASP ZAP (DAST)
- **Version**: Latest via Docker
- **Configuration**: `.zap/rules.tsv`
- **Mode**: Baseline scan (passive)
- **Output**: HTML report
- **Target**: Staging/dev environment

### Trivy (Container Scanner)
- **Version**: Latest
- **Command**: `trivy config <path>`
- **Output**: SARIF, JSON, table
- **Coverage**: OS packages, application dependencies, misconfigurations

### tfsec (Terraform Security Scanner)
- **Version**: Latest
- **Command**: `tfsec terraform/ --format json`
- **Output**: SARIF, JSON
- **Coverage**: AWS, GCP, Azure security best practices

## Running Security Tests Locally

### Quick Start

Run all security tests with a single command:

```bash
./scripts/run-security-tests.sh
```

This script will:
1. Create a virtual environment for security tools
2. Install all required dependencies
3. Run all security scans
4. Generate reports in `security-reports/`
5. Create a summary report

### Running Individual Tests

#### Backend SAST (Bandit)

```bash
cd backend
source venv_security/bin/activate
bandit -r app/ \
  -f json \
  -o ../security-reports/bandit-report.json \
  --severity-level medium \
  --confidence-level medium \
  --exclude tests/
```

#### Advanced SAST (Semgrep)

```bash
cd backend
semgrep --config=auto \
  --json \
  --output=../security-reports/semgrep-report.json \
  app/
```

#### Dependency Scanning (pip-audit)

```bash
cd backend
pip-audit --format json --output ../security-reports/pip-audit-report.json
```

#### Dependency Scanning (Safety)

```bash
cd backend
safety check --json --output ../security-reports/safety-report.json
```

#### Secret Scanning

```bash
detect-secrets scan \
  --all-files \
  --exclude-files 'package-lock\.json$|\.lock$|\.pyc$' \
  > security-reports/secrets-baseline.json
```

#### Custom Security Tests

```bash
cd backend
DATABASE_URL=sqlite:///:memory: \
SECRET_KEY=test_secret_key_12345 \
pytest tests/security/ \
  -v \
  --tb=short \
  --junit-xml=../security-reports/security-tests-junit.xml
```

#### Frontend Dependency Scanning

```bash
cd frontend
npm audit --json > ../security-reports/npm-audit-report.json
```

#### Frontend Security Linting

```bash
cd frontend
npx eslint . --ext .ts,.tsx \
  --format json \
  --output-file ../security-reports/eslint-security-report.json
```

#### Container Security (Trivy)

```bash
# Scan backend Dockerfile
trivy config backend/Dockerfile \
  --format json \
  --output security-reports/trivy-backend-dockerfile.json

# Scan frontend Dockerfile
trivy config frontend/Dockerfile \
  --format json \
  --output security-reports/trivy-frontend-dockerfile.json
```

#### Infrastructure Security (tfsec)

```bash
tfsec terraform/ \
  --format json \
  --out security-reports/tfsec-report.json
```

## Understanding Security Reports

### Report Locations

All security reports are generated in the `security-reports/` directory:

```
security-reports/
├── bandit-report.json          # Python SAST findings
├── bandit-report.html          # Human-readable Bandit report
├── semgrep-report.json         # Advanced SAST findings
├── safety-report.json          # Python dependency vulnerabilities
├── pip-audit-report.json       # Python dependency CVEs
├── npm-audit-report.json       # Node.js dependency vulnerabilities
├── npm-audit-report.txt        # Human-readable npm report
├── eslint-security-report.json # Frontend security issues
├── secrets-baseline.json       # Detected secrets
├── trivy-backend-dockerfile.json   # Backend container issues
├── trivy-frontend-dockerfile.json  # Frontend container issues
├── tfsec-report.json          # Infrastructure security issues
├── security-tests-junit.xml   # Custom security test results
└── security-summary.txt       # Overall summary
```

### Report Formats

#### JSON Reports
Most tools output JSON for machine readability and integration:

```json
{
  "results": [
    {
      "issue_severity": "HIGH",
      "issue_confidence": "HIGH",
      "issue_text": "Possible SQL injection",
      "filename": "app/api/users.py",
      "line_number": 42,
      "test_id": "B608",
      "test_name": "hardcoded_sql_expressions"
    }
  ]
}
```

#### SARIF Reports
Security Analysis Results Interchange Format (SARIF) is used for GitHub Security integration:

- Uploaded to GitHub Security tab
- Provides code scanning alerts
- Tracks issue status over time
- Integrates with pull request checks

### Severity Levels

All tools use consistent severity levels:

- **CRITICAL**: Immediate action required, exploitable vulnerabilities
- **HIGH**: Serious issues that should be addressed soon
- **MEDIUM**: Potential issues that should be reviewed
- **LOW**: Minor issues or best practice violations
- **INFO**: Informational findings, no immediate action needed

### Interpreting Findings

#### False Positives
Not all findings are genuine vulnerabilities:
- Review each finding in context
- Use tool-specific ignore mechanisms
- Document why findings are false positives

#### Prioritization
Focus on:
1. CRITICAL and HIGH severity issues
2. Issues in authentication/authorization code
3. Issues handling user input
4. Issues in production code (not tests)

## CI/CD Integration

### GitHub Actions Workflow

Security tests run automatically on:
- **Push** to `main` or `develop` branches
- **Pull requests** targeting `main` or `develop`
- **Schedule**: Daily at 2 AM UTC
- **Manual trigger**: via `workflow_dispatch`

### Workflow Jobs

```yaml
jobs:
  backend-sast:           # Bandit Python SAST
  semgrep-scan:           # Semgrep advanced SAST
  codeql-analysis:        # CodeQL analysis (Python & JavaScript)
  backend-dependencies:   # pip-audit scanning
  frontend-dependencies:  # npm audit scanning
  secret-scanning:        # detect-secrets
  container-security:     # Trivy scanning
  infrastructure-security: # tfsec Terraform scanning
  custom-security-tests:  # pytest security tests
  dast-scan:             # OWASP ZAP (scheduled only)
  security-summary:      # Generate summary report
```

### Viewing Results

#### GitHub Security Tab
1. Navigate to repository **Security** tab
2. Click **Code scanning**
3. View alerts by severity, tool, and status
4. Click individual alerts for details

#### Workflow Artifacts
1. Navigate to **Actions** tab
2. Select the security testing workflow run
3. Download artifacts (reports)
4. Extract and review JSON/HTML reports

#### Pull Request Comments
Security summary is automatically posted as a PR comment:
> 🔒 Security testing completed. Check the Actions tab for detailed results and artifacts.

### Failing Builds

By default, security tests use `continue-on-error: true` to prevent blocking builds on every finding. To enforce security gates:

1. Remove `continue-on-error: true` from critical jobs
2. Set severity thresholds for blocking
3. Use GitHub branch protection rules

## Adding New Security Tests

### Adding Custom pytest Security Tests

1. Create a new test file in `backend/tests/security/`:

```python
# backend/tests/security/test_new_feature_security.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestNewFeatureSecurity:
    """Test security of new feature."""

    def test_feature_requires_authentication(self):
        """Test that feature requires authentication."""
        response = client.get("/api/v1/new-feature")
        assert response.status_code == 401

    def test_feature_validates_input(self):
        """Test that feature validates input."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "Password123!"}
        )
        token = login_response.json()["access_token"]

        # Test invalid input
        response = client.post(
            "/api/v1/new-feature",
            headers={"Authorization": f"Bearer {token}"},
            json={"invalid": "data"}
        )
        assert response.status_code == 422
```

2. Run the new tests:

```bash
cd backend
DATABASE_URL=sqlite:///:memory: \
SECRET_KEY=test_secret_key_12345 \
pytest tests/security/test_new_feature_security.py -v
```

### Adding Bandit Exclusions

If you have legitimate code that Bandit flags, exclude it in `backend/.bandit`:

```ini
[bandit]
exclude_dirs = /tests/, /migrations/, /scripts/

# Skip specific test IDs
skips = B101,B601
```

### Adding Semgrep Custom Rules

Create custom Semgrep rules in `.semgrep/rules/`:

```yaml
# .semgrep/rules/custom-rules.yaml
rules:
  - id: hardcoded-database-password
    pattern: DATABASE_URL = "postgresql://user:$PASSWORD@..."
    message: Hardcoded database password detected
    severity: ERROR
    languages: [python]
```

Run with custom rules:

```bash
semgrep --config=.semgrep/rules/ app/
```

### Configuring OWASP ZAP Rules

Modify `.zap/rules.tsv` to adjust ZAP scanning behavior:

```tsv
# Rule ID	THRESHOLD	[IGNORE	[COMMENT]]
10202	HIGH	# CSRF Protection
10035	HIGH	# HSTS Header
90022	IGNORE	# Application Error Disclosure - Expected in dev
```

## Remediation Guidelines

### Common Vulnerabilities and Fixes

#### SQL Injection

**Issue**: Raw SQL queries with user input
```python
# BAD
query = f"SELECT * FROM users WHERE id = {user_id}"
```

**Fix**: Use parameterized queries
```python
# GOOD
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

#### XSS (Cross-Site Scripting)

**Issue**: Unescaped user input in templates
```python
# BAD
return f"<div>{user_input}</div>"
```

**Fix**: Use templating engines with auto-escaping
```python
# GOOD
from jinja2 import Template
template = Template("<div>{{ user_input }}</div>")
return template.render(user_input=user_input)
```

#### Hardcoded Secrets

**Issue**: Secrets in source code
```python
# BAD
API_KEY = "sk_live_1234567890abcdef"
```

**Fix**: Use environment variables
```python
# GOOD
import os
API_KEY = os.getenv("API_KEY")
```

#### Insecure Password Hashing

**Issue**: Weak hashing algorithms
```python
# BAD
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
```

**Fix**: Use bcrypt or argon2
```python
# GOOD
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash(password)
```

#### Missing Authentication

**Issue**: Endpoints without authentication
```python
# BAD
@app.get("/api/v1/user/data")
def get_user_data():
    return user_data
```

**Fix**: Require authentication
```python
# GOOD
from app.core.deps import get_current_user

@app.get("/api/v1/user/data")
def get_user_data(current_user: User = Depends(get_current_user)):
    return current_user.data
```

#### Broken Object Level Authorization (BOLA)

**Issue**: No ownership verification
```python
# BAD
@app.get("/api/v1/documents/{doc_id}")
def get_document(doc_id: str):
    return db.get_document(doc_id)
```

**Fix**: Verify ownership
```python
# GOOD
@app.get("/api/v1/documents/{doc_id}")
def get_document(doc_id: str, current_user: User = Depends(get_current_user)):
    document = db.get_document(doc_id)
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return document
```

#### Missing Rate Limiting

**Issue**: No rate limiting on endpoints
```python
# BAD
@app.post("/api/v1/auth/login")
def login(credentials: LoginRequest):
    return authenticate(credentials)
```

**Fix**: Add rate limiting
```python
# GOOD
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
def login(request: Request, credentials: LoginRequest):
    return authenticate(credentials)
```

### Dependency Vulnerabilities

When dependency scanners find vulnerabilities:

1. **Check if actively exploited**: Review CVE details
2. **Assess impact**: Does it affect your usage?
3. **Update dependency**: `pip install --upgrade <package>`
4. **Test after update**: Ensure no breaking changes
5. **Document if cannot fix**: Add to known issues

Example workflow:

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Regenerate requirements
pip freeze > requirements.txt

# Run tests
pytest tests/

# Re-run security scan
pip-audit
```

## Configuration Files

### backend/.bandit

Configures Bandit SAST scanner:

```ini
[bandit]
targets = app/
exclude_dirs = /tests/, /venv/, /migrations/
severity = MEDIUM
confidence = MEDIUM
format = json
output = security-reports/bandit-report.json
```

### backend/requirements-security.txt

Security testing dependencies:

```txt
bandit==1.7.5
safety==3.0.1
semgrep==1.45.0
pip-audit==2.6.1
detect-secrets==1.4.0
owasp-zap-api-python==0.3.0
pytest-security==0.1.1
```

Install with:

```bash
pip install -r requirements-security.txt
```

### .zap/rules.tsv

OWASP ZAP scanning rules:

```tsv
# Rule ID	THRESHOLD
10020	HIGH	# X-Frame-Options
10021	HIGH	# X-Content-Type-Options
10035	HIGH	# HSTS
10202	HIGH	# CSRF
```

### .github/workflows/security-testing.yml

CI/CD security pipeline configuration. Key sections:

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:
```

## Best Practices

### 1. Shift Left Security

- Run security tests early in development
- Integrate security into IDE (e.g., Semgrep extension)
- Review security findings before committing

### 2. Defense in Depth

- Use multiple security layers
- Don't rely on a single security control
- Validate input at every layer

### 3. Principle of Least Privilege

- Grant minimum necessary permissions
- Use role-based access control (RBAC)
- Regularly audit permissions

### 4. Secure by Default

- Enable security features by default
- Require explicit opt-out for insecure options
- Use secure defaults in configurations

### 5. Regular Updates

- Keep dependencies up to date
- Subscribe to security advisories
- Automate dependency updates (e.g., Dependabot)

### 6. Security Training

- Train developers on secure coding
- Conduct security code reviews
- Share security findings and lessons

### 7. Incident Response

- Have a security incident response plan
- Define escalation procedures
- Document and learn from incidents

### 8. Security Metrics

Track and monitor:
- Number of vulnerabilities by severity
- Time to remediation
- Security test coverage
- Dependency update frequency

## Troubleshooting

### Issue: Bandit Not Found

**Error**: `bandit: command not found`

**Solution**:
```bash
cd backend
python3 -m venv venv_security
source venv_security/bin/activate
pip install -r requirements-security.txt
```

### Issue: Too Many False Positives

**Error**: Bandit or Semgrep reporting many false positives

**Solution**:
1. Review findings carefully
2. Add exclusions to `.bandit` or `.semgrep/ignore.yaml`
3. Use `# nosec` comments sparingly:
   ```python
   password = get_password()  # nosec B105 - Not a hardcoded password
   ```

### Issue: OWASP ZAP Scan Timeout

**Error**: ZAP scan times out or takes too long

**Solution**:
1. Ensure target URL is accessible
2. Reduce scan scope in `.zap/rules.tsv`
3. Use ZAP API for more control
4. Run ZAP against staging environment

### Issue: GitHub Actions Permission Denied

**Error**: `Error: Resource not accessible by integration`

**Solution**: Ensure workflow has correct permissions:
```yaml
permissions:
  contents: read
  security-events: write
  issues: write
  pull-requests: write
```

### Issue: Security Tests Failing in CI but Pass Locally

**Possible Causes**:
1. Environment variable differences
2. Different Python/Node versions
3. Cached dependencies

**Solution**:
```bash
# Clear caches
rm -rf ~/.cache/pip
rm -rf node_modules

# Reinstall dependencies
pip install --no-cache-dir -r requirements.txt
npm ci

# Run tests
pytest tests/security/ -v
```

### Issue: detect-secrets Finding Too Many Secrets

**Error**: detect-secrets reports many false positives

**Solution**: Create `.secrets.baseline`:
```bash
detect-secrets scan --baseline .secrets.baseline

# Audit findings
detect-secrets audit .secrets.baseline

# Update baseline
detect-secrets scan --baseline .secrets.baseline --exclude-files '\.lock$'
```

### Issue: Trivy Container Scan Errors

**Error**: Trivy cannot scan Dockerfiles

**Solution**:
```bash
# Update Trivy
brew upgrade aquasecurity/trivy/trivy

# Use correct scan type
trivy config Dockerfile  # For Dockerfile misconfigurations
trivy image my-image     # For built image vulnerabilities
```

## Additional Resources

### Documentation
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Semgrep Rules](https://semgrep.dev/explore)
- [GitHub Advanced Security](https://docs.github.com/en/code-security)

### Tools
- [OWASP ZAP](https://www.zaproxy.org/)
- [Trivy](https://aquasecurity.github.io/trivy/)
- [tfsec](https://aquasecurity.github.io/tfsec/)
- [detect-secrets](https://github.com/Yelp/detect-secrets)

### Training
- [OWASP WebGoat](https://owasp.org/www-project-webgoat/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [Secure Code Warrior](https://www.securecodewarrior.com/)

### Community
- [OWASP Slack](https://owasp.org/slack/invite)
- [r/netsec](https://www.reddit.com/r/netsec/)
- [Security Stack Exchange](https://security.stackexchange.com/)

## Contact

For security issues or questions:
- **Security Team**: security@vividly.com
- **Bug Bounty**: See `SECURITY.md`
- **Internal**: #security Slack channel

---

**Last Updated**: 2025-10-28
**Maintained By**: Vividly Security Team
**Version**: 1.0.0
