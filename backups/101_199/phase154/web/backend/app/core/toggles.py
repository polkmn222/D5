import os

# Feature Toggles
# To disable a feature and show "Coming Soon", set to False
FEATURE_TOGGLES = {
    "products": True,
    "assets": True,
    "messaging": True
}

def is_feature_enabled(feature_name: str) -> bool:
    return FEATURE_TOGGLES.get(feature_name, True)
