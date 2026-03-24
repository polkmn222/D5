import os
from pathlib import Path
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

# BASE_DIR is .gemini/development/web/
BASE_DIR = Path(__file__).resolve().parents[3]

# Search for all frontend/templates directories under objects/
OBJECT_TEMPLATES = []
objects_path = BASE_DIR / "objects"
if objects_path.exists():
    for obj_dir in objects_path.iterdir():
        if obj_dir.is_dir():
            template_dir = obj_dir / "frontend" / "templates"
            if template_dir.exists():
                OBJECT_TEMPLATES.append(str(template_dir))

CORE_TEMPLATES = BASE_DIR / "core" / "frontend" / "templates"
MESSAGE_TEMPLATES = BASE_DIR / "message" / "frontend" / "templates"
AI_AGENT_TEMPLATES = BASE_DIR.parent / "ai_agent" / "frontend" / "templates"

# Legacy path for compatibility during migration
LEGACY_TEMPLATES = BASE_DIR / "frontend" / "templates"

search_paths = [
    str(CORE_TEMPLATES),
    str(MESSAGE_TEMPLATES),
    str(AI_AGENT_TEMPLATES),
    str(LEGACY_TEMPLATES),
] + OBJECT_TEMPLATES

logger.info(f"Jinja2 Template Search Paths: {search_paths}")

templates = Jinja2Templates(directory=search_paths)

def currency_filter(value):
    try:
        if value is None: return ""
        return f"₩ {int(value):,}"
    except (ValueError, TypeError):
        if value == "N/A": return ""
        return f"₩ {value}" if value else ""

def datetime_format(value, format="%Y. %-m. %-d. %p %I:%M"):
    if value is None or value == "" or value == "N/A":
        return ""
    from datetime import datetime
    if isinstance(value, datetime):
        return value.strftime(format)
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime(format)
        except ValueError:
            return value
    return str(value)

def format_value(value):
    """
    Returns blank for None or 'N/A'.
    Preserves actual blank strings.
    """
    if value is None or value == "N/A":
        return ""
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
