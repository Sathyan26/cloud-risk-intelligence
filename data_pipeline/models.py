import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_validator

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

VALID_REGIONS = {"North America", "Europe", "Asia", "South America", "Africa", "Oceania"}

REGION_ALIASES = {
    "n. america": "North America",
    "usa": "North America",
    "us": "North America",
    "eu": "Europe",
    "apac": "Asia",
    "latam": "South America",
    "anz": "Oceania",
}

STATUS_ALIASES = {
    "completed": "completed",
    "complete": "completed",
    "done": "completed",
}


class Customer(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    signup_date: date
    region: str

    @field_validator("customer_id", "first_name", "last_name")
    @classmethod
    def not_blank(cls, value):
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def degrade_malformed_email(cls, value):
        if value is None:
            return None
        value = value.strip()
        if not EMAIL_REGEX.match(value):
            # Soft failure: a malformed email doesn't disqualify the whole customer
            # record (and cascade-reject every transaction tied to it) — it's
            # supplementary contact info, not a required business identifier.
            return None
        return value

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value):
        if not value or not value.strip():
            raise ValueError("region is missing")
        normalized = REGION_ALIASES.get(value.strip().lower(), value.strip())
        if normalized not in VALID_REGIONS:
            raise ValueError(f"unrecognized region: {value}")
        return normalized


class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    amount: Decimal
    transaction_date: datetime
    merchant_category: str
    status: str

    @field_validator("transaction_id", "customer_id", "merchant_category")
    @classmethod
    def not_blank(cls, value):
        if not value or not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("amount must be positive")
        return value

    @field_validator("status")
    @classmethod
    def normalize_status(cls, value):
        normalized = STATUS_ALIASES.get(value.strip().lower())
        if normalized is None:
            raise ValueError(f"unrecognized status: {value}")
        return normalized


if __name__ == "__main__":
    good = Customer(
        customer_id="CUST000001", first_name="Jane", last_name="Doe",
        email="jane@example.com", signup_date="2024-01-15", region="USA",
    )
    print("Valid customer, region normalized to:", good.region)

    try:
        Customer(
            customer_id="CUST000002", first_name="John", last_name="Smith",
            email="john@example.com", signup_date="2024-01-15", region="Mars",
        )
    except Exception as e:
        print("Correctly rejected bad region:\n", e)