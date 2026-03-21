from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.sql import func
from .database import Base
from backend.app.core.enums import RecordType, ContactTier, LeadStatus, OpportunityStage, OpportunityStatus, MessageDirection, MessageStatus
from backend.app.utils.timezone import get_kst_now_naive

class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=get_kst_now_naive)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), default=get_kst_now_naive)
    deleted_at = Column(DateTime, nullable=True)

class VehicleSpecification(BaseModel):
    __tablename__ = "vehicle_specifications"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    record_type = Column(String, default=RecordType.MODEL) # Brand, Model
    parent = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    description = Column(Text, nullable=True)


class Model(BaseModel):
    __tablename__ = "models"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    description = Column(Text, nullable=True)

class Contact(BaseModel):
    __tablename__ = "contacts"

    id = Column(String(18), primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    name = Column(String, nullable=True) # For corporate/entity names if needed
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    lead_source = Column(String, nullable=True)
    status = Column(String, default="New")
    website = Column(String, nullable=True)
    tier = Column(String, default=ContactTier.BRONZE)
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    last_interaction_at = Column(DateTime, nullable=True)

class Lead(BaseModel):
    __tablename__ = "leads"

    id = Column(String(18), primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default=LeadStatus.NEW) # New, Follow Up, Qualified, Lost
    is_converted = Column(Boolean, default=False)
    converted_contact = Column(String(18), ForeignKey("contacts.id"), nullable=True)
    converted_opportunity = Column(String(18), ForeignKey("opportunities.id"), nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    product = Column(String(18), ForeignKey("products.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_followed = Column(Boolean, default=False)

class Product(BaseModel):
    __tablename__ = "products"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    category = Column(String, nullable=True)
    base_price = Column(Integer, default=0)
    description = Column(Text, nullable=True)

class Opportunity(BaseModel):
    __tablename__ = "opportunities"

    id = Column(String(18), primary_key=True, index=True)
    contact = Column(String(18), ForeignKey("contacts.id"), nullable=True)
    product = Column(String(18), ForeignKey("products.id"), nullable=True)
    lead = Column(String(18), ForeignKey("leads.id"), nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    asset = Column(String(18), ForeignKey("assets.id"), nullable=True)
    name = Column(String, nullable=True)
    amount = Column(Integer, default=0)
    stage = Column(String, default=OpportunityStage.PROSPECTING)
    status = Column(String, default=OpportunityStatus.OPEN) # Open, Closed Won, Closed Lost
    probability = Column(Integer, default=10)
    temperature = Column(String, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)
    close_date = Column(DateTime, nullable=True)
    ai_insight = Column(Text, nullable=True)
    is_followed = Column(Boolean, default=False)

class Asset(BaseModel):
    __tablename__ = "assets"

    id = Column(String(18), primary_key=True, index=True)
    contact = Column(String(18), ForeignKey("contacts.id"), nullable=True)
    product = Column(String(18), ForeignKey("products.id"), nullable=True)
    brand = Column(String(18), ForeignKey("vehicle_specifications.id"), nullable=True)
    model = Column(String(18), ForeignKey("models.id"), nullable=True)
    name = Column(String, nullable=True)
    vin = Column(String, nullable=True)
    # Using LeadStatus since AccountStatus might be removed/deprecated
    status = Column(String, default="Active") 
    purchase_date = Column(DateTime, nullable=True)
    price = Column(Integer, default=0)

class MessageSend(BaseModel):
    __tablename__ = "message_sends"

    id = Column(String(18), primary_key=True, index=True)
    contact = Column(String(18), ForeignKey("contacts.id"), nullable=True)
    template = Column(String(18), ForeignKey("message_templates.id"), nullable=True)
    direction = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String, default=MessageStatus.PENDING)
    provider_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(direction.in_([MessageDirection.INBOUND, MessageDirection.OUTBOUND]), name='check_direction'),
    )

class MessageTemplate(BaseModel):
    __tablename__ = "message_templates"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    content = Column(String, nullable=True)
    record_type = Column(String, default="SMS")
    file_path = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    attachment_id = Column(String(18), ForeignKey("attachments.id"), nullable=True)

class Attachment(BaseModel):
    __tablename__ = "attachments"

    id = Column(String(18), primary_key=True, index=True)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    parent_id = Column(String(18), nullable=True) # Optional generic link
    parent_type = Column(String, nullable=True)   # e.g., 'MessageTemplate'
    provider_key = Column(String, nullable=True)   # SUREM imageKey
