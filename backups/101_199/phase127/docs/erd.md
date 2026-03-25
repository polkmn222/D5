# Entity Relationship Diagram

This ERD reflects the active ORM models defined in `db/models.py`.

## Mermaid ERD

```mermaid
erDiagram
    CONTACT ||--o{ LEAD : converts
    CONTACT ||--o{ OPPORTUNITY : owns
    CONTACT ||--o{ ASSET : owns
    CONTACT ||--o{ MESSAGE_SEND : receives

    LEAD ||--o| OPPORTUNITY : converts_to
    LEAD }o--|| CONTACT : converted_contact
    LEAD }o--|| VEHICLE_SPECIFICATION : brand
    LEAD }o--|| MODEL : model
    LEAD }o--|| PRODUCT : product

    OPPORTUNITY }o--|| CONTACT : contact
    OPPORTUNITY }o--|| LEAD : lead
    OPPORTUNITY }o--|| PRODUCT : product
    OPPORTUNITY }o--|| VEHICLE_SPECIFICATION : brand
    OPPORTUNITY }o--|| MODEL : model
    OPPORTUNITY }o--|| ASSET : asset

    ASSET }o--|| CONTACT : contact
    ASSET }o--|| PRODUCT : product
    ASSET }o--|| VEHICLE_SPECIFICATION : brand
    ASSET }o--|| MODEL : model

    PRODUCT }o--|| VEHICLE_SPECIFICATION : brand
    PRODUCT }o--|| MODEL : model

    MODEL }o--|| VEHICLE_SPECIFICATION : brand
    VEHICLE_SPECIFICATION ||--o{ VEHICLE_SPECIFICATION : parent

    MESSAGE_SEND }o--|| CONTACT : contact
    MESSAGE_SEND }o--|| MESSAGE_TEMPLATE : template
    MESSAGE_TEMPLATE }o--|| ATTACHMENT : attachment

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
        string converted_contact FK
        string converted_opportunity FK
        string brand FK
        string model FK
        string product FK
    }

    OPPORTUNITY {
        string id PK
        string contact FK
        string lead FK
        string product FK
        string asset FK
        string stage
        string status
        integer amount
    }

    ASSET {
        string id PK
        string contact FK
        string product FK
        string brand FK
        string model FK
        string vin
        string status
    }

    PRODUCT {
        string id PK
        string name
        string brand FK
        string model FK
        integer base_price
    }

    VEHICLE_SPECIFICATION {
        string id PK
        string name
        string record_type
        string parent FK
    }

    MODEL {
        string id PK
        string name
        string brand FK
    }

    MESSAGE_SEND {
        string id PK
        string contact FK
        string template FK
        string direction
        string status
        datetime sent_at
    }

    MESSAGE_TEMPLATE {
        string id PK
        string name
        string record_type
        string attachment_id FK
    }

    ATTACHMENT {
        string id PK
        string name
        string file_path
        string provider_key
    }
```

## Notes

- `BaseModel` supplies `created_at`, `updated_at`, and `deleted_at` to most primary entities.
- `ServiceToken` exists for external service credentials and is intentionally omitted from the main ERD because it is operational rather than CRM-domain data.
