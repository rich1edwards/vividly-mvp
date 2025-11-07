#!/usr/bin/env python3
"""
Dead Letter Queue Inspection Tool

Inspect and manage messages from the Dead Letter Queue.
Failed content generation requests are sent here after max retries.

Usage:
    # View failed messages (don't acknowledge)
    python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev

    # View and acknowledge messages (remove from queue)
    python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev --ack

    # View specific number of messages
    python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev --max-messages 5

    # Export to JSON for analysis
    python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev --export dlq_messages.json

Requirements:
    - google-cloud-pubsub installed
    - Authenticated with gcloud (gcloud auth application-default login)
    - Subscriber permission on DLQ subscription
"""

import argparse
import json
import sys
from datetime import datetime
from typing import List, Dict, Any
from google.cloud import pubsub_v1
from google.api_core import retry


class DLQInspector:
    """Inspect and manage Dead Letter Queue messages."""

    def __init__(self, project_id: str, environment: str):
        """
        Initialize DLQ inspector.

        Args:
            project_id: GCP project ID
            environment: Environment (dev, staging, prod)
        """
        self.project_id = project_id
        self.environment = environment
        self.subscription_name = f"content-requests-dlq-reader-{environment}"
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = (
            f"projects/{project_id}/subscriptions/{self.subscription_name}"
        )

    def pull_messages(
        self, max_messages: int = 10, acknowledge: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Pull messages from Dead Letter Queue.

        Args:
            max_messages: Maximum number of messages to pull
            acknowledge: If True, acknowledge (delete) messages after viewing

        Returns:
            List of message data dictionaries
        """
        try:
            # Pull messages
            response = self.subscriber.pull(
                request={
                    "subscription": self.subscription_path,
                    "max_messages": max_messages,
                },
                timeout=30.0,
                retry=retry.Retry(deadline=60.0),
            )

            messages = []
            ack_ids = []

            for received_message in response.received_messages:
                # Parse message data
                try:
                    message_data = json.loads(
                        received_message.message.data.decode("utf-8")
                    )
                except json.JSONDecodeError:
                    message_data = {
                        "error": "Failed to decode message",
                        "raw_data": received_message.message.data.decode(
                            "utf-8", errors="replace"
                        ),
                    }

                # Extract attributes
                attributes = dict(received_message.message.attributes)

                # Build comprehensive message info
                message_info = {
                    "message_id": received_message.message.message_id,
                    "publish_time": received_message.message.publish_time.isoformat(),
                    "delivery_attempt": attributes.get(
                        "googclient_deliveryattempt", "unknown"
                    ),
                    "data": message_data,
                    "attributes": attributes,
                    "ack_id": received_message.ack_id,
                }

                messages.append(message_info)
                ack_ids.append(received_message.ack_id)

            # Acknowledge messages if requested
            if acknowledge and ack_ids:
                self.subscriber.acknowledge(
                    request={
                        "subscription": self.subscription_path,
                        "ack_ids": ack_ids,
                    }
                )
                print(f"\n✓ Acknowledged {len(ack_ids)} messages (removed from DLQ)")

            return messages

        except Exception as e:
            print(f"Error pulling messages: {e}", file=sys.stderr)
            return []

    def format_message(self, msg: Dict[str, Any], index: int) -> str:
        """
        Format message for display.

        Args:
            msg: Message dictionary
            index: Message index

        Returns:
            Formatted string
        """
        lines = [
            f"\n{'=' * 80}",
            f"MESSAGE #{index + 1}",
            f"{'=' * 80}",
            f"Message ID:       {msg['message_id']}",
            f"Publish Time:     {msg['publish_time']}",
            f"Delivery Attempt: {msg['delivery_attempt']}",
            "",
            "REQUEST DATA:",
        ]

        # Format request data
        data = msg["data"]
        if isinstance(data, dict):
            lines.append(f"  Request ID:     {data.get('request_id', 'N/A')}")
            lines.append(f"  Student ID:     {data.get('student_id', 'N/A')}")
            lines.append(f"  Correlation ID: {data.get('correlation_id', 'N/A')}")
            lines.append(f"  Student Query:  {data.get('student_query', 'N/A')}")
            lines.append(f"  Grade Level:    {data.get('grade_level', 'N/A')}")
            lines.append(f"  Interest:       {data.get('interest', 'None')}")
            lines.append(f"  Environment:    {data.get('environment', 'N/A')}")
        else:
            lines.append(f"  {data}")

        # Add attributes
        if msg["attributes"]:
            lines.append("")
            lines.append("ATTRIBUTES:")
            for key, value in msg["attributes"].items():
                lines.append(f"  {key}: {value}")

        lines.append(f"{'=' * 80}")

        return "\n".join(lines)

    def export_to_json(self, messages: List[Dict[str, Any]], filename: str):
        """
        Export messages to JSON file.

        Args:
            messages: List of message dictionaries
            filename: Output filename
        """
        export_data = {
            "export_time": datetime.utcnow().isoformat(),
            "project_id": self.project_id,
            "environment": self.environment,
            "subscription": self.subscription_name,
            "message_count": len(messages),
            "messages": messages,
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✓ Exported {len(messages)} messages to {filename}")

    def get_subscription_info(self) -> Dict[str, Any]:
        """
        Get subscription metadata.

        Returns:
            Subscription info dictionary
        """
        try:
            subscription = self.subscriber.get_subscription(
                request={"subscription": self.subscription_path}
            )

            return {
                "name": subscription.name,
                "topic": subscription.topic,
                "ack_deadline": subscription.ack_deadline_seconds,
                "message_retention": subscription.message_retention_duration.seconds,
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect Dead Letter Queue messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View 10 messages without acknowledging
  python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev

  # View and acknowledge 5 messages
  python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev --max-messages 5 --ack

  # Export to JSON
  python scripts/inspect_dlq.py --project vividly-dev-rich --environment dev --export failed_messages.json
        """,
    )

    parser.add_argument(
        "--project",
        required=True,
        help="GCP project ID (e.g., vividly-dev-rich)",
    )

    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Environment (dev, staging, prod)",
    )

    parser.add_argument(
        "--max-messages",
        type=int,
        default=10,
        help="Maximum number of messages to pull (default: 10)",
    )

    parser.add_argument(
        "--ack",
        action="store_true",
        help="Acknowledge messages after viewing (removes from DLQ)",
    )

    parser.add_argument(
        "--export",
        metavar="FILENAME",
        help="Export messages to JSON file",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Show subscription info only",
    )

    args = parser.parse_args()

    # Initialize inspector
    inspector = DLQInspector(args.project, args.environment)

    print(f"\nDead Letter Queue Inspector")
    print(f"Project:      {args.project}")
    print(f"Environment:  {args.environment}")
    print(f"Subscription: {inspector.subscription_name}")

    # Show subscription info if requested
    if args.info:
        print("\nSubscription Info:")
        info = inspector.get_subscription_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        return

    # Warning about acknowledgment
    if args.ack:
        print("\n⚠️  WARNING: --ack flag will DELETE messages from DLQ after viewing")
        response = input("Continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Cancelled.")
            return

    # Pull messages
    print(f"\nPulling up to {args.max_messages} messages from DLQ...\n")
    messages = inspector.pull_messages(
        max_messages=args.max_messages, acknowledge=args.ack
    )

    if not messages:
        print("✓ No messages in Dead Letter Queue")
        return

    print(f"\nFound {len(messages)} message(s) in DLQ")

    # Display messages
    for i, msg in enumerate(messages):
        print(inspector.format_message(msg, i))

    # Export if requested
    if args.export:
        inspector.export_to_json(messages, args.export)

    # Summary
    print(f"\nSummary:")
    print(f"  Messages pulled: {len(messages)}")
    print(f"  Acknowledged:    {'Yes' if args.ack else 'No'}")

    # Extract unique failure patterns
    failure_stages = {}
    for msg in messages:
        data = msg.get("data", {})
        if isinstance(data, dict):
            # This info would come from error_stage in ContentRequest
            # For now, just count by delivery attempts
            attempts = msg.get("delivery_attempt", "unknown")
            failure_stages[attempts] = failure_stages.get(attempts, 0) + 1

    if failure_stages:
        print(f"\n  Delivery Attempts:")
        for attempts, count in sorted(failure_stages.items()):
            print(f"    {attempts}: {count} messages")


if __name__ == "__main__":
    main()
