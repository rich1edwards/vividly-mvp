"""
Integration tests for Admin API endpoints.
Tests all 10 admin endpoints from Sprint 2.
"""
import pytest
import io
import csv
from fastapi import status


class TestAdminUserManagement:
    """Test admin user management endpoints."""

    def test_list_users_success(self, client, admin_headers, sample_student, sample_teacher):
        """Test listing users with admin access."""
        response = client.get("/api/v1/admin/users", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "pagination" in data
        assert len(data["users"]) >= 2  # At least student and teacher

    def test_list_users_filter_by_role(self, client, admin_headers, sample_student):
        """Test filtering users by role."""
        response = client.get(
            "/api/v1/admin/users?role=student",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "student"

    def test_list_users_forbidden_for_non_admin(self, client, student_headers):
        """Test that non-admin cannot list users."""
        response = client.get("/api/v1/admin/users", headers=student_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_single_user_success(self, client, admin_headers):
        """Test creating a single user."""
        user_data = {
            "email": "newuser@test.com",
            "first_name": "New",
            "last_name": "User",
            "role": "student",
            "grade_level": 10,
            "send_invitation": False
        }

        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "New"
        assert data["role"] == "student"
        assert "user_id" in data

    def test_create_user_duplicate_email(self, client, admin_headers, sample_student):
        """Test that duplicate email returns error."""
        user_data = {
            "email": sample_student.email,
            "first_name": "Duplicate",
            "last_name": "User",
            "role": "student"
        }

        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    def test_update_user_success(self, client, admin_headers, sample_student):
        """Test updating user profile."""
        update_data = {
            "grade_level": 11,
            "first_name": "Updated"
        }

        response = client.put(
            f"/api/v1/admin/users/{sample_student.user_id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["grade_level"] == 11
        assert data["first_name"] == "Updated"

    def test_delete_user_success(self, client, admin_headers, sample_student):
        """Test soft deleting a user."""
        response = client.delete(
            f"/api/v1/admin/users/{sample_student.user_id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify user is deactivated
        response = client.get(
            f"/api/v1/students/{sample_student.user_id}",
            headers=admin_headers
        )
        # Should either return 404 or show is_active=False
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]

    def test_delete_own_account_forbidden(self, client, admin_headers, sample_admin):
        """Test that admin cannot delete their own account."""
        response = client.delete(
            f"/api/v1/admin/users/{sample_admin.user_id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "own account" in response.json()["detail"].lower()


class TestBulkUserUpload:
    """Test bulk user upload functionality."""

    def test_bulk_upload_partial_success(self, client, admin_headers):
        """Test CSV upload with partial transaction mode."""
        # Create CSV content
        csv_content = "first_name,last_name,email,role,grade_level\n"
        csv_content += "John,Doe,john.bulk@test.com,student,10\n"
        csv_content += "Jane,Smith,jane.bulk@test.com,student,11\n"
        csv_content += "Bob,Jones,invalid-email,student,10\n"  # Invalid

        csv_file = io.BytesIO(csv_content.encode('utf-8'))

        response = client.post(
            "/api/v1/admin/users/bulk-upload",
            files={"file": ("users.csv", csv_file, "text/csv")},
            data={"transaction_mode": "partial"},
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "upload_id" in data
        assert data["successful"] >= 2
        assert data["failed"] >= 1
        assert len(data["results"]["failed_rows"]) >= 1

    def test_bulk_upload_atomic_rollback(self, client, admin_headers, sample_student):
        """Test CSV upload with atomic transaction mode."""
        # Create CSV with one duplicate email (should rollback all)
        csv_content = "first_name,last_name,email,role,grade_level\n"
        csv_content += "New,User1,new1@test.com,student,10\n"
        csv_content += f"Duplicate,User,{sample_student.email},student,10\n"  # Duplicate

        csv_file = io.BytesIO(csv_content.encode('utf-8'))

        response = client.post(
            "/api/v1/admin/users/bulk-upload",
            files={"file": ("users.csv", csv_file, "text/csv")},
            data={"transaction_mode": "atomic"},
            headers=admin_headers
        )

        # Should fail completely
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAccountRequests:
    """Test account request approval/denial endpoints."""

    def test_list_pending_requests(self, client, admin_headers, db_session):
        """Test listing pending account requests."""
        # Create a pending request
        from app.models.student_request import StudentRequest, RequestStatus

        request = StudentRequest(
            request_id="req_test_001",
            student_email="pending@test.com",
            student_first_name="Pending",
            student_last_name="Student",
            grade_level=10,
            status=RequestStatus.PENDING,
            requested_by="user_teacher_test_001"
        )
        db_session.add(request)
        db_session.commit()

        response = client.get("/api/v1/admin/requests", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "requests" in data
        assert len(data["requests"]) > 0

    def test_get_request_details(self, client, admin_headers, db_session):
        """Test getting request details."""
        from app.models.student_request import StudentRequest, RequestStatus

        request = StudentRequest(
            request_id="req_test_002",
            student_email="details@test.com",
            student_first_name="Details",
            student_last_name="Test",
            grade_level=10,
            status=RequestStatus.PENDING,
            requested_by="user_teacher_test_001"
        )
        db_session.add(request)
        db_session.commit()

        response = client.get(
            f"/api/v1/admin/requests/{request.request_id}",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["request_id"] == "req_test_002"
        assert data["student_email"] == "details@test.com"

    def test_approve_request_success(self, client, admin_headers, db_session, sample_admin):
        """Test approving an account request."""
        from app.models.student_request import StudentRequest, RequestStatus

        request = StudentRequest(
            request_id="req_test_003",
            student_email="approve@test.com",
            student_first_name="Approve",
            student_last_name="Test",
            grade_level=10,
            status=RequestStatus.PENDING,
            requested_by="user_teacher_test_001"
        )
        db_session.add(request)
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/requests/{request.request_id}/approve",
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "approved"
        assert "user_created" in data
        assert data["approved_by"] == sample_admin.user_id

    def test_deny_request_success(self, client, admin_headers, db_session, sample_admin):
        """Test denying an account request."""
        from app.models.student_request import StudentRequest, RequestStatus

        request = StudentRequest(
            request_id="req_test_004",
            student_email="deny@test.com",
            student_first_name="Deny",
            student_last_name="Test",
            grade_level=10,
            status=RequestStatus.PENDING,
            requested_by="user_teacher_test_001"
        )
        db_session.add(request)
        db_session.commit()

        denial_data = {"reason": "Duplicate request"}

        response = client.post(
            f"/api/v1/admin/requests/{request.request_id}/deny",
            json=denial_data,
            headers=admin_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "denied"
        assert data["denial_reason"] == "Duplicate request"


class TestAdminDashboard:
    """Test admin dashboard statistics."""

    def test_get_admin_stats(self, client, admin_headers, sample_student, sample_teacher):
        """Test getting admin dashboard statistics."""
        response = client.get("/api/v1/admin/stats", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_users" in data
        assert "total_students" in data
        assert "total_teachers" in data
        assert data["total_users"] >= 2  # At least student and teacher
