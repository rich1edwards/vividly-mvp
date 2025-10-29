"""
Student progress and activity tracking models.
"""
from sqlalchemy import Column, String, Integer, TIMESTAMP, Enum, Text, ForeignKey
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ProgressStatus(str, enum.Enum):
    """Progress status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActivityType(str, enum.Enum):
    """Activity type enumeration."""
    VIDEO_WATCHED = "video_watched"
    VIDEO_STARTED = "video_started"
    VIDEO_COMPLETED = "video_completed"
    TOPIC_STARTED = "topic_started"
    TOPIC_COMPLETED = "topic_completed"
    CLASS_JOINED = "class_joined"
    INTEREST_UPDATED = "interest_updated"
    PROFILE_UPDATED = "profile_updated"


class Topic(Base):
    """
    Topic model representing educational curriculum topics.

    Corresponds to database table: topics
    Sample data: 5 Physics topics preloaded (Newton's Laws)
    """

    __tablename__ = "topics"
    __table_args__ = {"extend_existing": True}

    # Primary key
    topic_id = Column(String(100), primary_key=True, index=True)

    # Topic details
    subject = Column(String(100), nullable=False, index=True)  # Physics, Chemistry, Biology
    unit = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    topic_order = Column(Integer, nullable=True)

    # Grade level range (Sprint 2)
    grade_level = Column(Integer, nullable=True)  # Legacy field
    grade_level_min = Column(Integer, default=9)
    grade_level_max = Column(Integer, default=12)

    # Curriculum metadata (Sprint 2)
    standards = Column(JSON, default=[])  # Common Core, NGSS, etc. (list of standard IDs or dicts)
    prerequisites = Column(JSON, default=[])  # Array of prerequisite topic_ids

    # Metadata
    meta_data = Column(JSON, nullable=True, default={})

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    active = Column(String(10), default="true")

    # Relationships
    student_progress = relationship("StudentProgress", back_populates="topic", cascade="all, delete-orphan")

    # Helper properties for API compatibility
    @property
    def category(self):
        """Alias for unit field."""
        return self.unit

    @property
    def grade_levels(self):
        """Return list of grade levels this topic covers."""
        if self.grade_level_min and self.grade_level_max:
            return list(range(self.grade_level_min, self.grade_level_max + 1))
        return []

    @property
    def difficulty(self):
        """Determine difficulty based on grade level."""
        if self.grade_level_min <= 9:
            return "beginner"
        elif self.grade_level_min <= 10:
            return "intermediate"
        else:
            return "advanced"

    @property
    def estimated_duration_min(self):
        """Estimated duration for topic."""
        return 15  # Default 15 minutes

    @property
    def related_topics(self):
        """Related topics (could be enhanced)."""
        return []

    @property
    def content_available(self):
        """Check if content is available (placeholder)."""
        return True  # TODO: Query content_metadata

    @property
    def popularity_score(self):
        """Popularity score (placeholder)."""
        return 0.5  # TODO: Calculate from student_progress

    @property
    def learning_objectives(self):
        """Learning objectives (placeholder)."""
        return []  # TODO: Store in JSONB

    def __repr__(self) -> str:
        return f"<Topic {self.subject}: {self.name}>"


class StudentProgress(Base):
    """
    StudentProgress model tracking learning progress per topic.

    Corresponds to database table: student_progress
    """

    __tablename__ = "student_progress"

    # Primary key
    progress_id = Column(String(100), primary_key=True, index=True)

    # References
    student_id = Column(String(100), ForeignKey('users.user_id'), nullable=False, index=True)
    topic_id = Column(String(100), ForeignKey('topics.topic_id'), nullable=False, index=True)
    class_id = Column(String(100), ForeignKey('classes.class_id'), nullable=True, index=True)

    # Progress tracking
    status = Column(Enum(ProgressStatus), nullable=False, default=ProgressStatus.NOT_STARTED, index=True)
    progress_percentage = Column(Integer, default=0)

    # Video watching
    videos_watched = Column(Integer, default=0)
    total_watch_time_seconds = Column(Integer, default=0)

    # Completion tracking
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True, index=True)

    # Metadata
    meta_data = Column(JSON, nullable=True, default={})

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="student_progress")
    topic = relationship("Topic", back_populates="student_progress")

    def __repr__(self) -> str:
        return f"<StudentProgress student={self.student_id} topic={self.topic_id} status={self.status}>"


class StudentActivity(Base):
    """
    StudentActivity model for event logging.

    Corresponds to database table: student_activity
    """

    __tablename__ = "student_activity"

    # Primary key
    activity_id = Column(String(100), primary_key=True, index=True)

    # References
    student_id = Column(String(100), ForeignKey('users.user_id'), nullable=False, index=True)
    activity_type = Column(Enum(ActivityType), nullable=False, index=True)

    # Context
    topic_id = Column(String(100), ForeignKey('topics.topic_id'), nullable=True, index=True)
    content_id = Column(String(100), nullable=True)
    class_id = Column(String(100), ForeignKey('classes.class_id'), nullable=True)
    interest_id = Column(String(100), ForeignKey('interests.interest_id'), nullable=True)

    # Details
    duration_seconds = Column(Integer, nullable=True)
    meta_data = Column(JSON, nullable=True, default={})

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<StudentActivity student={self.student_id} type={self.activity_type}>"
