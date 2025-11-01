"""
Authentication service containing business logic for auth operations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets

from app.models.user import User, UserRole, UserStatus
from app.models.session import Session as SessionModel
from app.schemas.auth import UserRegister, Token
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
)


def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{secrets.token_urlsafe(12)}"


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session_{secrets.token_urlsafe(12)}"


def register_user(db: Session, user_data: UserRegister) -> User:
    """
    Register a new user.

    Args:
        db: Database session
        user_data: User registration data

    Returns:
        User: Created user

    Raises:
        HTTPException: 400 if email already exists
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        user_id=generate_user_id(),
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        grade_level=user_data.grade_level,
        status=UserStatus.ACTIVE,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate user with email and password.

    Args:
        db: Database session
        email: User email
        password: User password

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: 401 if credentials invalid, 403 if account suspended
    """
    print(f"[AuthService] Authentication attempt for email: {email}")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        print(f"[AuthService] User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    print(
        f"[AuthService] User found: user_id={user.user_id}, email={user.email}, role={user.role}, status={user.status}"
    )
    print(f"[AuthService] Verifying password...")

    password_valid = verify_password(password, user.password_hash)
    print(f"[AuthService] Password verification result: {password_valid}")

    if not password_valid:
        print(f"[AuthService] Password verification failed for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.status != UserStatus.ACTIVE:
        print(
            f"[AuthService] User account not active: {user.email}, status={user.status}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}",
        )

    # Update last login
    print(
        f"[AuthService] Authentication successful for user: {user.email}, updating last_login_at"
    )
    user.last_login_at = datetime.utcnow()
    db.commit()

    return user


def create_user_tokens(
    db: Session, user: User, ip_address: str = None, user_agent: str = None
) -> Token:
    """
    Create access and refresh tokens for user.

    Args:
        db: Database session
        user: User object
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        Token: Access and refresh tokens
    """
    # Create tokens
    access_token = create_access_token(data={"sub": user.user_id})
    refresh_token = create_refresh_token(data={"sub": user.user_id})

    # Store refresh token in database
    session = SessionModel(
        session_id=generate_session_id(),
        user_id=user.user_id,
        refresh_token_hash=get_password_hash(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    db.add(session)
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1440 * 60,  # 24 hours in seconds
    )


def revoke_user_sessions(db: Session, user_id: str, all_sessions: bool = False) -> None:
    """
    Revoke user sessions (logout).

    Args:
        db: Database session
        user_id: User ID
        all_sessions: If True, revoke all sessions; if False, revoke latest session

    Returns:
        None
    """
    if all_sessions:
        # Revoke all sessions
        sessions = (
            db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.revoked == False)
            .all()
        )

        for session in sessions:
            session.revoked = True
            session.revoked_at = datetime.utcnow()
    else:
        # Revoke latest session
        session = (
            db.query(SessionModel)
            .filter(SessionModel.user_id == user_id, SessionModel.revoked == False)
            .order_by(SessionModel.created_at.desc())
            .first()
        )

        if session:
            session.revoked = True
            session.revoked_at = datetime.utcnow()

    db.commit()
