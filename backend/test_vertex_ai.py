#!/usr/bin/env python3
"""
Test script to verify Vertex AI API access with Gemini.
"""
import os
import sys

def test_vertex_ai_access():
    """Test Vertex AI API access with a simple Gemini call."""
    project_id = "vividly-dev-rich"
    location = "us-central1"
    model_name = "gemini-1.5-pro"

    print(f"Testing Vertex AI access...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print(f"Model: {model_name}")
    print()

    try:
        # Import inside try block to handle missing dependencies
        # Modern import pattern (google-cloud-aiplatform >= 1.60.0)
        import vertexai
        from vertexai.generative_models import GenerativeModel

        # Initialize Vertex AI before using models
        vertexai.init(project=project_id, location=location)
        print("✓ Vertex AI initialized successfully")

        # Create model instance
        model = GenerativeModel(model_name)
        print(f"✓ Model '{model_name}' loaded successfully")

        # Make a simple test call
        print("\nMaking test API call to Gemini...")
        response = model.generate_content(
            "Respond with exactly: 'Vertex AI is working correctly.'"
        )

        print("✓ API call successful!")
        print(f"\nResponse: {response.text}")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"\nError type: {type(e).__name__}")

        # Print full traceback for debugging
        import traceback
        traceback.print_exc()

        # Check for common permission issues
        if "403" in str(e) or "permission" in str(e).lower():
            print("\n⚠ This appears to be a permissions issue.")
            print("The service account may need the 'Vertex AI User' role.")
        elif "quota" in str(e).lower():
            print("\n⚠ This appears to be a quota issue.")
            print("Check your GCP quota limits for Vertex AI.")

        return False

if __name__ == "__main__":
    success = test_vertex_ai_access()
    sys.exit(0 if success else 1)
