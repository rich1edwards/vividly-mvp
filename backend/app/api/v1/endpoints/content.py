"""
Content Metadata API endpoints.

Endpoints for checking content availability, retrieving metadata, and submitting feedback.
Sprint 3.2.1: Added signed URL generation for secure content delivery.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

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
from app.schemas.content_delivery import (
    SignedURLRequest,
    SignedURLResponse,
    BatchURLRequest,
    BatchURLResponse,
    ContentAccessStats,
)
from app.schemas.content_tracking import (
    ViewTrackingRequest,
    ProgressTrackingRequest,
    CompletionTrackingRequest,
    CompletionResponse,
    ContentAnalytics,
)
from app.services import content_service
from app.services.content_delivery_service import ContentDeliveryService
from app.services.content_tracking_service import ContentTrackingService
from app.utils.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)


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


# ============================================================================
# Story 3.2.1: Signed URL Generation for Content Delivery
# ============================================================================

def get_content_delivery_service() -> ContentDeliveryService:
    """
    Dependency to get content delivery service instance.

    For production: Inject GCS client
    For testing: Can inject mocks
    """
    # TODO: In production, initialize with actual GCS client
    # from google.cloud import storage
    # gcs_client = storage.Client()
    return ContentDeliveryService(gcs_client=None)


@router.get(
    "/{cache_key}/url",
    response_model=SignedURLResponse,
    summary="Generate signed URL for content asset",
    description="""
    Generate time-limited signed URL for secure content delivery.

    **Security:**
    - URLs expire after 15 minutes (default)
    - Signed with GCS credentials
    - Cannot be tampered with

    **Supported Asset Types:**
    - video: MP4 video file (with quality selection)
    - audio: MP3 audio file
    - script: JSON script file
    - thumbnail: JPG thumbnail image

    **Quality Levels (video only):**
    - 1080p: Full HD (default)
    - 720p: HD
    - 480p: SD
    """,
    status_code=status.HTTP_200_OK
)
async def get_content_url(
    cache_key: str,
    asset_type: str = "video",
    quality: str = "1080p",
    current_user: User = Depends(get_current_user),
    delivery_service: ContentDeliveryService = Depends(get_content_delivery_service)
):
    """
    Generate signed URL for content asset.

    Args:
        cache_key: Content cache key
        asset_type: Asset type (video, audio, script, thumbnail)
        quality: Quality level for video (1080p, 720p, 480p)
        current_user: Authenticated user
        delivery_service: Content delivery service

    Returns:
        SignedURLResponse with URL and metadata
    """
    try:
        result = await delivery_service.generate_signed_url(
            cache_key=cache_key,
            asset_type=asset_type,
            quality=quality
        )

        return SignedURLResponse(**result)

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        logger.error(f"Content not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content asset not found"
        )
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signed URL"
        )


@router.post(
    "/urls/batch",
    response_model=BatchURLResponse,
    summary="Generate multiple signed URLs in batch",
    description="""
    Generate multiple signed URLs in a single request.

    Useful for fetching all assets (video, audio, script, thumbnail) for a content piece at once.

    **Limits:**
    - Maximum 10 URLs per batch
    - All URLs expire after 15 minutes
    """,
    status_code=status.HTTP_200_OK
)
async def get_batch_urls(
    request: BatchURLRequest,
    current_user: User = Depends(get_current_user),
    delivery_service: ContentDeliveryService = Depends(get_content_delivery_service)
):
    """
    Generate multiple signed URLs in batch.

    Args:
        request: Batch URL request with list of requests
        current_user: Authenticated user
        delivery_service: Content delivery service

    Returns:
        BatchURLResponse with list of signed URLs
    """
    try:
        result = await delivery_service.generate_batch_urls(
            requests=[req.model_dump() for req in request.requests]
        )

        return BatchURLResponse(**result)

    except Exception as e:
        logger.error(f"Failed to generate batch URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch URLs"
        )


@router.get(
    "/delivery/stats",
    response_model=ContentAccessStats,
    summary="Get content delivery statistics",
    description="""
    Get statistics about content URL generation and access patterns.

    Useful for monitoring and analytics.
    """,
    status_code=status.HTTP_200_OK
)
async def get_delivery_stats(
    current_user: User = Depends(get_current_user),
    delivery_service: ContentDeliveryService = Depends(get_content_delivery_service)
):
    """
    Get content delivery statistics.

    Args:
        current_user: Authenticated user
        delivery_service: Content delivery service

    Returns:
        ContentAccessStats with statistics
    """
    try:
        stats = delivery_service.get_access_stats()
        return ContentAccessStats(**stats)

    except Exception as e:
        logger.error(f"Failed to get delivery stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery statistics"
        )


# ============================================================================
# Story 3.2.2: Content Access Tracking
# ============================================================================

def get_tracking_service() -> ContentTrackingService:
    """Dependency to get content tracking service instance."""
    return ContentTrackingService()


@router.post(
    "/{cache_key}/view",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Track content view event",
    description="""
    Track when a student starts watching content.

    Called by frontend when video playback begins.
    Logs view event for analytics and increments view count.
    """
)
async def track_view(
    cache_key: str,
    request: ViewTrackingRequest,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db)
):
    """
    Track content view event.

    Args:
        cache_key: Content cache key
        request: View tracking request with quality, device, browser
        current_user: Authenticated user
        tracking_service: Tracking service
        db: Database session

    Returns:
        204 No Content on success
    """
    success = tracking_service.track_view(
        db=db,
        cache_key=cache_key,
        student_id=current_user.user_id,
        quality=request.quality,
        device_type=request.device_type,
        browser=request.browser
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    return None


@router.post(
    "/{cache_key}/progress",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Track playback progress",
    description="""
    Track student's playback progress.

    Called periodically by frontend (e.g., every 10 seconds) during playback.
    Updates student progress record with current position.
    """
)
async def track_progress(
    cache_key: str,
    request: ProgressTrackingRequest,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db)
):
    """
    Track playback progress.

    Args:
        cache_key: Content cache key
        request: Progress tracking request
        current_user: Authenticated user
        tracking_service: Tracking service
        db: Database session

    Returns:
        204 No Content on success
    """
    success = tracking_service.track_progress(
        db=db,
        cache_key=cache_key,
        student_id=current_user.user_id,
        current_time_seconds=request.current_time_seconds,
        duration_seconds=request.duration_seconds,
        playback_speed=request.playback_speed,
        paused=request.paused
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    return None


@router.post(
    "/{cache_key}/complete",
    response_model=CompletionResponse,
    summary="Mark content as completed",
    description="""
    Mark content as completed by student.

    Called by frontend when student finishes watching content (>=80% completion).
    Updates progress to COMPLETED status and checks for achievements.
    """
)
async def track_completion(
    cache_key: str,
    request: CompletionTrackingRequest,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db)
):
    """
    Mark content as completed.

    Args:
        cache_key: Content cache key
        request: Completion tracking request
        current_user: Authenticated user
        tracking_service: Tracking service
        db: Database session

    Returns:
        CompletionResponse with achievement and streak info
    """
    result = tracking_service.track_completion(
        db=db,
        cache_key=cache_key,
        student_id=current_user.user_id,
        watch_duration_seconds=request.watch_duration_seconds,
        completion_percentage=request.completion_percentage,
        skipped_segments=request.skipped_segments
    )

    return CompletionResponse(**result)


@router.get(
    "/{cache_key}/analytics",
    response_model=ContentAnalytics,
    summary="Get content analytics",
    description="""
    Get analytics data for content.

    Returns view counts, completion rates, and engagement metrics.
    Useful for teachers and admins to understand content performance.
    """
)
async def get_content_analytics(
    cache_key: str,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db)
):
    """
    Get content analytics.

    Args:
        cache_key: Content cache key
        current_user: Authenticated user
        tracking_service: Tracking service
        db: Database session

    Returns:
        ContentAnalytics with view and engagement metrics
    """
    analytics = tracking_service.get_content_analytics(
        db=db,
        cache_key=cache_key
    )

    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    return ContentAnalytics(**analytics)
