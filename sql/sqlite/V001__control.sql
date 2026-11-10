CREATE TABLE control_source_registry (
    source       TEXT PRIMARY KEY,
    bundle       TEXT NOT NULL,
    connector    TEXT NOT NULL,
    refresh      TEXT,
    owner        TEXT,
    active       INTEGER NOT NULL DEFAULT 1,
    last_loaded  TEXT
);

CREATE TABLE control_run (
    run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    bundle       TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    status       TEXT NOT NULL
        CHECK (status IN ('running', 'succeeded', 'failed'))
);

CREATE TABLE control_run_step (
    step_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       INTEGER NOT NULL REFERENCES control_run (run_id),
    source       TEXT NOT NULL,
    layer        TEXT NOT NULL,
    status       TEXT NOT NULL,
    rows_in      INTEGER,
    rows_out     INTEGER,
    error        TEXT,
    started_at   TEXT NOT NULL,
    finished_at  TEXT
);

CREATE TABLE control_dq_result (
    run_id       INTEGER NOT NULL REFERENCES control_run (run_id),
    source       TEXT NOT NULL,
    rule         TEXT NOT NULL,
    column_name  TEXT NOT NULL,
    severity     TEXT NOT NULL,
    failed       INTEGER NOT NULL,
    total        INTEGER NOT NULL
);

CREATE TABLE control_match_decision (
    decision_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    alias        TEXT NOT NULL,
    customer_key INTEGER,
    decision     TEXT NOT NULL,
    decided_by   TEXT,
    decided_at   TEXT
);