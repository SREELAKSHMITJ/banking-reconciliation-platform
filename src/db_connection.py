# Flow is .env(contains credentials) -> Python loads them -> psycopg connects to 
# PostgreSQL -> connection creates a cursor -> cursor runs SQL -> 
# Python reads the result
# Secrets should not be hardcoded into source code.

# Python's built-in OS module to read environment variables
# psycopg - library to connect Python with PostgreSQL
# Python reads .env using load_dotenv 

import os
import psycopg
from dotenv import load_dotenv

# to access contents in .env

load_dotenv()

# creating a reusable function- database connection code

def get_connection():
    # Connect to PostgreSQL and return the resulting connection object.
    # Basically - Go to PostgreSQL on localhost, through port 5432, 
    # log in as postgres using this password, and open the banking_reconciliation database.

    return psycopg.connect(
        # Get the host from .env (localhost - PostgreSQL running on my own comp)
        host = os.getenv("DB_HOST"),
        # usually 5432 - 5432 is PostgreSQL’s default/common port, 
        # rather than something Python specifically requires.
        port = os.getenv("DB_PORT"),
        #Connect specifically to the database called banking_reconciliation
        dbname = os.getenv("DB_NAME"),
        #for now its postgres
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD")
    )


# The below code says - Run the code underneath that only when I directly run this Python file.
# only when directly run using - python src/db_connection.py
# reusable module , direct test

if __name__ == "__main__":
    # get_connection() gets a PostgreSQL connection
    # The with is useful because Python manages the connection for us.
    # open connection -> use it -> finish -> close properly
    # Without with, we'd often need to manually remember: connection.close()

    with get_connection() as connection:

            # The connection connects Python to PostgreSQL.
            # The cursor is what we use to send SQL commands through that connection.
            # cursor doesn't create the SQL; 
            # it gives Python a way to send SQL to PostgreSQL and retrieve results
            with connection.cursor() as cursor:

                 # This sends the SQL command.
                 cursor.execute(
                      "SELECT current_database(), current_user;"
                 )
                 # get the result - Give me one result row --> ("banking_reconciliation", "postgres")
                 # which is a python tuple
                 result = cursor.fetchone()

                 print("Connected Successfully!!!")
                 print("Database:", result[0])
                 print("User:", result[1])

                # Python successfully connected to the PostgreSQL database built

                # How did Python connect to PostgreSQL database:
                # .env -> load_dotenv() -> os.getenv() -> psycopg.connect() -> connection ->
                # cursor -> execute SQL -> fetch result



#.venv\Scripts\activate --> activate python project environment 
# packages are installed into Python environments, 
# and you need to make sure you're running the same environment where the package was installed.

