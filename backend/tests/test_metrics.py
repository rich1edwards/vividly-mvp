"""
Unit tests for GCP Cloud Monitoring metrics module.

Tests cover:
- MetricsClient initialization with GCP project
- METRICS_ENABLED toggle functionality
- Graceful error handling and degradation
- Time series data formatting for GCP API
- All metric methods (rate limiting, auth, system health, content generation)
- Singleton pattern behavior
- Resource descriptor configuration
- Convenience functions

Following Andrew Ng's "Test everything" principle - comprehensive coverage.
"""
import os
import pytest
import time
from unittest.mock import MagicMock, patch, call
from typing import Dict, Any

# Import the module under test
from app.core.metrics import (
    MetricsClient,
    get_metrics_client,
    increment_rate_limit_hits,
    increment_rate_limit_exceeded,
    increment_http_request,
    record_request_duration,
)


class TestMetricsClientInitialization:
    """Test suite for MetricsClient initialization."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true", "GCP_PROJECT": "test-project"})
    def test_initialization_with_metrics_enabled(self, mock_client):
        """Test that MetricsClient initializes correctly when METRICS_ENABLED=true."""
        client = MetricsClient(project_id="test-project")

        assert client.project_id == "test-project"
        assert client.project_name == "projects/test-project"
        assert client.enabled is True
        assert client.client is not None
        mock_client.assert_called_once()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "false"})
    def test_initialization_with_metrics_disabled(self, mock_client):
        """Test that MetricsClient gracefully disables when METRICS_ENABLED=false."""
        client = MetricsClient(project_id="test-project")

        assert client.project_id == "test-project"
        assert client.enabled is False
        assert client.client is None
        mock_client.assert_not_called()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "1"})
    def test_initialization_with_metrics_enabled_numeric(self, mock_client):
        """Test METRICS_ENABLED=1 enables metrics."""
        client = MetricsClient(project_id="test-project")

        assert client.enabled is True
        mock_client.assert_called_once()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "yes"})
    def test_initialization_with_metrics_enabled_yes(self, mock_client):
        """Test METRICS_ENABLED=yes enables metrics."""
        client = MetricsClient(project_id="test-project")

        assert client.enabled is True
        mock_client.assert_called_once()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "0"})
    def test_initialization_with_metrics_disabled_zero(self, mock_client):
        """Test METRICS_ENABLED=0 disables metrics."""
        client = MetricsClient(project_id="test-project")

        assert client.enabled is False
        mock_client.assert_not_called()

    @patch(
        "app.core.metrics.monitoring_v3.MetricServiceClient",
        side_effect=Exception("GCP API error"),
    )
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_initialization_handles_gcp_api_errors_gracefully(self, mock_client):
        """Test that initialization errors don't crash, but disable metrics."""
        client = MetricsClient(project_id="test-project")

        assert client.project_id == "test-project"
        assert client.enabled is False
        assert client.client is None

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"GCP_PROJECT": "env-project"}, clear=True)
    def test_initialization_uses_gcp_project_env_var(self, mock_client):
        """Test that project_id defaults to GCP_PROJECT environment variable."""
        client = MetricsClient()

        assert client.project_id == "env-project"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_uses_default_project(self, mock_client):
        """Test that project_id defaults to vividly-dev-rich if no env var."""
        client = MetricsClient()

        assert client.project_id == "vividly-dev-rich"


class TestMetricsClientWriteTimeSeries:
    """Test suite for _write_time_series internal method."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_write_time_series_sends_data_to_gcp(self, mock_client_class):
        """Test that _write_time_series sends properly formatted data to GCP."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")

        client._write_time_series(
            metric_type="custom.googleapis.com/test/metric",
            value=42,
            labels={"key": "value"},
            value_type="INT64",
        )

        # Verify create_time_series was called
        mock_client_instance.create_time_series.assert_called_once()

        call_args = mock_client_instance.create_time_series.call_args
        assert call_args[1]["name"] == "projects/test-project"
        time_series = call_args[1]["time_series"][0]

        # Verify metric type
        assert time_series.metric.type == "custom.googleapis.com/test/metric"

        # Verify labels
        assert time_series.metric.labels["key"] == "value"

        # Verify resource type
        assert time_series.resource.type == "generic_task"
        assert time_series.resource.labels["project_id"] == "test-project"

        # Verify data point
        assert len(time_series.points) == 1
        assert time_series.points[0].value.int64_value == 42

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "false"})
    def test_write_time_series_does_nothing_when_disabled(self, mock_client_class):
        """Test that _write_time_series is a no-op when metrics are disabled."""
        client = MetricsClient(project_id="test-project")

        # Should not raise any errors, just return early
        client._write_time_series(
            metric_type="custom.googleapis.com/test/metric",
            value=42,
            labels={"key": "value"},
        )

        # No client should have been created
        mock_client_class.assert_not_called()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_write_time_series_handles_gcp_api_errors_gracefully(
        self, mock_client_class
    ):
        """Test that API errors are logged but don't crash the application."""
        mock_client_instance = MagicMock()
        mock_client_instance.create_time_series.side_effect = Exception("GCP API error")
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")

        # Should not raise, but log the error
        client._write_time_series(
            metric_type="custom.googleapis.com/test/metric", value=42
        )

        # Verify it tried to send
        mock_client_instance.create_time_series.assert_called_once()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_write_time_series_with_double_value(self, mock_client_class):
        """Test that DOUBLE value_type works correctly."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")

        client._write_time_series(
            metric_type="custom.googleapis.com/test/metric",
            value=3.14159,
            value_type="DOUBLE",
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        # Verify DOUBLE value
        assert time_series.points[0].value.double_value == 3.14159

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_write_time_series_without_labels(self, mock_client_class):
        """Test that _write_time_series works without labels."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")

        client._write_time_series(
            metric_type="custom.googleapis.com/test/metric", value=10, labels=None
        )

        # Should succeed without labels
        mock_client_instance.create_time_series.assert_called_once()

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_write_time_series_resource_labels(self, mock_client_class):
        """Test that resource labels are correctly set."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        with patch.dict(os.environ, {"K_REVISION": "test-revision-123"}):
            client = MetricsClient(project_id="test-project")

            client._write_time_series(
                metric_type="custom.googleapis.com/test/metric", value=1
            )

            call_args = mock_client_instance.create_time_series.call_args
            time_series = call_args[1]["time_series"][0]

            # Verify resource labels
            assert time_series.resource.labels["project_id"] == "test-project"
            assert time_series.resource.labels["task_id"] == "test-revision-123"
            assert "namespace" in time_series.resource.labels
            assert "job" in time_series.resource.labels


class TestRateLimitingMetrics:
    """Test suite for rate limiting metrics (Sprint 2 requirements)."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_rate_limit_hits(self, mock_client_class):
        """Test increment_rate_limit_hits sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_rate_limit_hits(
            endpoint="/api/auth/login", ip_address="127.0.0.1"
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/rate_limit_hits_total"
        )
        assert time_series.metric.labels["endpoint"] == "/api/auth/login"
        assert time_series.metric.labels["ip_address"] == "127.0.0.1"
        assert time_series.points[0].value.int64_value == 1

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_rate_limit_exceeded(self, mock_client_class):
        """Test increment_rate_limit_exceeded sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_rate_limit_exceeded(
            endpoint="/api/content", ip_address="192.168.1.1"
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/rate_limit_exceeded_total"
        )
        assert time_series.metric.labels["endpoint"] == "/api/content"
        assert time_series.metric.labels["ip_address"] == "192.168.1.1"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_brute_force_lockouts_with_email(self, mock_client_class):
        """Test increment_brute_force_lockouts with email provided."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_brute_force_lockouts(
            ip_address="10.0.0.1", email="test@example.com"
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/brute_force_lockouts_total"
        )
        assert time_series.metric.labels["ip_address"] == "10.0.0.1"
        assert time_series.metric.labels["email"] == "test@example.com"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_brute_force_lockouts_without_email(self, mock_client_class):
        """Test increment_brute_force_lockouts without email (for privacy)."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_brute_force_lockouts(ip_address="10.0.0.1", email=None)

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/brute_force_lockouts_total"
        )
        assert time_series.metric.labels["ip_address"] == "10.0.0.1"
        assert "email" not in time_series.metric.labels

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_record_rate_limit_middleware_latency(self, mock_client_class):
        """Test record_rate_limit_middleware_latency sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.record_rate_limit_middleware_latency(
            endpoint="/api/health", latency_ms=12.5
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/rate_limit_middleware_latency_ms"
        )
        assert time_series.metric.labels["endpoint"] == "/api/health"
        assert time_series.points[0].value.double_value == 12.5


class TestAuthenticationMetrics:
    """Test suite for authentication metrics."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_auth_login_attempts_success(self, mock_client_class):
        """Test increment_auth_login_attempts for successful login."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_auth_login_attempts(status="success", user_role="teacher")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/auth_login_attempts_total"
        )
        assert time_series.metric.labels["status"] == "success"
        assert time_series.metric.labels["user_role"] == "teacher"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_auth_login_attempts_without_role(self, mock_client_class):
        """Test increment_auth_login_attempts without user_role."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_auth_login_attempts(status="failure", user_role=None)

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert time_series.metric.labels["status"] == "failure"
        assert "user_role" not in time_series.metric.labels

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_auth_login_failures(self, mock_client_class):
        """Test increment_auth_login_failures sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_auth_login_failures(reason="invalid_password")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/auth_login_failures_total"
        )
        assert time_series.metric.labels["reason"] == "invalid_password"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_auth_token_refresh(self, mock_client_class):
        """Test increment_auth_token_refresh sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_auth_token_refresh(status="success")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/auth_token_refresh_total"
        )
        assert time_series.metric.labels["status"] == "success"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_record_auth_session_duration(self, mock_client_class):
        """Test record_auth_session_duration sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.record_auth_session_duration(duration_seconds=3600.5)

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/auth_session_duration_seconds"
        )
        assert time_series.points[0].value.double_value == 3600.5

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_set_auth_active_sessions(self, mock_client_class):
        """Test set_auth_active_sessions sends correct gauge metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.set_auth_active_sessions(count=42, user_role="student")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/auth_active_sessions"
        )
        assert time_series.metric.labels["user_role"] == "student"
        assert time_series.points[0].value.int64_value == 42


class TestSystemHealthMetrics:
    """Test suite for system health metrics."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_http_request(self, mock_client_class):
        """Test increment_http_request sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_http_request(
            method="GET", endpoint="/api/health", status_code=200
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/http_request_total"
        )
        assert time_series.metric.labels["method"] == "GET"
        assert time_series.metric.labels["endpoint"] == "/api/health"
        assert time_series.metric.labels["status_code"] == "200"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_http_request_error_status(self, mock_client_class):
        """Test increment_http_request with error status code."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_http_request(
            method="POST", endpoint="/api/content", status_code=500
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert time_series.metric.labels["status_code"] == "500"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_record_request_duration(self, mock_client_class):
        """Test record_request_duration sends correct metric."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.record_request_duration(
            method="POST", endpoint="/api/v1/content", duration_seconds=0.142
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/http_request_duration_seconds"
        )
        assert time_series.metric.labels["method"] == "POST"
        assert time_series.metric.labels["endpoint"] == "/api/v1/content"
        assert time_series.points[0].value.double_value == 0.142


class TestContentGenerationMetrics:
    """Test suite for content generation metrics."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_content_generation_requests_pending(self, mock_client_class):
        """Test increment_content_generation_requests with pending status."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_content_generation_requests(status="pending")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/content_generation_requests_total"
        )
        assert time_series.metric.labels["status"] == "pending"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_content_generation_requests_completed(self, mock_client_class):
        """Test increment_content_generation_requests with completed status."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.increment_content_generation_requests(status="completed")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert time_series.metric.labels["status"] == "completed"

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_record_content_generation_duration_nlu_stage(self, mock_client_class):
        """Test record_content_generation_duration for NLU stage."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.record_content_generation_duration(stage="nlu", duration_seconds=2.5)

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/content_generation_duration_seconds"
        )
        assert time_series.metric.labels["stage"] == "nlu"
        assert time_series.points[0].value.double_value == 2.5

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_record_content_generation_duration_total_stage(self, mock_client_class):
        """Test record_content_generation_duration for total pipeline time."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")
        client.record_content_generation_duration(stage="total", duration_seconds=45.8)

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]

        assert time_series.metric.labels["stage"] == "total"
        assert time_series.points[0].value.double_value == 45.8


class TestSingletonPattern:
    """Test suite for singleton pattern and global access."""

    def teardown_method(self):
        """Reset singleton between tests."""
        import app.core.metrics as metrics_module

        metrics_module._metrics_client = None

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_get_metrics_client_returns_singleton(self, mock_client_class):
        """Test that get_metrics_client returns the same instance."""
        client1 = get_metrics_client()
        client2 = get_metrics_client()

        assert client1 is client2
        # Client should only be initialized once
        assert mock_client_class.call_count == 1

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_get_metrics_client_creates_instance_on_first_call(self, mock_client_class):
        """Test that get_metrics_client creates instance on first call."""
        import app.core.metrics as metrics_module

        # Ensure no instance exists
        metrics_module._metrics_client = None

        client = get_metrics_client()

        assert client is not None
        assert isinstance(client, MetricsClient)
        mock_client_class.assert_called_once()


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def teardown_method(self):
        """Reset singleton between tests."""
        import app.core.metrics as metrics_module

        metrics_module._metrics_client = None

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_rate_limit_hits_convenience(self, mock_client_class):
        """Test increment_rate_limit_hits convenience function."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        increment_rate_limit_hits(endpoint="/api/test", ip_address="1.2.3.4")

        # Should have called the underlying method
        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]
        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/rate_limit_hits_total"
        )

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_rate_limit_exceeded_convenience(self, mock_client_class):
        """Test increment_rate_limit_exceeded convenience function."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        increment_rate_limit_exceeded(endpoint="/api/test", ip_address="1.2.3.4")

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]
        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/rate_limit_exceeded_total"
        )

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_increment_http_request_convenience(self, mock_client_class):
        """Test increment_http_request convenience function."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        increment_http_request(method="GET", endpoint="/api/health", status_code=200)

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]
        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/http_request_total"
        )

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true"})
    def test_record_request_duration_convenience(self, mock_client_class):
        """Test record_request_duration convenience function."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        record_request_duration(
            method="POST", endpoint="/api/test", duration_seconds=0.5
        )

        call_args = mock_client_instance.create_time_series.call_args
        time_series = call_args[1]["time_series"][0]
        assert (
            time_series.metric.type
            == "custom.googleapis.com/vividly/http_request_duration_seconds"
        )


class TestMetricsIntegration:
    """Integration tests for metrics client with realistic scenarios."""

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "true", "K_REVISION": "test-rev-123"})
    def test_multiple_metrics_in_sequence(self, mock_client_class):
        """Test sending multiple metrics in sequence."""
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        client = MetricsClient(project_id="test-project")

        # Simulate a full request lifecycle
        client.increment_http_request("POST", "/api/content", 200)
        client.record_request_duration("POST", "/api/content", 1.5)
        client.increment_content_generation_requests("completed")
        client.record_content_generation_duration("total", 45.0)

        # Should have made 4 calls
        assert mock_client_instance.create_time_series.call_count == 4

    @patch("app.core.metrics.monitoring_v3.MetricServiceClient")
    @patch.dict(os.environ, {"METRICS_ENABLED": "false"})
    def test_metrics_disabled_no_api_calls(self, mock_client_class):
        """Test that no API calls are made when metrics are disabled."""
        client = MetricsClient(project_id="test-project")

        # Try to send multiple metrics
        client.increment_http_request("GET", "/api/health", 200)
        client.increment_rate_limit_hits("/api/test", "1.2.3.4")
        client.record_request_duration("GET", "/api/health", 0.1)

        # No client should be created, no calls made
        mock_client_class.assert_not_called()


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
