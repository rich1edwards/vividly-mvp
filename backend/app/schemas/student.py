"""
Student service schemas.

Pydantic models for student service layer.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class StudentProfileUpdate(BaseModel):
    """Student profile update request."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade_level: Optional[int] = Field(None, ge=9, le=12)


class StudentProfile(BaseModel):
    """Complete student profile."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    grade_level: Optional[int] = None
    school_id: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    interests: List[dict] = []
    enrolled_classes: List[dict] = []
    progress_summary: dict = {}

    class Config:
        from_attributes = True


class InterestBase(BaseModel):
    """Base interest schema."""

    interest_id: str
    name: str
    category: str


class StudentInterestsUpdate(BaseModel):
    """Update student interests (1-5 interests)."""

    interest_ids: List[str] = Field(..., min_length=1, max_length=5)

    @field_validator("interest_ids", mode="after")
    @classmethod
    def validate_unique_interests(cls, v: List[str]) -> List[str]:
        """Ensure interest IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Interest IDs must be unique")
        return v


class TopicProgress(BaseModel):
    """Topic progress details."""

    topic_id: str
    topic_name: str
    subject: str
    status: str
    progress_percentage: int = 0
    videos_watched: int = 0
    total_watch_time_seconds: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StudentActivity(BaseModel):
    """Student activity log entry."""

    activity_id: str
    activity_type: str
    created_at: datetime
    topic_id: Optional[str] = None
    duration_seconds: Optional[int] = None


class LearningProgress(BaseModel):
    """Complete learning progress."""

    topics: List[TopicProgress] = []
    recent_activity: List[StudentActivity] = []
    total_topics_started: int = 0
    total_topics_completed: int = 0
    total_watch_time_seconds: int = 0
    learning_streak_days: int = 0


class JoinClassRequest(BaseModel):
    """Join class by code request."""

    class_code: str = Field(..., min_length=1, max_length=50)
