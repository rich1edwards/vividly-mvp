"""
Authorization Middleware

Implements role-based access control (RBAC) for API endpoints.
"""
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Set, Optional
import logging
import re

from app.models.user import UserRole

logger = logging.getLogger(__name__)


# Role hierarchy: admin > teacher > student
ROLE_HIERARCHY = {
    UserRole.ADMIN: 3,
    UserRole.TEACHER: 2,
    UserRole.STUDENT: 1,
}


# Endpoint permission mappings: {path_pattern: allowed_roles}
ENDPOINT_PERMISSIONS: Dict[str, Set[UserRole]] = {
    # Admin-only endpoints
    r"^/api/v1/admin/.*": {UserRole.ADMIN},

    # Teacher endpoints
    r"^/api/v1/teachers/.*": {UserRole.ADMIN, UserRole.TEACHER},
    r"^/api/v1/classes/.*": {UserRole.ADMIN, UserRole.TEACHER},

    # Student endpoints
    r"^/api/v1/students/.*": {UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT},
    r"^/api/v1/topics/.*": {UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT},
    r"^/api/v1/content/.*": {UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT},
    r"^/api/v1/cache/.*": {UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT},
    r"^/api/v1/nlu/.*": {UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT},

    # Public endpoints (no authentication required)
    r"^/health$": set(),  # Empty set = public
    r"^/api/docs.*": set(),
    r"^/api/redoc.*": set(),
    r"^/api/openapi.json$": set(),
    r"^/api/v1/auth/register$": set(),
    r"^/api/v1/auth/login$": set(),
}


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce role-based access control.

    Checks if the authenticated user has permission to access the requested endpoint
    based on their role.
    """

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Check if user has permission to access endpoint.

        Flow:
        1. Check if endpoint is public (no auth required)
        2. If not public, verify user is authenticated
        3. Check if user's role has permission for this endpoint
        4. Allow or deny access based on role
        """
        path = request.url.path
        method = request.method

        # Skip authorization for public endpoints
        if self._is_public_endpoint(path):
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            return await call_next(request)

        # Extract user from request state (set by authentication middleware)
        user = getattr(request.state, "user", None)

        if not user:
            # No authenticated user for protected endpoint
            logger.warning(f"Unauthorized access attempt to {path}")
            return Response(
                content='{"detail":"Authentication required"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )

        # Check if user's role has permission
        user_role = user.role
        allowed_roles = self._get_allowed_roles(path)

        if allowed_roles is None:
            # No specific permissions defined - allow by default (authenticated users)
            return await call_next(request)

        if user_role not in allowed_roles:
            # User role not permitted for this endpoint
            logger.warning(
                f"Authorization failed: {user.email} (role={user_role.value}) "
                f"attempted to access {path} (requires {[r.value for r in allowed_roles]})"
            )
            return Response(
                content='{"detail":"Insufficient permissions"}',
                status_code=status.HTTP_403_FORBIDDEN,
                media_type="application/json"
            )

        # Authorization successful
        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is public (no authentication required).

        Args:
            path: Request path

        Returns:
            True if endpoint is public, False otherwise
        """
        for pattern, allowed_roles in ENDPOINT_PERMISSIONS.items():
            if re.match(pattern, path):
                return len(allowed_roles) == 0  # Empty set = public

        return False

    def _get_allowed_roles(self, path: str) -> Optional[Set[UserRole]]:
        """
        Get allowed roles for an endpoint.

        Args:
            path: Request path

        Returns:
            Set of allowed roles, or None if no specific permissions defined
        """
        for pattern, allowed_roles in ENDPOINT_PERMISSIONS.items():
            if re.match(pattern, path):
                if len(allowed_roles) == 0:
                    # Public endpoint
                    return None
                return allowed_roles

        # No pattern matched - default to authenticated users only
        return None


def require_role(*allowed_roles: UserRole):
    """
    Decorator to require specific roles for an endpoint.

    This is a helper decorator that can be applied to individual endpoints
    for more fine-grained control beyond the middleware.

    Usage:
        @router.get("/admin/users")
        @require_role(UserRole.ADMIN)
        async def get_users():
            pass

    Args:
        allowed_roles: Roles allowed to access this endpoint
    """
    def decorator(func):
        # Store allowed roles in function metadata
        func._allowed_roles = set(allowed_roles)
        return func
    return decorator


def check_resource_ownership(user_id: str, resource_user_id: str) -> bool:
    """
    Check if user owns a resource.

    Helper function for BOLA/IDOR protection.

    Args:
        user_id: ID of requesting user
        resource_user_id: ID of user who owns the resource

    Returns:
        True if user owns resource, False otherwise
    """
    return user_id == resource_user_id


def check_class_ownership(db, user_id: str, class_id: str) -> bool:
    """
    Check if teacher owns a class.

    Helper function for BOLA/IDOR protection.

    Args:
        db: Database session
        user_id: ID of requesting user (teacher)
        class_id: ID of class to check

    Returns:
        True if teacher owns class, False otherwise
    """
    from app.models.class_model import Class

    class_obj = db.query(Class).filter(Class.class_id == class_id).first()

    if not class_obj:
        return False

    return class_obj.teacher_id == user_id
