from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import MessageSend, Contact, MessageTemplate
from web.backend.app.utils.sf_id import get_id
import random

def seed_messages():
    db = SessionLocal()
    try:
        contacts = db.query(Contact).limit(5).all()
        templates = db.query(MessageTemplate).limit(2).all()
        
        if not contacts:
            print("No contacts found to link messages to.")
            return

        for i in range(10):
            contact = random.choice(contacts)
            template = random.choice(templates) if templates else None
            
            msg = MessageSend(
                id=get_id("MessageSend"),
                contact=contact.id,
                template=template.id if template else None,
                direction="Outbound",
                content=f"Test message {i+1} content for {contact.first_name}",
                status="Sent"
            )
            db.add(msg)
        
        db.commit()
        print("Successfully seeded 10 MessageSend records.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding messages: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_messages()
