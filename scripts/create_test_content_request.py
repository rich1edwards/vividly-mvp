#!/usr/bin/env python3
"""
Create a test content generation request for end-to-end validation.

This script:
1. Creates a content_request record in the database
2. Publishes a message to the content-generation-topic Pub/Sub topic
3. Prints the request_id for tracking

Usage:
    python3 scripts/create_test_content_request.py
"""

import sys
import os
import uuid
import json
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.cloud import pubsub_v1

# Configuration
PROJECT_ID = "vividly-dev-rich"
TOPIC_NAME = "content-generation-topic"

def create_test_request():
    """Create test content generation request."""

    # Generate UUID
    request_id = str(uuid.uuid4())
    correlation_id = f"test-session-11-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    print(f"\\n=== Creating Test Content Request ===")
    print(f"Request ID: {request_id}")
    print(f"Correlation ID: {correlation_id}")

    # Get database URL from Secret Manager
    print(f"\\nStep 1: Creating database record...")

    try:
        # Import after path is set
        from app.models.content_request import ContentRequest
        from app.core.config import settings

        # Create database session
        engine = create_engine(str(settings.DATABASE_URL))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Create content request record
        content_request = ContentRequest(
            request_id=request_id,
            topic_id="test-topic-session11",
            interest="Machine Learning",  # Test with popular interest
            student_id=None,  # No user required for testing
            status="pending",
            modality="text_and_video",  # Test FULL pipeline (not text-only)
            priority=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(content_request)
        db.commit()
        db.refresh(content_request)

        print(f"✅ Database record created: status={content_request.status}, modality={content_request.modality}")

        db.close()

    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        print(f"   This is OK - worker will validate UUID but may fail on database lookup")
        print(f"   Continuing with Pub/Sub message creation...")

    # Publish to Pub/Sub
    print(f"\\nStep 2: Publishing Pub/Sub message...")

    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

        # Create message payload
        message_data = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "topic_id": "test-topic-session11",
            "interest": "Machine Learning",
            "modality": "text_and_video",
            "priority": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Publish message
        message_json = json.dumps(message_data)
        future = publisher.publish(topic_path, message_json.encode("utf-8"))
        message_id = future.result()

        print(f"✅ Pub/Sub message published: message_id={message_id}")

    except Exception as e:
        print(f"❌ Pub/Sub publish failed: {e}")
        return False

    print(f"\\n=== Test Request Created Successfully ===")
    print(f"\\nNext Steps:")
    print(f"1. Execute worker: gcloud run jobs execute dev-vividly-content-worker --region=us-central1 --project=vividly-dev-rich --wait")
    print(f"2. Monitor logs: gcloud logging read 'resource.type=\"cloud_run_job\" AND jsonPayload.request_id=\"{request_id}\"' --project=vividly-dev-rich --limit=50")
    print(f"3. Check database: SELECT * FROM content_requests WHERE request_id = '{request_id}';")
    print(f"\\nRequest ID to track: {request_id}")

    # Save to file for easy reference
    with open("/tmp/test_request_session11.txt", "w") as f:
        f.write(f"REQUEST_ID={request_id}\\n")
        f.write(f"CORRELATION_ID={correlation_id}\\n")
        f.write(f"MESSAGE_DATA={message_json}\\n")

    print(f"\\nRequest details saved to: /tmp/test_request_session11.txt")

    return True

if __name__ == "__main__":
    success = create_test_request()
    sys.exit(0 if success else 1)
