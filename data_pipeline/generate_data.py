import os
import random

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

NUM_CUSTOMERS = 2000
NUM_TRANSACTIONS = 20000
OUTPUT_DIR = "data/raw"

REGIONS = ["North America", "Europe", "Asia", "South America", "Africa", "Oceania"]
REGION_VARIANTS = {
    "North America": ["North America", "N. America", "USA", "US"],
    "Europe": ["Europe", "EU"],
    "Asia": ["Asia", "APAC"],
    "South America": ["South America", "LatAm"],
    "Africa": ["Africa"],
    "Oceania": ["Oceania", "ANZ"],
}
MERCHANT_CATEGORIES = [
    "groceries", "electronics", "travel", "dining",
    "utilities", "entertainment", "healthcare", "retail",
]


def generate_customers(n):
    customers = []
    for i in range(1, n + 1):
        region = random.choice(REGIONS)
        customers.append({
            "customer_id": f"CUST{i:06d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "signup_date": fake.date_between(start_date="-3y", end_date="today"),
            "region": region,
        })
    return pd.DataFrame(customers)


def inject_customer_issues(df):
    df = df.copy()

    missing_email_idx = df.sample(frac=0.04, random_state=1).index
    df.loc[missing_email_idx, "email"] = None

    malformed_idx = df.sample(frac=0.02, random_state=2).index
    df.loc[malformed_idx, "email"] = df.loc[malformed_idx, "email"].astype(str).str.replace("@", "_at_")

    missing_region_idx = df.sample(frac=0.03, random_state=3).index
    df.loc[missing_region_idx, "region"] = None

    def pick_variant(region):
        if pd.isna(region):
            return region
        return random.choice(REGION_VARIANTS.get(region, [region]))

    variant_idx = df.sample(frac=0.15, random_state=4).index
    df.loc[variant_idx, "region"] = df.loc[variant_idx, "region"].apply(pick_variant)

    dup_rows = df.sample(frac=0.02, random_state=5)
    df = pd.concat([df, dup_rows], ignore_index=True)

    df["signup_date"] = df["signup_date"].astype(str)
    return df


def generate_transactions(customer_ids, n):
    transactions = []
    for i in range(1, n + 1):
        transactions.append({
            "transaction_id": f"TXN{i:08d}",
            "customer_id": random.choice(customer_ids),
            "amount": round(np.random.exponential(scale=80) + 5, 2),
            "transaction_date": fake.date_time_between(start_date="-180d", end_date="now"),
            "merchant_category": random.choice(MERCHANT_CATEGORIES),
            "status": "completed",
        })
    return pd.DataFrame(transactions)


def inject_transaction_issues(df):
    df = df.copy()

    missing_amt_idx = df.sample(frac=0.015, random_state=10).index
    df.loc[missing_amt_idx, "amount"] = None

    negative_idx = df.sample(frac=0.005, random_state=11).index
    df.loc[negative_idx, "amount"] = -df.loc[negative_idx, "amount"]

    outlier_idx = df.sample(frac=0.003, random_state=12).index
    df.loc[outlier_idx, "amount"] = df.loc[outlier_idx, "amount"] * np.random.uniform(20, 50, size=len(outlier_idx))
    outlier_transaction_ids = set(df.loc[outlier_idx, "transaction_id"])

    orphan_idx = df.sample(frac=0.01, random_state=13).index
    df.loc[orphan_idx, "customer_id"] = [f"CUST9{random.randint(90000, 99999)}" for _ in range(len(orphan_idx))]

    dup_rows = df.sample(frac=0.01, random_state=14)
    df = pd.concat([df, dup_rows], ignore_index=True)

    missing_date_idx = df.sample(frac=0.01, random_state=15).index
    df.loc[missing_date_idx, "transaction_date"] = None

    status_variants = {"completed": ["completed", "Completed", "COMPLETE", "done"]}
    variant_idx = df.sample(frac=0.1, random_state=16).index
    df.loc[variant_idx, "status"] = df.loc[variant_idx, "status"].apply(
        lambda s: random.choice(status_variants.get(s, [s]))
    )

    return df, outlier_transaction_ids


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    customers = generate_customers(NUM_CUSTOMERS)
    customers_dirty = inject_customer_issues(customers)

    transactions = generate_transactions(customers["customer_id"].tolist(), NUM_TRANSACTIONS)
    transactions_dirty, outlier_transaction_ids = inject_transaction_issues(transactions)

    customers_dirty.to_csv(f"{OUTPUT_DIR}/customers.csv", index=False)
    transactions_dirty.to_csv(f"{OUTPUT_DIR}/transactions.csv", index=False)

    # Ground truth for evaluating unsupervised anomaly detection later. This is
    # deliberately NOT written alongside transactions.csv or loaded into the
    # pipeline — a real system wouldn't have it. It only exists because we're
    # the ones who injected the anomalies, and it lets us measure whether the
    # anomaly-detection model actually catches what we planted.
    pd.DataFrame({
        "transaction_id": sorted(outlier_transaction_ids),
        "is_synthetic_outlier": True,
    }).to_csv(f"{OUTPUT_DIR}/transaction_outlier_ground_truth.csv", index=False)

    print(f"Wrote {len(customers_dirty)} customer rows to {OUTPUT_DIR}/customers.csv")
    print(f"Wrote {len(transactions_dirty)} transaction rows to {OUTPUT_DIR}/transactions.csv")
    print(f"Wrote {len(outlier_transaction_ids)} ground-truth outlier IDs to "
          f"{OUTPUT_DIR}/transaction_outlier_ground_truth.csv")


if __name__ == "__main__":
    main()