"""
Integration tests for authentication endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.auth
class TestRegisterEndpoint:
    """Test /api/v1/auth/register endpoint."""

    def test_register_student_success(self, client):
        """Test successful student registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newstudent@test.com",
                "password": "Password123",
                "first_name": "New",
                "last_name": "Student",
                "role": "student",
                "grade_level": 10,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_teacher_success(self, client):
        """Test successful teacher registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newteacher@test.com",
                "password": "Password123",
                "first_name": "New",
                "last_name": "Teacher",
                "role": "teacher",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "Password123",
                "first_name": "Test",
                "last_name": "User",
                "role": "student",
                "grade_level": 10,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "password": "weak",
                "first_name": "Test",
                "last_name": "User",
                "role": "student",
                "grade_level": 10,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_duplicate_email(self, client, sample_student):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": sample_student.email,
                "password": "Password123",
                "first_name": "Duplicate",
                "last_name": "User",
                "role": "student",
                "grade_level": 10,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.auth
class TestLoginEndpoint:
    """Test /api/v1/auth/login endpoint."""

    def test_login_success(self, client, sample_student):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_student.email,
                "password": "Password123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, sample_student):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": sample_student.email,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "Password123",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.auth
class TestGetMeEndpoint:
    """Test /api/v1/auth/me endpoint."""

    def test_get_me_success(self, client, sample_student, student_headers):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=student_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == sample_student.user_id
        assert data["email"] == sample_student.email
        assert data["role"] == "student"

    def test_get_me_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


@pytest.mark.integration
@pytest.mark.auth
class TestLogoutEndpoint:
    """Test /api/v1/auth/logout endpoint."""

    def test_logout_success(self, client, sample_student, student_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=student_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_all_devices(self, client, sample_student, student_headers):
        """Test logout from all devices."""
        response = client.post(
            "/api/v1/auth/logout?all_devices=true", headers=student_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_no_token(self, client):
        """Test logout without token."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.auth
class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
