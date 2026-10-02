-- Per-customer spending, ranked overall and within their region.
-- CTE -> aggregation -> window functions (global RANK + PARTITION BY RANK).
CREATE OR REPLACE VIEW customer_spending_summary AS
WITH customer_stats AS (
    SELECT
        c.customer_id,
        c.region,
        COUNT(t.transaction_id) AS transaction_count,
        COALESCE(AVG(t.amount), 0) AS avg_transaction,
        COALESCE(SUM(t.amount), 0) AS total_spending
    FROM customers c
    LEFT JOIN transactions t ON t.customer_id = c.customer_id
    GROUP BY c.customer_id, c.region
)
SELECT
    customer_id,
    region,
    transaction_count,
    avg_transaction,
    total_spending,
    RANK() OVER (ORDER BY total_spending DESC) AS spending_rank,
    RANK() OVER (PARTITION BY region ORDER BY total_spending DESC) AS regional_spending_rank
FROM customer_stats;

-- Week-over-week transaction volume/value per region, the kind of trend
-- the GenAI assistant will eventually narrate ("risk increased 18% this week").
-- CTE -> aggregation with FILTER -> window function (LAG) for period-over-period change.
CREATE OR REPLACE VIEW weekly_transaction_trends AS
WITH weekly AS (
    SELECT
        date_trunc('week', t.transaction_date)::date AS week_start,
        c.region,
        COUNT(*) AS transaction_count,
        SUM(t.amount) AS total_amount,
        AVG(t.amount) AS avg_amount,
        COUNT(*) FILTER (WHERE t.amount > 500) AS high_value_count
    FROM transactions t
    JOIN customers c ON c.customer_id = t.customer_id
    GROUP BY 1, 2
)
SELECT
    week_start,
    region,
    transaction_count,
    total_amount,
    avg_amount,
    high_value_count,
    LAG(total_amount) OVER (PARTITION BY region ORDER BY week_start) AS prev_week_total_amount,
    ROUND(
        100.0 * (total_amount - LAG(total_amount) OVER (PARTITION BY region ORDER BY week_start))
        / NULLIF(LAG(total_amount) OVER (PARTITION BY region ORDER BY week_start), 0),
        1
    ) AS pct_change_vs_prev_week
FROM weekly
ORDER BY region, week_start;

-- What's landing in rejected_records, grouped by the failing field/rule.
CREATE OR REPLACE VIEW rejection_reason_breakdown AS
SELECT
    source_table,
    split_part(rejection_reason, ':', 1) AS reason_category,
    COUNT(*) AS occurrences
FROM rejected_records
GROUP BY source_table, split_part(rejection_reason, ':', 1)
ORDER BY occurrences DESC;

-- Time series of pipeline health, one row per time validate_and_load.py (or,
-- later, the Lambda equivalent) runs. A VIEW can't INSERT, which is exactly
-- why this is a genuine stored PROCEDURE instead.
CREATE TABLE IF NOT EXISTS data_quality_snapshots (
    id                          SERIAL PRIMARY KEY,
    snapshot_taken_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_customers_loaded      INT NOT NULL,
    total_transactions_loaded   INT NOT NULL,
    total_rejected_records      INT NOT NULL,
    rejection_rate_pct          NUMERIC(5,2) NOT NULL
);

CREATE OR REPLACE PROCEDURE take_data_quality_snapshot()
LANGUAGE plpgsql
AS $$
DECLARE
    v_customers    INT;
    v_transactions INT;
    v_rejected     INT;
    v_total_raw    INT;
BEGIN
    SELECT COUNT(*) INTO v_customers FROM customers;
    SELECT COUNT(*) INTO v_transactions FROM transactions;
    SELECT COUNT(*) INTO v_rejected FROM rejected_records;

    SELECT (SELECT COUNT(*) FROM raw_customers) + (SELECT COUNT(*) FROM raw_transactions)
    INTO v_total_raw;

    INSERT INTO data_quality_snapshots (
        total_customers_loaded, total_transactions_loaded,
        total_rejected_records, rejection_rate_pct
    )
    VALUES (
        v_customers, v_transactions, v_rejected,
        ROUND(100.0 * v_rejected / NULLIF(v_total_raw, 0), 2)
    );
END;
$$;
