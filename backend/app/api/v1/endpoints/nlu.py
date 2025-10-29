"""
NLU API Endpoints (Phase 3 Sprint 1)

Natural Language Understanding endpoints for topic extraction.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.nlu import (
    TopicExtractionRequest,
    TopicExtractionResponse,
    ClarificationRequest,
    TopicSuggestionRequest,
    TopicSuggestionsResponse
)
from app.services.nlu_service import get_nlu_service, NLUService
from app.utils.dependencies import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlu", tags=["nlu"])


@router.post(
    "/extract-topic",
    response_model=TopicExtractionResponse,
    summary="Extract topic from student query",
    description="""
    Use AI (Vertex AI Gemini) to extract educational topic from student's natural language query.

    **Features:**
    - Maps free-text to canonical topic IDs
    - Handles ambiguous queries with clarifying questions
    - Filters inappropriate/off-topic queries
    - Grade-level aware topic suggestions
    - <3s response time (p95)

    **Example queries:**
    - "Explain Newton's Third Law using basketball"
    - "Help me understand chemical bonds"
    - "What is photosynthesis?"
    """,
    status_code=status.HTTP_200_OK
)
async def extract_topic(
    request: TopicExtractionRequest,
    current_user: User = Depends(get_current_user),
    nlu_service: NLUService = Depends(get_nlu_service),
    db: Session = Depends(get_db)
):
    """
    Extract topic from natural language query using AI.

    Args:
        request: Query extraction request
        current_user: Authenticated user
        nlu_service: NLU service dependency
        db: Database session

    Returns:
        TopicExtractionResponse with extracted topic or clarifying questions
    """
    try:
        # Use student's grade if they're a student
        grade_level = request.grade_level
        if current_user.role == "student" and current_user.grade_level:
            grade_level = current_user.grade_level

        # Extract topic
        result = await nlu_service.extract_topic(
            student_query=request.query,
            grade_level=grade_level,
            student_id=current_user.user_id,
            recent_topics=request.recent_topics or [],
            subject_context=request.subject_context
        )

        return TopicExtractionResponse(**result)

    except Exception as e:
        logger.error(f"Topic extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Topic extraction failed. Please try again."
        )


@router.post(
    "/clarify",
    response_model=TopicExtractionResponse,
    summary="Re-extract topic with clarification",
    description="""
    Re-extract topic after student provides clarification answer.

    Used when initial extraction was ambiguous and clarifying questions were asked.
    """,
    status_code=status.HTTP_200_OK
)
async def clarify_topic(
    request: ClarificationRequest,
    current_user: User = Depends(get_current_user),
    nlu_service: NLUService = Depends(get_nlu_service),
    db: Session = Depends(get_db)
):
    """
    Re-extract topic with clarification from student.

    Args:
        request: Clarification request
        current_user: Authenticated user
        nlu_service: NLU service dependency
        db: Database session

    Returns:
        TopicExtractionResponse with refined extraction
    """
    try:
        # Combine original query with clarification
        combined_query = f"{request.original_query}. Specifically: {request.clarification_answer}"

        # Extract with combined context
        result = await nlu_service.extract_topic(
            student_query=combined_query,
            grade_level=request.grade_level,
            student_id=current_user.user_id,
            recent_topics=[],
            subject_context=None
        )

        return TopicExtractionResponse(**result)

    except Exception as e:
        logger.error(f"Clarification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Topic clarification failed. Please try again."
        )


@router.post(
    "/suggest-topics",
    response_model=TopicSuggestionsResponse,
    summary="Get topic suggestions",
    description="""
    Get personalized topic suggestions for student.

    **Factors:**
    - Grade level
    - Recent topics studied
    - Subject preference
    - Difficulty progression

    **Use cases:**
    - "What should I learn next?"
    - Empty state on dashboard
    - After completing a topic
    """,
    status_code=status.HTTP_200_OK
)
async def suggest_topics(
    request: TopicSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized topic suggestions.

    Args:
        request: Suggestion request parameters
        current_user: Authenticated user
        db: Database session

    Returns:
        TopicSuggestionsResponse with suggested topics
    """
    try:
        # Import here to avoid circular dependency
        from app.services import topics_service

        # Get topics for grade level
        topics = topics_service.list_topics(
            db=db,
            subject=request.subject,
            grade_level=request.grade_level,
            limit=request.limit
        )

        # Simple suggestion logic (can be enhanced with ML)
        suggestions = []
        for topic_data in topics.get("topics", []):
            topic = topic_data["topic"]
            suggestions.append({
                "topic_id": topic["topic_id"],
                "topic_name": topic["name"],
                "subject": topic["subject"],
                "difficulty": topic.get("difficulty", "intermediate"),
                "relevance_score": 0.8,  # Placeholder - ML model would provide this
                "reason": "Recommended for your grade level"
            })

        return TopicSuggestionsResponse(
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )

    except Exception as e:
        logger.error(f"Topic suggestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Topic suggestion failed. Please try again."
        )


@router.get(
    "/health",
    summary="Check NLU service health",
    description="Health check endpoint for NLU service",
    status_code=status.HTTP_200_OK
)
async def nlu_health_check(
    nlu_service: NLUService = Depends(get_nlu_service)
):
    """
    Health check for NLU service.

    Returns:
        Dict with service status
    """
    return {
        "service": "nlu",
        "status": "healthy",
        "vertex_ai_available": nlu_service.vertex_available,
        "model": nlu_service.model_name,
        "project": nlu_service.project_id,
        "location": nlu_service.location
    }
