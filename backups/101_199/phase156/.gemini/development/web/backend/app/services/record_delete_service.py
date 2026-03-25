from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from db.models import Attachment, Asset, Contact, Lead, MessageSend, MessageTemplate, Model, Opportunity, Product, VehicleSpecification
from web.backend.app.services.public_image_storage_service import PublicImageStorageService


logger = logging.getLogger(__name__)


class RecordDeleteService:
    @staticmethod
    def _delete_messages(db: Session, **filters) -> None:
        db.query(MessageSend).filter_by(**filters).delete(synchronize_session=False)

    @staticmethod
    def _delete_opportunities(db: Session, **filters) -> None:
        rows = db.query(Opportunity.id).filter_by(**filters).all()
        row_ids = [row.id for row in rows]
        if not row_ids:
            return
        db.query(Lead).filter(Lead.converted_opportunity.in_(row_ids)).update({Lead.converted_opportunity: None}, synchronize_session=False)
        db.query(Opportunity).filter(Opportunity.id.in_(row_ids)).delete(synchronize_session=False)

    @staticmethod
    def _delete_assets(db: Session, **filters) -> None:
        rows = db.query(Asset.id).filter_by(**filters).all()
        row_ids = [row.id for row in rows]
        if not row_ids:
            return
        db.query(Opportunity).filter(Opportunity.asset.in_(row_ids)).delete(synchronize_session=False)
        db.query(Asset).filter(Asset.id.in_(row_ids)).delete(synchronize_session=False)

    @staticmethod
    def _delete_leads(db: Session, **filters) -> None:
        rows = db.query(Lead.id).filter_by(**filters).all()
        row_ids = [row.id for row in rows]
        if not row_ids:
            return
        db.query(Opportunity).filter(Opportunity.lead.in_(row_ids)).delete(synchronize_session=False)
        db.query(Lead).filter(Lead.id.in_(row_ids)).delete(synchronize_session=False)

    @staticmethod
    def _delete_products(db: Session, **filters) -> None:
        rows = db.query(Product.id).filter_by(**filters).all()
        row_ids = [row.id for row in rows]
        if not row_ids:
            return
        db.query(Opportunity).filter(Opportunity.product.in_(row_ids)).delete(synchronize_session=False)
        asset_ids = [row.id for row in db.query(Asset.id).filter(Asset.product.in_(row_ids)).all()]
        if asset_ids:
            db.query(Opportunity).filter(Opportunity.asset.in_(asset_ids)).delete(synchronize_session=False)
            db.query(Asset).filter(Asset.id.in_(asset_ids)).delete(synchronize_session=False)
        db.query(Lead).filter(Lead.product.in_(row_ids)).delete(synchronize_session=False)
        db.query(Product).filter(Product.id.in_(row_ids)).delete(synchronize_session=False)

    @staticmethod
    def _delete_models(db: Session, **filters) -> None:
        rows = db.query(Model.id).filter_by(**filters).all()
        row_ids = [row.id for row in rows]
        if not row_ids:
            return
        db.query(Opportunity).filter(Opportunity.model.in_(row_ids)).delete(synchronize_session=False)
        asset_ids = [row.id for row in db.query(Asset.id).filter(Asset.model.in_(row_ids)).all()]
        if asset_ids:
            db.query(Opportunity).filter(Opportunity.asset.in_(asset_ids)).delete(synchronize_session=False)
            db.query(Asset).filter(Asset.id.in_(asset_ids)).delete(synchronize_session=False)
        db.query(Lead).filter(Lead.model.in_(row_ids)).delete(synchronize_session=False)
        db.query(Product).filter(Product.model.in_(row_ids)).delete(synchronize_session=False)
        db.query(Model).filter(Model.id.in_(row_ids)).delete(synchronize_session=False)

    @staticmethod
    def _delete_template_attachments(db: Session, template: MessageTemplate) -> None:
        attachment_ids = set()
        if getattr(template, "attachment_id", None):
            attachment_ids.add(template.attachment_id)
        attachment_ids.update(
            attachment.id
            for attachment in db.query(Attachment).filter(Attachment.parent_id == template.id).all()
        )
        for attachment_id in attachment_ids:
            attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
            if not attachment:
                continue
            PublicImageStorageService.delete_image(
                file_path=getattr(attachment, "file_path", None),
                provider_key=getattr(attachment, "provider_key", None),
            )
            db.delete(attachment)
        if getattr(template, "image_url", None) and not attachment_ids:
            PublicImageStorageService.delete_image(getattr(template, "image_url", None))

    @classmethod
    def delete_contact(cls, db: Session, contact_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(Contact).filter(Contact.id == contact_id).first()
            if not record:
                return False
            cls._delete_messages(db, contact=contact_id)
            cls._delete_opportunities(db, contact=contact_id)
            cls._delete_assets(db, contact=contact_id)
            db.query(Lead).filter(Lead.converted_contact == contact_id).update({Lead.converted_contact: None}, synchronize_session=False)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting contact %s", contact_id)
            raise

    @classmethod
    def delete_lead(cls, db: Session, lead_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(Lead).filter(Lead.id == lead_id).first()
            if not record:
                return False
            cls._delete_opportunities(db, lead=lead_id)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting lead %s", lead_id)
            raise

    @classmethod
    def delete_opportunity(cls, db: Session, opp_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
            if not record:
                return False
            db.query(Lead).filter(Lead.converted_opportunity == opp_id).update({Lead.converted_opportunity: None}, synchronize_session=False)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting opportunity %s", opp_id)
            raise

    @classmethod
    def delete_asset(cls, db: Session, asset_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(Asset).filter(Asset.id == asset_id).first()
            if not record:
                return False
            cls._delete_opportunities(db, asset=asset_id)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting asset %s", asset_id)
            raise

    @classmethod
    def delete_product(cls, db: Session, product_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(Product).filter(Product.id == product_id).first()
            if not record:
                return False
            cls._delete_opportunities(db, product=product_id)
            cls._delete_assets(db, product=product_id)
            cls._delete_leads(db, product=product_id)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting product %s", product_id)
            raise

    @classmethod
    def delete_model(cls, db: Session, model_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(Model).filter(Model.id == model_id).first()
            if not record:
                return False
            cls._delete_opportunities(db, model=model_id)
            cls._delete_assets(db, model=model_id)
            cls._delete_leads(db, model=model_id)
            cls._delete_products(db, model=model_id)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting model %s", model_id)
            raise

    @classmethod
    def delete_vehicle_spec(cls, db: Session, spec_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
            if not record:
                return False
            cls._delete_opportunities(db, brand=spec_id)
            cls._delete_assets(db, brand=spec_id)
            cls._delete_leads(db, brand=spec_id)
            cls._delete_products(db, brand=spec_id)
            cls._delete_models(db, brand=spec_id)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting vehicle specification %s", spec_id)
            raise

    @classmethod
    def delete_message(cls, db: Session, message_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(MessageSend).filter(MessageSend.id == message_id).first()
            if not record:
                return False
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting message %s", message_id)
            raise

    @classmethod
    def delete_message_template(cls, db: Session, template_id: str, commit: bool = True) -> bool:
        try:
            record = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
            if not record:
                return False
            cls._delete_messages(db, template=template_id)
            cls._delete_template_attachments(db, record)
            db.delete(record)
            if commit:
                db.commit()
            return True
        except Exception:
            if commit:
                db.rollback()
            logger.exception("Error hard deleting message template %s", template_id)
            raise
