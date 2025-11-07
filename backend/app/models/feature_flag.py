"""
Feature Flag Models

SQLAlchemy models for feature flag system supporting:
- Global and organization-specific flags
- Percentage rollout
- User-specific overrides
- Audit trail
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    TIMESTAMP,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.database_types import GUID, JSON


class FeatureFlag(Base):
    """
    Feature flag for controlled rollouts.

    Supports:
    - Global flags (organization_id = NULL)
    - Organization-specific flags
    - Percentage-based rollout
    """

    __tablename__ = "feature_flags"

    id = Column(
        GUID, primary_key=True
    )
    key = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Flag state
    enabled = Column(Boolean, default=False, nullable=False)
    rollout_percentage = Column(
        Integer,
        default=0,
        nullable=False,
        info={
            "check_constraint": "rollout_percentage >= 0 AND rollout_percentage <= 100"
        },
    )

    # Organization-specific (NULL = global)
    # NOTE: FK constraint temporarily removed - organizations table doesn't exist yet
    # Will restore FK when organizations table is created
    organization_id = Column(
        GUID, nullable=True, index=True
        # ForeignKey("organizations.id", ondelete="CASCADE")  # Temporarily disabled
    )

    # Metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    # NOTE: FK constraint temporarily removed - users.id uses user_id not id
    # Will restore FK when proper user ID reference is determined
    created_by = Column(GUID, nullable=True)
    # ForeignKey("users.id")  # Temporarily disabled

    # Relationships
    organization = relationship("Organization", back_populates="feature_flags")
    creator = relationship("User", foreign_keys=[created_by])
    overrides = relationship(
        "FeatureFlagOverride", back_populates="flag", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "FeatureFlagAudit", back_populates="flag", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("key", "organization_id", name="unique_flag_per_org"),
        CheckConstraint(
            "rollout_percentage >= 0 AND rollout_percentage <= 100",
            name="valid_rollout_percentage",
        ),
    )

    def __repr__(self):
        return f"<FeatureFlag(key={self.key}, enabled={self.enabled}, rollout={self.rollout_percentage}%)>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "rollout_percentage": self.rollout_percentage,
            "organization_id": str(self.organization_id)
            if self.organization_id
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FeatureFlagOverride(Base):
    """
    User-specific feature flag override.

    Allows enabling/disabling flags for specific users (e.g., beta testers).
    """

    __tablename__ = "feature_flag_overrides"

    id = Column(
        GUID, primary_key=True
    )
    flag_id = Column(
        GUID,
        ForeignKey("feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    # NOTE: FK constraint temporarily removed - users.id uses user_id not id
    # Will restore FK when proper user ID reference is determined
    user_id = Column(
        GUID, nullable=False
        # ForeignKey("users.id", ondelete="CASCADE")  # Temporarily disabled
    )

    # Override state
    enabled = Column(Boolean, nullable=False)

    # Metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    # NOTE: FK constraint temporarily removed - users.id uses user_id not id
    created_by = Column(GUID, nullable=True)
    # ForeignKey("users.id")  # Temporarily disabled
    reason = Column(Text)

    # Relationships
    flag = relationship("FeatureFlag", back_populates="overrides")
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])

    # Constraints
    __table_args__ = (
        UniqueConstraint("flag_id", "user_id", name="unique_override_per_user"),
    )

    def __repr__(self):
        return f"<FeatureFlagOverride(flag_id={self.flag_id}, user_id={self.user_id}, enabled={self.enabled})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "flag_id": str(self.flag_id),
            "user_id": str(self.user_id),
            "enabled": self.enabled,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FeatureFlagAudit(Base):
    """
    Audit log for feature flag changes.

    Tracks all changes to feature flags for compliance and debugging.
    """

    __tablename__ = "feature_flag_audit"

    id = Column(
        GUID, primary_key=True
    )
    flag_id = Column(
        GUID,
        ForeignKey("feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Change details
    action = Column(
        String(50), nullable=False
    )  # 'created', 'enabled', 'disabled', 'rollout_changed', 'deleted'
    old_value = Column(JSON)
    new_value = Column(JSON)

    # Actor
    # NOTE: FK constraint temporarily removed - users.id uses user_id not id
    changed_by = Column(GUID, nullable=True)
    # ForeignKey("users.id")  # Temporarily disabled
    changed_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Relationships
    flag = relationship("FeatureFlag", back_populates="audit_logs")
    actor = relationship("User")

    def __repr__(self):
        return f"<FeatureFlagAudit(flag_id={self.flag_id}, action={self.action}, changed_at={self.changed_at})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "flag_id": str(self.flag_id),
            "action": self.action,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": str(self.changed_by) if self.changed_by else None,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "ip_address": str(self.ip_address) if self.ip_address else None,
        }
