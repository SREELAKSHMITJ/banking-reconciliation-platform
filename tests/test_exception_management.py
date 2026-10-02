import pytest

from db_connection import get_connection
from load_exceptions import load_reconciliation_exceptions
from update_exception_status import update_exception_status

def test_exception_loader_is_complete_and_idempotent():

    # Count existing exceptions before loader runs
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.reconciliation_exceptions;
                """
            )

            count_before = cursor.fetchone()[0]


    # Run the real loader
    load_reconciliation_exceptions()


    # Count after first run
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.reconciliation_exceptions;
                """
            )

            count_after_first_run = cursor.fetchone()[0]


    # Run loader again
    load_reconciliation_exceptions()


    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Count after second run
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.reconciliation_exceptions;
                """
            )

            count_after_second_run = cursor.fetchone()[0]


            # Check whether any detected reconciliation rule
            # is still missing from the exception table
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM core.detected_reconciliation_rules d
                LEFT JOIN core.reconciliation_exceptions e
                    ON d.reference_number = e.reference_number
                   AND d.rule_code = e.rule_code
                WHERE e.exception_id IS NULL;
                """
            )

            missing_exception_count = cursor.fetchone()[0]


    assert count_after_first_run >= count_before
    assert count_after_second_run == count_after_first_run
    assert missing_exception_count == 0

# temporary pytest exception
def test_exception_lifecycle_and_history():

    reference_number = "PYTEST_LIFECYCLE_001"

    exception_id = None

    try:

        # Clean up any leftover record from an interrupted old test
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM core.exception_status_history
                    WHERE exception_id IN (
                        SELECT exception_id
                        FROM core.reconciliation_exceptions
                        WHERE reference_number = %s
                    );
                    """,
                    (reference_number,)
                )

                cursor.execute(
                    """
                    DELETE FROM core.reconciliation_exceptions
                    WHERE reference_number = %s;
                    """,
                    (reference_number,)
                )


        # Create a fresh OPEN exception
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO core.reconciliation_exceptions
                    (
                        reference_number,
                        rule_code,
                        severity,
                        status
                    )
                    VALUES (%s, 'REC001', 'HIGH', 'OPEN')
                    RETURNING exception_id;
                    """,
                    (reference_number,)
                )

                exception_id = cursor.fetchone()[0]


        # OPEN → IN_PROGRESS
        update_exception_status(
            exception_id,
            "IN_PROGRESS",
            "Pytest moved exception to investigation"
        )


        # IN_PROGRESS → RESOLVED
        update_exception_status(
            exception_id,
            "RESOLVED",
            "Pytest resolved exception"
        )


        # Check RESOLVED state
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT status, resolved_at
                    FROM core.reconciliation_exceptions
                    WHERE exception_id = %s;
                    """,
                    (exception_id,)
                )

                status, resolved_at = cursor.fetchone()


        assert status == "RESOLVED"
        assert resolved_at is not None


        # RESOLVED → OPEN
        update_exception_status(
            exception_id,
            "OPEN",
            "Pytest reopened exception"
        )


        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT status, resolved_at
                    FROM core.reconciliation_exceptions
                    WHERE exception_id = %s;
                    """,
                    (exception_id,)
                )

                status, resolved_at = cursor.fetchone()


                # Get lifecycle history
                cursor.execute(
                    """
                    SELECT old_status, new_status
                    FROM core.exception_status_history
                    WHERE exception_id = %s
                    ORDER BY history_id;
                    """,
                    (exception_id,)
                )

                history = cursor.fetchall()


        assert status == "OPEN"
        assert resolved_at is None

        assert history == [
            ("OPEN", "IN_PROGRESS"),
            ("IN_PROGRESS", "RESOLVED"),
            ("RESOLVED", "OPEN")
        ]


        # OPEN → RESOLVED is NOT allowed directly
        with pytest.raises(ValueError):

            update_exception_status(
                exception_id,
                "RESOLVED",
                "This transition should fail"
            )


    finally:

        # Remove Pytest-created data
        if exception_id is not None:

            with get_connection() as connection:
                with connection.cursor() as cursor:

                    cursor.execute(
                        """
                        DELETE FROM core.exception_status_history
                        WHERE exception_id = %s;
                        """,
                        (exception_id,)
                    )

                    cursor.execute(
                        """
                        DELETE FROM core.reconciliation_exceptions
                        WHERE exception_id = %s;
                        """,
                        (exception_id,)
                    )