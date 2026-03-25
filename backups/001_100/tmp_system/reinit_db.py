import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import engine, Base
from backend.app.models import * # Import all models to ensure they are registered

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Creating all tables with new schema...")
Base.metadata.create_all(bind=engine)
print("Database schema successfully updated.")
