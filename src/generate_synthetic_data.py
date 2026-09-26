# imports the Faker library
from faker import Faker
import random
from db_connection import get_connection
# Because ledger posting should happen a little after the transaction time.
from datetime import timedelta

# -- CUSTOMER -- 

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


# -- ACCOUNT -- 


ACCOUNT_TYPES = ["CHEQUING", "SAVINGS"]

def generate_account(customer_id):
    return {
        "customer_id" : customer_id,
        "account_number" : f"ACC{customer_id:06d}{random.randint(1000, 9999)}",
        "account_type" : random.choice(ACCOUNT_TYPES),
        "currency" : "CAD",
        "current_balance" : round(random.uniform(250, 15000), 2)
    }


def generate_accounts(customers):

    # For every customer -> randomly choose 1 or 2 accounts -> 
    # generate each account using that customer's ID -> put them all into one list
    accounts = []
    for customer in customers:
        number_of_accounts = random.randint(1,2)
        for _ in range(number_of_accounts):
            account = generate_account(customer["customer_id"])
            accounts.append(account)
    return accounts

def insert_accounts(accounts):
    query = """
            INSERT INTO core.accounts(customer_id, account_number,
                account_type, currency, current_balance)
            VALUES(%s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO NOTHING
            RETURNING account_id;
            """

    inserted_accounts = []

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for account in accounts:
                cursor.execute(query, (
                    account["customer_id"], account["account_number"],
                        account["account_type"], account["currency"],
                        account["current_balance"]
                    )
                )

                result = cursor.fetchone()

                if result is not None:
                        account["account_id"] = result[0]
                        inserted_accounts.append(account)

    return inserted_accounts

# Python account dictionary -> INSERT -> PostgreSQL generates account_id ->
# fetchone() -> add account_id back into dictionary



# -- TRANSACTION -- 


TRANSACTION_TYPES = ["DEPOSIT", "WITHDRAWAL", "PURCHASE", "BILL_PAYMENT"]
CHANNELS = ["ATM", "POS", "ONLINE", "BRANCH"]

def generate_transaction(account):

    # fake.unique.bothify(text="SYN##########") -> The # characters 
    # are replaced with digits. 

    transaction_type = random.choice(TRANSACTION_TYPES)

    channel_options = {
        "DEPOSIT": ["ATM", "BRANCH"],
        "WITHDRAWAL": ["ATM", "BRANCH"],
        "PURCHASE": ["POS", "ONLINE"],
        "BILL_PAYMENT": ["ONLINE", "BRANCH"]
    }

    return {
        "account_id" : account["account_id"],
        "account_number" : account["account_number"],
        "reference_number" : fake.unique.bothify(text="SYN##########"),
        "transaction_type" : transaction_type,
        "amount" : round(random.uniform(10, 2000), 2),
        "channel" : random.choice(channel_options[transaction_type]),
        "status" : random.choices(["SUCCESS","FAILED"], weights = [95,5])[0],
        "transaction_time" : fake.date_time_between(
            start_date = "-30d",
            end_date = "now"
        )
    }

def generate_transactions(accounts):
    transactions = []
    for account in accounts:
        number_of_transactions = random.randint(5,10)
        for _ in range(number_of_transactions):
            transaction = generate_transaction(account)
            transactions.append(transaction)
    return transactions

def insert_transactions(transactions): 
    query = """
            INSERT INTO core.transactions
            ( account_id, reference_number, transaction_type, amount,
                channel, status, transaction_time )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(reference_number) DO NOTHING
            RETURNING transaction_id;
            """

    inserted_transactions = []
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for transaction in transactions:
                cursor.execute(query, (
                     transaction["account_id"], transaction["reference_number"],
                     transaction["transaction_type"], transaction["amount"],
                     transaction["channel"], transaction["status"],
                     transaction["transaction_time"]
                    )
                )
                result = cursor.fetchone()

                if result is not None:
                    transaction["transaction_id"] = result[0]
                    inserted_transactions.append(transaction)

    return inserted_transactions
            

# -- LEDGER -- 


def generate_ledger_entry(transaction):
    status_map = {
        "SUCCESS": "POSTED",
        "FAILED": "FAILED"
    }

    return{
        "transaction_reference" : transaction["reference_number"],
        "account_number" : transaction["account_number"],
        "entry_type": transaction["transaction_type"],
        "amount": transaction["amount"],
        "status": status_map[transaction["status"]],
        "posted_at": transaction["transaction_time"] + 
                timedelta(seconds = random.randint(30,240))
    }

def generate_ledger_entries(transactions):
    ledger_entries = []
    for transaction in transactions:
        ledger_entry = generate_ledger_entry(transaction)
        ledger_entries.append(ledger_entry)
    return ledger_entries

def insert_ledger_entries(ledger_entries):
    query = """
            INSERT INTO core.ledger_entries
            (transaction_reference, account_number, entry_type, amount, status, posted_at)
            VALUES(%s, %s, %s, %s, %s, %s)
            RETURNING ledger_entry_id;
            """

    inserted_ledger_entries = []

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for ledger_entry in ledger_entries:
                cursor.execute(query, (
                    ledger_entry["transaction_reference"], ledger_entry["account_number"],
                        ledger_entry["entry_type"], ledger_entry["amount"],
                        ledger_entry["status"], ledger_entry["posted_at"]
                    )
                )
                result = cursor.fetchone()

                if result is not None:
                    ledger_entry["ledger_entry_id"] = result[0]
                    inserted_ledger_entries.append(ledger_entry)

    return inserted_ledger_entries


# -- SETTLEMENT --

def generate_settlement_record(transaction):
    status_map = {
        "SUCCESS": "SETTLED",
        "FAILED": "FAILED"
    }
    return{
        "transaction_reference" : transaction["reference_number"],
        "account_number": transaction["account_number"],
        "settlement_amount": transaction["amount"],
        "settlement_status": status_map[transaction["status"]],
        "settlement_time" : transaction["transaction_time"] + 
                timedelta(minutes = random.randint(5,20))
    }

def generate_settlement_records(transactions):
    settlement_records = []
    for transaction in transactions:
        settlement_record = generate_settlement_record(transaction)
        settlement_records.append(settlement_record)
    return settlement_records

def insert_settlement_records(settlement_records):
    query = """
            INSERT INTO core.settlement_records(transaction_reference, account_number,
                settlement_amount, settlement_status, settlement_time)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING settlement_id;
            """
    inserted_settlement_records = []

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for settlement_record in settlement_records:
                cursor.execute(query, (
                    settlement_record["transaction_reference"],
                    settlement_record["account_number"],
                    settlement_record["settlement_amount"],
                    settlement_record["settlement_status"],
                    settlement_record["settlement_time"]
                    )
                )

                result = cursor.fetchone()

                if result is not  None:
                    settlement_record["settlement_id"] = result[0]
                    inserted_settlement_records.append(settlement_record)

    return inserted_settlement_records
    




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


    # Customers
    customers = generate_customers(5)
    inserted_customers = insert_customers(customers)
    # for customer in inserted_customers:
    #     print(customer)

    # Accounts
    accounts = generate_accounts(inserted_customers)
    inserted_accounts = insert_accounts(accounts)
    for account in inserted_accounts:
        print(account)

    # Transactions
    transactions = generate_transactions(inserted_accounts)
    inserted_transactions = insert_transactions(transactions)
    for transaction in inserted_transactions:
        print(transaction)

    # Generate downstream records
    ledger_entries = generate_ledger_entries(inserted_transactions)
    settlement_records = generate_settlement_records(inserted_transactions)


    # ----------------------------------------
    #           ANOMALY INJECTION 
    # ----------------------------------------

    #Failed transactions list
    failed_transactions = []

    for transaction in inserted_transactions:
        if transaction["status"] == "FAILED":
            failed_transactions.append(transaction)

    # 1. MISSING LEDGER
    successful_transactions = []

    for transaction in inserted_transactions:
        if transaction["status"] == "SUCCESS":
            successful_transactions.append(transaction)
    if successful_transactions:
        missing_ledger_transaction = successful_transactions[0]

        missing_ledger_reference = missing_ledger_transaction["reference_number"]

        ledger_entries = [ledger_entry 
                        for ledger_entry in ledger_entries
                        if ledger_entry["transaction_reference"] != missing_ledger_reference]

        print("Injected MISSING_LEDGER anomaly for: ",
            missing_ledger_reference)

    else:
        print("No successful transaction available. "
                "MISSING_LEDGER anomaly skipped.")


    # 2. MISSING SETTLEMENT
    if len(successful_transactions) >= 2:   
        
        missing_settlement_transaction = successful_transactions[1]
        missing_settlement_reference = missing_settlement_transaction["reference_number"]

        settlement_records = [
            settlement_record
            for settlement_record in settlement_records
            if settlement_record["transaction_reference"] != missing_settlement_reference
        ]

        print("Injected MISSING_SETTLEMENT anomaly for:",
            missing_settlement_reference)
    else:
        print(
            "Not enough successful transactions available. "
            "MISSING_SETTLEMENT anomaly skipped."
        )


    # 3. Ledger amount mismatch
    if len(successful_transactions) >= 3:

        amount_mismatch_transaction = successful_transactions[2]

        amount_mismatch_reference = (
            amount_mismatch_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == amount_mismatch_reference
            ):

                ledger_entry["amount"] = round(
                    ledger_entry["amount"] + 25.00,
                    2
                )

                print(
                    "Injected LEDGER_AMOUNT_MISMATCH anomaly for:",
                    amount_mismatch_reference
                )

                break

    else:
        print(
            "Not enough successful transactions available. "
            "LEDGER_AMOUNT_MISMATCH anomaly skipped."
        )

    # 4. Settlement amount mismatch
    if len(successful_transactions) >= 4:

        settlement_amount_transaction = successful_transactions[3]
        settlement_amount_reference = (
            settlement_amount_transaction["reference_number"]
        )

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == settlement_amount_reference
            ):
                settlement_record["settlement_amount"] = round(
                    settlement_record["settlement_amount"] + 30.00,
                    2
                )

                print(
                    "Injected SETTLEMENT_AMOUNT_MISMATCH anomaly for:",
                    settlement_amount_reference
                )

                break

    # 5. LEDGER STATUS MISMATCH

    if len(successful_transactions) >= 5:

        ledger_status_transaction = successful_transactions[4]
        ledger_status_reference = (
            ledger_status_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == ledger_status_reference
            ):
                ledger_entry["status"] = "PENDING"

                print(
                    "Injected LEDGER_STATUS_MISMATCH anomaly for:",
                    ledger_status_reference
                )

                break    

    # 6. SETTLEMENT STATUS MISMATCH

    if len(successful_transactions) >= 6:

        settlement_status_transaction = successful_transactions[5]
        settlement_status_reference = (
            settlement_status_transaction["reference_number"]
        )

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == settlement_status_reference
            ):
                settlement_record["settlement_status"] = "PENDING"

                print(
                    "Injected SETTLEMENT_STATUS_MISMATCH anomaly for:",
                    settlement_status_reference
                )

                break

    # 7. UNEXPECTED LEDGER POSTING

    if len(failed_transactions) >= 1:

        unexpected_ledger_transaction = failed_transactions[0]
        unexpected_ledger_reference = (
            unexpected_ledger_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == unexpected_ledger_reference
            ):
                ledger_entry["status"] = "POSTED"

                print(
                    "Injected UNEXPECTED_LEDGER_POSTING anomaly for:",
                    unexpected_ledger_reference
                )

                break

    # 8. UNEXPECTED SETTLEMENT

    if len(failed_transactions) >= 2:

        unexpected_settlement_transaction = failed_transactions[1]
        unexpected_settlement_reference = (
            unexpected_settlement_transaction["reference_number"]
        )

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == unexpected_settlement_reference
            ):
                settlement_record["settlement_status"] = "SETTLED"

                print(
                    "Injected UNEXPECTED_SETTLEMENT anomaly for:",
                    unexpected_settlement_reference
                )

                break

    #  9. ACCOUNT MISMATCHES

    if len(successful_transactions) >= 7:

        account_mismatch_transaction = successful_transactions[6]
        account_mismatch_reference = (
            account_mismatch_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == account_mismatch_reference
            ):
                ledger_entry["account_number"] = "ACC_WRONG_LEDGER"
                break

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == account_mismatch_reference
            ):
                settlement_record["account_number"] = "ACC_WRONG_SETTLE"
                break

        print(
            "Injected ACCOUNT_MISMATCH anomalies for:",
            account_mismatch_reference
        )

    # 10. TRANSACTION TYPE MISMATCH

    if len(successful_transactions) >= 8:

        type_mismatch_transaction = successful_transactions[7]
        type_mismatch_reference = (
            type_mismatch_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == type_mismatch_reference
            ):

                if ledger_entry["entry_type"] != "PURCHASE":
                    ledger_entry["entry_type"] = "PURCHASE"
                else:
                    ledger_entry["entry_type"] = "DEPOSIT"

                print(
                    "Injected TRANSACTION_TYPE_MISMATCH anomaly for:",
                    type_mismatch_reference
                )

                break

    # 11. DUPLICATE TRANSACTION

    if len(failed_transactions) >= 3:

        original_transaction = failed_transactions[2]

        duplicate_transaction = original_transaction.copy()

        duplicate_transaction["reference_number"] = (
            fake.unique.bothify(text="DUP##########")
        )

        duplicate_transaction["transaction_time"] = (
            original_transaction["transaction_time"]
            + timedelta(seconds=10)
        )
        # Remove transaction_id if it exists. 
        # If it doesn't exist, don't crash — just return None.
        duplicate_transaction.pop("transaction_id", None)

        inserted_duplicate_transactions = insert_transactions(
            [duplicate_transaction]
        )

        if inserted_duplicate_transactions:
            print(
                "Injected DUPLICATE_TRANSACTION anomaly for:",
                duplicate_transaction["reference_number"]
            )

    # 12. DUPLICATE LEDGER ENTRY

    if len(successful_transactions) >= 9:

        duplicate_ledger_reference = (
            successful_transactions[8]["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == duplicate_ledger_reference
            ):
                duplicate_ledger_entry = ledger_entry.copy()

                ledger_entries.append(
                    duplicate_ledger_entry
                )

                print(
                    "Injected DUPLICATE_LEDGER_ENTRY anomaly for:",
                    duplicate_ledger_reference
                )

                break

    # 13. DUPLICATE SETTLEMENT

    if len(successful_transactions) >= 10:

        duplicate_settlement_reference = (
            successful_transactions[9]["reference_number"]
        )

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == duplicate_settlement_reference
            ):
                duplicate_settlement_record = (
                    settlement_record.copy()
                )

                settlement_records.append(
                    duplicate_settlement_record
                )

                print(
                    "Injected DUPLICATE_SETTLEMENT anomaly for:",
                    duplicate_settlement_reference
                )

                break

    # 14. LATE LEDGER POSTING

    if len(successful_transactions) >= 11:

        late_ledger_transaction = successful_transactions[10]
        late_ledger_reference = (
            late_ledger_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == late_ledger_reference
            ):
                ledger_entry["posted_at"] = (
                    late_ledger_transaction["transaction_time"]
                    + timedelta(minutes=10)
                )

                break

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == late_ledger_reference
            ):
                settlement_record["settlement_time"] = (
                    late_ledger_transaction["transaction_time"]
                    + timedelta(minutes=15)
                )

                break

        print(
            "Injected LATE_LEDGER_POSTING anomaly for:",
            late_ledger_reference
        )

    # 15. LATE SETTLEMENT

    if len(successful_transactions) >= 12:

        late_settlement_transaction = successful_transactions[11]
        late_settlement_reference = (
            late_settlement_transaction["reference_number"]
        )

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == late_settlement_reference
            ):
                settlement_record["settlement_time"] = (
                    late_settlement_transaction["transaction_time"]
                    + timedelta(minutes=45)
                )

                print(
                    "Injected LATE_SETTLEMENT anomaly for:",
                    late_settlement_reference
                )

                break

    # 16. LEDGER BEFORE TRANSACTION

    if len(successful_transactions) >= 13:

        ledger_before_transaction = successful_transactions[12]
        ledger_before_reference = (
            ledger_before_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == ledger_before_reference
            ):
                ledger_entry["posted_at"] = (
                    ledger_before_transaction["transaction_time"]
                    - timedelta(minutes=1)
                )

                print(
                    "Injected LEDGER_BEFORE_TRANSACTION anomaly for:",
                    ledger_before_reference
                )

                break

    # 17. SETTLEMENT BEFORE TRANSACTION

    if len(successful_transactions) >= 14:

        settlement_before_transaction = (
            successful_transactions[13]
        )

        settlement_before_reference = (
            settlement_before_transaction["reference_number"]
        )

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == settlement_before_reference
            ):
                settlement_record["settlement_time"] = (
                    settlement_before_transaction["transaction_time"]
                    - timedelta(minutes=1)
                )

                print(
                    "Injected SETTLEMENT_BEFORE_TRANSACTION anomaly for:",
                    settlement_before_reference
                )

                break

    # 18. SETTLEMENT BEFORE LEDGER

    if len(successful_transactions) >= 15:

        settlement_before_ledger_transaction = (
            successful_transactions[14]
        )

        settlement_before_ledger_reference = (
            settlement_before_ledger_transaction["reference_number"]
        )

        for ledger_entry in ledger_entries:

            if (
                ledger_entry["transaction_reference"]
                == settlement_before_ledger_reference
            ):
                ledger_entry["posted_at"] = (
                    settlement_before_ledger_transaction[
                        "transaction_time"
                    ]
                    + timedelta(minutes=2)
                )

                break

        for settlement_record in settlement_records:

            if (
                settlement_record["transaction_reference"]
                == settlement_before_ledger_reference
            ):
                settlement_record["settlement_time"] = (
                    settlement_before_ledger_transaction[
                        "transaction_time"
                    ]
                    + timedelta(minutes=1)
                )

                break

        print(
            "Injected SETTLEMENT_BEFORE_LEDGER anomaly for:",
            settlement_before_ledger_reference
        )

    # 19. MISSING TRANSACTION / ORPHAN DOWNSTREAM RECORDS

    # Only continue if both lists contain data. Empty lists are False.
    if inserted_accounts and inserted_transactions:

        orphan_reference = (
            fake.unique.bothify(text="ORPH##########")
        )

        orphan_time = (
            inserted_transactions[0]["transaction_time"]
        )

        # ledger_entries.transaction_reference & settlement_records.transaction_reference
        # do not have foreign keys directly 
        # forcing them to exist in transactions.reference_number.

        orphan_ledger = {
            "transaction_reference": orphan_reference,
            "account_number":
                inserted_accounts[0]["account_number"],
            "entry_type": "PURCHASE",
            "amount": 333.33,
            "status": "POSTED",
            "posted_at":
                orphan_time + timedelta(minutes=1)
        }

        orphan_settlement = {
            "transaction_reference": orphan_reference,
            "account_number":
                inserted_accounts[0]["account_number"],
            "settlement_amount": 333.33,
            "settlement_status": "SETTLED",
            "settlement_time":
                orphan_time + timedelta(minutes=3)
        }

        ledger_entries.append(orphan_ledger)
        settlement_records.append(orphan_settlement)

        print(
            "Injected MISSING_TRANSACTION anomaly for:",
            orphan_reference
        )

        # FULL OUTER JOIN in: core.reconciliation_base is what lets that orphan 
        # reference still appear even though the transaction side is missing.


    # Insert downstream records
    inserted_ledger_entries = insert_ledger_entries(ledger_entries)
    inserted_settlement_records = insert_settlement_records(settlement_records)


    # for ledger_entry in inserted_ledger_entries:
       # print(ledger_entry)

    # for settlement_record in inserted_settlement_records:
        # print(settlement_record)














# -- NOTES --

# random.choice() -> Choose one item from a sequence. We use this 
# when everything has roughly the same chance -> returns string

# random.choices() -> This can choose using weights/probabilities. 
# returns a list 

# The symbols [], {}, () -> 
# [] -> List/accessing something -> ["ATM", "POS"]
    # A list is basically a collection of things.
    # has index, value
    # mutable

# {} -> Dictionary or set -> {"name": "Sree"}
    # stores key : value pair
    # account["account_id"] -> Go into the account 
    # dictionary and give me the value whose key is "account_id".

        # Set {} -> A set keeps unique values. -> statuses = {"SUCCESS", "FAILED"}
        # numbers = {1, 2, 2, 3, 3, 3} -> would become
        # {1, 2, 3} -> duplicates disappear

        # {} - is an empty dictionary, not an empty set.
        # set() - is an empty set

# () -> Tuple or function call -> (12, "SAVINGS") / print()
    # It is similar to a list, but typically used for a fixed collection of values.
    # immutable

# String - one piece of text
# List - collection of items
# Dictionary - one object's properties
# Tuple - Fixed group of values

# break - Search through the ledger list until
# you find the record I want. Once you find and change it, stop searching.

# Faker has a function called bothify() -> replace special placeholders
# # → random digit      |    ? → random letter

# SYN...  → normal synthetic transaction
# DUP...  → intentionally created duplicate-style transaction
# ORPH... → orphan/downstream-only record

# For dictionaries: dictionary.pop("key") -> Remove this key/value pair from the dictionary.
