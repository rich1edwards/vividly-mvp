"""
Content Metadata model for generated video content.
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, Enum as SQLEnum, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class GenerationStatus(str, enum.Enum):
    """Content generation status enum."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ContentMetadata(Base):
    """Content metadata model for generated videos."""

    __tablename__ = "content_metadata"
    __table_args__ = {"extend_existing": True}

    content_id = Column(String(100), primary_key=True)
    request_id = Column(String(100))  # References content_requests

    student_id = Column(String(100), ForeignKey("users.user_id"), nullable=False)
    topic_id = Column(String(100), ForeignKey("topics.topic_id"), nullable=False)
    interest_id = Column(String(100), ForeignKey("interests.interest_id"))

    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Video
    video_url = Column(Text)
    thumbnail_url = Column(Text)
    duration_seconds = Column(Integer)

    # Storage
    gcs_bucket = Column(String(255))
    gcs_path = Column(String(500))
    cdn_url = Column(Text)

    # Status - using VARCHAR since enum types may differ
    status = Column(String(50), nullable=False, default="generating")

    # Generation metadata
    script_content = Column(Text)  # Full script
    generation_metadata = Column(JSON, default={})

    # Stats
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    average_rating = Column(DECIMAL(3, 2))

    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    archived = Column(Boolean, default=False)

    # Relationships
    topic_rel = relationship("Topic", foreign_keys=[topic_id], lazy="select")
    interest_rel = relationship("Interest", foreign_keys=[interest_id], lazy="select")

    # Helper properties for API compatibility
    @property
    def cache_key(self):
        """Cache key for content lookup."""
        return self.content_id

    @property
    def interest(self):
        """Interest name from interest_id."""
        if self.interest_id:
            return self.interest_id.replace("int_", "")
        return None

    @property
    def topic(self):
        """Topic relationship accessor."""
        return self.topic_rel

    @property
    def generated_at(self):
        """Alias for created_at."""
        return self.created_at

    @property
    def views(self):
        """Alias for view_count."""
        return self.view_count or 0

    @property
    def script_url(self):
        """Script URL (placeholder)."""
        if self.script_content:
            return f"https://storage.googleapis.com/{self.gcs_bucket}/{self.gcs_path}/script.json"
        return None

    @property
    def audio_url(self):
        """Audio URL (placeholder)."""
        if self.gcs_bucket and self.gcs_path:
            return f"https://cdn.vividly.edu/{self.gcs_path}/audio.mp3"
        return None

    @property
    def captions_url(self):
        """Captions URL (placeholder)."""
        if self.video_url:
            return f"{self.video_url.rsplit('.', 1)[0]}.vtt"
        return None

    @property
    def quality_levels(self):
        """Available quality levels."""
        if self.video_url:
            return ["1080p", "720p", "480p"]
        return []

    def __repr__(self):
        return f"<ContentMetadata {self.content_id}: {self.title}>"
