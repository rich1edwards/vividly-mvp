#!/usr/bin/env python3
"""
Phase 1.4 Real-Time Notification System - Deployment Readiness Validation

Comprehensive validation script to verify all Phase 1.4 components are ready for deployment.
Runs pre-deployment checks, infrastructure validation, and integration tests.

Usage:
    python3 scripts/validate_phase_1_4_readiness.py --env dev
    python3 scripts/validate_phase_1_4_readiness.py --env dev --skip-infrastructure
    python3 scripts/validate_phase_1_4_readiness.py --env staging --verbose

Environment Variables Required:
    - VIVIDLY_API_URL: Backend API URL (e.g., https://dev-vividly-api-xxx.run.app)
    - REDIS_URL: Redis connection URL (optional, for local testing)
    - ACCESS_TOKEN: Valid JWT token for API testing (optional)

Exit Codes:
    0: All checks passed, ready for deployment
    1: Critical failures, deployment blocked
    2: Warnings present, review required
"""

import sys
import os
import json
import time
import argparse
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import requests


class CheckStatus(Enum):
    """Status of a validation check."""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️  WARN"
    SKIP = "⏭️  SKIP"


@dataclass
class CheckResult:
    """Result of a validation check."""
    name: str
    status: CheckStatus
    message: str
    details: Optional[Dict] = None


class Phase14Validator:
    """Validator for Phase 1.4 Real-Time Notification System."""

    def __init__(self, env: str, api_url: str, verbose: bool = False):
        self.env = env
        self.api_url = api_url.rstrip('/')
        self.verbose = verbose
        self.results: List[CheckResult] = []
        self.access_token: Optional[str] = None

    def print_header(self, title: str):
        """Print section header."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")

    def print_result(self, result: CheckResult):
        """Print check result."""
        print(f"{result.status.value} {result.name}")
        print(f"    {result.message}")
        if self.verbose and result.details:
            print(f"    Details: {json.dumps(result.details, indent=2)}")
        print()

    def add_result(self, name: str, status: CheckStatus, message: str, details: Optional[Dict] = None):
        """Add a check result."""
        result = CheckResult(name, status, message, details)
        self.results.append(result)
        self.print_result(result)

    # =========================================================================
    # Code Structure Validation
    # =========================================================================

    def validate_code_structure(self):
        """Validate that all Phase 1.4 code files exist."""
        self.print_header("1. Code Structure Validation")

        required_files = [
            # Backend
            ("backend/app/services/notification_service.py", "NotificationService implementation"),
            ("backend/app/api/v1/endpoints/notifications.py", "SSE API endpoint"),
            ("backend/app/api/v1/endpoints/notification_monitoring.py", "Monitoring endpoints"),
            ("backend/app/workers/push_worker.py", "Push worker for notifications"),

            # Frontend
            ("frontend/src/hooks/useNotifications.ts", "useNotifications hook"),
            ("frontend/src/components/NotificationCenter.tsx", "NotificationCenter component"),
            ("frontend/src/types/notification.ts", "Notification types"),

            # Tests
            ("frontend/e2e/notifications/notification-flow.spec.ts", "E2E notification tests"),
            ("backend/tests/test_notification_monitoring.py", "Monitoring tests"),

            # Scripts
            ("scripts/run-notification-e2e-tests.sh", "E2E test runner"),

            # CI/CD
            (".github/workflows/e2e-notification-tests.yml", "E2E test workflow"),
        ]

        for file_path, description in required_files:
            full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
            if os.path.exists(full_path):
                # Check file size
                size = os.path.getsize(full_path)
                if size > 100:  # More than 100 bytes
                    self.add_result(
                        f"File: {file_path}",
                        CheckStatus.PASS,
                        f"{description} ({size} bytes)"
                    )
                else:
                    self.add_result(
                        f"File: {file_path}",
                        CheckStatus.WARN,
                        f"{description} exists but is very small ({size} bytes)"
                    )
            else:
                self.add_result(
                    f"File: {file_path}",
                    CheckStatus.FAIL,
                    f"{description} not found"
                )

    # =========================================================================
    # Backend API Validation
    # =========================================================================

    def validate_backend_api(self):
        """Validate backend API is accessible and has Phase 1.4 endpoints."""
        self.print_header("2. Backend API Validation")

        # Check API health
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                self.add_result(
                    "Backend API Health",
                    CheckStatus.PASS,
                    f"API is healthy ({response.status_code})",
                    response.json() if response.headers.get('content-type') == 'application/json' else None
                )
            else:
                self.add_result(
                    "Backend API Health",
                    CheckStatus.FAIL,
                    f"API returned {response.status_code}"
                )
                return
        except Exception as e:
            self.add_result(
                "Backend API Health",
                CheckStatus.FAIL,
                f"Failed to connect to API: {str(e)}"
            )
            return

        # Check notification health endpoint
        try:
            response = requests.get(f"{self.api_url}/api/v1/monitoring/notifications/health", timeout=10)
            if response.status_code in [200, 503]:  # 503 is acceptable (service unavailable but endpoint exists)
                data = response.json() if response.status_code == 200 else response.json().get('detail', {})
                self.add_result(
                    "Notification Health Endpoint",
                    CheckStatus.PASS if response.status_code == 200 else CheckStatus.WARN,
                    f"Endpoint exists ({response.status_code})",
                    data
                )
            else:
                self.add_result(
                    "Notification Health Endpoint",
                    CheckStatus.FAIL,
                    f"Unexpected status code: {response.status_code}"
                )
        except Exception as e:
            self.add_result(
                "Notification Health Endpoint",
                CheckStatus.FAIL,
                f"Failed to check notification health: {str(e)}"
            )

        # Check notification metrics endpoint
        try:
            response = requests.get(f"{self.api_url}/api/v1/monitoring/notifications/metrics", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.add_result(
                    "Notification Metrics Endpoint",
                    CheckStatus.PASS,
                    "Endpoint exists and returns metrics",
                    {
                        "notifications_published": data.get("notifications_published_total", 0),
                        "connections_active": data.get("active_connections_current", 0),
                        "availability_sli": data.get("sli_availability", 0)
                    }
                )
            else:
                self.add_result(
                    "Notification Metrics Endpoint",
                    CheckStatus.WARN,
                    f"Endpoint returned {response.status_code}"
                )
        except Exception as e:
            self.add_result(
                "Notification Metrics Endpoint",
                CheckStatus.WARN,
                f"Failed to check metrics: {str(e)}"
            )

    # =========================================================================
    # Redis/Cloud Memorystore Validation
    # =========================================================================

    def validate_redis_infrastructure(self):
        """Validate Redis/Cloud Memorystore is accessible."""
        self.print_header("3. Redis Infrastructure Validation")

        # Check Redis health via monitoring endpoint
        try:
            response = requests.get(f"{self.api_url}/api/v1/monitoring/notifications/redis/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                redis_connected = data.get("redis_connected", False)
                ping_latency = data.get("ping_latency_ms", 0)

                if redis_connected and ping_latency < 100:
                    self.add_result(
                        "Redis Connectivity",
                        CheckStatus.PASS,
                        f"Redis connected, latency: {ping_latency:.2f}ms",
                        data
                    )
                elif redis_connected:
                    self.add_result(
                        "Redis Connectivity",
                        CheckStatus.WARN,
                        f"Redis connected but high latency: {ping_latency:.2f}ms",
                        data
                    )
                else:
                    self.add_result(
                        "Redis Connectivity",
                        CheckStatus.FAIL,
                        "Redis not connected",
                        data
                    )
            elif response.status_code == 503:
                data = response.json().get('detail', {})
                self.add_result(
                    "Redis Connectivity",
                    CheckStatus.FAIL,
                    "Redis unavailable",
                    data
                )
            else:
                self.add_result(
                    "Redis Connectivity",
                    CheckStatus.FAIL,
                    f"Unexpected status code: {response.status_code}"
                )
        except Exception as e:
            self.add_result(
                "Redis Connectivity",
                CheckStatus.FAIL,
                f"Failed to check Redis health: {str(e)}"
            )

    # =========================================================================
    # Frontend Build Validation
    # =========================================================================

    def validate_frontend_build(self):
        """Validate frontend builds successfully."""
        self.print_header("4. Frontend Build Validation")

        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

        # Check if node_modules exists
        node_modules = os.path.join(frontend_dir, "node_modules")
        if os.path.exists(node_modules):
            self.add_result(
                "Frontend Dependencies",
                CheckStatus.PASS,
                "node_modules directory exists"
            )
        else:
            self.add_result(
                "Frontend Dependencies",
                CheckStatus.WARN,
                "node_modules not found - run 'npm install'"
            )
            return

        # Try to build frontend (skip in CI to save time)
        if not os.getenv("CI"):
            try:
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )

                if result.returncode == 0:
                    self.add_result(
                        "Frontend Build",
                        CheckStatus.PASS,
                        "Frontend builds successfully"
                    )
                else:
                    self.add_result(
                        "Frontend Build",
                        CheckStatus.FAIL,
                        f"Build failed: {result.stderr[:200]}"
                    )
            except subprocess.TimeoutExpired:
                self.add_result(
                    "Frontend Build",
                    CheckStatus.WARN,
                    "Build timeout after 5 minutes"
                )
            except Exception as e:
                self.add_result(
                    "Frontend Build",
                    CheckStatus.WARN,
                    f"Build check failed: {str(e)}"
                )
        else:
            self.add_result(
                "Frontend Build",
                CheckStatus.SKIP,
                "Skipped in CI environment"
            )

    # =========================================================================
    # E2E Test Validation
    # =========================================================================

    def validate_e2e_tests(self):
        """Validate E2E tests are configured correctly."""
        self.print_header("5. E2E Test Validation")

        # Check Playwright config
        playwright_config = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "frontend/playwright.config.ts"
        )
        if os.path.exists(playwright_config):
            self.add_result(
                "Playwright Configuration",
                CheckStatus.PASS,
                "playwright.config.ts exists"
            )
        else:
            self.add_result(
                "Playwright Configuration",
                CheckStatus.FAIL,
                "playwright.config.ts not found"
            )

        # Check E2E test file
        e2e_test = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "frontend/e2e/notifications/notification-flow.spec.ts"
        )
        if os.path.exists(e2e_test):
            # Count test cases
            with open(e2e_test, 'r') as f:
                content = f.read()
                test_count = content.count("test(") + content.count("test.only(")

            self.add_result(
                "E2E Notification Tests",
                CheckStatus.PASS,
                f"Test file exists with {test_count} test cases"
            )
        else:
            self.add_result(
                "E2E Notification Tests",
                CheckStatus.FAIL,
                "notification-flow.spec.ts not found"
            )

    # =========================================================================
    # Monitoring & Observability Validation
    # =========================================================================

    def validate_monitoring(self):
        """Validate monitoring endpoints and alerting."""
        self.print_header("6. Monitoring & Observability Validation")

        # Check monitoring endpoints exist
        monitoring_endpoints = [
            ("/api/v1/monitoring/notifications/health", "Health Check"),
            ("/api/v1/monitoring/notifications/metrics", "Metrics"),
            ("/api/v1/monitoring/notifications/redis/health", "Redis Health"),
        ]

        for endpoint, name in monitoring_endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                if response.status_code in [200, 503]:
                    self.add_result(
                        f"Monitoring: {name}",
                        CheckStatus.PASS,
                        f"Endpoint accessible ({response.status_code})"
                    )
                elif response.status_code == 404:
                    self.add_result(
                        f"Monitoring: {name}",
                        CheckStatus.FAIL,
                        "Endpoint not found (404)"
                    )
                else:
                    self.add_result(
                        f"Monitoring: {name}",
                        CheckStatus.WARN,
                        f"Unexpected status: {response.status_code}"
                    )
            except Exception as e:
                self.add_result(
                    f"Monitoring: {name}",
                    CheckStatus.FAIL,
                    f"Failed to access: {str(e)}"
                )

    # =========================================================================
    # Summary and Exit Code
    # =========================================================================

    def print_summary(self) -> int:
        """Print validation summary and return exit code."""
        self.print_header("Validation Summary")

        # Count results by status
        pass_count = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        fail_count = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warn_count = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        skip_count = sum(1 for r in self.results if r.status == CheckStatus.SKIP)
        total = len(self.results)

        print(f"Total Checks: {total}")
        print(f"  ✅ Passed:  {pass_count}")
        print(f"  ❌ Failed:  {fail_count}")
        print(f"  ⚠️  Warnings: {warn_count}")
        print(f"  ⏭️  Skipped: {skip_count}")
        print()

        # Determine exit code
        if fail_count > 0:
            print("🚫 DEPLOYMENT BLOCKED: Critical failures detected")
            print("   Please fix the failed checks before deploying.")
            return 1
        elif warn_count > 0:
            print("⚠️  REVIEW REQUIRED: Warnings detected")
            print("   Please review warnings before deploying.")
            return 2
        else:
            print("✅ READY FOR DEPLOYMENT: All checks passed")
            return 0

    def run_all_validations(self, skip_infrastructure: bool = False) -> int:
        """Run all validation checks."""
        print(f"\n{'='*80}")
        print(f"  Phase 1.4 Real-Time Notification System - Deployment Readiness")
        print(f"  Environment: {self.env}")
        print(f"  API URL: {self.api_url}")
        print(f"{'='*80}\n")

        # Run validations
        self.validate_code_structure()
        self.validate_backend_api()

        if not skip_infrastructure:
            self.validate_redis_infrastructure()
        else:
            self.add_result(
                "Redis Infrastructure",
                CheckStatus.SKIP,
                "Skipped via --skip-infrastructure flag"
            )

        self.validate_frontend_build()
        self.validate_e2e_tests()
        self.validate_monitoring()

        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Phase 1.4 Real-Time Notification System deployment readiness"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment to validate (default: dev)"
    )
    parser.add_argument(
        "--api-url",
        help="Backend API URL (overrides environment default)"
    )
    parser.add_argument(
        "--skip-infrastructure",
        action="store_true",
        help="Skip infrastructure checks (Redis, Cloud Memorystore)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed results"
    )

    args = parser.parse_args()

    # Determine API URL
    if args.api_url:
        api_url = args.api_url
    else:
        # Environment-specific defaults
        api_urls = {
            "dev": os.getenv("VIVIDLY_API_URL", "https://dev-vividly-api-rm2v4spyrq-uc.a.run.app"),
            "staging": os.getenv("VIVIDLY_API_URL", "https://staging-vividly-api-xxx.run.app"),
            "prod": os.getenv("VIVIDLY_API_URL", "https://vividly-api-xxx.run.app"),
        }
        api_url = api_urls[args.env]

    # Create validator and run
    validator = Phase14Validator(args.env, api_url, args.verbose)
    exit_code = validator.run_all_validations(args.skip_infrastructure)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
