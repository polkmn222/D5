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
        Permanently delete a record from the database, handling cascading dependencies.
        """
        model_class = cls._get_model_class(object_type)
        if not model_class:
            return False
            
        record = db.query(model_class).filter(model_class.id == record_id).first()
        if not record:
            return False

        try:
            # 1. Handle Object-Specific Cascades
            if object_type == "Contact":
                # Delete related messages
                db.query(MessageSend).filter(MessageSend.contact == record_id).delete(synchronize_session=False)
                # Delete opportunities
                db.query(Opportunity).filter(Opportunity.contact == record_id).delete(synchronize_session=False)
                # Delete assets
                db.query(Asset).filter(Asset.contact == record_id).delete(synchronize_session=False)
                # Nullify lead references
                db.query(Lead).filter(Lead.converted_contact == record_id).update({Lead.converted_contact: None}, synchronize_session=False)

            elif object_type == "Lead":
                # Delete opportunities converted from this lead
                db.query(Opportunity).filter(Opportunity.lead == record_id).delete(synchronize_session=False)

            elif object_type == "Opportunity":
                # Nullify lead references
                db.query(Lead).filter(Lead.converted_opportunity == record_id).update({Lead.converted_opportunity: None}, synchronize_session=False)

            elif object_type == "Product":
                # Delete related opportunities
                db.query(Opportunity).filter(Opportunity.product == record_id).delete(synchronize_session=False)
                # Delete related assets
                db.query(Asset).filter(Asset.product == record_id).delete(synchronize_session=False)
                # Nullify lead references
                db.query(Lead).filter(Lead.product == record_id).update({Lead.product: None}, synchronize_session=False)

            elif object_type == "VehicleSpecification": # Brand
                # Delete Models first
                model_ids = [m.id for m in db.query(Model.id).filter(Model.brand == record_id).all()]
                for mid in model_ids:
                    cls.hard_delete_record(db, "Model", mid)
                # Brand-specific cleanup
                db.query(Opportunity).filter(Opportunity.brand == record_id).delete(synchronize_session=False)
                db.query(Asset).filter(Asset.brand == record_id).delete(synchronize_session=False)
                db.query(Lead).filter(Lead.brand == record_id).delete(synchronize_session=False)
                db.query(Product).filter(Product.brand == record_id).delete(synchronize_session=False)

            elif object_type == "Model":
                db.query(Opportunity).filter(Opportunity.model == record_id).delete(synchronize_session=False)
                db.query(Asset).filter(Asset.model == record_id).delete(synchronize_session=False)
                db.query(Lead).filter(Lead.model == record_id).delete(synchronize_session=False)
                db.query(Product).filter(Product.model == record_id).delete(synchronize_session=False)

            elif object_type == "MessageTemplate":
                db.query(MessageSend).filter(MessageSend.template == record_id).delete(synchronize_session=False)

            # 2. Delete the record itself
            db.delete(record)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to permanently delete {object_type} {record_id}: {str(e)}")
            raise e

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
