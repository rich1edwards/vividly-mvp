"""
Middleware Package

Security and utility middleware for the Vividly API.
"""
from app.middleware.security import (
    SecurityHeadersMiddleware,
    BruteForceProtectionMiddleware,
    RateLimitMiddleware,
)
from app.middleware.authorization import (
    AuthorizationMiddleware,
    require_role,
    check_resource_ownership,
    check_class_ownership,
)

__all__ = [
    "SecurityHeadersMiddleware",
    "BruteForceProtectionMiddleware",
    "RateLimitMiddleware",
    "AuthorizationMiddleware",
    "require_role",
    "check_resource_ownership",
    "check_class_ownership",
]
