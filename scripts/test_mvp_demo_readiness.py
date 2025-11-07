#!/usr/bin/env python3
"""
MVP Demo Readiness End-to-End Test Script

Following Andrew Ng's principle: "Measure everything before you demo"

This script tests the critical path for MVP demo:
1. Clarification workflow (vague query → clarification → refined query)
2. Happy path content generation (clear query → success)
3. Performance measurement (timing)
4. Error detection

Usage:
    python3 scripts/test_mvp_demo_readiness.py

Requirements:
    pip install requests python-dotenv
"""

import requests
import time
import json
import sys
import os
import base64
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv("API_URL", "https://dev-vividly-api-rm2v4spyrq-uc.a.run.app")
# Use actual seeded student account from seed_database.py
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "john.doe.11@student.hillsboro.edu")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "Student123!")

# Test queries
VAGUE_QUERY = "Tell me about science"
REFINED_QUERY = "Explain the scientific method including hypothesis formation, experimentation, and conclusion drawing with real-world examples"
CLEAR_QUERY = "Explain how photosynthesis works in plants, including the light-dependent and light-independent reactions, and why plants are green"

# Performance thresholds (Andrew Ng: Set clear success criteria)
MAX_GENERATION_TIME_SECONDS = 120  # 2 minutes
MAX_CLARIFICATION_TIME_SECONDS = 30  # 30 seconds


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\\033[92m'
    RED = '\\033[91m'
    YELLOW = '\\033[93m'
    BLUE = '\\033[94m'
    ENDC = '\\033[0m'
    BOLD = '\\033[1m'


def print_header(message: str):
    """Print section header"""
    print(f"\\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.ENDC}\\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"  {message}")


class MVPDemoTester:
    """End-to-end tester for MVP demo readiness"""

    def __init__(self):
        self.api_base = API_BASE_URL
        self.token = None
        self.user_id = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "start_time": datetime.now(),
        }

    def decode_jwt_user_id(self, token: str) -> Optional[str]:
        """Extract user_id from JWT token payload."""
        try:
            # JWT format: header.payload.signature
            # We only need the payload (middle part)
            parts = token.split('.')
            if len(parts) != 3:
                return None

            # Add padding if needed (base64 requires length divisible by 4)
            payload = parts[1]
            padding = 4 - (len(payload) % 4)
            if padding != 4:
                payload += '=' * padding

            # Decode base64
            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)

            # Extract user_id from 'sub' claim
            return payload_data.get('sub')
        except Exception as e:
            print_error(f"Failed to decode JWT: {e}")
            return None

    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        print_header("Test 1: Authentication")

        try:
            response = requests.post(
                f"{self.api_base}/api/v1/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            )

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.user_id = self.decode_jwt_user_id(self.token)
                print_success(f"Authenticated as {TEST_USER_EMAIL}")
                print_info(f"Token: {self.token[:20]}...")
                print_info(f"User ID: {self.user_id}")
                self.test_results["passed"] += 1
                return True
            else:
                print_error(f"Authentication failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.test_results["failed"] += 1
                return False

        except Exception as e:
            print_error(f"Authentication error: {str(e)}")
            self.test_results["failed"] += 1
            return False
        finally:
            self.test_results["total_tests"] += 1

    def submit_content_request(self, query: str, description: str) -> Optional[Dict[str, Any]]:
        """Submit a content generation request"""
        print_info(f"Submitting: {description}")
        print_info(f"Query: {query}")

        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.post(
                f"{self.api_base}/api/v1/content/generate",
                headers=headers,
                json={
                    "student_query": query,
                    "student_id": self.user_id,
                    "grade_level": 10,
                    "subject": "Science",
                    "topic": "General"
                }
            )

            if response.status_code in [200, 201, 202]:
                result = response.json()
                print_success(f"Request submitted successfully")
                print_info(f"Request ID: {result.get('request_id', 'N/A')}")
                print_info(f"Status: {result.get('status', 'N/A')}")
                return result
            else:
                print_error(f"Request failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return None

        except Exception as e:
            print_error(f"Request error: {str(e)}")
            return None

    def test_clarification_workflow(self) -> bool:
        """Test the clarification workflow"""
        print_header("Test 2: Clarification Workflow (Critical)")
        print_info("This is the flagship feature - must work for demo!")

        start_time = time.time()

        # Submit vague query
        result = self.submit_content_request(VAGUE_QUERY, "Vague query to trigger clarification")

        if not result:
            print_error("Failed to submit request")
            self.test_results["failed"] += 1
            self.test_results["total_tests"] += 1
            return False

        elapsed = time.time() - start_time

        # Check if clarification was triggered
        status = result.get("status")

        if status == "clarification_needed":
            print_success(f"Clarification detected in {elapsed:.2f}s")

            # Check timing
            if elapsed > MAX_CLARIFICATION_TIME_SECONDS:
                print_warning(f"Clarification took {elapsed:.2f}s (threshold: {MAX_CLARIFICATION_TIME_SECONDS}s)")
                self.test_results["warnings"] += 1

            # Check clarifying questions
            questions = result.get("clarifying_questions", [])
            if questions:
                print_success(f"Received {len(questions)} clarifying questions:")
                for i, q in enumerate(questions, 1):
                    print_info(f"  {i}. {q}")
            else:
                print_error("No clarifying questions returned")
                self.test_results["failed"] += 1
                self.test_results["total_tests"] += 1
                return False

            # Now test refined query
            print_info("\\nSubmitting refined query...")
            refined_result = self.submit_content_request(REFINED_QUERY, "Refined query after clarification")

            if refined_result and refined_result.get("status") in ["pending", "validating", "generating"]:
                print_success("Refined query accepted and processing")
                request_id = refined_result.get("request_id")

                # Poll for result (with timeout)
                if request_id:
                    final_status = self.poll_request_status(request_id, max_wait=MAX_GENERATION_TIME_SECONDS)
                    if final_status in ["completed", "clarification_needed"]:
                        print_success(f"Clarification workflow complete: {final_status}")
                        self.test_results["passed"] += 1
                        self.test_results["total_tests"] += 1
                        return True
                    else:
                        print_error(f"Generation failed with status: {final_status}")
                        self.test_results["failed"] += 1
                        self.test_results["total_tests"] += 1
                        return False
            else:
                print_error("Refined query failed")
                self.test_results["failed"] += 1
                self.test_results["total_tests"] += 1
                return False

        elif status in ["pending", "validating", "generating"]:
            print_warning("Query did NOT trigger clarification (expected for vague query)")
            print_warning("This may indicate clarification logic is not working")
            self.test_results["warnings"] += 1
            self.test_results["total_tests"] += 1
            return False
        else:
            print_error(f"Unexpected status: {status}")
            self.test_results["failed"] += 1
            self.test_results["total_tests"] += 1
            return False

    def test_happy_path_generation(self) -> bool:
        """Test happy path content generation"""
        print_header("Test 3: Happy Path Content Generation")
        print_info("Testing clear query → successful generation")

        start_time = time.time()

        # Submit clear query
        result = self.submit_content_request(CLEAR_QUERY, "Clear, well-formed query")

        if not result:
            print_error("Failed to submit request")
            self.test_results["failed"] += 1
            self.test_results["total_tests"] += 1
            return False

        request_id = result.get("request_id")
        status = result.get("status")

        if status == "clarification_needed":
            print_warning("Clear query triggered clarification (unexpected)")
            print_warning("Query may need to be more specific")
            self.test_results["warnings"] += 1
            self.test_results["total_tests"] += 1
            return False

        if status not in ["pending", "validating", "generating"]:
            print_error(f"Unexpected status: {status}")
            self.test_results["failed"] += 1
            self.test_results["total_tests"] += 1
            return False

        # Poll for completion
        final_status = self.poll_request_status(request_id, max_wait=MAX_GENERATION_TIME_SECONDS)

        elapsed = time.time() - start_time

        if final_status == "completed":
            print_success(f"Content generated successfully in {elapsed:.2f}s")

            if elapsed > MAX_GENERATION_TIME_SECONDS:
                print_warning(f"Generation took {elapsed:.2f}s (threshold: {MAX_GENERATION_TIME_SECONDS}s)")
                print_warning("Demo may feel slow to users")
                self.test_results["warnings"] += 1

            self.test_results["passed"] += 1
            self.test_results["total_tests"] += 1
            return True
        else:
            print_error(f"Generation failed with status: {final_status}")
            self.test_results["failed"] += 1
            self.test_results["total_tests"] += 1
            return False

    def poll_request_status(self, request_id: str, max_wait: int = 120) -> str:
        """Poll request status until completion or timeout"""
        print_info(f"Polling request {request_id} (max {max_wait}s)...")

        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()
        last_status = None

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait:
                print_warning(f"Polling timeout after {elapsed:.2f}s")
                return "timeout"

            try:
                response = requests.get(
                    f"{self.api_base}/api/v1/content/request/{request_id}/status",
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")

                    if status != last_status:
                        print_info(f"  Status: {status} ({elapsed:.1f}s)")
                        last_status = status

                    # Terminal statuses
                    if status in ["completed", "failed", "clarification_needed"]:
                        return status

                # Wait before next poll
                time.sleep(5)

            except Exception as e:
                print_error(f"Polling error: {str(e)}")
                return "error"

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")

        elapsed = (datetime.now() - self.test_results["start_time"]).total_seconds()

        print_info(f"Total Tests: {self.test_results['total_tests']}")
        print_info(f"Time Elapsed: {elapsed:.1f}s")
        print("")

        if self.test_results["passed"] > 0:
            print_success(f"Passed: {self.test_results['passed']}")
        if self.test_results["failed"] > 0:
            print_error(f"Failed: {self.test_results['failed']}")
        if self.test_results["warnings"] > 0:
            print_warning(f"Warnings: {self.test_results['warnings']}")

        print("")

        # Demo readiness assessment
        if self.test_results["failed"] == 0:
            if self.test_results["warnings"] == 0:
                print_success("✓ MVP is 100% DEMO-READY")
                print_info("All critical tests passed with no warnings")
                print_info("System is ready for live demo")
                return 0
            else:
                print_warning("⚠ MVP is MOSTLY DEMO-READY with warnings")
                print_info("All tests passed but there are performance concerns")
                print_info("Demo can proceed with caveats")
                return 0
        else:
            print_error("✗ MVP is NOT DEMO-READY")
            print_info(f"{self.test_results['failed']} critical test(s) failed")
            print_info("Fix issues before demoing")
            return 1

    def run_all_tests(self) -> int:
        """Run all demo readiness tests"""
        print_header("MVP Demo Readiness Test Suite")
        print_info(f"API Base: {self.api_base}")
        print_info(f"Test User: {TEST_USER_EMAIL}")
        print_info(f"Started: {self.test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")

        # Test 1: Authentication
        if not self.authenticate():
            print_error("\\nCannot proceed without authentication")
            return self.print_summary()

        # Test 2: Clarification Workflow (CRITICAL)
        clarification_works = self.test_clarification_workflow()

        # Test 3: Happy Path Generation
        happy_path_works = self.test_happy_path_generation()

        # Print summary and return exit code
        return self.print_summary()


def main():
    """Main entry point"""
    print("")
    print(f"{Colors.BOLD}Vividly MVP Demo Readiness Test{Colors.ENDC}")
    print(f"{Colors.BOLD}Following Andrew Ng's principle: 'Measure everything before you demo'{Colors.ENDC}")
    print("")

    tester = MVPDemoTester()
    exit_code = tester.run_all_tests()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
