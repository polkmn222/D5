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
            ChecklistItem("Contacts CRUD", "Open `/contacts`, confirm the list loads without runtime errors, create a contact, open the detail page, edit a field, verify list/detail consistency, and delete the record.", "Contact list and detail behavior stays consistent through the full CRUD flow.", area="Contacts", severity="high"),
            ChecklistItem("Contacts list views", "On `/contacts`, open `Setup`, save or clone a custom list view, pin it, and verify `Recently Viewed` after opening a contact detail page.", "Contact saved list views, pinning, and recent-view behavior work end to end.", area="Contacts", severity="high"),
            ChecklistItem("Contacts lookup behavior", "Use a contact-related lookup or related list surface from a linked object detail page.", "Contact lookups, links, and related references render correctly.", area="Contacts", severity="medium"),
            ChecklistItem("Leads CRUD", "Open `/leads`, confirm the list loads without runtime errors, create a lead, update key fields, verify search visibility, and delete or archive the record.", "Lead CRUD behavior matches expectations in list, search, and detail views.", area="Leads", severity="high"),
            ChecklistItem("Leads list views", "On `/leads`, open `Setup`, save or clone a custom list view, pin it, and verify `Recently Viewed` after opening a lead detail page.", "Lead saved list views, pinning, and recent-view behavior work end to end.", area="Leads", severity="high"),
            ChecklistItem("Lead conversion", "From a lead detail page, run the visible conversion path and inspect downstream contact or opportunity records.", "Lead conversion creates or links downstream records as expected.", area="Leads", severity="high"),
            ChecklistItem("Opportunities CRUD", "Open `/opportunities`, confirm the list loads without runtime errors, create an opportunity, update amount or stage, and verify list/detail visibility.", "Opportunity updates persist and render correctly after save and refresh.", area="Opportunities", severity="high"),
            ChecklistItem("Opportunities list views", "On `/opportunities`, open `Setup`, save or clone a custom list view, pin it, and verify `Recently Viewed` after opening an opportunity detail page.", "Opportunity saved list views, pinning, and recent-view behavior work end to end.", area="Opportunities", severity="high"),
            ChecklistItem("Assets CRUD", "Open `/assets`, confirm the list loads without runtime errors, create or edit an asset, verify VIN or related fields, and confirm the detail page renders correctly.", "Asset list/detail behavior and related links remain correct.", area="Assets", severity="medium"),
            ChecklistItem("Assets list views", "On `/assets`, open `Setup`, save a custom list view, pin it, and verify `Recently Viewed` after opening an asset detail page.", "Asset saved list views, pinning, and recent-view behavior work end to end.", area="Assets", severity="medium"),
            ChecklistItem("Products CRUD", "Open `/products`, confirm the list loads without runtime errors, create or edit a product, and verify related brand/model associations and list/detail rendering.", "Product data persists and related links remain correct.", area="Products", severity="medium"),
            ChecklistItem("Products list views", "On `/products`, open `Setup`, save a custom list view, pin it, and verify `Recently Viewed` after opening a product detail page.", "Product saved list views, pinning, and recent-view behavior work end to end.", area="Products", severity="medium"),
            ChecklistItem("Vehicle specs and models", "Use the visible brand/model pages or forms to create or edit a brand/model pair, verify lookup resolution, and test the saved list-view controls on both pages.", "Vehicle spec and model relationships plus saved list-view behavior remain correct.", area="Vehicle Specs", severity="medium"),
            ChecklistItem("Tabs and inline edit", "On a representative detail page, switch `Details`, `Related`, and `Activity` tabs and test inline edit save/cancel controls.", "Tabs switch correctly and inline edit behaves consistently.", area="Shared UI", severity="high"),
            ChecklistItem("Batch edit and save", "Use a batch-edit capable view and trigger the visible save control for multiple changed fields.", "Batch save updates apply correctly without broken UI state.", area="Shared UI", severity="high"),
            ChecklistItem("Sorting behavior", "Use sortable table headers on a representative list or dashboard table.", "Header click actions reorder the visible rows as expected.", area="Shared UI", severity="medium"),
            ChecklistItem("Shared list view controls", "On representative CRM object list pages, confirm `Setup`, `Pin`, saved filters, visible fields, and recent-view switching behave correctly.", "Shared Salesforce-style list view controls work consistently across supported objects.", area="Shared UI", severity="high"),
            ChecklistItem("Bulk action visibility", "On a selectable list page, toggle row checkboxes and observe the visible bulk-action controls.", "Bulk controls appear only when valid selections exist and hide when selection is cleared.", area="Shared UI", severity="medium"),
            ChecklistItem("Optional messaging domain", "If messaging is in scope, open Send Message or template views and test the visible template, duplicate-review, or delivery controls.", "Messaging-specific flows behave correctly for the current change set.", area="Messaging", severity="medium"),
            ChecklistItem("Optional AI-agent domain", "If AI agent is in scope, open `/ai-agent`, test chat, selection context, pagination, or reset behavior.", "AI-agent manual flows behave correctly for the current change set.", area="AI Agent", severity="medium"),
        ],
        default_report_name="regression_checklist",
    )


if __name__ == "__main__":
    main()
