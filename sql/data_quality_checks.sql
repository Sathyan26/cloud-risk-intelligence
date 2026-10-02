-- Row counts
SELECT 'raw_customers' AS table_name, COUNT(*) FROM raw_customers
UNION ALL
SELECT 'raw_transactions', COUNT(*) FROM raw_transactions;

-- Missing values per column
SELECT
    COUNT(*) FILTER (WHERE customer_id IS NULL) AS missing_customer_id,
    COUNT(*) FILTER (WHERE first_name  IS NULL) AS missing_first_name,
    COUNT(*) FILTER (WHERE email       IS NULL) AS missing_email,
    COUNT(*) FILTER (WHERE signup_date IS NULL) AS missing_signup_date,
    COUNT(*) FILTER (WHERE region      IS NULL) AS missing_region
FROM raw_customers;

SELECT
    COUNT(*) FILTER (WHERE amount           IS NULL) AS missing_amount,
    COUNT(*) FILTER (WHERE transaction_date IS NULL) AS missing_transaction_date
FROM raw_transactions;

-- Duplicate customer_id / transaction_id (exact repeats)
SELECT customer_id, COUNT(*) AS occurrences
FROM raw_customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

SELECT transaction_id, COUNT(*) AS occurrences
FROM raw_transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- Malformed emails
SELECT customer_id, email
FROM raw_customers
WHERE email IS NOT NULL
  AND email !~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

-- Orphan transactions: customer_id with no matching customer (anti-join)
SELECT t.transaction_id, t.customer_id
FROM raw_transactions t
LEFT JOIN raw_customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- Negative amounts
SELECT transaction_id, amount
FROM raw_transactions
WHERE amount::NUMERIC < 0;

-- Statistical outliers via z-score (CTE + window functions)
WITH amount_stats AS (
    SELECT
        transaction_id,
        amount::NUMERIC AS amount_num,
        AVG(amount::NUMERIC) OVER () AS avg_amount,
        STDDEV(amount::NUMERIC) OVER () AS stddev_amount
    FROM raw_transactions
    WHERE amount IS NOT NULL
)
SELECT transaction_id, amount_num,
       (amount_num - avg_amount) / NULLIF(stddev_amount, 0) AS z_score
FROM amount_stats
WHERE ABS((amount_num - avg_amount) / NULLIF(stddev_amount, 0)) > 3
ORDER BY z_score DESC;

-- Inconsistent categorical values
SELECT region, COUNT(*) FROM raw_customers GROUP BY region ORDER BY COUNT(*) DESC;
SELECT status, COUNT(*) FROM raw_transactions GROUP BY status ORDER BY COUNT(*) DESC;