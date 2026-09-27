# runs reconciliation results into exception management

# idempotent behaviour -> Running the same operation repeatedly 
# doesn't keep creating duplicate results. due to the exception -> 
# UNIQUE (reference_number, rule_code) & ON CONFLICT (reference_number, rule_code)
# DO NOTHING

from db_connection import get_connection

def load_reconciliation_exceptions():
    query = """
            INSERT INTO core.reconciliation_exceptions
            (
            reference_number,
            rule_code,
            variance,
            severity
            )

            SELECT
                d.reference_number,
                d.rule_code,
                d.variance,
                r.default_severity

            FROM core.detected_reconciliation_rules d

            JOIN core.reconciliation_rules r
                ON d.rule_code = r.rule_code

            ON CONFLICT (reference_number, rule_code)
            DO NOTHING; 
            """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            # cursor.rowcount -> How many rows did this SQL statement affect?
            inserted_count = cursor.rowcount
        return inserted_count

if __name__ == "__main__":
    inserted_count = load_reconciliation_exceptions()
    print(f"Reconciliation exceptions loaded successfully. "
        f"New exceptions inserted: {inserted_count}")


# detected_reconciliation_rules -> its a view -> it answers What 
# problems exist according to the data right now?
# calculated from current data

# reconciliation_exceptions -> a table -> it answers What problems 
# has our operational reconciliation process recorded for investigation?