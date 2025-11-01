"""
Pydantic schemas for admin operations.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_serializer
from typing import Optional, List, Any
from datetime import datetime


# User Management Schemas


class UserCreate(BaseModel):
    """Create a single user."""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(student|teacher|admin)$")
    grade_level: Optional[int] = Field(None, ge=9, le=12)
    school_id: Optional[str] = None
    organization_id: Optional[str] = None
    send_invitation: bool = False


class UserUpdate(BaseModel):
    """Update user profile."""

    role: Optional[str] = Field(None, pattern="^(student|teacher|admin)$")
    grade_level: Optional[int] = Field(None, ge=9, le=12)
    subjects: Optional[List[str]] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)


class UserResponse(BaseModel):
    """User response."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    grade_level: Optional[int]
    school_id: Optional[str]
    organization_id: Optional[str]
    archived: bool  # Internal field from model
    created_at: datetime
    last_login_at: Optional[datetime]

    @model_serializer(mode="wrap")
    def _serialize(self, serializer: Any, info: Any) -> dict:
        """Convert archived to is_active on serialization."""
        data = serializer(self)
        # Replace archived with is_active (inverted)
        if "archived" in data:
            data["is_active"] = not data.pop("archived")
        return data

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""

    users: List[UserResponse]
    pagination: dict


# Bulk Upload Schemas


class BulkUploadResponse(BaseModel):
    """Bulk upload results."""

    upload_id: str
    total_rows: int
    successful: int
    failed: int
    duration_seconds: float
    results: dict


# Account Request Schemas


class RequestResponse(BaseModel):
    """Account request response."""

    request_id: str
    student_first_name: str
    student_last_name: str
    student_email: str
    grade_level: int
    class_id: Optional[str]
    class_name: Optional[str]
    requested_by_id: str
    requested_by_name: str
    requested_at: datetime
    notes: Optional[str]
    status: str

    class Config:
        from_attributes = True


class RequestListResponse(BaseModel):
    """Paginated request list response."""

    requests: List[dict]
    pagination: dict


class ApproveRequestResponse(BaseModel):
    """Request approval response."""

    request_id: str
    status: str
    user_created: dict
    approved_at: datetime
    approved_by: str
    invitation_sent: bool


class DenyRequestRequest(BaseModel):
    """Request denial request."""

    reason: str = Field(..., min_length=1, max_length=500)


class DenyRequestResponse(BaseModel):
    """Request denial response."""

    request_id: str
    status: str
    denied_at: datetime
    denied_by: str
    denial_reason: str
    teacher_notified: bool
