import pandas as pd
from sqlalchemy import text

from data_pipeline.db import get_engine


def get_customers(region=None, limit=50, offset=0):
    engine = get_engine()
    query = text("""
        SELECT c.customer_id, c.first_name, c.last_name, c.region, c.signup_date,
               s.churn_probability, s.predicted_churned
        FROM customers c
        LEFT JOIN customer_churn_scores s ON s.customer_id = c.customer_id
        WHERE (:region IS NULL OR c.region = :region)
        ORDER BY c.customer_id
        LIMIT :limit OFFSET :offset
    """)
    return pd.read_sql(query, engine, params={"region": region, "limit": limit, "offset": offset})


def get_customer_detail(customer_id):
    engine = get_engine()
    query = text("""
        SELECT c.customer_id, c.first_name, c.last_name, c.region, c.signup_date, c.email,
               COALESCE(COUNT(t.transaction_id), 0) AS transaction_count,
               COALESCE(SUM(t.amount), 0) AS total_spending,
               s.churn_probability, s.predicted_churned
        FROM customers c
        LEFT JOIN transactions t ON t.customer_id = c.customer_id
        LEFT JOIN customer_churn_scores s ON s.customer_id = c.customer_id
        WHERE c.customer_id = :customer_id
        GROUP BY c.customer_id, c.first_name, c.last_name, c.region, c.signup_date, c.email,
                 s.churn_probability, s.predicted_churned
    """)
    return pd.read_sql(query, engine, params={"customer_id": customer_id})


def get_transactions(customer_id=None, is_anomaly=None, limit=50, offset=0):
    engine = get_engine()
    query = text("""
        SELECT t.transaction_id, t.customer_id, t.amount, t.transaction_date,
               t.merchant_category, t.status, r.anomaly_score, r.is_anomaly
        FROM transactions t
        LEFT JOIN transaction_risk_scores r ON r.transaction_id = t.transaction_id
        WHERE (:customer_id IS NULL OR t.customer_id = :customer_id)
          AND (:is_anomaly IS NULL OR r.is_anomaly = :is_anomaly)
        ORDER BY t.transaction_date DESC
        LIMIT :limit OFFSET :offset
    """)
    return pd.read_sql(query, engine, params={
        "customer_id": customer_id, "is_anomaly": is_anomaly, "limit": limit, "offset": offset,
    })


def get_top_spenders(limit=10):
    engine = get_engine()
    query = text("SELECT * FROM customer_spending_summary ORDER BY spending_rank LIMIT :limit")
    return pd.read_sql(query, engine, params={"limit": limit})


def get_weekly_trends(region=None):
    engine = get_engine()
    query = text("""
        SELECT * FROM weekly_transaction_trends
        WHERE (:region IS NULL OR region = :region)
        ORDER BY region, week_start
    """)
    return pd.read_sql(query, engine, params={"region": region})


def get_latest_data_quality_snapshot():
    engine = get_engine()
    query = text("SELECT * FROM data_quality_snapshots ORDER BY snapshot_taken_at DESC LIMIT 1")
    return pd.read_sql(query, engine)


def get_rejection_breakdown():
    engine = get_engine()
    return pd.read_sql(text("SELECT * FROM rejection_reason_breakdown"), engine)


def get_top_anomalies(limit=20):
    engine = get_engine()
    query = text("""
        SELECT t.transaction_id, t.customer_id, t.amount, t.transaction_date,
               t.merchant_category, t.status, r.anomaly_score, r.is_anomaly
        FROM transaction_risk_scores r
        JOIN transactions t ON t.transaction_id = r.transaction_id
        WHERE r.is_anomaly = true
        ORDER BY r.anomaly_score DESC
        LIMIT :limit
    """)
    return pd.read_sql(query, engine, params={"limit": limit})


def get_top_churn_risks(limit=20):
    engine = get_engine()
    query = text("""
        SELECT c.customer_id, c.region, s.churn_probability, s.predicted_churned
        FROM customer_churn_scores s
        JOIN customers c ON c.customer_id = s.customer_id
        ORDER BY s.churn_probability DESC
        LIMIT :limit
    """)
    return pd.read_sql(query, engine, params={"limit": limit})
