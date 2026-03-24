# Entity Relationship Diagram (ERD)

The database schema for the **AI Ready CRM (D4)** follows a relational model optimized for the automotive industry.

## Mermaid ERD

```mermaid
erDiagram
    CONTACT ||--o{ LEAD : "converts_from"
    CONTACT ||--o{ OPPORTUNITY : "owns"
    CONTACT ||--o{ ASSET : "owns"
    CONTACT ||--o{ MESSAGE : "receives/sends"
    
    LEAD ||--o{ OPPORTUNITY : "converts_to"
    LEAD }o--|| PRODUCT : "interested_in"
    LEAD }o--|| VEHICLE_SPECIFICATION : "interested_brand"
    LEAD }o--|| MODEL : "interested_model"
    
    OPPORTUNITY }o--|| CONTACT : "linked_to"
    OPPORTUNITY }o--|| PRODUCT : "proposed_product"
    OPPORTUNITY }o--|| ASSET : "trade_in/related"
    OPPORTUNITY }o--|| VEHICLE_SPECIFICATION : "related_brand"
    OPPORTUNITY }o--|| MODEL : "related_model"
    
    ASSET }o--|| CONTACT : "owned_by"
    ASSET }o--|| PRODUCT : "is_product"
    ASSET }o--|| VEHICLE_SPECIFICATION : "brand"
    ASSET }o--|| MODEL : "model"
    
    PRODUCT }o--|| VEHICLE_SPECIFICATION : "brand"
    PRODUCT }o--|| MODEL : "model"
    
    VEHICLE_SPECIFICATION ||--o{ VEHICLE_SPECIFICATION : "parent (Brand -> Model)"
    MODEL }o--|| VEHICLE_SPECIFICATION : "brand"
    
    MESSAGE }o--|| CONTACT : "sent_to"
    MESSAGE }o--|| MESSAGE_TEMPLATE : "uses"

    CONTACT {
        string id PK
        string first_name
        string last_name
        string email
        string phone
        string tier
        text ai_summary
    }

    LEAD {
        string id PK
        string status
        boolean is_converted
        string converted_contact_id FK
    }

    OPPORTUNITY {
        string id PK
        string stage
        string status
        integer amount
        string contact_id FK
        string product_id FK
    }

    ASSET {
        string id PK
        string vin
        string status
        string contact_id FK
        string product_id FK
    }

    PRODUCT {
        string id PK
        string name
        integer base_price
        string brand_id FK
    }

    VEHICLE_SPECIFICATION {
        string id PK
        string name
        string record_type
        string parent_id FK
    }

    MESSAGE {
        string id PK
        string direction
        string content
        string status
        string contact_id FK
        string template_id FK
    }
```

## Core Entities

### Contact
The central entity representing an individual or business. Per the recent refactor, it consolidates Account data and serves as the primary lookup for most other objects.

### Lead
Represents a potential customer before qualification. Can be converted into a Contact and an Opportunity.

### Opportunity
A sales deal in progress. Tracks the stage, amount, and related products/contacts.

### Asset
A specific vehicle owned by a contact (identified by VIN). Closely mapped to Products and Brands.

### Product & Vehicle Specification
- **Vehicle Specification**: Hierarchical data for Brands and Models.
- **Product**: Abstract catalog items (e.g., "BMW 3 Series 2024") that can be linked to Assets and Opportunities.

### Messaging
- **Message**: Log of SMS/LMS communication.
- **Message Template**: Reusable content for automated or manual messaging.
