from pathlib import Path


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")

def test_template_sorting_hooks():
    templates_to_check = [
        APP_ROOT / "web" / "frontend" / "templates" / "dashboard" / "dashboard.html",
        APP_ROOT / "web" / "frontend" / "templates" / "dashboard" / "dashboard_ai_recommend_fragment.html",
        APP_ROOT / "web" / "frontend" / "templates" / "send_message.html",
    ]
    
    missing_hooks = []
    
    for template_path in templates_to_check:
        if not template_path.exists():
            print(f"[SKIP] {template_path} not found.")
            continue

        with template_path.open("r") as handle:
            content = handle.read()
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
