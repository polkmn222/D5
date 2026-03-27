Phase 260 Task Record

Scope
- Template-only chat-native open/view + preview/handoff bundle.
- Replace the current generic template manage/open HTML block with a proper chat-card contract.
- Keep scope limited to deterministic `Manage message_template <id>` / `OPEN_RECORD`, template chat-card response, selection/table `Open` chat-first routing, preserved-focus non-submit `OPEN_RECORD`, safe preview action, and existing `Use In Send Message` handoff reuse.

Approvals
- Treat `send/template` as one roadmap group but not one implementation phase.
- Start with `template` first.
- Use the existing modal preview helper only.
- Reuse the current `startTemplateSendFromAgent(templateId)` handoff path.

Out Of Scope
- Send-message flow redesign.
- Template create/edit chat-native forms.
- Provider/image upload logic.
- Target-resolution changes.
- Template storage/path migration.
- Browser automation.
- DB-backed verification.

Constraints
- Unit tests mandatory.
- DOM-level UI tests required for changed UI behavior.
- No manual testing.
- Do not use SQLite.
