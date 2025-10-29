"""
NLU Service for Topic Extraction (Phase 3 Sprint 1)

Uses Vertex AI Gemini to extract topics from student natural language queries.
Implements intelligent disambiguation and grade-level awareness.
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NLUService:
    """
    Natural Language Understanding service for topic extraction.

    Uses Vertex AI Gemini 1.5 Pro to:
    1. Parse student queries
    2. Map to canonical topics
    3. Handle ambiguity with clarifying questions
    4. Enforce grade-level appropriateness
    """

    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """
        Initialize NLU service with Vertex AI.

        Args:
            project_id: GCP project ID (defaults to env var)
            location: Vertex AI location (default: us-central1)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
        self.location = location
        self.model_name = "gemini-1.5-pro"

        # Try to initialize Vertex AI (will fail gracefully in test env)
        try:
            from google.cloud import aiplatform
            from vertexai.generative_models import GenerativeModel

            aiplatform.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            self.vertex_available = True
            logger.info(f"Vertex AI initialized: {self.project_id}/{self.location}")
        except Exception as e:
            logger.warning(f"Vertex AI not available: {e}. Running in mock mode.")
            self.model = None
            self.vertex_available = False

    async def extract_topic(
        self,
        student_query: str,
        grade_level: int,
        student_id: Optional[str] = None,
        recent_topics: Optional[List[str]] = None,
        subject_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract topic from student natural language query.

        Args:
            student_query: Student's question/request
            grade_level: Student's grade level (9-12)
            student_id: Optional student ID for context
            recent_topics: Optional list of recently studied topics
            subject_context: Optional subject hint (Physics, Chemistry, etc.)

        Returns:
            Dict with:
                - confidence: float (0.0-1.0)
                - topic_id: str or None
                - topic_name: str or None
                - clarification_needed: bool
                - clarifying_questions: List[str]
                - out_of_scope: bool
                - reasoning: str

        Example:
            >>> result = await nlu.extract_topic(
            ...     "Explain Newton's Third Law with basketball",
            ...     grade_level=10
            ... )
            >>> print(result["topic_id"])
            "topic_phys_mech_newton_3"
        """
        # Validate input
        if not student_query or len(student_query.strip()) < 3:
            return self._error_response("Query too short (minimum 3 characters)")

        if grade_level not in [9, 10, 11, 12]:
            return self._error_response(f"Invalid grade level: {grade_level}")

        # Mock mode for testing (no Vertex AI)
        if not self.vertex_available:
            return self._mock_extract_topic(student_query, grade_level)

        try:
            # Get grade-appropriate topics
            topics = await self._get_grade_appropriate_topics(grade_level)

            # Build prompt
            prompt = self._build_extraction_prompt(
                student_query=student_query,
                topics=topics,
                grade_level=grade_level,
                recent_topics=recent_topics or [],
                subject_context=subject_context
            )

            # Call Gemini with retry
            response_text = await self._call_gemini_with_retry(prompt)

            # Parse JSON response
            result = self._parse_gemini_response(response_text)

            # Validate topic_id if present
            if result.get("topic_id"):
                is_valid = await self._validate_topic_id(
                    result["topic_id"],
                    grade_level
                )
                if not is_valid:
                    logger.warning(f"Invalid topic_id: {result['topic_id']}")
                    result["topic_id"] = None
                    result["clarification_needed"] = True
                    result["clarifying_questions"] = [
                        "Could you rephrase your question?",
                        "Which subject are you studying?"
                    ]

            return result

        except Exception as e:
            logger.error(f"NLU extraction failed: {e}", exc_info=True)
            return self._fallback_response(student_query)

    def _build_extraction_prompt(
        self,
        student_query: str,
        topics: List[Dict],
        grade_level: int,
        recent_topics: List[str],
        subject_context: Optional[str]
    ) -> str:
        """Build prompt for Gemini topic extraction."""

        # Format topics as JSON for prompt
        topics_json = json.dumps(topics, indent=2)

        # Format recent topics
        recent_str = ", ".join(recent_topics) if recent_topics else "None"

        # Subject context
        subject_str = subject_context if subject_context else "Any STEM subject"

        prompt = f"""You are an educational AI assistant specializing in high school STEM subjects.

Your task is to analyze student queries and map them to standardized educational topics.

Available Topics (Grade {grade_level}):
{topics_json}

Student Information:
- Grade Level: {grade_level}
- Subject Context: {subject_str}
- Previous Topics: {recent_str}

Instructions:
1. Identify the primary academic concept in the query
2. Map to ONE of the available topic_ids above
3. If ambiguous, set clarification_needed=true and provide questions
4. If completely off-topic (non-academic), set out_of_scope=true
5. Consider grade-appropriateness (Grade {grade_level})
6. Respond ONLY with valid JSON (no markdown, no explanation)

Output Format (JSON only):
{{
  "confidence": 0.95,
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "clarification_needed": false,
  "clarifying_questions": [],
  "out_of_scope": false,
  "reasoning": "Clear reference to Newton's Third Law"
}}

Few-Shot Examples:

Query: "Explain Newton's Third Law using basketball"
Response: {{"confidence": 0.98, "topic_id": "topic_phys_mech_newton_3", "topic_name": "Newton's Third Law", "clarification_needed": false, "clarifying_questions": [], "out_of_scope": false, "reasoning": "Clear reference to Newton's Third Law in physics"}}

Query: "Tell me about gravity"
Response: {{"confidence": 0.65, "topic_id": null, "topic_name": null, "clarification_needed": true, "clarifying_questions": ["Are you interested in Newton's Law of Universal Gravitation?", "Or gravitational acceleration on Earth?"], "out_of_scope": false, "reasoning": "Multiple valid interpretations"}}

Query: "What's the best pizza place?"
Response: {{"confidence": 0.99, "topic_id": null, "topic_name": null, "clarification_needed": false, "clarifying_questions": [], "out_of_scope": true, "reasoning": "Not related to STEM education"}}

Now analyze this student query:
Query: "{student_query}"

Respond with JSON only:"""

        return prompt

    async def _call_gemini_with_retry(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> str:
        """
        Call Gemini API with exponential backoff retry.

        Args:
            prompt: Prompt text
            max_retries: Maximum retry attempts

        Returns:
            Response text from Gemini
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,  # Low for consistency
                        "top_p": 0.8,
                        "top_k": 40,
                        "max_output_tokens": 512,
                    }
                )
                return response.text

            except Exception as e:
                if attempt == max_retries - 1:
                    raise

                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Gemini API error (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(wait_time)

    def _parse_gemini_response(self, response_text: str) -> Dict:
        """
        Parse JSON from Gemini response.

        Handles markdown code blocks and extracts JSON.
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        # Find JSON boundaries
        json_start = text.find('{')
        json_end = text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            raise ValueError(f"No JSON found in response: {response_text[:200]}")

        json_str = text[json_start:json_end]

        try:
            result = json.loads(json_str)

            # Validate required fields
            required_fields = ["confidence", "topic_id", "clarification_needed", "out_of_scope"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nResponse: {json_str}")
            raise

    async def _get_grade_appropriate_topics(self, grade_level: int) -> List[Dict]:
        """
        Get topics appropriate for student's grade level.

        In production, this would query the database.
        For now, returns sample topics.
        """
        # Sample topics for demonstration
        all_topics = [
            {
                "topic_id": "topic_phys_mech_newton_1",
                "name": "Newton's First Law",
                "subject": "Physics",
                "grade_levels": [9, 10, 11, 12],
                "keywords": ["inertia", "motion", "force", "rest"]
            },
            {
                "topic_id": "topic_phys_mech_newton_2",
                "name": "Newton's Second Law",
                "subject": "Physics",
                "grade_levels": [9, 10, 11, 12],
                "keywords": ["force", "mass", "acceleration", "F=ma"]
            },
            {
                "topic_id": "topic_phys_mech_newton_3",
                "name": "Newton's Third Law",
                "subject": "Physics",
                "grade_levels": [9, 10, 11, 12],
                "keywords": ["action", "reaction", "force pairs", "equal opposite"]
            },
            {
                "topic_id": "topic_phys_energy_kinetic",
                "name": "Kinetic Energy",
                "subject": "Physics",
                "grade_levels": [10, 11, 12],
                "keywords": ["KE", "energy", "motion", "velocity", "1/2mv²"]
            },
            {
                "topic_id": "topic_chem_atoms_structure",
                "name": "Atomic Structure",
                "subject": "Chemistry",
                "grade_levels": [9, 10, 11, 12],
                "keywords": ["protons", "neutrons", "electrons", "nucleus"]
            }
        ]

        # Filter by grade level
        grade_topics = [
            t for t in all_topics
            if grade_level in t["grade_levels"]
        ]

        return grade_topics

    async def _validate_topic_id(self, topic_id: str, grade_level: int) -> bool:
        """
        Validate that topic_id exists and is appropriate for grade.

        In production, queries database.
        """
        topics = await self._get_grade_appropriate_topics(grade_level)
        valid_ids = {t["topic_id"] for t in topics}
        return topic_id in valid_ids

    def _mock_extract_topic(self, student_query: str, grade_level: int) -> Dict:
        """
        Mock topic extraction for testing (no Vertex AI required).

        Uses simple keyword matching.
        """
        query_lower = student_query.lower()

        # Simple keyword matching
        if "newton" in query_lower and "third" in query_lower:
            return {
                "confidence": 0.95,
                "topic_id": "topic_phys_mech_newton_3",
                "topic_name": "Newton's Third Law",
                "clarification_needed": False,
                "clarifying_questions": [],
                "out_of_scope": False,
                "reasoning": "Matched keywords: newton, third"
            }
        elif "newton" in query_lower and "second" in query_lower:
            return {
                "confidence": 0.95,
                "topic_id": "topic_phys_mech_newton_2",
                "topic_name": "Newton's Second Law",
                "clarification_needed": False,
                "clarifying_questions": [],
                "out_of_scope": False,
                "reasoning": "Matched keywords: newton, second"
            }
        elif "newton" in query_lower:
            return {
                "confidence": 0.70,
                "topic_id": None,
                "topic_name": None,
                "clarification_needed": True,
                "clarifying_questions": [
                    "Which Newton's Law? First, Second, or Third?",
                    "Or Newton's Law of Universal Gravitation?"
                ],
                "out_of_scope": False,
                "reasoning": "Ambiguous - multiple Newton topics"
            }
        elif any(word in query_lower for word in ["pizza", "movie", "game", "music"]):
            return {
                "confidence": 0.99,
                "topic_id": None,
                "topic_name": None,
                "clarification_needed": False,
                "clarifying_questions": [],
                "out_of_scope": True,
                "reasoning": "Non-academic query"
            }
        else:
            return {
                "confidence": 0.50,
                "topic_id": None,
                "topic_name": None,
                "clarification_needed": True,
                "clarifying_questions": [
                    "Could you be more specific about which topic you'd like to learn?",
                    "Which subject are you studying? (Physics, Chemistry, Biology, Math)"
                ],
                "out_of_scope": False,
                "reasoning": "Unclear query - need more information"
            }

    def _fallback_response(self, student_query: str) -> Dict:
        """Fallback response when NLU fails."""
        return {
            "confidence": 0.0,
            "topic_id": None,
            "topic_name": None,
            "clarification_needed": True,
            "clarifying_questions": [
                "I'm having trouble understanding your question.",
                "Could you rephrase it or provide more details?",
                "Which subject are you studying?"
            ],
            "out_of_scope": False,
            "reasoning": "NLU service temporarily unavailable"
        }

    def _error_response(self, error_message: str) -> Dict:
        """Error response for invalid input."""
        return {
            "confidence": 0.0,
            "topic_id": None,
            "topic_name": None,
            "clarification_needed": True,
            "clarifying_questions": [error_message],
            "out_of_scope": False,
            "reasoning": "Invalid input"
        }


# Singleton instance (lazy-loaded)
_nlu_service_instance = None


def get_nlu_service() -> NLUService:
    """Get singleton NLU service instance."""
    global _nlu_service_instance
    if _nlu_service_instance is None:
        _nlu_service_instance = NLUService()
    return _nlu_service_instance
