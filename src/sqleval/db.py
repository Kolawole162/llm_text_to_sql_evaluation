"""Database connection and safe query execution."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()


def get_engine():
    """Engine for the read-only evaluation user (settings come from .env)."""
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "eval_reader"),
        password=os.getenv("DB_PASSWORD", "eval_reader"),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "rushmore"),
    )
    return create_engine(url)


def run_sql(engine, sql):
    """Run one query and return (column_names, rows).

    exec_driver_sql sends the SQL exactly as written. (SQLAlchemy's text() would treat
    PostgreSQL casts such as '::date' as bind parameters and break valid queries.)
    The transaction is always rolled back, so nothing can ever be changed.
    """
    with engine.connect() as conn:
        try:
            result = conn.exec_driver_sql(sql)
            columns = list(result.keys())
            rows = [tuple(r) for r in result.fetchall()]
            return columns, rows
        finally:
            conn.rollback()