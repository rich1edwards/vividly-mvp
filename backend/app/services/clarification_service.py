"""
Clarification Service - Fast synchronous pre-check for obvious clarification cases.

This service provides IMMEDIATE clarification feedback for obvious cases,
before the request even reaches the worker. This improves UX by giving instant feedback.

Architecture Decision (Andrew Ng's pragmatic approach):
- Full LLM-based clarification happens in the worker (deep analysis)
- This service handles OBVIOUS cases synchronously (simple rules)
- Trade-off: Simple rules may miss edge cases, but provides instant UX feedback
"""
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ClarificationService:
    """Fast rule-based clarification detection."""

    # Vague queries that clearly need clarification
    VAGUE_PATTERNS = [
        r"^\s*tell me about\s+\w+\s*$",  # "tell me about science"
        r"^\s*explain\s+\w+\s*$",  # "explain math"
        r"^\s*what is\s+\w+\s*\??$",  # "what is biology?"
        r"^\s*teach me\s+\w+\s*$",  # "teach me history"
        r"^\s*i want to learn\s+\w+\s*$",  # "I want to learn coding"
        r"^\s*help with\s+\w+\s*$",  # "help with chemistry"
    ]

    # Minimum word count for a clear query
    MIN_CLEAR_QUERY_WORDS = 8

    def check_clarification_needed(
        self,
        student_query: str,
        grade_level: Optional[int] = None,
    ) -> Dict:
        """
        Fast synchronous check if query needs clarification.

        Returns:
            {
                "needs_clarification": bool,
                "clarifying_questions": List[str],  # Empty if not needed
                "reasoning": str,  # Why clarification is needed
            }
        """
        query_lower = student_query.lower().strip()

        # Rule 1: Check for vague patterns
        for pattern in self.VAGUE_PATTERNS:
            if re.match(pattern, query_lower):
                return self._generate_clarification_response(
                    student_query,
                    "Query is too vague or general",
                    grade_level,
                )

        # Rule 2: Check query length (word count)
        word_count = len(student_query.split())
        if word_count < self.MIN_CLEAR_QUERY_WORDS:
            return self._generate_clarification_response(
                student_query,
                f"Query is too brief ({word_count} words, need at least {self.MIN_CLEAR_QUERY_WORDS})",
                grade_level,
            )

        # Rule 3: Check for single-word queries
        if word_count == 1:
            return self._generate_clarification_response(
                student_query,
                "Single-word query needs more context",
                grade_level,
            )

        # Query seems clear enough for now
        # (Worker will do deep analysis if needed)
        return {
            "needs_clarification": False,
            "clarifying_questions": [],
            "reasoning": "Query appears sufficiently specific",
        }

    def _generate_clarification_response(
        self,
        query: str,
        reasoning: str,
        grade_level: Optional[int],
    ) -> Dict:
        """Generate clarification questions based on the vague query."""

        # Extract the topic from the query
        words = query.lower().split()

        # Find potential subject words (skip common words)
        skip_words = {
            "tell",
            "me",
            "about",
            "what",
            "is",
            "explain",
            "teach",
            "help",
            "with",
            "i",
            "want",
            "to",
            "learn",
            "a",
            "an",
            "the",
        }
        topic_words = [w for w in words if w not in skip_words]
        topic = topic_words[0] if topic_words else "this topic"

        # Generate questions
        questions = [
            f"What specific aspect of {topic} would you like to learn about?",
            f"Are you looking for an introduction, or do you have a specific question about {topic}?",
            "Can you provide more details about what you're trying to understand?",
        ]

        logger.info(
            f"Clarification needed for query: '{query}' - Reason: {reasoning}"
        )

        return {
            "needs_clarification": True,
            "clarifying_questions": questions,
            "reasoning": reasoning,
        }


# Global instance
_clarification_service: Optional[ClarificationService] = None


def get_clarification_service() -> ClarificationService:
    """Get singleton clarification service instance."""
    global _clarification_service
    if _clarification_service is None:
        _clarification_service = ClarificationService()
    return _clarification_service
