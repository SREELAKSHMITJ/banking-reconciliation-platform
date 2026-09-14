CREATE OR REPLACE VIEW core.reconciliation_base AS

SELECT
    COALESCE(
        t.reference_number,
        l.transaction_reference,
        s.transaction_reference
    ) AS reference_number,

    t.transaction_id,
    t.account_id,

    a.account_number AS transaction_account_number,

    t.transaction_type,
    t.amount AS transaction_amount,
    t.status AS transaction_status,
    t.transaction_time,

    l.ledger_entry_id,
    l.account_number AS ledger_account_number,
    l.entry_type,
    l.amount AS ledger_amount,
    l.status AS ledger_status,
    l.posted_at,

    s.settlement_id,
    s.account_number AS settlement_account_number,
    s.settlement_amount,
    s.settlement_status,
    s.settlement_time

FROM core.transactions t

LEFT JOIN core.accounts a
    ON t.account_id = a.account_id

FULL OUTER JOIN core.ledger_entries l
    ON t.reference_number = l.transaction_reference

FULL OUTER JOIN core.settlement_records s
    ON s.transaction_reference =
       COALESCE(t.reference_number, l.transaction_reference);