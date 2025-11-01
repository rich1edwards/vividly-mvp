"""
Interest service containing business logic for student interests.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Optional, Any
import logging
import os
import json

from app.models.interest import Interest, StudentInterest
from app.models.user import User
from app.schemas.interest import StudentInterestCreate

logger = logging.getLogger(__name__)


def get_all_interests(db: Session) -> List[Interest]:
    """
    Get all available interests.

    Args:
        db: Database session

    Returns:
        List[Interest]: All available interests ordered by category and display_order
    """
    return db.query(Interest).order_by(
        Interest.category,
        Interest.display_order
    ).all()


def get_student_interests(db: Session, student_id: str) -> List[Interest]:
    """
    Get interests selected by a student.

    Args:
        db: Database session
        student_id: Student user ID

    Returns:
        List[Interest]: Student's selected interests
    """
    student_interests = db.query(StudentInterest).filter(
        StudentInterest.student_id == student_id
    ).all()

    return [si.interest for si in student_interests]


def set_student_interests(
    db: Session,
    student_id: str,
    interest_data: StudentInterestCreate
) -> List[Interest]:
    """
    Set student's interests (replaces existing).

    Args:
        db: Database session
        student_id: Student user ID
        interest_data: Interest IDs to set (2-5)

    Returns:
        List[Interest]: Updated list of student's interests

    Raises:
        HTTPException: 400 if validation fails, 404 if interest not found
    """
    # Validate student exists
    student = db.query(User).filter(User.user_id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Validate interest count
    if len(interest_data.interest_ids) < 2 or len(interest_data.interest_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must select between 2-5 interests"
        )

    # Validate all interests exist
    interests = db.query(Interest).filter(
        Interest.interest_id.in_(interest_data.interest_ids)
    ).all()

    if len(interests) != len(interest_data.interest_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more interests not found"
        )

    # Remove existing student interests
    db.query(StudentInterest).filter(
        StudentInterest.student_id == student_id
    ).delete()

    # Add new student interests
    for interest_id in interest_data.interest_ids:
        student_interest = StudentInterest(
            student_id=student_id,
            interest_id=interest_id
        )
        db.add(student_interest)

    db.commit()

    # Return updated interests
    return get_student_interests(db, student_id)


def has_selected_interests(db: Session, student_id: str) -> bool:
    """
    Check if student has selected their interests.

    Args:
        db: Database session
        student_id: Student user ID

    Returns:
        bool: True if student has selected interests
    """
    count = db.query(StudentInterest).filter(
        StudentInterest.student_id == student_id
    ).count()

    return count >= 2


async def match_interest_to_request(
    db: Session,
    student_id: str,
    student_query: str,
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> Dict[str, Any]:
    """
    Use LLM to determine which student interest best aligns with their request.

    Args:
        db: Database session
        student_id: Student user ID
        student_query: Natural language query/request
        project_id: GCP project ID (optional, uses env var if not provided)
        location: Vertex AI location (default: us-central1)

    Returns:
        Dict with:
            - matched_interest: Interest object that best matches
            - interest_id: str (interest_id field)
            - interest_name: str (name field)
            - confidence: float (0.0-1.0)
            - reasoning: str (explanation of the match)
            - fallback_used: bool (True if no good match, used first interest)

    Example:
        >>> result = await match_interest_to_request(
        ...     db, "student_123", "Explain Newton's laws using basketball"
        ... )
        >>> print(result["interest_name"])
        "Basketball"
        >>> print(result["confidence"])
        0.95
    """
    # Get student's interests
    interests = get_student_interests(db, student_id)

    if not interests or len(interests) == 0:
        logger.warning(f"Student {student_id} has no interests selected")
        return {
            "matched_interest": None,
            "interest_id": None,
            "interest_name": None,
            "confidence": 0.0,
            "reasoning": "Student has not selected any interests",
            "fallback_used": True
        }

    # If only one interest, return it directly
    if len(interests) == 1:
        interest = interests[0]
        return {
            "matched_interest": interest,
            "interest_id": interest.interest_id,
            "interest_name": interest.name,
            "confidence": 1.0,
            "reasoning": "Only one interest available",
            "fallback_used": False
        }

    # Multiple interests - use LLM to match
    try:
        # Initialize Vertex AI
        project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")

        try:
            from google.cloud import aiplatform
            from vertexai.generative_models import GenerativeModel

            aiplatform.init(project=project_id, location=location)
            model = GenerativeModel("gemini-1.5-pro")
            vertex_available = True
        except Exception as e:
            logger.warning(f"Vertex AI not available: {e}. Using fallback matching.")
            vertex_available = False

        if vertex_available:
            # Build prompt for LLM
            interests_list = []
            for interest in interests:
                interests_list.append({
                    "interest_id": interest.interest_id,
                    "name": interest.name,
                    "category": interest.category,
                    "description": interest.description
                })

            prompt = f"""You are an AI assistant helping to personalize educational content.

Student's Interests:
{json.dumps(interests_list, indent=2)}

Student's Learning Request:
"{student_query}"

Task: Determine which of the student's interests best aligns with their learning request.
The goal is to use this interest to make the educational content more engaging and relatable.

Consider:
1. Direct mentions of the interest in the query
2. Conceptual connections between the query topic and the interest
3. How the interest could be used as an analogy or example
4. Which interest would make the content most engaging for this student

Respond ONLY with valid JSON in this exact format:
{{
  "matched_interest_id": "int_basketball",
  "interest_name": "Basketball",
  "confidence": 0.95,
  "reasoning": "The student explicitly asked to learn about physics using basketball examples."
}}

If no strong connection exists, pick the most creative match and set confidence accordingly (0.3-0.6).
Confidence scale:
- 0.9-1.0: Direct mention or very strong connection
- 0.7-0.9: Strong conceptual connection
- 0.5-0.7: Moderate connection, could work well
- 0.3-0.5: Weak connection, creative stretch
- 0.0-0.3: No meaningful connection

Response:"""

            # Call Gemini
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON response
            try:
                result = json.loads(response_text)
                matched_interest_id = result.get("matched_interest_id")
                confidence = float(result.get("confidence", 0.5))
                reasoning = result.get("reasoning", "LLM match")

                # Find the matched interest
                matched_interest = next(
                    (i for i in interests if i.interest_id == matched_interest_id),
                    None
                )

                if matched_interest:
                    return {
                        "matched_interest": matched_interest,
                        "interest_id": matched_interest.interest_id,
                        "interest_name": matched_interest.name,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "fallback_used": False
                    }
                else:
                    logger.warning(f"LLM returned invalid interest_id: {matched_interest_id}")
                    # Fall through to fallback
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse LLM response: {e}")
                logger.error(f"Response text: {response_text}")
                # Fall through to fallback

    except Exception as e:
        logger.error(f"Interest matching failed: {e}", exc_info=True)
        # Fall through to fallback

    # Fallback: Use first interest
    logger.info(f"Using fallback interest matching for student {student_id}")
    fallback_interest = interests[0]
    return {
        "matched_interest": fallback_interest,
        "interest_id": fallback_interest.interest_id,
        "interest_name": fallback_interest.name,
        "confidence": 0.5,
        "reasoning": "Fallback: Using first interest due to matching error",
        "fallback_used": True
    }
