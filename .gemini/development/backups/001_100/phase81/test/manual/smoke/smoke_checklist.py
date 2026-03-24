from textwrap import dedent


def main() -> None:
    print(
        dedent(
            """
            D4 Smoke Manual Checklist

            Environment
            - Confirm TEST_DATABASE_URL points to a dedicated PostgreSQL test database.
            - Optionally set D4_RESET_MANUAL_TEST_DB=1 for a clean reset.
            - Start the app with ./run_crm.sh.

            Smoke Checks
            1. Dashboard loads successfully.
            2. Top-level navigation opens key object pages.
            3. Global search or lookup search returns usable results.
            4. One core object create flow succeeds.
            5. One core object update flow succeeds.
            6. One core object delete or soft-delete flow succeeds.
            7. Detail tabs and shared action buttons render correctly.

            Reference
            - Canonical checklist: .gemini/development/docs/testing/manual_checklist.md
            """.strip()
        )
    )


if __name__ == "__main__":
    main()
