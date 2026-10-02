from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend import queries
from backend.assistant import ask_assistant
from backend.schemas import (
    AssistantRequest,
    AssistantResponse,
    ChurnRiskCustomer,
    CustomerDetail,
    CustomerSummary,
    TopSpender,
    TransactionOut,
    WeeklyTrend,
)

app = FastAPI(title="Cloud Risk Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/customers", response_model=list[CustomerSummary])
def list_customers(region: Optional[str] = None, limit: int = Query(50, le=200), offset: int = 0):
    df = queries.get_customers(region=region, limit=limit, offset=offset)
    return df.to_dict(orient="records")


@app.get("/customers/{customer_id}", response_model=CustomerDetail)
def customer_detail(customer_id: str):
    df = queries.get_customer_detail(customer_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Customer not found")
    return df.to_dict(orient="records")[0]


@app.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    customer_id: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    df = queries.get_transactions(customer_id=customer_id, is_anomaly=is_anomaly, limit=limit, offset=offset)
    return df.to_dict(orient="records")


@app.get("/analytics/top-spenders", response_model=list[TopSpender])
def top_spenders(limit: int = Query(10, le=100)):
    df = queries.get_top_spenders(limit=limit)
    return df.to_dict(orient="records")


@app.get("/analytics/weekly-trends", response_model=list[WeeklyTrend])
def weekly_trends(region: Optional[str] = None):
    df = queries.get_weekly_trends(region=region)
    return df.to_dict(orient="records")


@app.get("/analytics/data-quality")
def data_quality():
    snapshot_df = queries.get_latest_data_quality_snapshot()
    breakdown_df = queries.get_rejection_breakdown()
    return {
        "latest_snapshot": snapshot_df.to_dict(orient="records")[0] if not snapshot_df.empty else None,
        "rejection_breakdown": breakdown_df.to_dict(orient="records"),
    }


@app.get("/risk/anomalies", response_model=list[TransactionOut])
def top_anomalies(limit: int = Query(20, le=200)):
    df = queries.get_top_anomalies(limit=limit)
    return df.to_dict(orient="records")


@app.get("/risk/churn", response_model=list[ChurnRiskCustomer])
def top_churn_risks(limit: int = Query(20, le=200)):
    df = queries.get_top_churn_risks(limit=limit)
    return df.to_dict(orient="records")


@app.post("/assistant/ask", response_model=AssistantResponse)
def assistant_ask(request: AssistantRequest):
    return ask_assistant(request.question)
