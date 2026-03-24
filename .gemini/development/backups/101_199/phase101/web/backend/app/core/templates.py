from pathlib import Path
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parents[3]
FRONTEND_TEMPLATES = BASE_DIR / "frontend" / "templates"
MESSAGE_TEMPLATES = BASE_DIR.parent / "message" / "frontend" / "templates"
AI_AGENT_TEMPLATES = BASE_DIR.parent / "ai_agent" / "frontend" / "templates"

logger.info(f"Jinja2 Template Search Paths: {FRONTEND_TEMPLATES}, {MESSAGE_TEMPLATES}, {AI_AGENT_TEMPLATES}")

templates = Jinja2Templates(directory=[str(FRONTEND_TEMPLATES), str(MESSAGE_TEMPLATES), str(AI_AGENT_TEMPLATES)])

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

templates.env.filters["currency"] = currency_filter
templates.env.filters["datetime_format"] = datetime_format
templates.env.filters["format_value"] = format_value
