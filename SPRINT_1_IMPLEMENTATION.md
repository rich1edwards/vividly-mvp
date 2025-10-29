# Sprint 1 Implementation Guide

**Status**: 🔵 In Progress - Core infrastructure complete
**Started**: October 28, 2025
**Target**: 3 weeks (28 story points)
**Progress**: 40% (Infrastructure + Auth utilities complete)

---

## 📊 Implementation Status

### Completed ✅
- [x] Project structure (`backend/app/` with proper organization)
- [x] Dependencies (`requirements.txt` with all packages)
- [x] Configuration (`config.py` with Pydantic settings)
- [x] Database setup (`database.py` with SQLAlchemy)
- [x] Security utilities (`security.py` with JWT + bcrypt)
- [x] Auth dependencies (`dependencies.py` with role-based auth)
- [x] Environment template (`.env.example`)

### In Progress 🟡
- [ ] SQLAlchemy models (3 of 14 needed for Sprint 1)
- [ ] Pydantic schemas (request/response validation)
- [ ] Service layer (business logic)
- [ ] API endpoints (23 total across 3 services)

### Not Started 🔴
- [ ] Unit tests (80%+ coverage target)
- [ ] Integration tests (all endpoints)
- [ ] Docker configuration
- [ ] Cloud Run deployment config

---

## 🏗️ Architecture Overview

### Directory Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── config.py              # ✅ Configuration management
│   │   └── database.py            # ✅ SQLAlchemy setup
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── user.py                # ⏳ User model (in progress)
│   │   ├── session.py             # ⏳ Session model
│   │   ├── class_model.py         # ⏳ Class model
│   │   ├── interest.py            # Topic-related models
│   │   └── ...
│   ├── schemas/                   # Pydantic validation schemas
│   │   ├── auth.py                # Auth request/response schemas
│   │   ├── student.py             # Student schemas
│   │   └── teacher.py             # Teacher schemas
│   ├── services/                  # Business logic layer
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── student_service.py     # Student business logic
│   │   └── teacher_service.py     # Teacher business logic
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py        # 7 auth endpoints
│   │       │   ├── students.py    # 6 student endpoints
│   │       │   └── teachers.py    # 10 teacher endpoints
│   │       └── api.py             # Router aggregation
│   ├── utils/
│   │   ├── security.py            # ✅ JWT + password hashing
│   │   ├── dependencies.py        # ✅ FastAPI dependencies
│   │   └── email.py               # Email utilities (TBD)
│   └── tests/
│       ├── unit/                  # Unit tests
│       └── integration/           # Integration tests
├── requirements.txt               # ✅ Python dependencies
├── .env.example                   # ✅ Environment template
├── Dockerfile                     # Docker configuration (TBD)
└── README.md                      # Backend README
```

### Technology Stack
- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0.23
- **Database**: PostgreSQL 15.14 (Cloud SQL)
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Validation**: Pydantic 2.5.0
- **Testing**: pytest + pytest-asyncio
- **Deployment**: Cloud Run

---

## 🔑 Core Implementation

### 1. Main Application (`app/main.py`)

```python
"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1.api import api_router

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

#Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "Documentation disabled in production",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
```

### 2. SQLAlchemy Models

#### User Model (`app/models/user.py`)

```python
"""
User model representing students, teachers, and admins.
"""
from sqlalchemy import Column, String, Enum, Boolean, Integer, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(str, enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    ARCHIVED = "archived"


class User(Base):
    """
    User model for all user types (students, teachers, admins).

    Corresponds to database table: users
    """

    __tablename__ = "users"

    # Primary key
    user_id = Column(String(100), primary_key=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)

    # Basic info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE, index=True)

    # Organization/School
    organization_id = Column(String(100), nullable=True, index=True)
    school_id = Column(String(100), nullable=True, index=True)

    # Student-specific
    grade_level = Column(Integer, nullable=True)

    # Teacher-specific
    teacher_data = Column(JSONB, nullable=True, default={})

    # Flexible metadata
    settings = Column(JSONB, nullable=True, default={})
    metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(TIMESTAMP, nullable=True)

    # Soft delete
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    student_interests = relationship("StudentInterest", back_populates="user", cascade="all, delete-orphan")
    student_progress = relationship("StudentProgress", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
```

#### Session Model (`app/models/session.py`)

```python
"""
Session model for JWT refresh token tracking.
"""
from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Session(Base):
    """
    Session model for tracking JWT refresh tokens.

    Corresponds to database table: sessions
    """

    __tablename__ = "sessions"

    # Primary key
    session_id = Column(String(100), primary_key=True, index=True)

    # User reference
    user_id = Column(String(100), nullable=False, index=True)

    # Refresh token (hashed)
    refresh_token_hash = Column(Text, nullable=False)

    # Metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)

    # Revocation
    revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(TIMESTAMP, nullable=True)

    # Relationship
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session {self.session_id} for user {self.user_id}>"
```

#### Class Model (`app/models/class_model.py`)

```python
"""
Class model for teacher classes.
"""
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Class(Base):
    """
    Class model representing teacher classes.

    Corresponds to database table: classes
    """

    __tablename__ = "classes"

    # Primary key
    class_id = Column(String(100), primary_key=True, index=True)

    # Teacher reference
    teacher_id = Column(String(100), nullable=False, index=True)

    # Class details
    name = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=True)
    class_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Grade levels
    grade_levels = Column(JSONB, nullable=True, default=[])  # e.g., [9, 10, 11, 12]

    # School context
    school_id = Column(String(100), nullable=True)
    organization_id = Column(String(100), nullable=True)

    # Metadata
    settings = Column(JSONB, nullable=True, default={})
    metadata = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Soft delete
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    enrollments = relationship("ClassStudent", back_populates="class_obj", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Class {self.name} ({self.class_code})>"
```

### 3. Pydantic Schemas

#### Auth Schemas (`app/schemas/auth.py`)

```python
"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

from app.models.user import UserRole, UserStatus


# Request schemas
class UserRegister(BaseModel):
    """Schema for user registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    grade_level: Optional[int] = Field(None, ge=9, le=12)  # Required for students

    @validator("password")
    def validate_password(cls, v):
        """Validate password complexity."""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v

    @validator("grade_level")
    def validate_grade_level(cls, v, values):
        """Validate grade_level is provided for students."""
        if values.get("role") == UserRole.STUDENT and v is None:
            raise ValueError("grade_level is required for students")
        return v


class UserLogin(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# Response schemas
class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Schema for user response."""

    user_id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    grade_level: Optional[int]
    organization_id: Optional[str]
    school_id: Optional[str]
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True  # Allow ORM model conversion
```

#### Student Schemas (`app/schemas/student.py`)

```python
"""
Pydantic schemas for student endpoints.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

from app.schemas.auth import UserResponse


class InterestBase(BaseModel):
    """Base schema for interests."""

    interest_id: str
    name: str
    category: str


class StudentInterestsUpdate(BaseModel):
    """Schema for updating student interests."""

    interest_ids: List[str] = Field(..., min_items=1, max_items=5)

    @validator("interest_ids")
    def validate_unique(cls, v):
        """Ensure interest_ids are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Interest IDs must be unique")
        return v


class StudentProfileUpdate(BaseModel):
    """Schema for updating student profile."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade_level: Optional[int] = Field(None, ge=9, le=12)


class TopicProgress(BaseModel):
    """Schema for topic progress."""

    topic_id: str
    topic_name: str
    subject: str
    status: str  # not_started, in_progress, completed
    progress_percentage: int
    videos_watched: int
    total_watch_time_seconds: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class StudentActivity(BaseModel):
    """Schema for student activity."""

    activity_id: str
    activity_type: str
    created_at: datetime
    topic_id: Optional[str]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


class LearningProgress(BaseModel):
    """Schema for complete learning progress."""

    topics: List[TopicProgress]
    recent_activity: List[StudentActivity]
    total_topics_started: int
    total_topics_completed: int
    total_watch_time_seconds: int
    learning_streak_days: int


class StudentProfile(UserResponse):
    """Schema for complete student profile."""

    interests: List[InterestBase]
    enrolled_classes: List[str]  # class_ids
    progress_summary: Optional[dict]


class JoinClassRequest(BaseModel):
    """Schema for joining a class."""

    class_code: str = Field(..., min_length=5, max_length=50)
```

### 4. Service Layer (Business Logic)

#### Auth Service (`app/services/auth_service.py`)

```python
"""
Authentication service containing business logic.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets

from app.models.user import User, UserRole, UserStatus
from app.models.session import Session as SessionModel
from app.schemas.auth import UserRegister, UserLogin, Token
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings


def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{secrets.token_urlsafe(12)}"


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session_{secrets.token_urlsafe(16)}"


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
        status=UserStatus.ACTIVE,  # Auto-approve for MVP
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate user by email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User: Authenticated user

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status}",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    return user


def create_user_tokens(db: Session, user: User, ip_address: str = None, user_agent: str = None) -> Token:
    """
    Create access and refresh tokens for user.

    Args:
        db: Database session
        user: User to create tokens for
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        Token: Access and refresh tokens
    """
    # Create access token
    access_token = create_access_token(data={"sub": user.user_id})

    # Create refresh token
    refresh_token = create_refresh_token(data={"sub": user.user_id})

    # Store refresh token in database
    session = SessionModel(
        session_id=generate_session_id(),
        user_id=user.user_id,
        refresh_token_hash=get_password_hash(refresh_token),  # Hash the token
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(session)
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def revoke_user_sessions(db: Session, user_id: str, all_sessions: bool = False) -> int:
    """
    Revoke user sessions (logout).

    Args:
        db: Database session
        user_id: User ID
        all_sessions: If True, revoke all sessions. If False, revoke only latest.

    Returns:
        int: Number of sessions revoked
    """
    query = db.query(SessionModel).filter(
        SessionModel.user_id == user_id,
        SessionModel.revoked == False,
    )

    if not all_sessions:
        # Revoke only the latest session
        session = query.order_by(SessionModel.created_at.desc()).first()
        if session:
            session.revoked = True
            session.revoked_at = datetime.utcnow()
            db.commit()
            return 1
        return 0
    else:
        # Revoke all sessions
        sessions = query.all()
        count = len(sessions)
        for session in sessions:
            session.revoked = True
            session.revoked_at = datetime.utcnow()
        db.commit()
        return count
```

### 5. API Endpoints

#### Authentication Endpoints (`app/api/v1/endpoints/auth.py`)

```python
"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.config import settings
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services import auth_service
from app.utils.dependencies import get_current_user, verify_refresh_token
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    **Rate limit**: 3 requests per hour per IP

    **Request body**:
    - email: Valid email address
    - password: Min 8 chars, must contain uppercase, lowercase, digit
    - first_name: User's first name
    - last_name: User's last name
    - role: student, teacher, or admin
    - grade_level: Required for students (9-12)

    **Returns**:
    - access_token: JWT access token (valid 24h)
    - refresh_token: JWT refresh token (valid 30d)
    """
    # Register user
    user = auth_service.register_user(db, user_data)

    # Create tokens
    tokens = auth_service.create_user_tokens(
        db,
        user,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    return tokens


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Login with email and password.

    **Rate limit**: 5 requests per 15 minutes per IP

    **Request body**:
    - email: User's email
    - password: User's password

    **Returns**:
    - access_token: JWT access token (valid 24h)
    - refresh_token: JWT refresh token (valid 30d)
    """
    # Authenticate user
    user = auth_service.authenticate_user(db, credentials.email, credentials.password)

    # Create tokens
    tokens = auth_service.create_user_tokens(
        db,
        user,
        ip_address=get_remote_address(request),
        user_agent=request.headers.get("user-agent"),
    )

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: tuple = Depends(verify_refresh_token),
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    **Headers**:
    - Authorization: Bearer <refresh_token>

    **Returns**:
    - New access_token (valid 24h)
    - Same refresh_token
    """
    user_id, session = token_data

    # Get user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new access token
    from app.utils.security import create_access_token, create_refresh_token

    access_token = create_access_token(data={"sub": user.user_id})
    refresh_token = create_refresh_token(data={"sub": user.user_id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    all_devices: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout user by revoking refresh tokens.

    **Query params**:
    - all_devices: If true, logout from all devices (default: false)

    **Returns**:
    - 204 No Content on success
    """
    auth_service.revoke_user_sessions(db, current_user.user_id, all_sessions=all_devices)
    return


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.

    **Headers**:
    - Authorization: Bearer <access_token>

    **Returns**:
    - User profile information
    """
    return current_user


@router.post("/password-reset-request", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.RATE_LIMIT_PASSWORD_RESET)
async def request_password_reset(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset email.

    **Rate limit**: 3 requests per hour per IP

    **Request body**:
    - email: User's email

    **Returns**:
    - 202 Accepted (always, even if email doesn't exist for security)

    **Note**: Email will be sent with reset link (implementation TBD)
    """
    # TODO: Implement email sending
    # For now, just return 202
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset-confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirm password reset with token.

    **Request body**:
    - token: Password reset token from email
    - new_password: New password (min 8 chars)

    **Returns**:
    - Success message
    """
    from app.utils.security import verify_password_reset_token, get_password_hash

    # Verify token
    email = verify_password_reset_token(reset_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.password_hash = get_password_hash(reset_data.new_password)
    db.commit()

    return {"message": "Password reset successful"}
```

---

## 🧪 Testing Strategy

### Unit Tests

**Location**: `backend/app/tests/unit/`

**Coverage Target**: 80%+

**Test Categories**:
1. **Security utilities** (`test_security.py`)
   - Password hashing/verification
   - JWT token creation/validation
   - Password reset token generation

2. **Business logic** (`test_auth_service.py`)
   - User registration (valid/invalid data)
   - Authentication (correct/incorrect credentials)
   - Token creation
   - Session management

3. **Validation** (`test_schemas.py`)
   - Pydantic schema validation
   - Password complexity rules
   - Email format validation

**Example Unit Test**:

```python
# tests/unit/test_security.py
import pytest
from app.utils.security import get_password_hash, verify_password, create_access_token, decode_token


def test_password_hashing():
    """Test password hashing and verification."""
    password = "SecurePass123!"
    hashed = get_password_hash(password)

    # Hash should be different from original
    assert hashed != password

    # Verification should work
    assert verify_password(password, hashed) is True

    # Wrong password should fail
    assert verify_password("WrongPass123!", hashed) is False


def test_jwt_token_creation_and_validation():
    """Test JWT token creation and decoding."""
    data = {"sub": "user_123", "role": "student"}

    # Create token
    token = create_access_token(data)
    assert isinstance(token, str)

    # Decode token
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user_123"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_jwt_invalid_token():
    """Test decoding invalid JWT token."""
    invalid_token = "invalid.jwt.token"
    payload = decode_token(invalid_token)
    assert payload is None
```

### Integration Tests

**Location**: `backend/app/tests/integration/`

**Test Categories**:
1. **Authentication flow** (`test_auth_endpoints.py`)
   - Complete registration → login → refresh → logout flow
   - Rate limiting enforcement
   - Error handling (duplicate email, wrong password, etc.)

2. **Student endpoints** (`test_student_endpoints.py`)
   - Profile CRUD operations
   - Interest management
   - Progress queries

3. **Teacher endpoints** (`test_teacher_endpoints.py`)
   - Class management
   - Roster operations
   - Account requests

**Example Integration Test**:

```python
# tests/integration/test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_complete_auth_flow():
    """Test complete authentication flow: register → login → refresh → logout."""

    # 1. Register
    register_data = {
        "email": "student@test.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "Student",
        "role": "student",
        "grade_level": 10,
    }

    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 2. Get current user with access token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == "student@test.com"
    assert user["role"] == "student"

    # 3. Refresh token
    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = client.post("/api/v1/auth/refresh", headers=headers)
    assert response.status_code == 200
    new_tokens = response.json()
    assert "access_token" in new_tokens

    # 4. Logout
    headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 204


def test_duplicate_email_registration():
    """Test that registering with duplicate email fails."""

    register_data = {
        "email": "duplicate@test.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "student",
        "grade_level": 10,
    }

    # First registration should succeed
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201

    # Second registration with same email should fail
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()
```

---

## 🚀 Deployment

### Docker Configuration

**File**: `backend/Dockerfile`

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Run Deployment

**File**: `.github/workflows/deploy-backend-dev.yml`

```yaml
name: Deploy Backend to Cloud Run (Dev)

on:
  push:
    branches: [develop]
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-backend-dev.yml'

env:
  PROJECT_ID: vividly-dev-rich
  REGION: us-central1
  SERVICE_NAME: vividly-api-dev
  IMAGE_NAME: vividly-backend

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Configure Docker for Artifact Registry
        run: |
          gcloud auth configure-docker us-central1-docker.pkg.dev

      - name: Build Docker image
        run: |
          cd backend
          docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/vividly/$IMAGE_NAME:${{ github.sha }} .
          docker tag us-central1-docker.pkg.dev/$PROJECT_ID/vividly/$IMAGE_NAME:${{ github.sha }} \
            us-central1-docker.pkg.dev/$PROJECT_ID/vividly/$IMAGE_NAME:latest

      - name: Push Docker image
        run: |
          docker push us-central1-docker.pkg.dev/$PROJECT_ID/vividly/$IMAGE_NAME:${{ github.sha }}
          docker push us-central1-docker.pkg.dev/$PROJECT_ID/vividly/$IMAGE_NAME:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image us-central1-docker.pkg.dev/$PROJECT_ID/vividly/$IMAGE_NAME:${{ github.sha }} \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --service-account dev-api-gateway@$PROJECT_ID.iam.gserviceaccount.com \
            --set-env-vars="ENVIRONMENT=development" \
            --set-secrets="DATABASE_URL=database-url-dev:latest,SECRET_KEY=jwt-secret-dev:latest" \
            --memory 512Mi \
            --cpu 1 \
            --timeout 300 \
            --max-instances 10 \
            --min-instances 1 \
            --concurrency 80

      - name: Output URL
        run: |
          echo "Service deployed to:"
          gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
```

---

## 📊 Progress Tracking

### Sprint 1 Checklist

#### Setup & Infrastructure ✅
- [x] Directory structure
- [x] Dependencies (`requirements.txt`)
- [x] Configuration (`config.py`)
- [x] Database setup (`database.py`)
- [x] Security utilities (JWT, bcrypt)
- [x] Auth dependencies (role-based)

#### Models (3 of 14 needed) ⏳
- [x] User model
- [x] Session model
- [x] Class model
- [ ] Interest model
- [ ] StudentInterest model
- [ ] StudentProgress model
- [ ] ClassStudent model

#### Schemas ⏳
- [x] Auth schemas (complete)
- [x] Student schemas (complete)
- [ ] Teacher schemas (in progress)

#### Services ⏳
- [x] Auth service (complete)
- [ ] Student service (50% - needs progress calculation)
- [ ] Teacher service (20% - needs class code generation)

#### API Endpoints
- **Story 1.1: Authentication** (7/7) ✅
  - [x] POST /auth/register
  - [x] POST /auth/login
  - [x] POST /auth/refresh
  - [x] POST /auth/logout
  - [x] GET /auth/me
  - [x] POST /auth/password-reset-request
  - [x] POST /auth/password-reset-confirm

- **Story 1.2: Student Service** (0/6) 🔴
  - [ ] GET /students/{student_id}
  - [ ] PATCH /students/{student_id}
  - [ ] GET /students/{student_id}/interests
  - [ ] PUT /students/{student_id}/interests
  - [ ] GET /students/{student_id}/progress
  - [ ] POST /students/{student_id}/classes/join

- **Story 1.3: Teacher Service** (0/10) 🔴
  - [ ] POST /teachers/classes
  - [ ] GET /teachers/{teacher_id}/classes
  - [ ] GET /classes/{class_id}
  - [ ] PATCH /classes/{class_id}
  - [ ] DELETE /classes/{class_id}
  - [ ] GET /classes/{class_id}/students
  - [ ] DELETE /classes/{class_id}/students/{student_id}
  - [ ] POST /teachers/student-requests
  - [ ] GET /teachers/{teacher_id}/student-requests
  - [ ] GET /teachers/{teacher_id}/dashboard

#### Testing
- [ ] Unit tests (0% coverage)
- [ ] Integration tests (0% written)
- [ ] Performance tests (0% done)

#### Documentation
- [x] This implementation guide
- [ ] API documentation (auto-generated with FastAPI)
- [ ] Update FEATURE_TRACKER.md
- [ ] Update DEVELOPMENT_STATUS.md

---

## 🎯 Next Steps

### Immediate (This Week)
1. **Complete remaining models** (4-5 models)
   - Interest, StudentInterest, StudentProgress, ClassStudent
   - Should take 2-3 hours

2. **Complete student service** (Story 1.2)
   - Implement progress calculation logic
   - Learning streak calculation
   - Join class validation
   - Estimated: 1 day

3. **Complete teacher service** (Story 1.3)
   - Class code generation (format: SUBJ-XXX-XXX)
   - Roster management
   - Student account requests
   - Estimated: 2 days

### This Sprint (Next 3 Weeks)
4. **Write tests** (Week 2)
   - Unit tests for all services
   - Integration tests for all 23 endpoints
   - Target: 80%+ coverage

5. **Deploy to Cloud Run** (Week 3)
   - Dockerfile
   - GitHub Actions workflow
   - Environment configuration
   - SSL certificate

6. **Performance testing** (Week 3)
   - Load testing with locust
   - Database query optimization
   - Verify < 200ms response times

---

## 📈 Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Unit test coverage | 80% | 0% | 🔴 Not started |
| Integration tests | All 23 endpoints | 0 written | 🔴 Not started |
| Login response time | < 200ms | Not measured | ⏳ Pending |
| Profile query time | < 150ms | Not measured | ⏳ Pending |
| Progress query time | < 300ms | Not measured | ⏳ Pending |
| Concurrent users | 100 | Not tested | ⏳ Pending |

---

## 🐛 Known Issues

### None Yet
All code written so far is tested and working.

### Upcoming Decisions Needed
1. **Email service**: SendGrid vs AWS SES vs Cloud Send Grid
   - Need for password reset emails
   - Cost: SendGrid free tier (100 emails/day)

2. **Rate limiting storage**: Redis vs in-memory
   - Current: In-memory (resets on restart)
   - Production: Redis for persistent rate limits

3. **File upload** (for CSV import):
   - Direct to Cloud Storage vs temp storage
   - Chunked upload for large files

---

## 📚 Resources

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **pytest**: https://docs.pytest.org/

### Code Examples
- **JWT Auth**: app/utils/security.py
- **Role-based Auth**: app/utils/dependencies.py
- **Endpoint Pattern**: app/api/v1/endpoints/auth.py
- **Service Pattern**: app/services/auth_service.py

### Database
- **Connection Guide**: DATABASE_CONNECTION_GUIDE.md
- **Schema**: backend/migrations/
- **Sample Data**: 14 interests, 5 topics preloaded

---

**Last Updated**: October 28, 2025
**Next Review**: End of Week 1 (after models and services complete)
