import os
import sys
from pathlib import Path

from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[4]
APP_ROOT = PROJECT_ROOT / ".gemini" / "development"


def ensure_paths() -> None:
    for path in (PROJECT_ROOT, APP_ROOT):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def bootstrap_runtime():
    ensure_paths()
    database_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("Set TEST_DATABASE_URL to a PostgreSQL test database before running manual verification scripts.")

    os.environ["DATABASE_URL"] = database_url

    from db.database import Base, build_engine, normalize_database_url

    engine = build_engine(normalize_database_url(database_url))
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session_local, Base


def should_reset_database() -> bool:
    return os.getenv("D4_RESET_MANUAL_TEST_DB", "0").strip() == "1"
