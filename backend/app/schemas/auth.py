"""
Authentication Schemas

Pydantic models for authentication endpoints.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime
import re
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    """Alias for UserRegister - for backwards compatibility."""

    """
    User registration request.

    Example:
        {
            "email": "student@mnps.edu",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student",
            "grade_level": 10
        }
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    role: str = Field(..., description="User role (student, teacher)")
    grade_level: Optional[int] = Field(
        None, ge=9, le=12, description="Grade level (required for students)"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password contains mixed case, number."""
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role is allowed value."""
        allowed_roles = ["student", "teacher"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level_for_students(cls, v, info):
        """Validate grade_level is required for students."""
        if "role" in info.data and info.data["role"] == "student" and v is None:
            raise ValueError("grade_level is required for students")
        return v


class RegisterResponse(BaseModel):
    """
    User registration response.

    Example:
        {
            "user_id": "user_abc123",
            "email": "student@mnps.edu",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student",
            "grade_level": 10,
            "created_at": "2025-11-04T10:00:00Z"
        }
    """

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    grade_level: Optional[int] = None
    created_at: datetime


class LoginRequest(BaseModel):
    """
    User login request.

    Example:
        {
            "email": "student@mnps.edu",
            "password": "SecurePass123!"
        }
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserProfile(BaseModel):
    """
    User profile data (embedded in login response and /me endpoint).

    Example:
        {
            "user_id": "user_abc123",
            "email": "student@mnps.edu",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student",
            "grade_level": 10
        }
    """

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    grade_level: Optional[int] = None
    school_id: Optional[str] = None
    interests: Optional[List[str]] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    # Teacher-specific fields
    classes: Optional[List[dict]] = None


class LoginResponse(BaseModel):
    """
    User login response with tokens.

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 86400,
            "user": {...}
        }
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400  # 24 hours in seconds
    user: UserProfile


class RefreshTokenRequest(BaseModel):
    """
    Token refresh request.

    Example:
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    """

    refresh_token: str = Field(..., description="Refresh token from login")


class RefreshTokenResponse(BaseModel):
    """
    Token refresh response with new tokens.

    Example:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 86400
        }
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400


class PasswordResetRequest(BaseModel):
    """
    Password reset request (step 1 - request reset link).

    Example:
        {
            "email": "student@mnps.edu"
        }
    """

    email: EmailStr = Field(..., description="Email address to send reset link")


class PasswordResetResponse(BaseModel):
    """
    Password reset request response (always success for security).

    Example:
        {
            "message": "If an account exists with this email, a password reset link has been sent."
        }
    """

    message: str = (
        "If an account exists with this email, a password reset link has been sent."
    )


class PasswordResetConfirmRequest(BaseModel):
    """
    Password reset confirmation (step 2 - submit new password with token).

    Example:
        {
            "reset_token": "550e8400-e29b-41d4-a716-446655440000",
            "new_password": "NewSecurePass123!"
        }
    """

    reset_token: str = Field(..., description="Reset token from email")
    new_password: str = Field(
        ..., min_length=8, description="New password (min 8 characters)"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password contains mixed case, number."""
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class PasswordResetConfirmResponse(BaseModel):
    """
    Password reset confirmation response.

    Example:
        {
            "message": "Password reset successfully. Please log in with your new password."
        }
    """

    message: str = "Password reset successfully. Please log in with your new password."


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Example:
        {
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid email or password"
            }
        }
    """

    error: dict = Field(..., description="Error details")


# Aliases for backwards compatibility with Sprint 1 implementation
UserRegister = RegisterRequest
UserLogin = LoginRequest
Token = RefreshTokenResponse
UserResponse = RegisterResponse
PasswordResetConfirm = PasswordResetConfirmRequest


# Proper schemas for Sprint 1
class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    grade_level: Optional[int] = Field(None, ge=9, le=12)


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    grade_level: Optional[int] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None
    organization_id: Optional[str] = None

    class Config:
        from_attributes = True


class TokenWithUser(BaseModel):
    """JWT token response with user profile - used for login/register."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse  # Now UserResponse is defined above


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8)
