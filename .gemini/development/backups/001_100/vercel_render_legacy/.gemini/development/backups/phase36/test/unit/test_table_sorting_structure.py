import os

def test_template_sorting_hooks():
    templates_to_check = [
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/frontend/templates/dashboard/dashboard.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/frontend/templates/dashboard/dashboard_ai_recommend_fragment.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/frontend/templates/send_message.html"
    ]
    
    missing_hooks = []
    
    for template_path in templates_to_check:
        if not os.path.exists(template_path):
            print(f"[SKIP] {template_path} not found.")
            continue
            
        with open(template_path, 'r') as f:
            content = f.read()
            if "onclick=\"sortTable" not in content:
                missing_hooks.append(template_path)
    
    assert not missing_hooks, f"Templates missing sortTable hooks: {missing_hooks}"
    print("\n[TEST SUCCESS] All targeted templates contain sortTable hooks.")

if __name__ == "__main__":
    try:
        test_template_sorting_hooks()
    except AssertionError as e:
        print(f"[TEST FAILED] {e}")
        exit(1)
