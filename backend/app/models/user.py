"""
User model.
"""
from sqlalchemy import Column, String, Integer, Boolean, Enum, Text, TIMESTAMP
from sqlalchemy import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, enum.Enum):
    """User status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class User(Base):
    """User model for all user types (students, teachers, admins)."""

    __tablename__ = "users"

    # Primary key
    user_id = Column(String(100), primary_key=True, index=True)

    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Role and status
    role = Column(Enum(UserRole), nullable=False, index=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    # Student-specific fields
    grade_level = Column(Integer, nullable=True)  # For students: 9-12

    # Organization
    school_id = Column(String(100), nullable=True)
    organization_id = Column(String(100), nullable=True)

    # Teacher-specific data (JSON for flexibility)
    teacher_data = Column(JSON, nullable=True, default={})

    # User settings (JSON)
    settings = Column(JSON, nullable=True, default={})

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(TIMESTAMP, nullable=True)

    # Soft delete
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    student_interests = relationship(
        "StudentInterest", back_populates="user", cascade="all, delete-orphan"
    )
    student_progress = relationship(
        "StudentProgress", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
