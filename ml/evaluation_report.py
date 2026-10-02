import json
import os
from datetime import datetime, timezone

from sqlalchemy import text

from data_pipeline.db import get_engine
from ml import anomaly_detection, churn_model

REPORT_DIR = "ml/reports"


def persist_report(report):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO model_evaluation_runs (report_json) VALUES (CAST(:report_json AS JSONB))"),
            {"report_json": json.dumps(report)},
        )


def main():
    print("=== Running anomaly detection ===")
    anomaly_metrics = anomaly_detection.main()

    print("\n=== Running churn model ===")
    churn_metrics = churn_model.main()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "anomaly_detection": anomaly_metrics,
        "churn_model": churn_metrics,
    }

    os.makedirs(REPORT_DIR, exist_ok=True)
    filename = f"{REPORT_DIR}/evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)

    persist_report(report)

    print("\n=== Evaluation Report Summary ===")
    print(f"Anomaly detection: flagged {anomaly_metrics['flagged_count']}/{anomaly_metrics['total_scored']} "
          f"transactions ({anomaly_metrics['flagged_rate']:.2%}), "
          f"recall={anomaly_metrics['recall']:.1%} vs known synthetic outliers")
    print(f"Churn model: {churn_metrics['churned_count']}/{churn_metrics['total_customers']} customers "
          f"flagged churned ({churn_metrics['churn_rate']:.1%}), "
          f"ROC-AUC={churn_metrics['roc_auc']:.3f}, churned-class F1={churn_metrics['f1_churned']:.3f}")
    print(f"Full report written to {filename} and logged to model_evaluation_runs")


if __name__ == "__main__":
    main()
