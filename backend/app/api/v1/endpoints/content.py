"""
Content Metadata API endpoints.

Endpoints for checking content availability, retrieving metadata, and submitting feedback.
Sprint 3.2.1: Added signed URL generation for secure content delivery.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging
import uuid

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
from app.schemas.content_generation import (
    ContentGenerationRequest,
    ContentGenerationResponse,
)
from app.services import content_service
from app.services.content_delivery_service import ContentDeliveryService
from app.services.content_tracking_service import ContentTrackingService
from app.services.content_generation_service import ContentGenerationService
from app.services import interest_service
from app.services.request_monitoring_service import (
    get_monitoring_service,
    RequestMonitoringService,
)
from app.services.pubsub_service import get_pubsub_service
from app.services.content_request_service import ContentRequestService
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
        "cache_key": content.content_id,  # Use content_id as cache_key
        "topic_id": content.topic_id,
        "topic_name": content.topic.name if content.topic else content.topic_id,
        "interest": content.interest,
        "status": content.status,
        "title": content.title,
        "duration_seconds": content.duration_seconds,
        "views": content.views or 0,
    }

    if content.status == "completed":
        response.update(
            {
                "script_url": content.script_url,
                "audio_url": content.audio_url,
                "video_url": content.video_url,
                "captions_url": content.captions_url,
                "thumbnail_url": content.thumbnail_url,
                "quality_levels": content.quality_levels or ["1080p", "720p", "480p"],
                "generated_at": content.generated_at,
                "avg_completion_rate": 0.73,  # TODO: Calculate from analytics
            }
        )
    elif content.status in ["pending", "generating"]:
        response.update(
            {
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
            }
        )

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
        formatted_content.append(
            {
                "cache_key": content.cache_key,
                "topic_name": content.topic.name if content.topic else content.topic_id,
                "interest": content.interest,
                "thumbnail_url": content.thumbnail_url,
                "duration_seconds": content.duration_seconds,
                "generated_at": content.generated_at,
            }
        )

    return {
        "content": formatted_content,
        "pagination": result["pagination"],
    }


@router.post(
    "/{cache_key}/feedback",
    response_model=ContentFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    status_code=status.HTTP_200_OK,
)
async def get_content_url(
    cache_key: str,
    asset_type: str = "video",
    quality: str = "1080p",
    current_user: User = Depends(get_current_user),
    delivery_service: ContentDeliveryService = Depends(get_content_delivery_service),
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
            cache_key=cache_key, asset_type=asset_type, quality=quality
        )

        return SignedURLResponse(**result)

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"Content not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content asset not found"
        )
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signed URL",
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
    status_code=status.HTTP_200_OK,
)
async def get_batch_urls(
    request: BatchURLRequest,
    current_user: User = Depends(get_current_user),
    delivery_service: ContentDeliveryService = Depends(get_content_delivery_service),
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
            detail="Failed to generate batch URLs",
        )


@router.get(
    "/delivery/stats",
    response_model=ContentAccessStats,
    summary="Get content delivery statistics",
    description="""
    Get statistics about content URL generation and access patterns.

    Useful for monitoring and analytics.
    """,
    status_code=status.HTTP_200_OK,
)
async def get_delivery_stats(
    current_user: User = Depends(get_current_user),
    delivery_service: ContentDeliveryService = Depends(get_content_delivery_service),
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
            detail="Failed to retrieve delivery statistics",
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
    """,
)
async def track_view(
    cache_key: str,
    request: ViewTrackingRequest,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db),
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
        browser=request.browser,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
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
    """,
)
async def track_progress(
    cache_key: str,
    request: ProgressTrackingRequest,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db),
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
        paused=request.paused,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
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
    """,
)
async def track_completion(
    cache_key: str,
    request: CompletionTrackingRequest,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db),
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
        skipped_segments=request.skipped_segments,
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
    """,
)
async def get_content_analytics(
    cache_key: str,
    current_user: User = Depends(get_current_user),
    tracking_service: ContentTrackingService = Depends(get_tracking_service),
    db: Session = Depends(get_db),
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
    analytics = tracking_service.get_content_analytics(db=db, cache_key=cache_key)

    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    return ContentAnalytics(**analytics)


@router.get(
    "/student/{student_id}/history",
    response_model=dict,
    summary="Get student content history",
    description="""
    Get student's content viewing history.

    Returns list of content the student has viewed or generated.
    Students can only access their own history.
    """,
    status_code=status.HTTP_200_OK,
)
async def get_student_history(
    student_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get student content history.

    Args:
        student_id: Student ID
        limit: Results limit (max 50)
        current_user: Authenticated user
        db: Database session

    Returns:
        Dict with content list
    """
    # Students can only access their own history
    if current_user.role == "student" and current_user.user_id != student_id:
        # Return empty result instead of forbidden
        return {
            "content": [],
            "pagination": {"has_more": False},
        }

    if limit > 50:
        limit = 50

    result = content_service.get_student_content_history(
        db=db, student_id=student_id, limit=limit
    )

    # Format content list
    formatted_content = []
    for content in result["content"]:
        # Extract interest name from interest_id (remove "int_" prefix)
        interest_name = (
            content.interest_id.replace("int_", "") if content.interest_id else None
        )

        formatted_content.append(
            {
                "content_id": content.content_id,
                "topic_id": content.topic_id,
                "topic_name": content.topic_id,  # Use topic_id as fallback for topic_name
                "interest": interest_name,
                "title": content.title,
                "status": content.status,
                "video_url": content.video_url,
                "thumbnail_url": content.thumbnail_url,
                "duration_seconds": content.duration_seconds,
                "generated_at": content.created_at,  # Use created_at column, not generated_at property
                "views": content.view_count
                or 0,  # Use view_count column, not views property
            }
        )

    return {
        "content": formatted_content,
        "pagination": result["pagination"],
    }


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate personalized educational content from a natural language query.

    **Request Body**:
    - student_query: What the student wants to learn (natural language)
    - student_id: Student user ID
    - grade_level: Student's grade level (optional)
    - interest: Interest to personalize with (optional)

    **Returns**:
    - status: Generation status (pending, generating)
    - request_id: ID to track generation progress
    - cache_key: Key to retrieve content once completed
    - message: Human-readable status message
    - estimated_completion_seconds: Estimated time until completion

    **Example Request**:
    ```json
    {
        "student_query": "Explain photosynthesis using basketball",
        "student_id": "student_123",
        "grade_level": 8,
        "interest": "basketball"
    }
    ```
    """
    try:
        # Generate unique correlation ID for distributed tracing
        correlation_id = f"req_{uuid.uuid4().hex[:16]}"
        monitoring_service = get_monitoring_service()

        # Track: Request Received
        monitoring_service.track_event(
            request_id=correlation_id,
            student_id=request.student_id,
            stage=RequestMonitoringService.STAGE_REQUEST_RECEIVED,
            status="completed",
            metadata={
                "student_query": request.student_query[:100],  # First 100 chars
                "grade_level": request.grade_level,
            },
        )

        # If interest not provided, use LLM to match student's interest to their request
        interest_to_use = request.interest
        if not interest_to_use and current_user.role == "student":
            logger.info(f"Matching interest for student {current_user.user_id}")

            # Track: Interest Matching Started
            monitoring_service.track_event(
                request_id=correlation_id,
                student_id=request.student_id,
                stage=RequestMonitoringService.STAGE_INTEREST_MATCH,
                status="in_progress",
            )

            interest_match = await interest_service.match_interest_to_request(
                db=db,
                student_id=current_user.user_id,
                student_query=request.student_query,
            )
            if interest_match and interest_match.get("interest_name"):
                interest_to_use = interest_match["interest_name"]

                # Track: Interest Matching Completed
                monitoring_service.track_event(
                    request_id=correlation_id,
                    student_id=request.student_id,
                    stage=RequestMonitoringService.STAGE_INTEREST_MATCH,
                    status="completed",
                    confidence_score=interest_match.get("confidence"),
                    metadata={
                        "interest_name": interest_to_use,
                        "reasoning": interest_match.get("reasoning"),
                        "fallback_used": interest_match.get("fallback_used"),
                    },
                )

                logger.info(
                    f"Matched interest: {interest_to_use} "
                    f"(confidence: {interest_match.get('confidence', 0):.2f}, "
                    f"reasoning: {interest_match.get('reasoning', 'N/A')})"
                )
            else:
                logger.warning(
                    f"No interest match found for student {current_user.user_id}"
                )

                # Track: Interest Matching Failed
                monitoring_service.track_event(
                    request_id=correlation_id,
                    student_id=request.student_id,
                    stage=RequestMonitoringService.STAGE_INTEREST_MATCH,
                    status="completed",
                    confidence_score=0.0,
                    metadata={"no_match": True},
                )

        # ASYNC ARCHITECTURE: Create ContentRequest and publish to Pub/Sub
        # This decouples the API from long-running video generation tasks

        # 1. Create ContentRequest record in database
        content_req_service = ContentRequestService()
        content_request = content_req_service.create_request(
            db=db,
            student_id=request.student_id,
            topic=request.student_query,
            learning_objective=None,
            grade_level=str(request.grade_level),
            duration_minutes=3,
            correlation_id=correlation_id,
            # Phase 1A: Dual Modality Support
            requested_modalities=request.requested_modalities,
            preferred_modality=request.preferred_modality,
        )

        logger.info(
            f"Created ContentRequest: id={content_request.id}, "
            f"correlation_id={correlation_id}"
        )

        # 2. Publish request to Pub/Sub for async processing by worker
        pubsub_service = get_pubsub_service()
        publish_result = await pubsub_service.publish_content_request(
            request_id=str(content_request.id),
            correlation_id=correlation_id,
            student_id=request.student_id,
            student_query=request.student_query,
            grade_level=request.grade_level,
            interest=interest_to_use,
            # Phase 1A: Dual Modality Support
            requested_modalities=request.requested_modalities,
            preferred_modality=request.preferred_modality,
        )

        logger.info(
            f"Published to Pub/Sub: message_id={publish_result['message_id']}, "
            f"request_id={content_request.id}"
        )

        # Track: Request Published
        monitoring_service.track_event(
            request_id=correlation_id,
            student_id=request.student_id,
            stage="request_published",
            status="completed",
            metadata={
                "content_request_id": str(content_request.id),
                "pubsub_message_id": publish_result["message_id"],
                "topic": publish_result["topic"],
            },
        )

        # 3. Return 202 Accepted immediately (no waiting for video generation)
        return ContentGenerationResponse(
            status="pending",
            request_id=str(content_request.id),
            cache_key=None,
            message="Content generation request received. Poll /api/v1/content/request/{request_id}/status for progress.",
            content_url=None,
            estimated_completion_seconds=180,
        )

    except Exception as e:
        logger.error(f"Content generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}",
        )


@router.get(
    "/request/{request_id}/status",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def get_request_status(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the status of a content generation request.

    This endpoint enables long-polling for async content generation:
    - Frontend polls this endpoint every 3 seconds
    - Returns current status, progress percentage, and stage
    - When completed: returns video_url, script_text, thumbnail_url
    - When failed: returns error information

    **Path Parameters**:
    - request_id: UUID of the ContentRequest (returned from POST /generate)

    **Returns**:
    - request_id: UUID of the request
    - correlation_id: Correlation ID for distributed tracing
    - status: Current status (pending, validating, generating, completed, failed)
    - progress_percentage: Progress from 0-100
    - current_stage: Current processing stage (e.g., "Generating script", "Creating video")
    - created_at: Request creation timestamp
    - started_at: Processing start timestamp
    - completed_at: Completion timestamp (if completed)
    - video_url: Video URL (if completed)
    - script_text: Script text (if completed)
    - thumbnail_url: Thumbnail URL (if completed)
    - error_message: Error message (if failed)
    - error_stage: Stage where error occurred (if failed)
    - failed_at: Failure timestamp (if failed)

    **Status Values**:
    - pending: Request created, waiting for worker to pick up
    - validating: Worker validating request
    - generating: Content generation in progress
    - completed: Generation successful, video ready
    - failed: Generation failed

    **Example Response (In Progress)**:
    ```json
    {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "correlation_id": "req_abc123def456",
        "status": "generating",
        "progress_percentage": 65,
        "current_stage": "Creating video from script and audio",
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:30:05Z"
    }
    ```

    **Example Response (Completed)**:
    ```json
    {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "correlation_id": "req_abc123def456",
        "status": "completed",
        "progress_percentage": 100,
        "current_stage": "Upload complete",
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:30:05Z",
        "completed_at": "2024-01-15T10:33:45Z",
        "video_url": "gs://vividly-dev-content/videos/abc123.mp4",
        "script_text": "Welcome to photosynthesis...",
        "thumbnail_url": "gs://vividly-dev-content/thumbnails/abc123.jpg"
    }
    ```
    """
    try:
        # Get request status from service
        content_req_service = ContentRequestService()
        status_data = content_req_service.get_request_status(db, request_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content request not found: {request_id}",
            )

        # Verify authorization: user must own this request
        # Get the ContentRequest to check student_id
        content_request = content_req_service.get_request_by_id(db, request_id)
        if not content_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content request not found: {request_id}",
            )

        # Authorization check: student can only view their own requests
        # Teachers/admins can view any request
        if current_user.role == "student":
            if str(content_request.student_id) != str(current_user.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this request",
                )

        logger.info(
            f"Request status retrieved: request_id={request_id}, "
            f"status={status_data['status']}, "
            f"progress={status_data['progress_percentage']}%"
        )

        return status_data

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to get request status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get request status: {str(e)}",
        )
