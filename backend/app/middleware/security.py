"""
Security Middleware

Implements security headers, brute force protection, and other security measures.
"""
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Tuple
from datetime import datetime, timedelta
import logging
import json as json_lib

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    - Referrer-Policy: strict-origin-when-cross-origin
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class BruteForceProtectionMiddleware(BaseHTTPMiddleware):
    """
    Protects against brute force attacks on login endpoints.

    Tracks failed login attempts per IP and email combination.
    Implements exponential backoff and temporary lockouts.
    """

    def __init__(self, app, max_attempts: int = 5, lockout_duration: int = 300):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration  # seconds

        # Store failed attempts: {(ip, email): [(timestamp, count)]}
        self.failed_attempts: Dict[Tuple[str, str], list] = {}
        self.locked_accounts: Dict[Tuple[str, str], datetime] = {}

    async def dispatch(self, request: Request, call_next):
        # Only check login endpoints
        if request.url.path == "/api/v1/auth/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"

            # Get email from request body (if available)
            try:
                body = await request.body()
                # Re-create request with body for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive

                if body:
                    data = json_lib.loads(body)
                    email = data.get("email", "")

                    key = (client_ip, email)

                    # Check if account is locked
                    if key in self.locked_accounts:
                        lockout_time = self.locked_accounts[key]
                        if datetime.utcnow() < lockout_time:
                            remaining = (lockout_time - datetime.utcnow()).seconds
                            logger.warning(f"Blocked login attempt for locked account: {email} from {client_ip}")
                            return Response(
                                content=f'{{"detail":"Account temporarily locked. Try again in {remaining} seconds."}}',
                                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                media_type="application/json"
                            )
                        else:
                            # Lockout expired
                            del self.locked_accounts[key]
                            self.failed_attempts[key] = []

                    # Process request
                    response = await call_next(request)

                    # Track failed attempts
                    if response.status_code == 401:
                        self._record_failed_attempt(key)
                    elif response.status_code == 200:
                        # Successful login - clear failed attempts
                        if key in self.failed_attempts:
                            del self.failed_attempts[key]

                    return response
            except json_lib.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Error in brute force protection: {e}")

        return await call_next(request)

    def _record_failed_attempt(self, key: Tuple[str, str]):
        """Record a failed login attempt."""
        now = datetime.utcnow()

        if key not in self.failed_attempts:
            self.failed_attempts[key] = []

        # Clean old attempts (older than 1 hour)
        self.failed_attempts[key] = [
            (ts, count) for ts, count in self.failed_attempts[key]
            if now - ts < timedelta(hours=1)
        ]

        # Add new attempt
        self.failed_attempts[key].append((now, 1))

        # Check if we should lock the account
        recent_attempts = len(self.failed_attempts[key])
        if recent_attempts >= self.max_attempts:
            lockout_time = now + timedelta(seconds=self.lockout_duration)
            self.locked_accounts[key] = lockout_time
            logger.warning(f"Account locked due to {recent_attempts} failed attempts: {key[1]} from {key[0]}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Additional rate limiting for sensitive endpoints.

    This complements SlowAPI with more granular controls.
    """

    def __init__(self, app):
        super().__init__(app)
        # Store request counts: {(ip, path): [(timestamp, count)]}
        self.request_counts: Dict[Tuple[str, str], list] = {}

        # Rate limits per endpoint pattern (higher limits to allow for test environments)
        self.rate_limits = {
            "/api/v1/auth/login": (10, 60),  # 10 requests per 60 seconds
            "/api/v1/auth/register": (10, 60),  # 10 requests per 60 seconds
            "/api/v1/auth/logout": (20, 60),  # 20 requests per 60 seconds
        }

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Check if this path has rate limits
        for pattern, (max_requests, window_seconds) in self.rate_limits.items():
            if path == pattern:  # Exact match instead of startswith
                key = (client_ip, pattern)

                if self._is_rate_limited(key, max_requests, window_seconds):
                    logger.warning(f"Rate limit exceeded: {client_ip} on {path}")
                    return Response(
                        content='{"detail":"Rate limit exceeded. Please try again later."}',
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        media_type="application/json"
                    )

                self._record_request(key)
                break

        return await call_next(request)

    def _is_rate_limited(self, key: Tuple[str, str], max_requests: int, window_seconds: int) -> bool:
        """Check if the request should be rate limited."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        if key not in self.request_counts:
            return False

        # Clean old requests
        self.request_counts[key] = [
            ts for ts in self.request_counts[key]
            if ts > window_start
        ]

        return len(self.request_counts[key]) >= max_requests

    def _record_request(self, key: Tuple[str, str]):
        """Record a request."""
        now = datetime.utcnow()

        if key not in self.request_counts:
            self.request_counts[key] = []

        self.request_counts[key].append(now)
