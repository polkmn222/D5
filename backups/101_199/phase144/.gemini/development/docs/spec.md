# Verification Spec

## Definition of Success

A change is done only when all of the following are true:

1. Core functionality works for the intended user flow.
2. UI stays aligned with the established Salesforce-inspired patterns.
3. Record detail pages preserve the correct tab and interaction model for that object family; shared inline-edit expectations do not apply to intentionally read-only surfaces such as the current message-send detail page.
4. Relevant automated tests pass, or skipped coverage is explicitly documented.
5. The next unused phase number is used consistently for `task`, `Implementation`, `Walkthrough`, and `backups` artifacts.
6. Runtime-facing docs are updated when entry points, deployment behavior, data model expectations, or workflow rules change.

## Verification Checklist

- [ ] **ID Integrity**: New CRM records still receive valid 18-character identifiers where that pattern is expected.
- [ ] **Audit Fields**: `created_by`, `updated_by`, `created_at`, and `updated_at` continue to populate automatically and remain non-editable from normal UI flows.
- [ ] **Validation**: Invalid form input returns a clean validation experience instead of an unhandled server error.
- [ ] **Lead Lifecycle**: Converting a lead creates the expected downstream records for the current model, especially `Contact` and `Opportunity`, while preserving linked vehicle and product interest data.
- [ ] **Messaging Flows**: Message template selection, send actions, and provider-specific validation still behave correctly when touched.
- [ ] **Messaging UI Contract**: Messaging detail templates still resolve from `web/message/frontend/templates/`, and read-only pages are not accidentally forced back into shared inline-edit behavior.
- [ ] **AI Agent Mount**: AI-related work preserves the mounted `/ai-agent` runtime and its response contracts.
- [ ] **Known Test Status**: If some tests are expected to fail or skip because docs and tests are being brought back into sync, record that status in `docs/testing/known_status.md`.
- [ ] **Deployment Accuracy**: Vercel and Render docs still match `api/index.py`, `vercel.json`, and `render.yaml` after structural changes.
- [ ] **Database Compatibility**: Runtime changes remain compatible with the PostgreSQL-backed application path.

## Edge Cases to Verify

- Null lookup values and blank optional fields still render safely.
- Duplicate VIN or other uniqueness-sensitive data paths fail cleanly.
- Partial import or bulk operation failures do not leave the system in an inconsistent state.
- AI or messaging features degrade predictably when provider credentials are missing.
- Shared UI tests that assume all detail pages are editable are treated as suspect unless the object still uses the shared editable detail pattern.
