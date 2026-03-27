## Phase 244 Implementation Summary

- Scope stayed lead-only and frontend-first.
- Updated the chat-form submit success flow so lead create/edit keeps attention on the newest chat result instead of auto-scrolling back to the workspace panel.
- Kept workspace compatibility by still opening/updating the workspace in the background for lead, but without letting it steal visible focus after submit.
- Added a shared chat-message scroll helper so prompt/button-triggered actions also bring the newest active chat area into view.
