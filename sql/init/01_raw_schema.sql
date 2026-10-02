-- Permissive staging tables mirroring the raw CSV columns exactly (all TEXT).
-- Type/format enforcement happens in the validation layer (data_pipeline/models.py),
-- not here -- this is the "data just landed from S3" stand-in.

CREATE TABLE IF NOT EXISTS raw_customers (
    customer_id     TEXT,
    first_name      TEXT,
    last_name       TEXT,
    email           TEXT,
    signup_date     TEXT,
    region          TEXT
);

CREATE TABLE IF NOT EXISTS raw_transactions (
    transaction_id      TEXT,
    customer_id         TEXT,
    amount               TEXT,
    transaction_date    TEXT,
    merchant_category   TEXT,
    status               TEXT
);
