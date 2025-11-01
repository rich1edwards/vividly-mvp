"""
Integration tests for teacher endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.teacher
class TestCreateClass:
    """Test POST /api/v1/teachers/classes endpoint."""

    def test_create_class_success(self, client, sample_teacher, teacher_headers):
        """Test successfully creating a class."""
        response = client.post(
            "/api/v1/teachers/classes",
            headers=teacher_headers,
            json={
                "name": "New Physics Class",
                "subject": "Physics",
                "description": "A new physics class",
                "grade_levels": [9, 10, 11],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Physics Class"
        assert data["subject"] == "Physics"
        assert data["teacher_id"] == sample_teacher.user_id
        assert "class_code" in data
        assert len(data["class_code"]) > 0

    def test_create_class_student_forbidden(self, client, student_headers):
        """Test student cannot create a class."""
        response = client.post(
            "/api/v1/teachers/classes",
            headers=student_headers,
            json={"name": "Test Class", "subject": "Math"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_class_invalid_grade_levels(self, client, teacher_headers):
        """Test creating class with invalid grade levels."""
        response = client.post(
            "/api/v1/teachers/classes",
            headers=teacher_headers,
            json={
                "name": "Test Class",
                "subject": "Math",
                "grade_levels": [8, 13],  # Invalid
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.teacher
class TestGetTeacherClasses:
    """Test GET /api/v1/teachers/{teacher_id}/classes endpoint."""

    def test_get_own_classes_success(
        self, client, sample_teacher, teacher_headers, sample_class
    ):
        """Test teacher getting their own classes."""
        response = client.get(
            f"/api/v1/teachers/{sample_teacher.user_id}/classes",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_classes_include_archived(
        self, client, sample_teacher, teacher_headers, db_session
    ):
        """Test getting classes including archived ones."""
        # Create archived class
        from app.models.class_model import Class

        archived_class = Class(
            class_id="class_archived_test",
            teacher_id=sample_teacher.user_id,
            name="Archived Class",
            subject="Test",
            class_code="TEST-888-888",
            archived=True,
        )
        db_session.add(archived_class)
        db_session.commit()

        response = client.get(
            f"/api/v1/teachers/{sample_teacher.user_id}/classes?include_archived=true",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        archived_count = sum(1 for c in data if c.get("archived") == True)
        assert archived_count >= 1

    def test_teacher_cannot_access_other_classes(
        self, client, teacher_headers, sample_admin
    ):
        """Test teacher cannot access another teacher's classes."""
        response = client.get(
            f"/api/v1/teachers/{sample_admin.user_id}/classes", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.teacher
class TestGetClassDetails:
    """Test GET /api/v1/classes/{class_id} endpoint."""

    def test_get_class_details_success(self, client, sample_class, teacher_headers):
        """Test getting class details."""
        response = client.get(
            f"/api/v1/classes/{sample_class.class_id}", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["class_id"] == sample_class.class_id
        assert data["name"] == sample_class.name

    def test_get_nonexistent_class(self, client, teacher_headers):
        """Test getting nonexistent class."""
        response = client.get(
            "/api/v1/classes/nonexistent_class_id", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
@pytest.mark.teacher
class TestUpdateClass:
    """Test PATCH /api/v1/classes/{class_id} endpoint."""

    def test_update_class_success(self, client, sample_class, teacher_headers):
        """Test successfully updating a class."""
        response = client.patch(
            f"/api/v1/classes/{sample_class.class_id}",
            headers=teacher_headers,
            json={
                "name": "Updated Physics Class",
                "description": "Updated description",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Physics Class"
        assert data["description"] == "Updated description"

    def test_update_class_invalid_grades(self, client, sample_class, teacher_headers):
        """Test updating with invalid grade levels."""
        response = client.patch(
            f"/api/v1/classes/{sample_class.class_id}",
            headers=teacher_headers,
            json={"grade_levels": [5, 6]},  # Invalid
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.teacher
class TestArchiveClass:
    """Test DELETE /api/v1/classes/{class_id} endpoint."""

    def test_archive_class_success(self, client, sample_class, teacher_headers):
        """Test successfully archiving a class."""
        response = client.delete(
            f"/api/v1/classes/{sample_class.class_id}", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["archived"] == True


@pytest.mark.integration
@pytest.mark.teacher
class TestGetClassRoster:
    """Test GET /api/v1/classes/{class_id}/students endpoint."""

    def test_get_roster_success(
        self, client, sample_class, teacher_headers, sample_student, db_session
    ):
        """Test getting class roster."""
        # Enroll student
        from app.models.class_student import ClassStudent

        enrollment = ClassStudent(
            class_id=sample_class.class_id, student_id=sample_student.user_id
        )
        db_session.add(enrollment)
        db_session.commit()

        response = client.get(
            f"/api/v1/classes/{sample_class.class_id}/students", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["class_id"] == sample_class.class_id
        assert "students" in data
        assert data["total_students"] >= 1

    def test_get_roster_empty_class(self, client, sample_class, teacher_headers):
        """Test getting roster for empty class."""
        response = client.get(
            f"/api/v1/classes/{sample_class.class_id}/students", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_students"] == 0
        assert data["students"] == []


@pytest.mark.integration
@pytest.mark.teacher
class TestRemoveStudentFromClass:
    """Test DELETE /api/v1/classes/{class_id}/students/{student_id} endpoint."""

    def test_remove_student_success(
        self, client, sample_class, sample_student, teacher_headers, db_session
    ):
        """Test successfully removing a student."""
        # Enroll student first
        from app.models.class_student import ClassStudent

        enrollment = ClassStudent(
            class_id=sample_class.class_id, student_id=sample_student.user_id
        )
        db_session.add(enrollment)
        db_session.commit()

        response = client.delete(
            f"/api/v1/classes/{sample_class.class_id}/students/{sample_student.user_id}",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_remove_unenrolled_student(
        self, client, sample_class, sample_student, teacher_headers
    ):
        """Test removing a student not enrolled."""
        response = client.delete(
            f"/api/v1/classes/{sample_class.class_id}/students/{sample_student.user_id}",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
@pytest.mark.teacher
class TestStudentAccountRequests:
    """Test student account request endpoints."""

    def test_create_single_request_success(self, client, teacher_headers, sample_class):
        """Test creating a single student account request."""
        response = client.post(
            "/api/v1/teachers/student-requests",
            headers=teacher_headers,
            json={
                "student_email": "newstudent@school.edu",
                "student_first_name": "New",
                "student_last_name": "Student",
                "grade_level": 10,
                "class_id": sample_class.class_id,
                "notes": "Test request",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["student_email"] == "newstudent@school.edu"
        assert data["status"] == "pending"

    def test_create_bulk_requests_success(self, client, teacher_headers):
        """Test creating bulk student account requests."""
        response = client.post(
            "/api/v1/teachers/student-requests",
            headers=teacher_headers,
            json={
                "students": [
                    {
                        "student_email": "student1@school.edu",
                        "student_first_name": "Student",
                        "student_last_name": "One",
                        "grade_level": 10,
                    },
                    {
                        "student_email": "student2@school.edu",
                        "student_first_name": "Student",
                        "student_last_name": "Two",
                        "grade_level": 11,
                    },
                ]
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_create_request_duplicate_email(
        self, client, teacher_headers, sample_student
    ):
        """Test creating request with existing user email."""
        response = client.post(
            "/api/v1/teachers/student-requests",
            headers=teacher_headers,
            json={
                "student_email": sample_student.email,
                "student_first_name": "Test",
                "student_last_name": "Student",
                "grade_level": 10,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_bulk_too_many(self, client, teacher_headers):
        """Test creating bulk request with too many students."""
        students = [
            {
                "student_email": f"student{i}@school.edu",
                "student_first_name": "Student",
                "student_last_name": str(i),
                "grade_level": 10,
            }
            for i in range(51)  # 51 is too many (max 50)
        ]

        response = client.post(
            "/api/v1/teachers/student-requests",
            headers=teacher_headers,
            json={"students": students},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.teacher
class TestGetTeacherRequests:
    """Test GET /api/v1/teachers/{teacher_id}/student-requests endpoint."""

    def test_get_requests_success(self, client, sample_teacher, teacher_headers):
        """Test getting teacher's requests."""
        response = client.get(
            f"/api/v1/teachers/{sample_teacher.user_id}/student-requests",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_requests_filtered_by_status(
        self, client, sample_teacher, teacher_headers
    ):
        """Test getting requests filtered by status."""
        response = client.get(
            f"/api/v1/teachers/{sample_teacher.user_id}/student-requests?status_filter=pending",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.teacher
class TestTeacherDashboard:
    """Test GET /api/v1/teachers/{teacher_id}/dashboard endpoint."""

    def test_get_dashboard_success(
        self, client, sample_teacher, teacher_headers, sample_class
    ):
        """Test getting teacher dashboard."""
        response = client.get(
            f"/api/v1/teachers/{sample_teacher.user_id}/dashboard",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "teacher_id" in data
        assert "total_classes" in data
        assert "active_classes" in data
        assert "total_students" in data
        assert "pending_requests" in data
        assert "classes" in data
        assert isinstance(data["classes"], list)

    def test_teacher_cannot_access_other_dashboard(
        self, client, teacher_headers, sample_admin
    ):
        """Test teacher cannot access another teacher's dashboard."""
        response = client.get(
            f"/api/v1/teachers/{sample_admin.user_id}/dashboard",
            headers=teacher_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
