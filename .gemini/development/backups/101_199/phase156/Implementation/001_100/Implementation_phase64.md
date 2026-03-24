# Phase 64 - Selection Guidance, Image Lightbox, and Explicit Template Send Flow

## Goals
- Make the selection banner feel more conversational inside the AI Agent chat area.
- Add clickable image preview/lightbox behavior for template images.
- Make template-aware send-message requests more explicit and safer.

## Implemented Changes

### 1. Conversational Selection Banner
- Updated the selection banner copy to emphasize that users can keep chatting and doing CRUD before choosing Send Message.
- The selection banner remains in the chat area, not in the input footer.

### 2. Image Lightbox Support
- Added AI Agent image preview modal for template image thumbnails in result tables.
- Added Send Message template-image lightbox for the selected template preview card.

### 3. Explicit Template Send Guidance
- AI Agent send-message resolution now handles `template` phrasing more safely.
- If the user asks to send with a template but no current template is in context, the agent asks them to manage/open a template first.
- If a current template exists, the send handoff message clearly notes the template being used.

### 4. Template Replacement Guidance
- Added template-modal guidance that replacing or removing an image replaces the previous template image.

## Files Changed
- `.gemini/development/ai_agent/frontend/templates/ai_agent.html`
- `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- `.gemini/development/ai_agent/frontend/static/css/ai_agent.css`
- `.gemini/development/ai_agent/backend/service.py`
- `.gemini/development/frontend/templates/send_message.html`

## Backup
- `.gemini/development/ai_agent/backups/phase64/`
- `.gemini/development/backups/phase64_send_message.html`
