
import sys
import os

# Add the project root to the Python path
# This allows imports like 'from backend.app.main import app'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now, import the actual FastAPI app instance
from backend.app.main import app

# Vercel will look for this 'app' variable and serve it.
