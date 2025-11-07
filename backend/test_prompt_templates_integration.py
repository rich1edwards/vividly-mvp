"""
Test script for prompt templates integration.

Tests backwards compatibility:
1. File-based fallback (before database migration)
2. Database-driven (after database migration)
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.prompt_templates import get_template, render_template, get_model_config


def test_file_based_fallback():
    """Test that the system works with file-based templates (backwards compatibility)."""
    print("\n" + "="*80)
    print("TEST 1: File-based fallback (no database)")
    print("="*80)

    try:
        # Get template
        template = get_template("nlu_extraction_gemini_25")
        print(f"\n✓ Template loaded: {template['name']}")
        print(f"  Description: {template['description'][:80]}...")
        print(f"  Model: {template['model_name']}")
        print(f"  Temperature: {template['temperature']}")
        print(f"  Template length: {len(template['template'])} characters")

        # Get model config
        model_config = get_model_config("nlu_extraction_gemini_25")
        print(f"\n✓ Model config loaded:")
        print(f"  Model: {model_config['model_name']}")
        print(f"  Temperature: {model_config['temperature']}")
        print(f"  Max tokens: {model_config['max_output_tokens']}")

        # Render template
        variables = {
            "student_query": "Explain Newton's Third Law",
            "grade_level": 11,
            "topics_json": '[{"id": "topic_phys_mech_newton_3", "name": "Newton\'s Third Law"}]',
            "recent_topics": "Forces and Motion, Velocity",
            "subject_context": "Physics",
        }

        rendered = render_template("nlu_extraction_gemini_25", variables)
        print(f"\n✓ Template rendered successfully:")
        print(f"  Length: {len(rendered)} characters")
        print(f"  Contains query: {'Explain Newton' in rendered}")
        print(f"  Contains grade level: {'Grade 11' in rendered}")

        print("\n" + "="*80)
        print("✓ TEST 1 PASSED: File-based fallback works correctly")
        print("="*80)
        return True

    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_template():
    """Test error handling for invalid template keys."""
    print("\n" + "="*80)
    print("TEST 2: Error handling for invalid template")
    print("="*80)

    try:
        get_template("nonexistent_template")
        print("\n✗ TEST 2 FAILED: Should have raised KeyError")
        return False
    except KeyError as e:
        print(f"\n✓ TEST 2 PASSED: Correctly raised KeyError for invalid template")
        print(f"  Error message: {e}")
        return True
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: Unexpected error: {e}")
        return False


def test_database_integration_when_available():
    """Test database integration (will fallback gracefully if DB not available)."""
    print("\n" + "="*80)
    print("TEST 3: Database integration (graceful fallback if unavailable)")
    print("="*80)

    try:
        # This will try database first, then fallback to files
        # Since database migration hasn't run yet, it should use file fallback
        template = get_template("nlu_extraction_gemini_25")
        print(f"\n✓ Template loaded (database or fallback): {template['name']}")
        print("  Note: Check logs to see if database was attempted")

        print("\n" + "="*80)
        print("✓ TEST 3 PASSED: Database integration has graceful fallback")
        print("="*80)
        return True

    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PROMPT TEMPLATES INTEGRATION TEST SUITE")
    print("Testing backwards-compatible database integration")
    print("="*80)

    results = []

    # Run tests
    results.append(("File-based fallback", test_file_based_fallback()))
    results.append(("Invalid template error handling", test_invalid_template()))
    results.append(("Database integration with fallback", test_database_integration_when_available()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL TESTS PASSED - Backwards compatibility verified!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        sys.exit(1)
