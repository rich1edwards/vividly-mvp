"""
Teacher API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from app.core.database import get_db
from app.schemas.teacher import (
    CreateClassRequest,
    UpdateClassRequest,
    ClassResponse,
    RosterResponse,
    StudentAccountRequestCreate,
    BulkStudentAccountRequest,
    StudentAccountRequestResponse,
    TeacherDashboard,
)
from app.services import teacher_service
from app.utils.dependencies import get_current_user, get_current_active_teacher
from app.models.user import User


router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: CreateClassRequest,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Create a new class.

    **Authorization**: Teachers only

    **Request body**:
    - name: Class name (required, 1-255 chars)
    - subject: Subject name (optional, max 100 chars)
    - description: Class description (optional)
    - grade_levels: List of grades 9-12 (optional)

    **Returns**:
    - Complete class details including unique class_code
    - Class code format: "SUBJ-XXX-XXX" (e.g., "PHYS-ABC-123")

    **Notes**:
    - Class code is auto-generated from subject prefix
    - Students use class code to join the class
    - Class inherits school_id and organization_id from teacher
    """
    new_class = teacher_service.create_class(db, current_user.user_id, class_data)
    return new_class


@router.get("/{teacher_id}/classes", response_model=List[ClassResponse])
async def get_teacher_classes(
    teacher_id: str,
    include_archived: bool = Query(False, description="Include archived classes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all classes for a teacher.

    **Authorization**:
    - Teachers can only access their own classes
    - Admins can access any teacher's classes

    **Query parameters**:
    - include_archived: Include archived classes (default: false)

    **Returns**:
    - List of classes ordered by creation date (newest first)
    - Each class includes: name, subject, class_code, student count, etc.

    **Notes**:
    - Archived classes are soft-deleted (archived=true)
    - Class codes remain valid even after archiving
    """
    # Authorization: Teachers can only view their own classes
    if current_user.role == "teacher" and current_user.user_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can only access their own classes",
        )

    classes = teacher_service.get_teacher_classes(db, teacher_id, include_archived)
    return classes


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class_details(
    class_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific class.

    **Authorization**: Only the class owner (teacher) can access

    **Returns**:
    - Complete class details
    - Created/updated timestamps
    - Archived status

    **Validation**:
    - Class must exist
    - Teacher must own the class (403 if not)
    """
    class_obj = teacher_service.get_class_details(db, class_id, current_user.user_id)
    return class_obj


@router.patch("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: str,
    class_data: UpdateClassRequest,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Update class details.

    **Authorization**: Only the class owner (teacher) can update

    **Request body** (all fields optional):
    - name: New class name (1-255 chars)
    - subject: New subject name (max 100 chars)
    - description: New description
    - grade_levels: New grade levels (9-12)

    **Returns**:
    - Updated class details

    **Notes**:
    - Only provided fields are updated
    - class_code cannot be changed
    - updated_at timestamp is automatically updated
    """
    updated_class = teacher_service.update_class(db, class_id, current_user.user_id, class_data)
    return updated_class


@router.delete("/classes/{class_id}", response_model=ClassResponse)
async def archive_class(
    class_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Archive a class (soft delete).

    **Authorization**: Only the class owner (teacher) can archive

    **Returns**:
    - Archived class details with archived=true

    **Notes**:
    - This is a soft delete (data is preserved)
    - Archived classes are hidden by default in class lists
    - Students cannot join archived classes
    - Existing enrollments are preserved
    - Use include_archived=true to view archived classes
    """
    archived_class = teacher_service.archive_class(db, class_id, current_user.user_id)
    return archived_class


@router.get("/classes/{class_id}/students", response_model=RosterResponse)
async def get_class_roster(
    class_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Get class roster with student details and progress.

    **Authorization**: Only the class owner (teacher) can access roster

    **Returns**:
    - class_id, class_name, total_students
    - students: List of enrolled students with:
      - Basic info: user_id, email, name, grade_level
      - enrolled_at: When they joined the class
      - progress_summary:
        - topics_started: Count of topics started/in-progress
        - topics_completed: Count of completed topics

    **Notes**:
    - Students are ordered by enrollment date
    - Progress is aggregated across all topics
    - Includes students who joined via class code or admin enrollment
    """
    roster = teacher_service.get_class_roster(db, class_id, current_user.user_id)
    return roster


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Remove a student from a class.

    **Authorization**: Only the class owner (teacher) can remove students

    **Returns**: 204 No Content on success

    **Validation**:
    - Class must exist and belong to teacher
    - Student must be enrolled in the class (404 if not)

    **Notes**:
    - This removes the enrollment record
    - Student's progress data is preserved
    - Student can rejoin using the class code
    """
    teacher_service.remove_student_from_class(db, class_id, student_id, current_user.user_id)
    return


@router.post(
    "/student-requests",
    response_model=Union[StudentAccountRequestResponse, List[StudentAccountRequestResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def create_student_account_request(
    request_data: Union[StudentAccountRequestCreate, BulkStudentAccountRequest],
    current_user: User = Depends(get_current_active_teacher),
    db: Session = Depends(get_db),
):
    """
    Create student account request(s) for admin approval.

    **Authorization**: Teachers only

    **Request body** (two formats supported):

    1. **Single request**:
    - student_email: Student's email (required)
    - student_first_name: First name (required)
    - student_last_name: Last name (required)
    - grade_level: Grade 9-12 (required)
    - class_id: Auto-enroll after approval (optional)
    - notes: Notes for admin (optional)

    2. **Bulk request**:
    - students: Array of 1-50 student requests
    - All student emails must be unique

    **Returns**:
    - Single request: StudentAccountRequestResponse
    - Bulk request: List of StudentAccountRequestResponse

    **Validation**:
    - Email must not already exist in the system (400 if exists)
    - For bulk: All emails must be unique within the batch
    - Max 50 students per bulk request

    **Workflow**:
    1. Teacher creates request(s)
    2. Admin reviews and approves/rejects
    3. If approved, student account is created
    4. If class_id provided, student is auto-enrolled

    **Notes**:
    - Request inherits school_id and organization_id from teacher
    - Status starts as "pending"
    - Teachers can track status via GET /student-requests
    """
    # Determine if single or bulk request
    if isinstance(request_data, BulkStudentAccountRequest):
        # Bulk request
        requests = teacher_service.create_bulk_student_requests(db, current_user.user_id, request_data)
        return requests
    else:
        # Single request
        request = teacher_service.create_student_account_request(db, current_user.user_id, request_data)
        return request


@router.get("/{teacher_id}/student-requests", response_model=List[StudentAccountRequestResponse])
async def get_teacher_student_requests(
    teacher_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get teacher's student account requests.

    **Authorization**:
    - Teachers can only access their own requests
    - Admins can access any teacher's requests

    **Query parameters**:
    - status: Filter by status (pending, approved, rejected)

    **Returns**:
    - List of requests ordered by request date (newest first)
    - Each request includes:
      - request_id, status, requested_at
      - Student details (email, name, grade)
      - class_id if auto-enrollment requested
      - processed_at, created_user_id if approved

    **Request statuses**:
    - pending: Awaiting admin review
    - approved: Admin approved, account created
    - rejected: Admin rejected request

    **Notes**:
    - Created accounts have created_user_id populated
    - Rejected requests include rejection reason in metadata
    """
    # Authorization: Teachers can only view their own requests
    if current_user.role == "teacher" and current_user.user_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can only access their own requests",
        )

    requests = teacher_service.get_teacher_requests(db, teacher_id, status_filter)
    return requests


@router.get("/{teacher_id}/dashboard", response_model=TeacherDashboard)
async def get_teacher_dashboard(
    teacher_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get teacher dashboard with summary data.

    **Authorization**:
    - Teachers can only access their own dashboard
    - Admins can access any teacher's dashboard

    **Returns**:
    - **Summary metrics**:
      - total_classes: Total classes (including archived)
      - active_classes: Non-archived classes
      - total_students: Total enrolled across all active classes
      - pending_requests: Count of pending student account requests

    - **classes**: List of all classes with:
      - class_id, name, subject, class_code
      - student_count: Current enrollment
      - archived: Archive status
      - created_at: Creation timestamp

    **Notes**:
    - Total students is unique count across all classes
    - Same student in multiple classes counted once
    - Archived classes included in total but not student count
    - Ideal for teacher landing page/overview
    """
    # Authorization: Teachers can only view their own dashboard
    if current_user.role == "teacher" and current_user.user_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can only access their own dashboard",
        )

    dashboard = teacher_service.get_teacher_dashboard(db, teacher_id)
    return dashboard
