"""
Integration tests for Content Metadata API endpoints.
Tests all 5 content endpoints from Sprint 2.
"""
import pytest
from fastapi import status


class TestContentCacheLookup:
    """Test content cache check and lookup endpoints."""

    def test_check_content_exists_cache_hit(self, client, student_headers, db_session):
        """Test checking for existing content."""
        from app.models.content_metadata import ContentMetadata, GenerationStatus

        # Create existing content
        content = ContentMetadata(
            content_id="test_cache_001",
            student_id="user_student_test_001",
            topic_id="topic_newton_1",
            interest_id="int_basketball",
            title="Test Content",
            status=GenerationStatus.COMPLETED.value,
            video_url="https://cdn.test.com/video.mp4"
        )
        db_session.add(content)
        db_session.commit()

        check_data = {
            "topic_id": "topic_newton_1",
            "interest": "basketball"
        }

        response = client.post(
            "/api/v1/content/check",
            json=check_data,
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cache_hit"] is True
        assert data["cache_key"] is not None
        assert data["status"] == "completed"

    def test_check_content_exists_cache_miss(self, client, student_headers):
        """Test checking for non-existent content."""
        check_data = {
            "topic_id": "nonexistent_topic",
            "interest": "nonexistent_interest"
        }

        response = client.post(
            "/api/v1/content/check",
            json=check_data,
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cache_hit"] is False
        assert data["cache_key"] is None

    def test_get_content_by_cache_key_success(self, client, student_headers, db_session):
        """Test getting content metadata by cache key."""
        from app.models.content_metadata import ContentMetadata, GenerationStatus

        content = ContentMetadata(
            content_id="test_cache_002",
            student_id="user_student_test_001",
            topic_id="topic_newton_1",
            interest_id="int_basketball",
            title="Test Content 2",
            status=GenerationStatus.COMPLETED.value,
            video_url="https://cdn.test.com/video2.mp4",
            duration_seconds=180,
            view_count=5
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/v1/content/{content.content_id}",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cache_key"] == content.content_id
        assert data["status"] == "completed"
        assert data["video_url"] is not None
        assert data["duration_seconds"] == 180

    def test_get_content_not_found(self, client, student_headers):
        """Test getting non-existent content."""
        response = client.get(
            "/api/v1/content/nonexistent_cache_key",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestContentFeedback:
    """Test content feedback submission endpoints."""

    def test_submit_feedback_success(self, client, student_headers, db_session, sample_student):
        """Test submitting content feedback."""
        from app.models.content_metadata import ContentMetadata, GenerationStatus

        content = ContentMetadata(
            content_id="test_cache_feedback_001",
            student_id=sample_student.user_id,
            topic_id="topic_newton_1",
            interest_id="int_basketball",
            title="Test Content Feedback",
            status=GenerationStatus.COMPLETED.value,
            video_url="https://cdn.test.com/video.mp4"
        )
        db_session.add(content)
        db_session.commit()

        feedback_data = {
            "rating": 5,
            "feedback_type": "helpful",
            "comments": "Great explanation!"
        }

        response = client.post(
            f"/api/v1/content/{content.content_id}/feedback",
            json=feedback_data,
            headers=student_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["rating"] == 5
        assert data["feedback_type"] == "helpful"

    def test_submit_feedback_invalid_rating(self, client, student_headers, db_session):
        """Test that invalid ratings are rejected."""
        from app.models.content_metadata import ContentMetadata, GenerationStatus

        content = ContentMetadata(
            content_id="test_cache_feedback_002",
            student_id="user_student_test_001",
            topic_id="topic_newton_1",
            interest_id="int_basketball",
            title="Test Content",
            status=GenerationStatus.COMPLETED.value
        )
        db_session.add(content)
        db_session.commit()

        feedback_data = {
            "rating": 6,  # Invalid (must be 1-5)
            "feedback_type": "helpful"
        }

        response = client.post(
            f"/api/v1/content/{content.content_id}/feedback",
            json=feedback_data,
            headers=student_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_feedback_summary(self, client, student_headers, db_session):
        """Test getting feedback summary for content."""
        from app.models.content_metadata import ContentMetadata, GenerationStatus

        content = ContentMetadata(
            content_id="test_cache_feedback_003",
            student_id="user_student_test_001",
            topic_id="topic_newton_1",
            interest_id="int_basketball",
            title="Test Content Summary",
            status=GenerationStatus.COMPLETED.value,
            average_rating=4.5,
            view_count=10
        )
        db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/v1/content/{content.content_id}/feedback",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cache_key" in data
        assert "average_rating" in data
        # More assertions when feedback aggregation is implemented


class TestContentHistory:
    """Test content history endpoints."""

    def test_get_student_content_history(self, client, student_headers, db_session, sample_student):
        """Test getting student's content history."""
        from app.models.content_metadata import ContentMetadata, GenerationStatus

        # Create multiple content entries
        for i in range(3):
            content = ContentMetadata(
                content_id=f"history_{i}",
                student_id=sample_student.user_id,
                topic_id=f"topic_{i}",
                interest_id="int_basketball",
                title=f"History Content {i}",
                status=GenerationStatus.COMPLETED.value,
                view_count=i + 1
            )
            db_session.add(content)
        db_session.commit()

        response = client.get(
            f"/api/v1/content/student/{sample_student.user_id}/history",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "content" in data
        assert len(data["content"]) >= 3

    def test_cannot_access_other_student_history(self, client, student_headers, sample_teacher):
        """Test that students cannot access other students' history."""
        response = client.get(
            f"/api/v1/content/student/{sample_teacher.user_id}/history",
            headers=student_headers
        )

        # Should either be forbidden or return empty
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_200_OK
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # If allowed, should return empty for different user
            assert len(data.get("content", [])) == 0
