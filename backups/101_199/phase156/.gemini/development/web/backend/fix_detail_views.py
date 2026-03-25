import os
import re

files = [
    'app/templates/assets/detail_view.html',
    'app/templates/vehicle_spec/detail_view.html',
    'app/templates/lead/detail_view.html',
    'app/templates/common/detail_view.html',
    'app/templates/product/detail_view.html',
    'app/templates/message/detail_view.html',
    'app/templates/asset/detail_view.html',
    'app/templates/contact/detail_view.html',
    'app/templates/opportunity/detail_view.html'
]

def standardize_template(content):
    # 1. Handle lookup fields with a more robust regex
    # Capture the whole if/elif block for a lookup
    lookup_pattern = re.compile(
        r"({% (?:if|elif) field == '([^']+)' %})\s*"
        r"(<div id=\"value-{{ field }}\" class=\"sf-editable-field\"[^>]*>)\s*"
        r"(.*?)\s*"
        r"(<span class=\"sf-pencil-icon\" onclick=\"toggleLookupEdit\((.*?)\)\"[^>]*>✏️</span>)\s*"
        r"(</div>)",
        re.DOTALL
    )

    def lookup_repl(match):
        cond_start = match.group(1)
        field_name = match.group(2)
        div_start = match.group(3)
        content_inside = match.group(4).strip()
        pencil_span = match.group(5)
        args_str = match.group(6)
        div_end = match.group(7)

        # Parse args_str. It's comma separated, but some args might contain commas if they are jinja expressions.
        # Actually, in these templates they are usually 'arg1', 'arg2', 'arg3', 'arg4', 'arg5'
        # Let's try to split by ', ' if it's outside of quotes? Hard.
        # But wait, we can just keep the args as they are and just change the first one if needed.
        
        # Standardize div_start
        new_div_start = f'<div id="value-{{{{ field }}}}" class="sf-editable-field" onclick="toggleInlineEdit(\'{{{{ field }}}}\', \'{{{{ plural_type }}}}\', \'{{{{ record_id }}}}\', \'{{{{ field }}}}\')" style="width: 100%;">'
        
        # Handle args
        # Example args_str: 'Account_Hidden_Ref', 'Account', 'Account', '{{ ... }}', '{{ ... }}'
        # We want to change the first arg to '{{ field }}'
        args = re.findall(r"'(.*?)'(?:\s*,\s*|$)|({{.*?}})(?:\s*,\s*|$)", args_str)
        # That's also hard. 
        # Let's just use a simpler approach for args: replace the first quoted string.
        new_args_str = re.sub(r"^'[^']+'", f"'{{{{ field }}}}'", args_str)
        
        # Standardize pencil_span
        new_pencil_span = f'<span class="sf-pencil-icon" onclick="toggleLookupEdit({new_args_str}); event.stopPropagation();" style="margin-left: auto; padding-left: 1rem;">✏️</span>'
        
        # Extract hidden_ref from original args_str for data-label
        hidden_ref_match = re.search(r"^'([^']+)'", args_str)
        hidden_ref = hidden_ref_match.group(1) if hidden_ref_match else field_name

        # Wrap content in text-{{field}} if not already
        if f'id="text-{field_name}"' not in content_inside and 'id="text-{{ field }}"' not in content_inside:
            content_inside = f'<span id="text-{{{{ field }}}}">{content_inside}</span>'

        new_block = f"{cond_start}\n                {new_div_start}\n                    {content_inside}\n                    {new_pencil_span}\n                {div_end}\n                <div id=\"edit-{{{{ field }}}}\" style=\"display: none;\" data-label=\"{hidden_ref}\"></div>"
        return new_block

    content = lookup_pattern.sub(lookup_repl, content)

    # 2. Handle Temperature field
    temp_pattern = re.compile(
        r"({% (?:if|elif) field == 'Temperature' %})\s*"
        r"(<div id=\"value-{{ field }}\" class=\"sf-editable-field\"[^>]*>)\s*"
        r"(<span id=\"text-{{ field }}\">.*?</span>)\s*"
        r"(<span class=\"sf-pencil-icon\" onclick=\"toggleInlineEdit\('{{ field }}', '{{ plural_type }}', '{{ record_id }}', 'Temperature'\)\"[^>]*>✏️</span>)\s*"
        r"(</div>)",
        re.DOTALL
    )
    
    def temp_repl(match):
        cond_start = match.group(1)
        text_span = match.group(3)
        div_end = match.group(5)
        new_div_start = '<div id="value-{{ field }}" class="sf-editable-field" onclick="toggleInlineEdit(\'{{ field }}\', \'{{ plural_type }}\', \'{{ record_id }}\', \'{{ field }}\')" style="width: 100%;">'
        new_pencil_span = '<span class="sf-pencil-icon" style="margin-left: auto; padding-left: 1rem;">✏️</span>'
        return f"{cond_start}\n                {new_div_start}\n                    {text_span}\n                    {new_pencil_span}\n                {div_end}"

    content = temp_pattern.sub(temp_repl, content)

    # 3. Handle normal fields (Display Mode)
    display_pattern = re.compile(
        r"(<div id=\"value-{{ field }}\" class=\"sf-editable-field\" onclick=\"toggleInlineEdit\('{{ field }}', '{{ plural_type }}', '{{ record_id }}', '{{ field }}'\)\")([^>]*)>",
        re.DOTALL
    )
    content = display_pattern.sub(r'\1 style="width: 100%;">', content)

    # 4. Handle normal fields (Edit Mode)
    # Add data-label if missing
    edit_pattern = re.compile(
        r"<div id=\"edit-{{ field }}\" style=\"display: none;\"(?! data-label)>",
        re.DOTALL
    )
    content = edit_pattern.sub(r'<div id="edit-{{ field }}" style="display: none;" data-label="{{ field }}">', content)
    
    # 5. Handle Description
    desc_val_pattern = re.compile(
        r"(<div id=\"value-description\" class=\"sf-editable-field\" onclick=\"toggleInlineEdit\('description', '{{ plural_type }}', '{{ record_id }}', 'Description'\)\")([^>]*)>",
        re.DOTALL
    )
    content = desc_val_pattern.sub(r'\1 style="width: 100%;">', content)
    
    desc_edit_pattern = re.compile(
        r"<div id=\"edit-description\" style=\"display: none;\"(?! data-label)>",
        re.DOTALL
    )
    content = desc_edit_pattern.sub(r'<div id="edit-description" style="display: none;" data-label="Description">', content)

    # 6. Remove sf-inline-actions blocks
    actions_pattern = re.compile(
        r"<div class=\"sf-inline-actions\">.*?</div>",
        re.DOTALL
    )
    content = actions_pattern.sub("", content)
    
    return content

for file_path in files:
    if os.path.exists(file_path):
        print(f"Processing {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()
        
        new_content = standardize_template(content)
        
        with open(file_path, 'w') as f:
            f.write(new_content)
