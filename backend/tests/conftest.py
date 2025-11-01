"""
Pytest configuration and fixtures for testing.
"""
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Set test environment variables BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["DEBUG"] = "True"
os.environ["CORS_ORIGINS"] = '["http://localhost"]'
os.environ["APP_NAME"] = "Vividly API Test"

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User, UserRole, UserStatus
from app.models.session import Session as SessionModel
from app.models.class_model import Class
from app.models.interest import Interest, StudentInterest
from app.models.progress import Topic, ProgressStatus
from app.utils.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from datetime import datetime, timedelta


# Test database URL (SQLite in-memory for fast testing)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_interests(db_session) -> list[Interest]:
    """Create sample interests for testing."""
    interests = [
        Interest(interest_id="int_basketball", name="Basketball", category="sports"),
        Interest(interest_id="int_coding", name="Coding", category="technology"),
        Interest(interest_id="int_music", name="Music", category="arts"),
        Interest(interest_id="int_reading", name="Reading", category="other"),
        Interest(interest_id="int_gaming", name="Gaming", category="technology"),
    ]
    for interest in interests:
        db_session.add(interest)
    db_session.commit()
    return interests


@pytest.fixture
def sample_topics(db_session) -> list[Topic]:
    """Create sample topics for testing."""
    topics = [
        Topic(
            topic_id="topic_newton_1",
            subject="Physics",
            unit="Newton's Laws",
            name="Newton's First Law",
            topic_order=1,
        ),
        Topic(
            topic_id="topic_newton_2",
            subject="Physics",
            unit="Newton's Laws",
            name="Newton's Second Law",
            topic_order=2,
        ),
        Topic(
            topic_id="topic_newton_3",
            subject="Physics",
            unit="Newton's Laws",
            name="Newton's Third Law",
            topic_order=3,
        ),
    ]
    for topic in topics:
        db_session.add(topic)
    db_session.commit()
    return topics


@pytest.fixture
def sample_student(db_session) -> User:
    """Create a sample student user."""
    user = User(
        user_id="user_student_test_001",
        email="student@test.com",
        password_hash=get_password_hash("Password123"),
        first_name="Test",
        last_name="Student",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        grade_level=10,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_teacher(db_session) -> User:
    """Create a sample teacher user."""
    user = User(
        user_id="user_teacher_test_001",
        email="teacher@test.com",
        password_hash=get_password_hash("Password123"),
        first_name="Test",
        last_name="Teacher",
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_admin(db_session) -> User:
    """Create a sample admin user."""
    user = User(
        user_id="user_admin_test_001",
        email="admin@test.com",
        password_hash=get_password_hash("Password123"),
        first_name="Test",
        last_name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_class(db_session, sample_teacher) -> Class:
    """Create a sample class."""
    class_obj = Class(
        class_id="class_test_001",
        teacher_id=sample_teacher.user_id,
        name="Test Physics Class",
        subject="Physics",
        class_code="PHYS-ABC-123",
        description="Test class for physics",
        grade_levels=[9, 10, 11, 12],
    )
    db_session.add(class_obj)
    db_session.commit()
    db_session.refresh(class_obj)
    return class_obj


@pytest.fixture
def student_token(sample_student) -> str:
    """Generate access token for student."""
    return create_access_token(data={"sub": sample_student.user_id})


@pytest.fixture
def teacher_token(sample_teacher) -> str:
    """Generate access token for teacher."""
    return create_access_token(data={"sub": sample_teacher.user_id})


@pytest.fixture
def admin_token(sample_admin) -> str:
    """Generate access token for admin."""
    return create_access_token(data={"sub": sample_admin.user_id})


@pytest.fixture
def student_headers(student_token) -> dict:
    """Generate authorization headers for student."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def teacher_headers(teacher_token) -> dict:
    """Generate authorization headers for teacher."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def admin_headers(admin_token) -> dict:
    """Generate authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}
