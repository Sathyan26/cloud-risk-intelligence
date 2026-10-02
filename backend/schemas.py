from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class CustomerSummary(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    region: str
    signup_date: date
    churn_probability: Optional[float] = None
    predicted_churned: Optional[bool] = None


class CustomerDetail(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    region: str
    signup_date: date
    email: Optional[str] = None
    transaction_count: int
    total_spending: float
    churn_probability: Optional[float] = None
    predicted_churned: Optional[bool] = None


class TransactionOut(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    transaction_date: datetime
    merchant_category: str
    status: str
    anomaly_score: Optional[float] = None
    is_anomaly: Optional[bool] = None


class TopSpender(BaseModel):
    customer_id: str
    region: str
    transaction_count: int
    avg_transaction: float
    total_spending: float
    spending_rank: int
    regional_spending_rank: int


class WeeklyTrend(BaseModel):
    week_start: date
    region: str
    transaction_count: int
    total_amount: float
    avg_amount: float
    high_value_count: int
    prev_week_total_amount: Optional[float] = None
    pct_change_vs_prev_week: Optional[float] = None


class DataQualitySnapshot(BaseModel):
    snapshot_taken_at: datetime
    total_customers_loaded: int
    total_transactions_loaded: int
    total_rejected_records: int
    rejection_rate_pct: float


class RejectionBreakdownItem(BaseModel):
    source_table: str
    reason_category: str
    occurrences: int


class ChurnRiskCustomer(BaseModel):
    customer_id: str
    region: str
    churn_probability: float
    predicted_churned: bool


class AssistantRequest(BaseModel):
    question: str


class ToolCallLog(BaseModel):
    tool: str
    input: dict[str, Any]


class AssistantResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallLog]
