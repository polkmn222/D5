from pathlib import Path
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

# This file is at web/backend/app/core/templates.py
# BASE_DIR should be web/
BASE_DIR = Path(__file__).resolve().parents[3]

FRONTEND_TEMPLATES = BASE_DIR / "frontend" / "templates"
MESSAGE_TEMPLATES = BASE_DIR / "message" / "frontend" / "templates"
AI_AGENT_TEMPLATES = BASE_DIR.parent / "ai_agent" / "ui" / "frontend" / "templates"

search_paths = [
    str(FRONTEND_TEMPLATES),
    str(MESSAGE_TEMPLATES),
    str(AI_AGENT_TEMPLATES),
]

templates = Jinja2Templates(directory=search_paths)

def currency_filter(value):
    try:
        if value is None: return ""
        return f"₩ {int(value):,}"
    except (ValueError, TypeError):
        return ""

def datetime_format(value, format="%Y. %-m. %-d. %p %I:%M"):
    if not value: return ""
    from datetime import datetime
    if isinstance(value, datetime):
        return value.strftime(format)
    return str(value)

def format_value(value):
    if value is None: return ""
    return value

def temperature_label(value):
    normalized = str(value).strip().lower() if value not in (None, "", "N/A") else ""
    mapping = {
        "hot": "Hot",
        "urgent": "Hot",
        "warm": "Warm",
        "gold": "Warm",
        "cold": "Cold",
        "new": "Cold",
    }
    if not normalized:
        return ""
    return mapping.get(normalized, "Cold")

templates.env.filters["currency"] = currency_filter
templates.env.filters["datetime_format"] = datetime_format
templates.env.filters["format_value"] = format_value
templates.env.filters["temperature_label"] = temperature_label
