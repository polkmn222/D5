import json
import httpx
import logging
from ai_agent.backend.ai_service import AIService, GROQ_API_KEY
from sqlalchemy.orm import Session

class SeedService:
    @staticmethod
    async def generate_theme_data(db: Session, theme: str, count: int = 5):
        """
        Generates realistic Automotive CRM data (Leads, Products, Accounts) using AI.
        """
        prompt = f"""
        Generate {count} realistic CRM entries for an Automotive business themed around '{theme}'.
        
        CRITICAL: Do NOT use real world car brands (No Hyundai, Tesla, etc.). 
        Use fictional high-end sounding brands like "Solaris", "Zenith", "Aeri", "Nebula".
        
        Generate:
        1. "leads": list of (first_name, last_name, company, email, phone, status: 'Open', 'Working', 'Nurturing')
        2. "products": list of (name: Car Model like 'Zenith S1', brand, category: 'EV', 'SUV', 'Sedan', base_price: integer, status: 'Active')
        3. "contacts": list of (name, industry: 'Automotive', tier: 'Bronze', 'Silver', 'Gold', status: 'Active')
        
        Return ONLY valid JSON with keys "leads", "products", "contacts".
        """
        
        api_key = GROQ_API_KEY
        base_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    base_url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    raw_json = response.json()["choices"][0]["message"]["content"]
                    data = json.loads(raw_json)
                    
                    # 1. Seed Products
                    from .product_service import ProductService
                    for p in data.get("products", []):
                        ProductService.create_product(db, **p)
                        
                    # 2. Seed Leads
                    from .lead_service import LeadService
                    for l in data.get("leads", []):
                        LeadService.create_lead(db, **l)
                        
                    # 3. Seed Contacts (Entity/Corporate)
                    from .contact_service import ContactService
                    for c in data.get("contacts", []):
                        ContactService.create_contact(db, **c)
                        
                    return True
            except Exception as e:
                logging.error(f"Seeding failed: {e}")
                return False
        return False

# END FILE
