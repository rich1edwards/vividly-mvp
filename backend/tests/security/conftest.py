# Set TESTING environment variable BEFORE ANY imports
import os
os.environ["TESTING"] = "true"

"""
Security Test Configuration and Fixtures

Provides test database and users specifically for security tests.
Security tests use module-level TestClient, so we need session-scoped fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole, UserStatus
from app.models.class_model import Class
from app.utils.security import get_password_hash

# Test database URL (SQLite in-memory for security tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Consistent password for all test users: Password123!
TEST_PASSWORD = "Password123!"
TEST_PASSWORD_HASH = get_password_hash(TEST_PASSWORD)


# Session-scoped database engine and session for security tests
@pytest.fixture(scope="session")
def security_test_engine():
    """Create a session-scoped test database engine for security tests."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def security_test_session(security_test_engine):
    """Create a session-scoped database session for security tests."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=security_test_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_security_test_users(security_test_session):
    """
    Automatically create all test users needed for security tests.
    This runs ONCE per test session and creates:
    - 3 students
    - 2 teachers
    - 1 admin
    - 2 classes for teachers
    """
    # Create students
    student1 = User(
        user_id="user_student_001",
        email="student@test.com",
        password_hash=TEST_PASSWORD_HASH,
        first_name="Test",
        last_name="Student",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        grade_level=10,
        organization_id="org_test_001",
    )

    student2 = User(
        user_id="user_student_002",
        email="student1@test.com",
        password_hash=TEST_PASSWORD_HASH,
        first_name="Test",
        last_name="Student One",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        grade_level=10,
        organization_id="org_test_001",
    )

    student3 = User(
        user_id="student2_user_id",
        email="student2@test.com",
        password_hash=TEST_PASSWORD_HASH,
        first_name="Test",
        last_name="Student Two",
        role=UserRole.STUDENT,
        status=UserStatus.ACTIVE,
        grade_level=11,
        organization_id="org_test_001",
    )

    # Create teachers
    teacher1 = User(
        user_id="user_teacher_001",
        email="teacher@test.com",
        password_hash=get_password_hash("TeacherPassword123!"),
        first_name="Test",
        last_name="Teacher",
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE,
        organization_id="org_test_001",
    )

    teacher2 = User(
        user_id="user_teacher_002",
        email="teacher1@test.com",
        password_hash=get_password_hash("TeacherPassword123!"),
        first_name="Test",
        last_name="Teacher One",
        role=UserRole.TEACHER,
        status=UserStatus.ACTIVE,
        organization_id="org_test_001",
    )

    # Create admin
    admin = User(
        user_id="user_admin_001",
        email="admin@test.com",
        password_hash=get_password_hash("AdminPassword123!"),
        first_name="Test",
        last_name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        organization_id="org_test_001",
    )

    # Add all users to database
    security_test_session.add_all([student1, student2, student3, teacher1, teacher2, admin])
    security_test_session.commit()

    # Create classes for teachers
    class1 = Class(
        class_id="teacher1_class_id",
        teacher_id=teacher1.user_id,
        name="Test Physics Class",
        subject="Physics",
        class_code="PHYS-001",
        description="Test class for Teacher 1",
        grade_levels=[9, 10, 11],
        organization_id="org_test_001",
    )

    class2 = Class(
        class_id="teacher2_class_id",
        teacher_id=teacher2.user_id,
        name="Test Math Class",
        subject="Math",
        class_code="MATH-002",
        description="Test class for Teacher 2",
        grade_levels=[10, 11, 12],
        organization_id="org_test_001",
    )

    security_test_session.add_all([class1, class2])
    security_test_session.commit()

    # Override the get_db dependency in the app to use our security_test_session
    def override_get_db():
        try:
            yield security_test_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    return {
        "students": [student1, student2, student3],
        "teachers": [teacher1, teacher2],
        "admin": admin,
        "classes": [class1, class2],
    }
