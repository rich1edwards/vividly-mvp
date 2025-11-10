"""
Unit tests for structured logging module.

Tests cover:
- JSON formatting for production
- Development formatting with colors
- Context variable management
- Logger creation and configuration
- Decorator functionality
- Error handling and edge cases

Following Andrew Ng's "Test everything" principle - comprehensive coverage.
"""
import json
import logging
import pytest
from typing import Any, Dict
from unittest.mock import patch, MagicMock
from io import StringIO

# Import the module under test
from app.core.logging import (
    StructuredFormatter,
    DevelopmentFormatter,
    setup_logging,
    get_logger,
    set_request_context,
    clear_request_context,
    log_with_context,
    log_execution,
    request_id_var,
    user_id_var,
    correlation_id_var,
)


class TestStructuredFormatter:
    """Test suite for StructuredFormatter (JSON formatting)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = StructuredFormatter()
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)

    def teardown_method(self):
        """Clean up after each test."""
        clear_request_context()
        # Clear handlers
        self.logger.handlers = []

    def test_format_basic_log_entry(self):
        """Test basic log entry formatting as JSON."""
        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test.py",
            42,
            "Test message",
            (),
            None,
        )

        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        assert log_entry["severity"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert log_entry["logger"] == "test_logger"
        assert log_entry["line"] == 42
        assert "timestamp" in log_entry

    def test_format_includes_environment_metadata(self):
        """Test that environment metadata is included."""
        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test.py",
            10,
            "Test",
            (),
            None,
        )

        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        assert "environment" in log_entry
        assert "service" in log_entry
        assert "version" in log_entry

    def test_format_with_request_context(self):
        """Test that request context is included in logs."""
        set_request_context(
            request_id="req_123", user_id="user_456", correlation_id="corr_789"
        )

        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test.py",
            10,
            "Test",
            (),
            None,
        )

        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        assert log_entry["request_id"] == "req_123"
        assert log_entry["user_id"] == "user_456"
        assert log_entry["correlation_id"] == "corr_789"

    def test_format_with_exception(self):
        """Test that exception info is properly formatted."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            # Capture exc_info inside the except block
            exc_info = sys.exc_info()
            record = self.logger.makeRecord(
                "test_logger",
                logging.ERROR,
                "test.py",
                10,
                "Error occurred",
                (),
                exc_info=exc_info,
            )

        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        assert "exception" in log_entry
        assert log_entry["exception"]["type"] == "ValueError"
        assert log_entry["exception"]["message"] == "Test error"
        assert "traceback" in log_entry["exception"]

    def test_format_with_extra_fields(self):
        """Test that extra fields are included in log entry."""
        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test.py",
            10,
            "Test",
            (),
            None,
        )
        record.extra_fields = {"custom_field": "custom_value", "count": 42}

        formatted = self.formatter.format(record)
        log_entry = json.loads(formatted)

        assert log_entry["custom_field"] == "custom_value"
        assert log_entry["count"] == 42


class TestDevelopmentFormatter:
    """Test suite for DevelopmentFormatter (human-readable formatting)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = DevelopmentFormatter()
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)

    def teardown_method(self):
        """Clean up after each test."""
        clear_request_context()
        self.logger.handlers = []

    def test_format_includes_color_codes(self):
        """Test that color codes are included for different log levels."""
        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test.py",
            10,
            "Test",
            (),
            None,
        )

        formatted = self.formatter.format(record)

        # Should contain ANSI color codes
        assert "\033[" in formatted

    def test_format_includes_context_metadata(self):
        """Test that context metadata is included."""
        set_request_context(request_id="req_123", user_id="user_456")

        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test.py",
            10,
            "Test",
            (),
            None,
        )

        formatted = self.formatter.format(record)

        assert "request_id=req_123" in formatted
        assert "user_id=user_456" in formatted

    def test_format_includes_location_info(self):
        """Test that file location info is included."""
        record = self.logger.makeRecord(
            "test_logger",
            logging.INFO,
            "test_module",
            42,
            "Test",
            (),
            None,
        )
        record.funcName = "test_function"

        formatted = self.formatter.format(record)

        assert "(test_module:test_function:42)" in formatted


class TestLoggingSetup:
    """Test suite for logging setup and configuration."""

    def teardown_method(self):
        """Clean up after each test."""
        # Reset root logger
        root_logger = logging.getLogger()
        root_logger.handlers = []

    def test_setup_logging_default_configuration(self):
        """Test default logging configuration."""
        setup_logging()

        root_logger = logging.getLogger()

        assert len(root_logger.handlers) > 0
        assert root_logger.level == logging.INFO

    def test_setup_logging_custom_log_level(self):
        """Test custom log level configuration."""
        setup_logging(log_level="DEBUG")

        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG

    def test_setup_logging_force_json_formatting(self):
        """Test forcing JSON formatting."""
        setup_logging(force_json=True)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        assert isinstance(handler.formatter, StructuredFormatter)

    @patch("app.core.logging.settings")
    def test_setup_logging_production_uses_json(self, mock_settings):
        """Test that production environment uses JSON formatting."""
        mock_settings.ENVIRONMENT = "production"
        mock_settings.LOG_LEVEL = "INFO"

        setup_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        assert isinstance(handler.formatter, StructuredFormatter)

    def test_get_logger_returns_logger_instance(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger(__name__)

        assert isinstance(logger, logging.Logger)
        assert logger.name == __name__


class TestRequestContext:
    """Test suite for request context management."""

    def teardown_method(self):
        """Clean up after each test."""
        clear_request_context()

    def test_set_request_context_sets_all_fields(self):
        """Test setting all context fields."""
        set_request_context(
            request_id="req_123", user_id="user_456", correlation_id="corr_789"
        )

        assert request_id_var.get() == "req_123"
        assert user_id_var.get() == "user_456"
        assert correlation_id_var.get() == "corr_789"

    def test_set_request_context_partial_fields(self):
        """Test setting only some context fields."""
        set_request_context(request_id="req_123")

        assert request_id_var.get() == "req_123"
        assert user_id_var.get() is None
        assert correlation_id_var.get() is None

    def test_clear_request_context_clears_all_fields(self):
        """Test clearing all context fields."""
        set_request_context(
            request_id="req_123", user_id="user_456", correlation_id="corr_789"
        )

        clear_request_context()

        assert request_id_var.get() is None
        assert user_id_var.get() is None
        assert correlation_id_var.get() is None


class TestLogWithContext:
    """Test suite for log_with_context function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_logger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []

        # Add a handler to capture logs
        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

    def teardown_method(self):
        """Clean up after each test."""
        self.logger.handlers = []

    def test_log_with_context_adds_extra_fields(self):
        """Test that log_with_context adds extra fields."""
        log_with_context(
            self.logger, "INFO", "Test message", user_id="user_123", action="login"
        )

        self.stream.seek(0)
        log_output = self.stream.read()
        log_entry = json.loads(log_output)

        assert log_entry["message"] == "Test message"
        assert log_entry["user_id"] == "user_123"
        assert log_entry["action"] == "login"

    def test_log_with_context_respects_log_level(self):
        """Test that log level is respected."""
        # Set a higher threshold on the handler
        self.logger.handlers[0].setLevel(logging.WARNING)

        log_with_context(self.logger, "DEBUG", "Debug message")

        self.stream.seek(0)
        log_output = self.stream.read().strip()

        # Should be empty because DEBUG < WARNING and handler filters it
        assert log_output == ""


class TestLogExecutionDecorator:
    """Test suite for log_execution decorator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_logger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []

        # Add a handler to capture logs
        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

    def teardown_method(self):
        """Clean up after each test."""
        self.logger.handlers = []

    def test_decorator_logs_function_execution(self):
        """Test that decorator logs function start and completion."""

        @log_execution(self.logger, level="INFO")
        def test_function():
            return "result"

        result = test_function()

        assert result == "result"

        self.stream.seek(0)
        log_lines = self.stream.read().strip().split("\n")

        # Should have 2 log entries (start and complete)
        assert len(log_lines) == 2

        start_log = json.loads(log_lines[0])
        complete_log = json.loads(log_lines[1])

        assert "Starting execution" in start_log["message"]
        assert "Completed execution" in complete_log["message"]
        assert complete_log["status"] == "success"
        assert "duration_ms" in complete_log

    def test_decorator_logs_function_errors(self):
        """Test that decorator logs function errors."""

        @log_execution(self.logger, level="INFO")
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_function()

        self.stream.seek(0)
        log_lines = self.stream.read().strip().split("\n")

        # Should have 2 log entries (start and error)
        assert len(log_lines) == 2

        error_log = json.loads(log_lines[1])

        assert "Failed execution" in error_log["message"]
        assert error_log["status"] == "error"
        assert error_log["error_type"] == "ValueError"
        assert error_log["error_message"] == "Test error"

    @pytest.mark.asyncio
    async def test_decorator_works_with_async_functions(self):
        """Test that decorator works with async functions."""

        @log_execution(self.logger, level="INFO")
        async def async_function():
            return "async_result"

        result = await async_function()

        assert result == "async_result"

        self.stream.seek(0)
        log_lines = self.stream.read().strip().split("\n")

        # Should have 2 log entries (start and complete)
        assert len(log_lines) == 2

        complete_log = json.loads(log_lines[1])
        assert complete_log["status"] == "success"


class TestIntegration:
    """Integration tests for the logging system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_logger("integration_test")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []

        # Add a handler to capture logs
        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)

    def teardown_method(self):
        """Clean up after each test."""
        clear_request_context()
        self.logger.handlers = []

    def test_end_to_end_logging_with_context(self):
        """Test end-to-end logging with request context."""
        # Set request context
        set_request_context(
            request_id="req_integration_test", user_id="user_integration_test"
        )

        # Log a message
        self.logger.info("Integration test message")

        # Get output
        self.stream.seek(0)
        log_entry = json.loads(self.stream.read().strip())

        # Verify all expected fields are present
        assert log_entry["message"] == "Integration test message"
        assert log_entry["request_id"] == "req_integration_test"
        assert log_entry["user_id"] == "user_integration_test"
        assert log_entry["severity"] == "INFO"
        assert "timestamp" in log_entry
        assert "environment" in log_entry

    def test_logging_across_multiple_contexts(self):
        """Test that context changes affect subsequent logs."""
        # First context
        set_request_context(request_id="req_1")
        self.logger.info("Message 1")

        # Second context
        clear_request_context()
        set_request_context(request_id="req_2")
        self.logger.info("Message 2")

        # Get output
        self.stream.seek(0)
        log_lines = self.stream.read().strip().split("\n")

        log1 = json.loads(log_lines[0])
        log2 = json.loads(log_lines[1])

        assert log1["request_id"] == "req_1"
        assert log2["request_id"] == "req_2"


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
