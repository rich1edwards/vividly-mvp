"""
Class API endpoints.

Endpoints for class operations accessible by both teachers and students.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.teacher import (
    UpdateClassRequest,
    ClassResponse,
    RosterResponse,
)
from app.services import teacher_service
from app.utils.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class_details(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get class details by ID.

    **Authorization**:
    - Teachers can view their own classes
    - Students can view classes they're enrolled in
    - Admins can view any class

    **Returns**:
    - Complete class details including name, subject, teacher, grade levels
    - Enrollment count and roster preview
    """
    class_obj = teacher_service.get_class_by_id(db, class_id)
    return class_obj


@router.patch("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: str,
    class_data: UpdateClassRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update class details.

    **Authorization**:
    - Only the class teacher can update
    - Admins can update any class

    **Allowed fields**:
    - name: Class name
    - subject: Subject area
    - grade_levels: List of grade levels (9-12)
    - description: Class description
    """
    # Authorization: Only class teacher or admin can update
    class_obj = teacher_service.get_class_by_id(db, class_id)
    if current_user.role != "admin" and class_obj.teacher_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can update this class",
        )

    updated_class = teacher_service.update_class(db, class_id, class_data)
    return updated_class


@router.delete("/{class_id}", response_model=ClassResponse)
async def archive_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Archive a class (soft delete).

    **Authorization**:
    - Only the class teacher can archive
    - Admins can archive any class

    **Effects**:
    - Class is marked as archived
    - Students can no longer join
    - Existing enrollments remain (historical data)
    - Class code becomes invalid
    """
    # Authorization: Only class teacher or admin can archive
    class_obj = teacher_service.get_class_by_id(db, class_id)
    if current_user.role != "admin" and class_obj.teacher_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can archive this class",
        )

    archived_class = teacher_service.archive_class(db, class_id)
    return archived_class


@router.get("/{class_id}/students", response_model=RosterResponse)
async def get_class_roster(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get class roster with student details.

    **Authorization**:
    - Teachers can view roster for their classes
    - Admins can view any roster
    - Students cannot view rosters

    **Returns**:
    - List of enrolled students with:
      - Basic info (name, email, grade)
      - Enrollment date
      - Activity summary (optional)
    """
    # Authorization: Only class teacher or admin
    class_obj = teacher_service.get_class_by_id(db, class_id)
    if current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot view class rosters",
        )
    if current_user.role != "admin" and class_obj.teacher_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can view this roster",
        )

    roster = teacher_service.get_class_roster(db, class_id)
    return roster


@router.delete(
    "/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove student from class.

    **Authorization**:
    - Only the class teacher can remove students
    - Admins can remove students from any class

    **Effects**:
    - Student enrollment is deleted
    - Student loses access to class content
    - Historical activity data is preserved
    """
    # Authorization: Only class teacher or admin
    class_obj = teacher_service.get_class_by_id(db, class_id)
    if current_user.role != "admin" and class_obj.teacher_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can remove students",
        )

    teacher_service.remove_student_from_class(db, class_id, student_id)
    return None
