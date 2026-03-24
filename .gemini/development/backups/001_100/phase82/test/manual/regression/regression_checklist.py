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
        title="D4 Regression Manual Checklist",
        intro="""
        Scope
        - Use this run for broader CRM and shared UI verification.
        - Add messaging or AI-agent checks only when those domains are in scope.

        Reference
        - Canonical checklist: .gemini/development/docs/testing/manual_checklist.md
        """,
        items=[
            ChecklistItem("Contacts CRUD", "Create, open, edit, verify list/detail consistency, and delete a contact.", "Contact flows complete without data mismatch.", area="Contacts", severity="high"),
            ChecklistItem("Contacts lookup behavior", "Verify at least one contact-related lookup or related list surface.", "Contact lookups and related references render correctly.", area="Contacts", severity="medium"),
            ChecklistItem("Leads CRUD", "Create a lead, update key fields, verify search visibility, and delete or archive the record.", "Lead CRUD behavior matches expectations.", area="Leads", severity="high"),
            ChecklistItem("Lead conversion", "Convert a lead when that flow is in scope and inspect downstream records.", "Lead conversion creates or links downstream records as expected.", area="Leads", severity="high"),
            ChecklistItem("Opportunities CRUD", "Create an opportunity, update amount or stage, and verify list/detail visibility.", "Opportunity updates persist and render correctly.", area="Opportunities", severity="high"),
            ChecklistItem("Assets CRUD", "Create or edit an asset and verify VIN or related fields.", "Asset list/detail behavior and related links remain correct.", area="Assets", severity="medium"),
            ChecklistItem("Products CRUD", "Create or edit a product and verify its related brand/model associations.", "Product data renders and persists correctly.", area="Products", severity="medium"),
            ChecklistItem("Vehicle specs and models", "Create or edit a brand/model pair and verify lookup resolution.", "Vehicle spec and model relationships resolve correctly.", area="Vehicle Specs", severity="medium"),
            ChecklistItem("Tabs and inline edit", "Open detail tabs and test inline edit save/cancel behavior.", "Tabs switch correctly and inline edit behaves consistently.", area="Shared UI", severity="high"),
            ChecklistItem("Batch edit and save", "Use batch-edit capable views and save changes.", "Batch save updates apply correctly without broken state.", area="Shared UI", severity="high"),
            ChecklistItem("Sorting behavior", "Test sortable table headers in representative list or dashboard tables.", "Sort hooks and ordering behave as expected.", area="Shared UI", severity="medium"),
            ChecklistItem("Bulk action visibility", "Check list pages with selectable rows and confirm bulk controls only appear when valid selections exist.", "Bulk action controls appear only when expected.", area="Shared UI", severity="medium"),
            ChecklistItem("Optional messaging domain", "Run messaging checks if messaging is in scope.", "Messaging-specific flows behave correctly for the current change set.", area="Messaging", severity="medium"),
            ChecklistItem("Optional AI-agent domain", "Run AI-agent checks if AI agent is in scope.", "AI-agent manual flows behave correctly for the current change set.", area="AI Agent", severity="medium"),
        ],
        default_report_name="regression_checklist",
    )


if __name__ == "__main__":
    main()
