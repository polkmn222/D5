import random
import string

def generate_sf_id(prefix: str) -> str:
    """
    Generates a Salesforce-like 18-character ID.
    Prefix should be 3 characters.
    """
    # 1. 15-character base (Prefix + 12 random chars)
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=15 - len(prefix)))
    base_15 = prefix + random_part
    
    # 2. 3-character checksum
    # Divide into 3 chunks of 5
    chunks = [base_15[0:5], base_15[5:10], base_15[10:15]]
    lookup = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
    
    checksum = ""
    for chunk in chunks:
        val = 0
        for i, char in enumerate(chunk):
            if char in string.ascii_uppercase:
                val += (1 << i)
        checksum += lookup[val]
        
    return base_15 + checksum

# Object Prefixes
PREFIXES = {
    "Contact": "003",
    "Opportunity": "006",
    "Lead": "00Q",
    "Product": "01t",
    "Asset": "02i",

    "Message": "00P",
    "MessageTemplate": "00X",
    "VehicleSpecification": "avS",
    "Model": "MOD",
    "Attachment": "068"
}

def get_id(object_type: str) -> str:
    prefix = PREFIXES.get(object_type, "000")
    return generate_sf_id(prefix)

# END FILE
