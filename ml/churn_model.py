import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sqlalchemy import text

from data_pipeline.db import get_engine
from ml.features import build_customer_churn_features, load_customers, load_transactions

MODEL_DIR = "ml/models"
CHURN_QUANTILE = 0.8  # bottom 20% by recency = "churned"


def main():
    customers = load_customers()
    transactions = load_transactions()
    features = build_customer_churn_features(customers, transactions, CHURN_QUANTILE)

    print(f"Churn rate in dataset: {features['churned'].mean():.1%} "
          f"({features['churned'].sum()} of {len(features)} customers)")

    feature_cols = [c for c in features.columns if c not in ("customer_id", "churned")]
    X = features[feature_cols]
    y = features["churned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300, max_depth=8, class_weight="balanced", random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    report_text = classification_report(y_test, y_pred, target_names=["active", "churned"])
    report_dict = classification_report(
        y_test, y_pred, target_names=["active", "churned"], output_dict=True, zero_division=0
    )
    auc = roc_auc_score(y_test, y_proba)

    print(report_text)
    print(f"ROC-AUC: {auc:.3f}")

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("Feature importances:")
    print(importances.to_string())

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "feature_cols": feature_cols}, f"{MODEL_DIR}/churn_random_forest.joblib")

    # Score every customer (not just the held-out test split) for the dashboard/GenAI layer later.
    scores_df = features[["customer_id"]].copy()
    scores_df["churn_probability"] = model.predict_proba(X)[:, 1]
    scores_df["predicted_churned"] = model.predict(X).astype(bool)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE customer_churn_scores"))
        scores_df.to_sql("customer_churn_scores", conn, if_exists="append", index=False)

    return {
        "total_customers": int(len(y)),
        "churned_count": int(y.sum()),
        "churn_rate": float(y.mean()),
        "precision_churned": float(report_dict["churned"]["precision"]),
        "recall_churned": float(report_dict["churned"]["recall"]),
        "f1_churned": float(report_dict["churned"]["f1-score"]),
        "roc_auc": float(auc),
        "feature_importances": importances.round(4).to_dict(),
    }


if __name__ == "__main__":
    main()
