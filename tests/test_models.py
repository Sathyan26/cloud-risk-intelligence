import pytest
from pydantic import ValidationError

from data_pipeline.models import Customer, Transaction

VALID_CUSTOMER = dict(
    customer_id="CUST000001",
    first_name="Jane",
    last_name="Doe",
    email="jane@example.com",
    signup_date="2024-01-15",
    region="North America",
)

VALID_TRANSACTION = dict(
    transaction_id="TXN00000001",
    customer_id="CUST000001",
    amount="42.50",
    transaction_date="2024-06-01T12:00:00",
    merchant_category="dining",
    status="completed",
)


def test_valid_customer_passes():
    customer = Customer(**VALID_CUSTOMER)
    assert customer.region == "North America"


@pytest.mark.parametrize("alias,expected", [
    ("USA", "North America"),
    ("US", "North America"),
    ("N. America", "North America"),
    ("EU", "Europe"),
    ("APAC", "Asia"),
    ("LatAm", "South America"),
    ("ANZ", "Oceania"),
])
def test_region_aliases_normalize_to_canonical_value(alias, expected):
    customer = Customer(**{**VALID_CUSTOMER, "region": alias})
    assert customer.region == expected


def test_unrecognized_region_is_rejected():
    with pytest.raises(ValidationError):
        Customer(**{**VALID_CUSTOMER, "region": "Mars"})


def test_missing_region_is_rejected():
    with pytest.raises(ValidationError):
        Customer(**{**VALID_CUSTOMER, "region": None})


def test_blank_customer_id_is_rejected():
    with pytest.raises(ValidationError):
        Customer(**{**VALID_CUSTOMER, "customer_id": "  "})


def test_malformed_email_degrades_to_none_instead_of_rejecting_customer():
    customer = Customer(**{**VALID_CUSTOMER, "email": "jane_at_example.com"})
    assert customer.email is None


def test_missing_email_is_allowed():
    customer = Customer(**{**VALID_CUSTOMER, "email": None})
    assert customer.email is None


def test_valid_transaction_passes():
    transaction = Transaction(**VALID_TRANSACTION)
    assert transaction.status == "completed"


@pytest.mark.parametrize("status_variant", ["Completed", "COMPLETE", "done"])
def test_status_variants_normalize_to_completed(status_variant):
    transaction = Transaction(**{**VALID_TRANSACTION, "status": status_variant})
    assert transaction.status == "completed"


def test_unrecognized_status_is_rejected():
    with pytest.raises(ValidationError):
        Transaction(**{**VALID_TRANSACTION, "status": "refunded"})


def test_negative_amount_is_rejected():
    with pytest.raises(ValidationError):
        Transaction(**{**VALID_TRANSACTION, "amount": "-10.00"})


def test_zero_amount_is_rejected():
    with pytest.raises(ValidationError):
        Transaction(**{**VALID_TRANSACTION, "amount": "0"})


def test_blank_transaction_id_is_rejected():
    with pytest.raises(ValidationError):
        Transaction(**{**VALID_TRANSACTION, "transaction_id": ""})
