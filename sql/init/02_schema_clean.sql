CREATE TABLE IF NOT EXISTS customers (
    customer_id   TEXT PRIMARY KEY,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT,
    signup_date   DATE NOT NULL,
    region        TEXT NOT NULL,
    CONSTRAINT valid_region CHECK (region IN ('North America','Europe','Asia','South America','Africa','Oceania'))
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      TEXT PRIMARY KEY,
    customer_id         TEXT NOT NULL REFERENCES customers(customer_id),
    amount               NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    transaction_date    TIMESTAMP NOT NULL,
    merchant_category   TEXT NOT NULL,
    status               TEXT NOT NULL CHECK (status IN ('completed'))
);

CREATE TABLE IF NOT EXISTS rejected_records (
    id              SERIAL PRIMARY KEY,
    source_table    TEXT NOT NULL,
    source_row_json JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    rejected_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);