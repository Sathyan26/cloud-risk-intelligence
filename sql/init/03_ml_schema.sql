CREATE TABLE IF NOT EXISTS transaction_risk_scores (
    transaction_id  TEXT PRIMARY KEY REFERENCES transactions(transaction_id),
    anomaly_score   NUMERIC NOT NULL,
    is_anomaly      BOOLEAN NOT NULL,
    scored_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_churn_scores (
    customer_id        TEXT PRIMARY KEY REFERENCES customers(customer_id),
    churn_probability  NUMERIC NOT NULL,
    predicted_churned  BOOLEAN NOT NULL,
    scored_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_evaluation_runs (
    id           SERIAL PRIMARY KEY,
    run_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    report_json  JSONB NOT NULL
);
