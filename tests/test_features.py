import pandas as pd

from ml.features import build_customer_churn_features, build_transaction_features


def test_build_transaction_features_has_expected_columns():
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3"],
        "customer_id": ["C1", "C1", "C2"],
        "amount": [100.0, 100.0, 50.0],
        "transaction_date": ["2024-01-01T10:00:00", "2024-01-02T14:00:00", "2024-01-03T08:00:00"],
        "merchant_category": ["dining", "dining", "travel"],
    })

    features = build_transaction_features(df)

    for col in ["transaction_id", "amount", "log_amount", "amount_vs_customer_avg", "hour_of_day"]:
        assert col in features.columns
    assert "category_dining" in features.columns
    assert "category_travel" in features.columns


def test_amount_vs_customer_avg_is_one_for_uniform_spender():
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "customer_id": ["C1", "C1"],
        "amount": [100.0, 100.0],
        "transaction_date": ["2024-01-01T10:00:00", "2024-01-02T10:00:00"],
        "merchant_category": ["dining", "dining"],
    })

    features = build_transaction_features(df)

    assert (features["amount_vs_customer_avg"] == 1.0).all()


def _customers_df():
    return pd.DataFrame({
        "customer_id": ["C1", "C2", "C3", "C4", "C5"],
        "signup_date": ["2023-01-01"] * 5,
        "region": ["North America"] * 5,
    })


def _transactions_df():
    # Last-transaction dates spread out so recency (days before 2024-01-31) is
    # distinct per customer: C1=0, C2=10, C3=20, C4=30, C5=40.
    last_dates = {
        "C1": "2024-01-31",
        "C2": "2024-01-21",
        "C3": "2024-01-11",
        "C4": "2024-01-01",
        "C5": "2023-12-22",
    }
    rows = []
    for i, (cust, last_date) in enumerate(last_dates.items()):
        rows.append({
            "transaction_id": f"T{i}-early",
            "customer_id": cust,
            "amount": 50.0,
            "transaction_date": "2023-12-01T00:00:00",
            "merchant_category": "dining",
        })
        rows.append({
            "transaction_id": f"T{i}-last",
            "customer_id": cust,
            "amount": 50.0,
            "transaction_date": f"{last_date}T00:00:00",
            "merchant_category": "travel",
        })
    return pd.DataFrame(rows)


def test_recency_days_is_not_leaked_into_features():
    features = build_customer_churn_features(_customers_df(), _transactions_df(), churn_quantile=0.8)

    assert "recency_days" not in features.columns
    assert "churned" in features.columns


def test_most_stale_customer_is_flagged_churned_and_freshest_is_not():
    features = build_customer_churn_features(_customers_df(), _transactions_df(), churn_quantile=0.8)
    by_customer = features.set_index("customer_id")["churned"]

    assert by_customer["C5"] == 1  # most stale (40 days since last transaction)
    assert by_customer["C1"] == 0  # most recent (0 days since last transaction)


def test_customer_with_no_transactions_is_treated_as_churned():
    customers = _customers_df()
    transactions = _transactions_df()
    # Drop all of C1's transactions -- they signed up but never transacted.
    transactions = transactions[transactions["customer_id"] != "C1"]

    features = build_customer_churn_features(customers, transactions, churn_quantile=0.8)
    by_customer = features.set_index("customer_id")

    assert by_customer.loc["C1", "frequency"] == 0
    assert by_customer.loc["C1", "churned"] == 1
