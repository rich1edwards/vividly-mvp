"""
Integration tests for Async Content Generation Architecture.

Tests the complete async flow:
API → Pub/Sub → Worker → Database → Status Polling

This test suite verifies the async content generation system end-to-end.
"""
import pytest
import asyncio
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi import status


class TestAsyncContentGeneration:
    """Test async content generation flow."""

    @pytest.mark.asyncio
    async def test_generate_content_returns_202_accepted(
        self, client, student_headers, db_session, sample_student, sample_interests
    ):
        """Test that /generate endpoint returns 202 Accepted immediately."""
        request_data = {
            "student_id": str(sample_student.user_id),
            "student_query": "Explain Newton's Third Law with basketball",
            "grade_level": 10,
            "interest": "basketball",
        }

        # Mock Pub/Sub publish to avoid real GCP calls in tests
        with patch("app.services.pubsub_service.PubSubService.publish_content_request") as mock_publish:
            mock_publish.return_value = {
                "success": True,
                "message_id": "test_message_123",
                "topic": "projects/test/topics/content-requests-test"
            }

            response = client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=student_headers
            )

        # Should return 202 Accepted immediately
        assert response.status_code == status.HTTP_202_ACCEPTED

        data = response.json()
        assert data["status"] == "pending"
        assert "request_id" in data
        assert "correlation_id" in data
        assert data["message"] is not None
        assert data["estimated_completion_seconds"] > 0

        # Verify Pub/Sub publish was called
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args.kwargs["student_id"] == str(sample_student.user_id)
        assert call_args.kwargs["student_query"] == request_data["student_query"]
        assert call_args.kwargs["grade_level"] == request_data["grade_level"]

    @pytest.mark.asyncio
    async def test_content_request_created_in_database(
        self, client, student_headers, db_session, sample_student
    ):
        """Test that ContentRequest record is created in database."""
        from app.models.request_tracking import ContentRequest

        request_data = {
            "student_id": str(sample_student.user_id),
            "student_query": "Explain photosynthesis with gaming",
            "grade_level": 10,
        }

        with patch("app.services.pubsub_service.PubSubService.publish_content_request") as mock_publish:
            mock_publish.return_value = {"success": True, "message_id": "test_123"}

            response = client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=student_headers
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        request_id = response.json()["request_id"]

        # Verify ContentRequest was created in database
        content_request = db_session.query(ContentRequest).filter(
            ContentRequest.id == request_id
        ).first()

        assert content_request is not None
        assert content_request.student_id == uuid.UUID(sample_student.user_id)
        assert content_request.topic == request_data["student_query"]
        assert content_request.grade_level == str(request_data["grade_level"])
        assert content_request.status == "pending"
        assert content_request.progress_percentage == 0
        assert content_request.created_at is not None

    @pytest.mark.asyncio
    async def test_status_polling_returns_pending(
        self, client, student_headers, db_session, sample_student
    ):
        """Test that status polling returns pending state immediately after creation."""
        from app.models.request_tracking import ContentRequest
        import uuid

        # Create a ContentRequest directly
        request_id = uuid.uuid4()
        correlation_id = f"req_{uuid.uuid4().hex[:16]}"

        content_request = ContentRequest(
            id=request_id,
            correlation_id=correlation_id,
            student_id=sample_student.user_id,
            topic="Test topic",
            grade_level="10",
            status="pending",
            progress_percentage=0,
        )
        db_session.add(content_request)
        db_session.commit()

        # Poll status endpoint
        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["request_id"] == str(request_id)
        assert data["correlation_id"] == correlation_id
        assert data["status"] == "pending"
        assert data["progress_percentage"] == 0
        assert data["created_at"] is not None

    @pytest.mark.asyncio
    async def test_status_polling_returns_generating(
        self, client, student_headers, db_session, sample_student
    ):
        """Test status polling returns generating state with progress."""
        from app.models.request_tracking import ContentRequest
        import uuid
        from datetime import datetime

        request_id = uuid.uuid4()

        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_{uuid.uuid4().hex[:16]}",
            student_id=sample_student.user_id,
            topic="Test topic",
            grade_level="10",
            status="generating",
            progress_percentage=45,
            current_stage="Generating video from script and audio",
            started_at=datetime.utcnow(),
        )
        db_session.add(content_request)
        db_session.commit()

        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "generating"
        assert data["progress_percentage"] == 45
        assert data["current_stage"] == "Generating video from script and audio"
        assert data["started_at"] is not None

    @pytest.mark.asyncio
    async def test_status_polling_returns_completed(
        self, client, student_headers, db_session, sample_student
    ):
        """Test status polling returns completed state with results."""
        from app.models.request_tracking import ContentRequest
        import uuid
        from datetime import datetime

        request_id = uuid.uuid4()

        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_{uuid.uuid4().hex[:16]}",
            student_id=sample_student.user_id,
            topic="Test topic",
            grade_level="10",
            status="completed",
            progress_percentage=100,
            current_stage="Complete",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            video_url="gs://vividly-test/videos/test.mp4",
            script_text="Test script content...",
            thumbnail_url="gs://vividly-test/thumbnails/test.jpg",
        )
        db_session.add(content_request)
        db_session.commit()

        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "completed"
        assert data["progress_percentage"] == 100
        assert data["current_stage"] == "Complete"
        assert data["video_url"] is not None
        assert data["script_text"] is not None
        assert data["thumbnail_url"] is not None
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_status_polling_returns_failed(
        self, client, student_headers, db_session, sample_student
    ):
        """Test status polling returns failed state with error details."""
        from app.models.request_tracking import ContentRequest
        import uuid
        from datetime import datetime

        request_id = uuid.uuid4()

        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_{uuid.uuid4().hex[:16]}",
            student_id=sample_student.user_id,
            topic="Test topic",
            grade_level="10",
            status="failed",
            progress_percentage=35,
            current_stage="Generating script with Gemini",
            started_at=datetime.utcnow(),
            failed_at=datetime.utcnow(),
            error_message="Gemini API quota exceeded",
            error_stage="script_generation",
            error_details={"exception_type": "QuotaExceededError"},
        )
        db_session.add(content_request)
        db_session.commit()

        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "failed"
        assert data["progress_percentage"] == 35
        assert data["error_message"] is not None
        assert data["error_stage"] == "script_generation"
        assert data["error_details"] is not None
        assert data["failed_at"] is not None

    @pytest.mark.asyncio
    async def test_student_cannot_access_other_student_request(
        self, client, student_headers, db_session, sample_teacher
    ):
        """Test that students cannot access other students' requests."""
        from app.models.request_tracking import ContentRequest
        import uuid

        request_id = uuid.uuid4()

        # Create request for different user (teacher)
        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_{uuid.uuid4().hex[:16]}",
            student_id=sample_teacher.user_id,  # Different user
            topic="Test topic",
            grade_level="10",
            status="pending",
            progress_percentage=0,
        )
        db_session.add(content_request)
        db_session.commit()

        # Try to access with student credentials
        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )

        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_status_polling_not_found(
        self, client, student_headers
    ):
        """Test that polling non-existent request returns 404."""
        import uuid

        fake_request_id = uuid.uuid4()

        response = client.get(
            f"/api/v1/content/request/{fake_request_id}/status",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestContentRequestService:
    """Test ContentRequestService operations."""

    def test_create_request(self, db_session, sample_student):
        """Test creating a new content request."""
        from app.services.content_request_service import ContentRequestService

        service = ContentRequestService()

        request = service.create_request(
            db=db_session,
            student_id=str(sample_student.user_id),
            topic="Test physics topic",
            learning_objective="Understand Newton's laws",
            grade_level="10",
            duration_minutes=3,
        )

        assert request is not None
        assert request.student_id == uuid.UUID(sample_student.user_id)
        assert request.topic == "Test physics topic"
        assert request.status == "pending"
        assert request.progress_percentage == 0
        assert request.correlation_id is not None

    def test_update_status(self, db_session, sample_student):
        """Test updating request status."""
        from app.services.content_request_service import ContentRequestService
        from app.models.request_tracking import ContentRequest

        # Create request
        request_id = uuid.uuid4()
        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_test",
            student_id=sample_student.user_id,
            topic="Test",
            grade_level="10",
            status="pending",
            progress_percentage=0,
        )
        db_session.add(content_request)
        db_session.commit()

        # Update status
        service = ContentRequestService()
        success = service.update_status(
            db=db_session,
            request_id=str(request_id),
            status="generating",
            progress_percentage=50,
            current_stage="Generating video",
        )

        assert success is True

        # Verify update
        db_session.refresh(content_request)
        assert content_request.status == "generating"
        assert content_request.progress_percentage == 50
        assert content_request.current_stage == "Generating video"

    def test_set_results(self, db_session, sample_student):
        """Test setting results for completed request."""
        from app.services.content_request_service import ContentRequestService
        from app.models.request_tracking import ContentRequest

        request_id = uuid.uuid4()
        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_test",
            student_id=sample_student.user_id,
            topic="Test",
            grade_level="10",
            status="generating",
            progress_percentage=90,
        )
        db_session.add(content_request)
        db_session.commit()

        service = ContentRequestService()
        success = service.set_results(
            db=db_session,
            request_id=str(request_id),
            video_url="gs://test/video.mp4",
            script_text="Test script",
            thumbnail_url="gs://test/thumb.jpg",
        )

        assert success is True

        db_session.refresh(content_request)
        assert content_request.video_url == "gs://test/video.mp4"
        assert content_request.script_text == "Test script"
        assert content_request.thumbnail_url == "gs://test/thumb.jpg"

    def test_set_error(self, db_session, sample_student):
        """Test setting error for failed request."""
        from app.services.content_request_service import ContentRequestService
        from app.models.request_tracking import ContentRequest

        request_id = uuid.uuid4()
        content_request = ContentRequest(
            id=request_id,
            correlation_id=f"req_test",
            student_id=sample_student.user_id,
            topic="Test",
            grade_level="10",
            status="generating",
            progress_percentage=30,
        )
        db_session.add(content_request)
        db_session.commit()

        service = ContentRequestService()
        success = service.set_error(
            db=db_session,
            request_id=str(request_id),
            error_message="API quota exceeded",
            error_stage="script_generation",
            error_details={"code": "QUOTA_EXCEEDED"},
        )

        assert success is True

        db_session.refresh(content_request)
        assert content_request.status == "failed"
        assert content_request.error_message == "API quota exceeded"
        assert content_request.error_stage == "script_generation"
        assert content_request.error_details["code"] == "QUOTA_EXCEEDED"
        assert content_request.failed_at is not None

    def test_get_request_status(self, db_session, sample_student):
        """Test getting request status for API response."""
        from app.services.content_request_service import ContentRequestService
        from app.models.request_tracking import ContentRequest

        request_id = uuid.uuid4()
        correlation_id = f"req_{uuid.uuid4().hex[:16]}"

        content_request = ContentRequest(
            id=request_id,
            correlation_id=correlation_id,
            student_id=sample_student.user_id,
            topic="Test topic",
            grade_level="10",
            status="completed",
            progress_percentage=100,
            current_stage="Complete",
            video_url="gs://test/video.mp4",
        )
        db_session.add(content_request)
        db_session.commit()

        service = ContentRequestService()
        status_data = service.get_request_status(
            db=db_session,
            request_id=str(request_id),
        )

        assert status_data is not None
        assert status_data["request_id"] == str(request_id)
        assert status_data["correlation_id"] == correlation_id
        assert status_data["status"] == "completed"
        assert status_data["progress_percentage"] == 100
        assert status_data["video_url"] == "gs://test/video.mp4"


class TestPubSubService:
    """Test PubSubService operations."""

    @pytest.mark.asyncio
    async def test_publish_content_request(self):
        """Test publishing content request to Pub/Sub."""
        from app.services.pubsub_service import PubSubService
        import uuid

        request_id = str(uuid.uuid4())
        correlation_id = f"req_{uuid.uuid4().hex[:16]}"

        service = PubSubService(project_id="test-project")

        # Mock the publisher
        with patch.object(service, "publisher") as mock_publisher:
            mock_future = Mock()
            mock_future.result.return_value = "test_message_id_123"
            mock_publisher.publish.return_value = mock_future

            result = await service.publish_content_request(
                request_id=request_id,
                correlation_id=correlation_id,
                student_id="student_123",
                student_query="Explain Newton's law",
                grade_level=10,
                interest="basketball",
            )

            assert result["success"] is True
            assert result["message_id"] == "test_message_id_123"
            assert result["request_id"] == request_id

            # Verify publish was called with correct arguments
            mock_publisher.publish.assert_called_once()
            call_args = mock_publisher.publish.call_args

            # Verify message data
            import json
            message_data = json.loads(call_args[0][1].decode("utf-8"))
            assert message_data["request_id"] == request_id
            assert message_data["student_query"] == "Explain Newton's law"
            assert message_data["grade_level"] == 10
            assert message_data["interest"] == "basketball"

    def test_health_check_healthy(self):
        """Test health check when Pub/Sub is healthy."""
        from app.services.pubsub_service import PubSubService

        service = PubSubService(project_id="test-project")

        with patch.object(service, "publisher") as mock_publisher:
            mock_publisher.get_topic.return_value = Mock()

            health = service.health_check()

            assert health["healthy"] is True
            assert health["project_id"] == "test-project"
            assert "topic" in health

    def test_health_check_unhealthy(self):
        """Test health check when Pub/Sub has issues."""
        from app.services.pubsub_service import PubSubService

        service = PubSubService(project_id="test-project")

        with patch.object(service, "publisher") as mock_publisher:
            mock_publisher.get_topic.side_effect = Exception("Connection failed")

            health = service.health_check()

            assert health["healthy"] is False
            assert "error" in health


class TestEndToEndAsyncFlow:
    """Test complete end-to-end async flow (mocked worker)."""

    @pytest.mark.asyncio
    async def test_complete_async_flow_success(
        self, client, student_headers, db_session, sample_student
    ):
        """
        Test complete async flow: API → Pub/Sub → Worker (mocked) → Polling.

        This simulates the full lifecycle:
        1. POST /generate returns 202 Accepted
        2. ContentRequest created in DB (status: pending)
        3. Worker processes (mocked) and updates status
        4. GET /status returns completed with results
        """
        from app.services.content_request_service import ContentRequestService

        request_data = {
            "student_id": str(sample_student.user_id),
            "student_query": "Explain cellular respiration with basketball",
            "grade_level": 10,
            "interest": "basketball",
        }

        # Step 1: POST /generate
        with patch("app.services.pubsub_service.PubSubService.publish_content_request") as mock_publish:
            mock_publish.return_value = {"success": True, "message_id": "test_msg_123"}

            response = client.post(
                "/api/v1/content/generate",
                json=request_data,
                headers=student_headers
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        request_id = response.json()["request_id"]

        # Step 2: Verify ContentRequest created (pending)
        service = ContentRequestService()
        status_data = service.get_request_status(db=db_session, request_id=request_id)

        assert status_data["status"] == "pending"
        assert status_data["progress_percentage"] == 0

        # Step 3: Simulate worker processing
        # Update to validating (5%)
        service.update_status(
            db=db_session,
            request_id=request_id,
            status="validating",
            progress_percentage=5,
            current_stage="Validating request parameters",
        )

        # Poll status - should be validating
        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "validating"
        assert response.json()["progress_percentage"] == 5

        # Update to generating (45%)
        service.update_status(
            db=db_session,
            request_id=request_id,
            status="generating",
            progress_percentage=45,
            current_stage="Generating video from script and audio",
        )

        # Poll status - should be generating
        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "generating"
        assert response.json()["progress_percentage"] == 45

        # Update to uploading (90%)
        service.update_status(
            db=db_session,
            request_id=request_id,
            status="generating",
            progress_percentage=90,
            current_stage="Finalizing video and uploading to storage",
        )

        # Set results
        service.set_results(
            db=db_session,
            request_id=request_id,
            video_url="gs://vividly-test/videos/cellular_respiration_basketball.mp4",
            script_text="Let me explain cellular respiration using basketball...",
            thumbnail_url="gs://vividly-test/thumbnails/cellular_respiration.jpg",
        )

        # Update to completed (100%)
        service.update_status(
            db=db_session,
            request_id=request_id,
            status="completed",
            progress_percentage=100,
            current_stage="Complete",
        )

        # Step 4: Final poll - should be completed
        response = client.get(
            f"/api/v1/content/request/{request_id}/status",
            headers=student_headers
        )

        assert response.status_code == status.HTTP_200_OK
        final_data = response.json()

        assert final_data["status"] == "completed"
        assert final_data["progress_percentage"] == 100
        assert final_data["current_stage"] == "Complete"
        assert final_data["video_url"] is not None
        assert "basketball" in final_data["video_url"]
        assert final_data["script_text"] is not None
        assert final_data["thumbnail_url"] is not None
        assert final_data["completed_at"] is not None

        # Verify duration
        from datetime import datetime
        created_at = datetime.fromisoformat(final_data["created_at"].replace("Z", "+00:00"))
        completed_at = datetime.fromisoformat(final_data["completed_at"].replace("Z", "+00:00"))
        duration = (completed_at - created_at).total_seconds()

        # In real scenario this would be 3-15 minutes, but in test it's instant
        assert duration >= 0
