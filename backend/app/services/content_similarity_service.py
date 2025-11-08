"""
Content Similarity Detection Service.

Phase 1.2.2: Similar Content Detection
Detects similar existing content to help students discover relevant videos
and reduce unnecessary duplicate content generation.
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.content_metadata import ContentMetadata, GenerationStatus

logger = logging.getLogger(__name__)


class ContentSimilarityService:
    """
    Service for detecting similar content using multi-factor similarity algorithm.

    Similarity Scoring Algorithm (matches frontend RelatedVideosSidebar.tsx):
    - Same topic: +50 points
    - Same subject/interest: +30 points
    - Shared keywords: +10 points per keyword (extracted from title/description)
    - Recency bonus: +5 points for content from last 7 days
    - Completion status: Only completed videos are considered

    Thresholds:
    - High similarity (>=60): Very likely the same content
    - Medium similarity (40-59): Related content worth showing
    - Low similarity (<40): Not similar enough to show
    """

    # Similarity thresholds
    HIGH_SIMILARITY_THRESHOLD = 60
    MEDIUM_SIMILARITY_THRESHOLD = 40

    # Score weights (must match frontend algorithm)
    TOPIC_MATCH_SCORE = 50
    SUBJECT_MATCH_SCORE = 30
    KEYWORD_MATCH_SCORE = 10
    RECENCY_BONUS_SCORE = 5

    def __init__(self):
        """Initialize similarity service."""
        pass

    def calculate_similarity_score(
        self,
        content_a: Dict,
        content_b: ContentMetadata,
    ) -> int:
        """
        Calculate similarity score between query parameters and existing content.

        Args:
            content_a: Dict with keys: topic_id, interest, student_query
            content_b: ContentMetadata database object

        Returns:
            Integer similarity score (0-100+)
        """
        score = 0

        # Topic match: +50 points
        if content_a.get("topic_id") and content_b.topic_id:
            if content_a["topic_id"] == content_b.topic_id:
                score += self.TOPIC_MATCH_SCORE

        # Subject/Interest match: +30 points
        if content_a.get("interest") and content_b.interest:
            # Normalize interest strings for comparison
            interest_a = content_a["interest"].lower().strip()
            interest_b_normalized = content_b.interest.lower().strip() if content_b.interest else ""

            if interest_a == interest_b_normalized:
                score += self.SUBJECT_MATCH_SCORE

        # Keyword matching: +10 points per shared keyword
        if content_a.get("student_query") and content_b.title:
            keywords_a = self._extract_keywords(content_a["student_query"])
            keywords_b = self._extract_keywords(content_b.title)

            # Also check description if available
            if content_b.description:
                keywords_b.update(self._extract_keywords(content_b.description))

            shared_keywords = keywords_a.intersection(keywords_b)
            score += len(shared_keywords) * self.KEYWORD_MATCH_SCORE

        # Recency bonus: +5 points for recent content (last 7 days)
        if content_b.created_at:
            from datetime import datetime, timedelta
            days_since = (datetime.utcnow() - content_b.created_at).days
            if days_since <= 7:
                score += self.RECENCY_BONUS_SCORE

        return score

    def _extract_keywords(self, text: str) -> set:
        """
        Extract meaningful keywords from text.

        Args:
            text: Input text string

        Returns:
            Set of normalized keywords (lowercase, stripped)
        """
        # Simple keyword extraction: split by spaces, remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "about", "what",
            "how", "why", "when", "where", "who", "which", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
            "her", "us", "them", "my", "your", "his", "its", "our", "their"
        }

        # Normalize and filter
        words = text.lower().split()
        keywords = {
            word.strip(",.!?;:\"'()[]{}")
            for word in words
            if len(word) > 3 and word.lower() not in stop_words
        }

        return keywords

    def find_similar_content(
        self,
        db: Session,
        topic_id: Optional[str] = None,
        interest: Optional[str] = None,
        student_query: Optional[str] = None,
        student_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict]:
        """
        Find similar existing content based on query parameters.

        Args:
            db: Database session
            topic_id: Topic ID to match
            interest: Interest/subject to match
            student_query: Student's query text for keyword matching
            student_id: Optional student ID to prioritize their own content
            limit: Maximum number of similar items to return (default: 5)

        Returns:
            List of dicts with keys: content, similarity_score, similarity_level
            Sorted by similarity score (highest first)
        """
        try:
            # Build query for candidate content
            # Only search completed content (not pending/generating/failed)
            query = db.query(ContentMetadata).filter(
                ContentMetadata.status == GenerationStatus.COMPLETED.value,
                ContentMetadata.archived == False
            )

            # Optimization: If topic_id provided, pre-filter by topic
            # This reduces the number of items we need to score
            if topic_id:
                query = query.filter(ContentMetadata.topic_id == topic_id)

            # Execute query to get candidates
            candidates = query.all()

            logger.info(f"Found {len(candidates)} candidate videos for similarity check")

            # Calculate similarity scores for each candidate
            scored_results = []
            query_params = {
                "topic_id": topic_id,
                "interest": interest,
                "student_query": student_query,
            }

            for content in candidates:
                similarity_score = self.calculate_similarity_score(
                    query_params, content
                )

                # Only include content above low threshold
                if similarity_score >= self.MEDIUM_SIMILARITY_THRESHOLD:
                    # Determine similarity level
                    if similarity_score >= self.HIGH_SIMILARITY_THRESHOLD:
                        similarity_level = "high"
                    else:
                        similarity_level = "medium"

                    # Boost score if this is the student's own content
                    is_own_content = False
                    if student_id and content.student_id == student_id:
                        is_own_content = True
                        similarity_score += 5  # Small boost for own content

                    scored_results.append({
                        "content": content,
                        "similarity_score": similarity_score,
                        "similarity_level": similarity_level,
                        "is_own_content": is_own_content,
                    })

            # Sort by similarity score (highest first) and limit results
            scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            similar_content = scored_results[:limit]

            logger.info(
                f"Found {len(similar_content)} similar videos "
                f"(scores: {[r['similarity_score'] for r in similar_content]})"
            )

            return similar_content

        except Exception as e:
            logger.error(f"Error finding similar content: {e}", exc_info=True)
            return []

    def format_similarity_result(self, result: Dict) -> Dict:
        """
        Format similarity result for API response.

        Args:
            result: Dict from find_similar_content()

        Returns:
            Dict with API-friendly format
        """
        content = result["content"]

        return {
            "content_id": content.content_id,
            "cache_key": content.cache_key,
            "title": content.title,
            "description": content.description,
            "topic_id": content.topic_id,
            "topic_name": content.topic_rel.name if content.topic_rel else content.topic_id,
            "interest": content.interest,
            "video_url": content.video_url,
            "thumbnail_url": content.thumbnail_url,
            "duration_seconds": content.duration_seconds,
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "views": content.views,
            "average_rating": float(content.average_rating) if content.average_rating else None,
            "similarity_score": result["similarity_score"],
            "similarity_level": result["similarity_level"],
            "is_own_content": result["is_own_content"],
        }


# Singleton instance
_similarity_service = None


def get_similarity_service() -> ContentSimilarityService:
    """
    Get singleton instance of ContentSimilarityService.

    Returns:
        ContentSimilarityService instance
    """
    global _similarity_service
    if _similarity_service is None:
        _similarity_service = ContentSimilarityService()
    return _similarity_service
