-- This is the catalogue of DQ rules
-- A master list of all Data Quality rules our platform knows about.

-- COMPLETENESS → is something missing?
-- VALIDITY → is the value allowed?
-- UNIQUENESS → is something duplicated?
-- INTEGRITY → do relationships between tables make sense?
-- CONSISTENCY → do related values agree logically?

CREATE TABLE core.data_quality_checks(
    check_code VARCHAR(10) PRIMARY KEY,
    check_name VARCHAR(100) NOT NULL,
    quality_dimension VARCHAR(30) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    default_severity VARCHAR(20) NOT NULL,
    description TEXT
);

INSERT INTO core.data_quality_checks
(
    check_code,
    check_name,
    quality_dimension,
    target_table,
    default_severity,
    description
)
VALUES

-- -------------------------
-- COMPLETENESS
-- -------------------------

(
    'DQ001',
    'Customer Required Fields',
    'COMPLETENESS',
    'core.customers',
    'HIGH',
    'Checks whether required customer fields are populated.'
),

(
    'DQ002',
    'Account Required Fields',
    'COMPLETENESS',
    'core.accounts',
    'HIGH',
    'Checks whether required account fields are populated.'
),

(
    'DQ003',
    'Transaction Required Fields',
    'COMPLETENESS',
    'core.transactions',
    'CRITICAL',
    'Checks whether required transaction fields are populated.'
),

(
    'DQ004',
    'Ledger Required Fields',
    'COMPLETENESS',
    'core.ledger_entries',
    'CRITICAL',
    'Checks whether required ledger fields are populated.'
),

(
    'DQ005',
    'Settlement Required Fields',
    'COMPLETENESS',
    'core.settlement_records',
    'CRITICAL',
    'Checks whether required settlement fields are populated.'
),


-- -------------------------
-- VALIDITY
-- -------------------------

(
    'DQ006',
    'Valid Account Type',
    'VALIDITY',
    'core.accounts',
    'MEDIUM',
    'Checks whether account type is CHEQUING or SAVINGS.'
),

(
    'DQ007',
    'Valid Currency',
    'VALIDITY',
    'core.accounts',
    'HIGH',
    'Checks whether account currency is CAD for this project.'
),

(
    'DQ008',
    'Valid Transaction Type',
    'VALIDITY',
    'core.transactions',
    'HIGH',
    'Checks whether transaction type belongs to the supported transaction types.'
),

(
    'DQ009',
    'Valid Transaction Status',
    'VALIDITY',
    'core.transactions',
    'HIGH',
    'Checks whether transaction status is SUCCESS or FAILED.'
),

(
    'DQ010',
    'Valid Ledger Status',
    'VALIDITY',
    'core.ledger_entries',
    'HIGH',
    'Checks whether ledger status belongs to the supported ledger statuses.'
),

(
    'DQ011',
    'Valid Settlement Status',
    'VALIDITY',
    'core.settlement_records',
    'HIGH',
    'Checks whether settlement status belongs to the supported settlement statuses.'
),


-- -------------------------
-- UNIQUENESS
-- -------------------------

(
    'DQ012',
    'Duplicate Ledger Reference',
    'UNIQUENESS',
    'core.ledger_entries',
    'HIGH',
    'Checks whether more than one ledger entry exists for the same transaction reference.'
),

(
    'DQ013',
    'Duplicate Settlement Reference',
    'UNIQUENESS',
    'core.settlement_records',
    'HIGH',
    'Checks whether more than one settlement record exists for the same transaction reference.'
),


-- -------------------------
-- REFERENTIAL INTEGRITY
-- -------------------------

(
    'DQ014',
    'Account Without Customer',
    'INTEGRITY',
    'core.accounts',
    'CRITICAL',
    'Checks whether every account belongs to an existing customer.'
),

(
    'DQ015',
    'Transaction Without Account',
    'INTEGRITY',
    'core.transactions',
    'CRITICAL',
    'Checks whether every transaction belongs to an existing account.'
),

(
    'DQ016',
    'Ledger Account Not Found',
    'INTEGRITY',
    'core.ledger_entries',
    'CRITICAL',
    'Checks whether ledger account numbers exist in the accounts table.'
),

(
    'DQ017',
    'Settlement Account Not Found',
    'INTEGRITY',
    'core.settlement_records',
    'CRITICAL',
    'Checks whether settlement account numbers exist in the accounts table.'
),


-- -------------------------
-- TIMELINESS
-- -------------------------

(
    'DQ018',
    'Future Transaction Timestamp',
    'TIMELINESS',
    'core.transactions',
    'HIGH',
    'Checks whether transaction timestamps occur in the future.'
),

(
    'DQ019',
    'Future Ledger Timestamp',
    'TIMELINESS',
    'core.ledger_entries',
    'HIGH',
    'Checks whether ledger posting timestamps occur in the future.'
),

(
    'DQ020',
    'Future Settlement Timestamp',
    'TIMELINESS',
    'core.settlement_records',
    'HIGH',
    'Checks whether settlement timestamps occur in the future.'
)

ON CONFLICT (check_code)
DO NOTHING;



-- create a DQ run table
-- data_quality_runs acts like a batch header.

CREATE TABLE core.data_quality_runs (
    run_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    run_status VARCHAR(20) NOT NULL DEFAULT 'RUNNING'
);

-- Create core.data_quality_results

CREATE TABLE core.data_quality_results(
    result_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id INTEGER NOT NULL,
    check_code VARCHAR(10) NOT NULL,
    result_status VARCHAR(10) NOT NULL,
    checked_row_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    details TEXT,
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_dq_result_run
        FOREIGN KEY (run_id)
        REFERENCES core.data_quality_runs(run_id),

    CONSTRAINT fk_dq_result_check
        FOREIGN KEY (check_code)
        REFERENCES core.data_quality_checks(check_code),

    CONSTRAINT chk_dq_result_status
        CHECK (result_status IN ('PASS', 'FAIL', 'ERROR')),

    CONSTRAINT chk_dq_failure_count
        CHECK (failure_count >= 0),

    CONSTRAINT chk_dq_checked_row_count
        CHECK (checked_row_count >= 0),

    CONSTRAINT uq_dq_run_check
        UNIQUE (run_id, check_code)
);         




-- Building the DQ detector
-- DQ checks data trustworthiness -> Is each table healthy?
-- Reconciliation checks whether systems agree -> Do transaction, ledger, and settlement agree?

CREATE OR REPLACE VIEW core.detected_data_quality_issues AS

-- =====================================================
-- COMPLETENESS
-- =====================================================


-- DQ001 - CUSTOMER REQUIRED FIELDS

-- customer_id::TEXT  --> convert this integer to text.

SELECT 'DQ001' AS check_code,
    customer_id::TEXT AS record_key,
    'Customer has missing required data' AS issue_detail
FROM core.customers

-- NULL means no value
-- But '' means there is technically a string, but it contains nothing.
-- '     ' contains spaces - hence using TRIM()
-- Therefore: first_name IS NULL
-- OR TRIM(first_name) = '' --> means Catch missing or blank first names.

WHERE first_name IS NULL
    OR TRIM(first_name) = ''
    OR last_name IS NULL
   OR TRIM(last_name) = ''
   OR email IS NULL
   OR TRIM(email) = ''
   OR date_of_birth IS NULL

UNION ALL

-- DQ002 - ACCOUNT REQUIRED FIELDS

SELECT
    'DQ002',
    account_id::TEXT,
    'Account has missing required data'

FROM core.accounts

WHERE customer_id IS NULL
   OR account_number IS NULL
   OR TRIM(account_number) = ''
   OR account_type IS NULL
   OR TRIM(account_type) = ''
   OR currency IS NULL
   OR TRIM(currency) = ''
   OR current_balance IS NULL


UNION ALL

-- DQ003 - TRANSACTION REQUIRED FIELDS

SELECT
    'DQ003',
    transaction_id::TEXT,
    'Transaction has missing required data'

FROM core.transactions

WHERE account_id IS NULL
   OR reference_number IS NULL
   OR TRIM(reference_number) = ''
   OR transaction_type IS NULL
   OR TRIM(transaction_type) = ''
   OR amount IS NULL
   OR channel IS NULL
   OR TRIM(channel) = ''
   OR status IS NULL
   OR TRIM(status) = ''
   OR transaction_time IS NULL


UNION ALL


-- DQ004 - LEDGER REQUIRED FIELDS

SELECT
    'DQ004',
    ledger_entry_id::TEXT,
    'Ledger entry has missing required data'

FROM core.ledger_entries

WHERE transaction_reference IS NULL
   OR TRIM(transaction_reference) = ''
   OR account_number IS NULL
   OR TRIM(account_number) = ''
   OR entry_type IS NULL
   OR TRIM(entry_type) = ''
   OR amount IS NULL
   OR status IS NULL
   OR TRIM(status) = ''
   OR posted_at IS NULL


UNION ALL


-- DQ005 - SETTLEMENT REQUIRED FIELDS

SELECT
    'DQ005',
    settlement_id::TEXT,
    'Settlement record has missing required data'

FROM core.settlement_records

WHERE transaction_reference IS NULL
   OR TRIM(transaction_reference) = ''
   OR account_number IS NULL
   OR TRIM(account_number) = ''
   OR settlement_amount IS NULL
   OR settlement_status IS NULL
   OR TRIM(settlement_status) = ''
   OR settlement_time IS NULL


UNION ALL

-- =====================================================
-- VALIDITY
-- =====================================================

-- DQ006 - VALID ACCOUNT TYPE
SELECT
    'DQ006',
    account_id::TEXT,
    -- || means concatenating text
    'Invalid account type: ' || account_type
FROM core.accounts
WHERE account_type NOT IN ('CHEQUING', 'SAVINGS')


UNION ALL


-- DQ007 - VALID CURRENCY
SELECT
    'DQ007',
    account_id::TEXT,
    'Invalid currency: ' || currency
FROM core.accounts
WHERE currency <> 'CAD'


UNION ALL


-- DQ008 - VALID TRANSACTION TYPE
SELECT
    'DQ008',
    transaction_id::TEXT,
    'Invalid transaction type: ' || transaction_type
FROM core.transactions
WHERE transaction_type NOT IN (
    'DEPOSIT',
    'WITHDRAWAL',
    'PURCHASE',
    'BILL_PAYMENT'
)


UNION ALL


-- DQ009 - VALID TRANSACTION STATUS
SELECT
    'DQ009',
    transaction_id::TEXT,
    'Invalid transaction status: ' || status
FROM core.transactions
WHERE status NOT IN (
    'SUCCESS',
    'FAILED'
)


UNION ALL


-- DQ010 - VALID LEDGER STATUS
SELECT
    'DQ010',
    ledger_entry_id::TEXT,
    'Invalid ledger status: ' || status
FROM core.ledger_entries
WHERE status NOT IN (
    'POSTED',
    'FAILED',
    'PENDING'
)


UNION ALL


-- DQ011 - VALID SETTLEMENT STATUS
SELECT
    'DQ011',
    settlement_id::TEXT,
    'Invalid settlement status: ' || settlement_status
FROM core.settlement_records
WHERE settlement_status NOT IN (
    'SETTLED',
    'FAILED',
    'PENDING'
)


UNION ALL


-- =====================================================
-- UNIQUENESS
-- =====================================================

-- DQ012 → duplicate ledger reference -> Is the data itself duplicated?
-- Reconciliation rule REC018 → duplicate ledger entry -> 
-- Does this duplicate create a reconciliation exception?

-- DQ012 - DUPLICATE LEDGER REFERENCE
SELECT
    'DQ012',
    transaction_reference,
    'Duplicate ledger reference. Count: '
        || COUNT(*)::TEXT
FROM core.ledger_entries
-- Put rows with the same reference together, 
-- then only return groups containing more than one row.
-- HAVING is basically a filter applied after grouping.
GROUP BY transaction_reference
HAVING COUNT(*) > 1


UNION ALL


-- DQ013 - DUPLICATE SETTLEMENT REFERENCE
SELECT
    'DQ013',
    transaction_reference,
    'Duplicate settlement reference. Count: '
        || COUNT(*)::TEXT
FROM core.settlement_records
GROUP BY transaction_reference
HAVING COUNT(*) > 1


UNION ALL


-- =====================================================
-- REFERENTIAL INTEGRITY
-- =====================================================

-- DQ014 & DQ015 has foreign keys so PostgreSQL prevents those failures
-- but still monitoring them as DQ controls

-- DQ016 & DQ017 - does not have foreign key forcing that account to exist.

-- DQ014 - ACCOUNT WITHOUT CUSTOMER
SELECT
    'DQ014',
    a.account_id::TEXT,
    'Account references a customer that does not exist'
FROM core.accounts a
LEFT JOIN core.customers c
    ON a.customer_id = c.customer_id
WHERE c.customer_id IS NULL


UNION ALL


-- DQ015 - TRANSACTION WITHOUT ACCOUNT
SELECT
    'DQ015',
    t.transaction_id::TEXT,
    'Transaction references an account that does not exist'
FROM core.transactions t
LEFT JOIN core.accounts a
    ON t.account_id = a.account_id
WHERE a.account_id IS NULL


UNION ALL


-- DQ016 - LEDGER ACCOUNT NOT FOUND
SELECT
    'DQ016',
    l.ledger_entry_id::TEXT,
    'Ledger account does not exist in core.accounts: '
        || l.account_number
FROM core.ledger_entries l
LEFT JOIN core.accounts a
    ON l.account_number = a.account_number
WHERE a.account_id IS NULL


UNION ALL


-- DQ017 - SETTLEMENT ACCOUNT NOT FOUND
SELECT
    'DQ017',
    s.settlement_id::TEXT,
    'Settlement account does not exist in core.accounts: '
        || s.account_number
FROM core.settlement_records s
LEFT JOIN core.accounts a
    ON s.account_number = a.account_number
WHERE a.account_id IS NULL


UNION ALL


-- =====================================================
-- TIMELINESS
-- =====================================================

-- DQ018 - FUTURE TRANSACTION TIMESTAMP
SELECT
    'DQ018',
    transaction_id::TEXT,
    'Transaction timestamp is in the future'
FROM core.transactions
WHERE transaction_time > CURRENT_TIMESTAMP


UNION ALL


-- DQ019 - FUTURE LEDGER TIMESTAMP
SELECT
    'DQ019',
    ledger_entry_id::TEXT,
    'Ledger posting timestamp is in the future'
FROM core.ledger_entries
WHERE posted_at > CURRENT_TIMESTAMP


UNION ALL


-- DQ020 - FUTURE SETTLEMENT TIMESTAMP
SELECT
    'DQ020',
    settlement_id::TEXT,
    'Settlement timestamp is in the future'
FROM core.settlement_records
WHERE settlement_time > CURRENT_TIMESTAMP;



-- Create the DQ summary view

CREATE OR REPLACE VIEW core.data_quality_summary AS

SELECT
    c.check_code,
    c.check_name,
    c.quality_dimension,
    c.target_table,
    c.default_severity,

    CASE c.target_table
        WHEN 'core.customers'
            THEN (SELECT COUNT(*) FROM core.customers)

        WHEN 'core.accounts'
            THEN (SELECT COUNT(*) FROM core.accounts)

        WHEN 'core.transactions'
            THEN (SELECT COUNT(*) FROM core.transactions)

        WHEN 'core.ledger_entries'
            THEN (SELECT COUNT(*) FROM core.ledger_entries)

        WHEN 'core.settlement_records'
            THEN (SELECT COUNT(*) FROM core.settlement_records)

        ELSE 0
    END AS checked_row_count,

    COUNT(d.check_code) AS failure_count,

    CASE
        WHEN COUNT(d.check_code) = 0
            THEN 'PASS'
        ELSE 'FAIL'
    END AS result_status

FROM core.data_quality_checks c

LEFT JOIN core.detected_data_quality_issues d
    ON c.check_code = d.check_code

GROUP BY
    c.check_code,
    c.check_name,
    c.quality_dimension,
    c.target_table,
    c.default_severity;



