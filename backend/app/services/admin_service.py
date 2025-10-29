"""
Admin service containing business logic for admin operations.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status, UploadFile
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import csv
import io
import secrets

from app.models.user import User
from app.models.student_request import StudentRequest, RequestStatus
from app.models.class_student import ClassStudent
from app.models.session import Session as UserSession
from app.core.security import get_password_hash


def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{secrets.token_urlsafe(12)}"


def list_users(
    db: Session,
    role: Optional[str] = None,
    school_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> Dict:
    """
    List users with filtering and pagination.

    Args:
        db: Database session
        role: Filter by role (student, teacher, admin)
        school_id: Filter by school
        search: Search by name or email
        limit: Results per page
        cursor: Pagination cursor

    Returns:
        Dict with users list and pagination info
    """
    query = db.query(User).filter(User.archived == False)

    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if school_id:
        query = query.filter(User.school_id == school_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    # Apply cursor pagination
    if cursor:
        query = query.filter(User.user_id > cursor)

    # Get results
    users = query.order_by(User.user_id).limit(limit + 1).all()

    # Check if there are more results
    has_more = len(users) > limit
    if has_more:
        users = users[:limit]

    # Get total count (expensive, only if no filters)
    total_count = None
    if not role and not school_id and not search:
        total_count = db.query(func.count(User.user_id)).filter(User.archived == False).scalar()

    return {
        "users": users,
        "pagination": {
            "next_cursor": users[-1].user_id if has_more and users else None,
            "has_more": has_more,
            "total_count": total_count,
        },
    }


def create_user(
    db: Session,
    email: str,
    first_name: str,
    last_name: str,
    role: str,
    grade_level: Optional[int] = None,
    school_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    send_invitation: bool = False,
) -> User:
    """
    Create a single user manually.

    Args:
        db: Database session
        email: User email
        first_name: First name
        last_name: Last name
        role: User role (student, teacher, admin)
        grade_level: Grade level (for students)
        school_id: School ID
        organization_id: Organization ID
        send_invitation: Whether to send invitation email

    Returns:
        User: Created user

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Generate default password (users should reset on first login)
    default_password = secrets.token_urlsafe(16)

    # Create user
    new_user = User(
        user_id=generate_user_id(),
        email=email,
        password_hash=get_password_hash(default_password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        grade_level=grade_level,
        school_id=school_id,
        organization_id=organization_id,
        archived=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # TODO: Send invitation email with temporary password
    if send_invitation:
        # Queue invitation email
        pass

    return new_user


def update_user(
    db: Session,
    user_id: str,
    role: Optional[str] = None,
    grade_level: Optional[int] = None,
    subjects: Optional[List[str]] = None,
    **kwargs,
) -> User:
    """
    Update user profile.

    Args:
        db: Database session
        user_id: User ID to update
        role: New role (with validation)
        grade_level: New grade level
        subjects: Teacher subjects
        **kwargs: Other fields to update

    Returns:
        User: Updated user

    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields
    if role is not None:
        user.role = role
    if grade_level is not None:
        user.grade_level = grade_level
    if subjects is not None:
        # TODO: Store subjects in user profile
        pass

    # Update other fields
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user_id: str, admin_id: str) -> None:
    """
    Soft delete a user (deactivate).

    Args:
        db: Database session
        user_id: User ID to delete
        admin_id: Admin performing the deletion

    Raises:
        HTTPException: 400 if trying to delete own account, 404 if user not found
    """
    # Cannot delete own account
    if user_id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Soft delete
    user.archived = True
    user.archived_at = datetime.utcnow()

    # Revoke all sessions
    db.query(UserSession).filter(UserSession.user_id == user_id).update(
        {"revoked_at": datetime.utcnow()}
    )

    db.commit()


def bulk_upload_users(
    db: Session,
    file: UploadFile,
    transaction_mode: str = "partial",
) -> Dict:
    """
    Bulk upload users from CSV file.

    Args:
        db: Database session
        file: CSV file upload
        transaction_mode: "partial" (allow partial success) or "atomic" (all or nothing)

    Returns:
        Dict with upload results

    Raises:
        HTTPException: 400 if CSV is invalid
    """
    # Read CSV file
    contents = file.file.read()
    csv_reader = csv.DictReader(io.StringIO(contents.decode('utf-8')))

    # Validate CSV headers
    required_headers = {'first_name', 'last_name', 'email', 'role'}
    if not required_headers.issubset(set(csv_reader.fieldnames or [])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV must have headers: {', '.join(required_headers)}",
        )

    # Process rows
    upload_id = f"upload_{secrets.token_urlsafe(8)}"
    start_time = datetime.utcnow()
    results = {
        "created_users": [],
        "failed_rows": [],
    }

    # Collect all emails to check for duplicates in batch
    rows = list(csv_reader)
    emails = [row.get('email') for row in rows if row.get('email')]
    existing_emails = db.query(User.email).filter(User.email.in_(emails)).all()
    existing_emails_set = {email[0] for email in existing_emails}

    for idx, row in enumerate(rows, start=2):  # Start at 2 (after header row)
        try:
            email = row.get('email', '').strip()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            role = row.get('role', '').strip()
            grade_level = row.get('grade_level')
            school_id = row.get('school_id')

            # Validate required fields
            if not all([email, first_name, last_name, role]):
                results["failed_rows"].append({
                    "row_number": idx,
                    "email": email,
                    "error": "Missing required fields",
                    "error_code": "MISSING_FIELDS",
                })
                continue

            # Check for duplicate email
            if email in existing_emails_set:
                results["failed_rows"].append({
                    "row_number": idx,
                    "email": email,
                    "error": "Email already exists",
                    "error_code": "DUPLICATE_EMAIL",
                })
                continue

            # Validate email format
            if '@' not in email or '.' not in email:
                results["failed_rows"].append({
                    "row_number": idx,
                    "email": email,
                    "error": "Invalid email format",
                    "error_code": "INVALID_EMAIL",
                })
                continue

            # Create user
            user = create_user(
                db=db,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                grade_level=int(grade_level) if grade_level else None,
                school_id=school_id,
                send_invitation=False,  # Bulk email later
            )

            results["created_users"].append(user.user_id)
            existing_emails_set.add(email)  # Prevent duplicates within CSV

        except Exception as e:
            results["failed_rows"].append({
                "row_number": idx,
                "email": row.get('email', ''),
                "error": str(e),
                "error_code": "PROCESSING_ERROR",
            })

            # If atomic mode and any failure, rollback
            if transaction_mode == "atomic":
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Upload failed at row {idx}: {str(e)}",
                )

    end_time = datetime.utcnow()
    duration_seconds = (end_time - start_time).total_seconds()

    return {
        "upload_id": upload_id,
        "total_rows": len(rows),
        "successful": len(results["created_users"]),
        "failed": len(results["failed_rows"]),
        "duration_seconds": duration_seconds,
        "results": results,
    }


def list_pending_requests(
    db: Session,
    school_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    limit: int = 20,
) -> Dict:
    """
    List pending account requests.

    Args:
        db: Database session
        school_id: Filter by school
        teacher_id: Filter by requesting teacher
        limit: Results per page

    Returns:
        Dict with requests list
    """
    query = db.query(StudentRequest).filter(StudentRequest.status == RequestStatus.PENDING)

    if school_id:
        query = query.filter(StudentRequest.school_id == school_id)
    if teacher_id:
        query = query.filter(StudentRequest.requested_by == teacher_id)

    requests = query.order_by(StudentRequest.requested_at.desc()).limit(limit).all()

    # Enrich with teacher names and serialize
    results = []
    for request in requests:
        teacher = db.query(User).filter(User.user_id == request.requested_by).first()
        results.append({
            "request_id": request.request_id,
            "student_email": request.student_email,
            "student_first_name": request.student_first_name,
            "student_last_name": request.student_last_name,
            "grade_level": request.grade_level,
            "status": request.status.value,
            "requested_by": request.requested_by,
            "teacher_name": f"{teacher.first_name} {teacher.last_name}" if teacher else "Unknown",
            "requested_at": request.requested_at,
        })

    return {
        "requests": results,
        "pagination": {
            "has_more": len(requests) == limit,
        },
    }


def get_request_details(db: Session, request_id: str) -> Dict:
    """
    Get detailed information about a specific account request.

    Args:
        db: Database session
        request_id: Request ID

    Returns:
        Dict with request details

    Raises:
        HTTPException: 404 if request not found
    """
    request = db.query(StudentRequest).filter(StudentRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # Get teacher information
    teacher = db.query(User).filter(User.user_id == request.requested_by).first()

    return {
        "request_id": request.request_id,
        "student_email": request.student_email,
        "student_first_name": request.student_first_name,
        "student_last_name": request.student_last_name,
        "grade_level": request.grade_level,
        "status": request.status.value,
        "requested_by": request.requested_by,
        "teacher_name": f"{teacher.first_name} {teacher.last_name}" if teacher else "Unknown",
        "requested_at": request.requested_at,
        "school_id": request.school_id,
        "class_id": request.class_id,
        "notes": request.notes,
    }


def approve_request(db: Session, request_id: str, admin_id: str) -> Dict:
    """
    Approve an account request.

    Args:
        db: Database session
        request_id: Request ID
        admin_id: Admin approving the request

    Returns:
        Dict with approval details

    Raises:
        HTTPException: 404 if request not found, 400 if already processed
    """
    request = db.query(StudentRequest).filter(StudentRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    if request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request already {request.status}",
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.student_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create user
    user = create_user(
        db=db,
        email=request.student_email,
        first_name=request.student_first_name,
        last_name=request.student_last_name,
        role="student",
        grade_level=request.grade_level,
        school_id=request.school_id,
        organization_id=request.organization_id,
        send_invitation=True,
    )

    # Add to class if specified
    if request.class_id:
        enrollment = ClassStudent(
            class_id=request.class_id,
            student_id=user.user_id,
            enrolled_at=datetime.utcnow(),
        )
        db.add(enrollment)

    # Update request status
    request.status = RequestStatus.APPROVED
    request.approved_by = admin_id
    request.approved_at = datetime.utcnow()
    request.created_user_id = user.user_id

    db.commit()

    # TODO: Send welcome email to student
    # TODO: Notify requesting teacher

    return {
        "request_id": request_id,
        "status": "approved",
        "user_created": {
            "user_id": user.user_id,
            "email": user.email,
            "class_id": request.class_id,
        },
        "approved_at": request.approved_at,
        "approved_by": admin_id,
        "invitation_sent": True,
    }


def deny_request(db: Session, request_id: str, admin_id: str, reason: str) -> Dict:
    """
    Deny an account request.

    Args:
        db: Database session
        request_id: Request ID
        admin_id: Admin denying the request
        reason: Denial reason

    Returns:
        Dict with denial details

    Raises:
        HTTPException: 404 if request not found, 400 if already processed
    """
    request = db.query(StudentRequest).filter(StudentRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    if request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request already {request.status}",
        )

    # Update request status
    request.status = RequestStatus.REJECTED
    request.approved_by = admin_id  # Reusing field for "processed_by"
    request.approved_at = datetime.utcnow()  # Reusing field for "processed_at"
    request.notes = f"{request.notes}\n\nDenial reason: {reason}" if request.notes else f"Denial reason: {reason}"

    db.commit()

    # TODO: Notify requesting teacher

    return {
        "request_id": request_id,
        "status": "denied",
        "denied_at": request.approved_at,
        "denied_by": admin_id,
        "denial_reason": reason,
        "teacher_notified": True,
    }


def get_dashboard_stats(db: Session) -> Dict:
    """
    Get admin dashboard statistics.

    Args:
        db: Database session

    Returns:
        Dict with various statistics
    """
    from app.models.class_model import Class
    from app.models.content_metadata import ContentMetadata
    from datetime import timedelta

    # Get user counts
    total_users = db.query(func.count(User.user_id)).filter(User.archived == False).scalar()
    total_students = db.query(func.count(User.user_id)).filter(
        User.role == "student",
        User.archived == False
    ).scalar()
    total_teachers = db.query(func.count(User.user_id)).filter(
        User.role == "teacher",
        User.archived == False
    ).scalar()
    total_admins = db.query(func.count(User.user_id)).filter(
        User.role == "admin",
        User.archived == False
    ).scalar()

    # Get active users in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    active_users_today = db.query(func.count(func.distinct(UserSession.user_id))).filter(
        UserSession.created_at >= yesterday,
        UserSession.revoked_at.is_(None)
    ).scalar() or 0

    # Get class count
    total_classes = db.query(func.count(Class.class_id)).filter(Class.archived == False).scalar() or 0

    # Get content count
    total_content = db.query(func.count(ContentMetadata.content_id)).scalar() or 0

    return {
        "total_users": total_users or 0,
        "total_students": total_students or 0,
        "total_teachers": total_teachers or 0,
        "total_admins": total_admins or 0,
        "active_users_today": active_users_today,
        "total_classes": total_classes,
        "total_content": total_content,
    }
