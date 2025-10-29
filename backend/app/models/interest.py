"""
Interest and StudentInterest models.
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Interest(Base):
    """
    Interest model representing canonical list of student interests.

    Corresponds to database table: interests
    Sample data: 14 interests preloaded (basketball, coding, music, etc.)
    """

    __tablename__ = "interests"

    # Primary key
    interest_id = Column(String(100), primary_key=True, index=True)

    # Interest details
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)  # sports, music, art, etc.
    description = Column(String(500), nullable=True)
    display_order = Column(Integer, nullable=True)

    # Relationships
    student_interests = relationship("StudentInterest", back_populates="interest", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Interest {self.name} ({self.category})>"


class StudentInterest(Base):
    """
    StudentInterest junction table linking students to interests.

    Corresponds to database table: student_interest
    Students can select 1-5 interests.
    """

    __tablename__ = "student_interest"

    # Primary key (composite)
    student_id = Column(String(100), ForeignKey('users.user_id'), primary_key=True, index=True)
    interest_id = Column(String(100), ForeignKey('interests.interest_id'), primary_key=True, index=True)

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="student_interests")
    interest = relationship("Interest", back_populates="student_interests")

    def __repr__(self) -> str:
        return f"<StudentInterest student={self.student_id} interest={self.interest_id}>"
