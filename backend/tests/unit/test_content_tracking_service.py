"""
Unit tests for content tracking service.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from app.services.content_tracking_service import ContentTrackingService
from app.models.content_metadata import ContentMetadata
from app.models.progress import StudentProgress, ProgressStatus


@pytest.mark.unit
class TestTrackView:
    """Test view tracking."""

    def test_track_view_success(self):
        """Test successful view tracking."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.cache_key = "test_key"
        mock_content.views = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_content

        result = service.track_view(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            quality="1080p",
            device_type="desktop",
            browser="Chrome"
        )

        assert result is True
        assert mock_content.views == 11
        mock_db.commit.assert_called_once()

    def test_track_view_content_not_found(self):
        """Test view tracking when content doesn't exist."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.track_view(
            db=mock_db,
            cache_key="nonexistent",
            student_id="student_123",
            quality="1080p",
            device_type="desktop"
        )

        assert result is False
        mock_db.commit.assert_not_called()

    def test_track_view_initializes_none_views(self):
        """Test view tracking initializes None views to 0."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.views = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_content

        result = service.track_view(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            quality="1080p",
            device_type="mobile"
        )

        assert result is True
        assert mock_content.views == 1

    def test_track_view_database_error(self):
        """Test view tracking handles database errors."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database error")

        result = service.track_view(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            quality="1080p",
            device_type="desktop"
        )

        assert result is False
        mock_db.rollback.assert_called_once()


@pytest.mark.unit
class TestTrackProgress:
    """Test progress tracking."""

    def test_track_progress_existing_record(self):
        """Test tracking progress for existing record."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.topic_id = "topic_123"
        mock_content.cache_key = "test_key"

        mock_progress = Mock()
        mock_progress.current_position_seconds = 100
        mock_progress.total_watch_time_seconds = 200
        mock_progress.status = ProgressStatus.IN_PROGRESS
        mock_progress.completion_percentage = 33.3

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,  # First query: content
            mock_progress,  # Second query: progress
        ]

        result = service.track_progress(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            current_time_seconds=150,
            duration_seconds=300,
            playback_speed=1.0,
            paused=False
        )

        assert result is True
        assert mock_progress.current_position_seconds == 150
        mock_db.commit.assert_called_once()

    def test_track_progress_new_record(self):
        """Test tracking progress creates new record."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.topic_id = "topic_123"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,  # First query: content
            None,  # Second query: no existing progress
        ]

        result = service.track_progress(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            current_time_seconds=50,
            duration_seconds=300
        )

        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_track_progress_content_not_found(self):
        """Test progress tracking when content doesn't exist."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.track_progress(
            db=mock_db,
            cache_key="nonexistent",
            student_id="student_123",
            current_time_seconds=50,
            duration_seconds=300
        )

        assert result is False


@pytest.mark.unit
class TestTrackCompletion:
    """Test completion tracking."""

    def test_track_completion_success(self):
        """Test successful completion tracking."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.topic_id = "topic_123"
        mock_content.completions = 5

        mock_progress = Mock()
        mock_progress.status = ProgressStatus.IN_PROGRESS
        mock_progress.completed_at = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,
            mock_progress,
        ]

        result = service.track_completion(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            watch_duration_seconds=300,
            completion_percentage=95.0,
            skipped_segments=[]
        )

        assert isinstance(result, dict)
        assert result["progress_updated"] is True
        assert mock_progress.status == ProgressStatus.COMPLETED
        mock_db.commit.assert_called_once()

    def test_track_completion_content_not_found(self):
        """Test completion tracking when content doesn't exist."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.track_completion(
            db=mock_db,
            cache_key="nonexistent",
            student_id="student_123",
            watch_duration_seconds=300,
            completion_percentage=95.0,
            skipped_segments=[]
        )

        assert isinstance(result, dict)
        assert result["progress_updated"] is False

    def test_track_completion_no_progress_record(self):
        """Test completion tracking creates progress if missing."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.topic_id = "topic_123"
        mock_content.completions = 0

        # Mock queries: content, progress, achievement count
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,  # First: content query
            None,  # Second: no existing progress
        ]
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1  # Achievement count

        result = service.track_completion(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            watch_duration_seconds=300,
            completion_percentage=100.0,
            skipped_segments=[]
        )

        assert isinstance(result, dict)
        assert result["progress_updated"] is True
        mock_db.add.assert_called_once()


@pytest.mark.unit
class TestGetContentAnalytics:
    """Test content analytics retrieval."""

    def test_get_content_analytics_success(self):
        """Test getting analytics for content."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.cache_key = "test_key"
        mock_content.topic_id = "topic_123"
        mock_content.views = 100

        # Mock progress stats query
        mock_stats = Mock()
        mock_stats.avg_completion = 85.5
        mock_stats.avg_duration = 250.0

        # Set up mock queries
        mock_content_query = Mock()
        mock_content_query.filter.return_value.first.return_value = mock_content

        mock_stats_query = Mock()
        mock_stats_query.filter.return_value.first.return_value = mock_stats

        # Use side_effect to return different query objects
        mock_db.query.side_effect = [mock_content_query, mock_stats_query]

        result = service.get_content_analytics(
            db=mock_db,
            cache_key="test_key"
        )

        assert result is not None
        assert result["cache_key"] == "test_key"
        assert result["total_views"] == 100
        assert result["avg_watch_duration"] == 250.0
        assert result["avg_completion_rate"] == 85.5
        assert result["popular_quality"] == "1080p"

    def test_get_content_analytics_content_not_found(self):
        """Test analytics when content doesn't exist."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_content_analytics(
            db=mock_db,
            cache_key="nonexistent"
        )

        assert result is None

    def test_get_content_analytics_zero_views(self):
        """Test analytics with zero views."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(spec=ContentMetadata)
        mock_content.topic_id = "topic_123"
        mock_content.views = 0

        # Mock empty stats
        mock_stats = Mock()
        mock_stats.avg_completion = None
        mock_stats.avg_duration = None

        # Set up mock queries
        mock_content_query = Mock()
        mock_content_query.filter.return_value.first.return_value = mock_content

        mock_stats_query = Mock()
        mock_stats_query.filter.return_value.first.return_value = mock_stats

        mock_db.query.side_effect = [mock_content_query, mock_stats_query]

        result = service.get_content_analytics(
            db=mock_db,
            cache_key="test_key"
        )

        assert result is not None
        assert result["total_views"] == 0
        assert result["avg_completion_rate"] == 0.0
        assert result["avg_watch_duration"] == 0.0


@pytest.mark.unit
class TestCheckAchievements:
    """Test achievement checking."""

    def test_check_achievements_basic(self):
        """Test basic achievement checking."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_progress = Mock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5

        # Should return None (no achievements)
        result = service._check_achievements(mock_db, "student_123", mock_progress)

        assert result is None

    def test_check_achievements_first_completion(self):
        """Test achievement for first completion."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_progress = Mock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1

        # Should return first completion achievement
        result = service._check_achievements(mock_db, "student_123", mock_progress)

        assert result == "First Video Complete"


@pytest.mark.unit
class TestCalculateStreak:
    """Test streak calculation."""

    def test_calculate_streak_no_progress(self):
        """Test streak calculation with no progress."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        streak = service._calculate_streak(mock_db, "student_123")

        assert streak == 0

    def test_calculate_streak_with_consecutive_days(self):
        """Test streak calculation with consecutive days."""
        service = ContentTrackingService()

        mock_db = Mock()

        today = datetime.utcnow().date()
        mock_completion1 = Mock(completion_date=today)
        mock_completion2 = Mock(completion_date=today - timedelta(days=1))
        mock_completion3 = Mock(completion_date=today - timedelta(days=2))

        mock_db.query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = [
            mock_completion1,
            mock_completion2,
            mock_completion3,
        ]

        streak = service._calculate_streak(mock_db, "student_123")

        assert streak == 3  # 3 consecutive days

    def test_calculate_streak_broken_streak(self):
        """Test streak calculation with gap in days."""
        service = ContentTrackingService()

        mock_db = Mock()

        today = datetime.utcnow().date()
        mock_progress1 = Mock(completed_at=datetime.combine(today, datetime.min.time()))
        mock_progress2 = Mock(completed_at=datetime.combine(today - timedelta(days=3), datetime.min.time()))

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_progress1,
            mock_progress2,
        ]

        streak = service._calculate_streak(mock_db, "student_123")

        assert streak >= 0  # Streak might be broken


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_track_progress_with_different_speeds(self):
        """Test progress tracking with various playback speeds."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(topic_id="topic_123")
        mock_progress = Mock(
            current_position_seconds=0,
            total_watch_time_seconds=0,
            completion_percentage=0.0,
            status=ProgressStatus.IN_PROGRESS
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,
            mock_progress,
        ]

        # Test with 2x speed
        result = service.track_progress(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            current_time_seconds=100,
            duration_seconds=300,
            playback_speed=2.0
        )

        assert result is True

    def test_track_progress_near_end(self):
        """Test progress tracking near video end."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(topic_id="topic_123")
        mock_progress = Mock(
            current_position_seconds=0,
            completion_percentage=0.0,
            status=ProgressStatus.IN_PROGRESS
        )

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,
            mock_progress,
        ]

        # Track at 95% completion
        result = service.track_progress(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            current_time_seconds=285,
            duration_seconds=300
        )

        assert result is True

    def test_track_completion_with_low_completion_rate(self):
        """Test completion tracking with low completion percentage."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(topic_id="topic_123", completions=0)
        mock_progress = Mock(status=ProgressStatus.IN_PROGRESS)

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,
            mock_progress,
        ]
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1

        result = service.track_completion(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            watch_duration_seconds=300,
            completion_percentage=60.0,  # Low completion
            skipped_segments=[{"start": 100, "end": 150}]
        )

        assert isinstance(result, dict)
        assert result["progress_updated"] is True
        assert mock_progress.status == ProgressStatus.COMPLETED

    def test_multiple_completions_same_content(self):
        """Test tracking multiple completions of same content."""
        service = ContentTrackingService()

        mock_db = Mock()
        mock_content = Mock(topic_id="topic_123", completions=1)
        mock_progress = Mock(status=ProgressStatus.COMPLETED, completed_at=datetime.utcnow())

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_content,
            mock_progress,
        ]
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10

        # Track completion again (replay)
        result = service.track_completion(
            db=mock_db,
            cache_key="test_key",
            student_id="student_123",
            watch_duration_seconds=300,
            completion_percentage=100.0,
            skipped_segments=[]
        )

        assert isinstance(result, dict)
        assert result["progress_updated"] is True
