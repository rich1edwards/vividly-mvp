"""
Unit tests for authentication service.
"""
import pytest
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.services import auth_service
from app.schemas.auth import UserRegister
from app.models.user import User, UserRole, UserStatus
from app.utils.security import verify_password


@pytest.mark.unit
@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality."""

    def test_register_student_success(self, db_session):
        """Test successful student registration."""
        user_data = UserRegister(
            email="newstudent@test.com",
            password="Password123",
            first_name="New",
            last_name="Student",
            role=UserRole.STUDENT,
            grade_level=10,
        )

        user = auth_service.register_user(db_session, user_data)

        assert user.email == "newstudent@test.com"
        assert user.first_name == "New"
        assert user.last_name == "Student"
        assert user.role == UserRole.STUDENT
        assert user.grade_level == 10
        assert user.status == UserStatus.ACTIVE
        assert verify_password("Password123", user.password_hash)

    def test_register_teacher_success(self, db_session):
        """Test successful teacher registration."""
        user_data = UserRegister(
            email="newteacher@test.com",
            password="Password123",
            first_name="New",
            last_name="Teacher",
            role=UserRole.TEACHER,
        )

        user = auth_service.register_user(db_session, user_data)

        assert user.email == "newteacher@test.com"
        assert user.role == UserRole.TEACHER
        assert user.grade_level is None

    def test_register_duplicate_email(self, db_session, sample_student):
        """Test registration with duplicate email fails."""
        user_data = UserRegister(
            email=sample_student.email,
            password="Password123",
            first_name="Duplicate",
            last_name="User",
            role=UserRole.STUDENT,
            grade_level=10,
        )

        with pytest.raises(HTTPException) as exc:
            auth_service.register_user(db_session, user_data)

        assert exc.value.status_code == 400
        assert "already registered" in exc.value.detail.lower()


@pytest.mark.unit
@pytest.mark.auth
class TestUserAuthentication:
    """Test user authentication functionality."""

    def test_authenticate_success(self, db_session, sample_student):
        """Test successful authentication."""
        user = auth_service.authenticate_user(
            db_session,
            sample_student.email,
            "Password123"
        )

        assert user.user_id == sample_student.user_id
        assert user.email == sample_student.email
        assert user.last_login_at is not None

    def test_authenticate_wrong_password(self, db_session, sample_student):
        """Test authentication with wrong password fails."""
        with pytest.raises(HTTPException) as exc:
            auth_service.authenticate_user(
                db_session,
                sample_student.email,
                "WrongPassword123"
            )

        assert exc.value.status_code == 401
        assert "incorrect" in exc.value.detail.lower()

    def test_authenticate_nonexistent_user(self, db_session):
        """Test authentication with nonexistent user fails."""
        with pytest.raises(HTTPException) as exc:
            auth_service.authenticate_user(
                db_session,
                "nonexistent@test.com",
                "Password123"
            )

        assert exc.value.status_code == 401

    def test_authenticate_suspended_user(self, db_session):
        """Test authentication with suspended user fails."""
        user = User(
            user_id="user_suspended",
            email="suspended@test.com",
            password_hash="$2b$12$test",
            first_name="Suspended",
            last_name="User",
            role=UserRole.STUDENT,
            status=UserStatus.SUSPENDED,
        )
        db_session.add(user)
        db_session.commit()

        with pytest.raises(HTTPException) as exc:
            auth_service.authenticate_user(
                db_session,
                "suspended@test.com",
                "Password123"
            )

        assert exc.value.status_code == 403
        assert "suspended" in exc.value.detail.lower()


@pytest.mark.unit
@pytest.mark.auth
class TestTokenManagement:
    """Test token generation and refresh."""

    def test_create_tokens_success(self, db_session, sample_student):
        """Test successful token creation."""
        tokens = auth_service.create_user_tokens(
            db_session,
            sample_student,
            ip_address="127.0.0.1",
            user_agent="TestClient"
        )

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == 1440 * 60  # 24 hours in seconds

    def test_session_created_on_login(self, db_session, sample_student):
        """Test that session is created in database."""
        auth_service.create_user_tokens(
            db_session,
            sample_student,
            ip_address="127.0.0.1",
            user_agent="TestClient"
        )

        from app.models.session import Session as SessionModel
        session = db_session.query(SessionModel).filter(
            SessionModel.user_id == sample_student.user_id
        ).first()

        assert session is not None
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "TestClient"
        assert session.revoked is False


@pytest.mark.unit
@pytest.mark.auth
class TestLogout:
    """Test logout functionality."""

    def test_revoke_single_session(self, db_session, sample_student):
        """Test revoking a single session."""
        # Create a session
        tokens = auth_service.create_user_tokens(db_session, sample_student)

        # Revoke it
        auth_service.revoke_user_sessions(
            db_session,
            sample_student.user_id,
            all_sessions=False
        )

        from app.models.session import Session as SessionModel
        sessions = db_session.query(SessionModel).filter(
            SessionModel.user_id == sample_student.user_id,
            SessionModel.revoked == True
        ).all()

        assert len(sessions) >= 1

    def test_revoke_all_sessions(self, db_session, sample_student):
        """Test revoking all user sessions."""
        # Create multiple sessions
        auth_service.create_user_tokens(db_session, sample_student)
        auth_service.create_user_tokens(db_session, sample_student)

        # Revoke all
        auth_service.revoke_user_sessions(
            db_session,
            sample_student.user_id,
            all_sessions=True
        )

        from app.models.session import Session as SessionModel
        active_sessions = db_session.query(SessionModel).filter(
            SessionModel.user_id == sample_student.user_id,
            SessionModel.revoked == False
        ).count()

        assert active_sessions == 0
