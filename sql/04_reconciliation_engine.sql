-- =========================================================
-- BANKING RECONCILIATION DETECTION ENGINE
-- Detects REC001 - REC024
-- =========================================================

CREATE OR REPLACE VIEW core.detected_reconciliation_rules AS


-- REC001: MISSING_TRANSACTION
SELECT
    rb.reference_number,
    'REC001' AS rule_code,
    NULL::NUMERIC(15,2) AS variance
FROM core.reconciliation_base rb
WHERE rb.transaction_id IS NULL


UNION ALL


-- REC002: MISSING_LEDGER
SELECT
    rb.reference_number,
    'REC002',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_status = 'SUCCESS'
  AND rb.ledger_entry_id IS NULL


UNION ALL


-- REC003: MISSING_SETTLEMENT
SELECT
    rb.reference_number,
    'REC003',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_status = 'SUCCESS'
  AND rb.settlement_id IS NULL


UNION ALL


-- REC004: LEDGER_AMOUNT_MISMATCH
SELECT
    rb.reference_number,
    'REC004',
    ABS(
        rb.transaction_amount - rb.ledger_amount
    )::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_amount IS NOT NULL
  AND rb.ledger_amount IS NOT NULL
  AND rb.transaction_amount <> rb.ledger_amount


UNION ALL


-- REC005: SETTLEMENT_AMOUNT_MISMATCH
SELECT
    rb.reference_number,
    'REC005',
    ABS(
        rb.transaction_amount - rb.settlement_amount
    )::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_amount IS NOT NULL
  AND rb.settlement_amount IS NOT NULL
  AND rb.transaction_amount <> rb.settlement_amount


UNION ALL


-- REC006: LEDGER_SETTLEMENT_AMOUNT_MISMATCH
SELECT
    rb.reference_number,
    'REC006',
    ABS(
        rb.ledger_amount - rb.settlement_amount
    )::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.ledger_amount IS NOT NULL
  AND rb.settlement_amount IS NOT NULL
  AND rb.ledger_amount <> rb.settlement_amount


UNION ALL


-- REC007: LEDGER_STATUS_MISMATCH
SELECT
    rb.reference_number,
    'REC007',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_status = 'SUCCESS'
  AND rb.ledger_entry_id IS NOT NULL
  AND rb.ledger_status <> 'POSTED'


UNION ALL


-- REC008: SETTLEMENT_STATUS_MISMATCH
SELECT
    rb.reference_number,
    'REC008',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_status = 'SUCCESS'
  AND rb.settlement_id IS NOT NULL
  AND rb.settlement_status <> 'SETTLED'


UNION ALL


-- REC009: UNEXPECTED_LEDGER_POSTING
SELECT
    rb.reference_number,
    'REC009',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_status = 'FAILED'
  AND rb.ledger_status = 'POSTED'


UNION ALL


-- REC010: UNEXPECTED_SETTLEMENT
SELECT
    rb.reference_number,
    'REC010',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_status = 'FAILED'
  AND rb.settlement_status = 'SETTLED'


UNION ALL


-- REC011: SETTLEMENT_WITHOUT_LEDGER
SELECT
    rb.reference_number,
    'REC011',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.settlement_id IS NOT NULL
  AND rb.ledger_entry_id IS NULL


UNION ALL


-- REC012: SETTLEMENT_AFTER_FAILED_LEDGER
SELECT
    rb.reference_number,
    'REC012',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.ledger_status = 'FAILED'
  AND rb.settlement_status = 'SETTLED'


UNION ALL


-- REC013: TRANSACTION_LEDGER_ACCOUNT_MISMATCH
SELECT
    rb.reference_number,
    'REC013',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_account_number IS NOT NULL
  AND rb.ledger_account_number IS NOT NULL
  AND rb.transaction_account_number
      <> rb.ledger_account_number


UNION ALL


-- REC014: TRANSACTION_SETTLEMENT_ACCOUNT_MISMATCH
SELECT
    rb.reference_number,
    'REC014',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_account_number IS NOT NULL
  AND rb.settlement_account_number IS NOT NULL
  AND rb.transaction_account_number
      <> rb.settlement_account_number


UNION ALL


-- REC015: LEDGER_SETTLEMENT_ACCOUNT_MISMATCH
SELECT
    rb.reference_number,
    'REC015',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.ledger_account_number IS NOT NULL
  AND rb.settlement_account_number IS NOT NULL
  AND rb.ledger_account_number
      <> rb.settlement_account_number


UNION ALL


-- REC016: TRANSACTION_TYPE_MISMATCH
SELECT
    rb.reference_number,
    'REC016',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_type IS NOT NULL
  AND rb.entry_type IS NOT NULL
  AND rb.transaction_type <> rb.entry_type


UNION ALL


-- REC017: DUPLICATE_TRANSACTION
-- Different references that look like the same business transaction
SELECT DISTINCT
    t2.reference_number,
    'REC017',
    NULL::NUMERIC(15,2)
FROM core.transactions t1

JOIN core.transactions t2
    ON t1.transaction_id < t2.transaction_id
   AND t1.account_id = t2.account_id
   AND t1.transaction_type = t2.transaction_type
   AND t1.amount = t2.amount
   AND COALESCE(t1.channel, '')
       = COALESCE(t2.channel, '')
   AND t1.status = t2.status
   AND ABS(
       EXTRACT(
           EPOCH FROM
           (t2.transaction_time - t1.transaction_time)
       )
   ) <= 60


UNION ALL


-- REC018: DUPLICATE_LEDGER_ENTRY
SELECT
    l.transaction_reference,
    'REC018',
    NULL::NUMERIC(15,2)
FROM core.ledger_entries l
GROUP BY l.transaction_reference
HAVING COUNT(*) > 1


UNION ALL


-- REC019: DUPLICATE_SETTLEMENT
SELECT
    s.transaction_reference,
    'REC019',
    NULL::NUMERIC(15,2)
FROM core.settlement_records s
GROUP BY s.transaction_reference
HAVING COUNT(*) > 1


UNION ALL


-- REC020: LATE_LEDGER_POSTING
-- Project SLA: ledger should post within 5 minutes
SELECT
    rb.reference_number,
    'REC020',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_time IS NOT NULL
  AND rb.posted_at IS NOT NULL
  AND rb.posted_at >
      rb.transaction_time + INTERVAL '5 minutes'


UNION ALL


-- REC021: LATE_SETTLEMENT
-- Project SLA: settlement should occur within 30 minutes
SELECT
    rb.reference_number,
    'REC021',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_time IS NOT NULL
  AND rb.settlement_time IS NOT NULL
  AND rb.settlement_time >
      rb.transaction_time + INTERVAL '30 minutes'


UNION ALL


-- REC022: LEDGER_BEFORE_TRANSACTION
SELECT
    rb.reference_number,
    'REC022',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_time IS NOT NULL
  AND rb.posted_at IS NOT NULL
  AND rb.posted_at < rb.transaction_time


UNION ALL


-- REC023: SETTLEMENT_BEFORE_TRANSACTION
SELECT
    rb.reference_number,
    'REC023',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.transaction_time IS NOT NULL
  AND rb.settlement_time IS NOT NULL
  AND rb.settlement_time < rb.transaction_time


UNION ALL


-- REC024: SETTLEMENT_BEFORE_LEDGER
SELECT
    rb.reference_number,
    'REC024',
    NULL::NUMERIC(15,2)
FROM core.reconciliation_base rb
WHERE rb.posted_at IS NOT NULL
  AND rb.settlement_time IS NOT NULL
  AND rb.settlement_time < rb.posted_at;