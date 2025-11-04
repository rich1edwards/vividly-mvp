"""
Organization model for multi-tenant architecture.

Represents top-level entities that contain schools and users.
Examples: School districts, corporations, government agencies.
"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organization(Base):
    """
    Organization model for multi-tenancy.

    An organization can contain:
    - Multiple schools (K-12)
    - Multiple users (corporate training)
    - Custom content sources
    - Organization-wide settings

    Examples:
    - K-12: Metropolitan Nashville Public Schools (MNPS)
    - Corporate: Acme Corp Training Department
    - Healthcare: Memorial Hospital System
    - Government: Federal Aviation Administration
    """
    __tablename__ = "organizations"

    # Primary Key
    organization_id = Column(String(100), primary_key=True)

    # Basic Information
    name = Column(String(255), nullable=False, index=True)

    # Organization Type (from ORGANIZATION_ONBOARDING_SPEC.md)
    # Types: k12_education, higher_education, corporate_training, healthcare,
    #        government, professional_certification, customer_education, custom
    type = Column(
        String(50),
        nullable=False,
        default='k12_education',
        index=True
    )

    # Email domain for auto-enrollment (e.g., 'mnps.edu', 'acme.com')
    domain = Column(String(255), nullable=True, index=True)

    # Flexible Settings (JSON)
    # Structure:
    # {
    #   "knowledge_base": {
    #     "use_openstax": true,
    #     "enabled_templates": ["openstax", "custom_physics"],
    #     "custom_sources": [...]
    #   },
    #   "pricing": {
    #     "org_plan": "professional",  # basic, professional, enterprise
    #     "base_user_plan": "premium",  # plus, premium
    #     "allow_individual_upgrades": true,
    #     "require_upgrade_approval": false
    #   },
    #   "compliance": {
    #     "ferpa": true,
    #     "hipaa": false,
    #     "coppa": true
    #   },
    #   "features": {
    #     "sso_enabled": true,
    #     "api_access": true,
    #     "white_label": false
    #   },
    #   "learning_preferences": {
    #     "default_grade_levels": [9, 10, 11, 12],
    #     "subjects": ["physics", "chemistry", "biology"],
    #     "content_modality_defaults": {
    #       "text": true,
    #       "video": true,
    #       "audio": false
    #     }
    #   },
    #   "branding": {
    #     "logo_url": "https://...",
    #     "primary_color": "#003DA5",
    #     "custom_domain": "learn.acme.com"
    #   }
    # }
    settings = Column(JSON, nullable=False, default=dict)

    # Usage Limits (from PRICING_AND_MONETIZATION_SPEC.md)
    # These override individual user limits for org-managed users
    monthly_text_limit = Column(Integer, nullable=True)  # NULL = unlimited
    monthly_video_limit = Column(Integer, nullable=True)  # NULL = use plan default

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Soft Delete
    archived = Column(Boolean, nullable=False, default=False, index=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # TEMPORARY: Commented out schools relationship - School model doesn't exist yet
    # TODO: Implement School model or reference Class model properly
    # schools = relationship(
    #     "School",
    #     back_populates="organization",
    #     cascade="all, delete-orphan",
    #     lazy="dynamic"
    # )

    users = relationship(
        "User",
        back_populates="organization",
        foreign_keys="User.organization_id",
        lazy="dynamic"
    )

    feature_flags = relationship(
        "FeatureFlag",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Content sources will be added in Phase 2
    # content_sources = relationship("ContentSource", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.organization_id}, name={self.name}, type={self.type})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "type": self.type,
            "domain": self.domain,
            "settings": self.settings,
            "monthly_text_limit": self.monthly_text_limit,
            "monthly_video_limit": self.monthly_video_limit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived": self.archived
        }

    @property
    def org_plan(self):
        """Get organization plan tier (basic, professional, enterprise)."""
        return self.settings.get("pricing", {}).get("org_plan", "basic")

    @property
    def base_user_plan(self):
        """Get base plan provided to all users (plus, premium)."""
        return self.settings.get("pricing", {}).get("base_user_plan", "plus")

    @property
    def allow_individual_upgrades(self):
        """Whether users can upgrade to premium tiers individually."""
        return self.settings.get("pricing", {}).get("allow_individual_upgrades", True)

    @property
    def use_openstax(self):
        """Whether organization uses OpenStax content."""
        return self.settings.get("knowledge_base", {}).get("use_openstax", False)

    @property
    def enabled_templates(self):
        """List of enabled content templates."""
        return self.settings.get("knowledge_base", {}).get("enabled_templates", [])
