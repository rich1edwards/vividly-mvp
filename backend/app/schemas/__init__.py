"""
Pydantic schemas package.
"""
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.student import (
    StudentProfileUpdate,
    StudentProfile,
    InterestBase,
    StudentInterestsUpdate,
    TopicProgress,
    StudentActivity,
    LearningProgress,
    JoinClassRequest,
)
from app.schemas.teacher import (
    CreateClassRequest,
    UpdateClassRequest,
    ClassResponse,
    StudentInRoster,
    RosterResponse,
    StudentAccountRequestCreate,
    BulkStudentAccountRequest,
    StudentAccountRequestResponse,
    ClassSummary,
    TeacherDashboard,
)


__all__ = [
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "Token",
    "UserResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Student schemas
    "StudentProfileUpdate",
    "StudentProfile",
    "InterestBase",
    "StudentInterestsUpdate",
    "TopicProgress",
    "StudentActivity",
    "LearningProgress",
    "JoinClassRequest",
    # Teacher schemas
    "CreateClassRequest",
    "UpdateClassRequest",
    "ClassResponse",
    "StudentInRoster",
    "RosterResponse",
    "StudentAccountRequestCreate",
    "BulkStudentAccountRequest",
    "StudentAccountRequestResponse",
    "ClassSummary",
    "TeacherDashboard",
]
