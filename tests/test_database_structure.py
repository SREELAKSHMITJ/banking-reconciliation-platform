from db_connection import get_connection


def test_core_schema_exists():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # information_schema is PostgreSQL's own catalogue describing what exists 
            # in the db such as schemas, tables, views, columns, constraints, etc..

            # schemata contains list of schemas -> core is the schema -> which is basically
            # a folder inside a database

            # SELECT EXISTS -> Did that inner query find at least one matching row?

            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.schemata
                    WHERE schema_name = 'core'
                );
                """
            )

            result = cursor.fetchone()

    # This means the core schema must exist.
    assert result[0] is True


def test_required_tables_exist():

    # required_tables is a set, which contain unique values, order doesn't matter
    # we can compare groups easily
    required_tables = {
        "customers",
        "accounts",
        "transactions",
        "ledger_entries",
        "settlement_records",
        "reconciliation_rules",
        "reconciliation_exceptions",
        "exception_status_history",
        "data_quality_checks",
        "data_quality_runs",
        "data_quality_results"
    }

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # table_type = 'BASE TABLE' means Give me actual stored tables, not views.
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'core'
                  AND table_type = 'BASE TABLE';
                """
            )

            # fetchall() since we expect many rows
            rows = cursor.fetchall()

    # This is set comprehension
    existing_tables = {row[0] for row in rows}

    # Is every item in required_tables also present in existing_tables?
    assert required_tables.issubset(existing_tables)


def test_required_views_exist():

    required_views = {
        "reconciliation_base",
        "detected_reconciliation_rules",
        "detected_data_quality_issues",
        "data_quality_summary"
    }

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = 'core';
                """
            )

            rows = cursor.fetchall()

    existing_views = {row[0] for row in rows}

    assert required_views.issubset(existing_views)


def test_reconciliation_rule_count():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.reconciliation_rules;
                """
            )

            result = cursor.fetchone()

    assert result[0] == 24


def test_data_quality_check_count():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.data_quality_checks;
                """
            )

            result = cursor.fetchone()

    assert result[0] == 20


def test_data_quality_summary_has_all_checks():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.data_quality_summary;
                """
            )

            result = cursor.fetchone()

    assert result[0] == 20