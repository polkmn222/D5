from textwrap import dedent


def main() -> None:
    print(
        dedent(
            """
            D4 Regression Manual Checklist

            Core CRM Objects
            - Contacts: create, detail, inline edit, list/detail consistency, delete.
            - Leads: create, update, search visibility, convert flow, downstream verification.
            - Opportunities: create, update amount/stage, list/dashboard visibility, detail actions.
            - Assets, Products, Vehicle Specs, Models: create, lookup resolution, update, list/detail rendering, delete.

            Shared UI
            - Tabs switch correctly.
            - Inline edit opens, saves, and cancels.
            - Batch edit and batch save work.
            - Sorting hooks work.
            - Bulk action controls appear only for valid selections.

            Optional Domains
            - Messaging flows when messaging is in scope.
            - AI agent flows when AI agent is in scope.

            Reference
            - Canonical checklist: .gemini/development/docs/testing/manual_checklist.md
            """.strip()
        )
    )


if __name__ == "__main__":
    main()
