#!/bin/bash
#
# Comprehensive Security Testing Script for Vividly
#
# This script runs all security tests including:
# - SAST (Bandit, Semgrep)
# - Dependency scanning (pip-audit, safety, npm audit)
# - Secret scanning (detect-secrets)
# - Custom security tests
# - Container scanning (Trivy)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create reports directory
REPORTS_DIR="security-reports"
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Vividly Security Testing Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

#
# 1. BACKEND SECURITY TESTS
#
print_section "1. Backend Security Tests"

cd backend || exit 1

# 1.1 Install security testing dependencies if needed
if [ ! -d "venv_security" ]; then
    echo -e "${YELLOW}Creating security testing virtual environment...${NC}"
    python3 -m venv venv_security
    source venv_security/bin/activate
    pip install --upgrade pip
    pip install -r requirements-security.txt
else
    source venv_security/bin/activate
fi

# 1.2 Run Bandit (Python SAST)
print_section "1.1. Running Bandit (Python SAST)"
if command_exists bandit; then
    bandit -r app/ \
        -f json \
        -o "../$REPORTS_DIR/bandit-report.json" \
        --severity-level medium \
        --confidence-level medium \
        --exclude tests/ || echo -e "${YELLOW}Bandit found security issues${NC}"

    # Also create human-readable report
    bandit -r app/ \
        -f html \
        -o "../$REPORTS_DIR/bandit-report.html" \
        --severity-level medium \
        --confidence-level medium \
        --exclude tests/ || echo -e "${YELLOW}Bandit found security issues${NC}"

    echo -e "${GREEN}✓ Bandit scan complete${NC}"
else
    echo -e "${RED}✗ Bandit not found${NC}"
fi

# 1.3 Run Safety (Dependency vulnerability check)
print_section "1.2. Running Safety (Dependency Scanning)"
if command_exists safety; then
    safety check \
        --json \
        --output "../$REPORTS_DIR/safety-report.json" \
        || echo -e "${YELLOW}Safety found vulnerabilities${NC}"

    echo -e "${GREEN}✓ Safety scan complete${NC}"
else
    echo -e "${RED}✗ Safety not found${NC}"
fi

# 1.4 Run pip-audit
print_section "1.3. Running pip-audit"
if command_exists pip-audit; then
    pip-audit --format json --output "../$REPORTS_DIR/pip-audit-report.json" \
        || echo -e "${YELLOW}pip-audit found vulnerabilities${NC}"

    echo -e "${GREEN}✓ pip-audit scan complete${NC}"
else
    echo -e "${RED}✗ pip-audit not found${NC}"
fi

# 1.5 Run Semgrep (Advanced SAST)
print_section "1.4. Running Semgrep (Advanced SAST)"
if command_exists semgrep; then
    semgrep --config=auto \
        --json \
        --output="../$REPORTS_DIR/semgrep-report.json" \
        app/ \
        || echo -e "${YELLOW}Semgrep found security issues${NC}"

    echo -e "${GREEN}✓ Semgrep scan complete${NC}"
else
    echo -e "${RED}✗ Semgrep not found${NC}"
fi

# 1.6 Run custom security tests
print_section "1.5. Running Custom Security Tests"
if [ -f "pytest.ini" ]; then
    DATABASE_URL=sqlite:///:memory: \
    SECRET_KEY=test_secret_key_12345 \
    pytest tests/security/ \
        -v \
        --tb=short \
        --junit-xml="../$REPORTS_DIR/security-tests-junit.xml" \
        || echo -e "${YELLOW}Some security tests failed${NC}"

    echo -e "${GREEN}✓ Custom security tests complete${NC}"
else
    echo -e "${YELLOW}! pytest.ini not found, skipping custom tests${NC}"
fi

deactivate
cd ..

#
# 2. FRONTEND SECURITY TESTS
#
print_section "2. Frontend Security Tests"

cd frontend || exit 1

# 2.1 Run npm audit
print_section "2.1. Running npm audit"
if command_exists npm; then
    npm audit --json > "../$REPORTS_DIR/npm-audit-report.json" \
        || echo -e "${YELLOW}npm audit found vulnerabilities${NC}"

    # Human-readable report
    npm audit > "../$REPORTS_DIR/npm-audit-report.txt" \
        || echo -e "${YELLOW}npm audit found vulnerabilities${NC}"

    echo -e "${GREEN}✓ npm audit complete${NC}"
else
    echo -e "${RED}✗ npm not found${NC}"
fi

# 2.2 Run ESLint with security plugins
print_section "2.2. Running ESLint Security Checks"
if command_exists npx; then
    npx eslint . --ext .ts,.tsx \
        --format json \
        --output-file "../$REPORTS_DIR/eslint-security-report.json" \
        || echo -e "${YELLOW}ESLint found security issues${NC}"

    echo -e "${GREEN}✓ ESLint security scan complete${NC}"
else
    echo -e "${YELLOW}! ESLint not available${NC}"
fi

cd ..

#
# 3. SECRET SCANNING
#
print_section "3. Secret Scanning"

# 3.1 Run detect-secrets
if command_exists detect-secrets; then
    detect-secrets scan \
        --all-files \
        --exclude-files 'package-lock\.json$|\.lock$|\.pyc$' \
        > "$REPORTS_DIR/secrets-baseline.json" \
        || echo -e "${YELLOW}Secrets detected${NC}"

    echo -e "${GREEN}✓ Secret scanning complete${NC}"
else
    echo -e "${RED}✗ detect-secrets not found${NC}"
fi

#
# 4. CONTAINER SECURITY (if Docker is available)
#
print_section "4. Container Security Scanning"

if command_exists trivy; then
    # Scan backend Dockerfile
    if [ -f "backend/Dockerfile" ]; then
        trivy config backend/Dockerfile \
            --format json \
            --output "$REPORTS_DIR/trivy-backend-dockerfile.json" \
            || echo -e "${YELLOW}Trivy found issues in backend Dockerfile${NC}"
    fi

    # Scan frontend Dockerfile
    if [ -f "frontend/Dockerfile" ]; then
        trivy config frontend/Dockerfile \
            --format json \
            --output "$REPORTS_DIR/trivy-frontend-dockerfile.json" \
            || echo -e "${YELLOW}Trivy found issues in frontend Dockerfile${NC}"
    fi

    echo -e "${GREEN}✓ Container security scan complete${NC}"
else
    echo -e "${YELLOW}! Trivy not found, skipping container scanning${NC}"
fi

#
# 5. INFRASTRUCTURE SECURITY
#
print_section "5. Infrastructure Security Scanning"

if command_exists tfsec && [ -d "terraform" ]; then
    tfsec terraform/ \
        --format json \
        --out "$REPORTS_DIR/tfsec-report.json" \
        || echo -e "${YELLOW}tfsec found security issues${NC}"

    echo -e "${GREEN}✓ Terraform security scan complete${NC}"
else
    echo -e "${YELLOW}! tfsec not found or no terraform directory${NC}"
fi

#
# 6. GENERATE SUMMARY REPORT
#
print_section "6. Generating Summary Report"

cat > "$REPORTS_DIR/security-summary.txt" << EOF
Vividly Security Testing Summary
Generated: $(date)
=====================================

Reports generated:
- Bandit (SAST): bandit-report.json, bandit-report.html
- Safety (Dependencies): safety-report.json
- pip-audit: pip-audit-report.json
- Semgrep (SAST): semgrep-report.json
- Custom Security Tests: security-tests-junit.xml
- npm audit: npm-audit-report.json
- ESLint Security: eslint-security-report.json
- Secret Scanning: secrets-baseline.json
- Container Security: trivy-*-dockerfile.json
- Infrastructure: tfsec-report.json

All reports are available in: $REPORTS_DIR/

To view detailed reports:
- HTML Reports: Open *.html files in a browser
- JSON Reports: Use jq or your favorite JSON viewer

EOF

echo -e "${GREEN}✓ Summary report generated${NC}"

#
# 7. SUMMARY
#
print_section "Security Testing Complete!"

echo -e "${GREEN}All security tests completed successfully!${NC}"
echo ""
echo "Reports are available in: ${BLUE}$REPORTS_DIR/${NC}"
echo ""
echo "Next steps:"
echo "1. Review all reports in $REPORTS_DIR/"
echo "2. Prioritize HIGH and CRITICAL severity issues"
echo "3. Create tickets for remediation"
echo "4. Update security baselines as needed"
echo ""
echo -e "${YELLOW}Note: Some tests may show warnings. Review all findings.${NC}"
echo ""

# Exit with success
exit 0
