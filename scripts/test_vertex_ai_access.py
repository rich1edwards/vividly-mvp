#!/usr/bin/env python3
"""
Test Vertex AI Gemini access and find correct model name.

This script attempts to access Vertex AI Gemini models and reports
which model names work.
"""
import os
import sys

# Set up path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import vertexai
from vertexai.generative_models import GenerativeModel

# Configuration
PROJECT_ID = "vividly-dev-rich"
LOCATION = "us-central1"

# Model names to try
MODEL_NAMES = [
    "gemini-1.5-pro",
    "gemini-1.5-pro-001",
    "gemini-1.5-pro-002",
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-1.0-pro-001",
    "gemini-1.0-pro-002",
]

def test_model(model_name: str) -> bool:
    """Test if a model is accessible."""
    try:
        print(f"\nTesting model: {model_name}")
        model = GenerativeModel(model_name)

        # Try a simple generation
        response = model.generate_content(
            "Say 'Hello, Vertex AI!' in one sentence."
        )

        print(f"✅ SUCCESS: {model_name}")
        print(f"Response: {response.text[:100]}")
        return True

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"❌ NOT FOUND: {model_name}")
        elif "403" in error_msg:
            print(f"❌ PERMISSION DENIED: {model_name}")
        else:
            print(f"❌ ERROR: {model_name}")
            print(f"   {error_msg[:200]}")
        return False

def main():
    """Main test function."""
    print(f"Testing Vertex AI Gemini access")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print("=" * 60)

    # Initialize Vertex AI
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("✅ Vertex AI initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI: {e}")
        sys.exit(1)

    # Test each model
    successful_models = []
    for model_name in MODEL_NAMES:
        if test_model(model_name):
            successful_models.append(model_name)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if successful_models:
        print(f"\n✅ Working models: {len(successful_models)}")
        for model in successful_models:
            print(f"   - {model}")
        print(f"\n💡 RECOMMENDATION: Use '{successful_models[0]}' in code")
    else:
        print("\n❌ No working models found")
        print("\nPossible issues:")
        print("1. Vertex AI API not fully enabled (may take a few minutes)")
        print("2. Project lacks Gemini API access")
        print("3. Billing not configured")
        print("4. Region doesn't support Gemini (try us-central1)")
        print("\nNext steps:")
        print("1. Wait 5-10 minutes for API enablement")
        print("2. Visit: https://console.cloud.google.com/vertex-ai/generative/language")
        print("3. Accept terms of service if prompted")
        print("4. Verify billing is enabled")

if __name__ == "__main__":
    main()
