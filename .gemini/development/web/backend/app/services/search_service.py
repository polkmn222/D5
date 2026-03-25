from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from db.models import Lead, Contact, Opportunity, VehicleSpecification, Model, Product, MessageTemplate
from web.backend.app.utils.error_handler import handle_agent_errors

class SearchService:
    @classmethod
    @handle_agent_errors
    def global_search(cls, db: Session, query: str, scope: str = "all", limit: int = 5, offset: int = 0) -> Dict[str, Any]:
        if not query:
            return {"results": [], "counts": {}}
            
        results = []
        counts = {}
        q_pattern = f"%{query}%"

        # Define all search modules and their data fetching logic
        def get_leads(l_limit, l_offset=0):
            return db.query(Lead).filter(
                or_(Lead.first_name.ilike(q_pattern), Lead.last_name.ilike(q_pattern), Lead.phone.ilike(q_pattern)),
                Lead.deleted_at == None
            ).offset(l_offset).limit(l_limit).all()

        def get_contacts(c_limit, c_offset=0):
            return db.query(Contact).filter(
                or_(Contact.first_name.ilike(q_pattern), Contact.last_name.ilike(q_pattern), Contact.name.ilike(q_pattern), Contact.phone.ilike(q_pattern)),
                Contact.deleted_at == None
            ).offset(c_offset).limit(c_limit).all()

        def get_opps(o_limit, o_offset=0):
            return db.query(Opportunity).filter(Opportunity.name.ilike(q_pattern), Opportunity.deleted_at == None).offset(o_offset).limit(o_limit).all()

        def get_models(m_limit, m_offset=0):
            return db.query(Model).filter(Model.name.ilike(q_pattern), Model.deleted_at == None).offset(m_offset).limit(m_limit).all()

        def get_brands(b_limit, b_offset=0):
            return db.query(VehicleSpecification).filter(VehicleSpecification.name.ilike(q_pattern), VehicleSpecification.deleted_at == None).offset(b_offset).limit(b_limit).all()

        def get_products(p_limit, p_offset=0):
            return db.query(Product).filter(Product.name.ilike(q_pattern), Product.deleted_at == None).offset(p_offset).limit(p_limit).all()

        def get_templates(t_limit, t_offset=0):
            return db.query(MessageTemplate).filter(or_(MessageTemplate.name.ilike(q_pattern), MessageTemplate.subject.ilike(q_pattern)), MessageTemplate.deleted_at == None).offset(t_offset).limit(t_limit).all()

        # Get Counts for Sidebar (Always needed)
        counts["Lead"] = db.query(Lead).filter(or_(Lead.first_name.ilike(q_pattern), Lead.last_name.ilike(q_pattern), Lead.phone.ilike(q_pattern)), Lead.deleted_at == None).count()
        counts["Contact"] = db.query(Contact).filter(or_(Contact.first_name.ilike(q_pattern), Contact.last_name.ilike(q_pattern), Contact.name.ilike(q_pattern), Contact.phone.ilike(q_pattern)), Contact.deleted_at == None).count()
        counts["Opportunity"] = db.query(Opportunity).filter(Opportunity.name.ilike(q_pattern), Opportunity.deleted_at == None).count()
        counts["Model"] = db.query(Model).filter(Model.name.ilike(q_pattern), Model.deleted_at == None).count()
        counts["Brand"] = db.query(VehicleSpecification).filter(VehicleSpecification.name.ilike(q_pattern), VehicleSpecification.deleted_at == None).count()
        counts["Product"] = db.query(Product).filter(Product.name.ilike(q_pattern), Product.deleted_at == None).count()
        counts["Template"] = db.query(MessageTemplate).filter(or_(MessageTemplate.name.ilike(q_pattern), MessageTemplate.subject.ilike(q_pattern)), MessageTemplate.deleted_at == None).count()

        # Decide effective limit
        eff_limit = limit if scope == "all" else 50
        
        # 1. Search Leads
        if scope in ["all", "lead"]:
            leads = get_leads(eff_limit, offset if scope == "lead" else 0)
            for l in leads:
                name = f"{l.first_name if l.first_name else ''} {l.last_name if l.last_name else ''}".strip() or "Unnamed Lead"
                results.append({
                    "type": "Lead", 
                    "plural_type": "leads",
                    "name": name, 
                    "id": l.id, 
                    "url": f"/leads/{l.id}", 
                    "edit_url": f"/leads/new-modal?id={l.id}",
                    "email": l.email,
                    "phone": l.phone,
                    "status": l.status,
                    "created_at": l.created_at.strftime("%Y-%m-%d") if l.created_at else None
                })
                
        # 2. Search Contacts
        if scope in ["all", "contact"]:
            contacts = get_contacts(eff_limit, offset if scope == "contact" else 0)
            for c in contacts:
                name = c.name if c.name else f"{c.first_name if c.first_name else ''} {c.last_name if c.last_name else ''}".strip() or "Unnamed Contact"
                results.append({
                    "type": "Contact", 
                    "plural_type": "contacts",
                    "name": name, 
                    "id": c.id, 
                    "url": f"/contacts/{c.id}", 
                    "edit_url": f"/contacts/new-modal?id={c.id}",
                    "email": c.email,
                    "phone": c.phone,
                    "status": c.status,
                    "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else None
                })
                
        # 3. Search Opportunities
        if scope in ["all", "opportunity"]:
            opps = get_opps(eff_limit, offset if scope == "opportunity" else 0)
            for o in opps:
                results.append({
                    "type": "Opportunity", 
                    "plural_type": "opportunities",
                    "name": o.name or "Unnamed Opportunity", 
                    "id": o.id, 
                    "url": f"/opportunities/{o.id}", 
                    "edit_url": f"/opportunities/new-modal?id={o.id}",
                    "amount": f"{o.amount:,}" if o.amount else "0",
                    "stage": o.stage,
                    "close_date": o.close_date.strftime("%Y-%m-%d") if o.close_date else None
                })
                
        # 4. Search Models
        if scope in ["all", "model"]:
            models = get_models(eff_limit, offset if scope == "model" else 0)
            for m in models:
                results.append({
                    "type": "Model", 
                    "plural_type": "models",
                    "name": m.name or "Unnamed Model", 
                    "id": m.id, 
                    "url": f"/models/{m.id}", 
                    "edit_url": f"/models/new-modal?id={m.id}",
                    "description": m.description[:100] if m.description else "No description"
                })
                
        # 5. Search Brands (Specifications)
        if scope in ["all", "brand"]:
            brands = get_brands(eff_limit, offset if scope == "brand" else 0)
            for b in brands:
                results.append({
                    "type": "Brand", 
                    "plural_type": "vehicle_specifications",
                    "name": b.name or "Unnamed Brand", 
                    "id": b.id, 
                    "url": f"/vehicle_specifications/{b.id}", 
                    "edit_url": f"/vehicle_specifications/new-modal?id={b.id}",
                    "record_type": b.record_type,
                    "description": b.description[:100] if b.description else "No description"
                })

        # 6. Search Products
        if scope in ["all", "product"]:
            prods = get_products(eff_limit, offset if scope == "product" else 0)
            for p in prods:
                results.append({
                    "type": "Product", 
                    "plural_type": "products",
                    "name": p.name or "Unnamed Product", 
                    "id": p.id, 
                    "url": f"/products/{p.id}", 
                    "edit_url": f"/products/new-modal?id={p.id}",
                    "info": f"Price: {p.base_price}"
                })

        # 7. Search Templates
        if scope in ["all", "template"]:
            tmpls = get_templates(eff_limit, offset if scope == "template" else 0)
            for t in tmpls:
                results.append({
                    "type": "Template", 
                    "plural_type": "message_templates",
                    "name": t.name or "Unnamed Template", 
                    "id": t.id, 
                    "url": f"/message_templates/{t.id}", 
                    "edit_url": f"/message_templates/new-modal?id={t.id}",
                    "info": t.subject
                })
                
        return {"results": results, "counts": counts}
