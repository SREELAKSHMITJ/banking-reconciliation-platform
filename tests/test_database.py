from db_connection import get_connection

def test_database_connection():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            # SELECT 1; --> Return the number 1  --> like (1,)
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
    # I expect the database to return 1. If it does, pass the test. If it doesn't, fail.
    assert result[0] == 1

# Here:
# Can Python connect to PostgreSQL?
# Can PostgreSQL execute a query?
# Did it return what we expected?


# ======================================
#               NOTES:
# ======================================

# assert condition means this condition must be true.