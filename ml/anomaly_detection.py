import os

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text

from data_pipeline.db import get_engine
from ml.features import build_transaction_features, load_transactions

MODEL_DIR = "ml/models"
CONTAMINATION = 0.01  # business estimate of expected anomaly rate, not derived from ground truth


def train_and_score():
    transactions = load_transactions()
    features = build_transaction_features(transactions)

    feature_cols = [c for c in features.columns if c != "transaction_id"]
    X = features[feature_cols]

    model = IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=42)
    model.fit(X)

    features["anomaly_score"] = -model.score_samples(X)  # higher = more anomalous
    features["is_anomaly"] = model.predict(X) == -1

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "feature_cols": feature_cols}, f"{MODEL_DIR}/isolation_forest.joblib")

    return features[["transaction_id", "anomaly_score", "is_anomaly"]]


def persist_scores(scores_df):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE transaction_risk_scores"))
        scores_df.to_sql("transaction_risk_scores", conn, if_exists="append", index=False)


def evaluate_against_ground_truth(scores_df):
    ground_truth = pd.read_csv("data/raw/transaction_outlier_ground_truth.csv")
    merged = scores_df.merge(ground_truth, on="transaction_id", how="left")
    merged["is_synthetic_outlier"] = merged["is_synthetic_outlier"].fillna(False)

    true_positives = ((merged["is_anomaly"]) & (merged["is_synthetic_outlier"])).sum()
    false_negatives = ((~merged["is_anomaly"]) & (merged["is_synthetic_outlier"])).sum()
    flagged = merged["is_anomaly"].sum()
    total_synthetic = merged["is_synthetic_outlier"].sum()

    recall = true_positives / total_synthetic if total_synthetic else float("nan")
    precision = true_positives / flagged if flagged else float("nan")

    print(f"Flagged {flagged} of {len(merged)} transactions as anomalous ({flagged / len(merged):.2%})")
    print(f"Of {total_synthetic} known synthetic outliers, caught {true_positives} (recall={recall:.1%})")
    print(f"Precision against synthetic ground truth: {precision:.1%} "
          f"(expect this to look low -- most flags are organically large transactions, "
          f"not ones we artificially planted, which is normal and fine for unsupervised anomaly detection)")
    print(f"Missed {false_negatives} of the synthetic outliers")

    return {
        "total_scored": int(len(merged)),
        "flagged_count": int(flagged),
        "flagged_rate": float(flagged / len(merged)),
        "known_synthetic_outliers": int(total_synthetic),
        "true_positives": int(true_positives),
        "false_negatives": int(false_negatives),
        "recall": float(recall),
        "precision": float(precision),
    }


def main():
    scores_df = train_and_score()
    persist_scores(scores_df)
    return evaluate_against_ground_truth(scores_df)


if __name__ == "__main__":
    main()
