"""
Teacher service containing business logic for teacher operations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Dict
from datetime import datetime
import secrets
import string
import random

from app.models.user import User
from app.models.class_model import Class
from app.models.class_student import ClassStudent
from app.models.student_request import StudentRequest, RequestStatus
from app.models.progress import StudentProgress, ProgressStatus
from app.schemas.teacher import (
    CreateClassRequest,
    UpdateClassRequest,
    StudentAccountRequestCreate,
    BulkStudentAccountRequest,
)


def generate_class_id() -> str:
    """Generate a unique class ID."""
    return f"class_{secrets.token_urlsafe(12)}"


def generate_class_code(subject: str = None) -> str:
    """
    Generate a unique class code in format: SUBJ-XXX-XXX

    Args:
        subject: Optional subject name for prefix

    Returns:
        str: Class code like "PHYS-ABC-123"
    """
    # Generate subject prefix (first 4 letters, uppercase)
    if subject:
        prefix = subject[:4].upper()
    else:
        prefix = "CLAS"

    # Generate two random 3-character segments
    chars = string.ascii_uppercase + string.digits
    segment1 = "".join(random.choices(chars, k=3))
    segment2 = "".join(random.choices(chars, k=3))

    return f"{prefix}-{segment1}-{segment2}"


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"request_{secrets.token_urlsafe(12)}"


def create_class(db: Session, teacher_id: str, class_data: CreateClassRequest) -> Class:
    """
    Create a new class.

    Args:
        db: Database session
        teacher_id: Teacher user ID
        class_data: Class creation data

    Returns:
        Class: Created class

    Raises:
        HTTPException: 404 if teacher not found
    """
    # Validate teacher exists
    teacher = db.query(User).filter(User.user_id == teacher_id, User.role == "teacher").first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    # Generate unique class code (retry if collision)
    max_retries = 5
    class_code = None
    for _ in range(max_retries):
        code = generate_class_code(class_data.subject)
        existing = db.query(Class).filter(Class.class_code == code).first()
        if not existing:
            class_code = code
            break

    if not class_code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique class code",
        )

    # Create class
    new_class = Class(
        class_id=generate_class_id(),
        teacher_id=teacher_id,
        name=class_data.name,
        subject=class_data.subject,
        class_code=class_code,
        description=class_data.description,
        grade_levels=class_data.grade_levels or [],
        school_id=teacher.school_id,
        organization_id=teacher.organization_id,
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    return new_class


def get_teacher_classes(db: Session, teacher_id: str, include_archived: bool = False) -> List[Class]:
    """
    Get all classes for a teacher.

    Args:
        db: Database session
        teacher_id: Teacher user ID
        include_archived: Include archived classes

    Returns:
        List[Class]: Teacher's classes
    """
    query = db.query(Class).filter(Class.teacher_id == teacher_id)

    if not include_archived:
        query = query.filter(Class.archived == False)

    return query.order_by(Class.created_at.desc()).all()


def get_class_details(db: Session, class_id: str, teacher_id: str = None) -> Class:
    """
    Get class details.

    Args:
        db: Database session
        class_id: Class ID
        teacher_id: Optional teacher ID for authorization

    Returns:
        Class: Class details

    Raises:
        HTTPException: 404 if class not found, 403 if unauthorized
    """
    class_obj = db.query(Class).filter(Class.class_id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    # Authorization: Only the teacher who owns the class can access
    if teacher_id and class_obj.teacher_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this class",
        )

    return class_obj


def update_class(db: Session, class_id: str, class_data: UpdateClassRequest, teacher_id: str = None) -> Class:
    """
    Update class details.

    Args:
        db: Database session
        class_id: Class ID
        class_data: Class update data
        teacher_id: Optional teacher user ID for authorization

    Returns:
        Class: Updated class

    Raises:
        HTTPException: 404 if class not found, 403 if unauthorized
    """
    class_obj = get_class_details(db, class_id, teacher_id)

    # Update fields
    if class_data.name is not None:
        class_obj.name = class_data.name
    if class_data.subject is not None:
        class_obj.subject = class_data.subject
    if class_data.description is not None:
        class_obj.description = class_data.description
    if class_data.grade_levels is not None:
        class_obj.grade_levels = class_data.grade_levels

    db.commit()
    db.refresh(class_obj)

    return class_obj


def archive_class(db: Session, class_id: str, teacher_id: str = None) -> Class:
    """
    Archive a class (soft delete).

    Args:
        db: Database session
        class_id: Class ID
        teacher_id: Optional teacher user ID for authorization

    Returns:
        Class: Archived class

    Raises:
        HTTPException: 404 if class not found, 403 if unauthorized
    """
    class_obj = get_class_details(db, class_id, teacher_id)

    class_obj.archived = True
    class_obj.archived_at = datetime.utcnow()

    db.commit()
    db.refresh(class_obj)

    return class_obj


def get_class_roster(db: Session, class_id: str, teacher_id: str = None) -> Dict:
    """
    Get class roster with student details and progress.

    Args:
        db: Database session
        class_id: Class ID
        teacher_id: Optional teacher user ID for authorization

    Returns:
        dict: Roster with students and their progress

    Raises:
        HTTPException: 404 if class not found, 403 if unauthorized
    """
    class_obj = get_class_details(db, class_id, teacher_id)

    # Get enrolled students
    students = (
        db.query(User, ClassStudent)
        .join(ClassStudent, User.user_id == ClassStudent.student_id)
        .filter(ClassStudent.class_id == class_id)
        .all()
    )

    # Build student list with progress
    student_list = []
    for user, enrollment in students:
        # Get progress summary
        total_started = db.query(StudentProgress).filter(
            StudentProgress.student_id == user.user_id,
            StudentProgress.status.in_([ProgressStatus.IN_PROGRESS, ProgressStatus.COMPLETED]),
        ).count()

        total_completed = db.query(StudentProgress).filter(
            StudentProgress.student_id == user.user_id,
            StudentProgress.status == ProgressStatus.COMPLETED,
        ).count()

        student_list.append({
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "grade_level": user.grade_level,
            "enrolled_at": enrollment.enrolled_at,
            "progress_summary": {
                "topics_started": total_started,
                "topics_completed": total_completed,
            },
        })

    return {
        "class_id": class_obj.class_id,
        "class_name": class_obj.name,
        "total_students": len(student_list),
        "students": student_list,
    }


def remove_student_from_class(db: Session, class_id: str, student_id: str, teacher_id: str = None) -> None:
    """
    Remove a student from a class.

    Args:
        db: Database session
        class_id: Class ID
        student_id: Student user ID
        teacher_id: Optional teacher user ID for authorization

    Raises:
        HTTPException: 404 if class/enrollment not found, 403 if unauthorized
    """
    # Validate class and authorization
    get_class_details(db, class_id, teacher_id)

    # Find enrollment
    enrollment = (
        db.query(ClassStudent)
        .filter(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not enrolled in this class",
        )

    db.delete(enrollment)
    db.commit()


def create_student_account_request(
    db: Session, teacher_id: str, request_data: StudentAccountRequestCreate
) -> StudentRequest:
    """
    Create a student account request.

    Args:
        db: Database session
        teacher_id: Teacher user ID
        request_data: Student account request data

    Returns:
        StudentRequest: Created request

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request_data.student_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Get teacher details for school/org context
    teacher = db.query(User).filter(User.user_id == teacher_id).first()

    # Create request
    request = StudentRequest(
        request_id=generate_request_id(),
        requested_by=teacher_id,
        student_email=request_data.student_email,
        student_first_name=request_data.student_first_name,
        student_last_name=request_data.student_last_name,
        grade_level=request_data.grade_level,
        class_id=request_data.class_id,
        school_id=teacher.school_id,
        organization_id=teacher.organization_id,
        notes=request_data.notes,
        status=RequestStatus.PENDING,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return request


def create_bulk_student_requests(
    db: Session, teacher_id: str, bulk_data: BulkStudentAccountRequest
) -> List[StudentRequest]:
    """
    Create multiple student account requests.

    Args:
        db: Database session
        teacher_id: Teacher user ID
        bulk_data: Bulk student requests

    Returns:
        List[StudentRequest]: Created requests

    Raises:
        HTTPException: 400 if any email already exists
    """
    # Check if any emails already exist
    emails = [s.student_email for s in bulk_data.students]
    existing_users = db.query(User.email).filter(User.email.in_(emails)).all()
    if existing_users:
        existing_emails = [u[0] for u in existing_users]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following emails already exist: {', '.join(existing_emails)}",
        )

    # Create all requests
    requests = []
    for student_data in bulk_data.students:
        request = create_student_account_request(db, teacher_id, student_data)
        requests.append(request)

    return requests


def get_teacher_requests(db: Session, teacher_id: str, status_filter: str = None) -> List[StudentRequest]:
    """
    Get teacher's student account requests.

    Args:
        db: Database session
        teacher_id: Teacher user ID
        status_filter: Optional status filter (pending, approved, rejected)

    Returns:
        List[StudentRequest]: Teacher's requests
    """
    query = db.query(StudentRequest).filter(StudentRequest.requested_by == teacher_id)

    if status_filter:
        query = query.filter(StudentRequest.status == status_filter)

    return query.order_by(StudentRequest.requested_at.desc()).all()


def get_teacher_dashboard(db: Session, teacher_id: str) -> Dict:
    """
    Get teacher dashboard data.

    Args:
        db: Database session
        teacher_id: Teacher user ID

    Returns:
        dict: Dashboard data with classes, students, requests
    """
    # Get all classes
    all_classes = db.query(Class).filter(Class.teacher_id == teacher_id).all()
    active_classes = [c for c in all_classes if not c.archived]

    # Get total student count across all classes
    total_students = (
        db.query(ClassStudent)
        .join(Class)
        .filter(Class.teacher_id == teacher_id, Class.archived == False)
        .count()
    )

    # Get pending requests count
    pending_requests = (
        db.query(StudentRequest)
        .filter(StudentRequest.requested_by == teacher_id, StudentRequest.status == RequestStatus.PENDING)
        .count()
    )

    # Build class summaries
    class_summaries = []
    for class_obj in all_classes:
        student_count = (
            db.query(ClassStudent)
            .filter(ClassStudent.class_id == class_obj.class_id)
            .count()
        )

        class_summaries.append({
            "class_id": class_obj.class_id,
            "name": class_obj.name,
            "subject": class_obj.subject,
            "class_code": class_obj.class_code,
            "student_count": student_count,
            "archived": class_obj.archived,
            "created_at": class_obj.created_at,
        })

    return {
        "teacher_id": teacher_id,
        "total_classes": len(all_classes),
        "active_classes": len(active_classes),
        "total_students": total_students,
        "pending_requests": pending_requests,
        "classes": class_summaries,
    }


# Wrapper functions for class operations without teacher_id (auth handled in endpoints)

def get_class_by_id(db: Session, class_id: str) -> Class:
    """
    Get class by ID without authorization check.
    Authorization should be handled in the endpoint layer.
    """
    return get_class_details(db, class_id, teacher_id=None)
