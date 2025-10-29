"""
Student Service Schemas

Pydantic models for student endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class UpdateProfileRequest(BaseModel):
    """
    Student profile update request.

    Example:
        {
            "first_name": "Jonathan",
            "grade_level": 11
        }
    """

    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    grade_level: Optional[int] = Field(None, ge=9, le=12, description="Grade level (9-12)")


class InterestDetail(BaseModel):
    """
    Interest detail.

    Example:
        {
            "interest_id": "int_basketball",
            "name": "Basketball",
            "category": "sports",
            "icon_url": "https://cdn.vividly.edu/icons/basketball.svg",
            "selected_at": "2025-11-01T10:30:00Z"
        }
    """

    interest_id: str
    name: str
    category: str
    icon_url: Optional[str] = None
    selected_at: datetime


class ProgressSummary(BaseModel):
    """
    Student progress summary.

    Example:
        {
            "topics_completed": 5,
            "videos_watched": 12,
            "total_watch_time_minutes": 45,
            "streak_days": 3
        }
    """

    topics_completed: int = Field(0, description="Number of topics completed")
    videos_watched: int = Field(0, description="Number of videos watched")
    total_watch_time_minutes: int = Field(0, description="Total watch time in minutes")
    streak_days: int = Field(0, description="Current learning streak in days")
    last_active: Optional[datetime] = None


class StudentProfileResponse(BaseModel):
    """
    Student profile response.

    Example:
        {
            "student_id": "user_abc123",
            "email": "student@mnps.edu",
            "first_name": "John",
            "last_name": "Doe",
            "grade_level": 10,
            "school_id": "school_hillsboro_hs",
            "school_name": "Hillsboro High School",
            "interests": [...],
            "progress_summary": {...},
            "created_at": "2025-11-01T10:00:00Z"
        }
    """

    student_id: str
    email: str
    first_name: str
    last_name: str
    grade_level: int
    school_id: str
    school_name: Optional[str] = None
    interests: List[InterestDetail] = []
    progress_summary: ProgressSummary
    created_at: datetime


class UpdateInterestsRequest(BaseModel):
    """
    Update student interests request.

    Example:
        {
            "interest_ids": ["int_basketball", "int_music", "int_coding"]
        }
    """

    interest_ids: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="List of interest IDs (1-5 interests)"
    )

    @validator("interest_ids")
    def validate_no_duplicates(cls, v):
        """Ensure no duplicate interests."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate interests are not allowed")
        return v


class InterestsResponse(BaseModel):
    """
    Student interests response.

    Example:
        {
            "student_id": "user_abc123",
            "interests": [...]
        }
    """

    student_id: str
    interests: List[InterestDetail]


class UpdateInterestsResponse(BaseModel):
    """
    Update interests response.

    Example:
        {
            "student_id": "user_abc123",
            "interests": [...],
            "updated_at": "2025-11-04T14:20:00Z"
        }
    """

    student_id: str
    interests: List[InterestDetail]
    updated_at: datetime


class ActivityItem(BaseModel):
    """
    Single activity item.

    Example:
        {
            "activity_id": "act_001",
            "type": "video_completed",
            "topic_id": "topic_phys_mech_newton_3",
            "topic_name": "Newton's Third Law",
            "interest": "basketball",
            "completed_at": "2025-11-04T09:15:00Z",
            "watch_duration_seconds": 180
        }
    """

    activity_id: str
    type: str  # "video_completed", "topic_started", "topic_completed"
    topic_id: str
    topic_name: str
    interest: Optional[str] = None
    completed_at: datetime
    watch_duration_seconds: Optional[int] = None


class TopicProgress(BaseModel):
    """
    Topic progress detail.

    Example:
        {
            "topic_id": "topic_phys_mech_newton_1",
            "name": "Newton's First Law",
            "status": "completed",
            "completed_at": "2025-11-02T10:00:00Z",
            "progress_percentage": 100
        }
    """

    topic_id: str
    name: str
    status: str  # "not_started", "in_progress", "completed"
    completed_at: Optional[datetime] = None
    progress_percentage: Optional[int] = None


class SubjectProgress(BaseModel):
    """
    Subject progress with topics.

    Example:
        {
            "subject": "Physics",
            "unit": "Mechanics",
            "completed": 3,
            "total": 10,
            "topics": [...]
        }
    """

    subject: str
    unit: str
    completed: int
    total: int
    topics: List[TopicProgress]


class ProgressResponse(BaseModel):
    """
    Student progress response.

    Example:
        {
            "student_id": "user_abc123",
            "summary": {...},
            "recent_activity": [...],
            "topic_matrix": {...}
        }
    """

    student_id: str
    summary: ProgressSummary
    recent_activity: List[ActivityItem]
    topic_matrix: dict  # Nested dict: Subject -> Unit -> TopicProgress[]


class ErrorDetail(BaseModel):
    """
    Validation error detail.

    Example:
        {
            "field": "interest_ids",
            "constraint": "length",
            "min": 1,
            "max": 5,
            "actual": 6
        }
    """

    field: str
    constraint: str
    min: Optional[int] = None
    max: Optional[int] = None
    actual: Optional[int] = None
    message: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """
    Validation error response.

    Example:
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "You must select between 1 and 5 interests",
                "details": {...}
            }
        }
    """

    error: dict
