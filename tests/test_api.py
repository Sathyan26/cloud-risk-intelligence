import pandas as pd
from fastapi.testclient import TestClient

from backend import main


def _client():
    return TestClient(main.app)


def test_health():
    response = _client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_customers(monkeypatch):
    fake_df = pd.DataFrame([{
        "customer_id": "CUST000001",
        "first_name": "Jane",
        "last_name": "Doe",
        "region": "North America",
        "signup_date": "2024-01-15",
        "churn_probability": 0.2,
        "predicted_churned": False,
    }])
    monkeypatch.setattr(main.queries, "get_customers", lambda **kwargs: fake_df)

    response = _client().get("/customers")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["customer_id"] == "CUST000001"


def test_customer_detail_not_found_returns_404(monkeypatch):
    monkeypatch.setattr(main.queries, "get_customer_detail", lambda customer_id: pd.DataFrame())

    response = _client().get("/customers/CUST999999")

    assert response.status_code == 404


def test_customer_detail_found(monkeypatch):
    fake_df = pd.DataFrame([{
        "customer_id": "CUST000001",
        "first_name": "Jane",
        "last_name": "Doe",
        "region": "North America",
        "signup_date": "2024-01-15",
        "email": "jane@example.com",
        "transaction_count": 5,
        "total_spending": 123.45,
        "churn_probability": 0.2,
        "predicted_churned": False,
    }])
    monkeypatch.setattr(main.queries, "get_customer_detail", lambda customer_id: fake_df)

    response = _client().get("/customers/CUST000001")

    assert response.status_code == 200
    assert response.json()["total_spending"] == 123.45


def test_top_anomalies(monkeypatch):
    fake_df = pd.DataFrame([{
        "transaction_id": "TXN00000001",
        "customer_id": "CUST000001",
        "amount": 999.99,
        "transaction_date": "2024-06-01T12:00:00",
        "merchant_category": "dining",
        "status": "completed",
        "anomaly_score": 0.75,
        "is_anomaly": True,
    }])
    monkeypatch.setattr(main.queries, "get_top_anomalies", lambda limit: fake_df)

    response = _client().get("/risk/anomalies?limit=5")

    assert response.status_code == 200
    assert response.json()[0]["is_anomaly"] is True


def test_assistant_ask_uses_mocked_response(monkeypatch):
    monkeypatch.setattr(
        main, "ask_assistant",
        lambda question: {"answer": "Mocked answer", "tool_calls": []},
    )

    response = _client().post("/assistant/ask", json={"question": "test?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Mocked answer", "tool_calls": []}
