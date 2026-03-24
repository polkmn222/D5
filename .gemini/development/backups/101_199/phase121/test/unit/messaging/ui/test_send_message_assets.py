from pathlib import Path


ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
SEND_TEMPLATE = ROOT / "web" / "message" / "frontend" / "templates" / "send_message.html"
MESSAGE_TEMPLATE_DETAIL = ROOT / "web" / "message" / "frontend" / "templates" / "message_templates" / "detail_view.html"


def test_send_message_template_contains_duplicate_review_and_template_controls():
    html = SEND_TEMPLATE.read_text()

    assert "duplicate-review-modal" in html
    assert "Keep Duplicates Excluded" in html
    assert "Send To Duplicates Too" in html
    assert "Send Using Review Selection" in html
    assert "preview-template-btn" in html
    assert "delete-template-btn" in html
    assert "template-preview-card" in html
    assert "preview-modal-summary" in html
    assert "modal-mms-upload-area" in html
    assert "Upload JPG" in html
    assert "template-image-lightbox" in html


def test_send_message_template_contains_phone_dedupe_logic_and_ai_selection_import():
    html = SEND_TEMPLATE.read_text()

    assert "getDuplicatePhoneGroups" in html
    assert "normalizePhone" in html
    assert "filterRecipientsByDuplicatePreference" in html
    assert "toggleAllDuplicateOptions" in html
    assert "getReviewedDuplicateRecipients" in html
    assert "sendUsingDuplicateReviewSelection" in html
    assert "resolveRecipientsForPreview" in html
    assert "buildCurrentMessageConfig" in html
    assert "buildGroupedMessagePayload" in html
    assert "Preview and send use the same delivery plan" in html
    assert "validateCurrentMessageConfig" in html
    assert "MMS templates require a JPG image under 500KB." in html
    assert "Excluded Duplicate Phone" in html
    assert "initializeAiAgentSelection" in html
    assert "initializeAiAgentTemplate" in html
    assert "aiAgentMessageSelection" in html
    assert "aiAgentMessageTemplate" in html
    assert "aiAgentTemplateImported" in html
    assert "handleTemplateImageUpload" in html
    assert "openTemplateImageLightbox" in html
    assert "template-import-note" in html
    assert "AI Agent loaded an <strong>MMS</strong> template" in html
    assert "AI Agent loaded this template into Send Message" in html
    assert "MMS templates only support JPG images." in html
    assert "MMS template images must be 500KB or smaller." in html
    assert "Replacing or removing the image will replace the previous template image." in html
    assert "const payload = { name, content, record_type, subject: record_type === 'SMS' ? '' : subject, file_path, attachment_id, image_url }" in html
    assert "messageByteLength" in html
    assert "normalizeComposeType" in html
    assert "validateMessageRules" in html
    assert "SMS content is over 90 bytes. Change the template type to LMS?" in html
    assert "LMS and MMS templates must be 2000 bytes or fewer." in html


def test_send_message_template_uses_contact_based_staging_and_row_status_cleanup():
    html = SEND_TEMPLATE.read_text()

    assert "let stagedMessages = {}; // { contactId:" in html
    assert "const contactId = cb.value;" in html
    assert "if (contactId && !stagedMessages[contactId])" in html
    assert "stagedMessages[contactId] = {" in html
    assert "rowIds: []" in html
    assert "group.rowIds.forEach(id => {" in html
    assert "delete stagedMessages[id];" in html


def test_message_template_detail_supports_real_image_upload_actions():
    html = MESSAGE_TEMPLATE_DETAIL.read_text()

    assert "document.getElementById('file-Image').click()" in html
    assert "removeTemplateImage('{{ record_id }}')" in html
    assert "showComingSoon()" not in html
