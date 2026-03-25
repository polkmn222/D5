from fastapi.testclient import TestClient
from pathlib import Path
from web.backend.app.main import app
from db.database import engine, Base
from web.backend.app.core.templates import templates

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


def test_templates_register_temperature_label_filter():
    assert "temperature_label" in templates.env.filters


def test_base_template_includes_ajax_modal_submit_helpers():
    base_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/base.html").read_text()

    assert "function runJsonAction" in base_template
    assert "function enhanceModalForms" in base_template
    assert "enhanceModalForms(content);" in base_template
    assert "function showGlobalLoading" in base_template
    assert "function shouldSkipGlobalLoading" in base_template
    assert "sf-global-loading" in base_template


def test_shared_modal_templates_include_save_and_new_submit_mode():
    modal_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/sf_form_modal.html").read_text()
    nested_modal_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/templates/sf_form_modal.html").read_text()
    lead_modal_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/leads/create_edit_modal.html").read_text()

    assert 'data-submit-mode="save-new"' in modal_template
    assert 'data-submit-mode="save-new"' in nested_modal_template
    assert 'data-submit-mode="save-new"' in lead_modal_template
