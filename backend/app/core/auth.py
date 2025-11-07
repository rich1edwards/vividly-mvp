"""
Authentication and Authorization Module (Stub)

TODO (Session 11 Part 21): This is a minimal stub to unblock testing.
Replace with full JWT/session-based authentication system when implementing
user-facing features.

For now, admin endpoints that require auth should be protected by API Gateway
or other infrastructure-level auth mechanisms in production.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User, UserRole


async def get_current_user(
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Stub: Returns None (no authenticated user).

    TODO: Implement actual JWT/session-based authentication:
    - Parse Authorization header
    - Validate JWT token
    - Look up user in database
    - Return User object

    For testing, admin endpoints will be unprotected.
    In production, use API Gateway auth or other infrastructure-level protection.
    """
    return None


def require_role(required_role: UserRole):
    """
    Stub: Dependency to require specific user role.

    TODO: Implement actual role checking:
    - Get current user
    - Check user.role against required_role
    - Raise HTTPException if insufficient permissions

    For testing, this returns a no-op dependency.
    """
    async def check_role(current_user: Optional[User] = Depends(get_current_user)):
        # Stub: Allow all requests through for testing
        # TODO: Implement actual role checking
        pass

    return check_role
