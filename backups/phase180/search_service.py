from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from db.models import Lead, Contact, Opportunity, VehicleSpecification, Model, Product, MessageTemplate
from web.backend.app.utils.error_handler import handle_agent_errors

class SearchService:
    @classmethod
    @handle_agent_errors
    def global_search(cls, db: Session, query: str, scope: str = "all", limit: int = 5) -> Dict[str, Any]:
        if not query:
            return {"results": [], "counts": {}}
            
        results = []
        counts = {}
        q_pattern = f"%{query}%"

        # Define all search modules and their data fetching logic
        def get_leads(l_limit):
            return db.query(Lead).filter(
                or_(Lead.first_name.ilike(q_pattern), Lead.last_name.ilike(q_pattern), Lead.phone.ilike(q_pattern)),
                Lead.deleted_at == None
            ).limit(l_limit).all()

        def get_contacts(c_limit):
            return db.query(Contact).filter(
                or_(Contact.first_name.ilike(q_pattern), Contact.last_name.ilike(q_pattern), Contact.name.ilike(q_pattern), Contact.phone.ilike(q_pattern)),
                Contact.deleted_at == None
            ).limit(c_limit).all()

        def get_opps(o_limit):
            return db.query(Opportunity).filter(Opportunity.name.ilike(q_pattern), Opportunity.deleted_at == None).limit(o_limit).all()

        def get_models(m_limit):
            return db.query(Model).filter(Model.name.ilike(q_pattern), Model.deleted_at == None).limit(m_limit).all()

        def get_brands(b_limit):
            return db.query(VehicleSpecification).filter(VehicleSpecification.name.ilike(q_pattern), VehicleSpecification.deleted_at == None).limit(b_limit).all()

        def get_products(p_limit):
            return db.query(Product).filter(Product.name.ilike(q_pattern), Product.deleted_at == None).limit(p_limit).all()

        def get_templates(t_limit):
            return db.query(MessageTemplate).filter(or_(MessageTemplate.name.ilike(q_pattern), MessageTemplate.subject.ilike(q_pattern)), MessageTemplate.deleted_at == None).limit(t_limit).all()

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
            leads = get_leads(eff_limit)
            for l in leads:
                name = f"{l.first_name} {l.last_name}"
                results.append({
                    "type": "Lead", 
                    "name": name, 
                    "id": l.id, 
                    "url": f"/leads/{l.id}", 
                    "email": l.email,
                    "phone": l.phone,
                    "status": l.status,
                    "created_at": l.created_at.strftime("%Y-%m-%d") if l.created_at else None
                })
                
        # 2. Search Contacts
        if scope in ["all", "contact"]:
            contacts = get_contacts(eff_limit)
            for c in contacts:
                name = c.name if c.name else f"{c.first_name} {c.last_name}"
                results.append({
                    "type": "Contact", 
                    "name": name, 
                    "id": c.id, 
                    "url": f"/contacts/{c.id}", 
                    "email": c.email,
                    "phone": c.phone,
                    "status": c.status,
                    "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else None
                })
                
        # 3. Search Opportunities
        if scope in ["all", "opportunity"]:
            opps = get_opps(eff_limit)
            for o in opps:
                results.append({
                    "type": "Opportunity", 
                    "name": o.name, 
                    "id": o.id, 
                    "url": f"/opportunities/{o.id}", 
                    "amount": f"{o.amount:,}" if o.amount else "0",
                    "stage": o.stage,
                    "close_date": o.close_date.strftime("%Y-%m-%d") if o.close_date else None
                })
                
        # 4. Search Models
        if scope in ["all", "model"]:
            models = get_models(eff_limit)
            for m in models:
                results.append({
                    "type": "Model", 
                    "name": m.name, 
                    "id": m.id, 
                    "url": f"/models", 
                    "description": m.description[:100] if m.description else "No description"
                })
                
        # 5. Search Brands (Specifications)
        if scope in ["all", "brand"]:
            brands = get_brands(eff_limit)
            for b in brands:
                results.append({
                    "type": "Brand", 
                    "name": b.name, 
                    "id": b.id, 
                    "url": f"/vehicle_specifications", 
                    "record_type": b.record_type,
                    "description": b.description[:100] if b.description else "No description"
                })

        # 6. Search Products
        if scope in ["all", "product"]:
            prods = get_products(eff_limit)
            for p in prods:
                results.append({"type": "Product", "name": p.name, "id": p.id, "url": f"/products", "info": f"Price: {p.base_price}"})

        # 7. Search Templates
        if scope in ["all", "template"]:
            tmpls = get_templates(eff_limit)
            for t in tmpls:
                results.append({"type": "Template", "name": t.name, "id": t.id, "url": f"/message_templates", "info": t.subject})
                
        return {"results": results, "counts": counts}
