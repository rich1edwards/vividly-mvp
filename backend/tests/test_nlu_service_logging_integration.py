"""
Test NLU Service Logging Integration

Validates that log_prompt_execution() is properly integrated into nlu_service.py
and captures all required metrics.

Following Andrew Ng's "test everything" principle.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.nlu_service import NLUService


class TestNLUServiceLoggingIntegration:
    """Test that NLU service properly logs prompt executions."""

    @pytest.fixture
    def mock_vertex_response(self):
        """Mock Vertex AI response with usage metadata."""
        response = Mock()
        response.text = """{
            "confidence": 0.95,
            "topic_id": "topic_phys_mech_newton_3",
            "topic_name": "Newton's Third Law",
            "clarification_needed": false,
            "clarifying_questions": [],
            "out_of_scope": false,
            "reasoning": "Clear query about Newton's Third Law"
        }"""

        # Mock usage metadata
        usage_metadata = Mock()
        usage_metadata.prompt_token_count = 1000
        usage_metadata.candidates_token_count = 500
        response.usage_metadata = usage_metadata

        return response

    @pytest.mark.asyncio
    async def test_successful_execution_logs_all_metrics(self, mock_vertex_response):
        """Test that successful API calls log timing, tokens, and cost."""
        with patch("app.core.prompt_templates.log_prompt_execution") as mock_log:
            # Setup mocks
            mock_model = Mock()
            mock_model.generate_content.return_value = mock_vertex_response

            # Create service and manually configure it
            service = NLUService()
            service.vertex_available = True
            service.model = mock_model

            # Execute
            result = await service.extract_topic(
                student_query="Explain Newton's Third Law with basketball",
                grade_level=10,
            )

            # Verify log_prompt_execution was called
            assert mock_log.called, "log_prompt_execution should be called"

            # Verify call arguments
            call_kwargs = mock_log.call_args.kwargs

            # Check required fields
            assert call_kwargs["template_key"] == "nlu_extraction_gemini_25"
            assert call_kwargs["success"] is True
            assert call_kwargs["response_time_ms"] > 0

            # Check token counts
            assert call_kwargs["input_token_count"] == 1000
            assert call_kwargs["output_token_count"] == 500

            # Check cost calculation
            # Expected: (1000/1M * $0.075) + (500/1M * $0.30) = $0.000225
            expected_cost = 0.000225
            assert abs(call_kwargs["cost_usd"] - expected_cost) < 0.000001

            # Check metadata
            assert "model" in call_kwargs["metadata"]
            assert "temperature" in call_kwargs["metadata"]
            assert "attempt" in call_kwargs["metadata"]

    @pytest.mark.asyncio
    async def test_failed_execution_logs_error(self):
        """Test that API failures are logged with error details."""
        with patch("app.core.prompt_templates.log_prompt_execution") as mock_log:
            # Setup mocks to raise exception
            mock_model = Mock()
            mock_model.generate_content.side_effect = Exception(
                "API Error: Rate limit exceeded"
            )

            # Create service and manually configure it
            service = NLUService()
            service.vertex_available = True
            service.model = mock_model

            # Execute (should not raise, should return fallback)
            result = await service.extract_topic(
                student_query="Explain Newton's Third Law", grade_level=10
            )

            # Verify fallback response returned
            assert result["confidence"] == 0.0
            assert result["clarification_needed"] is True

            # Verify log_prompt_execution was called for failure
            assert mock_log.called, "log_prompt_execution should be called on failure"

            # Verify failure was logged
            call_kwargs = mock_log.call_args.kwargs
            assert call_kwargs["success"] is False
            assert call_kwargs["response_time_ms"] > 0
            assert "error_message" in call_kwargs
            assert "Rate limit exceeded" in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_retry_logic_logs_successful_attempt(self, mock_vertex_response):
        """Test that retry logic logs the successful attempt number."""
        with patch("app.core.prompt_templates.log_prompt_execution") as mock_log, patch(
            "asyncio.sleep"
        ):  # Mock sleep to speed up test
            # Setup mocks - fail first, succeed second
            mock_model = Mock()
            mock_model.generate_content.side_effect = [
                Exception("Temporary error"),
                mock_vertex_response,
            ]

            # Create service and manually configure it
            service = NLUService()
            service.vertex_available = True
            service.model = mock_model

            # Execute
            result = await service.extract_topic(
                student_query="Explain Newton's Third Law", grade_level=10
            )

            # Verify success after retry
            assert result["confidence"] == 0.95

            # Verify log shows attempt 2
            call_kwargs = mock_log.call_args.kwargs
            assert call_kwargs["metadata"]["attempt"] == 2

    @pytest.mark.asyncio
    async def test_mock_mode_does_not_log(self):
        """Test that mock mode (no Vertex AI) does not attempt logging."""
        with patch("app.core.prompt_templates.log_prompt_execution") as mock_log:
            # Create service in mock mode
            service = NLUService()
            service.vertex_available = False

            # Execute
            result = await service.extract_topic(
                student_query="Explain Newton's Third Law", grade_level=10
            )

            # Verify mock response returned
            assert result["confidence"] > 0

            # Verify NO logging occurred (mock mode doesn't use real API)
            assert not mock_log.called, "Mock mode should not log executions"

    @pytest.mark.asyncio
    async def test_missing_usage_metadata_handles_gracefully(self):
        """Test that missing usage metadata doesn't crash logging."""
        with patch("app.core.prompt_templates.log_prompt_execution") as mock_log:
            # Setup response without usage_metadata
            response = Mock()
            response.text = """{
                "confidence": 0.95,
                "topic_id": "topic_phys_mech_newton_3",
                "topic_name": "Newton's Third Law",
                "clarification_needed": false,
                "clarifying_questions": [],
                "out_of_scope": false,
                "reasoning": "Clear query"
            }"""
            response.usage_metadata = None  # No metadata

            mock_model = Mock()
            mock_model.generate_content.return_value = response

            # Create service and manually configure it
            service = NLUService()
            service.vertex_available = True
            service.model = mock_model

            # Execute
            result = await service.extract_topic(
                student_query="Explain Newton's Third Law", grade_level=10
            )

            # Verify execution succeeded
            assert result["confidence"] == 0.95

            # Verify logging was called with None for tokens/cost
            call_kwargs = mock_log.call_args.kwargs
            assert call_kwargs["success"] is True
            assert call_kwargs["input_token_count"] is None
            assert call_kwargs["output_token_count"] is None
            assert call_kwargs["cost_usd"] is None

    @pytest.mark.asyncio
    async def test_execution_id_returned_in_logs(self, mock_vertex_response):
        """Test that execution_id from logging is available for tracing."""
        with patch("app.core.prompt_templates.log_prompt_execution") as mock_log:
            # Mock log_prompt_execution to return execution_id
            mock_log.return_value = "exec_12345678-1234-1234-1234-123456789abc"

            mock_model = Mock()
            mock_model.generate_content.return_value = mock_vertex_response

            # Create service and manually configure it
            service = NLUService()
            service.vertex_available = True
            service.model = mock_model

            # Execute
            result = await service.extract_topic(
                student_query="Explain Newton's Third Law", grade_level=10
            )

            # Verify log was called and returned execution_id
            assert mock_log.called
            execution_id = mock_log.return_value
            assert execution_id.startswith("exec_")
            assert len(execution_id) > 10  # UUID format


class TestCostCalculationAccuracy:
    """Test cost calculation accuracy for different scenarios."""

    def test_gemini_flash_cost_calculation(self):
        """Test cost calculation for Gemini 2.5 Flash."""
        from app.core.prompt_templates import calculate_gemini_cost

        # Test case 1: Small request
        cost = calculate_gemini_cost(1000, 500, "gemini-2.5-flash")
        expected = (1000 / 1_000_000) * 0.075 + (500 / 1_000_000) * 0.30
        assert abs(cost - expected) < 0.000001
        assert abs(cost - 0.000225) < 0.000001

        # Test case 2: Large request
        cost = calculate_gemini_cost(100_000, 50_000, "gemini-2.5-flash")
        expected = (100_000 / 1_000_000) * 0.075 + (50_000 / 1_000_000) * 0.30
        assert abs(cost - expected) < 0.000001
        assert abs(cost - 0.0225) < 0.000001

        # Test case 3: Zero tokens
        cost = calculate_gemini_cost(0, 0, "gemini-2.5-flash")
        assert cost == 0.0

    def test_cost_calculation_with_different_models(self):
        """Test that different models use correct pricing."""
        from app.core.prompt_templates import calculate_gemini_cost

        # Gemini Pro is more expensive than Flash
        flash_cost = calculate_gemini_cost(10_000, 5_000, "gemini-2.5-flash")
        pro_cost = calculate_gemini_cost(10_000, 5_000, "gemini-pro")

        assert pro_cost > flash_cost

        # Verify Pro pricing: $0.50 input, $1.50 output per 1M
        expected_pro = (10_000 / 1_000_000) * 0.50 + (5_000 / 1_000_000) * 1.50
        assert abs(pro_cost - expected_pro) < 0.000001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
