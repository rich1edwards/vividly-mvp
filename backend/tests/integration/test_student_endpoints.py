"""
Integration tests for student endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.student
class TestGetStudentProfile:
    """Test GET /api/v1/students/{student_id} endpoint."""

    def test_get_own_profile_success(
        self, client, sample_student, student_headers, sample_interests
    ):
        """Test student getting their own profile."""
        response = client.get(
            f"/api/v1/students/{sample_student.user_id}", headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == sample_student.user_id
        assert data["email"] == sample_student.email
        assert data["role"] == "student"
        assert "interests" in data
        assert "enrolled_classes" in data
        assert "progress_summary" in data

    def test_student_cannot_access_other_profile(
        self, client, sample_student, sample_teacher, student_headers
    ):
        """Test student cannot access another student's profile."""
        # Try to access another student's profile (use teacher's ID as "other student")
        # The authorization check should prevent access before even checking if user exists
        response = client.get(
            f"/api/v1/students/{sample_teacher.user_id}", headers=student_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_teacher_can_access_student_profile(
        self, client, sample_student, teacher_headers
    ):
        """Test teacher can access any student profile."""
        response = client.get(
            f"/api/v1/students/{sample_student.user_id}", headers=teacher_headers
        )

        assert response.status_code == status.HTTP_200_OK

    def test_get_profile_no_auth(self, client, sample_student):
        """Test getting profile without authentication."""
        response = client.get(f"/api/v1/students/{sample_student.user_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.student
class TestUpdateStudentProfile:
    """Test PATCH /api/v1/students/{student_id} endpoint."""

    def test_update_own_profile_success(self, client, sample_student, student_headers):
        """Test student updating their own profile."""
        response = client.patch(
            f"/api/v1/students/{sample_student.user_id}",
            headers=student_headers,
            json={"first_name": "Updated", "last_name": "Name", "grade_level": 11},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["grade_level"] == 11

    def test_update_profile_invalid_grade(
        self, client, sample_student, student_headers
    ):
        """Test updating profile with invalid grade level."""
        response = client.patch(
            f"/api/v1/students/{sample_student.user_id}",
            headers=student_headers,
            json={"grade_level": 15},  # Invalid
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_student_cannot_update_other_profile(
        self, client, sample_student, student_headers
    ):
        """Test student cannot update another student's profile."""
        response = client.patch(
            "/api/v1/students/user_other_student",
            headers=student_headers,
            json={"first_name": "Hacked"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.integration
@pytest.mark.student
class TestStudentInterests:
    """Test student interests endpoints."""

    def test_get_interests_success(
        self, client, sample_student, student_headers, sample_interests, db_session
    ):
        """Test getting student interests."""
        # Add some interests
        from app.models.interest import StudentInterest

        db_session.add(
            StudentInterest(
                student_id=sample_student.user_id,
                interest_id=sample_interests[0].interest_id,
            )
        )
        db_session.commit()

        response = client.get(
            f"/api/v1/students/{sample_student.user_id}/interests",
            headers=student_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_update_interests_success(
        self, client, sample_student, student_headers, sample_interests
    ):
        """Test updating student interests."""
        interest_ids = [i.interest_id for i in sample_interests[:3]]

        response = client.put(
            f"/api/v1/students/{sample_student.user_id}/interests",
            headers=student_headers,
            json={"interest_ids": interest_ids},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_update_interests_too_many(
        self, client, sample_student, student_headers, sample_interests
    ):
        """Test updating with more than 5 interests."""
        # Create 6 interests
        interest_ids = [i.interest_id for i in sample_interests] + ["extra"]

        response = client.put(
            f"/api/v1/students/{sample_student.user_id}/interests",
            headers=student_headers,
            json={"interest_ids": interest_ids},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_interests_too_few(self, client, sample_student, student_headers):
        """Test updating with 0 interests."""
        response = client.put(
            f"/api/v1/students/{sample_student.user_id}/interests",
            headers=student_headers,
            json={"interest_ids": []},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_interests_duplicates(
        self, client, sample_student, student_headers, sample_interests
    ):
        """Test updating with duplicate interest IDs."""
        interest_id = sample_interests[0].interest_id

        response = client.put(
            f"/api/v1/students/{sample_student.user_id}/interests",
            headers=student_headers,
            json={"interest_ids": [interest_id, interest_id, interest_id]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
@pytest.mark.student
class TestLearningProgress:
    """Test GET /api/v1/students/{student_id}/progress endpoint."""

    def test_get_progress_success(
        self, client, sample_student, student_headers, sample_topics
    ):
        """Test getting learning progress."""
        response = client.get(
            f"/api/v1/students/{sample_student.user_id}/progress",
            headers=student_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "topics" in data
        assert "recent_activity" in data
        assert "total_topics_started" in data
        assert "total_topics_completed" in data
        assert "total_watch_time_seconds" in data
        assert "learning_streak_days" in data
        assert isinstance(data["learning_streak_days"], int)


@pytest.mark.integration
@pytest.mark.student
class TestJoinClass:
    """Test POST /api/v1/students/{student_id}/classes/join endpoint."""

    def test_join_class_success(
        self, client, sample_student, student_headers, sample_class
    ):
        """Test successfully joining a class."""
        response = client.post(
            f"/api/v1/students/{sample_student.user_id}/classes/join",
            headers=student_headers,
            json={"class_code": sample_class.class_code},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Successfully joined class"
        assert "class" in data
        assert data["class"]["class_id"] == sample_class.class_id

    def test_join_class_invalid_code(self, client, sample_student, student_headers):
        """Test joining with invalid class code."""
        response = client.post(
            f"/api/v1/students/{sample_student.user_id}/classes/join",
            headers=student_headers,
            json={"class_code": "INVALID-CODE-123"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_join_class_already_enrolled(
        self, client, sample_student, student_headers, sample_class, db_session
    ):
        """Test joining a class already enrolled in."""
        # First join
        from app.models.class_student import ClassStudent

        enrollment = ClassStudent(
            class_id=sample_class.class_id, student_id=sample_student.user_id
        )
        db_session.add(enrollment)
        db_session.commit()

        # Try to join again
        response = client.post(
            f"/api/v1/students/{sample_student.user_id}/classes/join",
            headers=student_headers,
            json={"class_code": sample_class.class_code},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already enrolled" in response.json()["detail"].lower()

    def test_join_archived_class(
        self, client, sample_student, student_headers, db_session, sample_teacher
    ):
        """Test joining an archived class."""
        from app.models.class_model import Class

        archived_class = Class(
            class_id="class_archived",
            teacher_id=sample_teacher.user_id,
            name="Archived Class",
            subject="Test",
            class_code="TEST-999-999",
            archived=True,
        )
        db_session.add(archived_class)
        db_session.commit()

        response = client.post(
            f"/api/v1/students/{sample_student.user_id}/classes/join",
            headers=student_headers,
            json={"class_code": "TEST-999-999"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "archived" in response.json()["detail"].lower()
