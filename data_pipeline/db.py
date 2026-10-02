import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def get_engine():
    database_url = os.environ["DATABASE_URL"]
    return create_engine(database_url)


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        print("Connected successfully:", conn.engine.url)