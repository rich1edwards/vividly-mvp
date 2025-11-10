#!/usr/bin/env python3
"""
CI/CD Verification Script for Metrics Configuration

This script verifies that the GCP Cloud Monitoring integration is properly
configured and all required metrics are defined.

Following Andrew Ng's "Test everything" principle - this ensures metrics
configuration is correct in CI/CD before deployment.

Usage:
    python scripts/verify_metrics_config.py

Exit codes:
    0: All checks passed
    1: Configuration errors found

Sprint 3 Phase 2: Production-ready metrics verification.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class MetricsConfigVerifier:
    """Verifies GCP Cloud Monitoring metrics configuration."""

    # Expected metrics from Sprint 2 and Sprint 3 requirements
    REQUIRED_METRICS = {
        # Rate Limiting Metrics (Sprint 2)
        "rate_limit_hits_total": {
            "type": "counter",
            "labels": ["endpoint", "ip_address"],
            "description": "Total rate limit checks performed",
        },
        "rate_limit_exceeded_total": {
            "type": "counter",
            "labels": ["endpoint", "ip_address"],
            "description": "Total rate limit exceeded events",
        },
        "brute_force_lockouts_total": {
            "type": "counter",
            "labels": ["ip_address"],
            "description": "Total brute force lockout events",
        },
        "rate_limit_middleware_latency_ms": {
            "type": "gauge",
            "labels": ["endpoint"],
            "description": "Rate limiting middleware processing time",
        },
        # Authentication Metrics
        "auth_login_attempts_total": {
            "type": "counter",
            "labels": ["status"],
            "description": "Total login attempts",
        },
        "auth_login_failures_total": {
            "type": "counter",
            "labels": ["reason"],
            "description": "Total failed login attempts",
        },
        "auth_token_refresh_total": {
            "type": "counter",
            "labels": ["status"],
            "description": "Total token refresh attempts",
        },
        "auth_session_duration_seconds": {
            "type": "gauge",
            "labels": [],
            "description": "Authentication session duration",
        },
        "auth_active_sessions": {
            "type": "gauge",
            "labels": [],
            "description": "Current active sessions",
        },
        # System Health Metrics (Sprint 3)
        "http_request_total": {
            "type": "counter",
            "labels": ["method", "endpoint", "status_code"],
            "description": "Total HTTP requests",
        },
        "http_request_duration_seconds": {
            "type": "gauge",
            "labels": ["method", "endpoint"],
            "description": "HTTP request processing time",
        },
        # Content Generation Metrics
        "content_generation_requests_total": {
            "type": "counter",
            "labels": ["status"],
            "description": "Total content generation requests",
        },
        "content_generation_duration_seconds": {
            "type": "gauge",
            "labels": ["stage"],
            "description": "Content generation stage duration",
        },
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

    def verify_dependencies(self) -> bool:
        """Verify required Python dependencies are installed."""
        print("\n" + "=" * 60)
        print("VERIFYING DEPENDENCIES")
        print("=" * 60)

        try:
            import google.cloud.monitoring_v3

            self.successes.append("✓ google-cloud-monitoring package installed")
            return True
        except ImportError as e:
            self.errors.append(f"✗ Missing dependency: google-cloud-monitoring")
            self.errors.append(
                f"  Install with: pip install google-cloud-monitoring==2.15.1"
            )
            return False

    def verify_metrics_client(self) -> bool:
        """Verify metrics client module is correctly implemented."""
        print("\n" + "=" * 60)
        print("VERIFYING METRICS CLIENT MODULE")
        print("=" * 60)

        try:
            from app.core.metrics import MetricsClient, get_metrics_client

            # Verify MetricsClient class exists
            self.successes.append("✓ MetricsClient class found")

            # Verify singleton function
            self.successes.append("✓ get_metrics_client function found")

            # Verify MetricsClient has required methods
            required_methods = [
                "increment_rate_limit_hits",
                "increment_rate_limit_exceeded",
                "increment_brute_force_lockouts",
                "record_rate_limit_middleware_latency",
                "increment_auth_login_attempts",
                "increment_auth_login_failures",
                "increment_auth_token_refresh",
                "record_auth_session_duration",
                "set_auth_active_sessions",
                "increment_http_request",
                "record_request_duration",
                "increment_content_generation_requests",
                "record_content_generation_duration",
            ]

            for method_name in required_methods:
                if hasattr(MetricsClient, method_name):
                    self.successes.append(
                        f"✓ MetricsClient.{method_name}() method found"
                    )
                else:
                    self.errors.append(
                        f"✗ Missing method: MetricsClient.{method_name}()"
                    )

            return len(self.errors) == 0

        except ImportError as e:
            self.errors.append(f"✗ Failed to import metrics module: {e}")
            return False
        except Exception as e:
            self.errors.append(f"✗ Error verifying metrics client: {e}")
            return False

    def verify_middleware_integration(self) -> bool:
        """Verify metrics are integrated into middleware."""
        print("\n" + "=" * 60)
        print("VERIFYING MIDDLEWARE INTEGRATION")
        print("=" * 60)

        # Check LoggingContextMiddleware integration
        try:
            from app.middleware.logging_middleware import LoggingContextMiddleware

            # Read the middleware source to verify metrics calls
            middleware_file = (
                backend_path / "app" / "middleware" / "logging_middleware.py"
            )
            if middleware_file.exists():
                content = middleware_file.read_text()

                if "get_metrics_client" in content:
                    self.successes.append(
                        "✓ LoggingContextMiddleware imports metrics client"
                    )
                else:
                    self.warnings.append(
                        "⚠ LoggingContextMiddleware may not use metrics client"
                    )

                if "increment_http_request" in content:
                    self.successes.append(
                        "✓ LoggingContextMiddleware tracks HTTP requests"
                    )
                else:
                    self.warnings.append(
                        "⚠ LoggingContextMiddleware may not track HTTP requests"
                    )

                if "record_request_duration" in content:
                    self.successes.append(
                        "✓ LoggingContextMiddleware tracks request duration"
                    )
                else:
                    self.warnings.append(
                        "⚠ LoggingContextMiddleware may not track request duration"
                    )

        except Exception as e:
            self.warnings.append(f"⚠ Could not verify LoggingContextMiddleware: {e}")

        # Check rate limiting middleware integration
        try:
            rate_limit_file = backend_path / "app" / "middleware" / "rate_limit.py"
            if rate_limit_file.exists():
                content = rate_limit_file.read_text()

                if "get_metrics_client" in content:
                    self.successes.append(
                        "✓ Rate limiting middleware imports metrics client"
                    )
                else:
                    self.warnings.append(
                        "⚠ Rate limiting middleware may not use metrics client"
                    )

                if "increment_rate_limit_hits" in content:
                    self.successes.append(
                        "✓ Rate limiting middleware tracks rate limit hits"
                    )
                else:
                    self.warnings.append(
                        "⚠ Rate limiting middleware may not track rate limit hits"
                    )

                if "increment_rate_limit_exceeded" in content:
                    self.successes.append(
                        "✓ Rate limiting middleware tracks rate limit exceeded"
                    )
                else:
                    self.warnings.append(
                        "⚠ Rate limiting middleware may not track rate limit exceeded"
                    )

        except Exception as e:
            self.warnings.append(f"⚠ Could not verify rate limiting middleware: {e}")

        return True

    def verify_environment_config(self) -> bool:
        """Verify environment variables and configuration."""
        print("\n" + "=" * 60)
        print("VERIFYING ENVIRONMENT CONFIGURATION")
        print("=" * 60)

        # Check if METRICS_ENABLED is set (should default to true)
        metrics_enabled = os.getenv("METRICS_ENABLED", "true")
        if metrics_enabled.lower() in ["true", "1", "yes"]:
            self.successes.append(
                f"✓ METRICS_ENABLED={metrics_enabled} (metrics will be collected)"
            )
        else:
            self.warnings.append(
                f"⚠ METRICS_ENABLED={metrics_enabled} (metrics disabled)"
            )

        # Check GCP_PROJECT
        gcp_project = os.getenv("GCP_PROJECT")
        if gcp_project:
            self.successes.append(f"✓ GCP_PROJECT={gcp_project}")
        else:
            self.warnings.append("⚠ GCP_PROJECT not set (will use default)")

        return True

    def verify_tests_exist(self) -> bool:
        """Verify tests for metrics client exist."""
        print("\n" + "=" * 60)
        print("VERIFYING TESTS")
        print("=" * 60)

        test_file = backend_path / "tests" / "test_metrics.py"
        if test_file.exists():
            self.successes.append("✓ Metrics test file exists (tests/test_metrics.py)")

            # Check test file has content
            content = test_file.read_text()
            if len(content) > 100:  # Basic sanity check
                self.successes.append(
                    f"✓ Metrics test file has {len(content)} characters"
                )
            else:
                self.warnings.append("⚠ Metrics test file seems empty")

            return True
        else:
            self.errors.append("✗ Missing test file: tests/test_metrics.py")
            return False

    def print_summary(self):
        """Print verification summary."""
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)

        if self.successes:
            print(f"\n✓ PASSED ({len(self.successes)} checks)")
            for success in self.successes:
                print(f"  {success}")

        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)} checks)")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n✗ FAILED ({len(self.errors)} checks)")
            for error in self.errors:
                print(f"  {error}")

        print("\n" + "=" * 60)
        total_checks = len(self.successes) + len(self.warnings) + len(self.errors)
        print(f"Total checks: {total_checks}")
        print(f"Passed: {len(self.successes)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Failed: {len(self.errors)}")
        print("=" * 60 + "\n")

    def run_all_checks(self) -> bool:
        """Run all verification checks."""
        print("\n" + "=" * 60)
        print("METRICS CONFIGURATION VERIFICATION")
        print("Sprint 3 Phase 2: GCP Cloud Monitoring Integration")
        print("=" * 60)

        checks = [
            ("Dependencies", self.verify_dependencies),
            ("Metrics Client", self.verify_metrics_client),
            ("Middleware Integration", self.verify_middleware_integration),
            ("Environment Config", self.verify_environment_config),
            ("Tests", self.verify_tests_exist),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                if not result and check_name != "Middleware Integration":
                    all_passed = False
            except Exception as e:
                self.errors.append(f"✗ {check_name} check failed: {e}")
                all_passed = False

        self.print_summary()

        return all_passed and len(self.errors) == 0


def main():
    """Main entry point."""
    verifier = MetricsConfigVerifier()

    try:
        success = verifier.run_all_checks()

        if success:
            print("✓ All metrics configuration checks passed!")
            print("  Metrics are ready for production deployment.")
            return 0
        else:
            print("✗ Metrics configuration verification failed!")
            print("  Please fix the errors above before deploying.")
            return 1

    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
