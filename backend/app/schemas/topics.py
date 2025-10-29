"""
Pydantic schemas for topics and interests operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Topic Schemas

class TopicSummary(BaseModel):
    """Basic topic information."""
    topic_id: str
    name: str
    subject: str
    category: Optional[str]
    grade_levels: List[int]
    difficulty: Optional[str]
    description: Optional[str]
    estimated_duration_min: Optional[int]
    prerequisites: List[str]
    standards: List[str]
    content_available: bool = False
    popularity_score: float = 0.0

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    """Paginated topic list response."""
    topics: List[TopicSummary]
    pagination: dict


class PrerequisiteInfo(BaseModel):
    """Prerequisite topic information."""
    topic_id: str
    name: str
    completed: bool
    completed_at: Optional[datetime] = None


class RelatedTopicInfo(BaseModel):
    """Related topic information."""
    topic_id: str
    name: str


class StandardInfo(BaseModel):
    """Educational standard information."""
    standard_id: str
    description: str
    source: str


class TopicDetailResponse(BaseModel):
    """Detailed topic information."""
    topic_id: str
    name: str
    subject: str
    category: Optional[str]
    grade_levels: List[int]
    difficulty: Optional[str]
    description: Optional[str]
    learning_objectives: List[str]
    prerequisites: List[PrerequisiteInfo]
    related_topics: List[RelatedTopicInfo]
    standards: List[dict]
    estimated_duration_min: Optional[int]
    content_available: bool
    available_interests: List[str]
    popularity_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class TopicSearchResult(BaseModel):
    """Search result for a topic."""
    topic_id: str
    name: str
    relevance_score: float
    highlights: List[str] = []
    subject: str
    category: Optional[str]


class TopicSearchResponse(BaseModel):
    """Topic search response."""
    query: str
    results: List[dict]
    total_results: int


# Interest Schemas

class InterestInfo(BaseModel):
    """Interest information."""
    interest_id: str
    name: str
    category: str
    icon_url: Optional[str]
    description: Optional[str]
    popularity: float
    content_count: int


class InterestListResponse(BaseModel):
    """Interest list response."""
    interests: List[dict]
    total_count: int
    categories: List[str]


class InterestCategoryInfo(BaseModel):
    """Interest category information."""
    category_id: str
    name: str
    description: str
    icon_url: Optional[str]
    interest_count: int
    interests: List[dict]


class InterestCategoryListResponse(BaseModel):
    """Interest category list response."""
    categories: List[dict]
