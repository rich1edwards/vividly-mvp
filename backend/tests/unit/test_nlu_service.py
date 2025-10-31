"""
Unit tests for NLU service.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List

from app.services.nlu_service import NLUService, get_nlu_service


@pytest.mark.unit
class TestNLUServiceInitialization:
    """Test NLU service initialization."""

    def test_init_without_vertex_ai(self):
        """Test initialization in mock mode (no Vertex AI)."""
        service = NLUService()

        assert service.project_id == "vividly-dev-rich"
        assert service.location == "us-central1"
        assert service.model_name == "gemini-1.5-pro"
        assert service.vertex_available is False
        assert service.model is None

    def test_init_with_custom_project(self):
        """Test initialization with custom project ID."""
        service = NLUService(project_id="custom-project", location="us-west1")

        assert service.project_id == "custom-project"
        assert service.location == "us-west1"

    @patch.dict('os.environ', {'GCP_PROJECT_ID': 'env-project'})
    def test_init_with_env_project(self):
        """Test initialization uses env var for project ID."""
        service = NLUService()

        assert service.project_id == "env-project"


@pytest.mark.unit
class TestExtractTopic:
    """Test topic extraction."""

    @pytest.mark.asyncio
    async def test_extract_topic_query_too_short(self):
        """Test extraction with query too short."""
        service = NLUService()

        result = await service.extract_topic("hi", grade_level=10)

        assert result["confidence"] == 0.0
        assert result["clarification_needed"] is True
        assert "too short" in result["clarifying_questions"][0].lower()

    @pytest.mark.asyncio
    async def test_extract_topic_invalid_grade(self):
        """Test extraction with invalid grade level."""
        service = NLUService()

        result = await service.extract_topic("Newton's laws", grade_level=5)

        assert result["confidence"] == 0.0
        assert result["clarification_needed"] is True
        assert "Invalid grade level" in result["clarifying_questions"][0]

    @pytest.mark.asyncio
    async def test_extract_topic_newton_third_law(self):
        """Test extraction for Newton's Third Law."""
        service = NLUService()

        result = await service.extract_topic(
            "Explain Newton's Third Law with basketball",
            grade_level=10
        )

        assert result["topic_id"] == "topic_phys_mech_newton_3"
        assert result["topic_name"] == "Newton's Third Law"
        assert result["confidence"] == 0.95
        assert result["clarification_needed"] is False
        assert result["out_of_scope"] is False

    @pytest.mark.asyncio
    async def test_extract_topic_newton_second_law(self):
        """Test extraction for Newton's Second Law."""
        service = NLUService()

        result = await service.extract_topic(
            "What is Newton's Second Law?",
            grade_level=11
        )

        assert result["topic_id"] == "topic_phys_mech_newton_2"
        assert result["topic_name"] == "Newton's Second Law"
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_extract_topic_ambiguous_newton(self):
        """Test extraction with ambiguous Newton query."""
        service = NLUService()

        result = await service.extract_topic(
            "Tell me about Newton",
            grade_level=10
        )

        assert result["topic_id"] is None
        assert result["clarification_needed"] is True
        assert len(result["clarifying_questions"]) > 0
        assert result["out_of_scope"] is False
        assert result["confidence"] == 0.70

    @pytest.mark.asyncio
    async def test_extract_topic_out_of_scope(self):
        """Test extraction with out-of-scope query."""
        service = NLUService()

        result = await service.extract_topic(
            "What's the best pizza place?",
            grade_level=10
        )

        assert result["topic_id"] is None
        assert result["out_of_scope"] is True
        assert result["clarification_needed"] is False
        assert result["confidence"] == 0.99

    @pytest.mark.asyncio
    async def test_extract_topic_unclear_query(self):
        """Test extraction with unclear query."""
        service = NLUService()

        result = await service.extract_topic(
            "Help me understand things",
            grade_level=10
        )

        assert result["topic_id"] is None
        assert result["clarification_needed"] is True
        assert len(result["clarifying_questions"]) > 0
        assert result["confidence"] == 0.50

    @pytest.mark.asyncio
    async def test_extract_topic_with_context(self):
        """Test extraction with subject context."""
        service = NLUService()

        result = await service.extract_topic(
            "Explain the third law",
            grade_level=10,
            student_id="student_123",
            recent_topics=["topic_phys_mech_newton_1"],
            subject_context="Physics"
        )

        # Should still work in mock mode
        assert "reasoning" in result


@pytest.mark.unit
class TestPromptBuilding:
    """Test prompt building."""

    def test_build_extraction_prompt_basic(self):
        """Test basic prompt building."""
        service = NLUService()

        topics = [
            {
                "topic_id": "topic_phys_mech_newton_3",
                "name": "Newton's Third Law",
                "subject": "Physics",
                "grade_levels": [9, 10, 11, 12]
            }
        ]

        prompt = service._build_extraction_prompt(
            student_query="What is Newton's Third Law?",
            topics=topics,
            grade_level=10,
            recent_topics=[],
            subject_context=None
        )

        assert "Newton's Third Law" in prompt
        assert "Grade 10" in prompt
        assert "What is Newton's Third Law?" in prompt
        assert "JSON only" in prompt

    def test_build_extraction_prompt_with_context(self):
        """Test prompt building with full context."""
        service = NLUService()

        topics = [{"topic_id": "test", "name": "Test Topic"}]

        prompt = service._build_extraction_prompt(
            student_query="Test query",
            topics=topics,
            grade_level=11,
            recent_topics=["topic_1", "topic_2"],
            subject_context="Physics"
        )

        assert "Physics" in prompt
        assert "topic_1" in prompt
        assert "Grade 11" in prompt


@pytest.mark.unit
class TestGeminiResponseParsing:
    """Test Gemini response parsing."""

    def test_parse_gemini_response_valid_json(self):
        """Test parsing valid JSON response."""
        service = NLUService()

        response = json.dumps({
            "confidence": 0.95,
            "topic_id": "topic_phys_mech_newton_3",
            "clarification_needed": False,
            "out_of_scope": False,
            "reasoning": "Clear match"
        })

        result = service._parse_gemini_response(response)

        assert result["confidence"] == 0.95
        assert result["topic_id"] == "topic_phys_mech_newton_3"

    def test_parse_gemini_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        service = NLUService()

        response = """```json
{
    "confidence": 0.90,
    "topic_id": "topic_test",
    "clarification_needed": false,
    "out_of_scope": false
}
```"""

        result = service._parse_gemini_response(response)

        assert result["confidence"] == 0.90
        assert result["topic_id"] == "topic_test"

    def test_parse_gemini_response_with_extra_text(self):
        """Test parsing JSON with surrounding text."""
        service = NLUService()

        response = """Here's the result:
{
    "confidence": 0.85,
    "topic_id": null,
    "clarification_needed": true,
    "out_of_scope": false
}
Additional notes."""

        result = service._parse_gemini_response(response)

        assert result["confidence"] == 0.85
        assert result["clarification_needed"] is True

    def test_parse_gemini_response_missing_field(self):
        """Test parsing JSON missing required field."""
        service = NLUService()

        response = json.dumps({
            "confidence": 0.95,
            "topic_id": "test"
            # Missing required fields
        })

        with pytest.raises(ValueError, match="Missing required field"):
            service._parse_gemini_response(response)

    def test_parse_gemini_response_invalid_json(self):
        """Test parsing invalid JSON."""
        service = NLUService()

        response = "This is not JSON at all"

        with pytest.raises(ValueError, match="No JSON found"):
            service._parse_gemini_response(response)

    def test_parse_gemini_response_malformed_json(self):
        """Test parsing malformed JSON."""
        service = NLUService()

        response = '{"confidence": 0.95, "topic_id": invalid}'

        with pytest.raises(json.JSONDecodeError):
            service._parse_gemini_response(response)


@pytest.mark.unit
class TestGradeAppropriateTopics:
    """Test grade-appropriate topic filtering."""

    @pytest.mark.asyncio
    async def test_get_grade_9_topics(self):
        """Test getting topics for grade 9."""
        service = NLUService()

        topics = await service._get_grade_appropriate_topics(9)

        assert len(topics) > 0
        # Grade 9 should have access to Newton's Laws
        topic_ids = {t["topic_id"] for t in topics}
        assert "topic_phys_mech_newton_1" in topic_ids

    @pytest.mark.asyncio
    async def test_get_grade_10_topics(self):
        """Test getting topics for grade 10."""
        service = NLUService()

        topics = await service._get_grade_appropriate_topics(10)

        assert len(topics) > 0
        # Grade 10 should have kinetic energy
        topic_ids = {t["topic_id"] for t in topics}
        assert "topic_phys_energy_kinetic" in topic_ids

    @pytest.mark.asyncio
    async def test_get_grade_12_topics(self):
        """Test getting topics for grade 12."""
        service = NLUService()

        topics = await service._get_grade_appropriate_topics(12)

        # Grade 12 should have all topics
        assert len(topics) >= 5

    @pytest.mark.asyncio
    async def test_topics_have_required_fields(self):
        """Test that topics have required fields."""
        service = NLUService()

        topics = await service._get_grade_appropriate_topics(10)

        for topic in topics:
            assert "topic_id" in topic
            assert "name" in topic
            assert "subject" in topic
            assert "grade_levels" in topic
            assert "keywords" in topic


@pytest.mark.unit
class TestTopicValidation:
    """Test topic ID validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_topic_id(self):
        """Test validating a valid topic ID."""
        service = NLUService()

        is_valid = await service._validate_topic_id("topic_phys_mech_newton_3", 10)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_topic_id(self):
        """Test validating an invalid topic ID."""
        service = NLUService()

        is_valid = await service._validate_topic_id("topic_nonexistent", 10)

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_grade_restricted_topic(self):
        """Test validating topic restricted by grade."""
        service = NLUService()

        # Kinetic energy is for grades 10-12, not grade 9
        is_valid = await service._validate_topic_id("topic_phys_energy_kinetic", 9)

        assert is_valid is False


@pytest.mark.unit
class TestMockExtraction:
    """Test mock extraction logic."""

    def test_mock_extract_newton_third(self):
        """Test mock extraction for Newton's Third Law."""
        service = NLUService()

        result = service._mock_extract_topic("Newton's Third Law", 10)

        assert result["topic_id"] == "topic_phys_mech_newton_3"
        assert result["confidence"] == 0.95

    def test_mock_extract_newton_second(self):
        """Test mock extraction for Newton's Second Law."""
        service = NLUService()

        result = service._mock_extract_topic("Newton's Second Law", 10)

        assert result["topic_id"] == "topic_phys_mech_newton_2"

    def test_mock_extract_ambiguous_newton(self):
        """Test mock extraction for ambiguous Newton."""
        service = NLUService()

        result = service._mock_extract_topic("Tell me about Newton", 10)

        assert result["topic_id"] is None
        assert result["clarification_needed"] is True
        assert "which" in result["clarifying_questions"][0].lower()

    def test_mock_extract_out_of_scope(self):
        """Test mock extraction for out-of-scope query."""
        service = NLUService()

        result = service._mock_extract_topic("Best pizza in town", 10)

        assert result["out_of_scope"] is True
        assert result["topic_id"] is None

    def test_mock_extract_unclear(self):
        """Test mock extraction for unclear query."""
        service = NLUService()

        result = service._mock_extract_topic("I need help", 10)

        assert result["clarification_needed"] is True
        assert result["confidence"] == 0.50


@pytest.mark.unit
class TestResponseHelpers:
    """Test response helper methods."""

    def test_fallback_response(self):
        """Test fallback response generation."""
        service = NLUService()

        result = service._fallback_response("Any query")

        assert result["confidence"] == 0.0
        assert result["topic_id"] is None
        assert result["clarification_needed"] is True
        assert len(result["clarifying_questions"]) > 0
        assert "unavailable" in result["reasoning"].lower()

    def test_error_response(self):
        """Test error response generation."""
        service = NLUService()

        result = service._error_response("Test error message")

        assert result["confidence"] == 0.0
        assert result["topic_id"] is None
        assert result["clarification_needed"] is True
        assert result["clarifying_questions"] == ["Test error message"]
        assert result["reasoning"] == "Invalid input"


@pytest.mark.unit
class TestSingleton:
    """Test singleton pattern."""

    def test_get_nlu_service_singleton(self):
        """Test that get_nlu_service returns singleton."""
        service1 = get_nlu_service()
        service2 = get_nlu_service()

        assert service1 is service2

    def test_get_nlu_service_returns_instance(self):
        """Test that get_nlu_service returns NLUService instance."""
        service = get_nlu_service()

        assert isinstance(service, NLUService)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_extract_topic_empty_string(self):
        """Test extraction with empty string."""
        service = NLUService()

        result = await service.extract_topic("", grade_level=10)

        assert result["confidence"] == 0.0
        assert result["clarification_needed"] is True

    @pytest.mark.asyncio
    async def test_extract_topic_whitespace_only(self):
        """Test extraction with whitespace only."""
        service = NLUService()

        result = await service.extract_topic("   ", grade_level=10)

        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_extract_topic_special_characters(self):
        """Test extraction with special characters."""
        service = NLUService()

        result = await service.extract_topic("What is F=ma???", grade_level=10)

        # Should still work and match Newton's Second Law
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_extract_topic_very_long_query(self):
        """Test extraction with very long query."""
        service = NLUService()

        long_query = "Newton's Third Law " * 50

        result = await service.extract_topic(long_query, grade_level=10)

        assert result["topic_id"] == "topic_phys_mech_newton_3"

    def test_parse_gemini_response_nested_json(self):
        """Test parsing response with nested JSON objects."""
        service = NLUService()

        response = json.dumps({
            "confidence": 0.95,
            "topic_id": "test",
            "clarification_needed": False,
            "out_of_scope": False,
            "extra_data": {
                "nested": "value"
            }
        })

        result = service._parse_gemini_response(response)

        assert result["confidence"] == 0.95
        assert "extra_data" in result
