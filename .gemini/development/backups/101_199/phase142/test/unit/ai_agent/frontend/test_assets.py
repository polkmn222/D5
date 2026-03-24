from pathlib import Path


ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
TEMPLATE = ROOT / "ai_agent" / "frontend" / "templates" / "ai_agent.html"
SCRIPT = ROOT / "ai_agent" / "frontend" / "static" / "js" / "ai_agent.js"
STYLE = ROOT / "ai_agent" / "frontend" / "static" / "css" / "ai_agent.css"


def test_template_contains_reset_agent_and_quick_guide_cards():
    html = TEMPLATE.read_text()

    assert "Reset Agent" in html
    assert "agent-hidden" in html
    assert "quick-guide-grid" in html
    assert "quick-card" in html
    assert "show the lead I just created" in html
    assert "delete that contact" in html
    assert "ai-agent-selection-bar" in html
    assert html.index("ai-agent-selection-bar") < html.index("id=\"ai-agent-footer\"")
    assert "Send Message" in html
    assert "Open the messaging flow for selected records" in html
    assert "ai-agent-selection-detail" in html
    assert "welcome-tip" in html
    assert "Change AI Recommend" in html
    assert "ai-agent-image-modal" in html
    assert "ai-agent-image-fallback" in html
    assert "ai-agent-close-btn" in html
    assert "closeAiAgent()" in html
    assert "triggerSelectionEdit()" in html
    assert "triggerSelectionDelete()" in html
    assert "triggerSelectionOpen()" in html
    assert "data-ai-selection-open" in html
    assert "data-ai-selection-clear" not in html
    assert "ai-agent-lang-eng" in html
    assert "ai-agent-lang-kor" in html
    assert "data-ai-guide-kicker" in html
    assert "data-ai-selection-send" in html


def test_script_contains_reset_and_pagination_hooks():
    js = SCRIPT.read_text()

    assert "/ai-agent/api/reset" in js
    assert "conversation_id: aiAgentConversationId" in js
    assert "per_page: 50" in js
    assert "requestAgentPage" in js
    assert "buildSelectionPayload" in js
    assert "agent-selection-label" in js
    assert "sessionStorage.setItem('aiAgentMessageSelection'" in js
    assert "sessionStorage.setItem('aiAgentMessageTemplate'" in js
    assert "triggerSelectionMessaging" in js
    assert "triggerSelectionOpen" in js
    assert "triggerSelectionEdit" in js
    assert "triggerSelectionDelete" in js
    assert "getAgentObjectRoute" in js
    assert "openAgentWorkspace(url" in js
    assert "openAgentWorkspaceHtml" in js
    assert "extractAgentWorkspaceMarkup" in js
    assert "wireAgentWorkspaceInteractions" in js
    assert "DOMParser" in js
    assert "ai-agent-workspace-content" in js
    assert "summarizeSelectionIds" in js
    assert "updateSelectionBar" in js
    assert "AI_AGENT_DEFAULT_BODY_HTML" in js
    assert "win.classList.add('agent-hidden')" in js
    assert "localAgentResultTables" in js
    assert "requestLocalAgentPage" in js
    assert "openAgentImagePreview" in js
    assert "agent-thumbnail-btn" in js
    assert "Template Preview" in js
    assert "Use In Send Message" in js
    assert "startTemplateSendFromAgent" in js
    assert "Template prepared for Send Message" in js
    assert "/messaging/ui?sourceObject=message_template" in js
    assert "openAgentWorkspace('/messaging/ui?sourceObject=message_template'" in js
    assert "ensureAiAgentPanelLoaded" in js
    assert "fetch('/ai-agent-panel')" in js
    assert "records${pagination.mode === 'local' ? ' · Local' : ''}" in js
    assert "image.onerror" in js
    assert "syncAiAgentWindowState" in js
    assert "closeAiAgent" in js
    assert "classList.toggle('agent-minimized'" in js
    assert "classList.toggle('agent-maximized'" in js
    assert "setDashboardRecommendationMode" in js
    assert "/api/recommendations/mode" in js
    assert "AI Recommend mode set to ${payload.mode}." in js
    assert "Who should I send the message to?" in js
    assert "setAiAgentLanguage" in js
    assert "applyAiAgentLanguageUi" in js
    assert "language_preference: aiAgentLanguagePreference" in js
    assert "최근 생성된 리드" in js
    assert "data-ai-guide-kicker" in js or "[data-ai-guide-kicker]" in js
    assert "Select one or more records to delete them." in js
    assert "Delete selected ${selection.object_type} records" in js
    assert "sendAiMessageWithDisplay" in js
    assert "data-record-label" in js
    assert "aiAgentActiveSelectionContainer.appendChild(bar)" in js
    assert "const AGENT_TABLE_SCHEMAS" in js
    assert "display_name" in js
    assert "Selection Ready" in js
    assert "/messaging/ui?sourceObject=message_template" in js


def test_styles_include_reset_button_and_pagination_classes():
    css = STYLE.read_text()

    assert ".agent-reset-btn" in css
    assert ".agent-pagination" in css
    assert ".quick-guide-hero" in css
    assert ".agent-selection-label" in css or ".agent-pagination-label" in css
    assert ".selection-bar" in css
    assert ".selection-bar-detail" in css
    assert ".selection-action-danger" in css
    assert ".agent-inline-action-confirm" in css
    assert ".agent-inline-action-cancel" in css
    assert ".welcome-tip" in css
    assert ".agent-hidden" in css
    assert ".agent-minimized" in css
    assert ".agent-image-modal" in css
    assert ".agent-thumbnail-btn" in css
    assert ".agent-action-stack" in css
    assert ".control-btn-primary" in css
    assert ".agent-image-fallback" in css
    assert ".agent-hidden" in css
    assert ".agent-window-control" in css
    assert ".agent-window-control-close" in css
    assert ".agent-maximized" in css
    assert ".agent-language-toggle" in css
    assert ".agent-workspace-content" in css
    assert ".selection-action-btn:disabled" in css
