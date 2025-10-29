"""
Content Metadata API endpoints.

Endpoints for checking content availability, retrieving metadata, and submitting feedback.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.content import (
    ContentCheckRequest,
    ContentCheckResponse,
    ContentMetadataResponse,
    ContentListResponse,
    ContentFeedbackSubmit,
    ContentFeedbackResponse,
    ContentFeedbackSummary,
)
from app.services import content_service
from app.utils.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/{cache_key}", response_model=dict)
async def get_content_metadata(
    cache_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get content metadata by cache key.

    **Returns**:
    - Complete content metadata
    - URLs for script, audio, video, captions, thumbnail
    - Generation status (completed or generating)
    - If generating: progress percentage and current stage
    - View count and completion statistics
    """
    content = content_service.get_content_by_cache_key(db, cache_key)

    # Build response based on status
    response = {
        "cache_key": content.cache_key,
        "topic_id": content.topic_id,
        "topic_name": content.topic.name if content.topic else content.topic_id,
        "interest": content.interest,
        "status": content.status,
        "title": content.title,
        "duration_seconds": content.duration_seconds,
        "views": content.views or 0,
    }

    if content.status == "completed":
        response.update({
            "script_url": content.script_url,
            "audio_url": content.audio_url,
            "video_url": content.video_url,
            "captions_url": content.captions_url,
            "thumbnail_url": content.thumbnail_url,
            "quality_levels": content.quality_levels or ["1080p", "720p", "480p"],
            "generated_at": content.generated_at,
            "avg_completion_rate": 0.73,  # TODO: Calculate from analytics
        })
    elif content.status in ["pending", "generating"]:
        response.update({
            "progress_percentage": 45,  # TODO: Get from request tracking
            "current_stage": "video_generation",
            "stages": {
                "nlu": {"status": "completed"},
                "script": {"status": "completed"},
                "audio": {"status": "completed"},
                "video": {"status": "in_progress", "progress": 45},
            },
            "estimated_completion_seconds": 120,
            "audio_url": content.audio_url,  # Fast Path available
            "script_url": content.script_url,
        })

    return response


@router.post("/check", response_model=ContentCheckResponse)
async def check_content_exists(
    check_data: ContentCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if content exists for a topic-interest combination.

    **Request Body**:
    - topic_id: Topic ID (required)
    - interest: Interest name (required)

    **Returns**:
    - cache_hit: True if content exists
    - cache_key: Cache key if content exists
    - status: Generation status (completed, generating, etc.)
    - video_url: Video URL if completed
    - message: Descriptive message
    """
    result = content_service.check_content_exists(
        db=db,
        topic_id=check_data.topic_id,
        interest=check_data.interest,
    )

    return result


@router.get("/recent", response_model=ContentListResponse)
async def get_recent_content(
    limit: int = 10,
    topic_id: Optional[str] = None,
    interest: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recently generated content.

    **Query Parameters**:
    - limit: Results limit (default: 10, max: 50)
    - topic_id: Optional filter by topic
    - interest: Optional filter by interest

    **Returns**:
    - List of recently generated content
    - Includes thumbnails, duration, and generation timestamp
    """
    if limit > 50:
        limit = 50

    student_id = current_user.user_id if current_user.role == "student" else None

    result = content_service.get_recent_content(
        db=db,
        limit=limit,
        topic_id=topic_id,
        interest=interest,
        student_id=student_id,
    )

    # Format content list
    formatted_content = []
    for content in result["content"]:
        formatted_content.append({
            "cache_key": content.cache_key,
            "topic_name": content.topic.name if content.topic else content.topic_id,
            "interest": content.interest,
            "thumbnail_url": content.thumbnail_url,
            "duration_seconds": content.duration_seconds,
            "generated_at": content.generated_at,
        })

    return {
        "content": formatted_content,
        "pagination": result["pagination"],
    }


@router.post("/{cache_key}/feedback", response_model=ContentFeedbackResponse)
async def submit_content_feedback(
    cache_key: str,
    feedback_data: ContentFeedbackSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit feedback for content.

    **Request Body**:
    - rating: Rating from 1-5 stars (required)
    - feedback_type: Type of feedback (optional)
      - helpful: Content was helpful
      - confusing: Content was confusing
      - inaccurate: Content has inaccuracies
      - inappropriate: Content is inappropriate
      - technical_issue: Technical problems (audio, video, etc.)
    - comments: Optional text feedback (max 1000 chars)

    **Returns**:
    - Feedback confirmation
    - Submitted timestamp
    """
    result = content_service.submit_content_feedback(
        db=db,
        cache_key=cache_key,
        student_id=current_user.user_id,
        rating=feedback_data.rating,
        feedback_type=feedback_data.feedback_type,
        comments=feedback_data.comments,
    )

    return result


@router.get("/{cache_key}/feedback", response_model=ContentFeedbackSummary)
async def get_content_feedback_summary(
    cache_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get feedback summary for content.

    **Returns**:
    - Total ratings count
    - Average rating
    - Rating distribution (1-5 stars)
    - Feedback type breakdown
    """
    result = content_service.get_content_feedback_summary(db=db, cache_key=cache_key)

    return result
