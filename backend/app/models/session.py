"""
Session model for JWT refresh token tracking.
"""
from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, ForeignKey
# INET replaced with String for SQLite compatibility
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Session(Base):
    """
    Session model for tracking JWT refresh tokens.

    This allows for:
    - Logout functionality (revoke specific session)
    - Logout from all devices (revoke all sessions)
    - Session history and tracking
    """

    __tablename__ = "sessions"

    # Primary key
    session_id = Column(String(100), primary_key=True, index=True)

    # User association
    user_id = Column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)

    # Token storage (hashed for security)
    refresh_token_hash = Column(Text, nullable=False)

    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)

    # Revocation
    revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session {self.session_id} for user {self.user_id}>"
