import re

with open('app/api/web_router.py', 'r') as f:
    content = f.read()

# Patches for creation (where url="...")
content = re.sub(
    r'(def create_[^(\n]+(?:\(.*?\))?.*?:.*?)(return RedirectResponse\(url=("[^"]+"), status_code=303\))',
    r'\1return RedirectResponse(url=\3 + "?success=Record+created+successfully", status_code=303)',
    content,
    flags=re.DOTALL
)

# Patches for update (where url=f"...")
content = re.sub(
    r'(def update_[^(\n]+(?:\(.*?\))?.*?:.*?)(return RedirectResponse\(url=(f"[^"]+"), status_code=303\))',
    r'\1return RedirectResponse(url=\3 + "?success=Record+updated+successfully", status_code=303)',
    content,
    flags=re.DOTALL
)

with open('app/api/web_router.py', 'w') as f:
    f.write(content)

print("Patch applied.")
