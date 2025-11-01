"""
Teacher Service Schemas

Pydantic models for teacher endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TeacherProfileResponse(BaseModel):
    """
    Teacher profile response.

    Example:
        {
            "teacher_id": "user_xyz789",
            "email": "teacher@mnps.edu",
            "first_name": "Jane",
            "last_name": "Smith",
            "school_id": "school_hillsboro_hs",
            "school_name": "Hillsboro High School",
            "subjects": ["Physics", "Chemistry"],
            "total_students": 87,
            "total_classes": 3,
            "created_at": "2025-09-01T10:00:00Z"
        }
    """

    teacher_id: str
    email: str
    first_name: str
    last_name: str
    school_id: str
    school_name: Optional[str] = None
    subjects: List[str] = []
    total_students: int = 0
    total_classes: int = 0
    created_at: datetime


class ClassSummary(BaseModel):
    """
    Class summary for list view.

    Example:
        {
            "class_id": "class_001",
            "name": "Physics 101 - Period 1",
            "subject": "Physics",
            "grade_level": 10,
            "student_count": 28,
            "active_students_7d": 24,
            "created_at": "2025-09-01T10:00:00Z"
        }
    """

    class_id: str
    name: str
    subject: str
    grade_level: int
    student_count: int
    active_students_7d: int = 0
    created_at: datetime


class PaginationInfo(BaseModel):
    """
    Pagination metadata.

    Example:
        {
            "next_cursor": "xyz789",
            "has_more": true,
            "total_count": 3
        }
    """

    next_cursor: Optional[str] = None
    has_more: bool = False
    total_count: int


class ClassListResponse(BaseModel):
    """
    Teacher's classes list response.

    Example:
        {
            "classes": [...],
            "pagination": {...}
        }
    """

    classes: List[ClassSummary]
    pagination: PaginationInfo


class CreateClassRequest(BaseModel):
    """
    Create class request.

    Example:
        {
            "name": "Physics 101 - Period 1",
            "subject": "Physics",
            "grade_level": 10,
            "description": "Introduction to Mechanics"
        }
    """

    name: str = Field(..., min_length=1, max_length=200, description="Class name")
    subject: str = Field(
        ..., min_length=1, max_length=100, description="Subject (e.g., Physics)"
    )
    grade_level: int = Field(..., ge=9, le=12, description="Grade level (9-12)")
    description: Optional[str] = Field(
        None, max_length=1000, description="Class description"
    )

    @validator("subject")
    def validate_subject(cls, v):
        """Validate subject is in allowed list."""
        allowed_subjects = [
            "Physics",
            "Chemistry",
            "Biology",
            "Math",
            "Algebra",
            "Geometry",
            "Calculus",
            "Computer Science",
            "Engineering",
        ]
        if v not in allowed_subjects:
            raise ValueError(f"Subject must be one of: {', '.join(allowed_subjects)}")
        return v


class UpdateClassRequest(BaseModel):
    """
    Update class request.

    Example:
        {
            "name": "Physics 101 - Period 2",
            "description": "Updated description"
        }
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Class name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Class description"
    )


class ClassResponse(BaseModel):
    """
    Class creation/update response.

    Example:
        {
            "class_id": "class_001",
            "name": "Physics 101 - Period 1",
            "subject": "Physics",
            "grade_level": 10,
            "description": "Introduction to Mechanics",
            "class_code": "PHYS-ABC-123",
            "teacher_id": "user_xyz789",
            "student_count": 0,
            "created_at": "2025-11-04T10:00:00Z"
        }
    """

    class_id: str
    name: str
    subject: str
    grade_level: int
    description: Optional[str] = None
    class_code: str
    teacher_id: str
    student_count: int = 0
    created_at: datetime


class StudentInClass(BaseModel):
    """
    Student information in class detail view.

    Example:
        {
            "student_id": "user_abc123",
            "name": "John Doe",
            "email": "john.doe@mnps.edu",
            "last_active": "2025-11-04T09:15:00Z",
            "videos_watched": 12,
            "topics_completed": 5
        }
    """

    student_id: str
    name: str
    email: str
    last_active: Optional[datetime] = None
    videos_watched: int = 0
    topics_completed: int = 0


class ClassDetailResponse(BaseModel):
    """
    Detailed class information with students.

    Example:
        {
            "class_id": "class_001",
            "name": "Physics 101 - Period 1",
            "subject": "Physics",
            "grade_level": 10,
            "description": "Introduction to Mechanics",
            "class_code": "PHYS-ABC-123",
            "student_count": 28,
            "students": [...],
            "created_at": "2025-09-01T10:00:00Z"
        }
    """

    class_id: str
    name: str
    subject: str
    grade_level: int
    description: Optional[str] = None
    class_code: str
    student_count: int
    students: List[StudentInClass]
    created_at: datetime


class CreateStudentRequestRequest(BaseModel):
    """
    Create student account request.

    Example:
        {
            "student_first_name": "Michael",
            "student_last_name": "Johnson",
            "student_email": "michael.johnson@mnps.edu",
            "grade_level": 10,
            "class_id": "class_001",
            "notes": "Transfer student from East High"
        }
    """

    student_first_name: str = Field(
        ..., min_length=1, max_length=100, description="Student first name"
    )
    student_last_name: str = Field(
        ..., min_length=1, max_length=100, description="Student last name"
    )
    student_email: str = Field(..., description="Student email address")
    grade_level: int = Field(..., ge=9, le=12, description="Grade level (9-12)")
    class_id: str = Field(..., description="Class ID to add student to")
    notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes for approver"
    )

    @validator("student_email")
    def validate_email_format(cls, v):
        """Basic email validation."""
        import re

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v


class StudentRequestResponse(BaseModel):
    """
    Student account request response.

    Example:
        {
            "request_id": "req_001",
            "student_first_name": "Michael",
            "student_last_name": "Johnson",
            "student_email": "michael.johnson@mnps.edu",
            "grade_level": 10,
            "class_id": "class_001",
            "status": "pending",
            "requested_by": "user_xyz789",
            "requested_at": "2025-11-04T10:00:00Z",
            "approver_id": "user_admin123",
            "approver_name": "Principal Jane Smith"
        }
    """

    request_id: str
    student_first_name: str
    student_last_name: str
    student_email: str
    grade_level: int
    class_id: str
    status: str  # "pending", "approved", "rejected"
    requested_by: str
    requested_at: datetime
    approver_id: str
    approver_name: Optional[str] = None


class StudentRequestSummary(BaseModel):
    """
    Student request summary for list view.

    Example:
        {
            "request_id": "req_001",
            "student_name": "Michael Johnson",
            "status": "pending",
            "requested_at": "2025-11-04T10:00:00Z"
        }
    """

    request_id: str
    student_name: str
    status: str
    requested_at: datetime


class StudentRequestListResponse(BaseModel):
    """
    List of student account requests.

    Example:
        {
            "requests": [...],
            "pagination": {...}
        }
    """

    requests: List[StudentRequestSummary]
    pagination: PaginationInfo


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Example:
        {
            "error": {
                "code": "FORBIDDEN",
                "message": "Only teachers can access this endpoint"
            }
        }
    """

    error: dict
