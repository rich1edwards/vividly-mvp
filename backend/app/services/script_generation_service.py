"""
Script Generation Service (Phase 3 Sprint 2)

Generates personalized educational video scripts using LearnLM/Gemini.
Incorporates RAG-retrieved content and student interests.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ScriptGenerationService:
    """
    Educational script generation service using LearnLM.

    Generates personalized 2-3 minute video scripts that:
    - Explain educational concepts clearly
    - Incorporate student interests
    - Use grade-appropriate language
    - Include examples and analogies
    """

    def __init__(self, project_id: str = None):
        """
        Initialize script generation service.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")

        # Try to initialize Vertex AI
        try:
            # Modern import pattern (google-cloud-aiplatform >= 1.60.0)
            import vertexai
            from vertexai.generative_models import GenerativeModel

            # Initialize Vertex AI before using models
            vertexai.init(project=self.project_id, location="us-central1")
            # Use Gemini with LearnLM tuning for education
            self.model = GenerativeModel("gemini-1.5-pro")
            self.vertex_available = True
            logger.info("Vertex AI (LearnLM) initialized")
        except Exception as e:
            logger.warning(f"Vertex AI not available: {e}. Running in mock mode.")
            self.model = None
            self.vertex_available = False

    async def generate_script(
        self,
        topic_id: str,
        topic_name: str,
        interest: str,
        grade_level: int,
        rag_content: List[Dict],
        duration_seconds: int = 180,
    ) -> Dict[str, Any]:
        """
        Generate personalized educational video script.

        Args:
            topic_id: Canonical topic ID
            topic_name: Human-readable topic name
            interest: Student interest for personalization
            grade_level: Student's grade level (9-12)
            rag_content: Retrieved OER content from RAG
            duration_seconds: Target video duration (default: 180s = 3min)

        Returns:
            Dict with:
                - script_id: str
                - topic_id: str
                - interest: str
                - title: str
                - hook: str (opening line)
                - sections: List[Dict] (script segments)
                - key_takeaways: List[str]
                - duration_estimate_seconds: int
                - generated_at: str (ISO timestamp)

        Example:
            >>> script = await generator.generate_script(
            ...     "topic_phys_mech_newton_3",
            ...     "Newton's Third Law",
            ...     "basketball",
            ...     10,
            ...     rag_content=[...]
            ... )
        """
        if not self.vertex_available:
            return self._mock_generate_script(
                topic_id, topic_name, interest, grade_level, duration_seconds
            )

        try:
            # Build prompt with RAG context
            prompt = self._build_script_prompt(
                topic_name=topic_name,
                interest=interest,
                grade_level=grade_level,
                rag_content=rag_content,
                duration_seconds=duration_seconds,
            )

            # Generate script with Gemini
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,  # Creative but controlled
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                },
            )

            # Parse response
            script = self._parse_script_response(response.text)

            # Add metadata
            script["script_id"] = self._generate_script_id(topic_id, interest)
            script["topic_id"] = topic_id
            script["interest"] = interest
            script["generated_at"] = datetime.utcnow().isoformat()

            return script

        except Exception as e:
            logger.error(f"Script generation failed: {e}", exc_info=True)
            return self._mock_generate_script(
                topic_id, topic_name, interest, grade_level, duration_seconds
            )

    def _build_script_prompt(
        self,
        topic_name: str,
        interest: str,
        grade_level: int,
        rag_content: List[Dict],
        duration_seconds: int,
    ) -> str:
        """Build prompt for script generation."""

        # Format RAG content for context
        context_text = "\n\n".join(
            [f"Source: {c['source']}\n{c['text']}" for c in rag_content]
        )

        prompt = f"""You are an expert educational content creator using LearnLM principles.

Create a {duration_seconds}-second video script explaining {topic_name} for Grade {grade_level} students.

**Personalization**: The student is interested in {interest}. Use this interest to create relatable examples and analogies.

**Educational Context**:
{context_text}

**Requirements**:
1. Start with an engaging hook related to {interest}
2. Break content into 3-4 clear sections
3. Use grade-appropriate language (Grade {grade_level})
4. Include concrete examples from {interest}
5. End with 3 key takeaways
6. Target duration: {duration_seconds} seconds (~150 words/minute)
7. Make it engaging, clear, and memorable

**Output Format** (JSON only):
{{
  "title": "Newton's Third Law in Basketball",
  "hook": "Ever wonder why basketball players jump so high? It's all about Newton's Third Law!",
  "sections": [
    {{
      "title": "What is Newton's Third Law?",
      "content": "For every action, there's an equal and opposite reaction...",
      "duration_seconds": 45,
      "visuals": ["Animation of force pairs", "Basketball player jumping"]
    }},
    {{
      "title": "How It Works in Basketball",
      "content": "When a player pushes down on the court...",
      "duration_seconds": 60,
      "visuals": ["Slow-motion jump shot", "Force diagram"]
    }}
  ],
  "key_takeaways": [
    "Forces always come in pairs",
    "Action and reaction forces are equal in magnitude",
    "In basketball, you push down to jump up"
  ],
  "duration_estimate_seconds": 180
}}

Generate the script (JSON only, no markdown):"""

        return prompt

    def _parse_script_response(self, response_text: str) -> Dict:
        """Parse script JSON from response."""
        # Remove markdown if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Extract JSON
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start == -1:
            raise ValueError("No JSON found in response")

        json_str = text[json_start:json_end]
        return json.loads(json_str)

    def _mock_generate_script(
        self,
        topic_id: str,
        topic_name: str,
        interest: str,
        grade_level: int,
        duration_seconds: int,
    ) -> Dict:
        """Mock script generation for testing."""

        script_id = self._generate_script_id(topic_id, interest)

        return {
            "script_id": script_id,
            "topic_id": topic_id,
            "interest": interest,
            "title": f"{topic_name} Explained Through {interest.title()}",
            "hook": f"Ever wonder how {topic_name.lower()} relates to {interest}? Let's find out!",
            "sections": [
                {
                    "title": f"Introduction to {topic_name}",
                    "content": f"Let's explore {topic_name} using examples from {interest} that you know and love.",
                    "duration_seconds": 45,
                    "visuals": [f"{interest} action shot", "Concept diagram"],
                },
                {
                    "title": "The Core Concept",
                    "content": f"The key idea behind {topic_name} is fascinating. Let me explain it step by step.",
                    "duration_seconds": 60,
                    "visuals": ["Animated diagram", "Real-world example"],
                },
                {
                    "title": f"How It Works in {interest.title()}",
                    "content": f"Now let's see how {topic_name} applies directly to {interest}. This is where it gets really interesting!",
                    "duration_seconds": 60,
                    "visuals": [f"{interest} slow-motion", "Force analysis"],
                },
                {
                    "title": "Summary and Key Points",
                    "content": f"Let's recap what we've learned about {topic_name} and how it connects to {interest}.",
                    "duration_seconds": 15,
                    "visuals": ["Key points on screen"],
                },
            ],
            "key_takeaways": [
                f"{topic_name} is a fundamental concept in science",
                f"You can see it in action during {interest}",
                "Understanding this helps you appreciate both science and sports",
            ],
            "duration_estimate_seconds": duration_seconds,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _generate_script_id(self, topic_id: str, interest: str) -> str:
        """Generate unique script ID."""
        import hashlib

        content = f"{topic_id}|{interest}|{datetime.utcnow().isoformat()}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"script_{hash_val}"


# Singleton instance
_script_gen_service_instance = None


def get_script_generation_service() -> ScriptGenerationService:
    """Get singleton script generation service instance."""
    global _script_gen_service_instance
    if _script_gen_service_instance is None:
        _script_gen_service_instance = ScriptGenerationService()
    return _script_gen_service_instance
