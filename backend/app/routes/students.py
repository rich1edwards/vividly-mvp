"""
Student Service API Routes

REST API for student profile, interests, and progress management.

Endpoints:
- GET /api/v1/students/profile - Get student profile
- PUT /api/v1/students/profile - Update student profile
- GET /api/v1/students/interests - Get student interests
- PUT /api/v1/students/interests - Update student interests
- GET /api/v1/students/progress - Get student progress

Sprint: Phase 2, Sprint 1
Epic: 1.2 Student Service
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..middleware.auth import get_current_active_user, require_role
from ..schemas.students import (
    UpdateProfileRequest,
    StudentProfileResponse,
    UpdateInterestsRequest,
    InterestsResponse,
    UpdateInterestsResponse,
    ProgressResponse,
    InterestDetail,
    ProgressSummary,
    ValidationErrorResponse,
)

router = APIRouter(prefix="/api/v1/students", tags=["Students"])


# Dependencies


def get_db() -> Session:
    """Get database session dependency."""
    raise NotImplementedError("Database dependency not configured")


def require_student(current_user: dict = Depends(get_current_active_user)) -> dict:
    """
    Require current user to be a student.

    Returns:
        Current user dict if role is 'student'

    Raises:
        HTTPException 403 if user is not a student
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Only students can access this endpoint",
                }
            },
        )
    return current_user


# Story 1.2.1: Student Profile Management (3 points)


@router.get(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student profile",
    description="""
    Get current student's profile information.

    - Fetches complete student profile
    - Includes interests with details
    - Includes progress summary
    - Only accessible to students (403 for other roles)

    Requires valid student JWT in Authorization header.
    """,
    responses={
        200: {"description": "Student profile retrieved"},
        401: {"description": "Unauthorized"},
        403: {
            "description": "Forbidden - Not a student",
            "model": ValidationErrorResponse,
        },
    },
)
async def get_student_profile(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Get current student's profile.

    API Contract Example:
        GET /api/v1/students/profile
        Authorization: Bearer <student-token>

        Response (200):
        {
            "student_id": "user_abc123",
            "email": "student@mnps.edu",
            "first_name": "John",
            "last_name": "Doe",
            "grade_level": 10,
            "school_id": "school_hillsboro_hs",
            "school_name": "Hillsboro High School",
            "interests": [
                {
                    "interest_id": "int_basketball",
                    "name": "Basketball",
                    "category": "sports",
                    "icon_url": "https://cdn.vividly.edu/icons/basketball.svg",
                    "selected_at": "2025-11-01T10:30:00Z"
                }
            ],
            "progress_summary": {
                "topics_completed": 5,
                "videos_watched": 12,
                "total_watch_time_minutes": 45,
                "streak_days": 3
            },
            "created_at": "2025-11-01T10:00:00Z"
        }
    """

    student_id = current_user["user_id"]

    # TODO: Fetch student profile from database
    # student = db.query(User).filter(
    #     User.user_id == student_id,
    #     User.role == "student"
    # ).first()
    # if not student:
    #     raise HTTPException(status_code=404, detail="Student not found")

    # TODO: Fetch student interests
    # interests = db.query(StudentInterest).join(Interest).filter(
    #     StudentInterest.student_id == student_id
    # ).all()
    # interest_details = [
    #     InterestDetail(
    #         interest_id=si.interest.interest_id,
    #         name=si.interest.name,
    #         category=si.interest.category,
    #         icon_url=si.interest.icon_url,
    #         selected_at=si.created_at
    #     )
    #     for si in interests
    # ]

    # TODO: Fetch school information
    # school = db.query(School).filter(School.school_id == student.school_id).first()
    # school_name = school.name if school else None

    # TODO: Calculate progress summary
    # progress_summary = calculate_student_progress_summary(student_id, db)
    # # This should query student_progress table and calculate:
    # # - topics_completed
    # # - videos_watched
    # # - total_watch_time_minutes
    # # - streak_days

    # TODO: Return student profile response
    # return StudentProfileResponse(
    #     student_id=student.user_id,
    #     email=student.email,
    #     first_name=student.first_name,
    #     last_name=student.last_name,
    #     grade_level=student.grade_level,
    #     school_id=student.school_id,
    #     school_name=school_name,
    #     interests=interest_details,
    #     progress_summary=progress_summary,
    #     created_at=student.created_at
    # )

    raise NotImplementedError("Get student profile endpoint not implemented")


@router.put(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student profile",
    description="""
    Update student profile information.

    - Updates allowed fields only (first_name, last_name, grade_level)
    - Cannot change email or role (security)
    - Validates all changes
    - Only accessible to students

    Requires valid student JWT in Authorization header.
    """,
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"description": "Unauthorized"},
        403: {
            "description": "Forbidden - Not a student",
            "model": ValidationErrorResponse,
        },
        422: {"description": "Validation error", "model": ValidationErrorResponse},
    },
)
async def update_student_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Update student profile.

    API Contract Example:
        PUT /api/v1/students/profile
        Authorization: Bearer <student-token>
        Content-Type: application/json

        {
            "first_name": "Jonathan",
            "grade_level": 11
        }

        Response (200):
        {
            "student_id": "user_abc123",
            "first_name": "Jonathan",
            "last_name": "Doe",
            "grade_level": 11,
            ...
        }
    """

    student_id = current_user["user_id"]

    # TODO: Fetch student from database
    # student = db.query(User).filter(User.user_id == student_id).first()
    # if not student:
    #     raise HTTPException(status_code=404, detail="Student not found")

    # TODO: Update allowed fields
    # if request.first_name is not None:
    #     student.first_name = request.first_name
    # if request.last_name is not None:
    #     student.last_name = request.last_name
    # if request.grade_level is not None:
    #     student.grade_level = request.grade_level
    #
    # student.updated_at = datetime.utcnow()
    # db.commit()
    # db.refresh(student)

    # TODO: Fetch updated profile (reuse logic from GET /profile)
    # return get_student_profile(current_user, db)

    raise NotImplementedError("Update student profile endpoint not implemented")


# Story 1.2.2: Interest Selection & Management (3 points)


@router.get(
    "/interests",
    response_model=InterestsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student interests",
    description="""
    Get current student's interests.

    - Returns list of selected interests with details
    - Includes interest metadata (name, category, icon)
    - Only accessible to students

    Requires valid student JWT in Authorization header.
    """,
    responses={
        200: {"description": "Interests retrieved"},
        401: {"description": "Unauthorized"},
        403: {
            "description": "Forbidden - Not a student",
            "model": ValidationErrorResponse,
        },
    },
)
async def get_student_interests(
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Get student's current interests.

    API Contract Example:
        GET /api/v1/students/interests
        Authorization: Bearer <student-token>

        Response (200):
        {
            "student_id": "user_abc123",
            "interests": [
                {
                    "interest_id": "int_basketball",
                    "name": "Basketball",
                    "category": "sports",
                    "icon_url": "https://cdn.vividly.edu/icons/basketball.svg",
                    "selected_at": "2025-11-01T10:30:00Z"
                },
                {
                    "interest_id": "int_music",
                    "name": "Music Production",
                    "category": "arts",
                    "icon_url": "https://cdn.vividly.edu/icons/music.svg",
                    "selected_at": "2025-11-01T10:30:00Z"
                }
            ]
        }
    """

    student_id = current_user["user_id"]

    # TODO: Fetch student interests from database
    # interests = db.query(StudentInterest).join(Interest).filter(
    #     StudentInterest.student_id == student_id
    # ).all()

    # TODO: Build interest details list
    # interest_details = [
    #     InterestDetail(
    #         interest_id=si.interest.interest_id,
    #         name=si.interest.name,
    #         category=si.interest.category,
    #         icon_url=si.interest.icon_url,
    #         selected_at=si.created_at
    #     )
    #     for si in interests
    # ]

    # TODO: Return interests response
    # return InterestsResponse(
    #     student_id=student_id,
    #     interests=interest_details
    # )

    raise NotImplementedError("Get student interests endpoint not implemented")


@router.put(
    "/interests",
    response_model=UpdateInterestsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update student interests",
    description="""
    Update student's selected interests.

    - Validates interest IDs exist in canonical list
    - Enforces 1-5 interest limit
    - Prevents duplicate interests
    - Replaces all existing interests
    - Only accessible to students

    Returns 422 for invalid interest IDs or constraint violations.
    """,
    responses={
        200: {"description": "Interests updated successfully"},
        401: {"description": "Unauthorized"},
        403: {
            "description": "Forbidden - Not a student",
            "model": ValidationErrorResponse,
        },
        422: {"description": "Validation error", "model": ValidationErrorResponse},
    },
)
async def update_student_interests(
    request: UpdateInterestsRequest,
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Update student's interests.

    API Contract Example:
        PUT /api/v1/students/interests
        Authorization: Bearer <student-token>
        Content-Type: application/json

        {
            "interest_ids": ["int_basketball", "int_music", "int_coding"]
        }

        Response (200):
        {
            "student_id": "user_abc123",
            "interests": [
                {"interest_id": "int_basketball", ...},
                {"interest_id": "int_music", ...},
                {"interest_id": "int_coding", ...}
            ],
            "updated_at": "2025-11-04T14:20:00Z"
        }

        Error (422):
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "You must select between 1 and 5 interests",
                "details": {
                    "field": "interest_ids",
                    "constraint": "length",
                    "min": 1,
                    "max": 5,
                    "actual": 6
                }
            }
        }
    """

    student_id = current_user["user_id"]

    # TODO: Validate all interest IDs exist in canonical interests table
    # interests = db.query(Interest).filter(
    #     Interest.interest_id.in_(request.interest_ids)
    # ).all()
    # found_ids = {i.interest_id for i in interests}
    # invalid_ids = set(request.interest_ids) - found_ids
    # if invalid_ids:
    #     raise HTTPException(
    #         status_code=422,
    #         detail={
    #             "error": {
    #                 "code": "VALIDATION_ERROR",
    #                 "message": f"Invalid interest IDs: {', '.join(invalid_ids)}",
    #                 "details": {
    #                     "field": "interest_ids",
    #                     "invalid_values": list(invalid_ids)
    #                 }
    #             }
    #         }
    #     )

    # TODO: Delete existing interests
    # db.query(StudentInterest).filter(
    #     StudentInterest.student_id == student_id
    # ).delete()

    # TODO: Insert new interests
    # for interest_id in request.interest_ids:
    #     student_interest = StudentInterest(
    #         student_id=student_id,
    #         interest_id=interest_id,
    #         created_at=datetime.utcnow()
    #     )
    #     db.add(student_interest)
    # db.commit()

    # TODO: Fetch updated interests with details
    # updated_interests = db.query(StudentInterest).join(Interest).filter(
    #     StudentInterest.student_id == student_id
    # ).all()
    # interest_details = [
    #     InterestDetail(
    #         interest_id=si.interest.interest_id,
    #         name=si.interest.name,
    #         category=si.interest.category,
    #         icon_url=si.interest.icon_url,
    #         selected_at=si.created_at
    #     )
    #     for si in updated_interests
    # ]

    # TODO: Return updated interests response
    # return UpdateInterestsResponse(
    #     student_id=student_id,
    #     interests=interest_details,
    #     updated_at=datetime.utcnow()
    # )

    raise NotImplementedError("Update student interests endpoint not implemented")


# Story 1.2.3: Student Progress Tracking (2 points)


@router.get(
    "/progress",
    response_model=ProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student progress",
    description="""
    Get student's learning progress and activity.

    - Returns comprehensive progress summary
    - Returns recent activity timeline (last 10 items)
    - Returns topic completion matrix by subject
    - Supports filtering by subject and date range
    - Calculates learning streak
    - Only accessible to students

    Query Parameters:
    - subject (optional): Filter by subject (e.g., "Physics", "Chemistry")
    - date_from (optional): Filter activity from date (ISO 8601)
    - date_to (optional): Filter activity to date (ISO 8601)
    """,
    responses={
        200: {"description": "Progress retrieved"},
        401: {"description": "Unauthorized"},
        403: {
            "description": "Forbidden - Not a student",
            "model": ValidationErrorResponse,
        },
    },
)
async def get_student_progress(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO 8601)"),
    current_user: dict = Depends(require_student),
    db: Session = Depends(get_db),
):
    """
    Get student's learning progress.

    API Contract Example:
        GET /api/v1/students/progress?subject=physics&date_from=2025-11-01
        Authorization: Bearer <student-token>

        Response (200):
        {
            "student_id": "user_abc123",
            "summary": {
                "topics_completed": 5,
                "videos_watched": 12,
                "total_watch_time_minutes": 45,
                "streak_days": 3,
                "last_active": "2025-11-04T09:15:00Z"
            },
            "recent_activity": [
                {
                    "activity_id": "act_001",
                    "type": "video_completed",
                    "topic_id": "topic_phys_mech_newton_3",
                    "topic_name": "Newton's Third Law",
                    "interest": "basketball",
                    "completed_at": "2025-11-04T09:15:00Z",
                    "watch_duration_seconds": 180
                }
            ],
            "topic_matrix": {
                "Physics": {
                    "Mechanics": {
                        "completed": 3,
                        "total": 10,
                        "topics": [
                            {
                                "topic_id": "topic_phys_mech_newton_1",
                                "name": "Newton's First Law",
                                "status": "completed",
                                "completed_at": "2025-11-02T10:00:00Z",
                                "progress_percentage": 100
                            }
                        ]
                    }
                }
            }
        }
    """

    student_id = current_user["user_id"]

    # TODO: Parse date filters
    # from datetime import datetime
    # date_from_dt = datetime.fromisoformat(date_from) if date_from else None
    # date_to_dt = datetime.fromisoformat(date_to) if date_to else None

    # TODO: Calculate progress summary
    # summary = calculate_student_progress_summary(student_id, db, subject, date_from_dt, date_to_dt)
    # This should query student_progress and calculate:
    # - topics_completed
    # - videos_watched
    # - total_watch_time_minutes
    # - streak_days (consecutive days with activity)
    # - last_active

    # TODO: Fetch recent activity (last 10 items)
    # query = db.query(StudentActivity).filter(
    #     StudentActivity.student_id == student_id
    # )
    # if subject:
    #     query = query.join(Topic).filter(Topic.subject == subject)
    # if date_from_dt:
    #     query = query.filter(StudentActivity.completed_at >= date_from_dt)
    # if date_to_dt:
    #     query = query.filter(StudentActivity.completed_at <= date_to_dt)
    #
    # activities = query.order_by(
    #     StudentActivity.completed_at.desc()
    # ).limit(10).all()
    #
    # activity_items = [
    #     ActivityItem(
    #         activity_id=a.activity_id,
    #         type=a.activity_type,
    #         topic_id=a.topic_id,
    #         topic_name=a.topic.name,
    #         interest=a.interest_id,
    #         completed_at=a.completed_at,
    #         watch_duration_seconds=a.watch_duration_seconds
    #     )
    #     for a in activities
    # ]

    # TODO: Build topic completion matrix
    # topic_matrix = build_topic_matrix(student_id, db, subject)
    # This should:
    # 1. Query all topics (optionally filtered by subject)
    # 2. Join with student_progress to get completion status
    # 3. Group by Subject -> Unit
    # 4. Calculate completed/total for each unit
    # 5. Return nested dict structure

    # TODO: Return progress response
    # return ProgressResponse(
    #     student_id=student_id,
    #     summary=summary,
    #     recent_activity=activity_items,
    #     topic_matrix=topic_matrix
    # )

    raise NotImplementedError("Get student progress endpoint not implemented")
