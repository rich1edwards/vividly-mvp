"""
Request Context Middleware for Structured Logging and Metrics.

Automatically injects request_id, user_id, and correlation_id into logging context
for all requests, enabling end-to-end request tracking across the application.

Also captures HTTP request metrics (count and duration) for observability in GCP.

Following Andrew Ng's "Build it right" principle - production-ready from day one.
"""
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.logging import set_request_context, clear_request_context, get_logger
from app.core.metrics import get_metrics_client

logger = get_logger(__name__)
metrics = get_metrics_client()


class LoggingContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically sets logging context for all requests.

    Features:
    - Generates unique request_id for each request
    - Extracts user_id from authentication (if available)
    - Propagates correlation_id from headers (for distributed tracing)
    - Cleans up context after request completion
    - Logs request start and completion with timing

    This ensures all logs within a request are automatically enriched with
    contextual metadata, making debugging and monitoring much easier.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and set up logging context."""
        # Capture start time for metrics
        start_time = time.time()

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Get correlation ID from headers (for distributed tracing)
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = request.headers.get("X-Request-ID", request_id)

        # Extract user_id from request state (set by authentication middleware)
        user_id = None
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "id"):
                user_id = str(user.id)

        # Set logging context for this request
        set_request_context(
            request_id=request_id,
            user_id=user_id,
            correlation_id=correlation_id
        )

        # Log request start
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate request duration
            duration_seconds = time.time() - start_time

            # Log request completion
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_seconds": duration_seconds,
                    }
                }
            )

            # Record metrics to GCP Cloud Monitoring
            metrics.increment_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            )
            metrics.record_request_duration(
                method=request.method,
                endpoint=request.url.path,
                duration_seconds=duration_seconds
            )

            # Add request_id to response headers for client-side tracking
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate request duration even for errors
            duration_seconds = time.time() - start_time

            # Log request error
            logger.error(
                f"{request.method} {request.url.path} - ERROR",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "duration_seconds": duration_seconds,
                    }
                }
            )

            # Record error metrics (status_code 500 for unhandled exceptions)
            metrics.increment_http_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            )
            metrics.record_request_duration(
                method=request.method,
                endpoint=request.url.path,
                duration_seconds=duration_seconds
            )

            raise

        finally:
            # Clean up context
            clear_request_context()
