"""
Pydantic schemas for content metadata operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Content Metadata Schemas

class ContentCheckRequest(BaseModel):
    """Request to check if content exists."""
    topic_id: str
    interest: str


class ContentCheckResponse(BaseModel):
    """Response for content existence check."""
    cache_hit: bool
    cache_key: Optional[str]
    status: Optional[str]
    video_url: Optional[str]
    message: Optional[str]
    metadata: Optional[dict] = None


class ContentMetadataResponse(BaseModel):
    """Content metadata response."""
    cache_key: str
    topic_id: str
    topic_name: str
    interest: str
    status: str
    title: Optional[str]
    duration_seconds: Optional[int]
    script_url: Optional[str]
    audio_url: Optional[str]
    video_url: Optional[str]
    captions_url: Optional[str]
    thumbnail_url: Optional[str]
    quality_levels: List[str] = []
    generated_at: Optional[datetime]
    views: int = 0
    avg_completion_rate: float = 0.0

    # For generating status
    progress_percentage: Optional[int] = None
    current_stage: Optional[str] = None
    stages: Optional[dict] = None
    estimated_completion_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class ContentSummary(BaseModel):
    """Summary of content for lists."""
    cache_key: str
    topic_name: str
    interest: str
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    generated_at: datetime

    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    """Content list response."""
    content: List[dict]
    pagination: dict


# Content Feedback Schemas

class ContentFeedbackSubmit(BaseModel):
    """Submit content feedback."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    feedback_type: Optional[str] = Field(
        None,
        pattern="^(helpful|confusing|inaccurate|inappropriate|technical_issue)$",
    )
    comments: Optional[str] = Field(None, max_length=1000)


class ContentFeedbackResponse(BaseModel):
    """Feedback submission response."""
    cache_key: str
    feedback_recorded: bool
    rating: int
    feedback_type: Optional[str]
    submitted_at: datetime


class ContentFeedbackSummary(BaseModel):
    """Feedback summary for content."""
    cache_key: str
    total_ratings: int
    average_rating: float
    rating_distribution: dict
    feedback_types: dict
