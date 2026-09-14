import pandas as pd
from db_connection import get_connection

# reusable logic
def load_exceptions():
    query = """
                SELECT e.reference_number, e.rule_code, r.rule_name, 
	                e.variance, e.severity, e.status, e.detected_at
                FROM core.reconciliation_exceptions e
                JOIN core.reconciliation_rules r
                    ON e.rule_code = r.rule_code
                ORDER BY e.detected_at DESC;
    
            """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            # get all SQL result rows
            rows = cursor.fetchall()

            # This is a list comprehension
            columns = [
                # cursor.description - tells Python the names of the columns returned by SQL

                # for column in cursor.description - Go through each returned SQL column
                # column.name - Give me just that column's name.
                # result is columns = [column1, column2, etc...]
                column.name for column in cursor.description
            ]

    # convert the database result into a Pandas table
    df = pd.DataFrame(rows, columns = columns)

    # give that DataFrame back to whoever calls load_exceptions().
    return df


# if __name__ == "__main__": is only being used to say:
# If I run this file directly, call load_exceptions() and show me the result

# direct test/demo
if __name__ == "__main__":
    exceptions_df = load_exceptions()

    # returns first 5 rows by default
    print(exceptions_df.head())
    print("\nTotal Exceptions:", len(exceptions_df))