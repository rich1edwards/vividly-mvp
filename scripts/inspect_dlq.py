#!/usr/bin/env python3
"""
Inspect Dead Letter Queue for Content Requests

This script pulls messages from the DLQ to identify problematic messages
that are causing worker timeouts (specifically invalid UUID request_ids).
"""

import json
from google.cloud import pubsub_v1
from google.api_core import retry

PROJECT_ID = "vividly-dev-rich"
SUBSCRIPTION_ID = "content-requests-dev-dlq"

def inspect_dlq():
    """Pull and inspect messages from the DLQ."""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    print(f"====================================")
    print(f"INSPECTING DLQ: {SUBSCRIPTION_ID}")
    print(f"====================================")
    print()

    # Pull messages (non-blocking)
    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": 100},
        retry=retry.Retry(deadline=30),
    )

    if not response.received_messages:
        print("No messages found in DLQ")
        return []

    print(f"Found {len(response.received_messages)} messages in DLQ")
    print()

    problematic_messages = []

    for i, received_message in enumerate(response.received_messages, 1):
        message = received_message.message
        data = message.data.decode("utf-8")

        try:
            payload = json.loads(data)
            request_id = payload.get("request_id", "UNKNOWN")

            print(f"------------------------------------")
            print(f"MESSAGE {i}")
            print(f"------------------------------------")
            print(f"Message ID: {message.message_id}")
            print(f"Publish Time: {message.publish_time}")
            print(f"Request ID: {request_id}")
            print(f"Delivery Attempt: {message.attributes.get('googclient_deliveryattempt', 'N/A')}")
            print()
            print(f"Payload:")
            print(json.dumps(payload, indent=2))
            print()

            # Check if request_id is a valid UUID format
            if request_id and not is_valid_uuid(request_id):
                print(f"⚠️  INVALID UUID: '{request_id}' is not a valid UUID")
                problematic_messages.append({
                    "ack_id": received_message.ack_id,
                    "message_id": message.message_id,
                    "request_id": request_id,
                    "payload": payload
                })

        except json.JSONDecodeError:
            print(f"ERROR: Could not decode message data as JSON")
            print(f"Raw data: {data}")
        except Exception as e:
            print(f"ERROR: {e}")

        print()

    print(f"====================================")
    print(f"SUMMARY")
    print(f"====================================")
    print(f"Total messages: {len(response.received_messages)}")
    print(f"Problematic messages (invalid UUID): {len(problematic_messages)}")
    print()

    if problematic_messages:
        print("Problematic Request IDs:")
        for msg in problematic_messages:
            print(f"  - {msg['request_id']} (Message ID: {msg['message_id']})")
        print()
        print("These messages are causing worker timeout loops")
        print("Recommendation: ACK these messages to remove them from DLQ")
        print()

        response = input("Do you want to ACK (delete) these problematic messages? (yes/no): ")
        if response.lower() == "yes":
            ack_messages(subscriber, subscription_path, problematic_messages)

    return problematic_messages

def is_valid_uuid(uuid_string):
    """Check if string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False

def ack_messages(subscriber, subscription_path, messages):
    """Acknowledge (delete) messages from subscription."""
    ack_ids = [msg["ack_id"] for msg in messages]

    print(f"Acknowledging {len(ack_ids)} messages...")
    subscriber.acknowledge(
        request={"subscription": subscription_path, "ack_ids": ack_ids}
    )
    print(f"✓ Successfully removed {len(ack_ids)} problematic messages from DLQ")

if __name__ == "__main__":
    try:
        inspect_dlq()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
