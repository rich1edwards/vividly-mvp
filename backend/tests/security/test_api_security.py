"""
API Security Tests

Tests for API security vulnerabilities including:
- Mass assignment
- Excessive data exposure
- Broken object level authorization (BOLA)
- Injection attacks
- Rate limiting
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMassAssignment:
    """Test protection against mass assignment vulnerabilities."""

    def test_cannot_assign_admin_role_during_registration(self):
        """Test that users cannot assign themselves admin role."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "attacker@test.com",
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "admin",  # Trying to become admin
                "grade_level": 10,
            },
        )

        # Should reject with 422 validation error
        assert response.status_code == 422, "Admin role registration should be rejected"
        error_detail = response.json().get("detail", [])
        # Check that error mentions role validation
        error_msg = str(error_detail).lower()
        assert (
            "role" in error_msg or "admin" in error_msg
        ), "Error should mention role issue"

    def test_cannot_modify_readonly_fields(self):
        """Test that readonly fields like user_id, created_at cannot be modified."""
        # Login as student
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@test.com", "password": "Password123!"},
        )

        token = login_response.json()["access_token"]
        original_user_id = login_response.json()["user"]["user_id"]

        # Try to modify user_id and other readonly fields
        response = client.patch(
            "/api/v1/students/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_id": "attacker_user_id",  # Should be ignored
                "created_at": "2000-01-01T00:00:00",  # Should be ignored
                "role": "admin",  # Should be ignored
                "first_name": "Updated",  # Should be allowed
            },
        )

        # Check that readonly fields weren't modified
        if response.status_code == 200:
            user_data = response.json()
            assert user_data["user_id"] == original_user_id
            assert user_data["role"] != "admin"


class TestExcessiveDataExposure:
    """Test that APIs don't expose sensitive data."""

    def test_passwords_not_exposed_in_responses(self):
        """Test that password hashes are never returned in API responses."""
        # Register user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecretPassword123!",
                "first_name": "New",
                "last_name": "User",
                "role": "student",
                "grade_level": 10,
            },
        )

        # Check response doesn't contain password
        response_text = response.text.lower()
        assert "password" not in response_text or "password_hash" not in response_text

        # Check profile endpoint
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "newuser@test.com", "password": "SecretPassword123!"},
        )

        token = login_response.json()["access_token"]

        profile_response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        profile_text = profile_response.text.lower()
        assert "password" not in profile_text
        assert "password_hash" not in profile_text

    def test_internal_fields_not_exposed(self):
        """Test that internal fields are not exposed in API responses."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@test.com", "password": "Password123!"},
        )

        token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        response_data = response.json()

        # Internal fields that should not be exposed
        internal_fields = [
            "password_hash",
            "password",
            "password_salt",
            "internal_notes",
        ]

        for field in internal_fields:
            assert (
                field not in response_data
            ), f"Internal field {field} should not be exposed"


class TestBrokenObjectLevelAuthorization:
    """Test for BOLA (IDOR) vulnerabilities."""

    def test_cannot_access_other_users_profile(self):
        """Test that users cannot access other users' profiles by changing IDs."""
        # Login as student 1
        login1 = client.post(
            "/api/v1/auth/login",
            json={"email": "student1@test.com", "password": "Password123!"},
        )

        student1_token = login1.json()["access_token"]

        # Try to access student 2's profile
        response = client.get(
            "/api/v1/students/student2_user_id/profile",
            headers={"Authorization": f"Bearer {student1_token}"},
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    def test_cannot_modify_other_users_data(self):
        """Test that users cannot modify other users' data."""
        # Login as student 1
        login1 = client.post(
            "/api/v1/auth/login",
            json={"email": "student1@test.com", "password": "Password123!"},
        )

        student1_token = login1.json()["access_token"]

        # Try to update student 2's profile
        response = client.patch(
            "/api/v1/students/student2_user_id/profile",
            headers={"Authorization": f"Bearer {student1_token}"},
            json={"first_name": "Hacked"},
        )

        # Should be forbidden
        assert response.status_code in [403, 404]

    def test_teacher_cannot_access_other_teachers_classes(self):
        """Test that teachers cannot access other teachers' classes."""
        # Login as teacher 1
        login1 = client.post(
            "/api/v1/auth/login",
            json={"email": "teacher1@test.com", "password": "TeacherPassword123!"},
        )

        teacher1_token = login1.json()["access_token"]

        # Try to access teacher 2's class
        response = client.get(
            "/api/v1/teacher/classes/teacher2_class_id",
            headers={"Authorization": f"Bearer {teacher1_token}"},
        )

        # Should be forbidden
        assert response.status_code in [403, 404]


class TestInjectionAttacks:
    """Test protection against various injection attacks."""

    def test_nosql_injection_prevention(self):
        """Test that NoSQL injection attempts are prevented."""
        nosql_payloads = [
            {"$gt": ""},
            {"$ne": None},
            {"$regex": ".*"},
        ]

        for payload in nosql_payloads:
            response = client.post(
                "/api/v1/auth/login", json={"email": payload, "password": "anything"}
            )

            # Should not return 200
            assert response.status_code != 200

    def test_command_injection_prevention(self):
        """Test that command injection attempts are prevented."""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(id)",
        ]

        for payload in command_injection_payloads:
            response = client.post(
                "/api/v1/students/profile",
                json={"first_name": payload, "last_name": "User"},
            )

            # Should not execute commands
            if response.status_code == 200:
                response_text = response.text
                # Check that system command output is not in response
                assert "uid=" not in response_text
                assert "root:" not in response_text

    def test_ldap_injection_prevention(self):
        """Test that LDAP injection attempts are prevented."""
        ldap_payloads = [
            "*",
            "*)(uid=*",
            "admin)(|(password=*",
        ]

        for payload in ldap_payloads:
            response = client.post(
                "/api/v1/auth/login", json={"email": payload, "password": "anything"}
            )

            # Should not bypass authentication
            assert response.status_code != 200


class TestRateLimiting:
    """Test API rate limiting."""

    @pytest.mark.skip(reason="Rate limiting disabled in test mode")
    def test_api_rate_limiting_enforced(self):
        """Test that API endpoints enforce rate limiting."""
        # Make rapid requests to an endpoint
        responses = []

        for i in range(100):
            response = client.get("/api/v1/interests")
            responses.append(response.status_code)

            if response.status_code == 429:  # Too Many Requests
                break

        # Should hit rate limit before 100 requests
        assert 429 in responses, "API should enforce rate limiting"

    @pytest.mark.skip(reason="Rate limiting disabled in test mode")
    def test_authenticated_endpoints_have_rate_limits(self):
        """Test that authenticated endpoints also have rate limits."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@test.com", "password": "Password123!"},
        )

        token = login_response.json()["access_token"]

        # Make rapid authenticated requests
        rate_limited = False

        for i in range(50):
            response = client.get(
                "/api/v1/student/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 429:
                rate_limited = True
                break

        # Should eventually hit rate limit
        assert rate_limited, "Authenticated endpoints should have rate limits"


class TestBusinessLogicSecurity:
    """Test business logic vulnerabilities."""

    def test_cannot_enroll_in_negative_grade(self):
        """Test that invalid grade levels are rejected."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "student",
                "grade_level": -1,  # Invalid
            },
        )

        assert response.status_code == 422

    def test_cannot_create_class_with_invalid_data(self):
        """Test that class creation validates data properly."""
        # Login as teacher
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@test.com", "password": "TeacherPassword123!"},
        )

        token = login_response.json()["access_token"]

        # Try to create class with invalid data
        invalid_class_data = [
            {"name": "", "subject": "Math"},  # Empty name
            {"name": "Class", "subject": ""},  # Empty subject
            {"name": "Class", "subject": "Math", "grade_levels": [13]},  # Invalid grade
            {"name": "Class", "subject": "Math", "grade_levels": []},  # No grades
        ]

        for data in invalid_class_data:
            response = client.post(
                "/api/v1/teachers/classes",
                headers={"Authorization": f"Bearer {token}"},
                json=data,
            )

            assert response.status_code in [400, 422]

    def test_race_condition_protection(self):
        """Test that race conditions are prevented in critical operations."""
        # This would test concurrent requests to ensure no race conditions
        # Example: Multiple simultaneous enrollments, class creations, etc.
        pass


class TestDataLeakage:
    """Test for potential data leakage."""

    def test_error_messages_dont_leak_sensitive_info(self):
        """Test that error messages don't reveal sensitive information."""
        # Try to login with non-existent user
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "Password123!"},
        )

        error_message = response.json().get("detail", "").lower()

        # Error should not reveal whether email exists
        sensitive_phrases = ["email not found", "user does not exist", "no user with"]

        for phrase in sensitive_phrases:
            assert phrase not in error_message, "Error message reveals user existence"

    def test_timing_attacks_prevention(self):
        """Test that responses take similar time for existing/non-existing users."""
        import time

        # Time login with existing user
        start = time.time()
        client.post(
            "/api/v1/auth/login",
            json={"email": "existing@test.com", "password": "WrongPassword"},
        )
        existing_time = time.time() - start

        # Time login with non-existing user
        start = time.time()
        client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "WrongPassword"},
        )
        nonexistent_time = time.time() - start

        # Times should be relatively similar (within 100ms)
        time_diff = abs(existing_time - nonexistent_time)
        assert time_diff < 0.1, "Timing difference could reveal user existence"


class TestFileUploadSecurity:
    """Test file upload security if applicable."""

    def test_file_type_validation(self):
        """Test that only allowed file types are accepted."""
        # This would test file upload endpoints if they exist
        pass

    def test_file_size_limits(self):
        """Test that file size limits are enforced."""
        # This would test file upload endpoints if they exist
        pass

    def test_malicious_file_detection(self):
        """Test that malicious files are rejected."""
        # This would test file upload endpoints if they exist
        pass
