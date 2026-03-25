import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Lead, Opportunity
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
        db.add(Lead(id="L1", first_name="Alice", last_name="Alpha", email="alice@example.com"))
        db.add(Lead(id="L2", first_name="Alex", last_name="Abbot", email="alex@example.com"))
        db.add(Opportunity(id="O1", name="Alpha Project", stage="Prospecting"))
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_search_suggestions_limit(db):
    # Search for "Al" - should return 3 results
    results = SearchService.global_search(db, "Al", scope="all", limit=1)
    # Be careful: limit is PR PER OBJECT in my implementation? 
    # Let's check SearchService.py
    # Yes, it's .limit(limit) for EACH query (Leads, Contacts, etc.)
    # So if limit=1, it could return 1 Lead AND 1 Opportunity.
    
    lead_count = len([r for r in results if r["type"] == "Lead"])
    opp_count = len([r for r in results if r["type"] == "Opportunity"])
    
    assert lead_count <= 1
    assert opp_count <= 1

def test_suggestion_format(db):
    results = SearchService.global_search(db, "Alice", scope="all", limit=5)
    assert len(results) > 0
    item = results[0]
    assert "name" in item
    assert "type" in item
    assert "url" in item
    assert "info" in item

if __name__ == "__main__":
    # Internal dev test
    pass
