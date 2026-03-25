import pytest
import uuid
from db.database import Base, engine, SessionLocal
from db.models import Lead, Contact
from web.backend.app.services.search_service import SearchService
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.contact_service import ContactService

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create some test data
        suffix = uuid.uuid4().hex[:6]
        l1 = LeadService.create_lead(db, first_name="SearchMe", last_name=f"Lead_{suffix}", email=f"search_{suffix}@example.com", phone="010-1111-2222")
        c1 = ContactService.create_contact(db, first_name="FindMe", last_name=f"Contact_{suffix}", email=f"find_{suffix}@example.com", phone="010-3333-4444")
        
        yield db
        
        # Cleanup
        if l1: LeadService.delete_lead(db, l1.id)
        if c1: ContactService.delete_contact(db, c1.id)
    finally:
        db.close()

def test_search_lead_by_name(db):
    data = SearchService.global_search(db, query="SearchMe", scope="lead")
    results = data["results"]
    assert len(results) > 0
    l = next(r for r in results if r['type'] == 'Lead')
    assert 'SearchMe' in l['name']
    assert 'email' in l
    assert 'phone' in l
    assert 'status' in l
    assert 'created_at' in l

def test_search_lead_by_phone(db):
    data = SearchService.global_search(db, query="1111", scope="lead")
    results = data["results"]
    assert len(results) > 0
    assert any(r['type'] == 'Lead' and 'SearchMe' in r['name'] for r in results)

def test_search_lead_by_email_should_fail(db):
    data = SearchService.global_search(db, query="example.com", scope="lead")
    results = data["results"]
    assert len(results) == 0

def test_search_contact_by_name(db):
    data = SearchService.global_search(db, query="FindMe", scope="contact")
    results = data["results"]
    assert len(results) > 0
    c = next(r for r in results if r['type'] == 'Contact')
    assert 'FindMe' in c['name']
    assert 'email' in c
    assert 'phone' in c
    assert 'status' in c
    assert 'created_at' in c

def test_search_contact_by_phone(db):
    data = SearchService.global_search(db, query="3333", scope="contact")
    results = data["results"]
    assert len(results) > 0
    assert any(r['type'] == 'Contact' and 'FindMe' in r['name'] for r in results)

def test_search_contact_by_email_should_fail(db):
    data = SearchService.global_search(db, query="example.com", scope="contact")
    results = data["results"]
    assert len(results) == 0

def test_search_all_grouping(db):
    data = SearchService.global_search(db, query="Me", scope="all")
    results = data["results"]
    counts = data["counts"]
    types = [r['type'] for r in results]
    assert 'Lead' in types
    assert 'Contact' in types
    assert counts.get('Lead', 0) > 0
    assert counts.get('Contact', 0) > 0
