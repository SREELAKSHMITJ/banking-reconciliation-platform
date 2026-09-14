-- =========================================================
-- RECONCILIATION RULE TEST MATRIX
-- Controlled QA scenarios for presence/status/sequence rules
-- =========================================================

CREATE TABLE IF NOT EXISTS core.status_test_matrix (
    test_case_id INTEGER PRIMARY KEY,
    transaction_state VARCHAR(20) NOT NULL,
    ledger_state VARCHAR(20) NOT NULL,
    settlement_state VARCHAR(20) NOT NULL
);


INSERT INTO core.status_test_matrix
    (test_case_id, transaction_state, ledger_state, settlement_state)
VALUES
(1,  'SUCCESS', 'POSTED',  'SETTLED'),
(2,  'SUCCESS', 'POSTED',  'FAILED'),
(3,  'SUCCESS', 'POSTED',  'MISSING'),
(4,  'SUCCESS', 'FAILED',  'SETTLED'),
(5,  'SUCCESS', 'FAILED',  'FAILED'),
(6,  'SUCCESS', 'FAILED',  'MISSING'),
(7,  'SUCCESS', 'MISSING', 'SETTLED'),
(8,  'SUCCESS', 'MISSING', 'FAILED'),
(9,  'SUCCESS', 'MISSING', 'MISSING'),

(10, 'FAILED',  'POSTED',  'SETTLED'),
(11, 'FAILED',  'POSTED',  'FAILED'),
(12, 'FAILED',  'POSTED',  'MISSING'),
(13, 'FAILED',  'FAILED',  'SETTLED'),
(14, 'FAILED',  'FAILED',  'FAILED'),
(15, 'FAILED',  'FAILED',  'MISSING'),
(16, 'FAILED',  'MISSING', 'SETTLED'),
(17, 'FAILED',  'MISSING', 'FAILED'),
(18, 'FAILED',  'MISSING', 'MISSING'),

(19, 'MISSING', 'POSTED',  'SETTLED'),
(20, 'MISSING', 'POSTED',  'FAILED'),
(21, 'MISSING', 'POSTED',  'MISSING'),
(22, 'MISSING', 'FAILED',  'SETTLED'),
(23, 'MISSING', 'FAILED',  'FAILED'),
(24, 'MISSING', 'FAILED',  'MISSING'),
(25, 'MISSING', 'MISSING', 'SETTLED'),
(26, 'MISSING', 'MISSING', 'FAILED')

ON CONFLICT (test_case_id) DO NOTHING;


-- =========================================================
-- EXPECTED RULE RESULTS
-- Acts as the independent QA answer key
-- =========================================================

CREATE TABLE IF NOT EXISTS core.status_test_expected_rules (
    test_case_id INTEGER NOT NULL,
    rule_code VARCHAR(10) NOT NULL,

    CONSTRAINT pk_status_test_expected_rules
        PRIMARY KEY (test_case_id, rule_code),

    CONSTRAINT fk_expected_test_case
        FOREIGN KEY (test_case_id)
        REFERENCES core.status_test_matrix(test_case_id),

    CONSTRAINT fk_expected_rule
        FOREIGN KEY (rule_code)
        REFERENCES core.reconciliation_rules(rule_code)
);


INSERT INTO core.status_test_expected_rules
    (test_case_id, rule_code)
VALUES
(2,  'REC008'),
(3,  'REC003'),

(4,  'REC007'),
(4,  'REC012'),

(5,  'REC007'),
(5,  'REC008'),

(6,  'REC003'),
(6,  'REC007'),

(7,  'REC002'),
(7,  'REC011'),

(8,  'REC002'),
(8,  'REC008'),
(8,  'REC011'),

(9,  'REC002'),
(9,  'REC003'),

(10, 'REC009'),
(10, 'REC010'),

(11, 'REC009'),
(12, 'REC009'),

(13, 'REC010'),
(13, 'REC012'),

(16, 'REC010'),
(16, 'REC011'),

(17, 'REC011'),

(19, 'REC001'),
(20, 'REC001'),
(21, 'REC001'),

(22, 'REC001'),
(22, 'REC012'),

(23, 'REC001'),
(24, 'REC001'),

(25, 'REC001'),
(25, 'REC011'),

(26, 'REC001'),
(26, 'REC011')

ON CONFLICT (test_case_id, rule_code) DO NOTHING;


-- =========================================================
-- EXPECTED VS ACTUAL VALIDATION
-- PASS           = expected rule was detected
-- MISSED_RULE    = expected rule was not detected
-- FALSE_POSITIVE = unexpected rule was detected
-- =========================================================

WITH expected AS (
    SELECT
        'TST'
        || LPAD(er.test_case_id::TEXT, 3, '0')
            AS reference_number,
        er.rule_code
    FROM core.status_test_expected_rules er
),

actual AS (
    SELECT
        e.reference_number,
        e.rule_code
    FROM core.reconciliation_exceptions e
    WHERE e.reference_number LIKE 'TST%'
),

comparison AS (
    SELECT
        COALESCE(
            expected.reference_number,
            actual.reference_number
        ) AS reference_number,

        COALESCE(
            expected.rule_code,
            actual.rule_code
        ) AS rule_code,

        CASE
            WHEN expected.rule_code IS NOT NULL
             AND actual.rule_code IS NOT NULL
                THEN 'PASS'

            WHEN expected.rule_code IS NOT NULL
             AND actual.rule_code IS NULL
                THEN 'MISSED_RULE'

            WHEN expected.rule_code IS NULL
             AND actual.rule_code IS NOT NULL
                THEN 'FALSE_POSITIVE'
        END AS test_result

    FROM expected

    FULL OUTER JOIN actual
        ON expected.reference_number = actual.reference_number
       AND expected.rule_code = actual.rule_code
)

SELECT
    test_result,
    COUNT(*) AS rule_count
FROM comparison
GROUP BY test_result
ORDER BY test_result;