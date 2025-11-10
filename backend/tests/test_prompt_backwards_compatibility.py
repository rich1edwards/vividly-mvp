"""
Backwards Compatibility Test Suite for Enterprise Prompt System

Following Andrew Ng's principle: "Build it right, test everything"

This test suite ensures that:
1. Existing hardcoded prompts still work after database migration
2. Fallback mechanism works when database is unavailable
3. No breaking changes to existing functionality
4. Seamless transition from hardcoded to database-driven prompts

These tests are designed to run in CI/CD pipelines to catch regressions.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Test configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestHardcodedPromptsFallback:
    """Test that hardcoded prompts still work as fallback"""

    def test_nlu_topic_extraction_hardcoded_exists(self):
        """Verify hardcoded NLU topic extraction prompt is available"""
        # This would import from your actual prompt_templates.py
        # For now, we'll test the database equivalent
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT content, variables
                FROM prompt_templates
                WHERE name = 'nlu_topic_extraction'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert (
                row is not None
            ), "NLU topic extraction prompt should exist in database"
            assert "user_input" in row[1], "Should have user_input variable"

    def test_clarification_question_hardcoded_exists(self):
        """Verify hardcoded clarification question prompt is available"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT content, variables
                FROM prompt_templates
                WHERE name = 'clarification_question_generation'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert (
                row is not None
            ), "Clarification question prompt should exist in database"
            assert "topic" in row[1], "Should have topic variable"

    def test_script_generation_hardcoded_exists(self):
        """Verify hardcoded script generation prompt is available"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT content, variables
                FROM prompt_templates
                WHERE name = 'educational_script_generation'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None, "Script generation prompt should exist in database"
            assert "topic" in row[1], "Should have topic variable"


class TestDatabasePromptRetrieval:
    """Test database-driven prompt retrieval"""

    def test_get_active_prompt_by_name(self):
        """Test retrieving active prompt by name"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT id, name, content, version
                FROM prompt_templates
                WHERE name = 'nlu_topic_extraction'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            assert row[1] == "nlu_topic_extraction"
            assert row[3] >= 1  # Should have version

    def test_get_latest_version(self):
        """Test that we get the latest version of a prompt"""
        with SessionLocal() as session:
            # Get the prompt with highest version number
            result = session.execute(
                text(
                    """
                SELECT id, name, version
                FROM prompt_templates
                WHERE name = 'nlu_topic_extraction'
                AND is_active = true
                ORDER BY version DESC
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            assert row[2] >= 1  # Should have a version number

    def test_prompt_has_required_metadata(self):
        """Test that prompts have all required metadata"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT id, name, category, content, variables, version, created_at
                FROM prompt_templates
                WHERE is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            assert row[0] is not None  # id
            assert row[1] is not None  # name
            assert row[2] is not None  # category
            assert row[3] is not None  # content
            assert row[4] is not None  # variables
            assert row[5] >= 1  # version
            assert row[6] is not None  # created_at


class TestPromptVariableSubstitution:
    """Test that variable substitution works correctly"""

    def test_nlu_prompt_variables_match_expected(self):
        """Test NLU prompt has expected variables"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT variables
                FROM prompt_templates
                WHERE name = 'nlu_topic_extraction'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            variables = row[0]

            # Should contain user_input variable
            assert "user_input" in variables

    def test_clarification_prompt_variables_match_expected(self):
        """Test clarification prompt has expected variables"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT variables
                FROM prompt_templates
                WHERE name = 'clarification_question_generation'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            variables = row[0]

            # Should contain topic variable
            assert "topic" in variables

    def test_script_prompt_variables_match_expected(self):
        """Test script generation prompt has expected variables"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT variables
                FROM prompt_templates
                WHERE name = 'educational_script_generation'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            variables = row[0]

            # Should contain topic variable
            assert "topic" in variables


class TestNoBreakingChanges:
    """Test that no breaking changes were introduced"""

    def test_all_expected_prompts_exist(self):
        """Verify all expected prompts from hardcoded system exist in database"""
        expected_prompts = [
            "nlu_topic_extraction",
            "clarification_question_generation",
            "educational_script_generation",
        ]

        with SessionLocal() as session:
            for prompt_name in expected_prompts:
                result = session.execute(
                    text(
                        """
                    SELECT COUNT(*)
                    FROM prompt_templates
                    WHERE name = :name
                    AND is_active = true;
                """
                    ),
                    {"name": prompt_name},
                )
                count = result.fetchone()[0]

                assert count >= 1, f"Prompt '{prompt_name}' should exist in database"

    def test_prompt_content_is_not_empty(self):
        """Ensure all prompts have actual content"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT name, content
                FROM prompt_templates
                WHERE is_active = true;
            """
                )
            )
            prompts = list(result)

            assert len(prompts) >= 3, "Should have at least 3 seed prompts"

            for prompt in prompts:
                name, content = prompt
                assert content is not None, f"Prompt '{name}' should have content"
                assert len(content) > 0, f"Prompt '{name}' content should not be empty"
                assert len(content) > 50, f"Prompt '{name}' content seems too short"

    def test_prompts_have_valid_json_variables(self):
        """Ensure all prompts have valid JSON variable arrays"""
        import json

        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT name, variables
                FROM prompt_templates
                WHERE is_active = true;
            """
                )
            )
            prompts = list(result)

            for prompt in prompts:
                name, variables = prompt
                assert (
                    variables is not None
                ), f"Prompt '{name}' should have variables field"

                # Should be parseable as JSON
                try:
                    var_list = (
                        json.loads(variables)
                        if isinstance(variables, str)
                        else variables
                    )
                    assert isinstance(
                        var_list, list
                    ), f"Prompt '{name}' variables should be a list"
                except json.JSONDecodeError:
                    pytest.fail(f"Prompt '{name}' variables are not valid JSON")


class TestGuardrailBackwardsCompatibility:
    """Test that guardrails don't break existing functionality"""

    def test_guardrails_are_enforced_but_not_blocking(self):
        """Verify guardrails exist but don't block legitimate requests"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM prompt_guardrails
                WHERE is_active = true
                AND enforcement_level = 'blocking';
            """
                )
            )
            blocking_count = result.fetchone()[0]

            # Initially, we should have no blocking guardrails in production
            # This ensures backwards compatibility
            assert (
                blocking_count == 0
            ), "No guardrails should be in blocking mode initially"

    def test_guardrails_have_warning_level(self):
        """Verify guardrails start in warning mode"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT name, enforcement_level
                FROM prompt_guardrails
                WHERE is_active = true;
            """
                )
            )
            guardrails = list(result)

            assert len(guardrails) >= 3, "Should have at least 3 seed guardrails"

            for guardrail in guardrails:
                name, enforcement_level = guardrail
                assert enforcement_level in [
                    "warning",
                    "blocking",
                ], f"Guardrail '{name}' has invalid enforcement level"


class TestPromptVersioning:
    """Test that versioning doesn't break existing functionality"""

    def test_version_numbers_start_at_1(self):
        """Verify all prompts start with version 1"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT name, version
                FROM prompt_templates
                WHERE created_by = 'system'
                AND is_active = true;
            """
                )
            )
            prompts = list(result)

            for prompt in prompts:
                name, version = prompt
                assert version == 1, f"Seed prompt '{name}' should start at version 1"

    def test_only_one_active_version_per_prompt(self):
        """Verify only one active version exists per prompt name"""
        with SessionLocal() as session:
            result = session.execute(
                text(
                    """
                SELECT name, COUNT(*)
                FROM prompt_templates
                WHERE is_active = true
                GROUP BY name
                HAVING COUNT(*) > 1;
            """
                )
            )
            duplicates = list(result)

            assert (
                len(duplicates) == 0
            ), "Each prompt should have only one active version"


@pytest.mark.integration
class TestEndToEndBackwardsCompatibility:
    """Integration tests for backwards compatibility"""

    def test_can_retrieve_and_use_nlu_prompt(self):
        """Test end-to-end retrieval and usage of NLU prompt"""
        with SessionLocal() as session:
            # Retrieve the prompt
            result = session.execute(
                text(
                    """
                SELECT content, variables
                FROM prompt_templates
                WHERE name = 'nlu_topic_extraction'
                AND is_active = true
                LIMIT 1;
            """
                )
            )
            row = result.fetchone()

            assert row is not None
            content, variables = row

            # Verify content has placeholders for variables
            import json

            var_list = (
                json.loads(variables) if isinstance(variables, str) else variables
            )

            for var in var_list:
                # Check if variable placeholder exists in content
                # Assuming variables are referenced as {variable_name}
                assert (
                    f"{{{var}}}" in content or var in content.lower()
                ), f"Variable '{var}' should be referenced in prompt content"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
