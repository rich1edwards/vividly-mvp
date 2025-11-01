"""
Admin API endpoints.

Endpoints for admin operations: user management, bulk uploads, and account request approval.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.admin import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    BulkUploadResponse,
    RequestListResponse,
    ApproveRequestResponse,
    DenyRequestRequest,
    DenyRequestResponse,
)
from app.services import admin_service
from app.utils.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for endpoint access."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/users", response_model=UserListResponse)
async def list_users(
    role: Optional[str] = None,
    school_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List users with filtering and pagination.

    **Query Parameters**:
    - role: Filter by role (student, teacher, admin)
    - school_id: Filter by school
    - search: Search by name or email
    - limit: Results per page (default: 20, max: 100)
    - cursor: Pagination cursor (user_id from last result)

    **Returns**:
    - Paginated list of users with details
    """
    if limit > 100:
        limit = 100

    result = admin_service.list_users(
        db=db,
        role=role,
        school_id=school_id,
        search=search,
        limit=limit,
        cursor=cursor,
    )

    return result


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a single user manually.

    **Request Body**:
    - email: User email (required)
    - first_name: First name (required)
    - last_name: Last name (required)
    - role: User role - student, teacher, or admin (required)
    - grade_level: Grade level 9-12 (for students)
    - school_id: School ID
    - organization_id: Organization ID
    - send_invitation: Whether to send invitation email

    **Returns**:
    - Created user details
    """
    user = admin_service.create_user(
        db=db,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        grade_level=user_data.grade_level,
        school_id=user_data.school_id,
        organization_id=user_data.organization_id,
        send_invitation=user_data.send_invitation,
    )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update user profile.

    **Allowed Updates**:
    - role: Change user role (student, teacher, admin)
    - grade_level: Update grade level
    - subjects: Teacher subjects (for teachers)
    - first_name: Update first name
    - last_name: Update last name

    **Returns**:
    - Updated user details
    """
    user = admin_service.update_user(
        db=db,
        user_id=user_id,
        role=user_data.role,
        grade_level=user_data.grade_level,
        subjects=user_data.subjects,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Soft delete a user (deactivate).

    **Effects**:
    - User is marked as inactive (is_active=false)
    - All sessions are revoked
    - User can no longer login
    - Historical data is preserved

    **Restrictions**:
    - Cannot delete own account
    """
    admin_service.delete_user(db=db, user_id=user_id, admin_id=current_user.user_id)
    return None


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get admin dashboard statistics.

    **Returns**:
    - total_users: Total user count
    - total_students: Student count
    - total_teachers: Teacher count
    - total_admins: Admin count
    - active_users_today: Users active in last 24h
    - total_classes: Total class count
    - total_content: Total content count
    """
    stats = admin_service.get_dashboard_stats(db=db)
    return stats


@router.post("/users/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_users(
    file: UploadFile = File(...),
    transaction_mode: str = Form("partial"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Bulk upload users from CSV file.

    **CSV Format**:
    ```csv
    first_name,last_name,email,role,grade_level,school_id
    John,Doe,john.doe@mnps.edu,student,10,school_hillsboro_hs
    Jane,Smith,jane.smith@mnps.edu,student,11,school_hillsboro_hs
    ```

    **Required Columns**:
    - first_name
    - last_name
    - email
    - role (student, teacher, or admin)

    **Optional Columns**:
    - grade_level (9-12 for students)
    - school_id

    **Transaction Modes**:
    - partial: Allow partial success (some rows can fail)
    - atomic: All or nothing (rollback if any row fails)

    **Returns**:
    - Upload ID
    - Total rows processed
    - Success/failure counts
    - Detailed error report for failed rows
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )

    if transaction_mode not in ["partial", "atomic"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="transaction_mode must be 'partial' or 'atomic'",
        )

    result = admin_service.bulk_upload_users(
        db=db,
        file=file,
        transaction_mode=transaction_mode,
    )

    return result


@router.get("/requests", response_model=RequestListResponse)
async def list_pending_requests(
    school_id: Optional[str] = None,
    teacher_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List pending account requests.

    **Query Parameters**:
    - school_id: Filter by school
    - teacher_id: Filter by requesting teacher
    - limit: Results per page (default: 20, max: 100)

    **Returns**:
    - List of pending requests with student and teacher details
    """
    if limit > 100:
        limit = 100

    result = admin_service.list_pending_requests(
        db=db,
        school_id=school_id,
        teacher_id=teacher_id,
        limit=limit,
    )

    return result


@router.get("/requests/{request_id}")
async def get_request_details(
    request_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific account request.

    **Returns**:
    - Request details
    - Student information
    - Requesting teacher information
    """
    result = admin_service.get_request_details(db=db, request_id=request_id)
    return result


@router.post("/requests/{request_id}/approve", response_model=ApproveRequestResponse)
async def approve_request(
    request_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Approve an account request.

    **Effects**:
    - Creates student account immediately
    - Enrolls student in requested class (if specified)
    - Sends welcome email to student
    - Notifies requesting teacher
    - Marks request as approved

    **Returns**:
    - Request ID
    - Created user details
    - Approval timestamp and admin
    """
    result = admin_service.approve_request(
        db=db,
        request_id=request_id,
        admin_id=current_user.user_id,
    )

    return result


@router.post("/requests/{request_id}/deny", response_model=DenyRequestResponse)
async def deny_request(
    request_id: str,
    deny_data: DenyRequestRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Deny an account request.

    **Request Body**:
    - reason: Denial reason (required)

    **Effects**:
    - Marks request as denied
    - Records denial reason
    - Notifies requesting teacher
    - No user account is created

    **Returns**:
    - Request ID
    - Denial details
    - Notification status
    """
    result = admin_service.deny_request(
        db=db,
        request_id=request_id,
        admin_id=current_user.user_id,
        reason=deny_data.reason,
    )

    return result
