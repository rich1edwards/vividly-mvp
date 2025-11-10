"""
Authentication service containing business logic for auth operations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)

from app.models.user import User, UserRole, UserStatus
from app.models.session import Session as SessionModel
from app.schemas.auth import UserRegister, Token, TokenWithUser, UserResponse
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


def create_user_tokens_with_profile(
    db: Session, user: User, ip_address: str = None, user_agent: str = None
) -> TokenWithUser:
    """
    Create access and refresh tokens for user, including user profile.
    Used for login and registration endpoints.

    Args:
        db: Database session
        user: User object
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        TokenWithUser: Access and refresh tokens with user profile
    """
    # Generate session ID first
    session_id = generate_session_id()

    # Create tokens with session_id embedded
    access_token = create_access_token(data={"sub": user.user_id, "sid": session_id})
    refresh_token = create_refresh_token(data={"sub": user.user_id, "sid": session_id})

    # Store refresh token in database
    session = SessionModel(
        session_id=session_id,
        user_id=user.user_id,
        refresh_token_hash=get_password_hash(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    db.add(session)
    db.commit()

    # Create user response - convert to dict to avoid Pydantic validation issues
    user_dict = {
        "user_id": user.user_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "status": user.status.value,
        "grade_level": user.grade_level,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "organization_id": user.organization_id,
    }

    return TokenWithUser(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1440 * 60,  # 24 hours in seconds
        user=user_dict,  # Pass as dict, Pydantic will convert to UserResponse
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


def refresh_access_token(
    db: Session, refresh_token: str, ip_address: str = None, user_agent: str = None
) -> Token:
    """
    Refresh access token using a valid refresh token.

    Validates the refresh token, checks session status, and issues new tokens.
    Implements token rotation for enhanced security - old refresh token is revoked
    and a new one is issued.

    Args:
        db: Database session
        refresh_token: Refresh token from client
        ip_address: Client IP address (optional)
        user_agent: Client user agent (optional)

    Returns:
        Token: New access and refresh tokens

    Raises:
        HTTPException: 401 if token is invalid, expired, or session revoked

    Following Andrew Ng's methodology:
    - Build it right: Proper validation, token rotation, session management
    - Test everything: Comprehensive error handling for all failure modes
    - Think about the future: Token rotation prevents token reuse attacks
    """
    from app.core.security import (
        decode_token,
        create_access_token,
        create_refresh_token,
    )

    try:
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        token_type = payload.get("type")

        # Verify it's a refresh token (not access token)
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token.",
            )

        user_id = payload.get("sub")
        session_id = payload.get("sid")

        if not user_id or not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Verify user exists and is active
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}",
            )

        # Verify session exists and is valid
        session = (
            db.query(SessionModel)
            .filter(
                SessionModel.session_id == session_id,
                SessionModel.user_id == user_id,
                SessionModel.revoked == False,
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked or does not exist",
            )

        # Check if session is expired
        if session.expires_at < datetime.utcnow():
            # Mark as revoked for cleanup
            session.revoked = True
            session.revoked_at = datetime.utcnow()
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired",
            )

        # Verify refresh token matches the one stored in session
        if not verify_password(refresh_token, session.refresh_token_hash):
            # Token doesn't match - possible replay attack
            logger.warning(
                f"Refresh token mismatch for session {session_id}. Possible replay attack."
            )
            session.revoked = True
            session.revoked_at = datetime.utcnow()
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Token rotation: Revoke old session and create new one with new tokens
        # This prevents token reuse attacks
        session.revoked = True
        session.revoked_at = datetime.utcnow()

        # Generate new session ID
        new_session_id = generate_session_id()

        # Create new tokens with new session ID
        new_access_token = create_access_token(
            data={"sub": user.user_id, "sid": new_session_id}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.user_id, "sid": new_session_id}
        )

        # Create new session record
        new_session = SessionModel(
            session_id=new_session_id,
            user_id=user.user_id,
            refresh_token_hash=get_password_hash(new_refresh_token),
            ip_address=ip_address
            or session.ip_address,  # Keep original if not provided
            user_agent=user_agent or session.user_agent,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

        db.add(new_session)
        db.commit()

        logger.info(
            f"Token refresh successful for user {user_id}. "
            f"Old session {session_id} revoked, new session {new_session_id} created."
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1440 * 60,  # 24 hours in seconds
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )
