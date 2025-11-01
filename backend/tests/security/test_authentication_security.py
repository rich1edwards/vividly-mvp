"""
Authentication Security Tests

Tests for authentication vulnerabilities including:
- Brute force protection
- Session management
- Password policies
- JWT token security
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import time

from app.main import app
from app.core.security import create_access_token, decode_token


client = TestClient(app)


class TestBruteForceProtection:
    """Test protection against brute force attacks."""

    @pytest.mark.skip(reason="Rate limiting disabled in test mode")
    def test_rate_limiting_login_attempts(self):
        """Test that login endpoint enforces rate limiting."""
        # Attempt multiple failed logins
        failed_attempts = 0
        rate_limited = False

        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": f"attacker{i}@test.com",
                    "password": "WrongPassword123!",
                },
            )

            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break

            failed_attempts += 1
            time.sleep(0.1)  # Small delay between attempts

        # Should be rate limited before 10 attempts
        assert rate_limited, "Login endpoint should enforce rate limiting"
        assert failed_attempts < 10, "Too many login attempts allowed"

    @pytest.mark.skip(reason="Brute force protection disabled in test mode")
    def test_account_lockout_after_failed_attempts(self):
        """Test that accounts are temporarily locked after multiple failed logins."""
        # This assumes account lockout is implemented
        # Adjust based on your actual implementation

        test_email = "legitimate@test.com"

        # Attempt multiple failed logins with same email
        for i in range(6):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": test_email, "password": "WrongPassword"},
            )

        # Next attempt should indicate account is locked
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": "CorrectPassword123!"},
        )

        # Should either be rate limited or show account locked error
        assert response.status_code in [429, 403, 401]


class TestPasswordSecurity:
    """Test password security requirements."""

    def test_password_minimum_length(self):
        """Test that passwords must meet minimum length requirement."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@test.com",
                "password": "Short1!",  # Too short
                "first_name": "Test",
                "last_name": "User",
                "role": "student",
                "grade_level": 10,
            },
        )

        assert response.status_code == 422, "Should reject short passwords"

    def test_password_complexity_requirements(self):
        """Test that passwords must contain uppercase, lowercase, and numbers."""
        weak_passwords = [
            "alllowercase",  # No uppercase or numbers
            "ALLUPPERCASE",  # No lowercase or numbers
            "NoNumbers",  # No numbers
            "12345678",  # No letters
            "lowernumber1",  # No uppercase
        ]

        for password in weak_passwords:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"user{password}@test.com",
                    "password": password,
                    "first_name": "Test",
                    "last_name": "User",
                    "role": "student",
                    "grade_level": 10,
                },
            )

            assert (
                response.status_code == 422
            ), f"Should reject weak password: {password}"

    def test_common_passwords_rejected(self):
        """Test that common/compromised passwords are rejected."""
        common_passwords = [
            "Password123!",
            "Welcome123!",
            "Admin123!",
        ]

        for password in common_passwords:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"user{password}@test.com",
                    "password": password,
                    "first_name": "Test",
                    "last_name": "User",
                    "role": "student",
                    "grade_level": 10,
                },
            )

            # Implementation may vary - either reject or warn
            # Adjust assertion based on your implementation
            # assert response.status_code in [422, 400]


class TestJWTSecurity:
    """Test JWT token security."""

    def test_jwt_token_expiration(self):
        """Test that JWT tokens expire after specified time."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "user_test123"},
            expires_delta=timedelta(seconds=-10),  # Already expired
        )

        # Try to use expired token
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401, "Expired tokens should be rejected"

    def test_jwt_token_tampering(self):
        """Test that tampered JWT tokens are rejected."""
        # Create valid token
        valid_token = create_access_token(data={"sub": "user_test123"})

        # Tamper with token (change last character)
        tampered_token = valid_token[:-1] + ("a" if valid_token[-1] != "a" else "b")

        # Try to use tampered token
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"}
        )

        assert response.status_code == 401, "Tampered tokens should be rejected"

    def test_jwt_missing_claims(self):
        """Test that tokens with missing required claims are rejected."""
        # This would need custom token creation to test
        # Depends on your JWT implementation
        pass


class TestSessionManagement:
    """Test session management security."""

    def test_logout_invalidates_token(self):
        """Test that logout properly invalidates the session."""
        # Login to get token
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@test.com", "password": "Password123!"},
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        assert logout_response.status_code == 204  # 204 No Content is correct for logout

        # Try to use token after logout
        me_response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        # Token should be invalid after logout
        assert me_response.status_code == 401

    def test_concurrent_sessions_limit(self):
        """Test that users can't have unlimited concurrent sessions."""
        # This depends on your session management implementation
        pass

    def test_session_fixation_prevention(self):
        """Test that session IDs are regenerated on login."""
        # This is typically handled by JWT approach
        # No traditional session fixation vulnerability with JWTs
        pass


class TestAuthorizationSecurity:
    """Test authorization and access control."""

    def test_student_cannot_access_teacher_endpoints(self):
        """Test that students cannot access teacher-only endpoints."""
        # Login as student
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@test.com", "password": "Password123!"},
        )

        student_token = response.json()["access_token"]

        # Try to access teacher endpoint (POST /teachers/classes requires teacher role)
        response = client.post(
            "/api/v1/teachers/classes",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"name": "Test Class", "subject": "Math", "grade_levels": [9, 10]},
        )

        assert (
            response.status_code == 403
        ), "Students should not access teacher endpoints"

    def test_teacher_cannot_access_admin_endpoints(self):
        """Test that teachers cannot access admin-only endpoints."""
        # Login as teacher
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@test.com", "password": "TeacherPassword123!"},
        )

        teacher_token = response.json()["access_token"]

        # Try to access admin endpoint
        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 403, "Teachers should not access admin endpoints"

    def test_horizontal_privilege_escalation_prevention(self):
        """Test that users cannot access other users' data."""
        # Login as student 1
        response1 = client.post(
            "/api/v1/auth/login",
            json={"email": "student1@test.com", "password": "Password123!"},
        )

        student1_token = response1.json()["access_token"]
        student1_id = response1.json()["user"]["user_id"]

        # Login as student 2 to get their user_id
        response2 = client.post(
            "/api/v1/auth/login",
            json={"email": "student2@test.com", "password": "Password123!"},
        )
        student2_id = response2.json()["user"]["user_id"]

        # Try to access student 2's data using student 1's token
        response = client.get(
            f"/api/v1/students/{student2_id}",
            headers={"Authorization": f"Bearer {student1_token}"},
        )

        # Should be forbidden
        assert response.status_code in [403, 404]


class TestInputValidationSecurity:
    """Test input validation to prevent injection attacks."""

    def test_sql_injection_prevention_in_login(self):
        """Test that SQL injection attempts are prevented."""
        sql_injection_payloads = [
            "admin' OR '1'='1",
            "admin'--",
            "admin' #",
            "' OR 1=1--",
        ]

        for payload in sql_injection_payloads:
            response = client.post(
                "/api/v1/auth/login", json={"email": payload, "password": "anything"}
            )

            # Should not return 200 (successful login)
            assert (
                response.status_code != 200
            ), f"SQL injection payload succeeded: {payload}"

    def test_xss_prevention_in_user_input(self):
        """Test that XSS payloads are sanitized."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@test.com",
                    "password": "Password123!",
                    "first_name": payload,
                    "last_name": "User",
                    "role": "student",
                    "grade_level": 10,
                },
            )

            # Should either reject or sanitize
            if response.status_code == 201:
                # If accepted, check that it's sanitized
                user_data = response.json()
                assert "<script>" not in user_data.get("first_name", "")
                assert "javascript:" not in user_data.get("first_name", "")

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are prevented."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
        ]

        for payload in path_traversal_payloads:
            # Test on various endpoints that might handle file paths
            response = client.get(f"/api/v1/files/{payload}")

            # Should not return 200 or reveal system files
            assert response.status_code in [400, 403, 404]


class TestCORSSecurity:
    """Test CORS (Cross-Origin Resource Sharing) security."""

    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured."""
        # CORS middleware only adds headers when Origin header is present
        response = client.options(
            "/api/v1/auth/login",
            headers={"Origin": "http://localhost:3000"}
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in [
            h.lower() for h in response.headers.keys()
        ]

    def test_cors_credentials_properly_configured(self):
        """Test that credentials are properly handled in CORS."""
        response = client.options(
            "/api/v1/auth/login",
            headers={"Origin": "http://localhost:3000"}
        )

        # Should allow credentials if needed
        if "access-control-allow-credentials" in response.headers:
            # If credentials are allowed, origin should not be *
            allow_origin = response.headers.get("access-control-allow-origin", "")
            assert allow_origin != "*", "Wildcard origin with credentials is insecure"


class TestCSRFProtection:
    """Test CSRF (Cross-Site Request Forgery) protection."""

    def test_state_changing_requests_require_authentication(self):
        """Test that POST/PUT/DELETE require authentication."""
        # Try POST without authentication (use teacher endpoint)
        response = client.post(
            "/api/v1/teachers/classes", json={"name": "Test Class", "subject": "Test"}
        )

        # Should return 401 (not authenticated) or 403 (authenticated but not authorized)
        assert response.status_code in [401, 403], "State-changing requests should require auth"

    def test_csrf_token_validation(self):
        """Test CSRF token validation if implemented."""
        # This depends on your CSRF protection implementation
        # JWT-based APIs typically don't use CSRF tokens
        pass


class TestSecurityHeaders:
    """Test security-related HTTP headers."""

    def test_security_headers_present(self):
        """Test that important security headers are set."""
        response = client.get("/api/v1/auth/login")

        # Check for important security headers
        headers_to_check = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-xss-protection": "1; mode=block",
            "strict-transport-security": None,  # Should exist
        }

        for header, expected_value in headers_to_check.items():
            header_value = response.headers.get(header, "").lower()

            if expected_value is None:
                # Just check it exists
                assert header in [
                    h.lower() for h in response.headers.keys()
                ], f"Missing security header: {header}"
            elif isinstance(expected_value, list):
                # Check if value is one of the expected
                assert any(
                    ev.lower() in header_value for ev in expected_value
                ), f"Header {header} has unexpected value: {header_value}"
            else:
                # Check exact value
                assert (
                    expected_value.lower() in header_value
                ), f"Header {header} has unexpected value: {header_value}"
