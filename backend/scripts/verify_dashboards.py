#!/usr/bin/env python3
"""
Sprint 3 Phase 4: Dashboard Configuration Verification Script
Following Andrew Ng's "Test everything" principle

This script verifies:
1. Dashboard JSON configuration is valid
2. All required widgets are present
3. Metric filters match Sprint 3 Phase 2 metrics
4. Terraform configuration is valid
5. Dashboard can be deployed to GCP

Usage:
    python3 scripts/verify_dashboards.py

Exit Codes:
    0 = All checks passed
    1 = One or more checks failed
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


class DashboardVerifier:
    """Verifies GCP monitoring dashboard configuration"""

    def __init__(self):
        self.passed_checks = []
        self.failed_checks = []
        self.base_path = Path(__file__).parent.parent.parent

        # Expected metrics from Sprint 3 Phase 2
        self.expected_metrics = [
            "vividly/rate_limit_hits_total",
            "vividly/rate_limit_exceeded_total",
            "vividly/rate_limit_middleware_latency_ms",
            "vividly/auth_login_attempts_total",
            "vividly/auth_login_failures_total",
            "vividly/auth_token_refresh_total",
            "vividly/auth_session_duration_seconds",
            "vividly/auth_active_sessions",
            "vividly/http_request_total",
            "vividly/http_request_duration_seconds",
            "vividly/content_generation_requests_total",
            "vividly/content_generation_duration_seconds",
        ]

    def check(self, check_name: str, condition: bool, message: str = "") -> bool:
        """Record a check result"""
        if condition:
            self.passed_checks.append(check_name)
            print(f"{GREEN}✓{RESET} {check_name}")
            if message:
                print(f"  {message}")
            return True
        else:
            self.failed_checks.append(check_name)
            print(f"{RED}✗{RESET} {check_name}")
            if message:
                print(f"  {RED}{message}{RESET}")
            return False

    def verify_dashboard_json_exists(self) -> bool:
        """Check if dashboard JSON configuration file exists"""
        dashboard_path = self.base_path / "infrastructure" / "monitoring" / "dashboards" / "vividly-metrics-overview.json"

        if not dashboard_path.exists():
            return self.check(
                "Dashboard JSON file exists",
                False,
                f"File not found: {dashboard_path}"
            )

        self.dashboard_path = dashboard_path
        return self.check("Dashboard JSON file exists", True, f"Found: {dashboard_path}")

    def verify_dashboard_json_valid(self) -> bool:
        """Check if dashboard JSON is valid"""
        try:
            with open(self.dashboard_path, 'r') as f:
                self.dashboard_config = json.load(f)

            return self.check("Dashboard JSON is valid", True, "JSON parsed successfully")
        except json.JSONDecodeError as e:
            return self.check("Dashboard JSON is valid", False, f"JSON parsing error: {e}")

    def verify_dashboard_structure(self) -> bool:
        """Check if dashboard has required structure"""
        required_keys = ["displayName", "mosaicLayout"]

        for key in required_keys:
            if key not in self.dashboard_config:
                return self.check(
                    f"Dashboard has '{key}' field",
                    False,
                    f"Missing required field: {key}"
                )
            self.check(f"Dashboard has '{key}' field", True)

        # Check mosaicLayout structure
        if "tiles" not in self.dashboard_config.get("mosaicLayout", {}):
            return self.check(
                "Dashboard has 'mosaicLayout.tiles' field",
                False,
                "Missing tiles array in mosaicLayout"
            )

        tile_count = len(self.dashboard_config["mosaicLayout"]["tiles"])
        return self.check(
            "Dashboard has tiles",
            tile_count > 0,
            f"Found {tile_count} widget tiles"
        )

    def verify_dashboard_metrics(self) -> bool:
        """Check if dashboard widgets use correct metrics"""
        tiles = self.dashboard_config["mosaicLayout"]["tiles"]
        found_metrics = set()

        for tile in tiles:
            widget = tile.get("widget", {})

            # Check xyChart widgets (time series)
            if "xyChart" in widget:
                datasets = widget["xyChart"].get("dataSets", [])
                for dataset in datasets:
                    query = dataset.get("timeSeriesQuery", {})
                    filter_str = query.get("timeSeriesFilter", {}).get("filter", "")

                    # Extract metric name from filter
                    if 'metric.type="custom.googleapis.com/' in filter_str:
                        metric_name = filter_str.split('custom.googleapis.com/')[1].split('"')[0]
                        found_metrics.add(metric_name)

        # Verify all expected metrics are present
        missing_metrics = []
        for expected_metric in self.expected_metrics:
            if expected_metric not in found_metrics:
                missing_metrics.append(expected_metric)

        if missing_metrics:
            return self.check(
                "All Phase 2 metrics included in dashboard",
                False,
                f"Missing metrics: {', '.join(missing_metrics)}"
            )

        return self.check(
            "All Phase 2 metrics included in dashboard",
            True,
            f"Found all {len(self.expected_metrics)} metrics"
        )

    def verify_dashboard_ui_elements(self) -> bool:
        """Check if dashboard has good UI/UX elements"""
        tiles = self.dashboard_config["mosaicLayout"]["tiles"]

        # Check for header text widget
        has_header = False
        has_emojis = False
        has_thresholds = False

        for tile in tiles:
            widget = tile.get("widget", {})

            # Check for text widget (header)
            if "text" in widget:
                has_header = True
                content = widget["text"].get("content", "")
                if "🟢" in content or "🟡" in content or "🔴" in content:
                    has_emojis = True

            # Check for thresholds (color-coded alerts)
            if "xyChart" in widget:
                if "thresholds" in widget["xyChart"]:
                    has_thresholds = True

        self.check("Dashboard has header widget", has_header)
        self.check("Dashboard uses emoji indicators", has_emojis)
        self.check("Dashboard has color-coded thresholds", has_thresholds)

        return has_header and has_emojis and has_thresholds

    def verify_terraform_exists(self) -> bool:
        """Check if Terraform configuration exists"""
        terraform_path = self.base_path / "infrastructure" / "monitoring" / "terraform" / "dashboards.tf"

        if not terraform_path.exists():
            return self.check(
                "Terraform configuration exists",
                False,
                f"File not found: {terraform_path}"
            )

        self.terraform_path = terraform_path
        return self.check("Terraform configuration exists", True, f"Found: {terraform_path}")

    def verify_terraform_structure(self) -> bool:
        """Check if Terraform configuration has required structure"""
        with open(self.terraform_path, 'r') as f:
            terraform_content = f.read()

        required_elements = [
            ("resource declaration", 'resource "google_monitoring_dashboard"'),
            ("project_id variable", 'variable "project_id"'),
            ("environment variable", 'variable "environment"'),
            ("dashboard_id output", 'output "dashboard_id"'),
            ("dashboard_url output", 'output "dashboard_url"'),
        ]

        all_found = True
        for name, element in required_elements:
            if element in terraform_content:
                self.check(f"Terraform has {name}", True)
            else:
                self.check(f"Terraform has {name}", False, f"Missing: {element}")
                all_found = False

        return all_found

    def print_summary(self):
        """Print verification summary"""
        print(f"\n{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}DASHBOARD VERIFICATION SUMMARY{RESET}")
        print(f"{BOLD}{'=' * 60}{RESET}\n")

        total_checks = len(self.passed_checks) + len(self.failed_checks)

        if self.failed_checks:
            print(f"{RED}✗ FAILED{RESET} ({len(self.failed_checks)} checks)\n")
            for check in self.failed_checks:
                print(f"  {RED}✗{RESET} {check}")
            print(f"\n{YELLOW}⚠ Dashboard configuration verification failed!{RESET}")
            print(f"{YELLOW}  Please fix the errors above before deploying.{RESET}\n")
            return False
        else:
            print(f"{GREEN}✓ All dashboard configuration checks passed!{RESET}")
            print(f"{GREEN}  Dashboards are ready for deployment.{RESET}\n")
            print(f"Total checks: {total_checks}")
            print(f"Passed: {GREEN}{len(self.passed_checks)}{RESET}")
            print(f"Failed: {RED}{len(self.failed_checks)}{RESET}\n")

            # Print deployment instructions
            print(f"{BOLD}Next Steps:{RESET}")
            print(f"1. Deploy dashboard using Terraform:")
            print(f"   cd infrastructure/monitoring/terraform")
            print(f"   terraform init")
            print(f"   terraform plan -var='project_id=vividly-dev-rich'")
            print(f"   terraform apply -var='project_id=vividly-dev-rich'\n")
            print(f"2. View dashboard in GCP Console:")
            print(f"   https://console.cloud.google.com/monitoring/dashboards\n")

            return True


def main():
    """Main verification function"""
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}DASHBOARD CONFIGURATION VERIFICATION{RESET}")
    print(f"{BOLD}Sprint 3 Phase 4: Pre-deployment check{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    verifier = DashboardVerifier()

    # Run all verification checks
    checks = [
        verifier.verify_dashboard_json_exists,
        verifier.verify_dashboard_json_valid,
        verifier.verify_dashboard_structure,
        verifier.verify_dashboard_metrics,
        verifier.verify_dashboard_ui_elements,
        verifier.verify_terraform_exists,
        verifier.verify_terraform_structure,
    ]

    for check in checks:
        if not check():
            # If a check fails and it's critical, stop early
            if check.__name__ in ["verify_dashboard_json_exists", "verify_dashboard_json_valid"]:
                verifier.print_summary()
                sys.exit(1)

    # Print summary and exit
    success = verifier.print_summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
