#!/usr/bin/env python3
"""
Quick local test of clarification service logic.
Testing the rules BEFORE deployment.
"""
import sys
sys.path.insert(0, "/Users/richedwards/AI-Dev-Projects/Vividly/backend")

from app.services.clarification_service import ClarificationService

def test_query(query: str, expected_clarification: bool):
    """Test a single query."""
    service = ClarificationService()
    result = service.check_clarification_needed(query, grade_level=10)

    actual = result["needs_clarification"]
    status = "✓" if actual == expected_clarification else "✗"

    print(f"{status} Query: '{query}'")
    print(f"  Expected clarification: {expected_clarification}, Got: {actual}")
    if actual:
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Questions: {result['clarifying_questions'][:2]}")  # First 2
    print()

    return actual == expected_clarification

def main():
    print("=" * 80)
    print("Local Clarification Service Test")
    print("=" * 80)
    print()

    tests = [
        # Should trigger clarification (vague queries)
        ("Tell me about science", True),
        ("Explain math", True),
        ("What is biology?", True),
        ("Teach me history", True),
        ("Help with chemistry", True),

        # Should NOT trigger clarification (clear queries)
        ("Explain how photosynthesis works in plants, including the light-dependent and light-independent reactions", False),
        ("What are the main causes of World War II and how did they lead to the conflict in Europe", False),
        ("Describe the process of mitosis and meiosis and explain the differences between them in cell division", False),
        ("How does Newton's third law apply to rocket propulsion and what are the forces involved in launching a satellite", False),
    ]

    passed = 0
    failed = 0

    for query, expected in tests:
        if test_query(query, expected):
            passed += 1
        else:
            failed += 1

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
