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


def test_asset_chat_card_open_record_uses_display_first_chat_routing():
    _run_node_dom_test(
        """
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

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

        if (!markup.includes("sendAiMessageWithDisplay('Open Executive Demo', 'Manage asset ASSET1')")) {
            throw new Error('expected asset chat card Open Record to use display-first Manage routing');
        }

        context.sendAiMessageWithDisplay('Open Executive Demo', 'Manage asset ASSET1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected asset card open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Executive Demo')) {
            throw new Error('expected asset card open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected asset card open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage asset ASSET1') {
            throw new Error(`expected asset card open to send Manage query, got ${context.__sentQuery}`);
        }
        """
    )


def test_brand_chat_card_open_record_uses_display_first_chat_routing():
    _run_node_dom_test(
        """
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

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

        if (!markup.includes("sendAiMessageWithDisplay('Open Hyundai', 'Manage brand BRAND1')")) {
            throw new Error('expected brand chat card Open Record to use display-first Manage routing');
        }

        context.sendAiMessageWithDisplay('Open Hyundai', 'Manage brand BRAND1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected brand card open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Hyundai')) {
            throw new Error('expected brand card open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected brand card open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage brand BRAND1') {
            throw new Error(`expected brand card open to send Manage query, got ${context.__sentQuery}`);
        }
        """
    )


def test_model_chat_card_open_record_uses_display_first_chat_routing():
    _run_node_dom_test(
        """
        context.sendAiMessage = (query) => {
            context.__sentQuery = query;
        };

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

        if (!markup.includes("sendAiMessageWithDisplay('Open Sonata', 'Manage model MODEL1')")) {
            throw new Error('expected model chat card Open Record to use display-first Manage routing');
        }

        context.sendAiMessageWithDisplay('Open Sonata', 'Manage model MODEL1');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one latest chat message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-user') {
            throw new Error(`expected model card open to append a user chat message, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Open Sonata')) {
            throw new Error('expected model card open to render the display text in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected model card open to scroll the latest chat area into view');
        }
        if (context.__sentQuery !== 'Manage model MODEL1') {
            throw new Error(`expected model card open to send Manage query, got ${context.__sentQuery}`);
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

        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
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

        if (session.aiAgentMessageTemplate !== 'TEMPLATE1') {
            throw new Error(`expected handoff to seed template selection, got ${session.aiAgentMessageTemplate}`);
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one messaging workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].url !== '/messaging/ui?sourceObject=message_template') {
            throw new Error(`expected existing messaging handoff url, got ${workspaceCalls[0].url}`);
        }
        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1 || !body.children[0].innerHTML.includes('Template prepared for Send Message')) {
            throw new Error('expected existing template handoff confirmation message to be appended in chat');
        }
        """
    )


def test_send_message_intent_appends_chat_feedback_before_workspace_open_and_preserves_focus():
    _run_node_dom_test(
        """
        const session = {};
        context.sessionStorage.setItem = (key, value) => {
            session[key] = value;
        };
        context.sessionStorage.removeItem = (key) => {
            delete session[key];
        };

        const workspaceCalls = [];
        context.fetchAiAgentResponse = async () => ({
            intent: 'SEND_MESSAGE',
            text: 'Opening the messaging flow for 1 selected contact record(s).',
            redirect_url: '/messaging/ui?sourceObject=contact&count=1',
            template_id: 'TEMPLATE1',
            selection: { object_type: 'contact', ids: ['CONTACT1'] },
        });
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };

        await context.sendAiMessage('Send Message');

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one agent send-handoff message, got ${body.children.length}`);
        }

        const latest = body.children[0];
        if (latest.className !== 'msg-agent') {
            throw new Error(`expected latest send handoff message to be agent chat, got ${latest.className}`);
        }
        if (!latest.innerHTML.includes('Opening the messaging flow for 1 selected contact record(s).')) {
            throw new Error('expected send handoff confirmation to be appended in chat');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected send handoff confirmation to scroll the latest chat area into view');
        }
        if (workspaceCalls.length !== 1) {
            throw new Error(`expected one messaging workspace open call, got ${workspaceCalls.length}`);
        }
        if (workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected send handoff workspace open to preserve chat focus');
        }
        if (session.aiAgentMessageTemplate !== 'TEMPLATE1') {
            throw new Error(`expected send handoff to keep template id, got ${session.aiAgentMessageTemplate}`);
        }
        if (session.aiAgentMessageSelection !== JSON.stringify({ object_type: 'contact', ids: ['CONTACT1'] })) {
            throw new Error(`expected send handoff to keep selection payload, got ${session.aiAgentMessageSelection}`);
        }
        """
    )


def test_selection_triggered_send_message_appends_latest_confirmation_and_opens_after_it():
    _run_node_dom_test(
        """
        const workspaceCalls = [];
        context.openAgentWorkspace = (url, title, options = {}) => {
            workspaceCalls.push({ url, title, options });
        };
        context.sendQuickMessage = (text) => {
            if (text !== 'Send Message') {
                throw new Error(`expected triggerSelectionMessaging to request Send Message, got ${text}`);
            }
            context.completeAgentSendMessageHandoff(
                '/messaging/ui?sourceObject=contact&count=1',
                'Opening the messaging flow for 1 selected contact record(s).',
                null,
                context.buildSelectionPayload()
            );
        };

        vm.runInContext("aiAgentActiveSelectionObject = 'contact';", context);
        vm.runInContext("aiAgentSelectionState.contact = new Set(['CONTACT1']);", context);
        vm.runInContext("aiAgentSelectionMeta.contact = new Map([['CONTACT1', 'Ada Kim']]);", context);

        context.triggerSelectionMessaging();

        const body = context.document.getElementById('ai-agent-body');
        if (body.children.length !== 1) {
            throw new Error(`expected one agent send confirmation, got ${body.children.length}`);
        }
        const latest = Array.from(body.children).find(node =>
            node.className === 'msg-agent' &&
            node.innerHTML.includes('Opening the messaging flow for 1 selected contact record(s).')
        );
        if (!latest) {
            throw new Error('expected send confirmation after selection-triggered send');
        }
        if (latest.scrollIntoViewCalls.length !== 1) {
            throw new Error('expected selection-triggered send confirmation to scroll into view');
        }
        if (workspaceCalls.length !== 1 || workspaceCalls[0].options.preserveChatFocus !== true) {
            throw new Error('expected selection-triggered send to open messaging workspace with preserved chat focus');
        }
        """
    )
