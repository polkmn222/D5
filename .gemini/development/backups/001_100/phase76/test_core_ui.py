from fastapi.testclient import TestClient
from web.backend.app.main import app
from db.database import engine, Base

def test_dashboard_route():
    # Ensure tables are created for the test context
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        # Check for presence of navigation or specific dashboard elements
        assert "Home" in response.text or "Dashboard" in response.text

def test_static_css_load():
    # Note: style.css might have been renamed or moved in recent phases. 
    # Let's check for base.css which is usually present.
    with TestClient(app) as client:
        response = client.get("/static/css/base.css")
        if response.status_code != 200:
            # Fallback to style.css if base.css is missing
            response = client.get("/static/css/style.css")
        
        assert response.status_code == 200
