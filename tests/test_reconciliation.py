import pytest
from db_connection import get_connection

def get_detected_rules(reference_number):

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT rule_code
                FROM core.detected_reconciliation_rules
                WHERE reference_number = %s
                ORDER BY rule_code;
                """,
                (reference_number,)
            )

            rows = cursor.fetchall()

    return {row[0] for row in rows}

# Pytest parameterization: Run the same test function repeatedly, 
# but feed it different test data each time.

@pytest.mark.parametrize(
    "reference_number, expected_rules",
    [
        (
            "TXN10003",
            {"REC004", "REC006"}
        ),
        (
            "QA_AMOUNT_SETTLE_001",
            {"REC005", "REC006"}
        ),
        (
            "QA_DUP_TXN_001B",
            {"REC017"}
        ), 
        (
            "QA_DUP_LEDGER_001",
            {"REC018"}
        ),
        (
            "QA_DUP_SETTLE_001",
            {"REC019"}
        ),
        (
            "QA_TIME_020",
            {"REC020"}
        ),
        (
            "QA_TIME_021",
            {"REC021"}
        ),
        (
            "QA_TIME_022",
            {"REC022"}
        ),
        (
            "QA_TIME_023",
            {"REC023", "REC024"}
        ),
        (
            "QA_TIME_024",
            {"REC024"}
        ),
        (
            "QA_ACC_TYPE_001",
            {"REC013", "REC014", "REC015", "REC016"}
        ),
    ]
)
def test_specialized_reconciliation_rules(reference_number,expected_rules):

    detected_rules = get_detected_rules(
        reference_number
    )

    assert detected_rules == expected_rules


def test_full_status_matrix_regression():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            # 1. Get all 26 test cases
            cursor.execute(
                """
                SELECT test_case_id, transaction_state, ledger_state, settlement_state
                FROM core.status_test_matrix
                ORDER BY test_case_id;
                """
            )

            test_cases = cursor.fetchall()

            # 2. Get all expected rules
            cursor.execute(
                """
                SELECT test_case_id, rule_code
                FROM core.status_test_expected_rules
                ORDER BY test_case_id, rule_code;
                """
            )

            expected_rows = cursor.fetchall()

    expected_by_case = {}

    for test_case_id, rule_code in expected_rows:
        if test_case_id not in expected_by_case:
            expected_by_case[test_case_id] = set()
        expected_by_case[test_case_id].add(rule_code)

    for (test_case_id, transaction_state, ledger_state, settlement_state) in test_cases:
        reference_number = f"TST{test_case_id:03d}"
        expected_rules = expected_by_case.get(test_case_id, set())
        actual_rules = get_detected_rules(reference_number)

        assert actual_rules == expected_rules, (
            f"Test case {test_case_id} failed. "
            f"States: "
            f"{transaction_state} / "
            f"{ledger_state} / "
            f"{settlement_state}. "
            f"Expected: {expected_rules}. "
            f"Actual: {actual_rules}."
        )
    