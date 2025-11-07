"""
Production Features Integration Tests

Tests for production-ready features implemented in Sprint 3:
- Retry count tracking
- Database indexes (validation)
- PubSub environment validation
- ContentRequestService enhancements

Run: pytest tests/test_production_features.py -v
"""

import pytest
from unittest.mock import patch
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.content_request_service import ContentRequestService
from app.services.pubsub_service import PubSubService
from app.models.request_tracking import ContentRequest
from app.core.database import SessionLocal, engine
from app.models import Base  # Import Base from models/__init__.py which includes all models


class TestRetryCountTracking:
    """Test retry count increment functionality"""

    def test_increment_retry_count_success(self, test_db: Session):
        """Test that retry count increments correctly"""
        # Create a request
        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-test-123",
            topic="Python Basics",
            learning_objective="Learn Python",
            grade_level="9th Grade",
            correlation_id="test-correlation-001"
        )

        assert request.retry_count == 0

        # Increment retry count
        result = ContentRequestService.increment_retry_count(
            db=test_db,
            request_id=request.id
        )

        assert result is True

        # Verify increment
        test_db.refresh(request)
        assert request.retry_count == 1

    def test_increment_retry_count_multiple_times(self, test_db: Session):
        """Test multiple retry count increments"""
        # Create a request
        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-test-456",
            topic="Math Algebra",
            learning_objective=None,
            grade_level="10th Grade",
            correlation_id="test-correlation-002"
        )

        # Increment 5 times (simulating max retries)
        for i in range(5):
            result = ContentRequestService.increment_retry_count(
                db=test_db,
                request_id=request.id
            )
            assert result is True

        test_db.refresh(request)
        assert request.retry_count == 5

    def test_increment_retry_count_nonexistent_request(self, test_db: Session):
        """Test incrementing retry count for non-existent request"""
        result = ContentRequestService.increment_retry_count(
            db=test_db,
            request_id="00000000-0000-0000-0000-000000000000"
        )

        # Should return False for non-existent request
        assert result is False


class TestContentRequestService:
    """Test ContentRequestService production features"""

    def test_create_request_with_correlation_id(self, test_db: Session):
        """Test creating request with custom correlation ID"""
        correlation_id = "custom-correlation-123"

        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-abc",
            topic="Chemistry Basics",
            learning_objective="Understand atoms",
            grade_level="11th Grade",
            correlation_id=correlation_id
        )

        assert request.correlation_id == correlation_id
        assert request.status == "pending"
        assert request.progress_percentage == 0
        assert request.retry_count == 0

    def test_create_request_auto_generates_correlation_id(self, test_db: Session):
        """Test that correlation ID is auto-generated if not provided"""
        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-xyz",
            topic="Biology Cells",
            learning_objective=None,
            grade_level="9th Grade"
        )

        assert request.correlation_id is not None
        assert request.correlation_id.startswith("req_")
        assert len(request.correlation_id) > 4

    def test_get_request_by_id(self, test_db: Session):
        """Test retrieving request by ID"""
        # Create request
        created = ContentRequestService.create_request(
            db=test_db,
            student_id="student-get-test",
            topic="Physics Motion",
            learning_objective=None,
            grade_level="12th Grade"
        )

        # Retrieve request
        retrieved = ContentRequestService.get_request_by_id(
            db=test_db,
            request_id=created.id
        )

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.topic == "Physics Motion"


class TestDatabaseIndexes:
    """Test database index existence (assumes migrations have run)"""

    def test_check_for_compound_indexes(self, test_db: Session):
        """Document expected indexes (may not exist until migration runs)"""
        expected_indexes = [
            'idx_content_requests_correlation_status',
            'idx_content_requests_student_status_created',
            'idx_content_requests_status_created',
            'idx_content_requests_org_status_created',
            'idx_content_requests_failed_debugging'
        ]

        # Query for indexes
        result = test_db.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'content_requests'
        """))

        existing_indexes = {row[0] for row in result.fetchall()}

        # Log which indexes exist (for debugging)
        print(f"\nExisting indexes: {existing_indexes}")

        # Note: This test documents expected indexes
        # In production, after migration, these should all exist
        for index_name in expected_indexes:
            if index_name in existing_indexes:
                print(f"✓ Index exists: {index_name}")
            else:
                print(f"✗ Index missing: {index_name} (will be created by migration)")


class TestPubSubEnvironmentValidation:
    """Test PubSub service environment validation"""

    def test_pubsub_service_requires_project_id(self):
        """Test that PubSubService validates GOOGLE_CLOUD_PROJECT"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises((ValueError, KeyError)):
                service = PubSubService()

    def test_pubsub_service_with_valid_env(self):
        """Test PubSubService initialization with valid environment"""
        with patch.dict('os.environ', {
            'GOOGLE_CLOUD_PROJECT': 'test-project-123',
            'PUBSUB_TOPIC': 'test-topic',
            'PUBSUB_SUBSCRIPTION': 'test-subscription'
        }):
            try:
                service = PubSubService()
                # If it initializes without error, validation passed
                assert True
            except Exception as e:
                # May fail due to missing credentials, but should not be ValueError
                assert not isinstance(e, ValueError), "Should not raise ValueError for valid env vars"


class TestRequestStatusTracking:
    """Test request status tracking and updates"""

    def test_mark_generating(self, test_db: Session):
        """Test marking request as generating"""
        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-status-test",
            topic="History WW2",
            learning_objective=None,
            grade_level="11th Grade"
        )

        # Mark as generating
        result = ContentRequestService.mark_generating(
            db=test_db,
            request_id=request.id
        )

        assert result is True
        test_db.refresh(request)
        assert request.status == "generating"
        assert request.started_at is not None

    def test_mark_completed(self, test_db: Session):
        """Test marking request as completed"""
        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-complete-test",
            topic="Art Renaissance",
            learning_objective=None,
            grade_level="10th Grade"
        )

        video_url = "https://storage.googleapis.com/test/video.mp4"

        # Mark as completed
        result = ContentRequestService.mark_completed(
            db=test_db,
            request_id=request.id,
            video_url=video_url
        )

        assert result is True
        test_db.refresh(request)
        assert request.status == "completed"
        assert request.video_url == video_url
        assert request.completed_at is not None

    def test_mark_failed(self, test_db: Session):
        """Test marking request as failed"""
        request = ContentRequestService.create_request(
            db=test_db,
            student_id="student-fail-test",
            topic="Music Theory",
            learning_objective=None,
            grade_level="9th Grade"
        )

        error_message = "Test error: API rate limit exceeded"
        error_stage = "script_generation"

        # Mark as failed
        result = ContentRequestService.mark_failed(
            db=test_db,
            request_id=request.id,
            error_message=error_message,
            error_stage=error_stage
        )

        assert result is True
        test_db.refresh(request)
        assert request.status == "failed"
        assert request.error_message == error_message
        assert request.error_stage == error_stage
        assert request.failed_at is not None


# Fixtures

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = SessionLocal()

    yield db

    # Cleanup
    db.close()

    # Drop all tables
    Base.metadata.drop_all(bind=engine)
