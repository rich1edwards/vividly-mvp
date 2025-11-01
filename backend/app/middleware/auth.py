"""
Authentication Middleware

Provides JWT token generation/validation, password hashing,
and RBAC (Role-Based Access Control) for the Vividly API.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from functools import wraps

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-CHANGE-IN-PRODUCTION")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)  # 24 hours

# Security scheme
security = HTTPBearer()


# ============================================================================
# Password Hashing
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with 12 rounds.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# ============================================================================
# JWT Token Management
# ============================================================================


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: str  # user_id
    email: str
    role: str
    org_id: str
    exp: datetime
    iat: datetime


def create_access_token(user_id: str, email: str, role: str, org_id: str) -> str:
    """
    Create JWT access token.

    Args:
        user_id: Unique user identifier
        email: User email address
        role: User role (student, teacher, admin)
        org_id: Organization identifier

    Returns:
        Encoded JWT token string
    """
    now = datetime.utcnow()
    expire = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "org_id": org_id,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        return TokenPayload(**payload)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


# ============================================================================
# Authentication Dependencies
# ============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get current authenticated user.

    Validates JWT token and returns user from database.

    Args:
        credentials: HTTP Bearer token from request
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = decode_access_token(token)

    # Fetch user from database
    user = db.query(User).filter(User.id == token_data.sub).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Account is {user.status}"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency to get current active user.

    Ensures user account is active and not locked.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User object

    Raises:
        HTTPException: If user account is not active
    """
    if not current_user.status == "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active"
        )

    return current_user


# ============================================================================
# Role-Based Access Control (RBAC)
# ============================================================================


class RoleChecker:
    """
    Dependency class for role-based access control.

    Usage:
        @app.get("/admin/dashboard")
        async def admin_dashboard(
            user: User = Depends(RoleChecker(["admin"]))
        ):
            ...
    """

    def __init__(self, allowed_roles: List[str]):
        """
        Initialize role checker.

        Args:
            allowed_roles: List of roles allowed to access endpoint
                          (e.g., ["admin"], ["teacher", "admin"])
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if user has required role.

        Args:
            current_user: Current authenticated user

        Returns:
            User object if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(self.allowed_roles)}",
            )

        return current_user


# Convenience dependencies for common role checks
require_admin = RoleChecker(["admin"])
require_teacher = RoleChecker(["teacher", "admin"])
require_student = RoleChecker(["student"])
require_teacher_or_admin = RoleChecker(["teacher", "admin"])


def check_organization_access(user: User, target_org_id: str) -> bool:
    """
    Check if user has access to target organization.

    Args:
        user: Current user
        target_org_id: Organization ID to check access for

    Returns:
        True if user has access, False otherwise
    """
    # Admin can access their own org
    if user.role == "admin" and user.org_id == target_org_id:
        return True

    # Teacher can access their own org
    if user.role == "teacher" and user.org_id == target_org_id:
        return True

    # Student can access their own org
    if user.role == "student" and user.org_id == target_org_id:
        return True

    return False


def check_student_access(
    current_user: User, target_student_id: str, db: Session
) -> bool:
    """
    Check if user has permission to access target student data.

    Rules:
    - Admin can access students in their organization
    - Teacher can access students in their classes
    - Student can only access their own data

    Args:
        current_user: Current authenticated user
        target_student_id: Student ID to check access for
        db: Database session

    Returns:
        True if user has access, False otherwise
    """
    # Student can only access their own data
    if current_user.role == "student":
        return current_user.id == target_student_id

    # Get target student
    target_student = db.query(User).filter(User.id == target_student_id).first()
    if not target_student or target_student.role != "student":
        return False

    # Admin can access students in their organization
    if current_user.role == "admin":
        return target_student.org_id == current_user.org_id

    # Teacher can access students in their classes
    if current_user.role == "teacher":
        # Check if student is in any of teacher's classes
        from app.models import ClassStudent, Class

        is_in_class = (
            db.query(ClassStudent)
            .join(Class)
            .filter(
                ClassStudent.student_id == target_student_id,
                Class.teacher_id == current_user.id,
                ClassStudent.status == "active",
            )
            .first()
        )

        return is_in_class is not None

    return False


# ============================================================================
# Login Attempt Tracking (Anti-Brute Force)
# ============================================================================


class LoginAttemptTracker:
    """
    Track failed login attempts to prevent brute force attacks.

    Uses Redis for fast, distributed tracking.
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes in seconds

    def record_failed_attempt(self, identifier: str):
        """
        Record a failed login attempt.

        Args:
            identifier: Email or IP address
        """
        key = f"login_attempts:{identifier}"
        attempts = self.redis.incr(key)

        if attempts == 1:
            # Set expiration on first attempt
            self.redis.expire(key, self.lockout_duration)

        if attempts >= self.max_attempts:
            # Lock account
            self.redis.setex(f"login_locked:{identifier}", self.lockout_duration, "1")

    def is_locked(self, identifier: str) -> bool:
        """
        Check if identifier is locked due to too many failed attempts.

        Args:
            identifier: Email or IP address

        Returns:
            True if locked, False otherwise
        """
        return self.redis.exists(f"login_locked:{identifier}") > 0

    def get_remaining_attempts(self, identifier: str) -> int:
        """
        Get number of remaining login attempts.

        Args:
            identifier: Email or IP address

        Returns:
            Number of attempts remaining before lockout
        """
        key = f"login_attempts:{identifier}"
        attempts = int(self.redis.get(key) or 0)
        return max(0, self.max_attempts - attempts)

    def clear_attempts(self, identifier: str):
        """
        Clear failed attempts for identifier (on successful login).

        Args:
            identifier: Email or IP address
        """
        self.redis.delete(f"login_attempts:{identifier}")
        self.redis.delete(f"login_locked:{identifier}")


# ============================================================================
# Session Management
# ============================================================================


async def revoke_user_sessions(user_id: str, redis_client):
    """
    Revoke all active sessions for a user.

    Used when:
    - User changes password
    - Admin resets user account
    - Security incident

    Args:
        user_id: User identifier
        redis_client: Redis client instance
    """
    # Store revoked user in Redis with expiration matching token expiration
    key = f"revoked_user:{user_id}"
    redis_client.setex(key, JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")


async def is_session_revoked(user_id: str, redis_client) -> bool:
    """
    Check if user's sessions have been revoked.

    Args:
        user_id: User identifier
        redis_client: Redis client instance

    Returns:
        True if revoked, False otherwise
    """
    key = f"revoked_user:{user_id}"
    return redis_client.exists(key) > 0


# ============================================================================
# Utility Functions
# ============================================================================


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Checks X-Forwarded-For header for proxied requests.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


def generate_password_reset_token(user_id: str, email: str) -> str:
    """
    Generate password reset token.

    Args:
        user_id: User identifier
        email: User email

    Returns:
        Encoded JWT reset token (expires in 1 hour)
    """
    now = datetime.utcnow()
    expire = now + timedelta(hours=1)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
        "type": "password_reset",
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_password_reset_token(token: str) -> Optional[dict]:
    """
    Verify password reset token.

    Args:
        token: Reset token string

    Returns:
        Token payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != "password_reset":
            return None

        return payload

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ============================================================================
# Example Usage in Routes
# ============================================================================

"""
# Public endpoint (no authentication)
@app.get("/api/v1/public/health")
async def health_check():
    return {"status": "healthy"}


# Authenticated endpoint (any role)
@app.get("/api/v1/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    return current_user


# Admin-only endpoint
@app.get("/api/v1/admin/users")
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


# Teacher or Admin endpoint
@app.get("/api/v1/teacher/classes")
async def list_classes(
    current_user: User = Depends(require_teacher_or_admin),
    db: Session = Depends(get_db)
):
    classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    return classes


# Student-only endpoint
@app.get("/api/v1/students/dashboard")
async def student_dashboard(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    # Student-specific logic
    return {"dashboard": "data"}


# Custom permission check
@app.get("/api/v1/students/{student_id}/progress")
async def get_student_progress(
    student_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check if current user has permission to view this student's data
    if not check_student_access(current_user, student_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this student's data"
        )

    # Fetch and return progress
    ...
"""
