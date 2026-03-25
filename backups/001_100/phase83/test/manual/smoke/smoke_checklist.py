import sys
from importlib import import_module
from pathlib import Path

APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
TEST_ROOT = APP_ROOT / "test"
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

_runner = import_module("manual._checklist_runner")
ChecklistItem = _runner.ChecklistItem
run_checklist = _runner.run_checklist


def main() -> None:
    run_checklist(
        title="D4 Smoke Manual Checklist",
        intro="""
        Environment
        - Confirm TEST_DATABASE_URL points to a dedicated PostgreSQL test database.
        - Optionally set D4_RESET_MANUAL_TEST_DB=1 for a clean reset.
        - Start the app with ./run_crm.sh.

        Reference
        - Canonical checklist: .gemini/development/docs/testing/manual_checklist.md
        """,
        items=[
            ChecklistItem("Dashboard load", "Open `/` after startup and confirm the dashboard page renders.", "The dashboard loads without a server error and the main dashboard UI is visible.", area="Dashboard", severity="high"),
            ChecklistItem("Navigation entrypoints", "Use the main navigation to open `/contacts`, `/leads`, `/opportunities`, and one catalog page such as `/products`.", "Each page loads and the corresponding list or landing view is visible.", area="Navigation", severity="high"),
            ChecklistItem("Global search", "Run one representative global search from the main search surface using an existing record name.", "Relevant search results appear without broken rendering or server errors.", area="Search", severity="medium"),
            ChecklistItem("Lookup search", "Open one lookup-enabled form, use the lookup search control, and select an existing related record.", "Lookup results appear, the record can be selected, and the chosen value stays visible.", area="Search", severity="medium"),
            ChecklistItem("Contact create", "Open `/contacts`, use the visible create/new action, submit a contact with representative fields, and open the saved detail page.", "The contact saves successfully and appears in both list and detail views.", area="Contacts", severity="high"),
            ChecklistItem("Lead update", "Open `/leads`, open one lead detail page, use inline edit or the visible edit action, and update a key field such as status.", "The updated lead value persists after save and refresh.", area="Leads", severity="high"),
            ChecklistItem("Opportunity delete or soft delete", "Open `/opportunities`, pick a safe test record, and use the visible delete or soft-delete action.", "The opportunity is removed from the active list or marked deleted as expected.", area="Opportunities", severity="high"),
            ChecklistItem("Detail tabs and actions", "Open one detail page and verify tabs such as `Details`, `Related`, and `Activity`, plus visible action buttons.", "Tabs switch correctly and visible action buttons remain usable.", area="Shared UI", severity="medium"),
        ],
        default_report_name="smoke_checklist",
    )


if __name__ == "__main__":
    main()
