from pathlib import Path


def test_new_template_modal_router_still_supports_template_form_surface():
    source = Path("development/web/backend/app/api/form_router.py").read_text(encoding="utf-8")

    assert '@router.get("/message_templates/new-modal")' in source
    assert '@router.get("/message_templates/new")' in source
    assert '"templates/sf_form_modal.html"' in source
    assert '"object_type": "MessageTemplate"' in source


def test_shared_modal_template_uses_exact_create_route_pattern():
    source = Path("development/web/frontend/templates/templates/sf_form_modal.html").read_text(encoding="utf-8")

    assert 'action="/{{ p_type }}{% if initial_values and initial_values.id %}/{{ initial_values.id }}{% else %}/{% endif %}"' in source
    assert 'enctype="multipart/form-data"' in source
    assert 'name="image"' in source
    assert 'accept="image/jpeg,image/jpg"' in source


def test_lead_modal_embedded_mode_contract_keeps_lookup_inputs_and_removes_modal_close():
    router_source = Path("development/web/backend/app/api/form_router.py").read_text(encoding="utf-8")
    template_source = Path("development/web/frontend/templates/templates/sf_form_modal.html").read_text(encoding="utf-8")
    embedded_page_source = Path("development/web/frontend/templates/leads/embedded_form_page.html").read_text(encoding="utf-8")

    assert "embedded: int = 0" in router_source
    assert '"embedded": bool(embedded)' in router_source
    assert "fields = [\"first_name\", \"last_name\", \"email\", \"phone\", \"status\", \"gender\", \"brand\", \"model\", \"product\", \"description\"]" in router_source
    assert '@router.get("/leads/embedded-form")' in router_source
    assert '"leads/embedded_form_page.html"' in router_source
    assert "{% if not embedded %}" in template_source
    assert "onclick=\"closeModal()\"" in template_source
    assert "cancelOpsPilotEmbeddedForm" in template_source
    assert "Save & New" in template_source
    assert "{% if embedded %}max-height: none; overflow: visible;{% else %}max-height: 80vh; overflow-y: auto;{% endif %}" in template_source
    assert "lookup-container-{{ field }}" in template_source
    assert "initLookup('lookup-container-{{ field }}'" in template_source
    assert '<script src="/static/js/lookup.js"></script>' in embedded_page_source
    assert '{% include "templates/sf_form_modal.html" %}' in embedded_page_source


def test_form_router_keeps_core_crm_modal_routes_for_create_and_edit_flows():
    source = Path("development/web/backend/app/api/form_router.py").read_text(encoding="utf-8")

    assert '@router.get("/contacts/new-modal")' in source
    assert '@router.get("/contacts/new")' in source
    assert '@router.get("/opportunities/new-modal")' in source
    assert '@router.get("/opportunities/new")' in source
    assert '@router.get("/products/new-modal")' in source
    assert '@router.get("/products/new")' in source
    assert '"object_type": "Contact"' in source
    assert '"object_type": "Opportunity"' in source
    assert '"object_type": "Product"' in source


def test_form_router_keeps_lookup_prefill_contracts_for_related_create_flows():
    source = Path("development/web/backend/app/api/form_router.py").read_text(encoding="utf-8")

    assert '"contact_name": _contact_display_name(contact_obj)' in source
    assert '"brand_name": brand_spec.name if brand_spec else ""' in source
    assert '"model_name": model_obj.name if model_obj else ""' in source
    assert '"product_name": prod_obj.name if prod_obj else ""' in source
    assert '"asset_name": asset_obj.name if asset_obj else ""' in source
    assert 'if model_obj and not brand and getattr(model_obj, "brand", None):' in source
