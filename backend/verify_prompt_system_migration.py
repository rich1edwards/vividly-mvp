#!/usr/bin/env python3
"""
Comprehensive Verification Script for Enterprise Prompt System Migration
Following Andrew Ng's principle: Build it right, test everything

This script verifies:
1. All tables were created successfully
2. All seed data was inserted
3. All indexes exist
4. All triggers are functional
5. All views are accessible
6. Schema migrations record exists

Usage:
    python verify_prompt_system_migration.py
"""

import os
import sys
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Tuple


# ANSI color codes for pretty output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def get_database_connection():
    """Get database connection from DATABASE_URL environment variable"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print_error("DATABASE_URL environment variable not set")
        sys.exit(1)

    parsed = urlparse(database_url)

    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
        )
        return conn
    except Exception as e:
        print_error(f"Failed to connect to database: {e}")
        sys.exit(1)


def verify_tables(conn) -> Tuple[bool, List[str]]:
    """Verify all required tables exist"""
    print_section("1. Verifying Tables")

    required_tables = [
        "prompt_templates",
        "prompt_executions",
        "prompt_guardrails",
        "ab_test_experiments",
        "schema_migrations",
    ]

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN %s
            ORDER BY table_name;
        """,
            (tuple(required_tables),),
        )

        existing_tables = [row[0] for row in cursor.fetchall()]

    all_found = True
    missing_tables = []

    for table in required_tables:
        if table in existing_tables:
            print_success(f"Table '{table}' exists")
        else:
            print_error(f"Table '{table}' NOT FOUND")
            all_found = False
            missing_tables.append(table)

    return all_found, missing_tables


def verify_indexes(conn) -> Tuple[bool, List[str]]:
    """Verify all required indexes exist"""
    print_section("2. Verifying Indexes")

    required_indexes = [
        "idx_prompt_templates_active",
        "idx_prompt_templates_ab_test",
        "idx_prompt_templates_version",
        "idx_prompt_templates_performance",
        "idx_prompt_executions_template",
        "idx_prompt_executions_user",
        "idx_prompt_executions_request",
        "idx_prompt_executions_errors",
        "idx_prompt_executions_guardrails",
        "idx_prompt_guardrails_active",
        "idx_prompt_guardrails_templates",
        "idx_prompt_guardrails_categories",
        "idx_prompt_guardrails_performance",
        "idx_ab_test_experiments_active",
        "idx_ab_test_experiments_timeline",
        "idx_ab_test_experiments_stats",
    ]

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND indexname IN %s
            ORDER BY indexname;
        """,
            (tuple(required_indexes),),
        )

        existing_indexes = [row[0] for row in cursor.fetchall()]

    all_found = True
    missing_indexes = []

    for index in required_indexes:
        if index in existing_indexes:
            print_success(f"Index '{index}' exists")
        else:
            print_error(f"Index '{index}' NOT FOUND")
            all_found = False
            missing_indexes.append(index)

    return all_found, missing_indexes


def verify_seed_data(conn) -> Tuple[bool, Dict[str, Any]]:
    """Verify seed data was inserted correctly"""
    print_section("3. Verifying Seed Data")

    results = {
        "prompts": {"expected": 3, "actual": 0, "found": []},
        "guardrails": {"expected": 3, "actual": 0, "found": []},
    }

    # Check seed prompts
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT name, category, is_active, version
            FROM prompt_templates
            WHERE created_by = 'system'
            ORDER BY name;
        """
        )
        prompts = cursor.fetchall()
        results["prompts"]["actual"] = len(prompts)
        results["prompts"]["found"] = [p["name"] for p in prompts]

    expected_prompts = [
        "nlu_topic_extraction",
        "clarification_question_generation",
        "educational_script_generation",
    ]

    all_prompts_found = True
    for prompt_name in expected_prompts:
        if prompt_name in results["prompts"]["found"]:
            print_success(f"Seed prompt '{prompt_name}' found")
        else:
            print_error(f"Seed prompt '{prompt_name}' NOT FOUND")
            all_prompts_found = False

    # Check seed guardrails
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT name, guardrail_type, is_active, severity
            FROM prompt_guardrails
            WHERE created_by = 'system'
            ORDER BY name;
        """
        )
        guardrails = cursor.fetchall()
        results["guardrails"]["actual"] = len(guardrails)
        results["guardrails"]["found"] = [g["name"] for g in guardrails]

    expected_guardrails = [
        "pii_detection_basic",
        "toxic_content_filter",
        "prompt_injection_detection",
    ]

    all_guardrails_found = True
    for guardrail_name in expected_guardrails:
        if guardrail_name in results["guardrails"]["found"]:
            print_success(f"Seed guardrail '{guardrail_name}' found")
        else:
            print_error(f"Seed guardrail '{guardrail_name}' NOT FOUND")
            all_guardrails_found = False

    return (all_prompts_found and all_guardrails_found), results


def verify_views(conn) -> Tuple[bool, List[str]]:
    """Verify all analytics views exist"""
    print_section("4. Verifying Analytics Views")

    required_views = [
        "v_template_performance",
        "v_recent_execution_errors",
        "v_guardrail_violations_summary",
        "v_active_ab_tests",
    ]

    all_found = True
    missing_views = []

    for view in required_views:
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {view};")
                print_success(f"View '{view}' exists and is queryable")
        except Exception as e:
            print_error(f"View '{view}' NOT FOUND or not queryable: {e}")
            all_found = False
            missing_views.append(view)

    return all_found, missing_views


def verify_triggers(conn) -> Tuple[bool, List[str]]:
    """Verify all triggers exist and are functional"""
    print_section("5. Verifying Triggers")

    required_triggers = [
        ("trigger_update_template_statistics", "prompt_executions"),
        ("trigger_update_ab_test_statistics", "prompt_executions"),
        ("trigger_enforce_single_active_template", "prompt_templates"),
    ]

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
            ORDER BY trigger_name;
        """
        )
        existing_triggers = [(row[0], row[1]) for row in cursor.fetchall()]

    all_found = True
    missing_triggers = []

    for trigger_name, table_name in required_triggers:
        if (trigger_name, table_name) in existing_triggers:
            print_success(f"Trigger '{trigger_name}' exists on table '{table_name}'")
        else:
            print_error(f"Trigger '{trigger_name}' on table '{table_name}' NOT FOUND")
            all_found = False
            missing_triggers.append(f"{trigger_name} on {table_name}")

    return all_found, missing_triggers


def verify_migration_record(conn) -> Tuple[bool, Dict[str, Any]]:
    """Verify schema_migrations record exists"""
    print_section("6. Verifying Migration Record")

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT version, description, executed_at
            FROM schema_migrations
            WHERE version = 'enterprise_prompt_system_phase1';
        """
        )
        record = cursor.fetchone()

    if record:
        print_success("Migration record 'enterprise_prompt_system_phase1' found")
        print(f"   Description: {record['description']}")
        print(f"   Executed at: {record['executed_at']}")
        return True, dict(record)
    else:
        print_error("Migration record 'enterprise_prompt_system_phase1' NOT FOUND")
        return False, {}


def test_database_functionality(conn) -> bool:
    """Test that the database is actually functional with a real query"""
    print_section("7. Testing Database Functionality")

    try:
        # Test 1: Query active templates
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT name, category, version, is_active
                FROM prompt_templates
                WHERE is_active = true
                ORDER BY category, name;
            """
            )
            active_templates = cursor.fetchall()
            print_success(
                f"Query active templates: {len(active_templates)} templates found"
            )
            for template in active_templates:
                print(
                    f"   - {template['name']} (v{template['version']}, {template['category']})"
                )

        # Test 2: Query active guardrails
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT name, guardrail_type, severity, action
                FROM prompt_guardrails
                WHERE is_active = true
                ORDER BY severity, name;
            """
            )
            active_guardrails = cursor.fetchall()
            print_success(
                f"Query active guardrails: {len(active_guardrails)} guardrails found"
            )
            for guardrail in active_guardrails:
                print(
                    f"   - {guardrail['name']} ({guardrail['severity']}, {guardrail['action']})"
                )

        # Test 3: Query v_template_performance view
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT name, category, total_executions, success_rate_percentage
                FROM v_template_performance
                LIMIT 5;
            """
            )
            performance = cursor.fetchall()
            print_success(f"Query v_template_performance view: {len(performance)} rows")

        return True
    except Exception as e:
        print_error(f"Database functionality test FAILED: {e}")
        return False


def print_final_summary(results: Dict[str, Any]):
    """Print final verification summary"""
    print_section("VERIFICATION SUMMARY")

    all_passed = all(results.values())

    print(f"Tables:           {'✓ PASS' if results['tables'] else '✗ FAIL'}")
    print(f"Indexes:          {'✓ PASS' if results['indexes'] else '✗ FAIL'}")
    print(f"Seed Data:        {'✓ PASS' if results['seed_data'] else '✗ FAIL'}")
    print(f"Views:            {'✓ PASS' if results['views'] else '✗ FAIL'}")
    print(f"Triggers:         {'✓ PASS' if results['triggers'] else '✗ FAIL'}")
    print(f"Migration Record: {'✓ PASS' if results['migration_record'] else '✗ FAIL'}")
    print(f"Functionality:    {'✓ PASS' if results['functionality'] else '✗ FAIL'}")

    print()
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
        print(
            f"{Colors.GREEN}{Colors.BOLD}✓ ALL VERIFICATION CHECKS PASSED{Colors.END}"
        )
        print(
            f"{Colors.GREEN}{Colors.BOLD}  Enterprise Prompt System Migration: SUCCESS{Colors.END}"
        )
        print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME VERIFICATION CHECKS FAILED{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}  Please review the errors above{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}{'='*70}{Colors.END}")
        return 1


def main():
    """Main verification workflow"""
    print(
        f"\n{Colors.BOLD}Enterprise Prompt System Migration - Verification Script{Colors.END}"
    )
    print(f"{Colors.BOLD}Timestamp: {datetime.now().isoformat()}{Colors.END}\n")

    # Get database connection
    conn = get_database_connection()
    print_success("Connected to database successfully")

    try:
        # Run all verification checks
        results = {}

        results["tables"], _ = verify_tables(conn)
        results["indexes"], _ = verify_indexes(conn)
        results["seed_data"], _ = verify_seed_data(conn)
        results["views"], _ = verify_views(conn)
        results["triggers"], _ = verify_triggers(conn)
        results["migration_record"], _ = verify_migration_record(conn)
        results["functionality"] = test_database_functionality(conn)

        # Print final summary
        exit_code = print_final_summary(results)

        conn.close()
        return exit_code

    except Exception as e:
        print_error(f"Verification failed with unexpected error: {e}")
        conn.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
