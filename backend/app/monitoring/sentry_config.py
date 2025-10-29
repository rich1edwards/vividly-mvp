"""
Sentry Error Tracking Configuration

Integrates Sentry for error tracking, performance monitoring,
and real-time error notifications.
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry():
    """
    Initialize Sentry SDK with FastAPI integration.

    Environment Variables:
        SENTRY_DSN: Sentry Data Source Name
        ENVIRONMENT: Environment name (dev, staging, prod)
        SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0-1.0)
        SENTRY_PROFILES_SAMPLE_RATE: Profiling sample rate (0.0-1.0)
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")

    if not sentry_dsn:
        print("Warning: SENTRY_DSN not set. Error tracking disabled.")
        return

    # Configure sample rates based on environment
    if environment == "prod":
        traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
        profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))
    elif environment == "staging":
        traces_sample_rate = 0.5
        profiles_sample_rate = 0.5
    else:  # dev
        traces_sample_rate = 1.0
        profiles_sample_rate = 1.0

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,

        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                failed_request_status_codes=[500, 599],
            ),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=None,
                event_level=None
            ),
        ],

        # Performance Monitoring
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,

        # Additional options
        send_default_pii=False,
        attach_stacktrace=True,
        max_breadcrumbs=50,
        release=os.getenv("GIT_COMMIT_SHA", "unknown"),
        before_send=before_send_hook,
    )

    print(f"✓ Sentry initialized for environment: {environment}")


def before_send_hook(event, hint):
    """Filter events before sending to Sentry."""
    # Don't send events for health check endpoints
    if "request" in event and "url" in event["request"]:
        url = event["request"]["url"]
        if "/health" in url or "/metrics" in url:
            return None

    # Don't send 404 errors
    if "exception" in event:
        for exception in event["exception"].get("values", []):
            if "HTTPException" in exception.get("type", ""):
                if "404" in str(exception.get("value", "")):
                    return None

    # Scrub sensitive data
    if "request" in event:
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            if "Authorization" in headers:
                headers["Authorization"] = "[Filtered]"
            if "Cookie" in headers:
                headers["Cookie"] = "[Filtered]"

    return event


def capture_exception(exception: Exception, **kwargs):
    """Manually capture exception with additional context."""
    with sentry_sdk.push_scope() as scope:
        if "tags" in kwargs:
            for key, value in kwargs["tags"].items():
                scope.set_tag(key, value)

        if "extra" in kwargs:
            for key, value in kwargs["extra"].items():
                scope.set_extra(key, value)

        if "user" in kwargs:
            scope.set_user(kwargs["user"])

        if "level" in kwargs:
            scope.level = kwargs["level"]

        sentry_sdk.capture_exception(exception)


def set_user_context(user_id: str, email: str = None, username: str = None):
    """Set user context for error tracking."""
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **data):
    """Add breadcrumb for debugging."""
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data
    )


from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SentryMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically capture user context and breadcrumbs."""

    async def dispatch(self, request: Request, call_next):
        add_breadcrumb(
            message=f"{request.method} {request.url.path}",
            category="http",
            level="info",
            data={
                "method": request.method,
                "url": str(request.url),
            }
        )

        if hasattr(request.state, "user"):
            user = request.state.user
            set_user_context(
                user_id=str(user.id),
                email=user.email,
                username=user.name
            )

        response = await call_next(request)

        add_breadcrumb(
            message=f"Response {response.status_code}",
            category="http",
            level="info" if response.status_code < 400 else "warning",
            data={"status_code": response.status_code}
        )

        return response
