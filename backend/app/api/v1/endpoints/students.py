"""
Student API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.student import (
    StudentProfileUpdate,
    StudentProfile,
    InterestBase,
    StudentInterestsUpdate,
    LearningProgress,
    JoinClassRequest,
)
from app.schemas.auth import UserResponse
from app.services import student_service
from app.utils.dependencies import get_current_user, get_current_active_student
from app.models.user import User


router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/{student_id}", response_model=dict)
async def get_student_profile(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get student profile with interests and enrolled classes.

    **Authorization**:
    - Students can only access their own profile
    - Teachers/admins can access any student profile

    **Returns**:
    - Complete student profile with interests and classes
    - Progress summary (topics started/completed, watch time)
    """
    # Authorization: Students can only view their own profile
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only access their own profile",
        )

    profile = student_service.get_student_profile(db, student_id)
    return profile


@router.patch("/{student_id}", response_model=UserResponse)
async def update_student_profile(
    student_id: str,
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update student profile (name, grade level only).

    **Authorization**:
    - Students can only update their own profile
    - Teachers/admins can update any student profile

    **Allowed fields**:
    - first_name
    - last_name
    - grade_level (9-12)

    **Note**: Email and role cannot be changed
    """
    # Authorization: Students can only update their own profile
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only update their own profile",
        )

    updated_student = student_service.update_student_profile(
        db, student_id, profile_data
    )
    return updated_student


@router.get("/{student_id}/interests", response_model=List[InterestBase])
async def get_student_interests(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get student's selected interests.

    **Authorization**:
    - Students can only access their own interests
    - Teachers/admins can access any student's interests

    **Returns**:
    - List of 1-5 interests with ID, name, and category
    """
    # Authorization: Students can only view their own interests
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only access their own interests",
        )

    interests = student_service.get_student_interests(db, student_id)
    return [
        InterestBase(
            interest_id=i.interest_id,
            name=i.name,
            category=i.category,
        )
        for i in interests
    ]


@router.put("/{student_id}/interests", response_model=List[InterestBase])
async def update_student_interests(
    student_id: str,
    interests_data: StudentInterestsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update student's interests (1-5 interests).

    **Authorization**:
    - Students can only update their own interests
    - Teachers/admins can update any student's interests

    **Request body**:
    - interest_ids: List of 1-5 interest IDs (must be unique)

    **Validation**:
    - Minimum 1 interest, maximum 5 interests
    - All interest IDs must be valid (from canonical list)
    - Interest IDs must be unique

    **Available interests** (14 total):
    - Sports: basketball, soccer, football, baseball
    - Arts: music, art, dance, theater
    - Tech: coding, gaming, robotics
    - Other: reading, writing, science

    **Returns**:
    - Updated list of interests
    """
    # Authorization: Students can only update their own interests
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only update their own interests",
        )

    interests = student_service.update_student_interests(db, student_id, interests_data)
    return [
        InterestBase(
            interest_id=i.interest_id,
            name=i.name,
            category=i.category,
        )
        for i in interests
    ]


@router.get("/{student_id}/progress", response_model=LearningProgress)
async def get_learning_progress(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get complete learning progress for student.

    **Authorization**:
    - Students can only access their own progress
    - Teachers/admins can access any student's progress

    **Returns**:
    - **topics**: List of all topics with progress
      - topic_id, topic_name, subject
      - status: not_started, in_progress, completed
      - progress_percentage: 0-100
      - videos_watched, total_watch_time_seconds
      - started_at, completed_at timestamps

    - **recent_activity**: Last 10 activities
      - activity_id, activity_type, created_at
      - topic_id, duration_seconds

    - **Summary metrics**:
      - total_topics_started: Count of topics started or completed
      - total_topics_completed: Count of completed topics
      - total_watch_time_seconds: Total video watch time
      - learning_streak_days: Consecutive days with activity

    **Learning streak calculation**:
    - Counts consecutive days from today backwards
    - Activity required each day to maintain streak
    - Maximum 30 days tracked
    """
    # Authorization: Students can only view their own progress
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only access their own progress",
        )

    progress = student_service.get_learning_progress(db, student_id)
    return progress


@router.post(
    "/{student_id}/classes/join",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def join_class(
    student_id: str,
    join_data: JoinClassRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Join a class by entering class code.

    **Authorization**:
    - Students can only join classes for themselves
    - Teachers/admins can enroll students in classes

    **Request body**:
    - class_code: Unique class code (format: "SUBJ-XXX-XXX")
      - Example: "PHYS-ABC-123"

    **Validation**:
    - Class must exist and not be archived
    - Student cannot already be enrolled
    - Class code is case-sensitive

    **Returns**:
    - Joined class details (class_id, name, subject, teacher_id)
    - Enrollment timestamp

    **Notes**:
    - Teachers provide class codes to students
    - Students can be in multiple classes
    - Joining logs an activity event
    """
    # Authorization: Students can only join classes for themselves
    if current_user.role == "student" and current_user.user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only join classes for themselves",
        )

    class_obj = student_service.join_class(db, student_id, join_data.class_code)

    return {
        "message": "Successfully joined class",
        "class": {
            "class_id": class_obj.class_id,
            "name": class_obj.name,
            "subject": class_obj.subject,
            "class_code": class_obj.class_code,
            "teacher_id": class_obj.teacher_id,
        },
    }
