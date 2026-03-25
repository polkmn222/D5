from sqlalchemy.orm import Session
from typing import List, Dict, Any
from db.models import Lead, Contact, Opportunity, Asset, Product, VehicleSpecification, Model, MessageTemplate, MessageSend
from web.backend.app.utils.error_handler import handle_agent_errors
import logging

logger = logging.getLogger(__name__)

class TrashService:
    @classmethod
    @handle_agent_errors
    def list_deleted_records(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Aggregate all soft-deleted records from core CRM models.
        """
        results = []
        
        models_to_check = [
            (Lead, "Lead"),
            (Contact, "Contact"),
            (Opportunity, "Opportunity"),
            (Asset, "Asset"),
            (Product, "Product"),
            (VehicleSpecification, "Brand"),
            (Model, "Model"),
            (MessageTemplate, "Message Template")
        ]
        
        for model_class, type_label in models_to_check:
            records = db.query(model_class).filter(model_class.deleted_at != None).all()
            for r in records:
                name = getattr(r, "name", None)
                if not name:
                    # Fallback for Lead/Contact names
                    first = getattr(r, "first_name", "")
                    last = getattr(r, "last_name", "")
                    name = f"{first} {last}".strip() or r.id
                
                results.append({
                    "id": r.id,
                    "type": type_label,
                    "object_type": model_class.__name__,
                    "name": name,
                    "deleted_at": r.deleted_at
                })
        
        # Sort by most recently deleted
        results.sort(key=lambda x: x["deleted_at"], reverse=True)
        return results

    @classmethod
    @handle_agent_errors
    def restore_record(cls, db: Session, object_type: str, record_id: str) -> bool:
        """
        Restore a soft-deleted record by clearing its deleted_at field.
        """
        model_class = cls._get_model_class(object_type)
        if not model_class:
            return False
            
        record = db.query(model_class).filter(model_class.id == record_id).first()
        if record:
            record.deleted_at = None
            db.commit()
            return True
        return False

    @classmethod
    @handle_agent_errors
    def hard_delete_record(cls, db: Session, object_type: str, record_id: str) -> bool:
        """
        Permanently delete a record from the database.
        """
        model_class = cls._get_model_class(object_type)
        if not model_class:
            return False
            
        record = db.query(model_class).filter(model_class.id == record_id).first()
        if record:
            db.delete(record)
            db.commit()
            return True
        return False

    @staticmethod
    def _get_model_class(object_type: str):
        mapping = {
            "Lead": Lead,
            "Contact": Contact,
            "Opportunity": Opportunity,
            "Asset": Asset,
            "Product": Product,
            "VehicleSpecification": VehicleSpecification,
            "Model": Model,
            "MessageTemplate": MessageTemplate
        }
        return mapping.get(object_type)
