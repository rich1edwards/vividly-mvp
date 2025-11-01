"""
NLU API Schemas (Phase 3 Sprint 1)

Pydantic models for Natural Language Understanding endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class TopicExtractionRequest(BaseModel):
    """Request to extract topic from student query."""

    query: str = Field(
        ...,
        description="Student's natural language query",
        min_length=3,
        max_length=500,
    )
    grade_level: int = Field(
        ..., description="Student's grade level (9-12)", ge=9, le=12
    )
    student_id: Optional[str] = Field(
        None, description="Optional student ID for context"
    )
    recent_topics: Optional[List[str]] = Field(
        default_factory=list, description="Recently studied topic IDs"
    )
    subject_context: Optional[str] = Field(
        None, description="Subject hint (Physics, Chemistry, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Explain Newton's Third Law using basketball",
                "grade_level": 10,
                "student_id": "user_abc123",
                "recent_topics": [
                    "topic_phys_mech_newton_1",
                    "topic_phys_mech_newton_2",
                ],
                "subject_context": "Physics",
            }
        }


class TopicExtractionResponse(BaseModel):
    """Response from topic extraction."""

    confidence: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    topic_id: Optional[str] = Field(None, description="Extracted topic ID if confident")
    topic_name: Optional[str] = Field(None, description="Human-readable topic name")
    clarification_needed: bool = Field(
        ..., description="Whether clarification is needed"
    )
    clarifying_questions: List[str] = Field(
        default_factory=list, description="Questions to help clarify"
    )
    out_of_scope: bool = Field(..., description="Whether query is non-academic")
    reasoning: str = Field(..., description="Explanation of extraction decision")

    class Config:
        json_schema_extra = {
            "example": {
                "confidence": 0.98,
                "topic_id": "topic_phys_mech_newton_3",
                "topic_name": "Newton's Third Law",
                "clarification_needed": False,
                "clarifying_questions": [],
                "out_of_scope": False,
                "reasoning": "Clear reference to Newton's Third Law with basketball context",
            }
        }


class ClarificationRequest(BaseModel):
    """Request with clarification answer."""

    original_query: str = Field(..., description="Original student query")
    clarification_answer: str = Field(
        ..., description="Student's answer to clarifying question"
    )
    grade_level: int = Field(..., description="Student's grade level", ge=9, le=12)
    previous_extraction: Optional[dict] = Field(
        None, description="Previous extraction result"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "Tell me about gravity",
                "clarification_answer": "Newton's Law of Universal Gravitation",
                "grade_level": 11,
                "previous_extraction": {
                    "confidence": 0.65,
                    "clarification_needed": True,
                },
            }
        }


class TopicSuggestionRequest(BaseModel):
    """Request for topic suggestions."""

    grade_level: int = Field(..., description="Student's grade level", ge=9, le=12)
    subject: Optional[str] = Field(None, description="Subject filter")
    recent_topics: Optional[List[str]] = Field(
        default_factory=list, description="Recently studied topics"
    )
    limit: int = Field(default=5, description="Number of suggestions", ge=1, le=20)

    class Config:
        json_schema_extra = {
            "example": {
                "grade_level": 10,
                "subject": "Physics",
                "recent_topics": ["topic_phys_mech_newton_1"],
                "limit": 5,
            }
        }


class TopicSuggestion(BaseModel):
    """Suggested topic."""

    topic_id: str = Field(..., description="Topic ID")
    topic_name: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject")
    difficulty: str = Field(..., description="Difficulty level")
    relevance_score: float = Field(..., description="Relevance to student (0.0-1.0)")
    reason: str = Field(..., description="Why this topic is suggested")


class TopicSuggestionsResponse(BaseModel):
    """Response with topic suggestions."""

    suggestions: List[TopicSuggestion] = Field(..., description="Suggested topics")
    total_suggestions: int = Field(..., description="Total suggestions available")

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "topic_id": "topic_phys_mech_newton_2",
                        "topic_name": "Newton's Second Law",
                        "subject": "Physics",
                        "difficulty": "intermediate",
                        "relevance_score": 0.95,
                        "reason": "Natural progression after Newton's First Law",
                    }
                ],
                "total_suggestions": 5,
            }
        }
