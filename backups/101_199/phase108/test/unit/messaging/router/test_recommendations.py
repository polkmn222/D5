import uuid

from fastapi.testclient import TestClient

from ai_agent.backend.recommendations import AIRecommendationService
from db.database import Base, SessionLocal, engine
from db.models import Contact, Model, Opportunity, VehicleSpecification
from web.backend.app.main import app


def test_messaging_recommendations_match_ai_recommendation_service(monkeypatch):
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    brand = VehicleSpecification(id=f"br_{suffix}", name="Test Brand", record_type="Brand")
    model = Model(id=f"mo_{suffix}", name="Roadster", brand=brand.id)
    contact = Contact(id=f"co_{suffix}", first_name="Ari", last_name="Kim", phone="010-1234-5678")
    opp = Opportunity(id=f"op_{suffix}", name="Hot Deal", contact=contact.id, model=model.id, stage="Negotiation/Review")
    opp.temp_display = "Urgent"

    session.add(brand)
    session.flush()
    session.add_all([model, contact])
    session.flush()
    session.add(opp)
    session.commit()
    opp_id = opp.id
    contact_id = contact.id

    monkeypatch.setattr(AIRecommendationService, "get_ai_recommendations", lambda db, limit=5: [opp])

    try:
        with TestClient(app) as client:
            response = client.get("/messaging/recommendations")
    finally:
        session.close()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == opp_id
    assert payload[0]["contact_id"] == contact_id
    assert payload[0]["temperature"] == "Hot"
    assert payload[0]["model"]["name"] == "Roadster"


def test_messaging_recommendations_skip_unsendable_items_but_keep_ai_order(monkeypatch):
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    brand = VehicleSpecification(id=f"br2_{suffix}", name="Test Brand 2", record_type="Brand")
    model = Model(id=f"mo2_{suffix}", name="Touring", brand=brand.id)
    silent_contact = Contact(id=f"co2a_{suffix}", first_name="No", last_name="Phone", phone=None)
    live_contact = Contact(id=f"co2b_{suffix}", first_name="Ready", last_name="Sender", phone="010-9999-8888")
    skipped_opp = Opportunity(id=f"op2a_{suffix}", name="Skipped Deal", contact=silent_contact.id, model=model.id, stage="Test Drive")
    kept_opp = Opportunity(id=f"op2b_{suffix}", name="Sendable Deal", contact=live_contact.id, model=model.id, stage="Negotiation/Review")
    skipped_opp.temp_display = "Hot"
    kept_opp.temp_display = "Urgent"

    session.add(brand)
    session.flush()
    session.add_all([model, silent_contact, live_contact])
    session.flush()
    session.add_all([skipped_opp, kept_opp])
    session.commit()
    kept_id = kept_opp.id

    monkeypatch.setattr(AIRecommendationService, "get_ai_recommendations", lambda db, limit=50: [skipped_opp, kept_opp])

    try:
        with TestClient(app) as client:
            response = client.get("/messaging/recommendations")
    finally:
        session.close()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == kept_id
    assert payload[0]["temperature"] == "Hot"
