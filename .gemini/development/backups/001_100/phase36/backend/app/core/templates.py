import os
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

# Absolute paths for reliability
# __file__ is /.../.gemini/skills/backend/app/core/templates.py
# parent 1: core, parent 2: app, parent 3: backend, parent 4: skills (BASE_DIR)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FRONTEND_TEMPLATES = os.path.join(BASE_DIR, "frontend", "templates")
# PROJECT_ROOT is D4 (the parent of .gemini)
# BASE_DIR is .gemini/skills
# Parent of skills is .gemini
# Parent of .gemini is D4
AI_AGENT_TEMPLATES = os.path.join(BASE_DIR, "ai_agent", "frontend", "templates")

logger.info(f"Jinja2 Template Search Paths: {FRONTEND_TEMPLATES}, {AI_AGENT_TEMPLATES}")

templates = Jinja2Templates(directory=[FRONTEND_TEMPLATES, AI_AGENT_TEMPLATES])

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
