import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Lead, Opportunity, Contact, Model
from backend.app.services.search_service import SearchService

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed test data
        db.add(Lead(id="L1", first_name="John", last_name="Doe", email="john@example.com"))
        db.add(Contact(id="C1", name="Jane Smith", email="jane@example.com"))
        db.add(Opportunity(id="O1", name="Big Deal", stage="Prospecting"))
        db.add(Model(id="M1", name="Model X", description="Luxury SUV"))
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_search_all(db):
    results = SearchService.global_search(db, "John", scope="all")
    assert len(results) == 1
    assert results[0]["type"] == "Lead"
    
    results = SearchService.global_search(db, "Deal", scope="all")
    assert len(results) == 1
    assert results[0]["type"] == "Opportunity"

def test_scoped_search_lead(db):
    # Search for "John" in Leads (should find)
    results = SearchService.global_search(db, "John", scope="lead")
    assert len(results) == 1
    assert results[0]["type"] == "Lead"
    
    # Search for "John" in Opportunities (should NOT find)
    results = SearchService.global_search(db, "John", scope="opportunity")
    assert len(results) == 0

def test_scoped_search_model(db):
    results = SearchService.global_search(db, "Model", scope="model")
    assert len(results) == 1
    assert results[0]["type"] == "Model"
    assert results[0]["name"] == "Model X"

def test_case_insensitivity(db):
    results = SearchService.global_search(db, "john", scope="all")
    assert len(results) == 1
    assert results[0]["name"] == "John Doe"

def test_empty_query(db):
    results = SearchService.global_search(db, "", scope="all")
    assert len(results) == 0
