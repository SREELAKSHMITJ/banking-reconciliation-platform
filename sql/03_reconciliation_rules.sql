-- Reconciliation rule catalogue

CREATE TABLE IF NOT EXISTS core.reconciliation_rules (
    rule_code VARCHAR(10) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_category VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    default_severity VARCHAR(20) NOT NULL
);


INSERT INTO core.reconciliation_rules
    (rule_code, rule_name, rule_category, description, default_severity)
VALUES

('REC001', 'MISSING_TRANSACTION', 'PRESENCE',
 'Downstream record exists without a matching transaction', 'HIGH'),

('REC002', 'MISSING_LEDGER', 'PRESENCE',
 'Successful transaction exists without a matching ledger entry', 'HIGH'),

('REC003', 'MISSING_SETTLEMENT', 'PRESENCE',
 'Successful transaction exists without a matching settlement record', 'HIGH'),

('REC004', 'LEDGER_AMOUNT_MISMATCH', 'AMOUNT',
 'Transaction amount does not match ledger amount', 'HIGH'),

('REC005', 'SETTLEMENT_AMOUNT_MISMATCH', 'AMOUNT',
 'Transaction amount does not match settlement amount', 'HIGH'),

('REC006', 'LEDGER_SETTLEMENT_AMOUNT_MISMATCH', 'AMOUNT',
 'Ledger amount does not match settlement amount', 'HIGH'),

('REC007', 'LEDGER_STATUS_MISMATCH', 'STATUS',
 'Successful transaction has an unexpected ledger status', 'HIGH'),

('REC008', 'SETTLEMENT_STATUS_MISMATCH', 'STATUS',
 'Successful transaction has an unexpected settlement status', 'HIGH'),

('REC009', 'UNEXPECTED_LEDGER_POSTING', 'STATUS',
 'Failed transaction was unexpectedly posted to the ledger', 'CRITICAL'),

('REC010', 'UNEXPECTED_SETTLEMENT', 'STATUS',
 'Failed transaction was unexpectedly settled', 'CRITICAL'),

('REC011', 'SETTLEMENT_WITHOUT_LEDGER', 'SEQUENCE',
 'Settlement exists without a corresponding ledger entry', 'CRITICAL'),

('REC012', 'SETTLEMENT_AFTER_FAILED_LEDGER', 'SEQUENCE',
 'Settlement occurred despite a failed ledger entry', 'CRITICAL'),

('REC013', 'TRANSACTION_LEDGER_ACCOUNT_MISMATCH', 'ACCOUNT',
 'Transaction and ledger account numbers do not match', 'CRITICAL'),

('REC014', 'TRANSACTION_SETTLEMENT_ACCOUNT_MISMATCH', 'ACCOUNT',
 'Transaction and settlement account numbers do not match', 'CRITICAL'),

('REC015', 'LEDGER_SETTLEMENT_ACCOUNT_MISMATCH', 'ACCOUNT',
 'Ledger and settlement account numbers do not match', 'CRITICAL'),

('REC016', 'TRANSACTION_TYPE_MISMATCH', 'TYPE',
 'Transaction type does not match ledger entry type', 'HIGH'),

('REC017', 'DUPLICATE_TRANSACTION', 'DUPLICATE',
 'Potential duplicate business transaction detected', 'HIGH'),

('REC018', 'DUPLICATE_LEDGER_ENTRY', 'DUPLICATE',
 'Multiple ledger entries exist for the same transaction reference', 'HIGH'),

('REC019', 'DUPLICATE_SETTLEMENT', 'DUPLICATE',
 'Multiple settlement records exist for the same transaction reference', 'HIGH'),

('REC020', 'LATE_LEDGER_POSTING', 'TIMING',
 'Ledger entry was posted outside the configured processing window', 'MEDIUM'),

('REC021', 'LATE_SETTLEMENT', 'TIMING',
 'Settlement occurred outside the configured processing window', 'HIGH'),

('REC022', 'LEDGER_BEFORE_TRANSACTION', 'SEQUENCE',
 'Ledger timestamp occurs before the transaction timestamp', 'HIGH'),

('REC023', 'SETTLEMENT_BEFORE_TRANSACTION', 'SEQUENCE',
 'Settlement timestamp occurs before the transaction timestamp', 'CRITICAL'),

('REC024', 'SETTLEMENT_BEFORE_LEDGER', 'SEQUENCE',
 'Settlement timestamp occurs before the ledger posting timestamp', 'HIGH')

ON CONFLICT (rule_code) DO NOTHING;