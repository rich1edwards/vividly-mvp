"""
Rate Limiting Middleware

Implements token bucket algorithm for API rate limiting using Redis.
Prevents abuse and ensures fair resource allocation.

Includes metrics tracking for Sprint 2 observability requirements.
"""

import os
import time
from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
import redis
from functools import wraps

from app.core.metrics import get_metrics_client
from app.core.logging import get_logger

logger = get_logger(__name__)
metrics = get_metrics_client()


class RateLimiter:
    """
    Token bucket rate limiter using Redis.

    Features:
    - Per-user rate limiting
    - Per-IP rate limiting (for anonymous endpoints)
    - Per-endpoint custom limits
    - Sliding window algorithm
    """

    def __init__(self, redis_client: redis.Redis):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    def check_rate_limit(
        self, identifier: str, limit: int, window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (user_id or IP)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed: bool, info: dict)
            info contains: remaining, reset_at
        """
        key = f"rate_limit:{identifier}"
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Use Redis sorted set with timestamps as scores
        # Remove old requests outside the window
        self.redis.zremrangebyscore(key, 0, window_start.timestamp())

        # Count requests in current window
        current_count = self.redis.zcard(key)

        if current_count >= limit:
            # Rate limit exceeded
            # Get the oldest timestamp to calculate reset time
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_at = datetime.fromtimestamp(oldest[0][1]) + timedelta(
                    seconds=window_seconds
                )
            else:
                reset_at = now + timedelta(seconds=window_seconds)

            return False, {
                "remaining": 0,
                "reset_at": reset_at.isoformat(),
                "retry_after": int((reset_at - now).total_seconds()),
            }

        # Add current request
        self.redis.zadd(key, {str(now.timestamp()): now.timestamp()})

        # Set expiration to prevent memory leaks
        self.redis.expire(key, window_seconds)

        # Calculate remaining requests
        remaining = limit - (current_count + 1)

        return True, {
            "remaining": remaining,
            "reset_at": (now + timedelta(seconds=window_seconds)).isoformat(),
            "retry_after": 0,
        }

    async def check_request(
        self, request: Request, identifier: str, limit: int, window_seconds: int
    ):
        """
        Check rate limit and raise exception if exceeded.

        Args:
            request: FastAPI request
            identifier: Unique identifier
            limit: Request limit
            window_seconds: Time window

        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        is_allowed, info = self.check_rate_limit(identifier, limit, window_seconds)

        # Add rate limit headers to response
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": info["reset_at"],
        }

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {info['retry_after']} seconds.",
                headers={
                    "Retry-After": str(info["retry_after"]),
                    **request.state.rate_limit_headers,
                },
            )


# ============================================================================
# Rate Limit Configurations
# ============================================================================

# Content request limits (most expensive operation)
CONTENT_REQUEST_RATE_LIMIT = int(os.getenv("CONTENT_REQUEST_RATE_LIMIT", "10"))
CONTENT_REQUEST_WINDOW = 3600  # 1 hour

# General API limits
API_RATE_LIMIT_PER_MINUTE = 60
API_RATE_LIMIT_PER_HOUR = 1000

# Authentication limits (stricter to prevent brute force)
AUTH_RATE_LIMIT = 5
AUTH_WINDOW = 900  # 15 minutes


# ============================================================================
# Rate Limiting Decorators
# ============================================================================


def rate_limit(
    limit: int, window_seconds: int, identifier_fn: Optional[callable] = None
):
    """
    Decorator for rate limiting endpoints.

    Args:
        limit: Maximum requests allowed
        window_seconds: Time window in seconds
        identifier_fn: Optional function to extract identifier from request
                      Default: uses user_id if authenticated, else IP

    Usage:
        @rate_limit(limit=10, window_seconds=3600)
        async def expensive_endpoint(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # Try kwargs
                request = kwargs.get("request")

            if not request:
                raise ValueError("Request object not found in endpoint arguments")

            # Get Redis client (assumes it's available in app state)
            redis_client = request.app.state.redis

            # Determine identifier
            if identifier_fn:
                identifier = identifier_fn(request)
            else:
                # Default: use user_id if authenticated, else IP
                user = getattr(request.state, "user", None)
                if user:
                    identifier = f"user:{user.id}"
                else:
                    from app.middleware.auth import get_client_ip

                    identifier = f"ip:{get_client_ip(request)}"

            # Create rate limiter
            limiter = RateLimiter(redis_client)

            # Check rate limit
            await limiter.check_request(request, identifier, limit, window_seconds)

            # Execute endpoint
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# FastAPI Middleware
# ============================================================================


async def rate_limit_middleware(request: Request, call_next):
    """
    Global rate limiting middleware.

    Applies general API rate limits to all requests.
    Individual endpoints can have stricter limits using decorators.

    Includes metrics tracking for Sprint 2 observability.
    """
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/api/v1/health"]:
        return await call_next(request)

    # Capture start time for middleware latency metrics
    start_time = time.time()

    redis_client = request.app.state.redis

    # Determine identifier
    user = getattr(request.state, "user", None)
    if user:
        identifier = f"user:{user.id}"
    else:
        from app.middleware.auth import get_client_ip

        identifier = f"ip:{get_client_ip(request)}"

    # Extract IP for metrics
    from app.middleware.auth import get_client_ip
    ip_address = get_client_ip(request)

    # Apply per-minute limit
    limiter = RateLimiter(redis_client)

    try:
        # Record rate limit hit metric
        metrics.increment_rate_limit_hits(
            endpoint=request.url.path,
            ip_address=ip_address
        )

        await limiter.check_request(
            request, f"{identifier}:minute", API_RATE_LIMIT_PER_MINUTE, 60
        )

        # Apply per-hour limit
        await limiter.check_request(
            request, f"{identifier}:hour", API_RATE_LIMIT_PER_HOUR, 3600
        )

    except HTTPException as e:
        # Record rate limit exceeded metric
        metrics.increment_rate_limit_exceeded(
            endpoint=request.url.path,
            ip_address=ip_address
        )

        # Record middleware latency even for rate limited requests
        latency_ms = (time.time() - start_time) * 1000
        metrics.record_rate_limit_middleware_latency(
            endpoint=request.url.path,
            latency_ms=latency_ms
        )

        # Return rate limit error
        return JSONResponse(
            status_code=e.status_code, content={"detail": e.detail}, headers=e.headers
        )

    # Record middleware latency
    latency_ms = (time.time() - start_time) * 1000
    metrics.record_rate_limit_middleware_latency(
        endpoint=request.url.path,
        latency_ms=latency_ms
    )

    # Process request
    response = await call_next(request)

    # Add rate limit headers if available
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value

    return response


# ============================================================================
# Specific Rate Limiters
# ============================================================================


async def check_content_request_rate_limit(user_id: str, redis_client):
    """
    Check rate limit for content requests.

    Args:
        user_id: User identifier
        redis_client: Redis client

    Raises:
        HTTPException: If rate limit exceeded
    """
    limiter = RateLimiter(redis_client)
    identifier = f"user:{user_id}:content_requests"

    is_allowed, info = limiter.check_rate_limit(
        identifier, CONTENT_REQUEST_RATE_LIMIT, CONTENT_REQUEST_WINDOW
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Content request limit exceeded ({CONTENT_REQUEST_RATE_LIMIT} per hour). "
            f"Try again in {info['retry_after']} seconds.",
            headers={
                "Retry-After": str(info["retry_after"]),
                "X-RateLimit-Limit": str(CONTENT_REQUEST_RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": info["reset_at"],
            },
        )


async def check_auth_rate_limit(identifier: str, redis_client):
    """
    Check rate limit for authentication attempts.

    Stricter limits to prevent brute force attacks.

    Args:
        identifier: Email or IP address
        redis_client: Redis client

    Raises:
        HTTPException: If rate limit exceeded
    """
    limiter = RateLimiter(redis_client)

    is_allowed, info = limiter.check_rate_limit(
        f"auth:{identifier}", AUTH_RATE_LIMIT, AUTH_WINDOW
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts. Try again in {info['retry_after']} seconds.",
            headers={"Retry-After": str(info["retry_after"])},
        )


# ============================================================================
# Example Usage
# ============================================================================

"""
# Using decorator for specific endpoint rate limit
@app.post("/api/v1/students/content/request")
@rate_limit(limit=10, window_seconds=3600)  # 10 requests per hour
async def request_content(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    # Create content request
    ...


# Using function for manual rate limit check
@app.post("/api/v1/students/content/request")
async def request_content(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    # Check rate limit
    redis_client = request.app.state.redis
    await check_content_request_rate_limit(current_user.id, redis_client)

    # Create content request
    ...


# Custom identifier function
def get_org_identifier(request: Request) -> str:
    user = request.state.user
    return f"org:{user.org_id}"

@app.get("/api/v1/admin/export")
@rate_limit(limit=5, window_seconds=3600, identifier_fn=get_org_identifier)
async def export_data(request: Request):
    # Rate limited per organization
    ...
"""
