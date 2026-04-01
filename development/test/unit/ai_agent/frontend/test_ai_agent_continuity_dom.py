import subprocess
import textwrap
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[4]
JS_PATH = BASE_DIR / "ai_agent" / "ui" / "frontend" / "static" / "js" / "ai_agent.js"


def _run_node_dom_test(test_body: str) -> None:
    script = textwrap.dedent(
        f"""
        const fs = require('fs');
        const vm = require('vm');

        const source = fs.readFileSync({str(JS_PATH)!r}, 'utf8');

        function createHarness() {{
            const elements = new Map();

            class FakeClassList {{
                constructor(owner) {{
                    this.owner = owner;
                    this.tokens = new Set();
                }}

                _sync() {{
                    this.owner.className = Array.from(this.tokens).join(' ');
                }}

                add(...names) {{
                    names.forEach(name => this.tokens.add(name));
                    this._sync();
                }}

                remove(...names) {{
                    names.forEach(name => this.tokens.delete(name));
                    this._sync();
                }}

                contains(name) {{
                    return this.tokens.has(name);
                }}

                toggle(name, force) {{
                    if (force === true) {{
                        this.tokens.add(name);
                    }} else if (force === false) {{
                        this.tokens.delete(name);
                    }} else if (this.tokens.has(name)) {{
                        this.tokens.delete(name);
                    }} else {{
                        this.tokens.add(name);
                    }}
                    this._sync();
                    return this.tokens.has(name);
                }}
            }}

            class FakeElement {{
                constructor(tagName = 'div', id = '') {{
                    this.tagName = tagName.toUpperCase();
                    this.children = [];
                    this.parentNode = null;
                    this.dataset = {{}};
                    this.style = {{}};
                    this.attributes = {{}};
                    this.className = '';
                    this.classList = new FakeClassList(this);
                    this.scrollIntoViewCalls = [];
                    this.scrollToCalls = [];
                    this._innerHTML = '';
                    this.textContent = '';
                    this.value = '';
                    this.id = id;
                }}

                appendChild(child) {{
                    child.parentNode = this;
                    this.children.push(child);
                    if (child.id) elements.set(child.id, child);
                    return child;
                }}

                prepend(child) {{
                    child.parentNode = this;
                    this.children.unshift(child);
                    if (child.id) elements.set(child.id, child);
                    return child;
                }}

                insertAdjacentElement(position, element) {{
                    if (!this.parentNode || position !== 'afterend') return;
                    const siblings = this.parentNode.children;
                    const index = siblings.indexOf(this);
                    if (index === -1) return;
                    element.parentNode = this.parentNode;
                    siblings.splice(index + 1, 0, element);
                    if (element.id) elements.set(element.id, element);
                }}

                remove() {{
                    if (!this.parentNode) return;
                    this.parentNode.children = this.parentNode.children.filter(child => child !== this);
                    if (this.id) elements.delete(this.id);
                }}

                querySelector(selector) {{
                    if (selector.startsWith('#')) {{
                        return elements.get(selector.slice(1)) || null;
                    }}
                    return null;
                }}

                querySelectorAll() {{
                    return [];
                }}

                closest() {{
                    return null;
                }}

                setAttribute(name, value) {{
                    this.attributes[name] = value;
                    if (name === 'id') {{
                        this.id = value;
                    }}
                }}

                getAttribute(name) {{
                    return this.attributes[name] || null;
                }}

                scrollIntoView(options) {{
                    this.scrollIntoViewCalls.push(options);
                }}

                scrollTo(options) {{
                    this.scrollToCalls.push(options);
                }}

                getBoundingClientRect() {{
                    return {{ top: 120, height: 240 }};
                }}

                get offsetTop() {{
                    return 120;
                }}

                get offsetHeight() {{
                    return 240;
                }}

                set innerHTML(value) {{
                    this._innerHTML = String(value);
                    this.textContent = String(value);
                }}

                get innerHTML() {{
                    return this._innerHTML;
                }}
            }}

            const document = {{
                createElement: (tagName) => new FakeElement(tagName),
                getElementById: (id) => elements.get(id) || null,
                querySelector: (selector) => selector.startsWith('#') ? (elements.get(selector.slice(1)) || null) : null,
                querySelectorAll: () => [],
                addEventListener: () => {{}},
                body: new FakeElement('body', 'document-body'),
            }};

            const localStorage = {{
                getItem: () => null,
                setItem: () => {{}},
                removeItem: () => {{}},
            }};

            const sessionStorage = {{
                getItem: () => null,
                setItem: () => {{}},
                removeItem: () => {{}},
            }};

            const context = {{
                console,
                document,
                localStorage,
                sessionStorage,
                window: {{
                    document,
                    crypto: {{ randomUUID: () => 'conv-fixed' }},
                    location: {{ origin: 'http://localhost' }},
                }},
                setTimeout: (fn) => {{
                    fn();
                    return 1;
                }},
                clearTimeout: () => {{}},
                requestAnimationFrame: (fn) => fn(),
                DOMParser: class {{
                    parseFromString() {{
                        return {{
                            querySelector: () => null,
                            body: {{ innerHTML: '' }},
                        }};
                    }}
                }},
                fetch: async () => ({{ ok: true, status: 200, text: async () => '', json: async () => ({{}}) }}),
                FormData: class {{}},
                URL,
                Date,
                Math,
                JSON,
                Promise,
            }};

            context.global = context;
            context.globalThis = context;

            const register = (id, value = '') => {{
                const element = new FakeElement('div', id);
                element.value = value;
                elements.set(id, element);
                return element;
            }};

            register('ai-agent-body');
            register('ai-agent-input');
            register('ai-agent-workspace');
            register('ai-agent-workspace-content');
            register('ai-agent-workspace-loading');
            register('ai-agent-workspace-title');
            register('ai-agent-selection-bar');

            context.__elements = elements;
            context.__FakeElement = FakeElement;
            return context;
        }}

        async function main() {{
            const context = createHarness();
            vm.createContext(context);
            vm.runInContext(source, context);
            {test_body}
        }}

        main().catch((error) => {{
            console.error(error && error.stack ? error.stack : error);
            process.exit(1);
        }});
        """
    )
    completed = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_inline_web_form_submit_uses_ai_managed_bridge_for_supported_objects():
    source = JS_PATH.read_text()
    assert "const aiManaged = await handleAiManagedInlineFormSubmit(container, sourceUrl, submitMode, closeHandler);" in source
    assert "if (aiManaged) {" in source
    assert "const managedOpenRecord = await resolveAgentOpenRecordFromRedirect(finalUrl);" in source
    assert "if (pathname === '/assets/new-modal') {" in source
    assert "if (pathname === '/models/new-modal') {" in source
    assert "if (pathname === '/message_templates/new-modal') {" in source
    assert "if (pathname === '/vehicle_specifications/new-modal' && sourceUrl?.searchParams?.get('type') === 'Brand') {" in source
    assert "function hasSelectedInlineFileForAiManagedSubmit(form) {" in source
    assert "if (hasSelectedInlineFileForAiManagedSubmit(form)) {" in source


def test_grouped_object_edit_actions_use_direct_inline_form_path():
    source = JS_PATH.read_text()
    assert "function shouldUseDirectAgentEditForm(objectType) {" in source
    assert "function openAgentEditFormDirect(objectType, recordId, displayName = '') {" in source
    assert "appendAgentInlineFormMessage(buildAgentEditIntro(objectType, displayName), url, `Edit ${displayName || objectType}`);" in source
    assert "if (shouldUseDirectAgentEditForm(selection.object_type)) {" in source
    assert "openAgentEditFormDirect(selection.object_type, selection.ids[0], label);" in source
    assert "onclick=\"openAgentEditFormDirect('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')\"" in source


def test_workspace_edit_uses_inline_form_path_for_grouped_objects():
    source = JS_PATH.read_text()
    assert "function triggerWorkspaceEdit() {" in source
    assert "panel.dataset.recordObjectType = getAiAgentObjectTypeFromPath(url) || '';" in source
    assert "panel.dataset.recordId = getAiAgentRecordIdFromPath(url) || '';" in source
    assert "if (shouldUseDirectAgentEditForm(objectType)) {" in source
    assert "openAgentEditFormDirect(objectType, recordId, title);" in source


def test_ai_agent_initializes_scoped_template_modal_visibility_for_inline_forms():
    source = JS_PATH.read_text()
    assert "function initializeAiAgentTemplateModalUi(container) {" in source
    assert "const form = container.querySelector('form');" in source
    assert "const typeSelect = form.querySelector('select[name=\"record_type\"]');" in source
    assert "const subjectWrapper = form.querySelector('.sf-field-wrapper[data-field=\"subject\"]');" in source
    assert "const imageWrapper = form.querySelector('.sf-field-wrapper[data-field=\"image\"]');" in source
    assert "if (String(formUrl || '').includes('/message_templates/new-modal')) {" in source
    assert "initializeAiAgentTemplateModalUi(container);" in source
    assert "typeSelect.addEventListener('change', updateScopedTemplateUi);" in source


def test_results_table_includes_new_action_button():
    source = JS_PATH.read_text()
    assert """onclick="triggerCreateFromTable(this, '${objectType}')">New</button>""" in source
    assert "function triggerCreateFromTable(btn, objectType) {" in source


def test_grouped_object_edit_routes_are_not_missing_for_brand_and_template():
    source = JS_PATH.read_text()
    assert "brand: { detail: `/vehicle_specifications/${recordId}`, edit: `/vehicle_specifications/new-modal?type=Brand&id=${recordId}` }" in source
    assert "message_template: { detail: `/message_templates/${recordId}`, edit: `/message_templates/new-modal?id=${recordId}` }" in source


def test_ai_agent_window_uses_ninety_percent_zoom():
    css_source = Path("development/ai_agent/ui/frontend/static/css/ai_agent.css").read_text()
    assert "#ai-agent-window {" in css_source
    assert "zoom: 0.9;" in css_source
    assert "width: clamp(440px, 96vw, 1080px);" in css_source
    assert "height: clamp(600px, 95vh, 900px);" in css_source
    assert "#ai-agent-window.agent-maximized {" in css_source
    assert "zoom: 0.95;" in css_source


def test_send_message_handoff_without_selection_seeds_guidance_state():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("function completeAgentSendMessageHandoff(")
    end = source.index("function startTemplateSendFromAgent(", start)
    branch = source[start:end]

    assert "const hasSelection = !!(selection && Array.isArray(selection.ids) && selection.ids.length);" in branch
    assert "sessionStorage.setItem('aiAgentMessageGuidance', JSON.stringify({" in branch
    assert "sessionStorage.removeItem('aiAgentMessageSelection');" in branch


def test_send_message_intent_uses_ai_native_composer_instead_of_workspace_handoff():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'SEND_MESSAGE') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form_url) {", start)
    branch = source[start:end]

    assert "appendAgentSendMessageComposer(" in branch
    assert "redirectUrl: data.redirect_url" in branch
    assert "selection: data.selection" in branch


def test_agent_send_message_composer_fetches_base_compose_data_then_lazy_loads_recommendations():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "fetchAiAgentWithTimeout('/messaging/ai-agent-compose-data'" in source
    assert "fetchAiAgentWithTimeout('/messaging/recommendations'" in source
    assert "fetchAiAgentWithTimeout('/messaging/demo-availability'" in source
    assert "async function submitAgentSendComposer(composerId, btn) {" in source
    assert "fetchAiAgentWithTimeout('/messaging/bulk-send'" in source
    assert "Choose a template or enter message content before sending." in source
    assert "MMS requires an image-backed template in AI Agent. Choose an MMS template first." in source
    assert "Save Recipients" in source
    assert "Clear All" in source
    assert "class=\"agent-send-action-stack\"" in source
    assert "Saved recipients:" in source


def test_agent_send_message_preview_only_renders_in_maximized_mode():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    css_source = Path("development/ai_agent/ui/frontend/static/css/ai_agent.css").read_text(encoding="utf-8")

    assert "showPreview: isAiAgentMaximized" in source
    assert "${state.showPreview ? renderAgentSendPreview(state) : ''}" in source
    assert "#ai-agent-window.agent-maximized .agent-send-composer-grid {" in css_source
    assert ".agent-send-preview-panel {" in css_source
    assert ".agent-send-action-stack {" in css_source
    assert ".agent-send-secondary-accent {" in css_source


def test_new_modal_workspace_extraction_keeps_trailing_modal_scripts():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "Array.from(doc.body.children || [])" in source
    assert ".filter(node => node.tagName === 'SCRIPT')" in source
    assert ".forEach(script => wrapper.appendChild(script.cloneNode(true)));" in source


def test_local_results_table_search_uses_visible_schema_fields_only():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "function agentTableRowMatches(row, objectType, term) {" in source
    assert "const schemaKeys = AGENT_TABLE_SCHEMAS[objectType] || Object.keys(row || {});" in source
    assert "tableState.results.filter(row => agentTableRowMatches(row, tableState.objectType, term))" in source


def test_local_results_table_search_restores_focus_after_rerender():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "requestLocalAgentPage(tableKey, 1, {" in source
    assert "focusSearch: true," in source
    assert "const nextInput = nextContainer?.querySelector?.('.agent-table-search');" in source
    assert "nextInput.focus();" in source
    assert "nextInput.setSelectionRange(searchState.selectionStart || 0, searchState.selectionEnd || 0);" in source


def test_send_ai_message_with_display_appends_latest_user_message_and_scrolls_it_into_view():
    _run_node_dom_test(
        """
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        context.sendAiMessageWithDisplay('Open Ada Kim', 'Manage lead LEAD1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected 1 chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected latest message to be user chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Ada Kim')) {
            throw new Error('expected latest chat message to include display text');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected prompt/button-triggered action to scroll latest chat message into view');
        }
        if (context.__sentQuery !== 'Manage lead LEAD1') {
            throw new Error(`expected sendAiMessage to receive actual query, got ${context.__sentQuery}`);
        }
        """
    )


def test_append_chat_message_scrolls_latest_message_anchor_into_view():
    _run_node_dom_test(
        """
        const body = context.document.getElementById('ai-agent-body');
        const appended = context.appendChatMessage('agent', 'Latest response');

        if (body.scrollToCalls.length !== 0) {
            throw new Error(`expected appendChatMessage not to force bottom scrolling, got ${body.scrollToCalls.length}`);
        }
        if (!appended || appended.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected appendChatMessage to scroll the latest message anchor into view');
        }
        """
    )


def test_send_ai_message_with_display_keeps_contact_prompt_action_in_latest_chat_area():
    _run_node_dom_test(
        """
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        context.sendAiMessageWithDisplay('Open Ada Kim', 'Manage contact CONTACT1');

        const body = context.document.getElementById('ai-agent-body');
        const latest = body.children[0];
        if (!latest || latest.className !== 'msg-user') {
            throw new Error('expected contact action to append a latest user chat message');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected contact prompt/button action to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage contact CONTACT1') {
            throw new Error(`expected contact action query, got ${context.__sentQuery}`);
        }
        """
    )


def test_send_ai_message_clears_workspace_loading_when_chat_request_fails():
    _run_node_dom_test(
        """
        const loading = context.document.getElementById('ai-agent-workspace-loading');
        loading.classList.remove('agent-hidden');
        context.fetch = async () => { throw new Error('network down'); };

        await context.sendAiMessage('show all leads');

        if (!loading.classList.contains('agent-hidden')) {
            throw new Error('expected failed AI Agent request to clear lingering workspace loading');
        }
        """
    )


def test_ai_agent_window_controls_contract_keeps_debug_toggle_and_uses_viewport_maximize():
    panel_source = (BASE_DIR / "ai_agent" / "ui" / "frontend" / "templates" / "ai_agent_panel.html").read_text(encoding="utf-8")
    js_source = JS_PATH.read_text(encoding="utf-8")
    css_source = (BASE_DIR / "ai_agent" / "ui" / "frontend" / "static" / "css" / "ai_agent.css").read_text(encoding="utf-8")

    assert 'id="ai-agent-debug-toggle"' in panel_source
    assert "let aiAgentDebugEnabled = localStorage.getItem('aiAgentDebugEnabled');" in js_source
    assert "aiAgentDebugEnabled = aiAgentDebugEnabled === '1';" in js_source
    assert "#ai-agent-window.agent-maximized {" in css_source
    assert "left: 16px;" in css_source
    assert "width: auto;" in css_source
    assert "max-width: none;" in css_source
    assert "#ai-agent-window.agent-minimized #ai-agent-debug-toggle {" in css_source


def test_contact_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'contact';", context);
        vm.runInContext("aiAgentSelectionState.contact = new Set(['CONTACT1']);", context);
        vm.runInContext("aiAgentSelectionMeta.contact = new Map([['CONTACT1', 'Ada Kim']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected contact selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Ada Kim')) {
            throw new Error('expected contact selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected contact selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage contact CONTACT1') {
            throw new Error(`expected contact selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from contact selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_contact_chat_card_renders_send_message_and_reuses_existing_chat_native_messaging_path():
    _run_node_dom_test(
        """
        const quickMessages = [];
        context.sendQuickMessage = (message) => {
            quickMessages.push(message);
        };

        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'contact',
            record_id: 'CONTACT1',
            title: 'Ada Kim',
            subtitle: 'Contact · Qualified',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Edit', action: 'edit', tone: 'secondary' },
                { label: 'Delete', action: 'delete', tone: 'danger' },
                { label: 'Send Message', action: 'send_message', tone: 'secondary' },
            ],
        });

        if (!markup.includes('Send Message')) {
            throw new Error('expected contact chat card markup to include Send Message');
        }
        if (markup.includes('Open Record')) {
            throw new Error('expected open-record button to be omitted from already-open chat cards');
        }
        if (!markup.includes("triggerLeadCardSendMessage('contact', 'CONTACT1', 'Ada Kim')")) {
            throw new Error('expected contact chat card Send Message action to reuse the existing card handler');
        }

        context.triggerLeadCardSendMessage('contact', 'CONTACT1', 'Ada Kim');

        const activeObject = vm.runInContext('aiAgentActiveSelectionObject', context);
        const selectedIds = vm.runInContext("Array.from(aiAgentSelectionState.contact || [])", context);
        const selectedName = vm.runInContext("aiAgentSelectionMeta.contact && aiAgentSelectionMeta.contact.get('CONTACT1')", context);

        if (activeObject !== 'contact') {
            throw new Error(`expected Send Message action to activate contact selection, got ${activeObject}`);
        }
        if (selectedIds.length !== 1 || selectedIds[0] !== 'CONTACT1') {
            throw new Error(`expected Send Message action to seed contact selection, got ${selectedIds}`);
        }
        if (selectedName !== 'Ada Kim') {
            throw new Error(`expected Send Message action to preserve display name, got ${selectedName}`);
        }
        if (quickMessages.length !== 1 || quickMessages[0] !== 'Send Message') {
            throw new Error(`expected Send Message action to trigger the chat-native messaging path, got ${quickMessages}`);
        }
        """
    )


def test_send_ai_message_with_display_keeps_opportunity_prompt_action_in_latest_chat_area():
    _run_node_dom_test(
        """
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        context.sendAiMessageWithDisplay('Open Fleet Renewal', 'Manage opportunity OPP1');

        const body = context.document.getElementById('ai-agent-body');
        const latest = body.children[0];
        if (!latest || latest.className !== 'msg-user') {
            throw new Error('expected opportunity action to append a latest user chat message');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected opportunity prompt/button action to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage opportunity OPP1') {
            throw new Error(`expected opportunity action query, got ${context.__sentQuery}`);
        }
        """
    )


def test_opportunity_chat_card_renders_send_message_and_reuses_existing_chat_native_messaging_path():
    _run_node_dom_test(
        """
        const quickMessages = [];
        context.sendQuickMessage = (message) => {
            quickMessages.push(message);
        };

        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'opportunity',
            record_id: 'OPP1',
            title: 'Fleet Renewal',
            subtitle: 'Opportunity · Qualification',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Edit', action: 'edit', tone: 'secondary' },
                { label: 'Delete', action: 'delete', tone: 'danger' },
                { label: 'Send Message', action: 'send_message', tone: 'secondary' },
            ],
        });

        if (!markup.includes('Send Message')) {
            throw new Error('expected opportunity chat card markup to include Send Message');
        }
        if (markup.includes('Open Record')) {
            throw new Error('expected open-record button to be omitted from already-open chat cards');
        }
        if (!markup.includes("triggerLeadCardSendMessage('opportunity', 'OPP1', 'Fleet Renewal')")) {
            throw new Error('expected opportunity chat card Send Message action to reuse the existing card handler');
        }

        context.triggerLeadCardSendMessage('opportunity', 'OPP1', 'Fleet Renewal');

        const activeObject = vm.runInContext('aiAgentActiveSelectionObject', context);
        const selectedIds = vm.runInContext("Array.from(aiAgentSelectionState.opportunity || [])", context);
        const selectedName = vm.runInContext("aiAgentSelectionMeta.opportunity && aiAgentSelectionMeta.opportunity.get('OPP1')", context);

        if (activeObject !== 'opportunity') {
            throw new Error(`expected Send Message action to activate opportunity selection, got ${activeObject}`);
        }
        if (selectedIds.length !== 1 || selectedIds[0] !== 'OPP1') {
            throw new Error(`expected Send Message action to seed opportunity selection, got ${selectedIds}`);
        }
        if (selectedName !== 'Fleet Renewal') {
            throw new Error(`expected Send Message action to preserve display name, got ${selectedName}`);
        }
        if (quickMessages.length !== 1 || quickMessages[0] !== 'Send Message') {
            throw new Error(`expected Send Message action to trigger the chat-native messaging path, got ${quickMessages}`);
        }
        """
    )


def test_opportunity_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'opportunity';", context);
        vm.runInContext("aiAgentSelectionState.opportunity = new Set(['OPP1']);", context);
        vm.runInContext("aiAgentSelectionMeta.opportunity = new Map([['OPP1', 'Fleet Renewal']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Fleet Renewal')) {
            throw new Error('expected opportunity selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected opportunity selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage opportunity OPP1') {
            throw new Error(`expected opportunity selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from opportunity selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_product_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'product';", context);
        vm.runInContext("aiAgentSelectionState.product = new Set(['PROD1']);", context);
        vm.runInContext("aiAgentSelectionMeta.product = new Map([['PROD1', 'Premium Plan']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected product selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Premium Plan')) {
            throw new Error('expected product selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected product selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage product PROD1') {
            throw new Error(`expected product selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from product selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_asset_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'asset';", context);
        vm.runInContext("aiAgentSelectionState.asset = new Set(['ASSET1']);", context);
        vm.runInContext("aiAgentSelectionMeta.asset = new Map([['ASSET1', 'Executive Demo']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected asset selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Executive Demo')) {
            throw new Error('expected asset selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected asset selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage asset ASSET1') {
            throw new Error(`expected asset selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from asset selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_brand_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'brand';", context);
        vm.runInContext("aiAgentSelectionState.brand = new Set(['BRAND1']);", context);
        vm.runInContext("aiAgentSelectionMeta.brand = new Map([['BRAND1', 'Hyundai']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected brand selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Hyundai')) {
            throw new Error('expected brand selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected brand selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage brand BRAND1') {
            throw new Error(`expected brand selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from brand selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_model_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'model';", context);
        vm.runInContext("aiAgentSelectionState.model = new Set(['MODEL1']);", context);
        vm.runInContext("aiAgentSelectionMeta.model = new Map([['MODEL1', 'Sonata']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected model selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Sonata')) {
            throw new Error('expected model selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected model selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage model MODEL1') {
            throw new Error(`expected model selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from model selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_message_template_selection_open_routes_through_chat_and_skips_direct_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'message_template';", context);
        vm.runInContext("aiAgentSelectionState.message_template = new Set(['TEMPLATE1']);", context);
        vm.runInContext("aiAgentSelectionMeta.message_template = new Map([['TEMPLATE1', 'Spring Promo']]);", context);

        context.triggerSelectionOpen();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected template selection open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Spring Promo')) {
            throw new Error('expected template selection open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected template selection open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage message_template TEMPLATE1') {
            throw new Error(`expected template selection open to send Manage query, got ${context.__sentQuery}`);
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no direct workspace open from template selection trigger, got ${workspaceCalls.length}`);
        }
        """
    )


def test_card_delete_confirmation_appends_in_chat_and_scrolls_into_view_without_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        context.triggerSnapshotDelete('contact', 'CONTACT1', 'Ada Kim');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one delete confirmation message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected delete confirmation to be an agent chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Are you sure you want to delete **Ada Kim**?')) {
            throw new Error('expected card delete confirmation to appear in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected card delete confirmation to scroll the latest chat area into view');
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no workspace open during card delete confirmation, got ${workspaceCalls.length}`);
        }
        """
    )


def test_selection_delete_confirmation_appends_in_chat_and_scrolls_into_view_without_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'opportunity';", context);
        vm.runInContext("aiAgentSelectionState.opportunity = new Set(['OPP1']);", context);
        vm.runInContext("aiAgentSelectionMeta.opportunity = new Map([['OPP1', 'Fleet Renewal']]);", context);

        context.triggerSelectionDelete();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one selection delete confirmation message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected selection delete confirmation to be an agent chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Are you sure you want to delete **Fleet Renewal**?')) {
            throw new Error('expected selection delete confirmation to appear in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected selection delete confirmation to scroll the latest chat area into view');
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected no workspace open during selection delete confirmation, got ${workspaceCalls.length}`);
        }
        """
    )


def test_product_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'product',
            record_id: 'PROD1',
            redirect_url: '/products/PROD1',
            text: 'Product **Premium Plan** is now open.',
            chat_card: { title: 'Premium Plan' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage product PROD1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final product result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Product **Premium Plan** is now open.')) {
            throw new Error('expected latest product open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected product non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected product workspace open to preserve chat focus');
        }
        """
    )


def test_asset_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'asset',
            record_id: 'ASSET1',
            redirect_url: '/assets/ASSET1',
            text: 'Asset **Executive Demo** is now open.',
            chat_card: { title: 'Executive Demo' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage asset ASSET1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final asset result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Asset **Executive Demo** is now open.')) {
            throw new Error('expected latest asset open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected asset non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected asset workspace open to preserve chat focus');
        }
        """
    )


def test_brand_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'brand',
            record_id: 'BRAND1',
            redirect_url: '/vehicle_specifications/BRAND1',
            text: 'Brand **Hyundai** is now open.',
            chat_card: { title: 'Hyundai' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage brand BRAND1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final brand result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Brand **Hyundai** is now open.')) {
            throw new Error('expected latest brand open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected brand non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected brand workspace open to preserve chat focus');
        }
        """
    )


def test_model_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'model',
            record_id: 'MODEL1',
            redirect_url: '/models/MODEL1',
            text: 'Model **Sonata** is now open.',
            chat_card: { title: 'Sonata' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage model MODEL1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final model result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Model **Sonata** is now open.')) {
            throw new Error('expected latest model open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected model non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected model workspace open to preserve chat focus');
        }
        """
    )


def test_message_template_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'message_template',
            record_id: 'TEMPLATE1',
            redirect_url: '/message_templates/TEMPLATE1',
            text: 'Message Template **Spring Promo** is now open.',
            chat_card: { title: 'Spring Promo' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage message_template TEMPLATE1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final template result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Message Template **Spring Promo** is now open.')) {
            throw new Error('expected latest template open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected template non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected template workspace open to preserve chat focus');
        }
        """
    )


def test_lead_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'lead',
            record_id: 'LEAD1',
            redirect_url: '/leads/LEAD1',
            text: 'Lead **Ada Kim** is now open.',
            chat_card: { title: 'Ada Kim' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage lead LEAD1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final lead result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Lead **Ada Kim** is now open.')) {
            throw new Error('expected latest lead open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected lead non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected lead workspace open to preserve chat focus');
        }
        """
    )


def test_lead_chat_form_submit_open_record_removes_submitting_state_and_skips_workspace_open():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.submitAiAgentFormResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'lead',
            record_id: 'LEAD1',
            redirect_url: '/leads/LEAD1',
            text: 'Lead **Ada Kim** has been updated. The refreshed record is open below.',
            chat_card: { title: 'Ada Kim' },
        });

        const card = new context.__FakeElement('div');
        card.classList.add('agent-chat-form-card');
        const form = new context.__FakeElement('form');
        form.dataset.formId = 'lead:edit:LEAD1';
        form.dataset.objectType = 'lead';
        form.dataset.mode = 'edit';
        form.dataset.recordId = 'LEAD1';
        form.closest = (selector) => selector === '.agent-chat-form-card' ? card : null;
        form.querySelector = (selector) => {
            if (selector === 'button[type="submit"]') return submitButton;
            return null;
        };
        form.querySelectorAll = () => [statusField];

        const submitButton = new context.__FakeElement('button');
        submitButton.disabled = false;
        submitButton.type = 'submit';
        const statusField = new context.__FakeElement('input');
        statusField.name = 'status';
        statusField.value = 'Qualified';
        const workspaceLoading = context.document.getElementById('ai-agent-workspace-loading');
        workspaceLoading.classList.remove('agent-hidden');
        const globalLoading = new context.__FakeElement('div', 'sf-global-loading');
        globalLoading.style.display = 'flex';
        context.__elements.set('sf-global-loading', globalLoading);

        card.remove = () => {
            card.__removed = true;
        };

        const event = {
            preventDefault() {},
            target: form,
        };

        const result = await context.submitAgentChatForm(event);

        if (result !== false) {
            throw new Error(`expected submitAgentChatForm to return false, got ${result}`);
        }
        if (card.__removed !== true) {
            throw new Error('expected lead chat form card to be removed after OPEN_RECORD response');
        }
        if (card.classList.contains('is-submitting')) {
            throw new Error('expected lead chat form submitting state to be cleared');
        }
        if (submitButton.disabled !== false) {
            throw new Error('expected lead submit button to be re-enabled');
        }
        if (!workspaceLoading.classList.contains('agent-hidden')) {
            throw new Error('expected lingering workspace loading indicator to be hidden after lead save');
        }
        if (globalLoading.style.display !== 'none') {
            throw new Error('expected lingering global saving overlay to be hidden after lead save');
        }
        if (workspaceCalls.length !== 0) {
            throw new Error(`expected lead chat form submit to skip workspace open, got ${workspaceCalls.length}`);
        }

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one appended agent message after lead save, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected lead save result to append an agent message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Lead **Ada Kim** has been updated.')) {
            throw new Error('expected lead save result text to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected lead save result to keep attention on the latest chat area');
        }
        """
    )


def test_contact_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'contact',
            record_id: 'CONTACT1',
            redirect_url: '/contacts/CONTACT1',
            text: 'Contact **Ada Kim** is now open.',
            chat_card: { title: 'Ada Kim' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage contact CONTACT1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final contact result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Contact **Ada Kim** is now open.')) {
            throw new Error('expected latest contact open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected contact non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected contact workspace open to preserve chat focus');
        }
        """
    )


def test_opportunity_non_submit_open_record_appends_latest_chat_result_and_preserves_chat_focus():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'OPEN_RECORD',
            object_type: 'opportunity',
            record_id: 'OPP1',
            redirect_url: '/opportunities/OPP1',
            text: 'Opportunity **Fleet Renewal** is now open.',
            chat_card: { title: 'Fleet Renewal' },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Manage opportunity OPP1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected only the final opportunity result to remain in chat, got ${body.children.length} nodes`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Opportunity **Fleet Renewal** is now open.')) {
            throw new Error('expected latest opportunity open result to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected opportunity non-submit OPEN_RECORD to keep attention on the latest chat area');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected opportunity workspace open to preserve chat focus');
        }
        """
    )


def test_asset_chat_card_omits_redundant_open_record_button():
    _run_node_dom_test(
        """
        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'asset',
            record_id: 'ASSET1',
            title: 'Executive Demo',
            subtitle: 'Asset · Active',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Edit', action: 'edit', tone: 'secondary' },
                { label: 'Delete', action: 'delete', tone: 'danger' },
            ],
        });

        if (markup.includes('Open Record')) {
            throw new Error('expected asset chat card to omit the redundant open-record button');
        }
        """
    )


def test_brand_chat_card_omits_redundant_open_record_button():
    _run_node_dom_test(
        """
        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'brand',
            record_id: 'BRAND1',
            title: 'Hyundai',
            subtitle: 'Brand · Brand',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Edit', action: 'edit', tone: 'secondary' },
                { label: 'Delete', action: 'delete', tone: 'danger' },
            ],
        });

        if (markup.includes('Open Record')) {
            throw new Error('expected brand chat card to omit the redundant open-record button');
        }
        """
    )


def test_model_chat_card_omits_redundant_open_record_button():
    _run_node_dom_test(
        """
        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'model',
            record_id: 'MODEL1',
            title: 'Sonata',
            subtitle: 'Model · Hyundai',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Edit', action: 'edit', tone: 'secondary' },
                { label: 'Delete', action: 'delete', tone: 'danger' },
            ],
        });

        if (markup.includes('Open Record')) {
            throw new Error('expected model chat card to omit the redundant open-record button');
        }
        """
    )


def test_message_template_chat_card_preview_image_uses_existing_preview_helper():
    _run_node_dom_test(
        """
        const modal = new context.__FakeElement('div', 'ai-agent-image-modal');
        modal.classList.add('agent-hidden');
        const image = new context.__FakeElement('img', 'ai-agent-image-preview');
        const title = new context.__FakeElement('div', 'ai-agent-image-title');
        const fallback = new context.__FakeElement('div', 'ai-agent-image-fallback');
        context.__elements.set('ai-agent-image-modal', modal);
        context.__elements.set('ai-agent-image-preview', image);
        context.__elements.set('ai-agent-image-title', title);
        context.__elements.set('ai-agent-image-fallback', fallback);

        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'message_template',
            record_id: 'TEMPLATE1',
            title: 'Spring Promo',
            subtitle: 'Template · MMS',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Preview Image', action: 'preview_image', tone: 'secondary', url: '/static/uploads/templates/spring.jpg' },
                { label: 'Use In Send Message', action: 'use_in_send', tone: 'secondary' },
            ],
        });

        if (!markup.includes("openAgentImagePreview('/static/uploads/templates/spring.jpg', 'Template Preview')")) {
            throw new Error('expected template chat card preview to use the existing preview helper');
        }

        context.openAgentImagePreview('/static/uploads/templates/spring.jpg', 'Template Preview');

        if (modal.classList.contains('agent-hidden')) {
            throw new Error('expected preview helper to open the image modal');
        }
        if (image.src !== '/static/uploads/templates/spring.jpg') {
            throw new Error(`expected preview helper to set image src, got ${image.src}`);
        }
        if (title.textContent !== 'Template Preview') {
            throw new Error(`expected preview helper to set title, got ${title.textContent}`);
        }
        """
    )


def test_message_template_chat_card_use_in_send_message_reuses_existing_handoff_path():
    _run_node_dom_test(
        """
        const session = {};
        context.sessionStorage.setItem = (key, value) => {
            session[key] = value;
        };
        context.sessionStorage.getItem = (key) => session[key] || null;

        const composerCalls = [];
        context.appendAgentSendMessageComposer = (text, payload = {}) => {
            composerCalls.push({ text, payload });
        };

        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'message_template',
            record_id: 'TEMPLATE1',
            title: 'Spring Promo',
            subtitle: 'Template · MMS',
            fields: [],
            actions: [
                { label: 'Open Record', action: 'open', tone: 'primary' },
                { label: 'Use In Send Message', action: 'use_in_send', tone: 'secondary' },
            ],
        });

        if (!markup.includes("startTemplateSendFromAgent('TEMPLATE1')")) {
            throw new Error('expected template chat card Use In Send Message to reuse the existing handoff path');
        }

        context.startTemplateSendFromAgent('TEMPLATE1');

        if (composerCalls.length !== 1) {
            throw new Error(`expected one AI-native send composer call, got ${composerCalls.length}`);
        }
        if (composerCalls[0].payload.templateId !== 'TEMPLATE1') {
            throw new Error(`expected template handoff to preserve template id, got ${composerCalls[0].payload.templateId}`);
        }
        if (!composerCalls[0].text.includes('Template prepared for Send Message')) {
            throw new Error('expected template send action to explain the composer handoff');
        }
        """
    )


def test_send_message_intent_appends_ai_native_composer():
    _run_node_dom_test(
        """
        const composerCalls = [];
        context.appendAgentSendMessageComposer = (text, payload = {}) => {
            composerCalls.push({ text, payload });
        };
        context.fetchAiAgentResponse = async () => ({
            intent: 'SEND_MESSAGE',
            text: 'Opening the messaging flow for 1 selected contact record(s).',
            redirect_url: '/messaging/ui?sourceObject=contact&count=1',
            template_id: 'TEMPLATE1',
            selection: { object_type: 'contact', ids: ['CONTACT1'] },
        });

        await context.sendAiMessage('Send Message');

        if (composerCalls.length !== 1) {
            throw new Error(`expected one composer handoff, got ${composerCalls.length}`);
        }
        if (composerCalls[0].payload.templateId !== 'TEMPLATE1') {
            throw new Error(`expected composer handoff to keep template id, got ${composerCalls[0].payload.templateId}`);
        }
        if (JSON.stringify(composerCalls[0].payload.selection) !== JSON.stringify({ object_type: 'contact', ids: ['CONTACT1'] })) {
            throw new Error(`expected composer handoff to keep selection payload, got ${JSON.stringify(composerCalls[0].payload.selection)}`);
        }
        """
    )


def test_selection_triggered_send_message_routes_into_ai_native_composer():
    _run_node_dom_test(
        """
        const composerCalls = [];
        context.appendAgentSendMessageComposer = (text, payload = {}) => {
            composerCalls.push({ text, payload });
        };
        context.sendQuickMessage = (text) => {
            if (text !== 'Send Message') {
                throw new Error(`expected triggerSelectionMessaging to request Send Message, got ${text}`);
            }
            context.appendAgentSendMessageComposer(
                'Opening the messaging flow for 1 selected contact record(s).',
                { selection: context.buildSelectionPayload() }
            );
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'contact';", context);
        vm.runInContext("aiAgentSelectionState.contact = new Set(['CONTACT1']);", context);
        vm.runInContext("aiAgentSelectionMeta.contact = new Map([['CONTACT1', 'Ada Kim']]);", context);

        context.triggerSelectionMessaging();

        if (composerCalls.length !== 1) {
            throw new Error(`expected one composer handoff, got ${composerCalls.length}`);
        }
        if (JSON.stringify(composerCalls[0].payload.selection) !== JSON.stringify({ object_type: 'contact', ids: ['CONTACT1'], labels: ['Ada Kim'] })) {
            throw new Error(`expected selection-triggered send to preserve selection payload, got ${JSON.stringify(composerCalls[0].payload.selection)}`);
        }
        """
    )


def test_send_message_actions_render_as_contact_administrator_when_ai_agent_messaging_is_blocked():
    _run_node_dom_test(
        """
        vm.runInContext(`
            aiAgentMessagingAvailabilityState.checked = true;
            aiAgentMessagingAvailabilityState.available = false;
            aiAgentMessagingAvailabilityState.message = 'Message sending is disabled on this deployment. Contact the administrator.';
        `, context);

        const markup = context.renderAgentChatCard({
            type: 'record_paste',
            object_type: 'contact',
            record_id: 'CONTACT1',
            title: 'Ada Kim',
            subtitle: 'Contact · Qualified',
            fields: [],
            actions: [
                { label: 'Send Message', action: 'send_message', tone: 'secondary' },
            ],
        });

        if (!markup.includes('Contact Administrator')) {
            throw new Error('expected blocked AI agent message action to render Contact Administrator label');
        }
        if (!markup.includes('disabled')) {
            throw new Error('expected blocked AI agent message action to render as disabled');
        }
        """
    )


def test_send_quick_message_send_message_stops_when_ai_agent_messaging_is_blocked():
    _run_node_dom_test(
        """
        vm.runInContext(`
            aiAgentMessagingAvailabilityState.checked = true;
            aiAgentMessagingAvailabilityState.available = false;
            aiAgentMessagingAvailabilityState.message = 'Message sending is disabled on this deployment. Contact the administrator.';
        `, context);

        const sentQueries = [];
        context.sendAiMessage = (query) => {
            sentQueries.push(query);
        };

        context.sendQuickMessage('Send Message');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one blocked-state agent message, got ${body.children.length}`);
        }
        if (!body.children[0].innerHTML.includes('Contact the administrator')) {
            throw new Error('expected blocked-state agent message to mention administrator contact');
        }
        if (sentQueries.length !== 0) {
            throw new Error(`expected no send-message query dispatch when blocked, got ${sentQueries}`);
        }
        """
    )


def test_jump_button_is_visible_when_user_is_not_near_bottom_and_hides_at_bottom():
    _run_node_dom_test(
        """
        const body = context.document.getElementById('ai-agent-body');
        const jump = new context.__FakeElement('button', 'ai-agent-jump-btn');
        context.__elements.set('ai-agent-jump-btn', jump);

        body.scrollHeight = 1600;
        body.clientHeight = 600;
        body.scrollTop = 200;
        context.updateAiAgentJumpButtonVisibility();

        if (!jump.classList.contains('is-visible')) {
            throw new Error('expected jump button to appear when user is scrolled away from the latest reply');
        }

        body.scrollTop = 1010;
        context.updateAiAgentJumpButtonVisibility();

        if (jump.classList.contains('is-visible')) {
            throw new Error('expected jump button to hide when user is already at the bottom');
        }
        """
    )


def test_jump_button_scrolls_to_latest_agent_message_start_not_forced_bottom():
    _run_node_dom_test(
        """
        const body = context.document.getElementById('ai-agent-body');
        const latest = new context.__FakeElement('div');
        latest.className = 'msg-agent';
        body.querySelectorAll = (selector) => selector === '.msg-agent' ? [latest] : [];

        context.jumpToLatestAgentMessage();

        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected jump button to scroll the latest agent message into view');
        }
        if (body.scrollToCalls.length !== 0) {
            throw new Error('expected jump button not to force a raw bottom scroll when a latest agent node exists');
        }
        """
    )


def test_maximize_ai_agent_preserves_existing_scroll_position():
    _run_node_dom_test(
        """
        const win = context.document.createElement('div');
        win.id = 'ai-agent-window';
        context.__elements.set('ai-agent-window', win);

        const body = context.document.getElementById('ai-agent-body');
        body.scrollTop = 640;

        context.maximizeAiAgent();

        if (!win.classList.contains('agent-maximized')) {
            throw new Error('expected maximizeAiAgent to toggle the maximized class');
        }
        if (body.scrollToCalls.length !== 0) {
            throw new Error('expected maximizeAiAgent not to force-scroll the chat body to the top');
        }
        if (body.scrollTop !== 640) {
            throw new Error(`expected maximizeAiAgent to preserve existing scrollTop, got ${body.scrollTop}`);
        }
        """
    )


def test_message_template_modal_respects_staged_image_removal_in_ai_agent():
    source = JS_PATH.read_text(encoding="utf-8")

    assert "function hasPendingInlineImageRemoval(form) {" in source
    assert "if (context.objectType === 'message_template' && hasPendingInlineImageRemoval(form)) {" in source
    assert "const removeImageInput = form.querySelector('#modal-form-remove-image');" in source
    assert "const removeRequested = removeImageInput?.value === 'true';" in source
    assert "helper.textContent = removeRequested ? 'Image removal staged. Click Save to apply it.' : '';" in source
