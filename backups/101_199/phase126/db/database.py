import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

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
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# END FILE
