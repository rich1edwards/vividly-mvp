"""
Structured logging module for Vividly backend.

This module provides production-ready structured logging with:
- JSON formatting for production
- Contextual logging (request_id, user_id, correlation_id)
- GCP Cloud Logging integration
- Environment-aware configuration

Following Andrew Ng's "Build it right" principle - production-ready from day one.
"""
import logging
import json
import sys
import traceback
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from contextvars import ContextVar
from functools import wraps

from app.core.config import settings

# Context variables for request-scoped logging
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format suitable for GCP Cloud Logging and local development.
    Includes contextual metadata from context variables.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with contextual metadata."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add environment metadata
        log_entry["environment"] = settings.ENVIRONMENT
        log_entry["service"] = settings.APP_NAME
        log_entry["version"] = settings.APP_VERSION

        # Add contextual metadata from context variables
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_entry["user_id"] = user_id

        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info and record.exc_info != True:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }
        elif record.exc_info == True:
            # exc_info=True means use sys.exc_info()
            import sys

            exc_info = sys.exc_info()
            if exc_info[0] is not None:
                log_entry["exception"] = {
                    "type": exc_info[0].__name__,
                    "message": str(exc_info[1]),
                    "traceback": traceback.format_exception(*exc_info),
                }

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development.

    Provides colored output with contextual metadata for local development.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and contextual metadata."""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Format base message
        message = f"{color}[{record.levelname}]{reset} {timestamp} - {record.name} - {record.getMessage()}"

        # Add contextual metadata
        context_parts = []

        request_id = request_id_var.get()
        if request_id:
            context_parts.append(f"request_id={request_id}")

        user_id = user_id_var.get()
        if user_id:
            context_parts.append(f"user_id={user_id}")

        correlation_id = correlation_id_var.get()
        if correlation_id:
            context_parts.append(f"correlation_id={correlation_id}")

        if context_parts:
            message += f" [{', '.join(context_parts)}]"

        # Add location info
        message += f" ({record.module}:{record.funcName}:{record.lineno})"

        # Add exception info if present
        if record.exc_info:
            message += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return message


def setup_logging(
    log_level: Optional[str] = None,
    force_json: bool = False,
) -> None:
    """
    Configure application logging.

    Sets up structured logging for the application with environment-aware formatting.

    Args:
        log_level: Override log level (defaults to settings.LOG_LEVEL)
        force_json: Force JSON formatting even in development

    Examples:
        # Default configuration (from environment)
        setup_logging()

        # Override log level
        setup_logging(log_level="DEBUG")

        # Force JSON formatting for testing
        setup_logging(force_json=True)
    """
    level = log_level or settings.LOG_LEVEL
    level_obj = getattr(logging, level.upper(), logging.INFO)

    # Determine formatter based on environment
    use_json = force_json or settings.ENVIRONMENT in ("production", "staging")

    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = DevelopmentFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level_obj)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_obj)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("slowapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Examples:
        logger = get_logger(__name__)
        logger.info("Application started")
        logger.error("Something went wrong", extra_fields={"user_id": "123"})
    """
    return logging.getLogger(name)


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Set contextual metadata for request-scoped logging.

    This should be called at the beginning of each request to add
    contextual metadata to all logs within the request scope.

    Args:
        request_id: Unique request identifier
        user_id: User identifier (if authenticated)
        correlation_id: Correlation ID for distributed tracing

    Examples:
        # In middleware
        set_request_context(
            request_id=str(uuid.uuid4()),
            user_id=current_user.id if current_user else None,
            correlation_id=request.headers.get("X-Correlation-ID")
        )
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if correlation_id:
        correlation_id_var.set(correlation_id)


def clear_request_context() -> None:
    """
    Clear contextual metadata after request completion.

    This should be called at the end of each request to clean up
    context variables.

    Examples:
        # In middleware finally block
        clear_request_context()
    """
    request_id_var.set(None)
    user_id_var.set(None)
    correlation_id_var.set(None)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields: Any,
) -> None:
    """
    Log a message with additional contextual fields.

    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **extra_fields: Additional fields to include in log entry

    Examples:
        log_with_context(
            logger,
            "INFO",
            "User login successful",
            user_id="user_123",
            ip_address="192.168.1.1",
            login_method="email"
        )
    """
    log_func = getattr(logger, level.lower(), logger.info)

    # Create log record with extra fields
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper(), logging.INFO),
        "(unknown file)",
        0,
        message,
        (),
        None,
    )
    record.extra_fields = extra_fields

    logger.handle(record)


# Decorator for function-level logging
def log_execution(logger: logging.Logger, level: str = "DEBUG"):
    """
    Decorator to log function execution with timing.

    Args:
        logger: Logger instance
        level: Log level for execution logs

    Examples:
        @log_execution(logger, level="INFO")
        def process_payment(amount: float):
            # Process payment logic
            pass
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            func_name = f"{func.__module__}.{func.__name__}"

            log_with_context(
                logger,
                level,
                f"Starting execution: {func_name}",
                function=func_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                result = await func(*args, **kwargs)
                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                log_with_context(
                    logger,
                    level,
                    f"Completed execution: {func_name}",
                    function=func_name,
                    duration_ms=duration_ms,
                    status="success",
                )

                return result
            except Exception as e:
                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                log_with_context(
                    logger,
                    "ERROR",
                    f"Failed execution: {func_name}",
                    function=func_name,
                    duration_ms=duration_ms,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            func_name = f"{func.__module__}.{func.__name__}"

            log_with_context(
                logger,
                level,
                f"Starting execution: {func_name}",
                function=func_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                log_with_context(
                    logger,
                    level,
                    f"Completed execution: {func_name}",
                    function=func_name,
                    duration_ms=duration_ms,
                    status="success",
                )

                return result
            except Exception as e:
                duration_ms = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds() * 1000

                log_with_context(
                    logger,
                    "ERROR",
                    f"Failed execution: {func_name}",
                    function=func_name,
                    duration_ms=duration_ms,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )

                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Initialize logging on module import
# This ensures logging is configured before any other module imports
if not logging.getLogger().handlers:
    setup_logging()
