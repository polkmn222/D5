from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from db.models import Lead, Contact, Opportunity, VehicleSpecification, Model, Product, MessageTemplate
from web.backend.app.utils.error_handler import handle_agent_errors

class SearchService:
    @classmethod
    @handle_agent_errors
    def global_search(cls, db: Session, query: str, scope: str = "all", limit: int = 5) -> List[Dict[str, Any]]:
        if not query:
            return []
            
        results = []
        q_pattern = f"%{query}%"
        
        # 1. Search Leads
        if scope in ["all", "lead"]:
            leads = db.query(Lead).filter(
                or_(
                    Lead.first_name.ilike(q_pattern),
                    Lead.last_name.ilike(q_pattern),
                    Lead.email.ilike(q_pattern),
                    Lead.phone.ilike(q_pattern)
                ),
                Lead.deleted_at == None
            ).limit(limit).all()
            for l in leads:
                name = f"{l.first_name} {l.last_name}"
                results.append({"type": "Lead", "name": name, "id": l.id, "url": f"/leads/{l.id}", "info": l.email or l.phone or "No contact info"})
                
        # 2. Search Contacts
        if scope in ["all", "contact"]:
            contacts = db.query(Contact).filter(
                or_(
                    Contact.first_name.ilike(q_pattern),
                    Contact.last_name.ilike(q_pattern),
                    Contact.name.ilike(q_pattern),
                    Contact.email.ilike(q_pattern),
                    Contact.phone.ilike(q_pattern)
                ),
                Contact.deleted_at == None
            ).limit(limit).all()
            for c in contacts:
                name = c.name if c.name else f"{c.first_name} {c.last_name}"
                results.append({"type": "Contact", "name": name, "id": c.id, "url": f"/contacts/{c.id}", "info": c.email or c.phone or "No contact info"})
                
        # 3. Search Opportunities
        if scope in ["all", "opportunity"]:
            opps = db.query(Opportunity).filter(Opportunity.name.ilike(q_pattern), Opportunity.deleted_at == None).limit(limit).all()
            for o in opps:
                results.append({"type": "Opportunity", "name": o.name, "id": o.id, "url": f"/opportunities/{o.id}", "info": f"Stage: {o.stage}"})
                
        # 4. Search Models
        if scope in ["all", "model"]:
            models = db.query(Model).filter(Model.name.ilike(q_pattern), Model.deleted_at == None).limit(limit).all()
            for m in models:
                results.append({"type": "Model", "name": m.name, "id": m.id, "url": f"/models", "info": m.description[:50] if m.description else "No description"})
                
        # 5. Search Brands (Specifications)
        if scope in ["all", "brand"]:
            brands = db.query(VehicleSpecification).filter(VehicleSpecification.name.ilike(q_pattern), VehicleSpecification.deleted_at == None).limit(limit).all()
            for b in brands:
                results.append({"type": "Brand", "name": b.name, "id": b.id, "url": f"/vehicle_specifications", "info": f"Type: {b.record_type}"})

        # 6. Search Products
        if scope in ["all", "product"]:
            prods = db.query(Product).filter(Product.name.ilike(q_pattern), Product.deleted_at == None).limit(limit).all()
            for p in prods:
                results.append({"type": "Product", "name": p.name, "id": p.id, "url": f"/products", "info": f"Price: {p.base_price}"})

        # 7. Search Templates
        if scope in ["all", "template"]:
            tmpls = db.query(MessageTemplate).filter(
                or_(
                    MessageTemplate.name.ilike(q_pattern),
                    MessageTemplate.subject.ilike(q_pattern)
                ),
                MessageTemplate.deleted_at == None
            ).limit(limit).all()
            for t in tmpls:
                results.append({"type": "Template", "name": t.name, "id": t.id, "url": f"/message_templates", "info": t.subject})
                
        return results
