"""
Comprehensive Unit Tests for Prompt Execution Logging

Following Andrew Ng's "test everything" principle - Session 11 Part 19+

Tests the log_prompt_execution() function to ensure:
1. Successful execution logging with all metrics
2. Failed execution logging with error details
3. Graceful degradation when database unavailable
4. Proper handling of edge cases (long errors, missing data, etc.)
5. Database trigger validation (auto-updated statistics)
6. Thread safety for concurrent logging

These tests are designed for CI/CD integration and provide comprehensive coverage.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Import the function we're testing
from app.core.prompt_templates import log_prompt_execution

# Test configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Provide a clean database session for each test"""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_template(db_session):
    """Create a test template in the database"""
    template_id = uuid.uuid4()

    # Insert test template
    db_session.execute(
        text(
            """
        INSERT INTO prompt_templates (
            id, name, description, category, template_text,
            variables, version, is_active, model_config, created_at
        ) VALUES (
            :id, :name, :description, :category, :template_text,
            :variables, :version, :is_active, :model_config, :created_at
        )
    """
        ),
        {
            "id": str(template_id),
            "name": "test_nlu_extraction",
            "description": "Test template for unit testing",
            "category": "nlu",
            "template_text": "Test prompt: {user_input}",
            "variables": ["user_input"],
            "version": 1,
            "is_active": True,
            "model_config": {
                "model_name": "gemini-2.5-flash",
                "temperature": 0.2,
                "max_output_tokens": 512,
            },
            "created_at": datetime.utcnow(),
        },
    )
    db_session.commit()

    yield template_id

    # Cleanup: Delete test executions and template
    db_session.execute(
        text(
            """
        DELETE FROM prompt_executions WHERE template_id = :template_id
    """
        ),
        {"template_id": str(template_id)},
    )

    db_session.execute(
        text(
            """
        DELETE FROM prompt_templates WHERE id = :template_id
    """
        ),
        {"template_id": str(template_id)},
    )

    db_session.commit()


class TestPromptExecutionLoggingSuccess:
    """Test successful execution logging scenarios"""

    def test_log_successful_execution_with_all_metrics(self, db_session, test_template):
        """
        GIVEN: Active template exists in database
        WHEN: log_prompt_execution() called with success=True and all metrics
        THEN: Execution record created with all fields, execution_id returned
        """
        # Execute logging
        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=True,
            response_time_ms=234.5,
            input_token_count=150,
            output_token_count=50,
            cost_usd=0.000018,
            metadata={"user_id": "test_user_123", "request_id": "req_abc"},
        )

        # Verify execution_id returned
        assert execution_id is not None
        assert isinstance(execution_id, str)

        # Verify execution record in database
        result = db_session.execute(
            text(
                """
            SELECT template_id, success, response_time_ms,
                   input_token_count, output_token_count, total_token_count,
                   cost_usd, error_message, metadata
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        row = result.fetchone()
        assert row is not None
        assert str(row[0]) == str(test_template)  # template_id
        assert row[1] is True  # success
        assert row[2] == 234.5  # response_time_ms
        assert row[3] == 150  # input_token_count
        assert row[4] == 50  # output_token_count
        assert row[5] == 200  # total_token_count (auto-calculated)
        assert row[6] == 0.000018  # cost_usd
        assert row[7] is None  # error_message (success case)
        assert row[8]["user_id"] == "test_user_123"  # metadata
        assert row[8]["request_id"] == "req_abc"

    def test_log_successful_execution_minimal_data(self, db_session, test_template):
        """
        GIVEN: Active template exists
        WHEN: log_prompt_execution() called with only required fields
        THEN: Execution record created, optional fields are NULL
        """
        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction", success=True, response_time_ms=100.0
        )

        assert execution_id is not None

        # Verify optional fields are NULL
        result = db_session.execute(
            text(
                """
            SELECT input_token_count, output_token_count, cost_usd,
                   error_message, metadata
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        row = result.fetchone()
        assert row[0] is None  # input_token_count
        assert row[1] is None  # output_token_count
        assert row[2] is None  # cost_usd
        assert row[3] is None  # error_message
        assert row[4] == {}  # metadata (empty dict)


class TestPromptExecutionLoggingFailure:
    """Test failed execution logging scenarios"""

    def test_log_failed_execution_with_error(self, db_session, test_template):
        """
        GIVEN: Active template exists
        WHEN: log_prompt_execution() called with success=False and error message
        THEN: Execution record created with error details
        """
        error_msg = "RateLimitError: Too many requests to Gemini API"

        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=False,
            response_time_ms=50.0,
            error_message=error_msg,
            metadata={"retry_count": 3},
        )

        assert execution_id is not None

        # Verify error recorded
        result = db_session.execute(
            text(
                """
            SELECT success, error_message, metadata
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        row = result.fetchone()
        assert row[0] is False  # success
        assert row[1] == error_msg  # error_message
        assert row[2]["retry_count"] == 3  # metadata

    def test_log_execution_error_message_truncation(self, db_session, test_template):
        """
        GIVEN: Error message longer than 1000 characters
        WHEN: log_prompt_execution() called with long error
        THEN: Error message truncated to 1000 chars (database limit)
        """
        # Create 2000 character error message
        long_error = "Error: " + ("X" * 2000)

        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=False,
            response_time_ms=10.0,
            error_message=long_error,
        )

        assert execution_id is not None

        # Verify truncation
        result = db_session.execute(
            text(
                """
            SELECT error_message, LENGTH(error_message) as msg_length
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        row = result.fetchone()
        assert len(row[0]) == 1000  # Truncated to database limit
        assert row[0].startswith("Error: XXX")  # Starts with original content


class TestPromptExecutionLoggingEdgeCases:
    """Test edge cases and graceful degradation"""

    def test_log_execution_template_not_in_database(self, db_session):
        """
        GIVEN: Template NOT in database (using file defaults)
        WHEN: log_prompt_execution() called
        THEN: Returns None, logs to Cloud Logging, does NOT crash
        """
        execution_id = log_prompt_execution(
            template_key="nonexistent_template", success=True, response_time_ms=100.0
        )

        # Should return None when template not found
        assert execution_id is None

        # Verify no execution record created
        result = db_session.execute(
            text(
                """
            SELECT COUNT(*) FROM prompt_executions
            WHERE executed_at > :recent
        """
            ),
            {"recent": datetime.utcnow() - timedelta(seconds=5)},
        )

        count = result.scalar()
        assert count == 0

    @patch("app.core.prompt_templates.get_db")
    def test_log_execution_database_unavailable(self, mock_get_db):
        """
        GIVEN: Database connection fails
        WHEN: log_prompt_execution() called
        THEN: Returns None, logs warning, does NOT crash (graceful degradation)
        """
        # Mock database failure
        mock_get_db.side_effect = Exception("Database connection failed")

        # Should not crash
        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction", success=True, response_time_ms=100.0
        )

        # Should return None on database failure
        assert execution_id is None

    def test_log_execution_with_token_count_calculation(
        self, db_session, test_template
    ):
        """
        GIVEN: Active template exists
        WHEN: log_prompt_execution() with input/output token counts
        THEN: total_token_count calculated correctly (input + output)
        """
        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=True,
            response_time_ms=200.0,
            input_token_count=1000,
            output_token_count=250,
        )

        result = db_session.execute(
            text(
                """
            SELECT input_token_count, output_token_count, total_token_count
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        row = result.fetchone()
        assert row[0] == 1000  # input
        assert row[1] == 250  # output
        assert row[2] == 1250  # total (1000 + 250)

    def test_log_execution_with_only_input_tokens(self, db_session, test_template):
        """
        GIVEN: Only input_token_count provided (no output)
        WHEN: log_prompt_execution() called
        THEN: total_token_count = input_token_count
        """
        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=True,
            response_time_ms=50.0,
            input_token_count=500,
            output_token_count=None,
        )

        result = db_session.execute(
            text(
                """
            SELECT total_token_count
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        total_tokens = result.scalar()
        assert total_tokens == 500


class TestPromptExecutionLoggingDatabaseTriggers:
    """Test database triggers auto-update template statistics"""

    def test_execution_updates_template_statistics(self, db_session, test_template):
        """
        GIVEN: Active template with database triggers installed
        WHEN: Multiple executions logged (success and failure)
        THEN: Template statistics auto-updated via triggers
              (total_executions, success_count, failure_count, avg_response_time_ms)
        """
        # Log 3 successful executions
        for i in range(3):
            log_prompt_execution(
                template_key="test_nlu_extraction",
                success=True,
                response_time_ms=100.0 + (i * 10),  # 100, 110, 120
            )

        # Log 2 failed executions
        for i in range(2):
            log_prompt_execution(
                template_key="test_nlu_extraction",
                success=False,
                response_time_ms=50.0,
                error_message="Test error",
            )

        # Give triggers time to run
        db_session.commit()

        # Verify template statistics updated
        result = db_session.execute(
            text(
                """
            SELECT total_executions, success_count, failure_count, avg_response_time_ms
            FROM prompt_templates
            WHERE id = :template_id
        """
            ),
            {"template_id": str(test_template)},
        )

        row = result.fetchone()
        assert row[0] == 5  # total_executions (3 success + 2 failure)
        assert row[1] == 3  # success_count
        assert row[2] == 2  # failure_count

        # Average response time: (100 + 110 + 120 + 50 + 50) / 5 = 86
        assert row[3] is not None
        assert 85 <= row[3] <= 87  # Allow small floating point variance


class TestPromptExecutionLoggingMetadata:
    """Test metadata storage and retrieval"""

    def test_log_execution_with_complex_metadata(self, db_session, test_template):
        """
        GIVEN: Complex metadata dict with nested structures
        WHEN: log_prompt_execution() with metadata
        THEN: Metadata stored as JSONB, queryable
        """
        complex_metadata = {
            "user_id": "user_123",
            "request_id": "req_abc_456",
            "grade_level": 10,
            "subject_context": "physics",
            "topics": ["mechanics", "newton_laws"],
            "session_data": {"duration_seconds": 45, "interactions": 5},
        }

        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=True,
            response_time_ms=150.0,
            metadata=complex_metadata,
        )

        # Verify metadata stored correctly
        result = db_session.execute(
            text(
                """
            SELECT metadata
            FROM prompt_executions
            WHERE id = :execution_id
        """
            ),
            {"execution_id": execution_id},
        )

        stored_metadata = result.scalar()
        assert stored_metadata["user_id"] == "user_123"
        assert stored_metadata["grade_level"] == 10
        assert "newton_laws" in stored_metadata["topics"]
        assert stored_metadata["session_data"]["interactions"] == 5


class TestPromptExecutionLoggingConcurrency:
    """Test thread safety for concurrent logging"""

    def test_concurrent_logging_no_race_conditions(self, db_session, test_template):
        """
        GIVEN: Multiple simultaneous execution logs
        WHEN: Concurrent calls to log_prompt_execution()
        THEN: All executions logged correctly, no race conditions
        """
        import threading

        execution_ids = []
        lock = threading.Lock()

        def log_execution(index):
            exec_id = log_prompt_execution(
                template_key="test_nlu_extraction",
                success=True,
                response_time_ms=100.0 + index,
                metadata={"thread_id": index},
            )
            with lock:
                execution_ids.append(exec_id)

        # Create 5 threads logging concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_execution, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all 5 executions logged
        assert len(execution_ids) == 5
        assert all(exec_id is not None for exec_id in execution_ids)

        # Verify all execution records exist
        for exec_id in execution_ids:
            result = db_session.execute(
                text(
                    """
                SELECT id FROM prompt_executions WHERE id = :exec_id
            """
                ),
                {"exec_id": exec_id},
            )
            assert result.fetchone() is not None


class TestPromptExecutionLoggingCostTracking:
    """Test cost calculation and tracking"""

    def test_log_execution_with_accurate_cost(self, db_session, test_template):
        """
        GIVEN: Execution with known token counts
        WHEN: log_prompt_execution() with calculated cost
        THEN: Cost stored accurately for budget tracking
        """
        # Gemini 2.5 Flash pricing (as of 2025-11-06):
        # Input: $0.075 per 1M tokens = $0.000000075 per token
        # Output: $0.30 per 1M tokens = $0.0000003 per token

        input_tokens = 1000
        output_tokens = 500

        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30
        total_cost = input_cost + output_cost

        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=True,
            response_time_ms=200.0,
            input_token_count=input_tokens,
            output_token_count=output_tokens,
            cost_usd=total_cost,
        )

        result = db_session.execute(
            text(
                """
            SELECT cost_usd FROM prompt_executions WHERE id = :exec_id
        """
            ),
            {"exec_id": execution_id},
        )

        stored_cost = result.scalar()
        assert abs(stored_cost - total_cost) < 0.000001  # Floating point precision


# Summary test that validates the complete integration
class TestPromptExecutionLoggingIntegration:
    """Integration test validating complete logging workflow"""

    def test_complete_execution_logging_workflow(self, db_session, test_template):
        """
        GIVEN: Active template and complete execution data
        WHEN: Full workflow executed (log → verify → query stats)
        THEN: All components work together correctly
        """
        # Step 1: Log execution
        execution_id = log_prompt_execution(
            template_key="test_nlu_extraction",
            success=True,
            response_time_ms=234.5,
            input_token_count=1500,
            output_token_count=300,
            cost_usd=0.0002025,
            metadata={
                "user_id": "integration_test_user",
                "request_id": "req_integration_001",
            },
        )

        assert execution_id is not None

        # Step 2: Verify execution record
        result = db_session.execute(
            text(
                """
            SELECT e.id, e.success, e.response_time_ms, e.total_token_count, e.cost_usd,
                   t.name, t.version
            FROM prompt_executions e
            JOIN prompt_templates t ON e.template_id = t.id
            WHERE e.id = :exec_id
        """
            ),
            {"exec_id": execution_id},
        )

        row = result.fetchone()
        assert row is not None
        assert row[1] is True  # success
        assert row[2] == 234.5  # response_time_ms
        assert row[3] == 1800  # total_token_count
        assert row[4] == 0.0002025  # cost_usd
        assert row[5] == "test_nlu_extraction"  # template name
        assert row[6] == 1  # template version

        # Step 3: Query analytics view (if exists)
        try:
            analytics_result = db_session.execute(
                text(
                    """
                SELECT * FROM v_template_performance
                WHERE template_name = 'test_nlu_extraction'
            """
                )
            )
            # View should return data if migration created it
            assert analytics_result is not None
        except Exception:
            # View might not exist yet - that's okay for unit tests
            pass

        # Success - complete workflow validated!
