import os
from pathlib import Path
import logging
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from web.backend.app.utils.perf_diagnostics import attach_sqlalchemy_instrumentation, diagnostics_enabled

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)
logger = logging.getLogger("web.perf")
_bootstrap_started_at = time.perf_counter()

def normalize_database_url(raw_url: str) -> str:
    if not raw_url:
        raise ValueError("DATABASE_URL is not set. PostgreSQL is mandatory.")
        
    url = make_url(raw_url)

    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")

    if url.get_backend_name() == "postgresql" and "sslmode" not in url.query:
        url = url.update_query_dict({"sslmode": "require"})

    return url.render_as_string(hide_password=False)


def build_engine(database_url: str):
    engine_kwargs: dict[str, object] = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }
    return create_engine(database_url, **engine_kwargs)


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        raise ValueError("DATABASE_URL is not set in the environment. PostgreSQL is required.")
    return db_url


SQLALCHEMY_DATABASE_URL = normalize_database_url(get_database_url())

engine = build_engine(SQLALCHEMY_DATABASE_URL)
attach_sqlalchemy_instrumentation(engine)

AUDIT_COLUMN_TABLES = [
    "vehicle_specifications",
    "models",
    "contacts",
    "leads",
    "products",
    "opportunities",
    "assets",
    "message_sends",
    "message_templates",
    "attachments",
    "lead_list_views",
]


def ensure_runtime_columns() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name in AUDIT_COLUMN_TABLES:
            try:
                columns = {column["name"] for column in inspector.get_columns(table_name)}
            except Exception:
                continue

            if "created_by" not in columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN created_by VARCHAR"))
            if "updated_by" not in columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN updated_by VARCHAR"))


ensure_runtime_columns()
if diagnostics_enabled():
    logger.info(
        "web_perf_startup component=db_bootstrap duration_ms=%.2f",
        (time.perf_counter() - _bootstrap_started_at) * 1000,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# END FILE
