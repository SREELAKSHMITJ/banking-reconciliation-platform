from db_connection import get_connection

ALLOWED_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS"},
    "IN_PROGRESS": {"OPEN", "RESOLVED"},
    "RESOLVED": {"OPEN"}
}

def update_exception_status(exception_id, updated_status, change_note = None):

    # both queries are safe together, bcoz they are inside get_connection():
    # if everything succeeds - commit or else any error - entire transaction rollbacks
    # exception would stay at its previous state
    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Find the current status first
            cursor.execute(
                """
                SELECT status FROM core.reconciliation_exceptions
                WHERE exception_id = %s;
                """, (exception_id,)
            )
            result = cursor.fetchone()
             
            if result is None:
                raise ValueError(f"Exception {exception_id} does not exist.")

            old_status = result[0]

            # Find this status. If it doesn't exist, give me an empty set.
            if updated_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
                raise ValueError(
                    f"Invalid status transition: "
                    f"{old_status} -> {updated_status}"
                )

            # Update current exception status
            cursor.execute(
                """
                UPDATE core.reconciliation_exceptions
                SET 
                    status = %s,
                    resolved_at = CASE
                        WHEN %s = 'RESOLVED'
                            THEN CURRENT_TIMESTAMP
                        ELSE NULL
                    END
                WHERE exception_id = %s;
                """,
                (updated_status, updated_status, exception_id)
            )

            # Store audit history
            cursor.execute(
                """
                INSERT INTO core.exception_status_history
                (
                    exception_id,
                    old_status,
                    new_status,
                    change_note
                )
                VALUES (%s, %s, %s, %s);
                """,
                (exception_id, old_status, updated_status, change_note)
            )

    return old_status, updated_status

if __name__ == "__main__":
    # old_status, new_status = update_exception_status(exception_id = 2,
    #                          new_status = "IN_PROGRESS", 
    #                          change_note = "Investigation started through Python")

    # old_status, new_status = update_exception_status(exception_id = 2,
    #                              new_status = "RESOLVED", 
    #                              change_note = "Issue investigated and resolved")

    # prove invalid transitions are blocked
    # old_status, new_status = update_exception_status(
    #     exception_id=2,
    #     new_status="RESOLVED",
    #    change_note="Invalid transition test"
    #)

    # Reopen exception 2
    # old_status, new_status = update_exception_status( exception_id=2,
    #                         new_status="OPEN",
    #                         change_note="Exception reopened for further investigation")


    exception_id = int(input("Enter Exception ID: "))
    new_status = input(
        "Enter new status "
        "(OPEN / IN_PROGRESS / RESOLVED): ").strip().upper()
    change_note = input("Enter change note: ").strip()

    old_status, updated_status = update_exception_status(
        exception_id = exception_id,
        updated_status = new_status,
        change_note = change_note
    )


    print(
        f"Exception {exception_id} updated: "
        f"{old_status} -> {updated_status}"
    )



# NOTES

# Reconciliation asks: Do Transaction, Ledger and Settlement agree with each other?
# Data Quality asks: Is the data itself complete, valid, unique and structurally trustworthy?


# COMPLETENESS → required values missing?
# VALIDITY → unknown status/type/currency?
# UNIQUENESS → duplicate business identifiers?
# REFERENTIAL INTEGRITY → transaction points to a real account?
# CONSISTENCY → impossible values/timestamps?