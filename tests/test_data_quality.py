from db_connection import get_connection
from run_data_quality import run_data_quality

def get_dq_issues(check_code):
    with get_connection() as connection:
        with connection.cursor() as cursor: 
            cursor.execute(
                """
                SELECT record_key
                FROM core.detected_data_quality_issues
                WHERE check_code = %s;
                """, (check_code,)
            )
            rows = cursor.fetchall()
    return {row[0] for row in rows}

def test_duplicate_ledger_dq_detection():

    detected_records = get_dq_issues("DQ012")

    assert "QA_DUP_LEDGER_001" in detected_records


def test_duplicate_settlement_dq_detection():

    detected_records = get_dq_issues("DQ013")

    assert "QA_DUP_SETTLE_001" in detected_records


def test_data_quality_summary_pass_fail_logic():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT check_code, result_status, failure_count
                FROM core.data_quality_summary
                ORDER BY check_code;
                """
            )
            rows = cursor.fetchall()

    assert len(rows) == 20

    for check_code, result_status, failure_count in rows:
        if failure_count == 0:
            expected_status = "PASS"
        else:
            expected_status = "FAIL" 

        assert result_status == expected_status, (
            f"{check_code}: "
            f"failure_count={failure_count}, "
            f"expected={expected_status}, "
            f"actual={result_status}"
        )  

def test_invalid_currency_detection():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Find one normal CAD account 
            cursor.execute(
                """
                SELECT account_id 
                FROM core.accounts
                WHERE currency = 'CAD'
                ORDER BY account_id
                LIMIT 1;
                """
            )

            result = cursor.fetchone()
            account_id = result[0]

            # Temporarily make the data bad
            cursor.execute(
                """
                UPDATE core.accounts
                SET currency = 'USD'
                WHERE account_id = %s;
                """, (account_id,)
            )

            # Check whether DQ007 detects it
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.detected_data_quality_issues
                WHERE check_code = 'DQ007'
                    AND record_key = %s;
                """, (str(account_id),)
            )

            failure_count = cursor.fetchone()[0]

            # Undo the temporary test data
            connection.rollback()

    assert failure_count == 1


def test_missing_transaction_field_detection():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT transaction_id
                FROM core.transactions
                WHERE channel IS NOT NULL
                ORDER BY transaction_id
                LIMIT 1;
                """
            )

            result = cursor.fetchone()

            assert result is not None

            transaction_id = result[0]

            cursor.execute(
                """
                 UPDATE core.transactions
                SET channel = NULL
                WHERE transaction_id = %s;
                """,
                (transaction_id,)
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.detected_data_quality_issues
                WHERE check_code = 'DQ003'
                  AND record_key = %s;
                """,
                (str(transaction_id),)
            )

            detected_count = cursor.fetchone()[0]

            connection.rollback()

    assert detected_count == 1

def test_ledger_account_not_found_detection():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Find one normal ledger entry
            cursor.execute(
                """
                SELECT ledger_entry_id
                FROM core.ledger_entries
                ORDER BY ledger_entry_id
                LIMIT 1;
                """
            )

            result = cursor.fetchone()

            assert result is not None

            ledger_entry_id = result[0]


            # Temporarily give it an account number
            # that does not exist in core.accounts
            cursor.execute(
                """
                UPDATE core.ledger_entries
                SET account_number = 'TEST_INVALID_ACCOUNT'
                WHERE ledger_entry_id = %s;
                """,
                (ledger_entry_id,)
            )


            # DQ016 should detect it
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.detected_data_quality_issues
                WHERE check_code = 'DQ016'
                  AND record_key = %s;
                """,
                (str(ledger_entry_id),)
            )

            detected_count = cursor.fetchone()[0]

            connection.rollback()

    assert detected_count == 1



def test_future_transaction_timestamp_detection():

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Find one transaction
            cursor.execute(
                """
                SELECT transaction_id
                FROM core.transactions
                ORDER BY transaction_id
                LIMIT 1;
                """
            )

            result = cursor.fetchone()

            assert result is not None

            transaction_id = result[0]


            # Temporarily move its timestamp into the future
            cursor.execute(
                """
                UPDATE core.transactions
                SET transaction_time =
                    CURRENT_TIMESTAMP + INTERVAL '1 day'
                WHERE transaction_id = %s;
                """,
                (transaction_id,)
            )


            # DQ018 should detect it
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.detected_data_quality_issues
                WHERE check_code = 'DQ018'
                  AND record_key = %s;
                """,
                (str(transaction_id),)
            )

            detected_count = cursor.fetchone()[0]

            connection.rollback()

    assert detected_count == 1

def test_data_quality_run_saves_all_results():

    run_id = run_data_quality()

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:

                # Check the run itself
                cursor.execute(
                    """
                    SELECT run_status, completed_at
                    FROM core.data_quality_runs
                    WHERE run_id = %s;
                    """, (run_id,)
                )

                run_status, completed_at = cursor.fetchone()

                # Count results saved for this run
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM core.data_quality_results
                    WHERE run_id = %s;
                    """, (run_id,)
                )

                result_count = cursor.fetchone()[0]

        assert run_status == 'COMPLETED'
        assert completed_at is not None
        assert result_count == 20

    finally:
        # Remove the test run after Pytest finishes
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM core.data_quality_results
                    WHERE run_id = %s;
                    """,
                    (run_id,)
                )

                cursor.execute(
                    """
                    DELETE FROM core.data_quality_runs
                    WHERE run_id = %s;
                    """,
                    (run_id,)
                )

                # we delete data_quality_results first because they reference data_quality_runs.run_id through a foreign key.


# try: perform the test
# finally: cleanup
# No matter whether the assertions pass or fail, try to clean up the test data.
# Because run_data_quality() actually inserts permanent rows.
# Without cleanup, every time you run Pytest you'd create: Run 8, Run 9, Run 10, Run 11... just from testing