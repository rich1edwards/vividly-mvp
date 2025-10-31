"""
Content Generation Request/Response Schemas.

Schemas for content generation API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ContentGenerationRequest(BaseModel):
    """Request to generate content from a natural language query."""

    student_query: str = Field(
        ...,
        description="Student's natural language query about what they want to learn",
        min_length=5,
        max_length=500,
        examples=["Explain photosynthesis using plants I see every day"]
    )
    student_id: str = Field(
        ...,
        description="Student user ID",
        examples=["student_123"]
    )
    grade_level: Optional[int] = Field(
        None,
        description="Student's grade level (1-12)",
        ge=1,
        le=12
    )
    interest: Optional[str] = Field(
        None,
        description="Interest to personalize content with",
        max_length=100,
        examples=["basketball", "video games", "cooking"]
    )


class ContentGenerationResponse(BaseModel):
    """Response from content generation request."""

    status: str = Field(
        ...,
        description="Generation status: pending, generating, completed, failed",
        examples=["pending", "generating", "completed"]
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique request ID for tracking generation progress"
    )
    cache_key: Optional[str] = Field(
        None,
        description="Cache key to retrieve content once generated"
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        examples=["Content generation started", "Content generation completed"]
    )
    content_url: Optional[str] = Field(
        None,
        description="URL to access generated content (if completed)"
    )
    estimated_completion_seconds: Optional[int] = Field(
        None,
        description="Estimated seconds until content generation completes",
        ge=0
    )
