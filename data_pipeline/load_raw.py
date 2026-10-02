import pandas as pd
from sqlalchemy import text

from data_pipeline.db import get_engine

RAW_DIR = "data/raw"


def load_csv(engine, csv_path, table_name):
    df = pd.read_csv(csv_path)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_name}"))
        df.to_sql(table_name, conn, if_exists="append", index=False)
    print(f"Loaded {len(df)} rows into {table_name}")


def main():
    engine = get_engine()
    load_csv(engine, f"{RAW_DIR}/customers.csv", "raw_customers")
    load_csv(engine, f"{RAW_DIR}/transactions.csv", "raw_transactions")


if __name__ == "__main__":
    main()
