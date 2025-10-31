"""
Unit tests for admin service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from fastapi import HTTPException, UploadFile
import io

from app.services.admin_service import (
    generate_user_id,
    list_users,
    create_user,
    update_user,
    delete_user,
    bulk_upload_users,
    list_pending_requests,
    get_request_details,
    approve_request,
    deny_request,
    get_dashboard_stats,
)
from app.models.user import User, UserRole
from app.models.student_request import StudentRequest, RequestStatus


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper functions."""

    def test_generate_user_id(self):
        """Test user ID generation format."""
        user_id = generate_user_id()

        assert user_id.startswith("user_")
        assert len(user_id) > 10

    def test_generate_user_id_uniqueness(self):
        """Test user IDs are unique."""
        ids = [generate_user_id() for _ in range(100)]

        assert len(ids) == len(set(ids))


@pytest.mark.unit
class TestListUsers:
    """Test list users functionality."""

    def test_list_users_no_filters(self):
        """Test listing users without filters."""
        db = Mock()
        mock_user1 = Mock(user_id="user_1")
        mock_user2 = Mock(user_id="user_2")

        # Setup mock query chain
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_user1,
            mock_user2,
        ]
        db.query.return_value.filter.return_value.scalar.return_value = 2

        result = list_users(db=db, limit=20)

        assert "users" in result
        assert "pagination" in result
        assert len(result["users"]) == 2
        assert result["pagination"]["has_more"] is False
        assert result["pagination"]["total_count"] == 2

    def test_list_users_with_role_filter(self):
        """Test listing users filtered by role."""
        db = Mock()

        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = list_users(db=db, role="teacher", limit=20)

        assert result["users"] == []

    def test_list_users_with_search(self):
        """Test listing users with search query."""
        db = Mock()

        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = list_users(db=db, search="john", limit=20)

        assert result["users"] == []

    def test_list_users_with_pagination(self):
        """Test listing users with cursor pagination."""
        db = Mock()
        mock_users = [Mock(user_id=f"user_{i}") for i in range(21)]

        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_users

        result = list_users(db=db, cursor="user_0", limit=20)

        assert result["pagination"]["has_more"] is True
        assert result["pagination"]["next_cursor"] == "user_19"  # Last user in the trimmed list (users[:20])
        assert len(result["users"]) == 20


@pytest.mark.unit
class TestCreateUser:
    """Test create user functionality."""

    def test_create_user_success(self):
        """Test successful user creation."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None  # No existing user

        user = create_user(
            db=db,
            email="newuser@test.com",
            first_name="New",
            last_name="User",
            role="student",
            grade_level=9,
        )

        # Verify database operations
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_create_user_duplicate_email(self):
        """Test creating user with existing email."""
        db = Mock()
        existing_user = Mock()
        db.query.return_value.filter.return_value.first.return_value = existing_user

        with pytest.raises(HTTPException) as exc_info:
            create_user(
                db=db,
                email="existing@test.com",
                first_name="Test",
                last_name="User",
                role="student",
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    def test_create_user_with_school_id(self):
        """Test creating user with school ID."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        user = create_user(
            db=db,
            email="newuser@test.com",
            first_name="New",
            last_name="User",
            role="student",
            school_id="school_123",
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_create_user_teacher_role(self):
        """Test creating teacher user."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        user = create_user(
            db=db,
            email="teacher@test.com",
            first_name="Teacher",
            last_name="Smith",
            role="teacher",
        )

        db.add.assert_called_once()


@pytest.mark.unit
class TestUpdateUser:
    """Test update user functionality."""

    def test_update_user_success(self):
        """Test successful user update."""
        db = Mock()
        mock_user = Mock(user_id="user_1", role="student", grade_level=9)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = update_user(db=db, user_id="user_1", grade_level=10)

        assert mock_user.grade_level == 10
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_update_user_not_found(self):
        """Test updating non-existent user."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            update_user(db=db, user_id="nonexistent")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()

    def test_update_user_role(self):
        """Test updating user role."""
        db = Mock()
        mock_user = Mock(user_id="user_1", role="student")
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = update_user(db=db, user_id="user_1", role="teacher")

        assert mock_user.role == "teacher"
        db.commit.assert_called_once()

    def test_update_user_multiple_fields(self):
        """Test updating multiple user fields."""
        db = Mock()
        mock_user = Mock(user_id="user_1", first_name="Old", last_name="Name")
        db.query.return_value.filter.return_value.first.return_value = mock_user

        result = update_user(
            db=db,
            user_id="user_1",
            first_name="New",
            last_name="Name2",
        )

        db.commit.assert_called_once()


@pytest.mark.unit
class TestDeleteUser:
    """Test delete user functionality."""

    def test_delete_user_success(self):
        """Test successful user deletion (soft delete)."""
        db = Mock()
        mock_user = Mock(user_id="user_1", archived=False)
        db.query.return_value.filter.return_value.first.return_value = mock_user

        delete_user(db=db, user_id="user_1", admin_id="admin_1")

        assert mock_user.archived is True
        assert mock_user.archived_at is not None
        db.commit.assert_called_once()

    def test_delete_user_own_account(self):
        """Test preventing deletion of own account."""
        db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            delete_user(db=db, user_id="admin_1", admin_id="admin_1")

        assert exc_info.value.status_code == 400
        assert "own account" in str(exc_info.value.detail).lower()

    def test_delete_user_not_found(self):
        """Test deleting non-existent user."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_user(db=db, user_id="nonexistent", admin_id="admin_1")

        assert exc_info.value.status_code == 404

    def test_delete_user_revokes_sessions(self):
        """Test that deletion revokes all user sessions."""
        db = Mock()
        mock_user = Mock(user_id="user_1")
        db.query.return_value.filter.return_value.first.return_value = mock_user

        delete_user(db=db, user_id="user_1", admin_id="admin_1")

        # Verify sessions are updated (revoked)
        db.query.return_value.filter.return_value.update.assert_called_once()


@pytest.mark.unit
class TestBulkUploadUsers:
    """Test bulk upload users functionality."""

    @patch('app.services.admin_service.create_user')
    def test_bulk_upload_success(self, mock_create_user):
        """Test successful bulk upload."""
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = []  # No existing emails

        # Mock successful user creation
        mock_create_user.side_effect = [
            Mock(user_id="user_1"),
            Mock(user_id="user_2"),
        ]

        csv_content = "first_name,last_name,email,role\nJohn,Doe,john@test.com,student\nJane,Smith,jane@test.com,teacher"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        result = bulk_upload_users(db=db, file=file)

        assert result["successful"] == 2
        assert result["failed"] == 0
        assert result["total_rows"] == 2

    def test_bulk_upload_missing_headers(self):
        """Test bulk upload with missing required headers."""
        db = Mock()

        csv_content = "first_name,last_name,email\nJohn,Doe,john@test.com"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        with pytest.raises(HTTPException) as exc_info:
            bulk_upload_users(db=db, file=file)

        assert exc_info.value.status_code == 400
        assert "headers" in str(exc_info.value.detail).lower()

    def test_bulk_upload_duplicate_email(self):
        """Test bulk upload with duplicate email."""
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = [("existing@test.com",)]

        csv_content = "first_name,last_name,email,role\nJohn,Doe,existing@test.com,student"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        result = bulk_upload_users(db=db, file=file, transaction_mode="partial")

        assert result["failed"] == 1
        assert result["results"]["failed_rows"][0]["error_code"] == "DUPLICATE_EMAIL"

    def test_bulk_upload_missing_fields(self):
        """Test bulk upload with missing required fields."""
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = []

        csv_content = "first_name,last_name,email,role\nJohn,,john@test.com,student"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        result = bulk_upload_users(db=db, file=file)

        assert result["failed"] == 1
        assert result["results"]["failed_rows"][0]["error_code"] == "MISSING_FIELDS"

    def test_bulk_upload_invalid_email(self):
        """Test bulk upload with invalid email format."""
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = []

        csv_content = "first_name,last_name,email,role\nJohn,Doe,invalid-email,student"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        result = bulk_upload_users(db=db, file=file)

        assert result["failed"] == 1
        assert result["results"]["failed_rows"][0]["error_code"] == "INVALID_EMAIL"

    def test_bulk_upload_atomic_mode_failure(self):
        """Test bulk upload in atomic mode fails completely on error."""
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = [("existing@test.com",)]

        csv_content = "first_name,last_name,email,role\nJohn,Doe,existing@test.com,student"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        with pytest.raises(HTTPException) as exc_info:
            bulk_upload_users(db=db, file=file, transaction_mode="atomic")

        assert exc_info.value.status_code == 400
        db.rollback.assert_called()

    @patch('app.services.admin_service.create_user')
    def test_bulk_upload_partial_success(self, mock_create_user):
        """Test bulk upload with some successes and failures."""
        db = Mock()
        db.query.return_value.filter.return_value.all.return_value = [("existing@test.com",)]

        # Mock successful user creation for the valid email
        mock_create_user.return_value = Mock(user_id="user_1")

        csv_content = "first_name,last_name,email,role\nJohn,Doe,new@test.com,student\nJane,Smith,existing@test.com,teacher"
        file = Mock(spec=UploadFile)
        file.file = io.BytesIO(csv_content.encode())

        result = bulk_upload_users(db=db, file=file, transaction_mode="partial")

        assert result["successful"] == 1
        assert result["failed"] == 1


@pytest.mark.unit
class TestAccountRequests:
    """Test account request management."""

    def test_list_pending_requests(self):
        """Test listing pending account requests."""
        db = Mock()
        mock_request = Mock(
            request_id="req_1",
            student_email="student@test.com",
            student_first_name="Student",
            student_last_name="One",
            grade_level=9,
            status=RequestStatus.PENDING,
            requested_by="teacher_1",
            requested_at=datetime.utcnow(),
        )
        mock_teacher = Mock(first_name="Teacher", last_name="Smith")

        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_request
        ]
        db.query.return_value.filter.return_value.first.return_value = mock_teacher

        result = list_pending_requests(db=db, limit=20)

        assert "requests" in result
        assert len(result["requests"]) == 1
        assert result["requests"][0]["teacher_name"] == "Teacher Smith"

    def test_list_pending_requests_with_school_filter(self):
        """Test listing requests filtered by school."""
        db = Mock()
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = list_pending_requests(db=db, school_id="school_123")

        assert result["requests"] == []

    def test_get_request_details_success(self):
        """Test getting request details."""
        db = Mock()
        mock_request = Mock(
            request_id="req_1",
            student_email="student@test.com",
            student_first_name="Student",
            student_last_name="One",
            grade_level=9,
            status=RequestStatus.PENDING,
            requested_by="teacher_1",
            requested_at=datetime.utcnow(),
            school_id="school_1",
            class_id="class_1",
            notes="Test notes",
        )
        mock_teacher = Mock(first_name="Teacher", last_name="Smith")

        db.query.return_value.filter.return_value.first.side_effect = [mock_request, mock_teacher]

        result = get_request_details(db=db, request_id="req_1")

        assert result["request_id"] == "req_1"
        assert result["student_email"] == "student@test.com"
        assert result["teacher_name"] == "Teacher Smith"

    def test_get_request_details_not_found(self):
        """Test getting non-existent request."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_request_details(db=db, request_id="nonexistent")

        assert exc_info.value.status_code == 404


@pytest.mark.unit
class TestApproveRequest:
    """Test account request approval."""

    @patch('app.services.admin_service.create_user')
    def test_approve_request_success(self, mock_create_user):
        """Test successful request approval."""
        db = Mock()
        mock_request = Mock(
            request_id="req_1",
            status=RequestStatus.PENDING,
            student_email="student@test.com",
            student_first_name="Student",
            student_last_name="One",
            grade_level=9,
            school_id="school_1",
            organization_id="org_1",
            class_id="class_1",
        )

        # Mock the created user
        mock_user = Mock(user_id="user_123", email="student@test.com")
        mock_create_user.return_value = mock_user

        db.query.return_value.filter.return_value.first.side_effect = [
            mock_request,  # First call: get request
            None,  # Second call: check existing user (none)
        ]

        result = approve_request(db=db, request_id="req_1", admin_id="admin_1")

        assert result["status"] == "approved"
        assert result["invitation_sent"] is True
        assert result["user_created"]["user_id"] == "user_123"
        assert mock_request.status == RequestStatus.APPROVED
        db.commit.assert_called_once()

    def test_approve_request_not_found(self):
        """Test approving non-existent request."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            approve_request(db=db, request_id="nonexistent", admin_id="admin_1")

        assert exc_info.value.status_code == 404

    def test_approve_request_already_processed(self):
        """Test approving already processed request."""
        db = Mock()
        mock_request = Mock(status=RequestStatus.APPROVED)
        db.query.return_value.filter.return_value.first.return_value = mock_request

        with pytest.raises(HTTPException) as exc_info:
            approve_request(db=db, request_id="req_1", admin_id="admin_1")

        assert exc_info.value.status_code == 400
        assert "already" in str(exc_info.value.detail).lower()

    def test_approve_request_duplicate_email(self):
        """Test approving request for existing user."""
        db = Mock()
        mock_request = Mock(status=RequestStatus.PENDING, student_email="existing@test.com")
        existing_user = Mock()

        db.query.return_value.filter.return_value.first.side_effect = [mock_request, existing_user]

        with pytest.raises(HTTPException) as exc_info:
            approve_request(db=db, request_id="req_1", admin_id="admin_1")

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail).lower()


@pytest.mark.unit
class TestDenyRequest:
    """Test account request denial."""

    def test_deny_request_success(self):
        """Test successful request denial."""
        db = Mock()
        mock_request = Mock(
            request_id="req_1",
            status=RequestStatus.PENDING,
            notes=None,
        )
        db.query.return_value.filter.return_value.first.return_value = mock_request

        result = deny_request(db=db, request_id="req_1", admin_id="admin_1", reason="Insufficient information")

        assert result["status"] == "denied"
        assert mock_request.status == RequestStatus.REJECTED
        assert "Insufficient information" in mock_request.notes
        db.commit.assert_called_once()

    def test_deny_request_not_found(self):
        """Test denying non-existent request."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            deny_request(db=db, request_id="nonexistent", admin_id="admin_1", reason="Test")

        assert exc_info.value.status_code == 404

    def test_deny_request_already_processed(self):
        """Test denying already processed request."""
        db = Mock()
        mock_request = Mock(status=RequestStatus.APPROVED)
        db.query.return_value.filter.return_value.first.return_value = mock_request

        with pytest.raises(HTTPException) as exc_info:
            deny_request(db=db, request_id="req_1", admin_id="admin_1", reason="Test")

        assert exc_info.value.status_code == 400


@pytest.mark.unit
class TestDashboardStats:
    """Test dashboard statistics."""

    def test_get_dashboard_stats(self):
        """Test retrieving dashboard statistics."""
        db = Mock()

        # Create separate mock query chains for each query
        mock_queries = []
        for count in [100, 75, 20, 5, 50, 25, 200]:
            mock_query = Mock()
            mock_query.filter.return_value.scalar.return_value = count
            mock_query.scalar.return_value = count
            mock_queries.append(mock_query)

        db.query.side_effect = mock_queries

        result = get_dashboard_stats(db=db)

        assert result["total_users"] == 100
        assert result["total_students"] == 75
        assert result["total_teachers"] == 20
        assert result["total_admins"] == 5
        assert result["active_users_today"] == 50
        assert result["total_classes"] == 25
        assert result["total_content"] == 200

    def test_get_dashboard_stats_empty(self):
        """Test dashboard stats with no data."""
        db = Mock()

        # Create mock query chains that return None
        mock_query = Mock()
        mock_query.filter.return_value.scalar.return_value = None
        mock_query.scalar.return_value = None
        db.query.return_value = mock_query

        result = get_dashboard_stats(db=db)

        assert result["total_users"] == 0
        assert result["total_students"] == 0
        assert result["total_content"] == 0
