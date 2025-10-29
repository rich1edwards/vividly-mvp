"""
Content service containing business logic for content metadata operations.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from fastapi import HTTPException, status
from typing import List, Dict, Optional
from datetime import datetime

from app.models.content_metadata import ContentMetadata, GenerationStatus


def get_content_by_cache_key(db: Session, cache_key: str) -> ContentMetadata:
    """
    Get content metadata by cache key (content_id).

    Args:
        db: Database session
        cache_key: Content cache key (content_id)

    Returns:
        ContentMetadata: Content metadata

    Raises:
        HTTPException: 404 if content not found
    """
    content = db.query(ContentMetadata).filter(ContentMetadata.content_id == cache_key).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    return content


def check_content_exists(db: Session, topic_id: str, interest: str) -> Dict:
    """
    Check if content exists for a topic-interest combination.

    Args:
        db: Database session
        topic_id: Topic ID
        interest: Interest name (e.g., "basketball")

    Returns:
        Dict with cache hit status and content info
    """
    # Convert interest name to interest_id format (e.g., "basketball" -> "int_basketball")
    interest_id = f"int_{interest}"

    # Look for completed content
    content = (
        db.query(ContentMetadata)
        .filter(
            and_(
                ContentMetadata.topic_id == topic_id,
                ContentMetadata.interest_id == interest_id,
                ContentMetadata.status == GenerationStatus.COMPLETED.value,
            )
        )
        .first()
    )

    if content:
        return {
            "cache_hit": True,
            "cache_key": content.content_id,  # Use content_id as cache_key
            "status": content.status,  # Expose status at top level
            "video_url": content.video_url,  # Expose video_url at top level
            "message": "Content found in cache",
            "metadata": {
                "title": content.title,
                "duration_seconds": content.duration_seconds,
                "generated_at": content.generated_at,
                "views": content.views or 0,
            },
        }
    else:
        # Check if generation is in progress
        in_progress = (
            db.query(ContentMetadata)
            .filter(
                and_(
                    ContentMetadata.topic_id == topic_id,
                    ContentMetadata.interest_id == interest_id,
                    ContentMetadata.status.in_([
                        GenerationStatus.PENDING.value,
                        GenerationStatus.GENERATING.value,
                    ]),
                )
            )
            .first()
        )

        if in_progress:
            return {
                "cache_hit": False,
                "cache_key": in_progress.content_id,
                "status": in_progress.status,
                "video_url": None,
                "message": "Content is currently being generated",
            }
        else:
            return {
                "cache_hit": False,
                "cache_key": None,
                "status": None,
                "video_url": None,
                "message": "Content needs to be generated",
            }


def get_recent_content(
    db: Session,
    limit: int = 10,
    topic_id: Optional[str] = None,
    interest: Optional[str] = None,
    student_id: Optional[str] = None,
) -> Dict:
    """
    Get recently generated content.

    Args:
        db: Database session
        limit: Results limit
        topic_id: Optional filter by topic
        interest: Optional filter by interest
        student_id: Optional filter by student

    Returns:
        Dict with content list
    """
    query = db.query(ContentMetadata).filter(
        ContentMetadata.status == GenerationStatus.COMPLETED
    )

    # Apply filters
    if topic_id:
        query = query.filter(ContentMetadata.topic_id == topic_id)
    if interest:
        # Convert interest name to interest_id format
        interest_id = f"int_{interest}"
        query = query.filter(ContentMetadata.interest_id == interest_id)
    if student_id:
        # TODO: Filter by content created for this student
        pass

    # Get recent content
    content_list = (
        query.order_by(desc(ContentMetadata.generated_at))
        .limit(limit)
        .all()
    )

    return {
        "content": content_list,
        "pagination": {
            "has_more": len(content_list) == limit,
        },
    }


def submit_content_feedback(
    db: Session,
    cache_key: str,
    student_id: str,
    rating: int,
    feedback_type: Optional[str] = None,
    comments: Optional[str] = None,
) -> Dict:
    """
    Submit feedback for content.

    Args:
        db: Database session
        cache_key: Content cache key
        student_id: Student submitting feedback
        rating: Rating 1-5 stars
        feedback_type: Type of feedback (helpful, confusing, inaccurate, etc.)
        comments: Optional text feedback

    Returns:
        Dict with feedback confirmation

    Raises:
        HTTPException: 404 if content not found
    """
    content = get_content_by_cache_key(db, cache_key)

    # TODO: Store feedback in database
    # For now, just acknowledge

    return {
        "cache_key": cache_key,
        "feedback_recorded": True,
        "rating": rating,
        "feedback_type": feedback_type,
        "submitted_at": datetime.utcnow(),
    }


def get_content_feedback_summary(db: Session, cache_key: str) -> Dict:
    """
    Get feedback summary for content.

    Args:
        db: Database session
        cache_key: Content cache key

    Returns:
        Dict with feedback statistics

    Raises:
        HTTPException: 404 if content not found
    """
    content = get_content_by_cache_key(db, cache_key)

    # TODO: Query feedback from database
    # For now, return placeholder data

    return {
        "cache_key": cache_key,
        "total_ratings": 0,
        "average_rating": 0.0,
        "rating_distribution": {
            "5": 0,
            "4": 0,
            "3": 0,
            "2": 0,
            "1": 0,
        },
        "feedback_types": {},
    }


def get_student_content_history(
    db: Session,
    student_id: str,
    limit: int = 20,
) -> Dict:
    """
    Get student's content viewing history.

    Args:
        db: Database session
        student_id: Student ID
        limit: Results limit

    Returns:
        Dict with content list
    """
    content_list = (
        db.query(ContentMetadata)
        .filter(ContentMetadata.student_id == student_id)
        .order_by(desc(ContentMetadata.created_at))  # Use created_at column, not generated_at property
        .limit(limit)
        .all()
    )

    return {
        "content": content_list,
        "pagination": {
            "has_more": len(content_list) == limit,
        },
    }
