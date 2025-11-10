"""
Rate Limiting Configuration

Implements rate limiting for the Vividly API to protect against brute force attacks
and abuse.

Following Andrew Ng's Methodology:
- Build it right: Industry-standard rate limiting with slowapi
- Test everything: Comprehensive test coverage in tests/test_rate_limit.py
- Think about the future: Design supports easy upgrade to Redis-backed solution

Sprint 2: Rate Limiting & Security Implementation
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
# Uses in-memory storage by default (suitable for single-instance deployments)
# Can be upgraded to Redis-backed storage for distributed deployments
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Global default
    storage_uri="memory://",
    strategy="fixed-window",  # Simple and predictable
    headers_enabled=True,  # Include rate limit headers in responses
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with rate limit information.
    Following security best practices:
    - Clear error messages for legitimate users
    - Includes retry information
    - Logs attempts for monitoring
    """
    logger.warning(
        f"Rate limit exceeded for {request.client.host if request.client else 'unknown'} "
        f"on {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": str(exc.detail).split(" ")[3]
            if " " in str(exc.detail)
            else "60",
        },
        headers={
            "Retry-After": str(exc.detail).split(" ")[3]
            if " " in str(exc.detail)
            else "60",
        },
    )


# Rate limit configurations for different endpoint types
# Following OWASP recommendations and industry best practices

# Authentication endpoints - Most restrictive
AUTH_REGISTER_LIMIT = "5/hour"  # Prevent account enumeration and spam
AUTH_LOGIN_LIMIT = "10/minute"  # Prevent brute force attacks
AUTH_REFRESH_LIMIT = "30/minute"  # Prevent token abuse
AUTH_PASSWORD_RESET_REQUEST_LIMIT = "3/hour"  # Prevent email bombing
AUTH_PASSWORD_RESET_CONFIRM_LIMIT = "5/hour"  # Prevent token guessing

# Content generation endpoints - Moderate restrictions
CONTENT_GENERATE_LIMIT = "20/minute"  # Balance UX and abuse prevention
CONTENT_STATUS_LIMIT = "60/minute"  # Higher limit for status checks

# General API endpoints - Less restrictive
API_READ_LIMIT = "100/minute"  # Generous limit for read operations
API_WRITE_LIMIT = "30/minute"  # More restrictive for write operations


def get_rate_limit_config(endpoint_type: str) -> str:
    """
    Get rate limit configuration for specific endpoint type.

    Args:
        endpoint_type: Type of endpoint (e.g., 'auth_login', 'content_generate')

    Returns:
        Rate limit string (e.g., '10/minute')

    Following the principle: Different endpoints have different security requirements.
    """
    config_map = {
        "auth_register": AUTH_REGISTER_LIMIT,
        "auth_login": AUTH_LOGIN_LIMIT,
        "auth_refresh": AUTH_REFRESH_LIMIT,
        "auth_password_reset_request": AUTH_PASSWORD_RESET_REQUEST_LIMIT,
        "auth_password_reset_confirm": AUTH_PASSWORD_RESET_CONFIRM_LIMIT,
        "content_generate": CONTENT_GENERATE_LIMIT,
        "content_status": CONTENT_STATUS_LIMIT,
        "api_read": API_READ_LIMIT,
        "api_write": API_WRITE_LIMIT,
    }

    return config_map.get(endpoint_type, "100/minute")  # Default fallback


# Future Enhancement: Redis-backed rate limiting
# When scaling to multiple instances, update storage_uri to:
# storage_uri = "redis://host:port"
#
# This will enable distributed rate limiting across all instances
# while maintaining the same API and behavior.
#
# Migration steps:
# 1. Set up Redis instance (Cloud Memorystore on GCP)
# 2. Update storage_uri in limiter initialization
# 3. No code changes needed - drop-in replacement
# 4. Test thoroughly before deploying to production
