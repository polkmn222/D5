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
            ChecklistItem("Dashboard load", "Open the root dashboard page after startup.", "The dashboard renders without a server error.", area="Dashboard", severity="high"),
            ChecklistItem("Navigation entrypoints", "Open Contacts, Leads, Opportunities, and one catalog object from main navigation.", "Key object pages open successfully.", area="Navigation", severity="high"),
            ChecklistItem("Global search", "Run one representative global search from the main UI.", "Relevant results appear without broken rendering.", area="Search", severity="medium"),
            ChecklistItem("Lookup search", "Open one lookup-enabled form and search for an existing related record.", "Lookup results appear and selection works.", area="Search", severity="medium"),
            ChecklistItem("Contact create", "Create one contact with representative required fields.", "The contact saves and opens in list/detail views.", area="Contacts", severity="high"),
            ChecklistItem("Lead update", "Open one lead and update a key field such as status.", "The updated lead value persists correctly.", area="Leads", severity="high"),
            ChecklistItem("Opportunity delete or soft delete", "Delete or soft-delete one opportunity or other safe test record.", "The record is removed or marked deleted as expected.", area="Opportunities", severity="high"),
            ChecklistItem("Detail tabs and actions", "Open a detail page and switch tabs or key action buttons.", "Tabs and shared actions render and behave correctly.", area="Shared UI", severity="medium"),
        ],
        default_report_name="smoke_checklist",
    )


if __name__ == "__main__":
    main()
