import csv
import io
from sqlalchemy.orm import Session
from .contact_service import ContactService
from .lead_service import LeadService
from .opportunity_service import OpportunityService

class ImportService:
    @staticmethod
    async def import_csv(db: Session, object_type: str, file_content: str):
        f = io.StringIO(file_content)
        reader = csv.DictReader(f)
        imported_count = 0
        
        for row in reader:
            try:
                if object_type == "Contact":
                    ContactService.create_contact(db, **row)
                elif object_type == "Lead":
                    LeadService.create_lead(db, **row)
                elif object_type == "Opportunity":
                    OpportunityService.create_opportunity(db, **row)
                imported_count += 1
            except Exception as e:
                print(f"Error importing row: {e}")
        
        return imported_count

# END FILE
