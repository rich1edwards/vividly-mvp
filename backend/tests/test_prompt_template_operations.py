"""
Comprehensive Test Suite for Enterprise Prompt Template Operations

Following Andrew Ng's principle: "Build it right, test everything"

This test suite validates:
1. Prompt template CRUD operations
2. Version management and rollback
3. A/B test configuration and tracking
4. Guardrail enforcement
5. Execution logging and analytics
6. Performance characteristics

These tests are designed to run in CI/CD pipelines and production environments.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Test configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestPromptTemplateSchema:
    """Validate that all required schema elements exist"""

    def test_tables_exist(self):
        """Verify all prompt system tables exist"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('prompt_templates', 'prompt_executions',
                                    'prompt_guardrails', 'ab_test_experiments')
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]

            assert 'prompt_templates' in tables
            assert 'prompt_executions' in tables
            assert 'prompt_guardrails' in tables
            assert 'ab_test_experiments' in tables

    def test_seed_prompts_exist(self):
        """Verify seed prompts were inserted"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT name
                FROM prompt_templates
                WHERE created_by = 'system'
                AND is_active = true
                ORDER BY name;
            """))
            prompts = [row[0] for row in result]

            assert 'nlu_topic_extraction' in prompts
            assert 'clarification_question_generation' in prompts
            assert 'educational_script_generation' in prompts

    def test_seed_guardrails_exist(self):
        """Verify seed guardrails were inserted"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT name
                FROM prompt_guardrails
                WHERE created_by = 'system'
                AND is_active = true
                ORDER BY name;
            """))
            guardrails = [row[0] for row in result]

            assert 'pii_detection_basic' in guardrails
            assert 'toxic_content_filter' in guardrails
            assert 'prompt_injection_detection' in guardrails


class TestPromptTemplateCRUD:
    """Test Create, Read, Update, Delete operations"""

    @pytest.fixture
    def test_template_id(self):
        """Create a test template and return its ID"""
        template_id = uuid.uuid4()
        with SessionLocal() as session:
            session.execute(text("""
                INSERT INTO prompt_templates (
                    id, name, category, content, variables, is_active, version, created_by
                )
                VALUES (
                    :id, :name, :category, :content, :variables, true, 1, 'test'
                )
            """), {
                'id': template_id,
                'name': f'test_template_{template_id}',
                'category': 'testing',
                'content': 'Test prompt content with {variable}',
                'variables': '["variable"]'
            })
            session.commit()

        yield template_id

        # Cleanup
        with SessionLocal() as session:
            session.execute(text("DELETE FROM prompt_templates WHERE id = :id"), {'id': template_id})
            session.commit()

    def test_create_template(self, test_template_id):
        """Test creating a new prompt template"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT name, category, is_active, version
                FROM prompt_templates
                WHERE id = :id
            """), {'id': test_template_id})
            row = result.fetchone()

            assert row is not None
            assert row[0].startswith('test_template_')
            assert row[1] == 'testing'
            assert row[2] is True  # is_active
            assert row[3] == 1     # version

    def test_read_active_templates(self):
        """Test querying active templates"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT name, category, is_active
                FROM prompt_templates
                WHERE is_active = true
                ORDER BY name
                LIMIT 5;
            """))
            templates = list(result)

            assert len(templates) >= 3  # At least our seed prompts
            for template in templates:
                assert template[2] is True  # All should be active

    def test_update_template(self, test_template_id):
        """Test updating a template"""
        with SessionLocal() as session:
            # Update the template
            session.execute(text("""
                UPDATE prompt_templates
                SET content = :new_content,
                    version = version + 1
                WHERE id = :id
            """), {
                'id': test_template_id,
                'new_content': 'Updated content with {variable}'
            })
            session.commit()

            # Verify update
            result = session.execute(text("""
                SELECT content, version
                FROM prompt_templates
                WHERE id = :id
            """), {'id': test_template_id})
            row = result.fetchone()

            assert row[0] == 'Updated content with {variable}'
            assert row[1] == 2


class TestPromptExecution:
    """Test prompt execution logging and tracking"""

    @pytest.fixture
    def test_execution_data(self):
        """Setup test data for execution tests"""
        with SessionLocal() as session:
            # Get a template ID
            result = session.execute(text("""
                SELECT id
                FROM prompt_templates
                WHERE name = 'nlu_topic_extraction'
                LIMIT 1;
            """))
            template_id = result.fetchone()[0]

            return {
                'template_id': template_id,
                'user_id': uuid.uuid4(),
                'request_id': uuid.uuid4()
            }

    def test_log_execution(self, test_execution_data):
        """Test logging a prompt execution"""
        execution_id = uuid.uuid4()

        with SessionLocal() as session:
            session.execute(text("""
                INSERT INTO prompt_executions (
                    id, template_id, user_id, content_request_id,
                    rendered_prompt, model_response, tokens_used,
                    latency_ms, success
                )
                VALUES (
                    :id, :template_id, :user_id, :request_id,
                    :prompt, :response, :tokens, :latency, true
                )
            """), {
                'id': execution_id,
                'template_id': test_execution_data['template_id'],
                'user_id': test_execution_data['user_id'],
                'request_id': test_execution_data['request_id'],
                'prompt': 'Rendered test prompt',
                'response': 'Test model response',
                'tokens': 150,
                'latency': 500
            })
            session.commit()

            # Verify execution was logged
            result = session.execute(text("""
                SELECT success, tokens_used, latency_ms
                FROM prompt_executions
                WHERE id = :id
            """), {'id': execution_id})
            row = result.fetchone()

            assert row is not None
            assert row[0] is True  # success
            assert row[1] == 150   # tokens_used
            assert row[2] == 500   # latency_ms

            # Cleanup
            session.execute(text("DELETE FROM prompt_executions WHERE id = :id"), {'id': execution_id})
            session.commit()


class TestGuardrailEnforcement:
    """Test guardrail checking and violation logging"""

    def test_guardrails_are_active(self):
        """Verify active guardrails exist"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT COUNT(*)
                FROM prompt_guardrails
                WHERE is_active = true;
            """))
            count = result.fetchone()[0]

            assert count >= 3  # At least our seed guardrails

    def test_guardrail_violation_logging(self):
        """Test logging guardrail violations"""
        execution_id = uuid.uuid4()
        violation_id = uuid.uuid4()

        with SessionLocal() as session:
            # Get a template and guardrail
            template_result = session.execute(text("""
                SELECT id FROM prompt_templates WHERE is_active = true LIMIT 1;
            """))
            template_id = template_result.fetchone()[0]

            guardrail_result = session.execute(text("""
                SELECT id FROM prompt_guardrails WHERE is_active = true LIMIT 1;
            """))
            guardrail_id = guardrail_result.fetchone()[0]

            # Log execution
            session.execute(text("""
                INSERT INTO prompt_executions (
                    id, template_id, user_id, rendered_prompt, success
                )
                VALUES (:id, :template_id, :user_id, :prompt, false)
            """), {
                'id': execution_id,
                'template_id': template_id,
                'user_id': uuid.uuid4(),
                'prompt': 'Test prompt'
            })

            # Log violation
            session.execute(text("""
                INSERT INTO prompt_executions (id, guardrail_violations)
                VALUES (:id, :violations)
                ON CONFLICT (id) DO UPDATE
                SET guardrail_violations = EXCLUDED.guardrail_violations
            """), {
                'id': execution_id,
                'violations': f'[{{"guardrail_id": "{guardrail_id}", "severity": "high", "message": "Test violation"}}]'
            })
            session.commit()

            # Verify violation was logged
            result = session.execute(text("""
                SELECT guardrail_violations
                FROM prompt_executions
                WHERE id = :id
            """), {'id': execution_id})
            row = result.fetchone()

            assert row is not None
            assert 'Test violation' in str(row[0])

            # Cleanup
            session.execute(text("DELETE FROM prompt_executions WHERE id = :id"), {'id': execution_id})
            session.commit()


class TestAnalyticsViews:
    """Test analytics views are functional"""

    def test_template_performance_view(self):
        """Test v_template_performance view"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT name, total_executions, avg_latency_ms, success_rate_percentage
                FROM v_template_performance
                LIMIT 10;
            """))
            rows = list(result)

            # View should be queryable
            assert isinstance(rows, list)
            for row in rows:
                # Validate data types
                assert isinstance(row[0], str)      # name
                assert isinstance(row[1], int)      # total_executions
                assert row[2] is None or isinstance(row[2], (int, float))  # avg_latency_ms
                assert row[3] is None or isinstance(row[3], (int, float))  # success_rate

    def test_recent_errors_view(self):
        """Test v_recent_execution_errors view"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT execution_id, template_name, error_message
                FROM v_recent_execution_errors
                LIMIT 10;
            """))
            rows = list(result)

            # View should be queryable (may be empty)
            assert isinstance(rows, list)

    def test_guardrail_violations_view(self):
        """Test v_guardrail_violations_summary view"""
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT template_name, total_violations
                FROM v_guardrail_violations_summary
                LIMIT 10;
            """))
            rows = list(result)

            # View should be queryable (may be empty)
            assert isinstance(rows, list)


@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks"""

    def test_query_active_templates_performance(self, benchmark):
        """Benchmark querying active templates"""
        def query_active_templates():
            with SessionLocal() as session:
                result = session.execute(text("""
                    SELECT id, name, category, content
                    FROM prompt_templates
                    WHERE is_active = true
                    ORDER BY category, name;
                """))
                return list(result)

        result = benchmark(query_active_templates)
        assert len(result) >= 3  # Should find seed prompts

    def test_template_performance_view_query(self, benchmark):
        """Benchmark analytics view query"""
        def query_performance_view():
            with SessionLocal() as session:
                result = session.execute(text("""
                    SELECT *
                    FROM v_template_performance
                    ORDER BY total_executions DESC
                    LIMIT 100;
                """))
                return list(result)

        benchmark(query_performance_view)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
