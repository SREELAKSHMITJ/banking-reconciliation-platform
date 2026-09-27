from db_connection import get_connection

def run_data_quality():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            # ----------------------------------------
            # 1. START A NEW DQ RUN
            # ----------------------------------------

            cursor.execute(
                """
                INSERT INTO core.data_quality_runs
                DEFAULT VALUES
                RETURNING run_id;
                """
            )

            result = cursor.fetchone()
            run_id = result[0]

            # ----------------------------------------
            # 2. SAVE RESULTS FOR ALL 20 CHECKS
            # ----------------------------------------

            cursor.execute(
                """
                INSERT INTO core.data_quality_results
                (
                    run_id,
                    check_code,
                    result_status,
                    checked_row_count,
                    failure_count,
                    details
                )
                SELECT %s, check_code,  
                    result_status,
                    checked_row_count,
                    failure_count,
                    CASE
                        WHEN failure_count = 0
                            THEN 'No data quality issues detected'
                        ELSE
                            failure_count::TEXT
                            || ' data quality issue(s) detected'
                    END

                FROM core.data_quality_summary;
                """, (run_id,)
            )

            # ----------------------------------------
            # 3. MARK RUN AS COMPLETED
            # ----------------------------------------

            cursor.execute(
                """
                UPDATE core.data_quality_runs
                SET run_status = 'COMPLETED',
                    completed_at = CURRENT_TIMESTAMP
                WHERE run_id = %s;
                """, (run_id,)
            )
    return run_id

if __name__ == "__main__":
    run_id = run_data_quality()
    print(
        f"Data Quality run successfully completed. "
        f"Run ID: {run_id}"
    )
