"""
StudentRequest model for account approval workflow.
"""
from sqlalchemy import Column, String, Enum, TIMESTAMP, Integer, Text, ForeignKey
from sqlalchemy import JSON
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class RequestStatus(str, enum.Enum):
    """Request status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StudentRequest(Base):
    """
    StudentRequest model for teacher-initiated student account requests.

    Corresponds to database table: student_request
    """

    __tablename__ = "student_request"

    # Primary key
    request_id = Column(String(100), primary_key=True, index=True)

    # Request details
    requested_by = Column(String(100), ForeignKey('users.user_id'), nullable=False, index=True)  # teacher user_id
    approver_id = Column(String(100), ForeignKey('users.user_id'), nullable=True, index=True)  # admin user_id

    # Student details (to be created)
    student_email = Column(String(255), nullable=False)
    student_first_name = Column(String(100), nullable=False)
    student_last_name = Column(String(100), nullable=False)
    grade_level = Column(Integer, nullable=False)
    class_id = Column(String(100), ForeignKey('classes.class_id'), nullable=True)  # Auto-enroll in this class

    # Organization context
    school_id = Column(String(100), nullable=True)
    organization_id = Column(String(100), nullable=True)

    # Request status
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING, index=True)

    # Notes and metadata
    notes = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True, default={})

    # Timestamps
    requested_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)
    processed_at = Column(TIMESTAMP, nullable=True)

    # Created user (if approved)
    created_user_id = Column(String(100), ForeignKey('users.user_id'), nullable=True)

    def __repr__(self) -> str:
        return f"<StudentRequest {self.student_email} status={self.status}>"
