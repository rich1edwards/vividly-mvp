"""
Interest Endpoints

FastAPI router for managing student interests.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.interest import (
    InterestResponse,
    StudentInterestCreate,
    StudentInterestsListResponse,
)
from app.services import interest_service
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/", response_model=List[InterestResponse])
def get_interests(
    db: Session = Depends(get_db),
):
    """
    Get all available interests.

    Returns list of all interests organized by category.
    """
    interests = interest_service.get_all_interests(db)
    return interests


@router.get("/me", response_model=StudentInterestsListResponse)
def get_my_interests(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Get current student's selected interests.

    Only accessible by students.
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can have interests",
        )

    interests = interest_service.get_student_interests(db, current_user.user_id)
    return StudentInterestsListResponse(interests=interests, count=len(interests))


@router.post("/me", response_model=StudentInterestsListResponse)
def set_my_interests(
    interest_data: StudentInterestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Set current student's interests.

    Replaces existing interests with new selection (2-5 required).
    Only accessible by students.
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can set interests",
        )

    interests = interest_service.set_student_interests(
        db, current_user.user_id, interest_data
    )

    return StudentInterestsListResponse(interests=interests, count=len(interests))


@router.get("/me/has-selected", response_model=dict)
def has_selected_interests(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Check if current student has selected interests.

    Returns: {"has_selected": bool}
    """
    if current_user.role != UserRole.STUDENT:
        return {"has_selected": True}  # Non-students don't need interests

    has_selected = interest_service.has_selected_interests(db, current_user.user_id)
    return {"has_selected": has_selected}
