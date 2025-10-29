"""
Class model for teacher classes.
"""
from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Class(Base):
    """
    Class model for teacher-created classes.

    Teachers create classes and students join using class codes.
    """

    __tablename__ = "classes"

    # Primary key
    class_id = Column(String(100), primary_key=True, index=True)

    # Teacher association
    teacher_id = Column(String(100), ForeignKey('users.user_id'), nullable=False, index=True)

    # Class details
    name = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=True)
    class_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "PHYS-ABC-123"
    description = Column(Text, nullable=True)

    # Grade levels (JSON array)
    grade_levels = Column(JSON, nullable=True, default=[])

    # Organization
    school_id = Column(String(100), nullable=True)
    organization_id = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Soft delete
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    enrollments = relationship("ClassStudent", back_populates="class_obj")

    def __repr__(self) -> str:
        return f"<Class {self.name} ({self.class_code})>"
