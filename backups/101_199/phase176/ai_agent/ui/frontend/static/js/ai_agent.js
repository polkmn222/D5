let isAiAgentMinimized = false;
let isAiAgentMaximized = false;
let agentTableStyle = 'default';
let aiAgentConversationId = createConversationId();
let aiAgentSelectionState = {};
let aiAgentSelectionMeta = {};
let aiAgentActiveSelectionObject = null;
let aiAgentActiveSelectionContainer = null;
let localAgentResultTables = {};
let aiAgentLanguagePreference = localStorage.getItem('aiAgentLanguagePreference') || 'eng';
const AI_AGENT_DEFAULT_BODY_HTML = `
    <div style="text-align: center; color: #706e6b; font-size: 0.75rem; margin-bottom: 20px; font-weight: 500;">CONVERSATION STARTED</div>
    <div class="msg-agent">
        <div class="msg-agent-header">
            <div class="msg-agent-icon">🤖</div>
            <span style="font-size: 0.8rem; font-weight: 700; color: #3e3e3c;">AI AGENT</span>
        </div>
        <div class="msg-agent-content">
            <div class="msg-agent-text">Hello! I'm your AI Agent. I can help you manage <strong>Leads</strong>, <strong>Contacts</strong>, <strong>Opportunities</strong>, <strong>Products</strong>, and more with natural English commands.</div>
            <div class="agent-welcome-tips">
                <button class="welcome-tip" onclick="sendQuickMessage('create lead')">Create a lead</button>
                <button class="welcome-tip" onclick="sendQuickMessage('show all contacts')">Browse contacts</button>
                <button class="welcome-tip" onclick="sendQuickMessage('show the lead I just created')">Open last created record</button>
            </div>
        </div>
    </div>
    <div id="ai-agent-selection-bar" class="selection-bar is-hidden">
        <div class="selection-bar-copy">
            <span class="selection-bar-title">Selection Ready</span>
            <span id="ai-agent-selection-summary">No records selected</span>
            <span id="ai-agent-selection-detail" class="selection-bar-detail">Select one or more records, then choose Open, Edit, Delete, or Send Message.</span>
        </div>
        <div class="selection-bar-actions">
            <button class="selection-action-btn" onclick="triggerSelectionOpen()">Open</button>
            <button class="selection-action-btn" onclick="triggerSelectionEdit()">Edit</button>
            <button class="selection-action-btn selection-action-danger" onclick="triggerSelectionDelete()">Delete</button>
            <button class="selection-action-btn selection-action-primary" onclick="triggerSelectionMessaging()">Send Message</button>
        </div>
    </div>
`;

const AGENT_TABLE_SCHEMAS = {
    lead: ['display_name', 'phone', 'status', 'model', 'created_at'],
    contact: ['display_name', 'phone', 'email', 'tier', 'created_at'],
    opportunity: ['name', 'contact_display_name', 'contact_phone', 'stage', 'amount', 'model_name'],
    product: ['name', 'brand', 'model', 'category', 'base_price'],
    asset: ['name', 'vin', 'status', 'brand', 'model'],
    brand: ['name', 'record_type', 'description'],
    model: ['name', 'brand', 'description'],
    message_template: ['name', 'record_type', 'subject', 'content', 'has_image'],
    message_send: ['contact', 'direction', 'status', 'sent_at'],
};

const AGENT_TABLE_LABELS = {
    display_name: 'Name',
    first_name: 'First Name',
    last_name: 'Last Name',
    phone: 'Phone',
    email: 'Email',
    status: 'Status',
    is_followed: 'Followed',
    tier: 'Tier',
    last_interaction_at: 'Last Interaction',
    name: 'Name',
    stage: 'Stage',
    temperature: 'Temperature',
    amount: 'Amount',
    close_date: 'Close Date',
    updated_at: 'Updated',
    brand: 'Brand',
    model: 'Model',
    category: 'Category',
    base_price: 'Base Price',
    vin: 'VIN',
    purchase_date: 'Purchase Date',
    record_type: 'Type',
    content: 'Content',
    image_url: 'Image',
    contact: 'Contact',
    direction: 'Direction',
    sent_at: 'Sent At',
    contact_display_name: 'Contact Name',
    contact_phone: 'Contact Phone',
    model_name: 'Model',
    has_image: 'Image',
};

function getAgentFieldValue(row, key) {
    if (key === 'display_name') {
        return [row.first_name, row.last_name].filter(Boolean).join(' ').trim() || row.name || '-';
    }
    if (key === 'has_image') {
        return (row.image_url || row.attachment_id) ? '✓' : '✕';
    }
    return row[key] ?? '-';
}

function formatAgentFieldValue(key, value) {
    if (value === null || value === undefined || value === '') return '-';
    if (key === 'is_followed') return value ? 'Yes' : 'No';
    if (['amount', 'base_price'].includes(key)) {
        const number = Number(value);
        return Number.isFinite(number) ? `₩ ${number.toLocaleString()}` : value;
    }
    if (['created_at', 'updated_at', 'close_date', 'last_interaction_at', 'sent_at', 'purchase_date'].includes(key)) {
        return String(value).slice(0, 10);
    }
    if (key === 'content') {
        const text = String(value);
        return text.length > 80 ? `${text.slice(0, 77)}...` : text;
    }
    if (key === 'has_image') {
        return value;
    }
    return value;
}

function getAiAgentUiCopy() {
    if (aiAgentLanguagePreference === 'kor') {
        return {
            trigger: 'AI Agent 열기',
            subtitle: '레코드 조회, 후속 관리, 메시지 전송을 돕는 CRM 도우미입니다.',
            reset: '대화 초기화',
            kicker: 'AI 빠른 가이드',
            guideTitle: '원하는 작업부터 시작하세요',
            guideCopy: '직접적인 CRM 작업을 고른 뒤, 채팅에서 다음 단계를 이어가세요.',
            browseTitle: '레코드 조회',
            allLeads: '전체 리드',
            allLeadsCopy: '최신 리드 목록 열기',
            allContacts: '전체 연락처',
            allContactsCopy: '연락처 레코드 확인',
            allOpps: '전체 기회',
            allOppsCopy: '현재 파이프라인 보기',
            recentOpps: '최근 기회',
            recentOppsCopy: '최근 업데이트 딜 확인',
            actionsTitle: 'AI 작업',
            recommend: 'AI Recommend',
            recommendCopy: '추천 기회 보기',
            changeRecommend: '추천 로직 변경',
            changeRecommendCopy: '홈 카드 추천 기준 바꾸기',
            sendMessage: '메시지 보내기',
            sendMessageCopy: '선택한 레코드로 메시지 흐름 열기',
            topDeals: '상위 딜',
            topDealsCopy: '핵심 기회 보기',
            myLeads: '내 리드',
            myLeadsCopy: '개인 리드 빠르게 보기',
            examples: '예시',
            examplesCopy: '`리드 생성해줘` · `전체 연락처 보여줘` · `방금 만든 리드 열어줘` · `그 연락처 삭제해줘`',
            welcome: "안녕하세요! 저는 AI Agent입니다. 자연어로 <strong>리드</strong>, <strong>연락처</strong>, <strong>기회</strong>, <strong>상품</strong> 등을 도와드릴게요.",
            createLead: "리드 만들기",
            browseContacts: "연락처 보기",
            openLast: "최근 생성 레코드 열기",
            inputPlaceholder: "메시지나 명령을 입력하세요...",
            sendMessageGuide: "누구에게 메시지를 보낼까요? 최근 생성된 리드, 전체 연락처, 최근 생성된 연락처를 먼저 불러오고 레코드를 선택해 주세요.",
            languageToast: "AI Agent language set to Korean.",
            selectionTitle: '선택 준비됨',
            open: '열기',
            edit: '수정',
            delete: '삭제',
            send: '메시지 보내기',
        };
    }

    return {
        trigger: 'Ask AI Agent',
        subtitle: 'English-first CRM copilot for records, follow-ups, and messaging.',
        reset: 'Reset Agent',
        kicker: 'AI Quick Guide',
        guideTitle: 'Start with a clear task',
        guideCopy: 'Start with a direct CRM task, then refine the next step in chat.',
        browseTitle: 'Browse Records',
        allLeads: 'All Leads',
        allLeadsCopy: 'Open the latest lead list',
        allContacts: 'All Contacts',
        allContactsCopy: 'Review contact records',
        allOpps: 'All Opportunities',
        allOppsCopy: 'See current pipeline items',
        recentOpps: 'Recent Opps',
        recentOppsCopy: 'Check newly updated deals',
        actionsTitle: 'Agent Actions',
        recommend: 'AI Recommend',
        recommendCopy: 'Surface recommended deals',
        changeRecommend: 'Change AI Recommend',
        changeRecommendCopy: 'Change the recommendation logic for the home card',
        sendMessage: 'Send Message',
        sendMessageCopy: 'Open the messaging flow for selected records',
        topDeals: 'Top Deals',
        topDealsCopy: 'Ask for top-value opportunities',
        myLeads: 'My Leads',
        myLeadsCopy: 'Get a quick personal list',
        examples: 'Examples',
        examplesCopy: '`create lead` · `show all contacts` · `show the lead I just created` · `delete that contact`',
        welcome: "Hello! I'm your AI Agent. I can help you manage <strong>Leads</strong>, <strong>Contacts</strong>, <strong>Opportunities</strong>, <strong>Products</strong>, and more with natural English commands.",
        createLead: "Create a lead",
        browseContacts: "Browse contacts",
        openLast: "Open last created record",
        inputPlaceholder: "Type a message or command...",
        sendMessageGuide: "Who should I send the message to? Try showing recent leads, all contacts, or recently created leads first, then select one or more records.",
        languageToast: "AI Agent language set to English.",
        selectionTitle: 'Selection Ready',
        open: 'Open',
        edit: 'Edit',
        delete: 'Delete',
        send: 'Send Message',
    };
}

function applyAiAgentLanguageUi() {
    const copy = getAiAgentUiCopy();
    const input = document.getElementById('ai-agent-input');
    if (input) input.setAttribute('placeholder', copy.inputPlaceholder);

    const setText = (selector, value) => {
        const node = document.querySelector(selector);
        if (node) node.textContent = value;
    };
    const setHtml = (selector, value) => {
        const node = document.querySelector(selector);
        if (node) node.innerHTML = value;
    };

    setText('[data-ai-agent-trigger-label]', copy.trigger);
    setText('[data-ai-agent-subtitle]', copy.subtitle);
    setText('[data-ai-agent-reset-label]', copy.reset);
    setText('[data-ai-guide-kicker]', copy.kicker);
    setText('[data-ai-guide-title]', copy.guideTitle);
    setText('[data-ai-guide-copy]', copy.guideCopy);
    setText('[data-ai-guide-section-browse]', copy.browseTitle);
    setText('[data-ai-guide-all-leads]', copy.allLeads);
    setText('[data-ai-guide-all-leads-copy]', copy.allLeadsCopy);
    setText('[data-ai-guide-all-contacts]', copy.allContacts);
    setText('[data-ai-guide-all-contacts-copy]', copy.allContactsCopy);
    setText('[data-ai-guide-all-opps]', copy.allOpps);
    setText('[data-ai-guide-all-opps-copy]', copy.allOppsCopy);
    setText('[data-ai-guide-recent-opps]', copy.recentOpps);
    setText('[data-ai-guide-recent-opps-copy]', copy.recentOppsCopy);
    setText('[data-ai-guide-section-actions]', copy.actionsTitle);
    setText('[data-ai-guide-recommend]', copy.recommend);
    setText('[data-ai-guide-recommend-copy]', copy.recommendCopy);
    setText('[data-ai-guide-change-recommend]', copy.changeRecommend);
    setText('[data-ai-guide-change-recommend-copy]', copy.changeRecommendCopy);
    setText('[data-ai-guide-send-message]', copy.sendMessage);
    setText('[data-ai-guide-send-message-copy]', copy.sendMessageCopy);
    setText('[data-ai-guide-top-deals]', copy.topDeals);
    setText('[data-ai-guide-top-deals-copy]', copy.topDealsCopy);
    setText('[data-ai-guide-my-leads]', copy.myLeads);
    setText('[data-ai-guide-my-leads-copy]', copy.myLeadsCopy);
    setText('[data-ai-guide-examples]', copy.examples);
    setText('[data-ai-guide-examples-copy]', copy.examplesCopy);
    setText('[data-ai-selection-title]', copy.selectionTitle);
    setText('[data-ai-selection-open]', copy.open);
    setText('[data-ai-selection-edit]', copy.edit);
    setText('[data-ai-selection-delete]', copy.delete);
    setText('[data-ai-selection-send]', copy.send);

    const welcome = document.querySelector('.msg-agent .msg-agent-text');
    if (welcome) welcome.innerHTML = copy.welcome;

    const tips = document.querySelectorAll('.agent-welcome-tips .welcome-tip');
    if (tips[0]) tips[0].textContent = copy.createLead;
    if (tips[1]) tips[1].textContent = copy.browseContacts;
    if (tips[2]) tips[2].textContent = copy.openLast;

    document.getElementById('ai-agent-lang-eng')?.classList.toggle('is-active', aiAgentLanguagePreference === 'eng');
    document.getElementById('ai-agent-lang-kor')?.classList.toggle('is-active', aiAgentLanguagePreference === 'kor');
}

function setAiAgentLanguage(lang) {
    aiAgentLanguagePreference = lang === 'kor' ? 'kor' : 'eng';
    localStorage.setItem('aiAgentLanguagePreference', aiAgentLanguagePreference);
    applyAiAgentLanguageUi();
    if (typeof showToast === 'function') showToast(getAiAgentUiCopy().languageToast);
}

function normalizeObjectLabel(objectType, count) {
    if (!objectType) return 'records';
    const label = objectType.replace('_', ' ');
    return count === 1 ? label : `${label}s`;
}

function ensureSelectionMeta(objectType) {
    if (!objectType) return null;
    if (!aiAgentSelectionMeta[objectType]) {
        aiAgentSelectionMeta[objectType] = new Map();
    }
    return aiAgentSelectionMeta[objectType];
}

function summarizeSelectionIds(ids) {
    if (!ids || !ids.length) return "Select one or more records, then choose Open, Edit, Delete, or Send Message.";
    const preview = ids.slice(0, 3).join(', ');
    if (ids.length <= 3) {
        return `Selected IDs: ${preview}`;
    }
    return `Selected IDs: ${preview} +${ids.length - 3} more`;
}

function updateSelectionBar() {
    const bar = document.getElementById('ai-agent-selection-bar');
    const summary = document.getElementById('ai-agent-selection-summary');
    const detail = document.getElementById('ai-agent-selection-detail');
    if (!bar || !summary || !detail) return;

    const selection = buildSelectionPayload();
    if (!selection) {
        bar.classList.add('is-hidden');
        summary.textContent = 'No records selected';
        detail.textContent = "Select one or more records, then choose Open, Edit, Delete, or Send Message.";
        return;
    }

    if (aiAgentActiveSelectionContainer) {
        const pagination = aiAgentActiveSelectionContainer.querySelector('.agent-pagination');
        if (pagination && pagination.parentNode === aiAgentActiveSelectionContainer) {
            aiAgentActiveSelectionContainer.insertBefore(bar, pagination);
        } else {
            aiAgentActiveSelectionContainer.appendChild(bar);
        }
    }

    const count = selection.ids.length;
    const label = normalizeObjectLabel(selection.object_type, count);
    const names = selection.labels || [];
    summary.textContent = count === 1
        ? (names[0] || `${label} selected`)
        : `${count} ${label} selected${names.length ? ` · ${names.slice(0, 2).join(', ')}` : ''}`;
    detail.textContent = count === 1
        ? `Choose what to do with ${names[0] || 'this record'}: Open, Edit, Delete, or Send Message.`
        : `Choose what to do with these ${count} ${label}: Delete or Send Message.`;

    const openBtn = bar.querySelector('[data-ai-selection-open]');
    const editBtn = bar.querySelector('[data-ai-selection-edit]');
    const sendBtn = bar.querySelector('[data-ai-selection-send]');
    if (openBtn) openBtn.disabled = count !== 1;
    if (editBtn) editBtn.disabled = count !== 1;
    if (sendBtn) sendBtn.disabled = false;
    bar.classList.remove('is-hidden');
}

function extractAgentWorkspaceMarkup(doc, url) {
    if (url.includes('/messaging/ui')) {
        return doc.querySelector('#messaging-main-view')?.outerHTML || doc.body.innerHTML;
    }
    if (url.includes('/new-modal')) {
        const wrapper = document.createElement('div');
        ['.sf-modal-header', '.sf-modal-body', '.sf-modal-footer'].forEach(selector => {
            const node = doc.querySelector(selector);
            if (node) wrapper.appendChild(node);
        });
        return wrapper.innerHTML || doc.body.innerHTML;
    }

    const wrapper = document.createElement('div');
    ['.detail-header', '.detail-tabs', '#tab-details', '#tab-related'].forEach(selector => {
        const node = doc.querySelector(selector);
        if (node) wrapper.appendChild(node);
    });
    return wrapper.innerHTML || doc.body.innerHTML;
}

function wireAgentWorkspaceInteractions(content, sourceUrl) {
    if (!content) return;
    if (typeof enhanceModalForms === 'function' && sourceUrl.includes('/new-modal')) {
        content.dataset.modalSourceUrl = sourceUrl;
        enhanceModalForms(content);
    }

    content.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            const loading = document.getElementById('ai-agent-workspace-loading');
            if (loading) loading.classList.remove('agent-hidden');
        }, { once: true });
    });

    content.querySelectorAll('script').forEach(script => {
        const replacement = document.createElement('script');
        replacement.textContent = script.textContent;
        document.body.appendChild(replacement);
        replacement.remove();
    });

    content.querySelectorAll('.detail-header .btn, .sf-modal-header .btn').forEach(btn => {
        const text = btn.textContent?.trim().toLowerCase();
        if (text === 'delete') {
            btn.addEventListener('click', event => event.preventDefault());
        }
    });
}

function openAgentWorkspace(url, title) {
    const panel = document.getElementById('ai-agent-workspace');
    const content = document.getElementById('ai-agent-workspace-content');
    const loading = document.getElementById('ai-agent-workspace-loading');
    const heading = document.getElementById('ai-agent-workspace-title');
    if (!panel || !content || !loading || !heading || !url) return;

    heading.textContent = title || 'Record View';
    panel.classList.remove('agent-hidden');
    loading.classList.remove('agent-hidden');
    content.innerHTML = '';
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const extracted = extractAgentWorkspaceMarkup(doc, url);
            content.innerHTML = extracted;
            wireAgentWorkspaceInteractions(content, url);
        })
        .catch(error => {
            console.error(error);
            content.innerHTML = '<div class="sf-card" style="padding:1rem;color:var(--error);">Unable to load this record inside AI Agent.</div>';
        })
        .finally(() => {
            loading.classList.add('agent-hidden');
        });
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function openAgentWorkspaceHtml(title, html) {
    const panel = document.getElementById('ai-agent-workspace');
    const content = document.getElementById('ai-agent-workspace-content');
    const loading = document.getElementById('ai-agent-workspace-loading');
    const heading = document.getElementById('ai-agent-workspace-title');
    if (!panel || !content || !loading || !heading) return;
    heading.textContent = title || 'Record View';
    panel.classList.remove('agent-hidden');
    loading.classList.add('agent-hidden');
    content.innerHTML = html;
    wireAgentWorkspaceInteractions(content, 'inline-html');
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function closeAgentWorkspace() {
    const panel = document.getElementById('ai-agent-workspace');
    const content = document.getElementById('ai-agent-workspace-content');
    const loading = document.getElementById('ai-agent-workspace-loading');
    if (panel) panel.classList.add('agent-hidden');
    if (content) content.innerHTML = '';
    if (loading) loading.classList.add('agent-hidden');
}

function openAgentImagePreview(url, title = 'Template Image') {
    const modal = document.getElementById('ai-agent-image-modal');
    const image = document.getElementById('ai-agent-image-preview');
    const heading = document.getElementById('ai-agent-image-title');
    const fallback = document.getElementById('ai-agent-image-fallback');
    if (!modal || !image || !heading || !fallback || !url) return;
    fallback.style.display = 'none';
    image.style.display = 'block';
    image.onerror = () => {
        image.style.display = 'none';
        fallback.style.display = 'flex';
    };
    image.onload = () => {
        image.style.display = 'block';
        fallback.style.display = 'none';
    };
    image.src = url;
    heading.textContent = title;
    modal.classList.remove('agent-hidden');
}

function closeAgentImagePreview() {
    const modal = document.getElementById('ai-agent-image-modal');
    const image = document.getElementById('ai-agent-image-preview');
    const fallback = document.getElementById('ai-agent-image-fallback');
    if (!modal || !image || !fallback) return;
    modal.classList.add('agent-hidden');
    image.src = '';
    image.style.display = 'block';
    fallback.style.display = 'none';
}

function startTemplateSendFromAgent(templateId) {
    if (!templateId) return;
    sessionStorage.setItem('aiAgentMessageTemplate', templateId);
    appendChatMessage('agent', `Template prepared for Send Message. I'll open the messaging screen with template \`${templateId}\` ready.`);
    openAgentWorkspace('/messaging/ui?sourceObject=message_template', 'Send Message');
}

function createConversationId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
    }
    return `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function ensureAiAgentPanelLoaded() {
    if (document.getElementById('ai-agent-window')) return true;
    const root = document.getElementById('ai-agent-root');
    if (!root) return false;
    root.innerHTML = '<div class="sf-card" style="padding:1rem;text-align:center;color:#5b708b;">Loading AI Agent...</div>';
    try {
        const response = await fetch('/ai-agent-panel');
        const html = await response.text();
        if (!response.ok) throw new Error('Failed to load AI Agent panel.');
        root.innerHTML = html;
        applyAiAgentLanguageUi();
        return true;
    } catch (error) {
        console.error(error);
        root.innerHTML = '<div class="sf-card" style="padding:1rem;text-align:center;color:var(--error);">Unable to load AI Agent right now.</div>';
        return false;
    }
}

async function toggleAiAgent() {
    const loaded = await ensureAiAgentPanelLoaded();
    if (!loaded) return;
    const win = document.getElementById('ai-agent-window');
    if (!win) return;
    if (win.classList.contains('agent-hidden')) {
        win.classList.remove('agent-hidden');
        syncAiAgentWindowState();
        return;
    }
    closeAiAgent();
}

function syncAiAgentWindowState() {
    const win = document.getElementById('ai-agent-window');
    const minimizeBtn = document.getElementById('ai-agent-minimize-btn');
    const maximizeBtn = document.getElementById('ai-agent-maximize-btn');
    if (!win) return;

    win.classList.toggle('agent-minimized', isAiAgentMinimized);
    win.classList.toggle('agent-maximized', isAiAgentMaximized);

    if (minimizeBtn) {
        minimizeBtn.innerHTML = isAiAgentMinimized ? '&#9723;' : '&minus;';
        minimizeBtn.setAttribute('aria-label', isAiAgentMinimized ? 'Restore AI Agent' : 'Minimize AI Agent');
        minimizeBtn.setAttribute('title', isAiAgentMinimized ? 'Restore AI Agent' : 'Minimize AI Agent');
    }

    if (maximizeBtn) {
        maximizeBtn.textContent = isAiAgentMaximized ? '🗗' : '⛶';
        maximizeBtn.setAttribute('aria-label', isAiAgentMaximized ? 'Restore AI Agent size' : 'Maximize AI Agent');
        maximizeBtn.setAttribute('title', isAiAgentMaximized ? 'Restore AI Agent size' : 'Maximize AI Agent');
    }
}

function closeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    if (!win) return;

    isAiAgentMinimized = false;
    isAiAgentMaximized = false;
    win.classList.add('agent-hidden');
    syncAiAgentWindowState();
}

async function resetAiAgent() {
    const body = document.getElementById('ai-agent-body');
    const input = document.getElementById('ai-agent-input');

    try {
        await fetch('/ai-agent/api/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: aiAgentConversationId })
        });
    } catch (error) {
        console.error('AI Agent reset error:', error);
    }

    body.innerHTML = AI_AGENT_DEFAULT_BODY_HTML;
    if (input) input.value = '';

    aiAgentConversationId = createConversationId();
    aiAgentSelectionState = {};
    aiAgentActiveSelectionObject = null;
    sessionStorage.removeItem('aiAgentMessageSelection');
    applyAiAgentLanguageUi();
    updateSelectionBar();
}

function minimizeAiAgent(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const win = document.getElementById('ai-agent-window');
    if (!win || win.classList.contains('agent-hidden')) return;

    isAiAgentMinimized = !isAiAgentMinimized;
    if (isAiAgentMinimized) {
        isAiAgentMaximized = false;
    }
    syncAiAgentWindowState();
}

function maximizeAiAgent(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const win = document.getElementById('ai-agent-window');
    if (!win || win.classList.contains('agent-hidden')) return;

    isAiAgentMaximized = !isAiAgentMaximized;
    if (isAiAgentMaximized) {
        isAiAgentMinimized = false;
    }
    syncAiAgentWindowState();
}

async function fetchAiAgentResponse(query, pageOverride = 1) {
    const response = await fetch('/ai-agent/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query,
            conversation_id: aiAgentConversationId,
            page: pageOverride,
            per_page: 30,
            selection: buildSelectionPayload(),
            language_preference: aiAgentLanguagePreference,
        })
    });
    return response.json();
}

async function sendAiMessage(queryOverride = null, pageOverride = 1) {
    const input = document.getElementById('ai-agent-input');
    const query = (queryOverride ?? input.value).trim();
    if (!query) return;

    if (!queryOverride) {
        appendChatMessage('user', query);
        input.value = '';
    }

    const loadingId = 'loading-' + Date.now();
    appendChatMessage('agent', '<span class="loading-dots">Thinking</span>', loadingId);

    try {
        const data = await fetchAiAgentResponse(query, pageOverride);
        
        const loadingIndicator = document.getElementById(loadingId);
        if (loadingIndicator) loadingIndicator.remove();

        // Handle UI modification intent
        if (data.intent === 'MODIFY_UI') {
            const text = data.text.toLowerCase();
            if (text.includes('compact') || text.includes('축소')) agentTableStyle = 'compact';
            else if (text.includes('modern') || text.includes('모던')) agentTableStyle = 'modern';
            else if (text.includes('default') || text.includes('기본') || text.includes('salesforce')) agentTableStyle = 'default';
            
            // Re-style current tables in the DOM
            document.querySelectorAll('.agent-table').forEach(t => {
                t.className = `agent-table agent-table-${agentTableStyle}`;
            });
        }

        // Handle Open Record intent (Phase 170/171 Natural Transition)
        if (data.intent === 'OPEN_RECORD') {
            if (data.text) {
                appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query, data.chat_card);
            }
            if (data.redirect_url) {
                openAgentWorkspace(data.redirect_url, data.record_id ? `Record ${data.record_id}` : 'Record View');
            }
            return;
        }

        // Handle Send Message intent
        if (data.intent === 'SEND_MESSAGE') {
            if (data.selection) {
                sessionStorage.setItem('aiAgentMessageSelection', JSON.stringify(data.selection));
            }
            if (data.template_id) {
                sessionStorage.setItem('aiAgentMessageTemplate', data.template_id);
            } else {
                sessionStorage.removeItem('aiAgentMessageTemplate');
            }
            if (data.redirect_url) {
                openAgentWorkspace(data.redirect_url, 'Send Message');
            }
            return;
        }

        if (data.intent === 'OPEN_FORM' && data.form_url) {
            appendAgentInlineFormMessage(data.text || 'I opened the form here in chat.', data.form_url, data.form_title || 'Form');
            return;
        }

        if (data.text) {
            appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query, data.chat_card);
        } else {
            appendChatMessage('agent', "I'm sorry, I couldn't process that request.");
        }

        // Immediately remove deleted rows from all visible tables
        if (data.deleted_ids && data.deleted_ids.length > 0 && data.object_type) {
            data.deleted_ids.forEach(id => removeAgentTableRow(data.object_type, String(id)));
            clearActiveSelection();
            window._agentPendingDelete = null;
        }
    } catch (error) {
        console.error("AI Agent Error:", error);
        const loadingIndicator = document.getElementById(loadingId);
        if (loadingIndicator) loadingIndicator.remove();
        appendChatMessage('agent', "Sorry, I encountered an error connecting to the AI service.");
    }
}

function appendChatMessage(role, text, id = null, sql = null, results = null, objectType = null, pagination = null, originalQuery = null, chatCard = null) {
    const body = document.getElementById('ai-agent-body');
    if (!body) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = role === 'user' ? 'msg-user' : 'msg-agent';
    if (id) msgDiv.id = id;

    if (role === 'user') {
        msgDiv.innerHTML = `
            <div class="msg-user-content">
                <div class="msg-user-icon">👤</div>
                <div class="msg-user-text">${text}</div>
            </div>
        `;
    } else {
        // Convert [Action Name] into clickable buttons
        let processedText = text.replace(/\[([^\]]+)\]/g, (match, p1) => {
            const normalized = p1.trim().toLowerCase();
            const actionClass = normalized === 'yes' ? 'agent-inline-action agent-inline-action-confirm' : (normalized === 'cancel' ? 'agent-inline-action agent-inline-action-cancel' : 'agent-inline-action');
            return `<button class="${actionClass}" onclick="sendQuickMessage('${p1}')">${p1}</button>`;
        });
        processedText = processedText.replace(/\n/g, '<br>');

        let innerHTML = `
            <div class="msg-agent-header">
                <div class="msg-agent-icon">🤖</div>
                <span style="font-size: 0.8rem; font-weight: 700; color: #3e3e3c;">AI AGENT</span>
            </div>
            <div class="msg-agent-content">
                <div class="msg-agent-text">
                    ${results ? '✅ ' : ''}${processedText}
                </div>
        `;

        if (sql) {
            innerHTML += `<div class="sql-block">${sql}</div>`;
        }

        if (results && results.length > 0) {
            innerHTML += renderResultsTable(results, objectType, pagination, originalQuery);
        }

        if (chatCard) {
            innerHTML += renderAgentChatCard(chatCard);
        }

        innerHTML += `</div>`;
        msgDiv.innerHTML = innerHTML;
    }

    body.appendChild(msgDiv);
    updateSelectionBar();
    
    // Handle [Yes] / [Cancel] for pending delete confirmation
    if (role === 'user') {
        const trimmed = text.trim().toLowerCase();
        if ((trimmed === 'yes') && window._agentPendingDelete) {
            const pending = window._agentPendingDelete;
            window._agentPendingDelete = null;
            // Execute the actual deletion via AI agent
            if (pending.ids && pending.ids.length > 1) {
                sendAiMessage(`Delete selected ${pending.objectType} records`);
            } else {
                sendAiMessage(`Delete ${pending.objectType} ${pending.ids ? pending.ids[0] : pending.recordId}`);
            }
            return;
        }
        if ((trimmed === 'cancel') && window._agentPendingDelete) {
            window._agentPendingDelete = null;
        }
    }

    // Auto-scroll to the results table top if one was just added
    setTimeout(() => {
        const resultsCont = msgDiv.querySelector('.results-container');
        if (resultsCont) {
            resultsCont.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            msgDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, 100);
}

function removeExistingAgentInlineForms() {
    document.querySelectorAll('.agent-inline-form-shell').forEach(node => node.remove());
}

function appendAgentInlineFormMessage(text, formUrl, formTitle) {
    const body = document.getElementById('ai-agent-body');
    if (!body) return;

    removeExistingAgentInlineForms();

    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg-agent';
    msgDiv.innerHTML = `
        <div class="msg-agent-header">
            <div class="msg-agent-icon">🤖</div>
            <span style="font-size: 0.8rem; font-weight: 700; color: #3e3e3c;">AI AGENT</span>
        </div>
        <div class="msg-agent-content">
            <div class="msg-agent-text">${text}</div>
            <div class="agent-inline-form-shell">
                <div class="agent-inline-form-loading">Loading ${escapeAgentHtml(formTitle || 'form')}...</div>
            </div>
        </div>
    `;
    body.appendChild(msgDiv);

    const shell = msgDiv.querySelector('.agent-inline-form-shell');
    if (shell) {
        loadAgentInlineForm(shell, formUrl, formTitle);
    }

    // Scroll to the form start so user sees it immediately
    setTimeout(() => {
        msgDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);
}

async function loadAgentInlineForm(shell, formUrl, formTitle) {
    if (!shell || !formUrl) return;

    try {
        const response = await fetch(formUrl);
        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, 'text/html');
        shell.innerHTML = extractAgentWorkspaceMarkup(doc, formUrl);
        shell.dataset.modalSourceUrl = formUrl;
        shell.dataset.formTitle = formTitle || 'Form';
        wireAgentInlineForm(shell, formUrl);
    } catch (error) {
        console.error(error);
        shell.innerHTML = '<div class="agent-inline-form-error">Unable to load the form here right now.</div>';
    }
}

function wireAgentInlineForm(shell, formUrl) {
    if (!shell) return;

    shell.querySelectorAll('script').forEach(script => {
        const replacement = document.createElement('script');
        replacement.textContent = script.textContent;
        document.body.appendChild(replacement);
        replacement.remove();
    });

    shell.querySelectorAll('[onclick="closeModal()"], .sf-modal-header span[onclick]').forEach(node => {
        node.removeAttribute('onclick');
        node.addEventListener('click', () => shell.remove());
    });

    shell.querySelectorAll('form').forEach(form => {
        if (form.dataset.aiAgentInlineEnhanced === 'true') return;
        form.dataset.aiAgentInlineEnhanced = 'true';
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const submitter = event.submitter || document.activeElement;
            const submitMode = submitter?.dataset?.submitMode || 'save';
            const submitButton = submitter || form.querySelector('button[type="submit"]');

            if (typeof validateForm === 'function' && validateForm(form) === false) {
                return;
            }

            if (submitButton) submitButton.disabled = true;

            try {
                const response = await fetch(form.action || formUrl, {
                    method: (form.method || 'POST').toUpperCase(),
                    body: new FormData(form),
                    headers: { 'Accept': 'text/html,application/json' },
                    redirect: 'follow',
                });

                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {
                    const data = await response.json();
                    if (!response.ok || data.status === 'error') {
                        throw new Error(data.message || 'Failed to save the form.');
                    }
                    appendChatMessage('agent', data.message || 'Form saved successfully.');
                    shell.remove();
                    return;
                }

                if (response.redirected) {
                    const finalUrl = new URL(response.url, window.location.origin);
                    const successMsg = decodeToastMessage(finalUrl.searchParams.get('success'), 'Record saved successfully.');
                    const errorMsg = decodeToastMessage(finalUrl.searchParams.get('error'));

                    if (errorMsg) {
                        appendChatMessage('agent', errorMsg);
                        return;
                    }

                    if (submitMode === 'save-new') {
                        appendChatMessage('agent', successMsg);
                        const sourceUrl = new URL(shell.dataset.modalSourceUrl || formUrl, window.location.origin);
                        sourceUrl.searchParams.delete('id');
                        await loadAgentInlineForm(shell, `${sourceUrl.pathname}${sourceUrl.search}`, shell.dataset.formTitle || 'Form');
                        return;
                    }

                    shell.remove();
                    appendChatMessage('agent', successMsg);

                    // Auto-show saved record snapshot
                    const objectPathMatch = finalUrl.pathname.match(/^\/([a-z_]+)\/([^/?#]+)/);
                    if (objectPathMatch) {
                        const urlObject = objectPathMatch[1]; // e.g. 'leads', 'contacts'
                        const urlRecordId = objectPathMatch[2];
                        // Map plural URL segment to singular object type
                        const objectTypeMap = { leads: 'lead', contacts: 'contact', opportunities: 'opportunity', assets: 'asset', products: 'product', models: 'model', vehicle_specifications: 'brand' };
                        const resolvedType = objectTypeMap[urlObject] || urlObject.replace(/s$/, '');
                        const followData = await fetchAiAgentResponse(`Manage ${resolvedType} ${urlRecordId}`);
                        if (followData?.text) {
                            appendChatMessage('agent', followData.text, null, followData.sql, followData.results, followData.object_type, followData.pagination, followData.original_query, followData.chat_card);
                        }
                    }
                    return;
                }

                const html = await response.text();
                const doc = new DOMParser().parseFromString(html, 'text/html');
                shell.innerHTML = extractAgentWorkspaceMarkup(doc, formUrl);
                wireAgentInlineForm(shell, formUrl);
            } catch (error) {
                console.error(error);
                appendChatMessage('agent', error.message || 'Failed to save the form.');
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    });
}

function sendQuickMessage(text) {
    const input = document.getElementById('ai-agent-input');
    if (!input) return;
    input.value = text;
    sendAiMessage();
}

function sendAiMessageWithDisplay(displayText, actualQuery) {
    appendChatMessage('user', displayText);
    sendAiMessage(actualQuery);
}

document.addEventListener('DOMContentLoaded', applyAiAgentLanguageUi);

function escapeAgentHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderAgentChatCard(card) {
    if (!card || card.type !== 'lead_paste') return '';
    const fields = Array.isArray(card.fields) ? card.fields : [];
    const fieldMarkup = fields.map(field => `
        <div class="agent-paste-row">
            <span class="agent-paste-label">${escapeAgentHtml(field.label)}</span>
            <span class="agent-paste-value">${escapeAgentHtml(field.value)}</span>
        </div>
    `).join('');

    const recordId = card.record_id || '';
    const objectType = card.object_type || 'lead';
    const displayName = card.title || 'Lead';

    // Render action buttons dynamically from backend-provided actions array
    let actionButtonsHtml = '';
    if (recordId && Array.isArray(card.actions) && card.actions.length > 0) {
        const buttons = card.actions.map(act => {
            const label = escapeAgentHtml(act.label || '');
            const tone = act.tone || 'default';
            const btnClass = tone === 'danger'
                ? 'agent-paste-action-btn agent-paste-action-danger'
                : tone === 'secondary'
                    ? 'agent-paste-action-btn agent-paste-action-secondary'
                    : 'agent-paste-action-btn';

            if (act.action === 'edit') {
                const editQuery = `Manage ${escapeAgentQuery(objectType)} ${escapeAgentQuery(recordId)} edit`;
                return `<button class="${btnClass}" onclick="sendAiMessageWithDisplay('Edit ${escapeAgentHtml(displayName)}', '${editQuery}')">${label}</button>`;
            }
            if (act.action === 'delete') {
                return `<button class="${btnClass}" onclick="triggerSnapshotDelete('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')">${label}</button>`;
            }
            if (act.action === 'send_message') {
                return `<button class="${btnClass}" onclick="triggerLeadCardSendMessage('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')">${label}</button>`;
            }
            return `<button class="${btnClass}" onclick="sendQuickMessage('${escapeAgentQuery(act.action)} ${escapeAgentQuery(objectType)} ${escapeAgentQuery(recordId)}')">${label}</button>`;
        }).join('');
        actionButtonsHtml = `<div class="agent-paste-actions">${buttons}</div>`;
    } else if (recordId) {
        // Fallback: legacy hardcoded Edit/Delete if no actions array
        const editQuery = `Manage ${objectType} ${recordId} edit`;
        actionButtonsHtml = `
            <div class="agent-paste-actions">
                <button class="agent-paste-action-btn" onclick="sendAiMessageWithDisplay('Edit ${escapeAgentHtml(displayName)}', '${escapeAgentQuery(editQuery)}')">Edit</button>
                <button class="agent-paste-action-btn agent-paste-action-danger" onclick="triggerSnapshotDelete('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')">Delete</button>
            </div>
        `;
    }

    return `
        <div class="agent-paste-card" data-agent-card-type="${escapeAgentHtml(card.type)}" data-record-id="${escapeAgentHtml(recordId)}" data-record-object-type="${escapeAgentHtml(objectType)}">
            <div class="agent-paste-meta">
                <span>${escapeAgentHtml(card.paste_label || 'Pasted')}</span>
                ${actionButtonsHtml}
            </div>
            <div class="agent-paste-header">
                <strong>${escapeAgentHtml(card.title || 'Lead')}</strong>
                <span>${escapeAgentHtml(card.subtitle || '')}</span>
            </div>
            <div class="agent-paste-body">${fieldMarkup}</div>
            ${card.hint ? `<div class="agent-paste-hint">${escapeAgentHtml(card.hint)}</div>` : ''}
        </div>
    `;
}

function triggerLeadCardSendMessage(objectType, recordId, displayName) {
    if (!objectType || !recordId) return;
    // Set this record as the messaging selection
    const selectionBucket = ensureSelectionBucket(objectType);
    const meta = ensureSelectionMeta(objectType);
    if (selectionBucket) selectionBucket.add(recordId);
    if (meta) meta.set(recordId, displayName);
    aiAgentActiveSelectionObject = objectType;
    // Trigger the send message flow via AI
    sendQuickMessage('Send Message');
}

function triggerSnapshotDelete(objectType, recordId, displayName) {
    if (!objectType || !recordId) return;
    appendChatMessage('agent', `Are you sure you want to delete **${displayName}**?\n[Yes] [Cancel]\n<!--delete-confirm|${objectType}|${recordId}|${displayName}-->`);

    // Store pending deletion context on the window so Yes/Cancel handlers can pick it up
    window._agentPendingDelete = { objectType, recordId, displayName };
}

function shouldUseAgentChatPaste(objectType) {
    return objectType === 'lead';
}

function renderResultsTable(results, objectType, pagination = null, originalQuery = null) {
    if (!results || results.length === 0) return "";
    if (!pagination && results.length > 30) {
        const localKey = `agent-local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
        localAgentResultTables[localKey] = {
            results,
            objectType,
            originalQuery,
        };
        return renderLocalResultsTable(localKey, 1);
    }

    return renderAgentResultsMarkup(results, objectType, pagination, originalQuery);
}

function renderLocalResultsTable(tableKey, page) {
    const tableState = localAgentResultTables[tableKey];
    if (!tableState) return '';

    const perPage = 30;
    const safePage = Math.max(page, 1);
    const start = (safePage - 1) * perPage;
    const pagedResults = tableState.results.slice(start, start + perPage);
    const pagination = {
        page: safePage,
        per_page: perPage,
        total: tableState.results.length,
        total_pages: Math.max(1, Math.ceil(tableState.results.length / perPage)),
        object_type: tableState.objectType,
        mode: 'local',
        table_key: tableKey,
    };

    return renderAgentResultsMarkup(pagedResults, tableState.objectType, pagination, tableState.originalQuery);
}

function renderAgentResultsMarkup(results, objectType, pagination = null, originalQuery = null) {
    const selectedIds = getSelectedIds(objectType);
    const hasTemplatePreview = objectType === 'message_template';
    const schemaKeys = (AGENT_TABLE_SCHEMAS[objectType] || Object.keys(results[0]))
        .filter(k => Object.prototype.hasOwnProperty.call(results[0], k));
    const tableUid = `agent-table-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    
    let html = `
        <div class="results-container" data-object-type="${objectType || ''}" ${pagination?.table_key ? `data-table-key="${pagination.table_key}"` : ''} data-table-uid="${tableUid}">
            <div class="table-controls">
                <div class="table-controls-instruction">Select records to take action.</div>
                <div class="table-controls-search-row">
                    <input type="text" class="agent-table-search" placeholder="Search across all records..." oninput="debounceAgentTableSearch(this, '${objectType}')" onkeydown="handleAgentTableSearch(event, this, '${objectType}')" aria-label="Search in table">
                    <div style="font-size: 0.7rem; color: #8a94a6; margin-top: 4px;">Partial matching (LIKE) is applied to all records. Press Enter for immediate search.</div>
                </div>
                <div class="table-controls-btn-row">
                    <button class="control-btn btn-icon" onclick="selectAllAgentRows(this, '${objectType}')" title="Select All"><span style="font-size:1rem; line-height:1;">✓</span></button>
                    <button class="control-btn btn-icon" onclick="clearAllAgentRows(this, '${objectType}')" title="Clear All"><span style="font-size:1rem; line-height:1;">✕</span></button>
                    <button class="control-btn control-btn-action" onclick="triggerSelectionOpenFromTable(this, '${objectType}')">Open</button>
                    <button class="control-btn control-btn-edit" onclick="triggerSelectionEditFromTable(this, '${objectType}')">Edit</button>
                    <button class="control-btn control-btn-danger" onclick="triggerSelectionDeleteFromTable(this, '${objectType}')">Delete</button>
                </div>
                <div class="table-controls-status">
                    Selected: <strong class="agent-selection-count">${selectedIds.length}</strong> items
                </div>
            </div>
            <div style="overflow-x: auto;">
                <table class="agent-table agent-table-${agentTableStyle}" id="${tableUid}">
                    <thead>
                        <tr>
                            <th style="width: 40px;">Sel.</th>
                            <th style="width: 40px;">No.</th>
    `;
    
    const keys = schemaKeys.filter(k => !['id', 'deleted_at', 'record_id'].includes(k));
    keys.forEach((k, idx) => {
        html += `<th onclick="sortAgentTable(this, ${idx + 2})" style="cursor: pointer; position: relative; padding-right: 20px;">
                    ${AGENT_TABLE_LABELS[k] || k.replace('_', ' ')}
                    <span class="sort-icon" style="position: absolute; right: 4px; opacity: 0.3;">⇅</span>
                 </th>`;
    });
    if (hasTemplatePreview) {
        html += '<th style="width: 110px;">Actions</th>';
    }
    html += '</tr></thead><tbody>';

    const rowStart = pagination ? ((pagination.page - 1) * pagination.per_page) + 1 : 1;

    results.forEach((row, index) => {
        const rowId = row.id || row.ID || "";
        const isChecked = selectedIds.includes(rowId);
        const rowLabel = getAgentFieldValue(row, 'display_name') || row.subject || row.phone || row.email || rowId;
        html += `<tr data-record-id="${rowId}" data-record-label="${String(rowLabel).replace(/"/g, '&quot;')}" onclick="selectAgentRecord('${rowId}', '${objectType}', this)" style="cursor: pointer;">
                    <td><input type="checkbox" ${isChecked ? 'checked' : ''} onclick="toggleAgentRowSelection(event, '${objectType}', '${rowId}')"></td>
                    <td style="color: #666; font-size: 0.75rem;">${rowStart + index}</td>`;
        keys.forEach(k => {
            let val = formatAgentFieldValue(k, getAgentFieldValue(row, k));
            if ((k === 'image_url' || k === 'file_path') && typeof val === 'string' && val.startsWith('/static/')) {
                html += `<td><button class="agent-thumbnail-btn" onclick="event.stopPropagation(); openAgentImagePreview('${escapeAgentQuery(val)}', 'Template Image')"><img src="${val}" alt="Template image" style="width: 56px; height: 56px; object-fit: cover; border-radius: 10px; border: 1px solid #d7deeb;"></button></td>`;
            } else if (k === 'name' || k === 'first_name' || k === 'display_name') {
                html += `<td><strong style="color: #0176d3;">${val}</strong></td>`;
            } else {
                html += `<td>${val}</td>`;
            }
        });
        if (hasTemplatePreview) {
            const previewUrl = (typeof row.image_url === 'string' && row.image_url.startsWith('/static/'))
                ? row.image_url
                : ((typeof row.file_path === 'string' && row.file_path.startsWith('/static/')) ? row.file_path : '');
            html += `<td><div class="agent-action-stack">${previewUrl ? `<button class="control-btn" onclick="event.stopPropagation(); openAgentImagePreview('${escapeAgentQuery(previewUrl)}', 'Template Preview')">Preview</button>` : '<span style="color:#8a94a6;font-size:0.78rem;">No image</span>'}<button class="control-btn control-btn-primary" onclick="event.stopPropagation(); startTemplateSendFromAgent('${rowId}')">Use In Send Message</button></div></td>`;
        }
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';

    if (pagination && pagination.total_pages > 1 && originalQuery) {
        html += `
            <div class="agent-pagination">
                <button class="control-btn" ${pagination.page <= 1 ? 'disabled' : ''} onclick="${pagination.mode === 'local' ? `requestLocalAgentPage('${pagination.table_key}', ${pagination.page - 1})` : `requestAgentPage('${escapeAgentQuery(originalQuery)}', ${pagination.page - 1})`}">Previous</button>
                <span class="agent-pagination-label">Page ${pagination.page} of ${pagination.total_pages} · ${pagination.total} records${pagination.mode === 'local' ? ' · Local' : ''}</span>
                <button class="control-btn" ${pagination.page >= pagination.total_pages ? 'disabled' : ''} onclick="${pagination.mode === 'local' ? `requestLocalAgentPage('${pagination.table_key}', ${pagination.page + 1})` : `requestAgentPage('${escapeAgentQuery(originalQuery)}', ${pagination.page + 1})`}">Next</button>
            </div>
        `;
    }

    html += '</div>';
    return html;
}

function filterAgentTable(input) {
    if (!input) return;
    const container = input.closest('.results-container');
    if (!container) return;
    const term = input.value.toLowerCase().trim();
    const rows = container.querySelectorAll('table tbody tr');
    
    let visibleCount = 0;
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const isMatch = term === '' || text.includes(term);
        row.style.display = isMatch ? '' : 'none';
        if (isMatch) visibleCount++;
    });

    // If we have a local filter but it's not enough, the debounced backend search will help.
}

let agentSearchDebounceTimeout;
function debounceAgentTableSearch(input, objectType) {
    // First, do a local fast filter
    filterAgentTable(input);

    // Then, set up a debounced backend search for the full dataset
    clearTimeout(agentSearchDebounceTimeout);
    const term = input.value.trim();
    if (term.length >= 2) {
        agentSearchDebounceTimeout = setTimeout(() => {
            requestAgentSearch(term, objectType);
        }, 1200); // Wait 1.2s before hitting the full backend to avoid excessive chat messages
    }
}

function handleAgentTableSearch(event, input, objectType) {
    if (event.key === 'Enter') {
        clearTimeout(agentSearchDebounceTimeout);
        const term = input.value.trim();
        if (term) {
            requestAgentSearch(term, objectType);
        }
    }
}

async function requestAgentSearch(term, objectType) {
    // Show a small processing indicator or message
    const query = `search ${objectType}s for ${term}`;
    sendAiMessageWithDisplay(`Search ${objectType}s: ${term}`, query);
}

function removeAgentTableRow(objectType, recordId) {
    if (!objectType || !recordId) return;
    document.querySelectorAll(`.results-container[data-object-type="${objectType}"]`).forEach(container => {
        const row = container.querySelector(`tr[data-record-id="${recordId}"]`);
        if (row) {
            row.style.transition = 'opacity 0.3s ease, height 0.3s ease';
            row.style.opacity = '0';
            setTimeout(() => { row.remove(); }, 300);
        }
        // Update count after removal
        if (objectType && aiAgentSelectionState[objectType]) {
            aiAgentSelectionState[objectType].delete(recordId);
        }
        if (objectType && aiAgentSelectionMeta[objectType]) {
            aiAgentSelectionMeta[objectType].delete(recordId);
        }
        updateTableSelectionCount(container, objectType);
    });
    updateSelectionBar();
}

function updateTableSelectionCount(container, objectType) {
    if (!container || !objectType) return;
    const count = getSelectedIds(objectType).length;
    const countEl = container.querySelector('.agent-selection-count');
    if (countEl) countEl.textContent = count;
}

function triggerSelectionOpenFromTable(btn, objectType) {
    // Build selection from this specific table container
    const container = btn.closest('.results-container');
    if (!container) return triggerSelectionOpen();
    _setActiveSelectionFromContainer(container, objectType);
    triggerSelectionOpen();
}

function triggerSelectionEditFromTable(btn, objectType) {
    const container = btn.closest('.results-container');
    if (!container) return triggerSelectionEdit();
    _setActiveSelectionFromContainer(container, objectType);
    triggerSelectionEdit();
}

function triggerSelectionDeleteFromTable(btn, objectType) {
    const container = btn.closest('.results-container');
    if (!container) return triggerSelectionDelete();
    _setActiveSelectionFromContainer(container, objectType);
    triggerSelectionDelete();
}

function _setActiveSelectionFromContainer(container, objectType) {
    aiAgentActiveSelectionObject = objectType;
    aiAgentActiveSelectionContainer = container;
}

function requestLocalAgentPage(tableKey, page) {
    const container = document.querySelector(`.results-container[data-table-key="${tableKey}"]`);
    const markup = renderLocalResultsTable(tableKey, page);
    if (container && markup) {
        container.outerHTML = markup;
    }
}

function escapeAgentQuery(value) {
    return String(value).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

function requestAgentPage(query, page) {
    sendAiMessage(query, page);
}

function getSelectedIds(objectType) {
    if (!objectType || !aiAgentSelectionState[objectType]) return [];
    return Array.from(aiAgentSelectionState[objectType]);
}

function buildSelectionPayload() {
    if (!aiAgentActiveSelectionObject) return null;
    const ids = getSelectedIds(aiAgentActiveSelectionObject);
    if (!ids.length) return null;
    const meta = ensureSelectionMeta(aiAgentActiveSelectionObject);
    return {
        object_type: aiAgentActiveSelectionObject,
        ids: ids,
        labels: ids.map(id => meta?.get(id) || id),
    };
}

function getAgentObjectRoute(objectType, recordId, action = 'detail') {
    const routes = {
        lead: { detail: `/leads/${recordId}`, edit: `/leads/new-modal?id=${recordId}` },
        contact: { detail: `/contacts/${recordId}`, edit: `/contacts/new-modal?id=${recordId}` },
        opportunity: { detail: `/opportunities/${recordId}`, edit: `/opportunities/new-modal?id=${recordId}` },
        product: { detail: `/products/${recordId}`, edit: `/products/new-modal?id=${recordId}` },
        asset: { detail: `/assets/${recordId}`, edit: `/assets/new-modal?id=${recordId}` },
        model: { detail: `/models/${recordId}`, edit: `/models/new-modal?id=${recordId}` },
        brand: { detail: `/vehicle_specifications/${recordId}`, edit: `/vehicle_specifications/new-modal?id=${recordId}` },
        message_template: { detail: `/message_templates/${recordId}`, edit: null },
    };
    return routes[objectType]?.[action] || null;
}

function ensureSelectionBucket(objectType) {
    if (!objectType) return null;
    if (!aiAgentSelectionState[objectType]) {
        aiAgentSelectionState[objectType] = new Set();
    }
    return aiAgentSelectionState[objectType];
}

function updateSelectionLabel(container, objectType) {
    if (!container || !objectType) return;
    // Support both old (.agent-selection-label strong) and new (.agent-selection-count) selectors
    const count = getSelectedIds(objectType).length;
    const oldLabel = container.querySelector('.agent-selection-label strong');
    if (oldLabel) oldLabel.textContent = count;
    const newCount = container.querySelector('.agent-selection-count');
    if (newCount) newCount.textContent = count;
}

function toggleAgentRowSelection(event, objectType, recordId) {
    event.stopPropagation();
    if (!objectType || !recordId) return;
    aiAgentActiveSelectionObject = objectType;
    aiAgentActiveSelectionContainer = event.target.closest('.results-container') || aiAgentActiveSelectionContainer;
    const bucket = ensureSelectionBucket(objectType);
    const meta = ensureSelectionMeta(objectType);
    const row = event.target.closest('tr');
    const label = row?.getAttribute('data-record-label') || recordId;
    if (event.target.checked) {
        bucket.add(recordId);
        meta?.set(recordId, label);
    } else {
        bucket.delete(recordId);
        meta?.delete(recordId);
    }
    updateSelectionLabel(event.target.closest('.results-container'), objectType);
    updateSelectionBar();
}

let agentSortAsc = true;
let lastAgentSortCol = -1;

function sortAgentTable(th, colIdx) {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (lastAgentSortCol === colIdx) {
        agentSortAsc = !agentSortAsc;
    } else {
        agentSortAsc = true;
        lastAgentSortCol = colIdx;
    }

    // Update icons
    table.querySelectorAll('.sort-icon').forEach(span => {
        span.innerHTML = '⇅';
        span.style.opacity = '0.3';
    });
    const icon = th.querySelector('.sort-icon');
    if (icon) {
        icon.innerHTML = agentSortAsc ? '↑' : '↓';
        icon.style.opacity = '1';
        icon.style.color = '#0176d3';
    }

    rows.sort((a, b) => {
        const valA = a.children[colIdx].innerText.trim().toLowerCase();
        const valB = b.children[colIdx].innerText.trim().toLowerCase();
        
        if (valA === valB) return 0;
        
        // Handle numbers
        const numA = parseFloat(valA.replace(/[^0-9.-]+/g, ""));
        const numB = parseFloat(valB.replace(/[^0-9.-]+/g, ""));
        if (!isNaN(numA) && !isNaN(numB) && valA.match(/^[0-9,.₩$-]+$/)) {
            return agentSortAsc ? numA - numB : numB - numA;
        }

        return agentSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    });

    tbody.innerHTML = '';
    rows.forEach((row, idx) => {
        // Refresh index
        row.children[1].innerText = idx + 1;
        tbody.appendChild(row);
    });
}

function selectAllAgentRows(btn, objectType) {
    const table = btn.closest('.results-container').querySelector('table');
    const bucket = ensureSelectionBucket(objectType);
    const meta = ensureSelectionMeta(objectType);
    aiAgentActiveSelectionObject = objectType;
    aiAgentActiveSelectionContainer = btn.closest('.results-container');
    table.querySelectorAll('tbody tr').forEach(row => {
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (!checkbox) return;
        const recordId = row.getAttribute('data-record-id');
        const label = row.getAttribute('data-record-label') || recordId;
        checkbox.checked = true;
        if (recordId) {
            bucket.add(recordId);
            meta?.set(recordId, label);
        }
    });
    updateSelectionLabel(btn.closest('.results-container'), objectType);
    updateSelectionBar();
}

function clearAllAgentRows(btn, objectType) {
    const table = btn.closest('.results-container').querySelector('table');
    table.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    if (objectType && aiAgentSelectionState[objectType]) {
        aiAgentSelectionState[objectType].clear();
    }
    if (objectType && aiAgentSelectionMeta[objectType]) {
        aiAgentSelectionMeta[objectType].clear();
    }
    updateSelectionLabel(btn.closest('.results-container'), objectType);
    updateSelectionBar();
}

function clearActiveSelection() {
    Object.keys(aiAgentSelectionState).forEach(objectType => {
        aiAgentSelectionState[objectType].clear();
    });
    Object.keys(aiAgentSelectionMeta).forEach(objectType => {
        aiAgentSelectionMeta[objectType].clear();
    });
    aiAgentActiveSelectionObject = null;
    aiAgentActiveSelectionContainer = null;
    document.querySelectorAll('.results-container input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    document.querySelectorAll('.results-container').forEach(container => {
        const objectType = container.getAttribute('data-object-type');
        updateSelectionLabel(container, objectType);
    });
    updateSelectionBar();
}

function triggerSelectionMessaging() {
    const selection = buildSelectionPayload();
    if (!selection) {
        appendChatMessage('agent', getAiAgentUiCopy().sendMessageGuide);
        return;
    }
    sendQuickMessage('Send Message');
}

function triggerSelectionOpen() {
    const selection = buildSelectionPayload();
    if (!selection) {
        appendChatMessage('agent', 'Select a record first, then choose Open.');
        return;
    }
    if (selection.ids.length !== 1) {
        appendChatMessage('agent', 'Open works on one record at a time. Select a single record, then try again.');
        return;
    }
    const label = selection.labels?.[0] || selection.ids[0];
    if (shouldUseAgentChatPaste(selection.object_type)) {
        sendAiMessageWithDisplay(`Open ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);
        return;
    }
    const url = getAgentObjectRoute(selection.object_type, selection.ids[0], 'detail');
    if (url) {
        openAgentWorkspace(url, `${label}`);
        return;
    }
    sendAiMessageWithDisplay(`Open ${label}`, `Show ${selection.object_type} ${selection.ids[0]}`);
}

function triggerSelectionEdit() {
    const selection = buildSelectionPayload();
    if (!selection) {
        appendChatMessage('agent', 'Select exactly one record to edit it.');
        return;
    }
    if (selection.ids.length !== 1) {
        appendChatMessage('agent', 'Edit works on one record at a time. Select a single record, then try again.');
        return;
    }
    const label = selection.labels?.[0] || selection.ids[0];
    if (shouldUseAgentChatPaste(selection.object_type)) {
        sendAiMessageWithDisplay(`Edit ${label}`, `Manage ${selection.object_type} ${selection.ids[0]} edit`);
        return;
    }
    const url = getAgentObjectRoute(selection.object_type, selection.ids[0], 'edit');
    if (url) {
        openAgentWorkspace(url, `Edit ${label}`);
        return;
    }
    sendAiMessageWithDisplay(`Edit ${label}`, `Manage ${selection.object_type} ${selection.ids[0]}`);
}

function triggerSelectionDelete() {
    const selection = buildSelectionPayload();
    if (!selection) {
        appendChatMessage('agent', 'Select one or more records to delete them.');
        return;
    }
    const firstLabel = selection.labels?.[0] || selection.ids[0];
    const subject = selection.ids.length === 1
        ? `**${firstLabel}**`
        : `**${selection.ids.length}** ${normalizeObjectLabel(selection.object_type, selection.ids.length)}`;
    appendChatMessage('agent', `Are you sure you want to delete ${subject}?\n[Yes] [Cancel]`);
    // Store pending deletion so the Yes handler can resolve it
    window._agentPendingDelete = {
        objectType: selection.object_type,
        ids: [...selection.ids],
        labels: [...(selection.labels || [])],
        displayName: firstLabel,
    };
}

function selectAgentRecord(recordId, objectType, row) {
    if (!recordId || !objectType || !row) return;
    const checkbox = row.querySelector('input[type="checkbox"]');
    if (!checkbox) return;
    checkbox.checked = !checkbox.checked;
    toggleAgentRowSelection({ stopPropagation() {}, target: checkbox }, objectType, recordId);
}

async function startAiRecommend(btn) {
    if (!btn) return;
    const originalText = btn.innerText;
    btn.innerText = "Processing...";
    btn.disabled = true;
    const container = document.getElementById('ai-recommendation-results');
    
    try {
        const response = await fetch('/api/recommendations');
        if (response.ok) {
            const html = await response.text();
            if (container) {
                container.innerHTML = html;
                container.style.display = 'block';
            }
            const modeLabel = document.querySelector('[data-ai-recommend-current-mode]')?.textContent?.replace('AI Recommend Mode: ', '').trim();
            const pendingModeToast = window.aiRecommendPendingToast || (modeLabel ? `AI Recommend mode set to ${modeLabel}.` : '');
            window.aiRecommendPendingToast = '';
            if (pendingModeToast && typeof showToast === 'function') showToast(pendingModeToast);
        } else {
            if (typeof showToast === 'function') showToast("Server error loading recommendations.", true);
        }
    } catch (error) { 
        console.error(error); 
        if (typeof showToast === 'function') showToast("Network error loading recommendations.", true);
    }
    finally { btn.innerText = originalText; btn.disabled = false; }
}

function updateDashboardRecommendationModeButtons(mode) {
    document.querySelectorAll('[data-ai-recommend-mode]').forEach(btn => {
        const isActive = btn.getAttribute('data-ai-recommend-mode') === mode;
        btn.classList.toggle('is-active', isActive);
        btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    const label = document.querySelector('[data-ai-recommend-current-mode]');
    if (label) {
        label.textContent = `AI Recommend Mode: ${mode}`;
    }
}

async function setDashboardRecommendationMode(mode) {
    try {
        const response = await fetch('/api/recommendations/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        });

        const payload = await response.json();
        if (!response.ok || payload.status !== 'success') {
            throw new Error(payload.message || 'Failed to change recommendation mode.');
        }

        updateDashboardRecommendationModeButtons(payload.mode);
        window.aiRecommendPendingToast = `AI Recommend mode set to ${payload.mode}.`;
    } catch (error) {
        console.error(error);
        if (typeof showToast === 'function') showToast('Unable to change AI recommendation mode.', true);
    }
}
