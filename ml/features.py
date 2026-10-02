import numpy as np
import pandas as pd

from data_pipeline.db import get_engine


def load_transactions():
    engine = get_engine()
    return pd.read_sql(
        "SELECT transaction_id, customer_id, amount, transaction_date, merchant_category "
        "FROM transactions",
        engine,
    )


def load_customers():
    engine = get_engine()
    return pd.read_sql("SELECT customer_id, signup_date, region FROM customers", engine)


def build_transaction_features(df):
    df = df.copy()
    df["amount"] = df["amount"].astype(float)
    df["log_amount"] = np.log1p(df["amount"])

    customer_avg = df.groupby("customer_id")["amount"].transform("mean")
    df["amount_vs_customer_avg"] = df["amount"] / customer_avg

    df["hour_of_day"] = pd.to_datetime(df["transaction_date"]).dt.hour

    category_dummies = pd.get_dummies(df["merchant_category"], prefix="category")

    feature_df = pd.concat(
        [
            df[["transaction_id", "amount", "log_amount", "amount_vs_customer_avg", "hour_of_day"]],
            category_dummies,
        ],
        axis=1,
    )
    return feature_df


def build_customer_churn_features(customers_df, transactions_df, churn_quantile=0.8):
    customers_df = customers_df.copy()
    transactions_df = transactions_df.copy()
    transactions_df["transaction_date"] = pd.to_datetime(transactions_df["transaction_date"])
    customers_df["signup_date"] = pd.to_datetime(customers_df["signup_date"])

    # Snapshot date: the latest activity in the dataset, not wall-clock "today" --
    # recency should be relative to the data, so re-running this later doesn't
    # silently shift every label.
    reference_date = transactions_df["transaction_date"].max()

    agg = transactions_df.groupby("customer_id").agg(
        frequency=("transaction_id", "count"),
        monetary_total=("amount", "sum"),
        monetary_avg=("amount", "mean"),
        last_transaction_date=("transaction_date", "max"),
        distinct_categories=("merchant_category", "nunique"),
    ).reset_index()

    merged = customers_df.merge(agg, on="customer_id", how="left")

    merged["frequency"] = merged["frequency"].fillna(0)
    merged["monetary_total"] = merged["monetary_total"].fillna(0.0)
    merged["monetary_avg"] = merged["monetary_avg"].fillna(0.0)
    merged["distinct_categories"] = merged["distinct_categories"].fillna(0)

    merged["tenure_days"] = (reference_date - merged["signup_date"]).dt.days

    never_transacted = merged["last_transaction_date"].isna()
    merged["recency_days"] = (reference_date - merged["last_transaction_date"]).dt.days
    merged.loc[never_transacted, "recency_days"] = merged.loc[never_transacted, "tenure_days"]

    # recency_days defines the label and must NOT also be used as a feature --
    # that would be leaking the target straight into the inputs. Using a quantile
    # cutoff (classic RFM scoring) instead of a fixed day-count so the label
    # adapts to this dataset's actual recency distribution rather than guessing
    # a day threshold that might land almost everyone (or no one) as "churned."
    recency_cutoff = merged["recency_days"].quantile(churn_quantile)
    merged["churned"] = (merged["recency_days"] >= recency_cutoff).astype(int)

    region_dummies = pd.get_dummies(merged["region"], prefix="region")

    feature_cols = ["frequency", "monetary_total", "monetary_avg", "distinct_categories", "tenure_days"]
    features = pd.concat(
        [merged[["customer_id"] + feature_cols], region_dummies, merged[["churned"]]],
        axis=1,
    )
    return features
