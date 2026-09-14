CREATE SCHEMA IF NOT EXISTS core;


-- CUSTOMERS
CREATE TABLE IF NOT EXISTS core.customers (
    customer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ACCOUNTS
CREATE TABLE IF NOT EXISTS core.accounts (
    account_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    account_type VARCHAR(20) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'CAD',
    current_balance NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_account_customer
        FOREIGN KEY (customer_id)
        REFERENCES core.customers(customer_id)
);


-- TRANSACTIONS
CREATE TABLE IF NOT EXISTS core.transactions (
    transaction_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id INTEGER NOT NULL,
    reference_number VARCHAR(30) NOT NULL UNIQUE,
    transaction_type VARCHAR(30) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    channel VARCHAR(30),
    status VARCHAR(20) NOT NULL,
    transaction_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_transaction_account
        FOREIGN KEY (account_id)
        REFERENCES core.accounts(account_id),

    CONSTRAINT chk_transaction_amount
        CHECK (amount > 0)
);


-- LEDGER ENTRIES
CREATE TABLE IF NOT EXISTS core.ledger_entries (
    ledger_entry_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_reference VARCHAR(30) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    entry_type VARCHAR(30) NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    posted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_ledger_amount
        CHECK (amount > 0)
);


-- SETTLEMENT RECORDS
CREATE TABLE IF NOT EXISTS core.settlement_records (
    settlement_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_reference VARCHAR(30) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    settlement_amount NUMERIC(15,2) NOT NULL,
    settlement_status VARCHAR(20) NOT NULL,
    settlement_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_settlement_amount
        CHECK (settlement_amount > 0)
);