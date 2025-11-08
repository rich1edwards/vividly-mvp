"""
Unit Tests for Push Worker Notification Integration (Phase 1.4)

Tests notification publishing at key points in the content generation workflow:
- Generation started notification
- Progress update notifications
- Generation completed notification
- Generation failed notification
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from app.workers.push_worker import process_message
from app.services.notification_service import (
    NotificationEventType,
    NotificationPayload,
)


@pytest.fixture
def mock_notification_service():
    """Mock NotificationService for testing."""
    service = AsyncMock()
    service.publish_notification = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_content_generation_service():
    """Mock ContentGenerationService for testing."""
    service = MagicMock()
    return service


@pytest.fixture
def mock_content_request_service():
    """Mock ContentRequestService for testing."""
    service = MagicMock()
    service.get_request_by_id = MagicMock(return_value=None)
    service.update_status = MagicMock()
    service.set_results = MagicMock()
    service.set_error = MagicMock()
    return service


@pytest.fixture
def sample_message_data():
    """Sample Pub/Sub message data for testing."""
    return {
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "student_id": "user_123",
        "student_query": "Explain photosynthesis",
        "grade_level": "9th grade",
        "interest": "biology",
        "requested_modalities": ["video"],
        "preferred_modality": "video",
        "correlation_id": "corr_123",
    }


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock(spec=Session)
    return session


class TestNotificationStarted:
    """Tests for content generation started notification."""

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_publishes_started_notification_on_generation_start(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that started notification is published when generation begins."""
        # Mock services
        mock_content_service.generate_content_from_query = AsyncMock(
            return_value={"status": "completed", "video_url": "http://example.com/video.mp4"}
        )
        mock_notification_service.publish_notification = AsyncMock(return_value=True)
        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        # Process message
        result = await process_message(sample_message_data, mock_db_session)

        # Verify started notification was published
        assert result is True

        # Find the "started" notification call
        started_calls = [
            call for call in mock_notification_service.publish_notification.call_args_list
            if call[1]['notification'].event_type == NotificationEventType.CONTENT_GENERATION_STARTED
        ]

        assert len(started_calls) >= 1
        started_call = started_calls[0]

        # Verify notification payload
        assert started_call[1]['user_id'] == "user_123"
        notification = started_call[1]['notification']
        assert notification.event_type == NotificationEventType.CONTENT_GENERATION_STARTED
        assert notification.content_request_id == "123e4567-e89b-12d3-a456-426614174000"
        assert "Explain photosynthesis" in notification.message
        assert notification.progress_percentage == 10

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_started_notification_failure_does_not_stop_processing(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that processing continues even if started notification fails."""
        # Mock notification service to fail
        mock_notification_service.publish_notification = AsyncMock(
            side_effect=Exception("Redis unavailable")
        )
        mock_content_service.generate_content_from_query = AsyncMock(
            return_value={"status": "completed", "video_url": "http://example.com/video.mp4"}
        )
        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        # Process message should still succeed
        result = await process_message(sample_message_data, mock_db_session)

        # Processing should continue despite notification failure
        assert result is True
        mock_content_service.generate_content_from_query.assert_called_once()


class TestNotificationProgress:
    """Tests for content generation progress notifications."""

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_publishes_progress_notification_during_generation(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that progress notification is published during generation."""
        mock_content_service.generate_content_from_query = AsyncMock(
            return_value={"status": "completed", "video_url": "http://example.com/video.mp4"}
        )
        mock_notification_service.publish_notification = AsyncMock(return_value=True)
        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        result = await process_message(sample_message_data, mock_db_session)

        assert result is True

        # Find the "progress" notification call
        progress_calls = [
            call for call in mock_notification_service.publish_notification.call_args_list
            if call[1]['notification'].event_type == NotificationEventType.CONTENT_GENERATION_PROGRESS
        ]

        assert len(progress_calls) >= 1
        progress_call = progress_calls[0]

        notification = progress_call[1]['notification']
        assert notification.event_type == NotificationEventType.CONTENT_GENERATION_PROGRESS
        assert notification.progress_percentage == 90
        assert "Finalizing" in notification.message or "finalizing" in notification.message.lower()


class TestNotificationCompleted:
    """Tests for content generation completed notification."""

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_publishes_completed_notification_on_success(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that completed notification is published when generation succeeds."""
        video_url = "https://storage.googleapis.com/vividly-dev/video123.mp4"
        thumbnail_url = "https://storage.googleapis.com/vividly-dev/thumb123.png"

        mock_content_service.generate_content_from_query = AsyncMock(
            return_value={
                "status": "completed",
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "script_text": "Sample script",
            }
        )
        mock_notification_service.publish_notification = AsyncMock(return_value=True)
        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        result = await process_message(sample_message_data, mock_db_session)

        assert result is True

        # Find the "completed" notification call
        completed_calls = [
            call for call in mock_notification_service.publish_notification.call_args_list
            if call[1]['notification'].event_type == NotificationEventType.CONTENT_GENERATION_COMPLETED
        ]

        assert len(completed_calls) == 1
        completed_call = completed_calls[0]

        # Verify notification payload
        notification = completed_call[1]['notification']
        assert notification.event_type == NotificationEventType.CONTENT_GENERATION_COMPLETED
        assert notification.progress_percentage == 100
        assert "ready" in notification.title.lower() or "ready" in notification.message.lower()
        assert notification.metadata['video_url'] == video_url
        assert notification.metadata['thumbnail_url'] == thumbnail_url


class TestNotificationFailed:
    """Tests for content generation failed notification."""

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_publishes_failed_notification_on_exception(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that failed notification is published when generation fails."""
        error_message = "Gemini API timeout"

        mock_content_service.generate_content_from_query = AsyncMock(
            side_effect=Exception(error_message)
        )
        mock_notification_service.publish_notification = AsyncMock(return_value=True)
        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        result = await process_message(sample_message_data, mock_db_session)

        # Should return False to trigger retry
        assert result is False

        # Find the "failed" notification call
        failed_calls = [
            call for call in mock_notification_service.publish_notification.call_args_list
            if call[1]['notification'].event_type == NotificationEventType.CONTENT_GENERATION_FAILED
        ]

        assert len(failed_calls) == 1
        failed_call = failed_calls[0]

        # Verify notification payload
        notification = failed_call[1]['notification']
        assert notification.event_type == NotificationEventType.CONTENT_GENERATION_FAILED
        assert "failed" in notification.title.lower() or "error" in notification.title.lower()
        assert notification.progress_percentage == 0
        assert notification.metadata['error_message'] == error_message
        assert notification.metadata['error_type'] == "Exception"

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_failed_notification_error_handling(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that processing continues even if failed notification itself fails."""
        # Generation fails
        mock_content_service.generate_content_from_query = AsyncMock(
            side_effect=Exception("Generation error")
        )

        # Notification also fails
        mock_notification_service.publish_notification = AsyncMock(
            side_effect=Exception("Notification error")
        )

        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        # Should still return False (for retry) despite notification error
        result = await process_message(sample_message_data, mock_db_session)
        assert result is False

        # Error should be logged to request_service
        mock_request_service.set_error.assert_called_once()


class TestNotificationFullFlow:
    """Tests for complete notification flow across all states."""

    @pytest.mark.asyncio
    @patch("app.workers.push_worker.notification_service")
    @patch("app.workers.push_worker.content_service")
    @patch("app.workers.push_worker.request_service")
    async def test_full_successful_flow_publishes_all_notifications(
        self,
        mock_request_service,
        mock_content_service,
        mock_notification_service,
        sample_message_data,
        mock_db_session,
    ):
        """Test that all notifications are published in successful flow."""
        mock_content_service.generate_content_from_query = AsyncMock(
            return_value={
                "status": "completed",
                "video_url": "http://example.com/video.mp4",
                "thumbnail_url": "http://example.com/thumb.png",
                "script_text": "Sample script",
            }
        )
        mock_notification_service.publish_notification = AsyncMock(return_value=True)
        mock_request_service.get_request_by_id = MagicMock(return_value=None)

        result = await process_message(sample_message_data, mock_db_session)

        assert result is True

        # Verify all three notification types were published
        all_calls = mock_notification_service.publish_notification.call_args_list
        event_types = [call[1]['notification'].event_type for call in all_calls]

        assert NotificationEventType.CONTENT_GENERATION_STARTED in event_types
        assert NotificationEventType.CONTENT_GENERATION_PROGRESS in event_types
        assert NotificationEventType.CONTENT_GENERATION_COMPLETED in event_types
        assert NotificationEventType.CONTENT_GENERATION_FAILED not in event_types

        # Verify at least 3 notifications (started, progress, completed)
        assert len(all_calls) >= 3
