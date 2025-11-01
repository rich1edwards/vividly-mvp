"""
Authentication Endpoints

FastAPI router for authentication operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services import auth_service
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user (student or teacher).

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **role**: student or teacher
    - **grade_level**: Required for students (9-12)

    Returns access and refresh tokens (auto-login).
    """
    user = auth_service.register_user(db, user_data)
    tokens = auth_service.create_user_tokens(db, user)
    return tokens


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return access + refresh tokens.

    - **email**: Registered email address
    - **password**: User password
    """
    print(f"[Auth Endpoint] Login request received for email: {credentials.email}")

    user = auth_service.authenticate_user(db, credentials.email, credentials.password)

    print(
        f"[Auth Endpoint] User authenticated successfully: user_id={user.user_id}, email={user.email}"
    )
    print(f"[Auth Endpoint] Creating tokens for user...")

    tokens = auth_service.create_user_tokens(db, user)

    print(f"[Auth Endpoint] Tokens created successfully, returning response")
    return tokens


@router.post("/refresh", response_model=Token)
def refresh_token(
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    # TODO: Implement refresh token logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not yet implemented",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Logout user by revoking current session.
    """
    auth_service.revoke_user_sessions(db, current_user.user_id)
    return None


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Logout from all devices by revoking all sessions.
    """
    auth_service.revoke_user_sessions(db, current_user.user_id, all_sessions=True)
    return None


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current authenticated user's profile.
    """
    return current_user


@router.post("/password-reset/request")
def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset link (always returns success for security).
    """
    # TODO: Implement password reset request logic
    return {
        "message": "If an account exists with this email, a password reset link has been sent"
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirm password reset with token and new password.
    """
    # TODO: Implement password reset confirmation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset confirmation not yet implemented",
    )
