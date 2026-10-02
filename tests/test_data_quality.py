from db_connection import get_connection

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

    