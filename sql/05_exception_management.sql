-- =========================================================
-- RECONCILIATION EXCEPTION MANAGEMENT
-- Stores detected reconciliation issues
-- =========================================================


CREATE TABLE IF NOT EXISTS core.reconciliation_exceptions (
    exception_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    reference_number VARCHAR(30) NOT NULL,

    rule_code VARCHAR(10) NOT NULL,

    variance NUMERIC(15,2),

    severity VARCHAR(20) NOT NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',

    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    resolved_at TIMESTAMP,

    CONSTRAINT fk_exception_rule
        FOREIGN KEY (rule_code)
        REFERENCES core.reconciliation_rules(rule_code),

    CONSTRAINT uq_exception_reference_rule
        UNIQUE (reference_number, rule_code)
);


-- =========================================================
-- LOAD CURRENT DETECTIONS INTO EXCEPTION TABLE
-- =========================================================

INSERT INTO core.reconciliation_exceptions
    (
        reference_number,
        rule_code,
        variance,
        severity
    )

SELECT
    d.reference_number,
    d.rule_code,
    d.variance,
    r.default_severity

FROM core.detected_reconciliation_rules d

JOIN core.reconciliation_rules r
    ON d.rule_code = r.rule_code

ON CONFLICT (reference_number, rule_code)
DO NOTHING;