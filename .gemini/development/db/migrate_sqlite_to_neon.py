import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect
from sqlalchemy.orm import Session

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.append(str(PROJECT_DIR))

from db.database import Base, build_engine, normalize_database_url
from db.models import (
    Asset,
    Attachment,
    Contact,
    Lead,
    MessageSend,
    MessageTemplate,
    Model,
    Opportunity,
    Product,
    VehicleSpecification,
)

load_dotenv(PROJECT_DIR / ".env")

SOURCE_SQLITE_PATH = Path(os.getenv("SOURCE_SQLITE_PATH", PROJECT_DIR / "crm.db"))
TARGET_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
MODEL_ORDER = [
    VehicleSpecification,
    Model,
    Contact,
    Product,
    Lead,
    Asset,
    Attachment,
    MessageTemplate,
    MessageSend,
    Opportunity,
]


def row_to_payload(instance):
    return {
        column.name: normalize_value(getattr(instance, column.name))
        for column in instance.__table__.columns
    }


def normalize_value(value):
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in {"", "None", "null", "NULL"}:
            return None

    return value


def prepare_payload(model, payload):
    prepared = dict(payload)

    if model is Lead:
        prepared["converted_opportunity"] = None

    return prepared


def build_source_id_map(source_session: Session):
    id_map = {}

    for model in MODEL_ORDER:
        id_map[model.__tablename__] = {
            row[0] for row in source_session.query(model.id).all()
        }

    return id_map


def sanitize_foreign_keys(model, payload, source_id_map):
    sanitized = dict(payload)

    for foreign_key in model.__table__.foreign_keys:
        column_name = foreign_key.parent.name
        value = sanitized.get(column_name)

        if value is None:
            continue

        target_table = foreign_key.column.table.name
        if value not in source_id_map.get(target_table, set()):
            sanitized[column_name] = None

    return sanitized


def sync_lead_converted_opportunities(source_session: Session, target_session: Session, source_id_map):
    leads = source_session.query(Lead).filter(Lead.converted_opportunity.isnot(None)).all()

    for lead in leads:
        if lead.converted_opportunity not in source_id_map.get("opportunities", set()):
            continue

        target_lead = target_session.get(Lead, lead.id)
        if target_lead is None:
            continue

        target_lead.converted_opportunity = lead.converted_opportunity

    target_session.commit()
    print(f"Synced converted_opportunity for {len(leads)} leads.")


def migrate():
    if not SOURCE_SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {SOURCE_SQLITE_PATH}")

    if not TARGET_DATABASE_URL:
        raise RuntimeError("DATABASE_URL must point to your Neon database.")

    normalized_target_url = normalize_database_url(TARGET_DATABASE_URL)
    if normalized_target_url.startswith("sqlite"):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL/Neon connection string.")

    source_engine = build_engine(f"sqlite:///{SOURCE_SQLITE_PATH}")
    target_engine = build_engine(normalized_target_url)

    Base.metadata.create_all(bind=target_engine)

    source_inspector = inspect(source_engine)
    source_tables = set(source_inspector.get_table_names())

    with Session(source_engine) as source_session, Session(target_engine) as target_session:
        source_id_map = build_source_id_map(source_session)

        for model in MODEL_ORDER:
            table_name = model.__tablename__
            if table_name not in source_tables:
                print(f"Skipping {table_name}: table not found in source SQLite database.")
                continue

            rows = source_session.query(model).all()
            for row in rows:
                payload = prepare_payload(model, row_to_payload(row))
                payload = sanitize_foreign_keys(model, payload, source_id_map)
                target_session.merge(model(**payload))

            target_session.commit()
            print(f"Migrated {len(rows)} rows into {table_name}.")

        sync_lead_converted_opportunities(source_session, target_session, source_id_map)

    print("SQLite to Neon migration complete.")


if __name__ == "__main__":
    migrate()
