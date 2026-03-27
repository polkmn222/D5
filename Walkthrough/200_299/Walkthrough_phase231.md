# Phase 231 Walkthrough

## What Was Done

- Added a dedicated schema-form scroll helper in the AI-agent frontend.
- Applied that helper after a chat-native create/edit form card is appended to the conversation.
- Applied that helper again when a validation refresh returns a replacement `OPEN_FORM`.
- Normalized selection/table Edit actions so `lead`, `contact`, and `opportunity` all re-enter the chat-native edit flow instead of opening workspace directly.

## How It Works

1. When the backend returns schema-based `OPEN_FORM`, the frontend appends the chat form card and scrolls it into view.
2. If submit returns validation errors as another schema-based `OPEN_FORM`, the frontend replaces the card in place and scrolls the replacement card into view.
3. Selection-bar Edit and table Edit now send the `Manage ... edit` chat request for the approved objects.
4. The old workspace `form_url` branch remains available only as fallback.

## How To Verify

- Run the focused unit test file for chat-native form behavior.
- Confirm source-level coverage for:
  - schema-form branch and submit endpoint
  - no workspace use in the schema-form branch
  - initial render auto-scroll
  - validation-refresh auto-scroll
  - selection Edit routing for `lead`, `contact`, and `opportunity`

## Test Command

`PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
