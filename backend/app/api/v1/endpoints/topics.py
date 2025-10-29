"""
Topics and Interests API endpoints.

Endpoints for browsing topics, searching, and managing interests.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.topics import (
    TopicListResponse,
    TopicDetailResponse,
    TopicSearchResponse,
    InterestListResponse,
    InterestCategoryListResponse,
)
from app.services import topics_service
from app.utils.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/topics", response_model=TopicListResponse)
async def list_topics(
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all topics with filtering and pagination.

    **Query Parameters**:
    - subject: Filter by subject (Physics, Math, Chemistry, etc.)
    - grade_level: Filter by grade level (9-12)
    - category: Filter by category (Mechanics, Algebra, etc.)
    - limit: Results per page (default: 20, max: 100)
    - cursor: Pagination cursor (topic_id from last result)

    **Returns**:
    - Paginated list of topics with details
    - Includes prerequisites, standards, content availability
    """
    if limit > 100:
        limit = 100

    result = topics_service.list_topics(
        db=db,
        subject=subject,
        grade_level=grade_level,
        category=category,
        limit=limit,
        cursor=cursor,
    )

    return result


@router.get("/topics/search", response_model=TopicSearchResponse)
async def search_topics(
    q: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search topics by name and description.

    **Query Parameters**:
    - q: Search query (required)
    - limit: Results limit (default: 10, max: 50)

    **Returns**:
    - Search results ranked by relevance
    - Includes highlights of matching text
    """
    if not q or len(q) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters",
        )

    if limit > 50:
        limit = 50

    result = topics_service.search_topics(db=db, query_text=q, limit=limit)

    return result


@router.get("/topics/{topic_id}", response_model=dict)
async def get_topic_details(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed topic information.

    **Returns**:
    - Complete topic details
    - Prerequisites with completion status (for students)
    - Related topics
    - Standards alignment
    - Available interests for personalization
    """
    student_id = current_user.user_id if current_user.role == "student" else None

    result = topics_service.get_topic_details(
        db=db,
        topic_id=topic_id,
        student_id=student_id,
    )

    # Format response
    topic = result["topic"]
    return {
        "topic_id": topic.topic_id,
        "name": topic.name,
        "subject": topic.subject,
        "category": topic.category,
        "grade_levels": topic.grade_levels,
        "difficulty": topic.difficulty,
        "description": topic.description,
        "learning_objectives": topic.learning_objectives or [],
        "prerequisites": result["prerequisites"],
        "related_topics": result["related_topics"],
        "standards": topic.standards or [],
        "estimated_duration_min": topic.estimated_duration_min,
        "content_available": topic.content_available,
        "available_interests": [],  # TODO: Query available interests
        "popularity_score": topic.popularity_score or 0.0,
        "created_at": topic.created_at,
    }


@router.get("/topics/{topic_id}/prerequisites", response_model=dict)
async def get_topic_prerequisites(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get topic prerequisites with completion status.

    **Returns**:
    - List of prerequisite topics
    - Completion status for logged-in student
    - Ordered by dependency (must complete in order)
    """
    student_id = current_user.user_id if current_user.role == "student" else None

    prerequisites = topics_service.get_topic_prerequisites(
        db=db,
        topic_id=topic_id,
        student_id=student_id,
    )

    return {
        "topic_id": topic_id,
        "prerequisites": prerequisites,
    }


@router.get("/interests", response_model=InterestListResponse)
async def list_interests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all canonical interests.

    **Returns**:
    - All 60 canonical interests
    - Grouped by category (sports, arts, technology, etc.)
    - Includes icon URLs for display
    - Popularity score (percentage of students)
    - Content count (videos available per interest)
    """
    result = topics_service.list_interests(db=db)

    return result


@router.get("/interests/categories", response_model=InterestCategoryListResponse)
async def list_interest_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List interest categories with their interests.

    **Returns**:
    - All interest categories
    - Interests grouped by category
    - Interest counts per category
    """
    result = topics_service.list_interest_categories(db=db)

    return result
