# Cloud Risk Intelligence Platform

A data-quality, risk-scoring, and churn-monitoring platform for transaction data: ingest messy records, validate and clean them against a real schema, surface quality and risk through SQL analytics and ML, and ask a GenAI assistant to explain what happened — grounded in real query results, not guesses.

Built end-to-end: synthetic data generation → SQL-based validation and analytics → two ML models → a FastAPI backend with a tool-using GenAI assistant → a React dashboard. Containerized with Docker, tested with pytest, checked by CI, and designed (though not yet deployed) for AWS.

## What it actually demonstrates

| Area | What's here |
|---|---|
| **Data engineering** | Synthetic "messy" data generator with deliberately injected nulls, duplicates, malformed values, and outliers; a Pydantic-based validation layer with tiered severity (hard rejects vs. soft field degradation); a rejected-records audit trail |
| **SQL** | CTEs, window functions (`RANK`, `LAG`, `PARTITION BY`), views, a genuine stored `PROCEDURE`, anti-joins, aggregate `FILTER` clauses |
| **ML** | Unsupervised anomaly detection (Isolation Forest) evaluated against a held-out synthetic ground truth; a supervised churn classifier (Random Forest) with an honestly-reported AUC and a documented data limitation |
| **GenAI** | A tool-use (function-calling) assistant that only answers from real query results — verified to refuse fabricating metrics it has no data for |
| **Backend/Frontend** | FastAPI + React dashboard, fully wired to live data |
| **Ops** | Docker Compose (verified working end-to-end), a 32-test pytest suite, GitHub Actions CI, and a cost-conscious Terraform module for the AWS deployment |

## Architecture

```
 CSV generation ──▶ raw_customers / raw_transactions (staging tables, all-TEXT)
                            │
                            ▼
               Pydantic validation (data_pipeline/validate_and_load.py)
                     │                        │
              valid rows                 invalid rows
                     │                        │
                     ▼                        ▼
         customers / transactions      rejected_records
         (typed, constrained)          (reason + raw row, JSONB)
                     │
                     ▼
     SQL analytics (views, window functions, stored procedure)
     + ML scoring (anomaly detection, churn) ──▶ transaction_risk_scores,
                                                  customer_churn_scores
                     │
                     ▼
            FastAPI backend ──▶ React dashboard
                     │
                     ▼
          GenAI assistant (tool-use over the same query layer)
```

**Status note**: everything above runs locally/in Docker today. The original design also calls for S3 → Lambda as the ingestion front door in AWS (Phase 2) — that's written as Terraform + a Lambda handler in `infrastructure/`, validated for syntax, but **not yet deployed**, since the AWS account used for this project was suspended mid-build. See [Cloud deployment status](#cloud-deployment-status-not-yet-live) below — worth reading before assuming the AWS half is live.

## Tech stack

Python (pandas, NumPy, Pydantic, SQLAlchemy, scikit-learn, FastAPI), PostgreSQL, React + Vite + Recharts, the Anthropic API (tool use), Docker Compose, GitHub Actions, Terraform.

## Project structure

```
data_pipeline/   synthetic data generation, Pydantic validation models, raw-load + validate/load scripts
sql/init/        numbered schema files (staging tables, clean schema, ML tables, views/procedure) -- auto-applied by Postgres on first container start
sql/             ad-hoc exploratory data-quality queries
ml/              feature engineering, anomaly detection, churn model, consolidated evaluation report
backend/         FastAPI app: queries, Pydantic response schemas, the GenAI assistant
frontend/        React dashboard (Vite)
tests/           pytest suite (no live DB required -- the API tests mock the query layer)
infrastructure/  Terraform (AWS) + the Lambda handler it deploys
.github/workflows/  CI: lint, test, Docker build validation
```

## Getting started

### Option A: Docker (recommended)

```bash
docker compose up -d postgres api frontend
docker compose --profile tools run --rm pipeline   # generates data, loads it, validates it, trains + scores both ML models
```

Dashboard: http://localhost:5173 · API docs: http://localhost:8000/docs

The `pipeline` service is a one-off job (not started by default) — rerun it any time to regenerate and rescore the dataset. Postgres's schema is created automatically from `sql/init/*.sql` the first time its container starts.

You'll need a `.env` file with `ANTHROPIC_API_KEY` set for the GenAI assistant endpoint to work (see `.env` usage in `backend/assistant.py`); the rest of the dashboard works without it.

### Option B: Native (no Docker)

1. `python -m venv venv && venv\Scripts\Activate.ps1` (Windows) then `pip install -r requirements.txt`
2. Install PostgreSQL locally, create a database + role, and run the files in `sql/init/` against it in order (`01_` through `04_`)
3. Set `DATABASE_URL` and `ANTHROPIC_API_KEY` in a `.env` file at the project root
4. `python data_pipeline/generate_data.py && python -m data_pipeline.load_raw && python data_pipeline/validate_and_load.py && python -m ml.evaluation_report`
5. `uvicorn backend.main:app --reload` and, separately, `npm install && npm run dev` inside `frontend/`

## Testing

```bash
pytest -v
```

32 tests, no live database required — covers Pydantic validation rules (including the region/email severity-tiering described below), ML feature engineering (including an explicit check that the churn label's `recency_days` is never leaked into the model's own features), and the API layer (query functions mocked).

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: `ruff` lint, the pytest suite, then — only if both pass — a Docker build-validation job for both images.

## Key design decisions worth being able to explain

- **Validation severity is tiered, not uniform.** A malformed email degrades gracefully (nulled, customer kept) rather than rejecting the whole customer record — because the `customers`/`transactions` foreign key meant one bad field was cascading to reject that customer's entire transaction history. `region`, by contrast, is a hard requirement, because it's used directly in the analytics layer (`customer_spending_summary` groups by it). Not every invalid field deserves the same severity of response.
- **Anomaly detection is unsupervised on purpose.** There's no real fraud-label dataset (there never is, for a new system) — Isolation Forest with a business-chosen contamination rate (1%, not the true injected rate, which would be leaking ground truth) mirrors how real fraud-detection cold starts actually work. Evaluated against a hidden synthetic ground truth: ~93% recall, deliberately low precision (most flags are organically large transactions, not the ones we planted — that's expected, not a bug).
- **The churn model's AUC (~0.65) is reported honestly, not polished.** The synthetic transaction generator assigns customers and dates uniformly at random — there's no real behavioral decline pattern to learn, so `frequency`/`monetary_total` dominate the model's feature importance mostly because they're mechanically linked to recency in how the data was built, not because of real churn psychology. A real dataset with genuine behavioral drift would be expected to perform meaningfully better. Saying this plainly is safer than letting the number speak for itself.
- **The GenAI assistant uses tool-use, not free-form SQL generation or embeddings-based RAG.** The model picks from a small set of pre-built, parameterized query functions — it can't execute arbitrary SQL (no injection surface) and can't fabricate a metric that isn't backed by a real query (verified: asked about a "risk score" that doesn't exist in the schema, it said so instead of inventing one).

## Cloud deployment status (not yet live)

The Phase 2 AWS architecture — S3 ingestion bucket, a Lambda validation trigger, RDS Postgres, the VPC wiring between them — exists as Terraform in `infrastructure/terraform/` and a handler in `infrastructure/lambda_src/`. It's been checked with `terraform validate` and `terraform fmt`, so the configuration is internally consistent, but it has **never been applied against real AWS** (the account was suspended during this project). That's a meaningfully different claim than "deployed and verified" — worth being direct about if asked.

Cost-conscious choices baked into that config, for when it can be applied: no NAT gateway (a free S3 gateway endpoint covers Lambda's only outbound need instead — NAT alone would burn a large share of a small project budget just sitting idle), the smallest RDS instance class eligible for the free tier, single-AZ (not multi-AZ), an S3 lifecycle rule expiring objects after 30 days, and a 14-day CloudWatch log retention cap instead of the indefinite default.
