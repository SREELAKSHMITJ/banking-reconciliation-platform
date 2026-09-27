-- Exception lifecycle history

CREATE TABLE core.exception_status_history (
    history_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    exception_id INTEGER NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    change_note TEXT,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_exception
        FOREIGN KEY (exception_id)
        REFERENCES core.reconciliation_exceptions(exception_id)
);


-- Protect valid exception status values

ALTER TABLE core.reconciliation_exceptions
ADD CONSTRAINT chk_exception_status
CHECK (
    status IN (
        'OPEN',
        'IN_PROGRESS',
        'RESOLVED'
    )
);