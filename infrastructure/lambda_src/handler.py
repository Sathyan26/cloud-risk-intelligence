import json
import os

import boto3
import psycopg2
from pydantic import ValidationError

from data_pipeline.models import Customer, Transaction

s3 = boto3.client("s3")

MODEL_BY_PREFIX = {
    "raw/customers/": Customer,
    "raw/transactions/": Transaction,
}


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def model_for_key(key):
    for prefix, model in MODEL_BY_PREFIX.items():
        if key.startswith(prefix):
            return model
    return None


def handler(event, context):
    """
    S3 ObjectCreated trigger. Mirrors the validation logic in
    data_pipeline/validate_and_load.py: every row is checked against its
    Pydantic model, valid rows go to the clean table, everything else goes
    to rejected_records with a reason. This is the same rule set as the
    local pipeline -- the point of this handler is the trigger wiring
    (S3 -> Lambda -> Postgres), not a second copy of the validation rules.
    """
    conn = get_db_connection()
    try:
        with conn, conn.cursor() as cur:
            for record in event["Records"]:
                bucket = record["s3"]["bucket"]["name"]
                key = record["s3"]["object"]["key"]

                model = model_for_key(key)
                if model is None:
                    continue

                obj = s3.get_object(Bucket=bucket, Key=key)
                rows = json.loads(obj["Body"].read())

                target_table = "customers" if model is Customer else "transactions"

                for row in rows:
                    try:
                        validated = model(**row)
                        columns = ", ".join(validated.model_fields.keys())
                        placeholders = ", ".join(["%s"] * len(validated.model_fields))
                        cur.execute(
                            f"INSERT INTO {target_table} ({columns}) VALUES ({placeholders}) "
                            f"ON CONFLICT DO NOTHING",
                            list(validated.model_dump().values()),
                        )
                    except ValidationError as exc:
                        cur.execute(
                            "INSERT INTO rejected_records (source_table, source_row_json, rejection_reason) "
                            "VALUES (%s, %s, %s)",
                            (f"raw_{target_table}", json.dumps(row, default=str), str(exc)),
                        )
    finally:
        conn.close()

    return {"statusCode": 200}
