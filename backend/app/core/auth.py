"""
Authentication and Authorization Module

Implements JWT-based authentication and role-based access control (RBAC).
Uses the security infrastructure from app.core.security.

Session 11 Part 22: Replaced stub implementation with proper JWT authentication.
Following Andrew Ng's methodology: "Build it right - leverage existing infrastructure."
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import (
    get_current_user as security_get_current_user,
    get_current_active_user as security_get_current_active_user,
)
from app.models.user import User, UserRole


# Re-export security functions for backward compatibility
async def get_current_user(
    current_user: User = Depends(security_get_current_user),
) -> User:
    """
    Get current authenticated user from JWT token.

    This is a wrapper around security.get_current_user() for backward compatibility.
    See app.core.security for implementation details.

    Args:
        current_user: User extracted from JWT token

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    return current_user


async def get_current_active_user(
    current_user: User = Depends(security_get_current_active_user),
) -> User:
    """
    Get current active user (not suspended or archived).

    This is a wrapper around security.get_current_active_user() for backward compatibility.
    See app.core.security for implementation details.

    Args:
        current_user: User extracted from JWT token

    Returns:
        User: Current active user

    Raises:
        HTTPException: 401 if token is invalid, 403 if user is not active
    """
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role with hierarchical RBAC.

    Role Hierarchy (highest to lowest):
    1. SUPER_ADMIN - Full system access
    2. ADMIN - Organization-wide admin access
    3. TEACHER - Teacher access within organization
    4. STUDENT - Student access only

    Higher roles automatically have access to lower role endpoints.
    Example: SUPER_ADMIN can access ADMIN, TEACHER, and STUDENT endpoints.

    Args:
        required_role: Minimum role required for access

    Returns:
        Dependency function that validates user role

    Raises:
        HTTPException: 403 if user lacks required permissions

    Example:
        ```python
        @router.get("/admin/users")
        async def list_users(
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            # Only ADMIN and SUPER_ADMIN can access
            ...
        ```
    """
    # Define role hierarchy (higher index = higher privilege)
    role_hierarchy = {
        UserRole.STUDENT: 0,
        UserRole.TEACHER: 1,
        UserRole.ADMIN: 2,
        UserRole.SUPER_ADMIN: 3,
    }

    async def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if current user has required role or higher.

        Args:
            current_user: Current authenticated active user

        Returns:
            User: Current user if authorized

        Raises:
            HTTPException: 403 if insufficient permissions
        """
        user_role_level = role_hierarchy.get(current_user.role, -1)
        required_role_level = role_hierarchy.get(required_role, 999)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}, "
                f"current role: {current_user.role.value}",
            )

        return current_user

    return check_role


def require_organization_access(organization_id: str):
    """
    Dependency factory to require access to specific organization.

    Validates that user belongs to the specified organization.
    SUPER_ADMIN bypasses this check (can access all organizations).

    Args:
        organization_id: Organization ID to validate access for

    Returns:
        Dependency function that validates organization access

    Raises:
        HTTPException: 403 if user lacks organization access

    Example:
        ```python
        @router.get("/organizations/{org_id}/students")
        async def list_org_students(
            org_id: str,
            current_user: User = Depends(require_organization_access(org_id))
        ):
            # Only users in org_id can access
            ...
        ```
    """

    async def check_organization(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Check if current user has access to organization.

        Args:
            current_user: Current authenticated active user

        Returns:
            User: Current user if authorized

        Raises:
            HTTPException: 403 if user not in organization
        """
        # SUPER_ADMIN bypasses organization checks
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        # Validate user belongs to organization
        if current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User does not belong to organization {organization_id}",
            )

        return current_user

    return check_organization
