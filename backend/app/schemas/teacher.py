"""
Pydantic schemas for teacher endpoints.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime


# Class schemas
class CreateClassRequest(BaseModel):
    """Schema for creating a class."""

    name: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    grade_levels: Optional[List[int]] = Field(
        None, description="List of grade levels (9-12)"
    )

    @validator("grade_levels")
    def validate_grade_levels(cls, v):
        """Validate grade levels are between 9-12."""
        if v:
            for grade in v:
                if grade < 9 or grade > 12:
                    raise ValueError("Grade levels must be between 9 and 12")
        return v


class UpdateClassRequest(BaseModel):
    """Schema for updating a class."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    grade_levels: Optional[List[int]] = None

    @validator("grade_levels")
    def validate_grade_levels(cls, v):
        """Validate grade levels are between 9-12."""
        if v:
            for grade in v:
                if grade < 9 or grade > 12:
                    raise ValueError("Grade levels must be between 9 and 12")
        return v


class ClassResponse(BaseModel):
    """Schema for class response."""

    class_id: str
    teacher_id: str
    name: str
    subject: Optional[str]
    class_code: str
    description: Optional[str]
    grade_levels: Optional[List]
    school_id: Optional[str]
    organization_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    archived: bool

    class Config:
        from_attributes = True


# Roster schemas
class StudentInRoster(BaseModel):
    """Schema for student in class roster."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    grade_level: Optional[int]
    enrolled_at: datetime
    progress_summary: Optional[Dict] = None

    class Config:
        from_attributes = True


class RosterResponse(BaseModel):
    """Schema for class roster response."""

    class_id: str
    class_name: str
    total_students: int
    students: List[StudentInRoster]


# Student account request schemas
class StudentAccountRequestCreate(BaseModel):
    """Schema for creating student account request."""

    student_email: str = Field(..., description="Student's email address")
    student_first_name: str = Field(..., min_length=1, max_length=100)
    student_last_name: str = Field(..., min_length=1, max_length=100)
    grade_level: int = Field(..., ge=9, le=12)
    class_id: Optional[str] = Field(
        None, description="Auto-enroll in this class after approval"
    )
    notes: Optional[str] = Field(None, description="Notes for admin")


class BulkStudentAccountRequest(BaseModel):
    """Schema for bulk student account creation."""

    students: List[StudentAccountRequestCreate] = Field(..., min_items=1, max_items=50)

    @validator("students")
    def validate_unique_emails(cls, v):
        """Ensure student emails are unique in the batch."""
        emails = [s.student_email for s in v]
        if len(emails) != len(set(emails)):
            raise ValueError("Student emails must be unique")
        return v


class StudentAccountRequestResponse(BaseModel):
    """Schema for student account request response."""

    request_id: str
    requested_by: str
    student_email: str
    student_first_name: str
    student_last_name: str
    grade_level: int
    class_id: Optional[str]
    status: str  # pending, approved, rejected
    requested_at: datetime
    processed_at: Optional[datetime]
    created_user_id: Optional[str]

    class Config:
        from_attributes = True


# Dashboard schema
class ClassSummary(BaseModel):
    """Schema for class summary in dashboard."""

    class_id: str
    name: str
    subject: Optional[str]
    class_code: str
    student_count: int
    archived: bool
    created_at: datetime


class TeacherDashboard(BaseModel):
    """Schema for teacher dashboard data."""

    teacher_id: str
    total_classes: int
    active_classes: int
    total_students: int
    pending_requests: int
    classes: List[ClassSummary]
    recent_activity: Optional[List[Dict]] = None
