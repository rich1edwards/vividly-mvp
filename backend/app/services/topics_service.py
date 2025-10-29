"""
Topics service containing business logic for topics and interests operations.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status
from typing import List, Dict, Optional

from app.models.interest import Interest, StudentInterest
from app.models.progress import Topic, StudentProgress, ProgressStatus


def list_topics(
    db: Session,
    subject: Optional[str] = None,
    grade_level: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> Dict:
    """
    List all topics with filtering and pagination.

    Args:
        db: Database session
        subject: Filter by subject (Physics, Math, etc.)
        grade_level: Filter by grade level
        category: Filter by category (Mechanics, Algebra, etc.)
        limit: Results per page
        cursor: Pagination cursor

    Returns:
        Dict with topics list and pagination info
    """
    query = db.query(Topic)

    # Apply filters
    if subject:
        query = query.filter(Topic.subject == subject)
    if category:
        query = query.filter(Topic.category == category)
    if grade_level:
        # Filter topics that include this grade level (grade_level_min <= grade <= grade_level_max)
        query = query.filter(
            Topic.grade_level_min <= grade_level,
            Topic.grade_level_max >= grade_level
        )

    # Apply cursor pagination
    if cursor:
        query = query.filter(Topic.topic_id > cursor)

    # Get results
    topics = query.order_by(Topic.topic_id).limit(limit + 1).all()

    # Check if there are more results
    has_more = len(topics) > limit
    if has_more:
        topics = topics[:limit]

    # Get total count (expensive, only if no filters)
    total_count = None
    if not subject and not grade_level and not category:
        total_count = db.query(func.count(Topic.topic_id)).scalar()

    return {
        "topics": topics,
        "pagination": {
            "next_cursor": topics[-1].topic_id if has_more and topics else None,
            "has_more": has_more,
            "total_count": total_count,
        },
    }


def search_topics(db: Session, query_text: str, limit: int = 10) -> Dict:
    """
    Search topics by name and description.

    Args:
        db: Database session
        query_text: Search query
        limit: Results limit

    Returns:
        Dict with search results
    """
    search_pattern = f"%{query_text}%"

    # Simple search using LIKE (could be enhanced with full-text search)
    topics = (
        db.query(Topic)
        .filter(
            or_(
                Topic.name.ilike(search_pattern),
                Topic.description.ilike(search_pattern),
            )
        )
        .limit(limit)
        .all()
    )

    # Add relevance scoring (simple: exact matches score higher)
    results = []
    for topic in topics:
        relevance_score = 0.5  # Base score

        # Boost for exact name match
        if query_text.lower() in topic.name.lower():
            relevance_score += 0.3

        # Boost for description match
        if query_text.lower() in (topic.description or "").lower():
            relevance_score += 0.2

        # Serialize topic to dict
        results.append({
            "topic": {
                "topic_id": topic.topic_id,
                "name": topic.name,
                "subject": topic.subject,
                "category": topic.category,
                "description": topic.description,
            },
            "relevance_score": min(relevance_score, 1.0),
            "highlights": [topic.name] if query_text.lower() in topic.name.lower() else [],
        })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "query": query_text,
        "results": results,
        "total_results": len(results),
    }


def get_topic_details(db: Session, topic_id: str, student_id: Optional[str] = None) -> Dict:
    """
    Get detailed topic information including prerequisites and progress.

    Args:
        db: Database session
        topic_id: Topic ID
        student_id: Optional student ID to check completion status

    Returns:
        Dict with complete topic details

    Raises:
        HTTPException: 404 if topic not found
    """
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    # Get prerequisite topics with completion status
    prerequisites = []
    if topic.prerequisites:
        for prereq_id in topic.prerequisites:
            prereq_topic = db.query(Topic).filter(Topic.topic_id == prereq_id).first()
            if prereq_topic:
                prereq_data = {
                    "topic_id": prereq_topic.topic_id,
                    "name": prereq_topic.name,
                    "completed": False,
                    "completed_at": None,
                }

                # Check completion status if student provided
                if student_id:
                    progress = (
                        db.query(StudentProgress)
                        .filter(
                            StudentProgress.student_id == student_id,
                            StudentProgress.topic_id == prereq_id,
                            StudentProgress.status == ProgressStatus.COMPLETED,
                        )
                        .first()
                    )
                    if progress:
                        prereq_data["completed"] = True
                        prereq_data["completed_at"] = progress.completed_at

                prerequisites.append(prereq_data)

    # Get related topics
    related_topics = []
    if topic.related_topics:
        for related_id in topic.related_topics:
            related_topic = db.query(Topic).filter(Topic.topic_id == related_id).first()
            if related_topic:
                related_topics.append({
                    "topic_id": related_topic.topic_id,
                    "name": related_topic.name,
                })

    return {
        "topic": topic,
        "prerequisites": prerequisites,
        "related_topics": related_topics,
    }


def get_topic_prerequisites(db: Session, topic_id: str, student_id: Optional[str] = None) -> List[Dict]:
    """
    Get topic prerequisites with completion status.

    Args:
        db: Database session
        topic_id: Topic ID
        student_id: Optional student ID to check completion

    Returns:
        List of prerequisite topics with completion status
    """
    topic = db.query(Topic).filter(Topic.topic_id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    if not topic.prerequisites:
        return []

    prerequisites = []
    for prereq_id in topic.prerequisites:
        prereq_topic = db.query(Topic).filter(Topic.topic_id == prereq_id).first()
        if prereq_topic:
            prereq_data = {
                "topic_id": prereq_topic.topic_id,
                "name": prereq_topic.name,
                "subject": prereq_topic.subject,
                "completed": False,
            }

            # Check completion status
            if student_id:
                progress = (
                    db.query(StudentProgress)
                    .filter(
                        StudentProgress.student_id == student_id,
                        StudentProgress.topic_id == prereq_id,
                        StudentProgress.status == ProgressStatus.COMPLETED,
                    )
                    .first()
                )
                if progress:
                    prereq_data["completed"] = True

            prerequisites.append(prereq_data)

    return prerequisites


def list_interests(db: Session) -> Dict:
    """
    List all canonical interests.

    Args:
        db: Database session

    Returns:
        Dict with interests grouped by category
    """
    interests = db.query(Interest).order_by(Interest.category, Interest.name).all()

    # Calculate popularity (percentage of students with each interest)
    total_students = db.query(func.count(func.distinct(StudentInterest.student_id))).scalar() or 1

    results = []
    for interest in interests:
        student_count = (
            db.query(func.count(StudentInterest.student_id))
            .filter(StudentInterest.interest_id == interest.interest_id)
            .scalar()
        )
        popularity = student_count / total_students if total_students > 0 else 0

        results.append({
            "interest_id": interest.interest_id,
            "name": interest.name,
            "category": interest.category,
            "icon_url": None,  # TODO: Add icon_url field to Interest model
            "description": interest.description,
            "popularity": round(popularity, 2),
            "content_count": 0,  # TODO: Count videos using this interest
        })

    # Get unique categories
    categories = list(set(interest.category for interest in interests if interest.category))

    return {
        "interests": results,
        "total_count": len(results),
        "categories": categories,
    }


def list_interest_categories(db: Session) -> Dict:
    """
    List interest categories with their interests.

    Args:
        db: Database session

    Returns:
        Dict with categories and their interests
    """
    interests = db.query(Interest).order_by(Interest.category, Interest.name).all()

    # Group by category
    categories_dict = {}
    for interest in interests:
        category = interest.category or "Other"
        if category not in categories_dict:
            categories_dict[category] = {
                "category_id": category.lower().replace(" ", "_"),
                "name": category.title(),
                "description": f"{category} related interests",
                "icon_url": None,  # TODO: Add category icons
                "interests": [],
            }

        categories_dict[category]["interests"].append({
            "interest_id": interest.interest_id,
            "name": interest.name,
        })

    # Add interest counts
    for category_data in categories_dict.values():
        category_data["interest_count"] = len(category_data["interests"])

    return {
        "categories": list(categories_dict.values()),
    }
