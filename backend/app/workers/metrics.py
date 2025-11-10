"""
Cloud Monitoring Metrics for Content Worker

Exports custom metrics to Google Cloud Monitoring for observability:
- Message processing metrics (success/failure rates)
- Processing duration metrics
- Queue depth metrics
- Retry metrics

These metrics enable:
- Production debugging and troubleshooting
- SLO/SLA monitoring
- Alerting on anomalies
- Capacity planning
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from google.cloud import monitoring_v3
from google.api.metric_pb2 import MetricDescriptor

logger = logging.getLogger(__name__)


class WorkerMetrics:
    """
    Export custom metrics to Cloud Monitoring.

    Metrics exported:
    - content_worker/messages_processed - Counter of processed messages
    - content_worker/messages_failed - Counter of failed messages
    - content_worker/processing_duration - Distribution of processing times
    - content_worker/retry_count - Distribution of retry counts
    """

    def __init__(self, project_id: str, environment: str):
        """
        Initialize metrics exporter.

        Args:
            project_id: GCP project ID
            environment: Environment (dev, staging, prod)
        """
        self.project_id = project_id
        self.environment = environment
        self.project_name = f"projects/{project_id}"

        # Initialize monitoring client
        try:
            self.client = monitoring_v3.MetricServiceClient()
            logger.info(
                f"Cloud Monitoring metrics initialized: project={project_id}, env={environment}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Monitoring client: {e}")
            self.client = None

        # Metric names
        self.metric_prefix = "custom.googleapis.com/content_worker"

    def record_message_processed(
        self,
        success: bool,
        duration_seconds: float,
        retry_count: int = 0,
        request_id: Optional[str] = None,
    ):
        """
        Record metrics for a processed message.

        Args:
            success: Whether message processing succeeded
            duration_seconds: Processing duration in seconds
            retry_count: Number of retry attempts
            request_id: Optional request ID for labeling
        """
        if not self.client:
            return

        try:
            # Write counter metric
            metric_type = f"{self.metric_prefix}/messages_processed"
            self._write_time_series(
                metric_type=metric_type,
                value=1,
                labels={
                    "environment": self.environment,
                    "status": "success" if success else "failure",
                },
                value_type="INT64",
            )

            # Write duration distribution
            if success:
                duration_metric_type = f"{self.metric_prefix}/processing_duration"
                self._write_time_series(
                    metric_type=duration_metric_type,
                    value=duration_seconds,
                    labels={
                        "environment": self.environment,
                    },
                    value_type="DOUBLE",
                )

            # Write retry count distribution
            if retry_count > 0:
                retry_metric_type = f"{self.metric_prefix}/retry_count"
                self._write_time_series(
                    metric_type=retry_metric_type,
                    value=retry_count,
                    labels={
                        "environment": self.environment,
                    },
                    value_type="INT64",
                )

        except Exception as e:
            # Don't fail worker if metrics fail - log and continue
            logger.error(f"Failed to record metrics: {e}")

    def _write_time_series(
        self,
        metric_type: str,
        value: float,
        labels: Dict[str, str],
        value_type: str = "INT64",
    ):
        """
        Write a single time series data point.

        Args:
            metric_type: Full metric type (e.g., custom.googleapis.com/...)
            value: Metric value
            labels: Metric labels
            value_type: Value type (INT64, DOUBLE, etc.)
        """
        if not self.client:
            return

        try:
            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = metric_type
            series.resource.type = "global"

            # Add labels
            for key, val in labels.items():
                series.metric.labels[key] = val

            # Create data point
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10**9)
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point({"interval": interval})

            # Set value based on type
            if value_type == "INT64":
                point.value.int64_value = int(value)
            elif value_type == "DOUBLE":
                point.value.double_value = float(value)

            series.points = [point]

            # Write time series
            self.client.create_time_series(name=self.project_name, time_series=[series])

        except Exception as e:
            # Log but don't fail worker
            logger.error(f"Failed to write time series: {e}")


# Singleton instance
_metrics_instance: Optional[WorkerMetrics] = None


def get_metrics(project_id: str, environment: str) -> WorkerMetrics:
    """
    Get singleton metrics instance.

    Args:
        project_id: GCP project ID
        environment: Environment (dev, staging, prod)

    Returns:
        WorkerMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = WorkerMetrics(project_id, environment)
    return _metrics_instance
