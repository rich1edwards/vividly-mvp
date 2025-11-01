"""
Student service containing business logic for student operations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import secrets

from app.models.user import User
from app.models.interest import Interest, StudentInterest
from app.models.progress import (
    StudentProgress,
    StudentActivity,
    Topic,
    ProgressStatus,
    ActivityType,
)
from app.models.class_student import ClassStudent
from app.models.class_model import Class
from app.schemas.student import (
    StudentProfileUpdate,
    StudentInterestsUpdate,
    LearningProgress,
    TopicProgress,
    StudentActivity as StudentActivitySchema,
)


def generate_progress_id() -> str:
    """Generate a unique progress ID."""
    return f"progress_{secrets.token_urlsafe(12)}"


def generate_activity_id() -> str:
    """Generate a unique activity ID."""
    return f"activity_{secrets.token_urlsafe(12)}"


def get_student_profile(db: Session, student_id: str) -> Dict:
    """
    Get complete student profile with interests and classes.

    Args:
        db: Database session
        student_id: Student user ID

    Returns:
        dict: Complete student profile

    Raises:
        HTTPException: 404 if student not found
    """
    # Get student
    student = (
        db.query(User)
        .filter(User.user_id == student_id, User.role == "student")
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Get interests
    interests = (
        db.query(Interest)
        .join(StudentInterest)
        .filter(StudentInterest.student_id == student_id)
        .all()
    )

    # Get enrolled classes
    enrolled_classes = (
        db.query(Class)
        .join(ClassStudent)
        .filter(ClassStudent.student_id == student_id, Class.archived == False)
        .all()
    )

    # Get progress summary
    total_started = (
        db.query(StudentProgress)
        .filter(
            StudentProgress.student_id == student_id,
            StudentProgress.status.in_(
                [ProgressStatus.IN_PROGRESS, ProgressStatus.COMPLETED]
            ),
        )
        .count()
    )

    total_completed = (
        db.query(StudentProgress)
        .filter(
            StudentProgress.student_id == student_id,
            StudentProgress.status == ProgressStatus.COMPLETED,
        )
        .count()
    )

    total_watch_time = (
        db.query(StudentProgress.total_watch_time_seconds)
        .filter(StudentProgress.student_id == student_id)
        .all()
    )
    total_watch_seconds = sum([t[0] or 0 for t in total_watch_time])

    return {
        "user_id": student.user_id,
        "email": student.email,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "role": student.role,
        "status": student.status,
        "grade_level": student.grade_level,
        "school_id": student.school_id,
        "organization_id": student.organization_id,
        "created_at": student.created_at,
        "last_login_at": student.last_login_at,
        "interests": [
            {
                "interest_id": i.interest_id,
                "name": i.name,
                "category": i.category,
            }
            for i in interests
        ],
        "enrolled_classes": [
            {
                "class_id": c.class_id,
                "name": c.name,
                "subject": c.subject,
                "class_code": c.class_code,
                "teacher_id": c.teacher_id,
            }
            for c in enrolled_classes
        ],
        "progress_summary": {
            "total_topics_started": total_started,
            "total_topics_completed": total_completed,
            "total_watch_time_seconds": total_watch_seconds,
        },
    }


def update_student_profile(
    db: Session, student_id: str, profile_data: StudentProfileUpdate
) -> User:
    """
    Update student profile (name, grade level only).

    Args:
        db: Database session
        student_id: Student user ID
        profile_data: Profile update data

    Returns:
        User: Updated student

    Raises:
        HTTPException: 404 if student not found
    """
    student = (
        db.query(User)
        .filter(User.user_id == student_id, User.role == "student")
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Update allowed fields
    if profile_data.first_name is not None:
        student.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        student.last_name = profile_data.last_name
    if profile_data.grade_level is not None:
        student.grade_level = profile_data.grade_level

    db.commit()
    db.refresh(student)

    # Log activity
    log_activity(
        db,
        student_id=student_id,
        activity_type=ActivityType.PROFILE_UPDATED,
        metadata={"updated_fields": profile_data.dict(exclude_unset=True)},
    )

    return student


def get_student_interests(db: Session, student_id: str) -> List[Interest]:
    """
    Get student's selected interests.

    Args:
        db: Database session
        student_id: Student user ID

    Returns:
        List[Interest]: Student's interests
    """
    interests = (
        db.query(Interest)
        .join(StudentInterest)
        .filter(StudentInterest.student_id == student_id)
        .all()
    )
    return interests


def update_student_interests(
    db: Session, student_id: str, interests_data: StudentInterestsUpdate
) -> List[Interest]:
    """
    Update student's interests (1-5 interests).

    Args:
        db: Database session
        student_id: Student user ID
        interests_data: Interest IDs to set

    Returns:
        List[Interest]: Updated interests

    Raises:
        HTTPException: 400 if validation fails, 404 if interest not found
    """
    # Validate student exists
    student = (
        db.query(User)
        .filter(User.user_id == student_id, User.role == "student")
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Validate interests exist
    interests = (
        db.query(Interest)
        .filter(Interest.interest_id.in_(interests_data.interest_ids))
        .all()
    )
    if len(interests) != len(interests_data.interest_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more interests not found",
        )

    # Remove existing interests
    db.query(StudentInterest).filter(StudentInterest.student_id == student_id).delete()

    # Add new interests
    for interest_id in interests_data.interest_ids:
        student_interest = StudentInterest(
            student_id=student_id,
            interest_id=interest_id,
        )
        db.add(student_interest)

    db.commit()

    # Log activity
    log_activity(
        db,
        student_id=student_id,
        activity_type=ActivityType.INTEREST_UPDATED,
        metadata={"interest_ids": interests_data.interest_ids},
    )

    return interests


def get_learning_progress(db: Session, student_id: str) -> LearningProgress:
    """
    Get complete learning progress for student.

    Args:
        db: Database session
        student_id: Student user ID

    Returns:
        LearningProgress: Complete learning progress with streak

    Raises:
        HTTPException: 404 if student not found
    """
    # Validate student exists
    student = (
        db.query(User)
        .filter(User.user_id == student_id, User.role == "student")
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Get all progress entries with topic details
    progress_entries = (
        db.query(StudentProgress, Topic)
        .join(Topic, StudentProgress.topic_id == Topic.topic_id)
        .filter(StudentProgress.student_id == student_id)
        .all()
    )

    # Build topic progress list
    topics = []
    for progress, topic in progress_entries:
        topics.append(
            TopicProgress(
                topic_id=topic.topic_id,
                topic_name=topic.name,
                subject=topic.subject,
                status=progress.status.value,
                progress_percentage=progress.progress_percentage,
                videos_watched=progress.videos_watched,
                total_watch_time_seconds=progress.total_watch_time_seconds,
                started_at=progress.started_at,
                completed_at=progress.completed_at,
            )
        )

    # Get recent activity (last 10)
    recent_activities = (
        db.query(StudentActivity)
        .filter(StudentActivity.student_id == student_id)
        .order_by(StudentActivity.created_at.desc())
        .limit(10)
        .all()
    )

    activity_list = [
        StudentActivitySchema(
            activity_id=a.activity_id,
            activity_type=a.activity_type.value,
            created_at=a.created_at,
            topic_id=a.topic_id,
            duration_seconds=a.duration_seconds,
        )
        for a in recent_activities
    ]

    # Calculate totals
    total_started = len([t for t in topics if t.status != "not_started"])
    total_completed = len([t for t in topics if t.status == "completed"])
    total_watch_time = sum([t.total_watch_time_seconds for t in topics])

    # Calculate learning streak
    streak_days = calculate_learning_streak(db, student_id)

    return LearningProgress(
        topics=topics,
        recent_activity=activity_list,
        total_topics_started=total_started,
        total_topics_completed=total_completed,
        total_watch_time_seconds=total_watch_time,
        learning_streak_days=streak_days,
    )


def calculate_learning_streak(db: Session, student_id: str) -> int:
    """
    Calculate consecutive days of learning activity.

    Args:
        db: Database session
        student_id: Student user ID

    Returns:
        int: Number of consecutive days with activity
    """
    # Get activities from last 30 days, grouped by date
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    activities = (
        db.query(StudentActivity)
        .filter(
            StudentActivity.student_id == student_id,
            StudentActivity.created_at >= thirty_days_ago,
        )
        .order_by(StudentActivity.created_at.desc())
        .all()
    )

    if not activities:
        return 0

    # Get unique dates (UTC)
    activity_dates = set()
    for activity in activities:
        activity_dates.add(activity.created_at.date())

    # Calculate streak from today backwards
    streak = 0
    current_date = datetime.utcnow().date()

    while current_date in activity_dates:
        streak += 1
        current_date = current_date - timedelta(days=1)

        # Cap at 30 days
        if streak >= 30:
            break

    return streak


def join_class(db: Session, student_id: str, class_code: str) -> Class:
    """
    Join a class by class code.

    Args:
        db: Database session
        student_id: Student user ID
        class_code: Class code to join (e.g., "PHYS-ABC-123")

    Returns:
        Class: The joined class

    Raises:
        HTTPException: 404 if class not found, 400 if already enrolled or class archived
    """
    # Validate student exists
    student = (
        db.query(User)
        .filter(User.user_id == student_id, User.role == "student")
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Find class by code
    class_obj = db.query(Class).filter(Class.class_code == class_code).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found with this code",
        )

    # Check if class is archived
    if class_obj.archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This class is archived and no longer accepting students",
        )

    # Check if already enrolled
    existing_enrollment = (
        db.query(ClassStudent)
        .filter(
            ClassStudent.class_id == class_obj.class_id,
            ClassStudent.student_id == student_id,
        )
        .first()
    )
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this class",
        )

    # Create enrollment
    enrollment = ClassStudent(
        class_id=class_obj.class_id,
        student_id=student_id,
    )
    db.add(enrollment)
    db.commit()

    # Log activity
    log_activity(
        db,
        student_id=student_id,
        activity_type=ActivityType.CLASS_JOINED,
        class_id=class_obj.class_id,
        metadata={"class_code": class_code, "class_name": class_obj.name},
    )

    return class_obj


def log_activity(
    db: Session,
    student_id: str,
    activity_type: ActivityType,
    topic_id: Optional[str] = None,
    content_id: Optional[str] = None,
    class_id: Optional[str] = None,
    interest_id: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    metadata: Optional[Dict] = None,
) -> StudentActivity:
    """
    Log student activity.

    Args:
        db: Database session
        student_id: Student user ID
        activity_type: Type of activity
        topic_id: Optional topic ID
        content_id: Optional content ID
        class_id: Optional class ID
        interest_id: Optional interest ID
        duration_seconds: Optional duration
        metadata: Optional additional metadata

    Returns:
        StudentActivity: Created activity record
    """
    activity = StudentActivity(
        activity_id=generate_activity_id(),
        student_id=student_id,
        activity_type=activity_type,
        topic_id=topic_id,
        content_id=content_id,
        class_id=class_id,
        interest_id=interest_id,
        duration_seconds=duration_seconds,
        meta_data=metadata or {},
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity
