from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / ".gemini" / "development"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from web.backend.app.main import app
