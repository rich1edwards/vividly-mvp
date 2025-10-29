"""
Content Library Database Models

Stores OER content chunks with metadata for RAG retrieval.
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

from app.models.base import Base


class ContentChunk(Base):
    """
    Represents a chunk of educational content from OER sources.

    Each chunk is a semantically meaningful section of content
    that can be retrieved and used for RAG-based generation.
    """
    __tablename__ = "content_chunks"

    # Primary key
    chunk_id = Column(String(64), primary_key=True)

    # Source metadata
    source_title = Column(String(255), nullable=False)  # "College Physics 2e"
    source_author = Column(String(255), nullable=False)  # "OpenStax"
    source_url = Column(String(512), nullable=False)
    source_license = Column(String(50), nullable=False)  # "CC BY 4.0"

    # Content hierarchy
    subject = Column(String(50), nullable=False, index=True)  # physics, chemistry, biology
    chapter = Column(String(255), nullable=False)  # "Chapter 4: Dynamics"
    section = Column(String(255), nullable=False)  # "4.3 Newton's Third Law"
    subsection = Column(String(255), nullable=True)

    # Topic mapping (links to topics table)
    topic_ids = Column(ARRAY(String), nullable=False, index=True)  # ["topic_phys_mech_newton_3"]

    # Content
    text = Column(Text, nullable=False)  # The actual content text
    cleaned_text = Column(Text, nullable=False)  # Cleaned version for embedding

    # Metadata for context
    word_count = Column(Integer, nullable=False)
    reading_level = Column(Integer, nullable=True)  # Flesch-Kincaid grade level

    # Images and figures
    figure_urls = Column(ARRAY(String), nullable=True)  # URLs to related figures
    equations = Column(ARRAY(String), nullable=True)  # LaTeX equations in chunk

    # Keywords and concepts
    keywords = Column(ARRAY(String), nullable=False, index=True)
    concepts = Column(ARRAY(String), nullable=False)  # Main concepts covered

    # Quality metrics
    quality_score = Column(Float, nullable=True)  # 0.0-1.0, content quality
    relevance_threshold = Column(Float, nullable=True)  # Minimum relevance for retrieval

    # Embedding (stored separately in vector database)
    embedding_id = Column(String(64), nullable=True)  # Reference to vector DB entry
    embedding_model = Column(String(100), nullable=True)  # "text-embedding-gecko@003"

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_content_subject_topic', 'subject', 'topic_ids'),
        Index('idx_content_keywords', 'keywords'),
        Index('idx_content_quality', 'quality_score'),
    )

    def __repr__(self):
        return f"<ContentChunk(chunk_id='{self.chunk_id}', subject='{self.subject}', section='{self.section}')>"


class ContentSource(Base):
    """
    Tracks OER content sources and ingestion status.
    """
    __tablename__ = "content_sources"

    source_id = Column(String(64), primary_key=True)

    # Source information
    title = Column(String(255), nullable=False)  # "College Physics 2e"
    author = Column(String(255), nullable=False)  # "OpenStax"
    subject = Column(String(50), nullable=False)  # physics, chemistry
    url = Column(String(512), nullable=False)
    license = Column(String(50), nullable=False)  # "CC BY 4.0"

    # Ingestion metadata
    ingestion_status = Column(String(50), nullable=False)  # pending, processing, completed, failed
    chunks_count = Column(Integer, nullable=False, default=0)
    last_ingested_at = Column(DateTime, nullable=True)

    # Version tracking
    source_version = Column(String(50), nullable=True)  # OpenStax version
    last_updated_at = Column(DateTime, nullable=True)

    # Statistics
    total_words = Column(Integer, nullable=True)
    total_chapters = Column(Integer, nullable=True)
    total_sections = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ContentSource(source_id='{self.source_id}', title='{self.title}', status='{self.ingestion_status}')>"


class VectorIndex(Base):
    """
    Tracks vector index deployments for Vertex AI Matching Engine.
    """
    __tablename__ = "vector_indexes"

    index_id = Column(String(64), primary_key=True)

    # Index metadata
    index_name = Column(String(255), nullable=False)
    index_endpoint = Column(String(512), nullable=True)  # Vertex AI endpoint URL

    # Configuration
    embedding_model = Column(String(100), nullable=False)  # "text-embedding-gecko@003"
    dimensions = Column(Integer, nullable=False)  # 768
    index_type = Column(String(50), nullable=False)  # "tree-ah", "brute-force"

    # Statistics
    total_vectors = Column(Integer, nullable=False, default=0)
    last_updated_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(50), nullable=False)  # creating, ready, updating, failed

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VectorIndex(index_id='{self.index_id}', status='{self.status}', vectors={self.total_vectors})>"
