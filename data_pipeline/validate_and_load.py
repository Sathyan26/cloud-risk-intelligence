import json

import pandas as pd
from pydantic import ValidationError
from sqlalchemy import text

from db import get_engine
from models import Customer, Transaction


def clean_value(value):
    if isinstance(value, float) and pd.isna(value):
        return None
    return value


def load_raw(engine, table_name):
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    records = df.to_dict(orient="records")
    return [{k: clean_value(v) for k, v in row.items()} for row in records]


def format_validation_error(exc):
    parts = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"])
        parts.append(f"{field}: {err['msg']}")
    return "; ".join(parts)


def validate_rows(rows, model_cls, table_name):
    valid, rejected = [], []
    for row in rows:
        try:
            valid.append(model_cls(**row))
        except ValidationError as e:
            rejected.append({
                "source_table": table_name,
                "source_row_json": json.dumps(row, default=str),
                "rejection_reason": format_validation_error(e),
            })
    return valid, rejected


def dedupe(objects, id_field, table_name):
    seen = set()
    deduped, rejected = [], []
    for obj in objects:
        key = getattr(obj, id_field)
        if key in seen:
            rejected.append({
                "source_table": table_name,
                "source_row_json": obj.model_dump_json(),
                "rejection_reason": f"duplicate {id_field}: {key}",
            })
        else:
            seen.add(key)
            deduped.append(obj)
    return deduped, rejected


def insert_rejected(conn, rejected_rows):
    if not rejected_rows:
        return
    conn.execute(
        text(
            "INSERT INTO rejected_records (source_table, source_row_json, rejection_reason) "
            "VALUES (:source_table, CAST(:source_row_json AS JSONB), :rejection_reason)"
        ),
        rejected_rows,
    )


def main():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE rejected_records, transactions, customers RESTART IDENTITY CASCADE"))

    raw_customers = load_raw(engine, "raw_customers")
    raw_transactions = load_raw(engine, "raw_transactions")

    valid_customers, rejected_customers = validate_rows(raw_customers, Customer, "raw_customers")
    valid_customers, dup_customers = dedupe(valid_customers, "customer_id", "raw_customers")

    valid_transactions, rejected_transactions = validate_rows(raw_transactions, Transaction, "raw_transactions")
    valid_transactions, dup_transactions = dedupe(valid_transactions, "transaction_id", "raw_transactions")

    valid_customer_ids = {c.customer_id for c in valid_customers}
    orphan_transactions = []
    referenced_transactions = []
    for t in valid_transactions:
        if t.customer_id in valid_customer_ids:
            referenced_transactions.append(t)
        else:
            orphan_transactions.append({
                "source_table": "raw_transactions",
                "source_row_json": t.model_dump_json(),
                "rejection_reason": f"customer_id not found in valid customers: {t.customer_id}",
            })
    valid_transactions = referenced_transactions

    customers_df = pd.DataFrame([c.model_dump() for c in valid_customers])
    transactions_df = pd.DataFrame([t.model_dump() for t in valid_transactions])

    customers_df.to_sql("customers", engine, if_exists="append", index=False)
    transactions_df.to_sql("transactions", engine, if_exists="append", index=False)

    all_rejected = rejected_customers + dup_customers + rejected_transactions + dup_transactions + orphan_transactions
    with engine.begin() as conn:
        insert_rejected(conn, all_rejected)

    with engine.begin() as conn:
        conn.execute(text("CALL take_data_quality_snapshot()"))

    print(f"Customers:    {len(valid_customers)} loaded, {len(rejected_customers) + len(dup_customers)} rejected")
    print(f"Transactions: {len(valid_transactions)} loaded, "
          f"{len(rejected_transactions) + len(dup_transactions) + len(orphan_transactions)} rejected")


if __name__ == "__main__":
    main()
