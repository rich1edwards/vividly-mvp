"""
ClassStudent junction table model.
"""
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ClassStudent(Base):
    """
    ClassStudent junction table linking students to classes.

    Corresponds to database table: class_student
    """

    __tablename__ = "class_student"

    # Primary key (composite)
    class_id = Column(String(100), ForeignKey('classes.class_id'), primary_key=True, index=True)
    student_id = Column(String(100), ForeignKey('users.user_id'), primary_key=True, index=True)

    # Timestamps
    enrolled_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relationships
    class_obj = relationship("Class", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<ClassStudent class={self.class_id} student={self.student_id}>"
