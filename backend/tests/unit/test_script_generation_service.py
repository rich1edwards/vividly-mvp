"""
Unit tests for script generation service.
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.script_generation_service import (
    ScriptGenerationService,
    get_script_generation_service
)


@pytest.mark.unit
class TestScriptGenerationServiceInitialization:
    """Test service initialization."""

    def test_init_without_vertex_ai(self):
        """Test initialization in mock mode (no Vertex AI)."""
        service = ScriptGenerationService()

        assert service.project_id == "vividly-dev-rich"
        assert service.vertex_available is False
        assert service.model is None

    def test_init_with_custom_project(self):
        """Test initialization with custom project ID."""
        service = ScriptGenerationService(project_id="custom-project")

        assert service.project_id == "custom-project"

    @patch.dict('os.environ', {'GCP_PROJECT_ID': 'env-project'})
    def test_init_with_env_project(self):
        """Test initialization uses env var for project ID."""
        service = ScriptGenerationService()

        assert service.project_id == "env-project"


@pytest.mark.unit
class TestGenerateScript:
    """Test script generation."""

    @pytest.mark.asyncio
    async def test_generate_script_mock_mode(self):
        """Test script generation in mock mode."""
        service = ScriptGenerationService()

        rag_content = [
            {
                "source": "OpenStax Physics",
                "text": "Newton's Third Law states that for every action..."
            }
        ]

        script = await service.generate_script(
            topic_id="topic_phys_mech_newton_3",
            topic_name="Newton's Third Law",
            interest="basketball",
            grade_level=10,
            rag_content=rag_content,
            duration_seconds=180
        )

        assert script["script_id"].startswith("script_")
        assert script["topic_id"] == "topic_phys_mech_newton_3"
        assert script["interest"] == "basketball"
        assert "title" in script
        assert "basketball" in script["title"].lower()
        assert "hook" in script
        assert len(script["sections"]) > 0
        assert len(script["key_takeaways"]) > 0
        assert script["duration_estimate_seconds"] == 180

    @pytest.mark.asyncio
    async def test_generate_script_different_interests(self):
        """Test script generation with different interests."""
        service = ScriptGenerationService()

        rag_content = [{"source": "Test", "text": "Content"}]

        # Test with soccer
        script1 = await service.generate_script(
            topic_id="topic_phys_mech_newton_3",
            topic_name="Newton's Third Law",
            interest="soccer",
            grade_level=10,
            rag_content=rag_content
        )

        assert "soccer" in script1["title"].lower()

        # Test with dance
        script2 = await service.generate_script(
            topic_id="topic_phys_mech_newton_3",
            topic_name="Newton's Third Law",
            interest="dance",
            grade_level=10,
            rag_content=rag_content
        )

        assert "dance" in script2["title"].lower()

    @pytest.mark.asyncio
    async def test_generate_script_different_durations(self):
        """Test script generation with different durations."""
        service = ScriptGenerationService()

        rag_content = [{"source": "Test", "text": "Content"}]

        # Short video
        script1 = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="basketball",
            grade_level=10,
            rag_content=rag_content,
            duration_seconds=120
        )

        assert script1["duration_estimate_seconds"] == 120

        # Long video
        script2 = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="basketball",
            grade_level=10,
            rag_content=rag_content,
            duration_seconds=300
        )

        assert script2["duration_estimate_seconds"] == 300

    @pytest.mark.asyncio
    async def test_generate_script_sections_structure(self):
        """Test that generated script has proper sections structure."""
        service = ScriptGenerationService()

        script = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="basketball",
            grade_level=10,
            rag_content=[{"source": "Test", "text": "Content"}]
        )

        for section in script["sections"]:
            assert "title" in section
            assert "content" in section
            assert "duration_seconds" in section
            assert "visuals" in section
            assert isinstance(section["visuals"], list)

    @pytest.mark.asyncio
    async def test_generate_script_key_takeaways(self):
        """Test that script includes key takeaways."""
        service = ScriptGenerationService()

        script = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="basketball",
            grade_level=10,
            rag_content=[{"source": "Test", "text": "Content"}]
        )

        assert len(script["key_takeaways"]) >= 3
        assert all(isinstance(takeaway, str) for takeaway in script["key_takeaways"])


@pytest.mark.unit
class TestPromptBuilding:
    """Test prompt building."""

    def test_build_script_prompt_basic(self):
        """Test basic prompt building."""
        service = ScriptGenerationService()

        rag_content = [
            {
                "source": "OpenStax Physics",
                "text": "Newton's Third Law states..."
            },
            {
                "source": "Khan Academy",
                "text": "For every action, there is an equal and opposite reaction."
            }
        ]

        prompt = service._build_script_prompt(
            topic_name="Newton's Third Law",
            interest="basketball",
            grade_level=10,
            rag_content=rag_content,
            duration_seconds=180
        )

        assert "Newton's Third Law" in prompt
        assert "basketball" in prompt
        assert "Grade 10" in prompt
        assert "180-second" in prompt
        assert "OpenStax Physics" in prompt
        assert "Khan Academy" in prompt

    def test_build_script_prompt_empty_rag(self):
        """Test prompt building with empty RAG content."""
        service = ScriptGenerationService()

        prompt = service._build_script_prompt(
            topic_name="Test Topic",
            interest="soccer",
            grade_level=11,
            rag_content=[],
            duration_seconds=120
        )

        assert "Test Topic" in prompt
        assert "soccer" in prompt
        assert "Grade 11" in prompt

    def test_build_script_prompt_requirements(self):
        """Test that prompt includes all requirements."""
        service = ScriptGenerationService()

        prompt = service._build_script_prompt(
            topic_name="Test",
            interest="basketball",
            grade_level=10,
            rag_content=[],
            duration_seconds=180
        )

        assert "hook" in prompt.lower()
        assert "sections" in prompt.lower()
        assert "key takeaways" in prompt.lower()
        assert "JSON" in prompt


@pytest.mark.unit
class TestScriptResponseParsing:
    """Test script response parsing."""

    def test_parse_script_response_valid_json(self):
        """Test parsing valid JSON response."""
        service = ScriptGenerationService()

        response = json.dumps({
            "title": "Test Script",
            "hook": "Engaging opening line",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "Content here",
                    "duration_seconds": 60,
                    "visuals": ["Visual 1"]
                }
            ],
            "key_takeaways": ["Point 1", "Point 2"],
            "duration_estimate_seconds": 180
        })

        script = service._parse_script_response(response)

        assert script["title"] == "Test Script"
        assert len(script["sections"]) == 1
        assert len(script["key_takeaways"]) == 2

    def test_parse_script_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        service = ScriptGenerationService()

        response = """```json
{
    "title": "Test",
    "hook": "Hook",
    "sections": [],
    "key_takeaways": [],
    "duration_estimate_seconds": 180
}
```"""

        script = service._parse_script_response(response)

        assert script["title"] == "Test"

    def test_parse_script_response_with_extra_text(self):
        """Test parsing JSON with surrounding text."""
        service = ScriptGenerationService()

        response = """Here's your script:
{
    "title": "Test Script",
    "hook": "Hook",
    "sections": [],
    "key_takeaways": ["Point 1"],
    "duration_estimate_seconds": 120
}
Hope this helps!"""

        script = service._parse_script_response(response)

        assert script["title"] == "Test Script"

    def test_parse_script_response_no_json(self):
        """Test parsing response without JSON."""
        service = ScriptGenerationService()

        response = "This is just plain text without any JSON"

        with pytest.raises(ValueError, match="No JSON found"):
            service._parse_script_response(response)

    def test_parse_script_response_invalid_json(self):
        """Test parsing invalid JSON."""
        service = ScriptGenerationService()

        response = '{"title": "Test", invalid json here}'

        with pytest.raises(json.JSONDecodeError):
            service._parse_script_response(response)


@pytest.mark.unit
class TestMockGeneration:
    """Test mock script generation."""

    def test_mock_generate_script_structure(self):
        """Test mock script has correct structure."""
        service = ScriptGenerationService()

        script = service._mock_generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="basketball",
            grade_level=10,
            duration_seconds=180
        )

        assert script["script_id"].startswith("script_")
        assert script["topic_id"] == "topic_test"
        assert script["interest"] == "basketball"
        assert "title" in script
        assert "hook" in script
        assert "sections" in script
        assert "key_takeaways" in script
        assert "duration_estimate_seconds" in script
        assert "generated_at" in script

    def test_mock_generate_script_sections_count(self):
        """Test mock script has 4 sections."""
        service = ScriptGenerationService()

        script = service._mock_generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="soccer",
            grade_level=11,
            duration_seconds=180
        )

        assert len(script["sections"]) == 4

    def test_mock_generate_script_personalization(self):
        """Test mock script includes interest."""
        service = ScriptGenerationService()

        script = service._mock_generate_script(
            topic_id="topic_test",
            topic_name="Physics Concept",
            interest="skateboarding",
            grade_level=10,
            duration_seconds=180
        )

        title_lower = script["title"].lower()
        assert "skateboarding" in title_lower or "skateboard" in title_lower

    def test_mock_generate_script_key_takeaways(self):
        """Test mock script has 3 key takeaways."""
        service = ScriptGenerationService()

        script = service._mock_generate_script(
            topic_id="topic_test",
            topic_name="Test",
            interest="basketball",
            grade_level=10,
            duration_seconds=180
        )

        assert len(script["key_takeaways"]) == 3


@pytest.mark.unit
class TestScriptIDGeneration:
    """Test script ID generation."""

    def test_generate_script_id_format(self):
        """Test script ID has correct format."""
        service = ScriptGenerationService()

        script_id = service._generate_script_id("topic_test", "basketball")

        assert script_id.startswith("script_")
        assert len(script_id) == 23  # "script_" (7) + 16 hex chars

    def test_generate_script_id_uniqueness(self):
        """Test that script IDs are unique."""
        service = ScriptGenerationService()

        # Generate multiple IDs (they include timestamp so should be unique)
        ids = [
            service._generate_script_id("topic_test", "basketball")
            for _ in range(5)
        ]

        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_generate_script_id_deterministic_prefix(self):
        """Test script IDs always start with 'script_'."""
        service = ScriptGenerationService()

        for _ in range(10):
            script_id = service._generate_script_id("topic_any", "any_interest")
            assert script_id.startswith("script_")


@pytest.mark.unit
class TestSingleton:
    """Test singleton pattern."""

    def test_get_script_generation_service_singleton(self):
        """Test that get function returns singleton."""
        service1 = get_script_generation_service()
        service2 = get_script_generation_service()

        assert service1 is service2

    def test_get_script_generation_service_returns_instance(self):
        """Test that get function returns correct instance."""
        service = get_script_generation_service()

        assert isinstance(service, ScriptGenerationService)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_generate_script_empty_rag_content(self):
        """Test script generation with empty RAG content."""
        service = ScriptGenerationService()

        script = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test Topic",
            interest="basketball",
            grade_level=10,
            rag_content=[],
            duration_seconds=180
        )

        assert "script_id" in script
        assert len(script["sections"]) > 0

    @pytest.mark.asyncio
    async def test_generate_script_very_short_duration(self):
        """Test script generation with very short duration."""
        service = ScriptGenerationService()

        script = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test",
            interest="basketball",
            grade_level=10,
            rag_content=[],
            duration_seconds=60
        )

        assert script["duration_estimate_seconds"] == 60

    @pytest.mark.asyncio
    async def test_generate_script_long_topic_name(self):
        """Test script generation with long topic name."""
        service = ScriptGenerationService()

        long_topic = "Understanding the Fundamental Principles of Advanced Quantum Mechanics"

        script = await service.generate_script(
            topic_id="topic_test",
            topic_name=long_topic,
            interest="basketball",
            grade_level=12,
            rag_content=[],
            duration_seconds=180
        )

        assert long_topic in script["title"]

    @pytest.mark.asyncio
    async def test_generate_script_special_characters_in_interest(self):
        """Test script generation with special characters."""
        service = ScriptGenerationService()

        script = await service.generate_script(
            topic_id="topic_test",
            topic_name="Test",
            interest="rock & roll",
            grade_level=10,
            rag_content=[],
            duration_seconds=180
        )

        assert "script_id" in script

    def test_parse_script_response_nested_objects(self):
        """Test parsing script with nested objects."""
        service = ScriptGenerationService()

        response = json.dumps({
            "title": "Test",
            "hook": "Hook",
            "sections": [
                {
                    "title": "Section 1",
                    "content": "Content",
                    "duration_seconds": 60,
                    "visuals": ["Visual 1", "Visual 2"],
                    "metadata": {
                        "difficulty": "medium",
                        "tags": ["physics", "motion"]
                    }
                }
            ],
            "key_takeaways": ["Point 1"],
            "duration_estimate_seconds": 180
        })

        script = service._parse_script_response(response)

        assert "metadata" in script["sections"][0]
        assert script["sections"][0]["metadata"]["difficulty"] == "medium"
