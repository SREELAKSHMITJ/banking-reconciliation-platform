# imports the Faker library
from faker import Faker
import random
from db_connection import get_connection

# creates a Faker generator using Canadian-style data where applicable.
fake = Faker("en_CA")

def generate_customer():
    first_name = fake.first_name()
    last_name = fake.last_name()

    customer = {
        "first_name" : first_name,
        "last_name" : last_name,
        "email": fake.unique.email(),

        # In result - we will get - 'date_of_birth': datetime.date(1957, 5, 26)
        # It is not just text. Faker returned a real Python date object. 
        # That’s actually ideal because psycopg can send a Python date 
        # directly into a PostgreSQL DATE column.
        # Python datetime.date(1957, 5, 26) -> PostgreSQL DATE -> 1957-05-26
        "date_of_birth" : fake.date_of_birth(minimum_age = 18, maximum_age = 80)
    }

    return customer

def generate_customers(count):

    # empty list
    customers = []

    # '_' here means - Repeat this loop, but I don't actually need the loop number
    for _ in range(count):
        customer = generate_customer()
        customers.append(customer)

    return customers 


def insert_customers(customers):

    # VALUES (%s, %s, %s, %s) -> I will provide these four values separately.
    # which is later - (customer["first_name"], customer["last_name"],
    # customer["email"], customer["date_of_birth"])

    # For 'ON CONFLICT (email) DO NOTHING' : new customer → returns ID → keep it
    # duplicate email → no row inserted → don't keep it

    query = """
            INSERT INTO core.customers
            (first_name, last_name, email, date_of_birth)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING customer_id;
            """

    inserted_customers = []

    with get_connection() as connection:
        with connection.cursor() as cursor: 
            for customer in customers:
                # cursor.execute(query, values) -> is safer because 
                # Psycopg handles the values properly and protects against SQL injection.
                cursor.execute(query,
                    (customer["first_name"], customer["last_name"], 
                    customer["email"], customer["date_of_birth"])
                )
                result = cursor.fetchone()

                # If an email already exists, PostgreSQL inserts nothing, 
                # so there may be no ID returned.
                if result is not None:
                    customer["customer_id"] = result[0]
                    inserted_customers.append(customer)
    return inserted_customers

if __name__ == "__main__":

    # print(fake.name())
    # print(fake.email())

    # ISO 8601 date format - YYYY-MM-DD
    # print(fake.date_of_birth(minimum_age = 18, maximum_age = 80))

    # customer = generate_customer()
    # print(customer)

    # customers = generate_customers(5)
    #for customer in customers:
    #    print(customer)

    # customers = generate_customers(5)
    # insert_customers(customers)
    # print("Customers inserted successfully!")

    customers = generate_customers(5)
    inserted_customers = insert_customers(customers)
    for customer in inserted_customers:
        print(customer)
