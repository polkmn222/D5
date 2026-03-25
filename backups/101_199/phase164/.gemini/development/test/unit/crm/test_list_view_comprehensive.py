import pytest
import json
from db.database import SessionLocal, Base, engine
from db.models import LeadListView
from web.backend.app.services.lead_list_view_service import LeadListViewService

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_builtin_views_creation(db):
    default_cols = ["name", "email", "phone"]
    builtin_views = (
        {"id": "test-all", "label": "All Tests", "source": "all"},
        {"id": "test-recent", "label": "Recent Tests", "source": "recent"},
    )
    views = LeadListViewService.list_views(db, default_cols, object_type="TestObj", builtin_views=builtin_views)
    
    # Check if builtin views are created
    view_ids = [v["id"] for v in views]
    assert "test-all" in view_ids
    assert "test-recent" in view_ids
    
    # Verify they are system views
    for v in views:
        if v["id"] in ["test-all", "test-recent"]:
            assert v["editable"] is False

def test_custom_view_lifecycle(db):
    default_cols = ["name", "email", "phone"]
    builtin_views = (
        {"id": "test-all", "label": "All Tests", "source": "all"},
        {"id": "test-recent", "label": "Recent Tests", "source": "recent"},
    )
    payload = {
        "label": "My Custom View",
        "visibleColumns": ["name", "email"],
        "filters": {
            "searchTerm": "test",
            "logic": "and",
            "conditions": [{"field": "name", "operator": "contains", "value": "test"}]
        }
    }
    
    # 1. Create
    view = LeadListViewService.create_view(db, payload, default_cols, object_type="TestObj", builtin_views=builtin_views)
    assert view["label"] == "My Custom View"
    assert view["visibleColumns"] == ["name", "email"]
    assert view["filters"]["searchTerm"] == "test"
    
    # 2. Update
    update_payload = {"label": "Updated Label", "visibleColumns": ["phone"]}
    updated = LeadListViewService.update_view(db, view["id"], update_payload, default_cols, object_type="TestObj", builtin_views=builtin_views)
    assert updated["label"] == "Updated Label"
    assert updated["visibleColumns"] == ["phone"]
    
    # 3. Pin
    pinned_id = LeadListViewService.set_pinned_view(db, view["id"], default_cols, pinned=True, object_type="TestObj", builtin_views=builtin_views)
    assert pinned_id == view["id"]
    
    # Verify pinning in list
    views = LeadListViewService.list_views(db, default_cols, object_type="TestObj", builtin_views=builtin_views)
    target = next(v for v in views if v["id"] == view["id"])
    assert target["isPinned"] is True
    
    # 4. Delete
    LeadListViewService.delete_view(db, view["id"], object_type="TestObj", builtin_views=builtin_views)
    
    # Verify deletion
    views = LeadListViewService.list_views(db, default_cols, object_type="TestObj", builtin_views=builtin_views)
    assert not any(v["id"] == view["id"] for v in views)

def test_builtin_view_protection(db):
    default_cols = ["name", "email"]
    builtin_views = (
        {"id": "test-all", "label": "All Tests", "source": "all"},
        {"id": "test-recent", "label": "Recent Tests", "source": "recent"},
    )
    # Should raise ValueError when trying to delete or update builtin view
    with pytest.raises(ValueError, match="Built-in views cannot be edited"):
        LeadListViewService.update_view(db, "test-all", {"label": "Fail"}, default_cols, object_type="TestObj", builtin_views=builtin_views)
    
    with pytest.raises(ValueError, match="Built-in views cannot be deleted"):
        LeadListViewService.delete_view(db, "test-all", object_type="TestObj", builtin_views=builtin_views)
