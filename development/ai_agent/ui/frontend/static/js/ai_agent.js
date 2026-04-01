let isAiAgentMinimized = false;
let isAiAgentMaximized = false;
let agentTableStyle = 'default';
let aiAgentConversationId = createConversationId();
let aiAgentSelectionState = {};
let aiAgentSelectionMeta = {};
let aiAgentActiveSelectionObject = null;
let aiAgentActiveSelectionContainer = null;
let localAgentResultTables = {};
let aiAgentSendComposerCounter = 0;
const aiAgentSendComposerState = {};
let aiAgentLanguagePreference = localStorage.getItem('aiAgentLanguagePreference') || 'eng';
let aiAgentDebugEnabled = localStorage.getItem('aiAgentDebugEnabled');
aiAgentDebugEnabled = aiAgentDebugEnabled === '1';
let aiAgentDebugEntries = [];
let aiAgentMediaRecorder = null;
let aiAgentRecorderChunks = [];
let aiAgentRecorderStream = null;
let aiAgentVoiceRecording = false;
let aiAgentVoiceTranscribing = false;
const aiAgentMessagingAvailabilityState = {
    checked: false,
    available: true,
    message: '',
    reason: null,
};
const AI_AGENT_FETCH_TIMEOUT_MS = 15000;
const AI_AGENT_WORKSPACE_TIMEOUT_MS = 12000;
const AI_AGENT_QUICK_GUIDE_STORAGE_KEY = 'aiAgentQuickGuideActivity';
const AI_AGENT_QUICK_GUIDE_MAX_ITEMS = 8;
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
            <button class="selection-action-btn selection-action-edit" onclick="triggerSelectionEdit()">Edit</button>
            <button class="selection-action-btn selection-action-danger" onclick="triggerSelectionDelete()">Delete</button>
            <button class="selection-action-btn selection-action-primary" onclick="triggerSelectionMessaging()" data-ai-selection-send>Send Message</button>
        </div>
    </div>
    <div id="ai-agent-messaging-block-banner" class="agent-inline-notice agent-hidden" style="display:none; margin: 0 0 12px; padding: 10px 12px; border: 1px solid #f2c7c7; border-radius: 10px; background: #fff6f6; color: #7b2d2f; font-size: 0.85rem;"></div>
    <div id="ai-agent-workspace" class="agent-workspace agent-hidden">
        <div class="agent-workspace-header">
            <div>
                <div class="agent-workspace-kicker">AI Agent Workspace</div>
                <strong id="ai-agent-workspace-title">Record View</strong>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <button class="control-btn control-btn-edit" onclick="triggerWorkspaceEdit()" id="ai-agent-workspace-edit-btn" style="display: none;">Edit</button>
                <button class="control-btn" onclick="triggerWorkspaceDelete()" id="ai-agent-workspace-delete-btn" style="display: none; color: var(--error);">Delete</button>
                <button class="agent-workspace-close" onclick="closeAgentWorkspace()">&times;</button>
            </div>
        </div>
        <div id="ai-agent-workspace-loading" class="agent-workspace-loading agent-hidden">Loading...</div>
        <div id="ai-agent-workspace-content" class="agent-workspace-content"></div>
    </div>
`;

const AGENT_TABLE_SCHEMAS = {
    lead: ['display_name', 'phone', 'status', 'model', 'created_at'],
    contact: ['display_name', 'phone', 'email', 'tier', 'created_at'],
    opportunity: ['name', 'amount', 'stage', 'temperature', 'created_at', 'contact_display_name', 'contact_phone', 'model'],
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
    has_image: 'Image',
};

const AGENT_LOOKUP_VISUALS = {
    Lead: { color: '#49a5e1', text: 'LQ' },
    Contact: { color: '#a094ed', text: 'C' },
    Opportunity: { color: '#fcb95b', text: 'O' },
    Asset: { color: '#3ba755', text: 'AS' },
    Product: { color: '#b781d3', text: 'P' },
    Brand: { color: '#54698d', text: 'B' },
    VehicleSpecification: { color: '#54698d', text: 'B' },
    Model: { color: '#e094ed', text: 'M' },
    MessageSend: { color: '#00a1e0', text: 'MS' },
    Message: { color: '#00a1e0', text: 'MS' },
    MessageTemplate: { color: '#2e8b57', text: 'MT' },
    Template: { color: '#2e8b57', text: 'MT' },
};

function getAgentLookupVisual(lookupObject) {
    return AGENT_LOOKUP_VISUALS[lookupObject] || { color: '#54698d', text: 'R' };
}

function fetchAiAgentWithTimeout(resource, options = {}, timeoutMs = AI_AGENT_FETCH_TIMEOUT_MS) {
    if (typeof AbortController !== 'function') {
        return fetch(resource, options);
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    return fetch(resource, { ...options, signal: controller.signal })
        .finally(() => {
            clearTimeout(timer);
        });
}

function applyAiAgentMessagingAvailabilityState() {
    const quickButton = document.querySelector('[data-ai-send-message-trigger]');
    const selectionButton = document.querySelector('[data-ai-selection-send]');
    const banner = document.getElementById('ai-agent-messaging-block-banner');
    const blocked = aiAgentMessagingAvailabilityState.checked && !aiAgentMessagingAvailabilityState.available;

    [quickButton, selectionButton].forEach((button) => {
        if (!button) return;
        button.disabled = blocked;
        button.style.opacity = blocked ? '0.65' : '1';
        button.style.cursor = blocked ? 'not-allowed' : 'pointer';
        button.title = blocked ? aiAgentMessagingAvailabilityState.message : '';
    });

    if (!banner) return;
    if (!blocked) {
        banner.style.display = 'none';
        banner.classList.add('agent-hidden');
        banner.textContent = '';
        return;
    }
    banner.style.display = 'block';
    banner.classList.remove('agent-hidden');
    banner.textContent = aiAgentMessagingAvailabilityState.message || 'Message service is unavailable. Contact the administrator.';
}

async function refreshAiAgentMessagingAvailability() {
    aiAgentMessagingAvailabilityState.checked = false;
    aiAgentMessagingAvailabilityState.available = true;
    aiAgentMessagingAvailabilityState.message = '';
    aiAgentMessagingAvailabilityState.reason = null;
    try {
        const response = await fetchAiAgentWithTimeout('/messaging/demo-availability', {}, AI_AGENT_WORKSPACE_TIMEOUT_MS);
        const payload = await response.json();
        aiAgentMessagingAvailabilityState.checked = true;
        aiAgentMessagingAvailabilityState.available = Boolean(payload.available);
        aiAgentMessagingAvailabilityState.reason = payload.reason || null;
        aiAgentMessagingAvailabilityState.message = payload.message || 'Message service is unavailable. Contact the administrator.';
    } catch (error) {
        aiAgentMessagingAvailabilityState.checked = true;
        aiAgentMessagingAvailabilityState.available = false;
        aiAgentMessagingAvailabilityState.reason = null;
        aiAgentMessagingAvailabilityState.message = 'Message service is unavailable. Contact the administrator.';
    }
    applyAiAgentMessagingAvailabilityState();
}

function ensureAiAgentMessagingAvailable() {
    if (aiAgentMessagingAvailabilityState.checked && !aiAgentMessagingAvailabilityState.available) {
        appendChatMessage('agent', aiAgentMessagingAvailabilityState.message || 'Message service is unavailable. Contact the administrator.');
        return false;
    }
    return true;
}

function loadQuickGuideActivity() {
    try {
        const raw = localStorage.getItem(AI_AGENT_QUICK_GUIDE_STORAGE_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
        return [];
    }
}

function saveQuickGuideActivity(items) {
    localStorage.setItem(AI_AGENT_QUICK_GUIDE_STORAGE_KEY, JSON.stringify(Array.isArray(items) ? items : []));
}

function buildQuickGuideActivityEntry(query, label) {
    const safeQuery = String(query || '').trim();
    const safeLabel = String(label || safeQuery).trim();
    return {
        id: `quick-${safeQuery.toLowerCase()}`,
        query: safeQuery,
        label: safeLabel,
        pinned: false,
        last_used_at: Date.now(),
    };
}

function recordQuickGuideActivity(query, label = null) {
    const safeQuery = String(query || '').trim();
    if (!safeQuery) return;
    const nextEntry = buildQuickGuideActivityEntry(safeQuery, label || safeQuery);
    const existingItems = loadQuickGuideActivity();
    const previousEntry = existingItems.find(item => item && item.query === safeQuery);
    const items = existingItems.filter(item => item && item.query !== safeQuery);
    items.unshift({
        ...nextEntry,
        pinned: previousEntry?.pinned || false,
    });
    const pinnedItems = items.filter(item => item.pinned);
    const recentItems = items.filter(item => !item.pinned).slice(0, AI_AGENT_QUICK_GUIDE_MAX_ITEMS);
    saveQuickGuideActivity([...pinnedItems, ...recentItems]);
    renderQuickGuideActivityList();
}

function toggleQuickGuidePin(id) {
    const items = loadQuickGuideActivity();
    const nextItems = items.map(item => item.id === id ? { ...item, pinned: !item.pinned } : item);
    nextItems.sort((left, right) => {
        if (Boolean(left.pinned) !== Boolean(right.pinned)) return left.pinned ? -1 : 1;
        return Number(right.last_used_at || 0) - Number(left.last_used_at || 0);
    });
    saveQuickGuideActivity(nextItems);
    renderQuickGuideActivityList();
}

function runQuickGuideActivity(id) {
    const item = loadQuickGuideActivity().find(entry => entry.id === id);
    if (!item) return;
    recordQuickGuideActivity(item.query, item.label);
    sendQuickMessage(item.query);
}

function renderQuickGuideActivityList() {
    const container = document.getElementById('ai-agent-activity-list');
    const empty = document.getElementById('ai-agent-activity-empty');
    if (!container || !empty) return;
    const copy = getAiAgentUiCopy();

    const items = loadQuickGuideActivity()
        .sort((left, right) => {
            if (Boolean(left.pinned) !== Boolean(right.pinned)) return left.pinned ? -1 : 1;
            return Number(right.last_used_at || 0) - Number(left.last_used_at || 0);
        })
        .slice(0, AI_AGENT_QUICK_GUIDE_MAX_ITEMS);

    if (!items.length) {
        container.innerHTML = '';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    container.innerHTML = items.map((item) => `
        <div class="quick-guide-history-item${item.pinned ? ' is-pinned' : ''}">
            <button type="button" class="quick-guide-history-run" onclick="runQuickGuideActivity('${escapeAgentQuery(item.id)}')">
                <strong>${escapeAgentHtml(item.label || item.query)}</strong>
                <small>${escapeAgentHtml(item.query)}</small>
            </button>
            <button
                type="button"
                class="quick-guide-history-pin${item.pinned ? ' is-active' : ''}"
                onclick="toggleQuickGuidePin('${escapeAgentQuery(item.id)}')"
                aria-label="${item.pinned ? copy.pinned : copy.pin}"
                title="${item.pinned ? copy.pinned : copy.pin}"
            >${item.pinned ? copy.pinned : copy.pin}</button>
        </div>
    `).join('');
}

function getAgentFieldValue(row, key) {
    if (key === 'display_name') {
        return row.display_name || [row.first_name, row.last_name].filter(Boolean).join(' ').trim() || row.name || '-';
    }
    if (key === 'has_image') {
        return (row.image_url || row.attachment_id) ? '✓' : '✕';
    }
    return row[key] ?? '-';
}

function formatAgentFieldValue(key, value) {
    if (value === null || value === undefined || value === '') return '';
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

function agentTableRowMatches(row, objectType, term) {
    const normalizedTerm = String(term || '').trim().toLowerCase();
    if (!normalizedTerm) return true;
    const schemaKeys = AGENT_TABLE_SCHEMAS[objectType] || Object.keys(row || {});
    return schemaKeys.some((key) => {
        const rawValue = getAgentFieldValue(row || {}, key);
        const formatted = formatAgentFieldValue(key, rawValue);
        return String(formatted ?? '').toLowerCase().includes(normalizedTerm);
    });
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
            historyTitle: '최근 및 고정',
            historyCopy: '자주 쓰는 작업을 고정하고 최근 명령을 빠르게 다시 실행하세요.',
            historyEmpty: '아직 최근 명령이 없습니다. 빠른 버튼이나 채팅 명령을 사용하면 여기에 표시됩니다.',
            pin: '고정',
            pinned: '고정됨',
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
        historyTitle: 'Recent & Pinned',
        historyCopy: 'Pin frequent actions and keep your latest commands close by.',
        historyEmpty: 'No recent commands yet. Use a quick action or type a command to build your list.',
        pin: 'Pin',
        pinned: 'Pinned',
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
    setText('[data-ai-guide-section-history]', copy.historyTitle);
    setText('[data-ai-guide-history-copy]', copy.historyCopy);
    setText('[data-ai-guide-history-empty]', copy.historyEmpty);
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
    syncAiAgentDebugUi();
    updateAiAgentComposerState();
    renderQuickGuideActivityList();
}

function formatAiAgentDebugValue(value) {
    if (value === null || value === undefined || value === '') return '';
    if (typeof value === 'string') return value;
    try {
        return JSON.stringify(value);
    } catch (error) {
        return String(value);
    }
}

function recordAiAgentDebug(stage, details = {}) {
    const timestamp = new Date();
    const message = Object.entries(details)
        .filter(([, value]) => value !== undefined && value !== null && value !== '')
        .map(([key, value]) => `${key}=${formatAiAgentDebugValue(value)}`)
        .join(' | ');

    aiAgentDebugEntries.unshift({
        time: timestamp.toLocaleTimeString([], { hour12: false }),
        stage,
        message,
    });
    aiAgentDebugEntries = aiAgentDebugEntries.slice(0, 25);
    syncAiAgentDebugUi();
}

function syncAiAgentDebugUi() {
    const toggle = document.getElementById('ai-agent-debug-toggle');
    const panel = document.getElementById('ai-agent-debug-panel');
    const status = document.getElementById('ai-agent-debug-status');
    const log = document.getElementById('ai-agent-debug-log');

    if (toggle) {
        toggle.textContent = aiAgentDebugEnabled ? 'Debug On' : 'Debug Off';
        toggle.classList.toggle('is-active', aiAgentDebugEnabled);
    }

    if (!panel || !status || !log) return;

    panel.classList.toggle('agent-hidden', !aiAgentDebugEnabled);
    if (!aiAgentDebugEnabled) return;

    status.textContent = aiAgentDebugEntries.length
        ? `Showing the latest ${aiAgentDebugEntries.length} runtime events for workspace and form loading.`
        : 'Debug instrumentation is active for this session.';

    log.innerHTML = aiAgentDebugEntries.length
        ? aiAgentDebugEntries.map(entry => `
            <div class="ai-agent-debug-entry">
                <div class="ai-agent-debug-time">${escapeAgentHtml(entry.time)}</div>
                <div class="ai-agent-debug-message"><strong>${escapeAgentHtml(entry.stage)}</strong>${entry.message ? `<br>${escapeAgentHtml(entry.message)}` : ''}</div>
            </div>
        `).join('')
        : '<div class="ai-agent-debug-entry"><div class="ai-agent-debug-time">ready</div><div class="ai-agent-debug-message">No events recorded yet.</div></div>';
}

function toggleAiAgentDebug() {
    aiAgentDebugEnabled = !aiAgentDebugEnabled;
    localStorage.setItem('aiAgentDebugEnabled', aiAgentDebugEnabled ? '1' : '0');
    if (aiAgentDebugEnabled) {
        recordAiAgentDebug('debug-toggle', { state: 'enabled' });
        return;
    }
    syncAiAgentDebugUi();
}

function clearAiAgentDebugLog() {
    aiAgentDebugEntries = [];
    syncAiAgentDebugUi();
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
    if (sendBtn) {
        const blocked = aiAgentMessagingAvailabilityState.checked && !aiAgentMessagingAvailabilityState.available;
        sendBtn.disabled = blocked;
        sendBtn.title = blocked ? aiAgentMessagingAvailabilityState.message : '';
    }
    bar.classList.remove('is-hidden');
}

function extractAgentWorkspaceMarkup(doc, url) {
    if (url.includes('/messaging/ui')) {
        return doc.querySelector('#messaging-main-view')?.outerHTML || doc.body.innerHTML;
    }
    if (url.includes('/new-modal')) {
        const wrapper = document.createElement('div');
        const header = doc.querySelector('.sf-modal-header');
        if (header) {
            wrapper.appendChild(header.cloneNode(true));
        }
        const form = doc.querySelector('form');
        if (form) {
            wrapper.appendChild(form.cloneNode(true));
        } else {
            ['.sf-modal-body', '.sf-modal-footer'].forEach(selector => {
                const node = doc.querySelector(selector);
                if (node) wrapper.appendChild(node.cloneNode(true));
            });
        }
        Array.from(doc.body.children || [])
            .filter(node => node.tagName === 'SCRIPT')
            .forEach(script => wrapper.appendChild(script.cloneNode(true)));
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
    if (sourceUrl.includes('/new-modal')) {
        recordAiAgentDebug('workspace-wire', {
            sourceUrl,
            mode: 'workspace',
            forms: content.querySelectorAll('form').length,
        });
        content.dataset.modalSourceUrl = sourceUrl;
        wireAgentFormContainer(content, sourceUrl, {
            mode: 'workspace',
            onClose: () => closeAgentWorkspace(),
        });
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

function placeAgentWorkspaceProminently(panel, body) {
    if (!panel || !body) return;
    const selectionBar = document.getElementById('ai-agent-selection-bar');
    if (selectionBar && selectionBar.parentElement === body) {
        selectionBar.insertAdjacentElement('afterend', panel);
        return;
    }
    body.prepend(panel);
}

function scrollAgentWorkspaceIntoView(panel, body) {
    if (!panel || !body) return;
    const panelTop = panel.offsetTop;
    const bodyTop = body.offsetTop;
    const nextScrollTop = Math.max(panelTop - bodyTop - 8, 0);
    body.scrollTo({ top: nextScrollTop, behavior: 'smooth' });
    updateAiAgentJumpButtonVisibility();
}

function scrollAgentChatMessageIntoView(target) {
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    requestAnimationFrame(() => {
        updateAiAgentJumpButtonVisibility();
    });
}

function scrollAiAgentBodyToBottom() {
    const body = document.getElementById('ai-agent-body');
    if (!body || typeof body.scrollTo !== 'function') return;
    requestAnimationFrame(() => {
        body.scrollTo({ top: Number(body.scrollHeight || 0), behavior: 'smooth' });
        updateAiAgentJumpButtonVisibility();
    });
}

function getLatestAgentMessageNode() {
    const body = document.getElementById('ai-agent-body');
    if (!body || typeof body.querySelectorAll !== 'function') return null;
    const nodes = body.querySelectorAll('.msg-agent');
    return nodes && nodes.length ? nodes[nodes.length - 1] : null;
}

function updateAiAgentJumpButtonVisibility() {
    const body = document.getElementById('ai-agent-body');
    const button = document.getElementById('ai-agent-jump-btn');
    if (!body || !button) return;
    const scrollHeight = Number(body.scrollHeight || 0);
    const scrollTop = Number(body.scrollTop || 0);
    const clientHeight = Number(body.clientHeight || 0);
    const distanceFromBottom = Math.max(scrollHeight - scrollTop - clientHeight, 0);
    button.classList.toggle('is-visible', distanceFromBottom > 80);
}

function jumpToLatestAgentMessage() {
    const target = getLatestAgentMessageNode();
    if (target && typeof target.scrollIntoView === 'function') {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        scrollAiAgentBodyToBottom();
    }
    updateAiAgentJumpButtonVisibility();
}

function renderAgentWorkspaceFrame(content, url, title) {
    if (!content || !url) return;
    content.innerHTML = `
        <iframe
            class="agent-workspace-frame"
            src="${escapeAgentHtml(url)}"
            title="${escapeAgentHtml(title || 'Form')}"
            loading="eager"
        ></iframe>
    `;
}

function openAgentWorkspace(url, title, options = {}) {
    const panel = document.getElementById('ai-agent-workspace');
    const content = document.getElementById('ai-agent-workspace-content');
    const loading = document.getElementById('ai-agent-workspace-loading');
    const heading = document.getElementById('ai-agent-workspace-title');
    const body = document.getElementById('ai-agent-body');
    const preserveChatFocus = options.preserveChatFocus === true;
    if (!panel || !content || !loading || !heading || !url) return;

    recordAiAgentDebug('workspace-open', {
        url,
        title: title || 'Record View',
        panelFound: !!panel,
        contentFound: !!content,
        loadingFound: !!loading,
    });

    placeAgentWorkspaceProminently(panel, body);
    panel.dataset.recordTitle = title || 'Record View';
    panel.dataset.recordObjectType = getAiAgentObjectTypeFromPath(url) || '';
    panel.dataset.recordId = getAiAgentRecordIdFromPath(url) || '';

    heading.textContent = title || 'Record View';
    panel.classList.remove('agent-hidden');
    loading.classList.remove('agent-hidden');
    content.innerHTML = '';
    requestAnimationFrame(() => {
        const rect = panel.getBoundingClientRect();
        recordAiAgentDebug('workspace-visible', {
            top: Math.round(rect.top),
            height: Math.round(rect.height),
            hidden: panel.classList.contains('agent-hidden'),
            preserveChatFocus,
        });
    });
    if (!preserveChatFocus) {
        scrollAgentWorkspaceIntoView(panel, body);
    }
    if (url.includes('/new-modal')) {
        renderAgentWorkspaceFrame(content, url, title || 'Form');
        const frame = content.querySelector('.agent-workspace-frame');
        if (frame) {
            const frameTimeout = setTimeout(() => {
                loading.classList.add('agent-hidden');
                recordAiAgentDebug('workspace-frame-timeout', {
                    url,
                    title: title || 'Form',
                });
            }, AI_AGENT_WORKSPACE_TIMEOUT_MS);
            frame.addEventListener('load', () => {
                clearTimeout(frameTimeout);
                loading.classList.add('agent-hidden');
                recordAiAgentDebug('workspace-frame-load', {
                    url,
                    title: title || 'Form',
                });
                if (!preserveChatFocus) {
                    scrollAgentWorkspaceIntoView(panel, body);
                }
            }, { once: true });
        }
        recordAiAgentDebug('workspace-frame-open', {
            url,
            title: title || 'Form',
        });
        return;
    }
    fetchAiAgentWithTimeout(url, {}, AI_AGENT_WORKSPACE_TIMEOUT_MS)
        .then(async response => {
            const html = await response.text();
            recordAiAgentDebug('workspace-fetch', {
                url,
                status: response.status,
                ok: response.ok,
                bytes: html.length,
            });
            return html;
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const extracted = extractAgentWorkspaceMarkup(doc, url);
            recordAiAgentDebug('workspace-extract', {
                hasForm: !!doc.querySelector('form'),
                hasHeader: !!doc.querySelector('.sf-modal-header'),
                extractedBytes: extracted.length,
            });
            content.innerHTML = extracted;
            wireAgentWorkspaceInteractions(content, url);
            recordAiAgentDebug('workspace-render', {
                forms: content.querySelectorAll('form').length,
                scripts: content.querySelectorAll('script').length,
                text: content.textContent.trim().slice(0, 80),
            });
        })
        .catch(error => {
            console.error(error);
            recordAiAgentDebug('workspace-error', {
                url,
                message: error.message || String(error),
            });
            content.innerHTML = '<div class="sf-card" style="padding:1rem;color:var(--error);">Unable to load this record inside AI Agent.</div>';
        })
        .finally(() => {
            loading.classList.add('agent-hidden');
            recordAiAgentDebug('workspace-finish', {
                loadingHidden: loading.classList.contains('agent-hidden'),
                preserveChatFocus,
            });
            if (!preserveChatFocus) {
                scrollAgentWorkspaceIntoView(panel, body);
            }
        });
}

function openAgentWorkspaceHtml(title, html) {
    const panel = document.getElementById('ai-agent-workspace');
    const content = document.getElementById('ai-agent-workspace-content');
    const loading = document.getElementById('ai-agent-workspace-loading');
    const heading = document.getElementById('ai-agent-workspace-title');
    const body = document.getElementById('ai-agent-body');
    if (!panel || !content || !loading || !heading) return;
    placeAgentWorkspaceProminently(panel, body);
    heading.textContent = title || 'Record View';
    panel.classList.remove('agent-hidden');
    loading.classList.add('agent-hidden');
    content.innerHTML = html;
    wireAgentWorkspaceInteractions(content, 'inline-html');
    scrollAgentWorkspaceIntoView(panel, body);
}

function closeAgentWorkspace() {
    const panel = document.getElementById('ai-agent-workspace');
    const content = document.getElementById('ai-agent-workspace-content');
    const loading = document.getElementById('ai-agent-workspace-loading');
    if (panel) panel.classList.add('agent-hidden');
    if (content) content.innerHTML = '';
    if (loading) loading.classList.add('agent-hidden');
}

function clearAiAgentTransientLoadingState() {
    const workspaceLoading = document.getElementById('ai-agent-workspace-loading');
    const globalLoading = document.getElementById('sf-global-loading');
    if (workspaceLoading) workspaceLoading.classList.add('agent-hidden');
    if (typeof resetGlobalLoadingState === 'function') {
        resetGlobalLoadingState();
    } else if (globalLoading) {
        globalLoading.style.display = 'none';
    }

    document.querySelectorAll('.agent-chat-form-card.is-submitting').forEach(card => {
        card.classList.remove('is-submitting');
    });

    document.querySelectorAll('.agent-chat-form button[type="submit"]').forEach(button => {
        button.disabled = false;
    });
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

function completeAgentSendMessageHandoff(redirectUrl, messageText, templateId = null, selection = null) {
    const hasSelection = !!(selection && Array.isArray(selection.ids) && selection.ids.length);
    if (hasSelection) {
        sessionStorage.setItem('aiAgentMessageSelection', JSON.stringify(selection));
        sessionStorage.removeItem('aiAgentMessageGuidance');
    } else {
        sessionStorage.removeItem('aiAgentMessageSelection');
        sessionStorage.setItem('aiAgentMessageGuidance', JSON.stringify({
            source: 'ai_agent',
            steps: ['Choose recipients', 'Select a template or type your content', 'Review the preview and send'],
        }));
    }
    if (templateId) {
        sessionStorage.setItem('aiAgentMessageTemplate', templateId);
    } else {
        sessionStorage.removeItem('aiAgentMessageTemplate');
    }

    let appendedMessage = null;
    if (messageText) {
        appendedMessage = appendChatMessage('agent', messageText);
    }
    if (redirectUrl) {
        requestAnimationFrame(() => openAgentWorkspace(redirectUrl, 'Send Message', { preserveChatFocus: true }));
    }
}

function getAiAgentSendComposerState(composerId) {
    return aiAgentSendComposerState[composerId];
}

function setAiAgentSendComposerState(composerId, nextState) {
    aiAgentSendComposerState[composerId] = nextState;
}

function buildAgentMessageRecipientRows(rows, state) {
    const activeRows = Array.isArray(rows) ? rows : [];
    if (!activeRows.length) {
        return '<tr><td colspan="5" style="text-align:center;color:#7b8ba1;padding:18px;">No recipients found.</td></tr>';
    }
    return activeRows.map((item) => {
        const rowKey = String(item.id || item.contact_id || '');
        const checked = state.selectedContactIds.has(String(item.contact_id || ''));
        return `
            <tr>
                <td><input type="checkbox" ${checked ? 'checked' : ''} onchange="toggleAgentSendRecipient('${state.composerId}', '${String(item.contact_id || '')}', this.checked)"></td>
                <td><strong style="color:#16325c;">${escapeAgentHtml(item.contact?.name || '-')}</strong></td>
                <td>${escapeAgentHtml(item.contact?.phone || '-')}</td>
                <td>${escapeAgentHtml(item.stage || '-')}</td>
                <td>${escapeAgentHtml(item.model?.name || '-')}</td>
            </tr>
        `;
    }).join('');
}

function renderAgentSendPreview(state) {
    const bubbleText = state.messageType === 'SMS'
        ? (state.content || 'Your message preview will appear here.')
        : `${state.subject ? `${state.subject}\n\n` : ''}${state.content || 'Your message preview will appear here.'}`;

    return `
        <div class="agent-send-preview-panel">
            <div class="agent-send-panel-title">Mobile Preview</div>
            <div class="agent-send-preview-phone">
                <div class="agent-send-preview-notch"></div>
                <div class="agent-send-preview-screen">
                    <div class="agent-send-preview-header">
                        <div class="agent-send-preview-avatar">GK</div>
                        <div style="font-size:0.8rem;font-weight:700;color:#333;">GK CRM Support</div>
                    </div>
                    <div class="agent-send-preview-body">
                        <div class="agent-send-preview-bubble">${escapeAgentHtml(bubbleText)}</div>
                    </div>
                    <div class="agent-send-preview-footer">
                        <div class="agent-send-preview-input"></div>
                        <div class="agent-send-preview-dot"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderAgentSendComposerContent(state) {
    const selectedCount = state.selectedContactIds.size;
    const sourceRows = state.useRecommendations ? state.recommendedRecipients : state.defaultRecipients;
    const term = (state.searchTerm || '').toLowerCase().trim();
    const visibleRows = term
        ? sourceRows.filter((item) => JSON.stringify(item || {}).toLowerCase().includes(term))
        : sourceRows;
    const templateOptions = ['<option value="">-- Select Template --</option>']
        .concat(state.templates.map((tpl) => `<option value="${escapeAgentHtml(tpl.id)}" ${state.templateId === tpl.id ? 'selected' : ''}>${escapeAgentHtml(tpl.name)}</option>`))
        .join('');
    const isSms = state.messageType === 'SMS';
    const requiresMmsAsset = state.messageType === 'MMS' && !state.attachmentId;
    const hasMessageBody = Boolean((state.content || '').trim()) || Boolean(state.templateId);
    const canSaveRecipients = selectedCount > 0 && hasMessageBody;
    const canSend = selectedCount > 0 && hasMessageBody && !requiresMmsAsset;
    const guidanceText = requiresMmsAsset
        ? 'MMS needs an image-backed template in AI Agent. Choose an MMS template before sending.'
        : 'Choose recipients, save the current selection if needed, then select a template or write your message.';

    return `
        <div class="agent-send-composer-grid">
            <div style="display:flex;flex-direction:column;gap:18px;">
                <div class="agent-send-panel">
                    <div class="agent-send-panel-title">Recipients</div>
                    <div class="agent-send-toolbar">
                        <button type="button" class="agent-send-toggle ${state.useRecommendations ? 'is-active' : ''}" onclick="toggleAgentSendRecommendationMode('${state.composerId}', this)">${state.recommendationsLoading ? 'Loading...' : 'AI Recommend'}</button>
                        <input type="text" class="agent-send-search" value="${escapeAgentHtml(state.searchTerm || '')}" placeholder="Search recipients..." oninput="filterAgentSendRecipients('${state.composerId}', this.value)">
                    </div>
                    <div class="agent-send-recipient-wrap">
                        <table class="agent-send-recipient-table">
                            <thead>
                                <tr>
                                    <th style="width:36px;"><input type="checkbox" ${visibleRows.length && visibleRows.every((item) => state.selectedContactIds.has(String(item.contact_id || ''))) ? 'checked' : ''} onchange="toggleAllAgentSendRecipients('${state.composerId}', this.checked)"></th>
                                    <th>Name</th>
                                    <th>Phone</th>
                                    <th>Stage</th>
                                    <th>Model</th>
                                </tr>
                            </thead>
                            <tbody>${buildAgentMessageRecipientRows(visibleRows, state)}</tbody>
                        </table>
                    </div>
                    <div class="agent-send-status">${selectedCount} recipient(s) selected${state.useRecommendations ? ' · AI Recommend mode' : ''}</div>
                </div>
                <div class="agent-send-panel">
                    <div class="agent-send-panel-title">Compose</div>
                    <div class="agent-send-field">
                        <label>Template</label>
                        <select onchange="applyAgentSendTemplate('${state.composerId}', this.value)">${templateOptions}</select>
                    </div>
                    <div class="agent-send-radio-row">
                        ${['SMS', 'LMS', 'MMS'].map((type) => `<label><input type="radio" name="agent-send-type-${state.composerId}" value="${type}" ${state.messageType === type ? 'checked' : ''} onchange="setAgentSendType('${state.composerId}', '${type}')"> ${type}</label>`).join('')}
                    </div>
                    <div class="agent-send-field agent-send-subject ${isSms ? 'is-hidden' : ''}">
                        <label>Subject</label>
                        <input type="text" value="${escapeAgentHtml(state.subject || '')}" oninput="setAgentSendSubject('${state.composerId}', this.value)">
                    </div>
                    <div class="agent-send-field">
                        <label>Content</label>
                        <textarea oninput="setAgentSendContent('${state.composerId}', this.value)">${escapeAgentHtml(state.content || '')}</textarea>
                    </div>
                    <div class="agent-send-actions">
                        <div class="agent-send-guidance">${escapeAgentHtml(guidanceText)}</div>
                        <div class="agent-send-action-stack">
                            <button type="button" class="agent-send-secondary agent-send-secondary-accent" ${canSaveRecipients ? '' : 'disabled'} onclick="saveAgentSendRecipients('${state.composerId}')">Save Recipients</button>
                            <button type="button" class="agent-send-secondary" onclick="clearAgentSendComposer('${state.composerId}')">Clear All</button>
                            <button type="button" class="agent-send-submit" ${canSend ? '' : 'disabled'} onclick="submitAgentSendComposer('${state.composerId}', this)">Send Message</button>
                        </div>
                    </div>
                </div>
            </div>
            ${state.showPreview ? renderAgentSendPreview(state) : ''}
        </div>
    `;
}

function refreshAgentSendComposer(composerId) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    const shell = document.querySelector(`.agent-send-composer-shell[data-composer-id="${composerId}"]`);
    if (!shell) return;
    shell.innerHTML = renderAgentSendComposerContent(state);
}

async function loadAgentSendComposer(composerId) {
    const shell = document.querySelector(`.agent-send-composer-shell[data-composer-id="${composerId}"]`);
    const state = getAiAgentSendComposerState(composerId);
    if (!shell || !state) return;
    shell.innerHTML = '<div class="agent-send-composer-loading">Loading Send Message composer...</div>';
    try {
        const response = await fetchAiAgentWithTimeout('/messaging/ai-agent-compose-data', {}, AI_AGENT_WORKSPACE_TIMEOUT_MS);
        const payload = await response.json();
        if (!response.ok || payload.status === 'error') {
            throw new Error(payload.message || 'Failed to load Send Message data.');
        }
        state.defaultRecipients = Array.isArray(payload.default_recipients) ? payload.default_recipients : [];
        state.recommendedRecipients = [];
        state.templates = Array.isArray(payload.templates) ? payload.templates : [];
        if (state.templateId && !state.templates.some((tpl) => tpl.id === state.templateId)) {
            state.templateId = '';
        }
        if (state.selection && Array.isArray(state.selection.ids) && state.selection.ids.length) {
            const selectedIds = state.selection.ids.map((item) => String(item));
            const compareByOpportunity = state.selection.object_type === 'opportunity';
            state.defaultRecipients.forEach((row) => {
                const candidate = String(compareByOpportunity ? row.id : row.contact_id);
                if (selectedIds.includes(candidate)) state.selectedContactIds.add(String(row.contact_id));
            });
            state.recommendedRecipients.forEach((row) => {
                const candidate = String(compareByOpportunity ? row.id : row.contact_id);
                if (selectedIds.includes(candidate)) state.selectedContactIds.add(String(row.contact_id));
            });
        }
        if (state.templateId) {
            const template = state.templates.find((tpl) => tpl.id === state.templateId);
            if (template) {
                state.content = template.content || state.content;
                state.subject = template.subject || '';
                state.messageType = template.record_type || state.messageType;
                state.attachmentId = template.attachment_id || '';
            }
        }
        refreshAgentSendComposer(composerId);
    } catch (error) {
        console.error(error);
        shell.innerHTML = `<div class="agent-send-composer-error">${escapeAgentHtml(error.message || 'Unable to load Send Message composer.')}</div>`;
    }
}

function appendAgentSendMessageComposer(text, payload = {}) {
    const body = document.getElementById('ai-agent-body');
    if (!body) return;
    const composerId = `agent-send-${Date.now()}-${++aiAgentSendComposerCounter}`;
    setAiAgentSendComposerState(composerId, {
        composerId,
        selection: payload.selection || null,
        templateId: payload.templateId || '',
        searchTerm: '',
        useRecommendations: false,
        recommendationsLoaded: false,
        recommendationsLoading: false,
        defaultRecipients: [],
        recommendedRecipients: [],
        templates: [],
        selectedContactIds: new Set(),
        messageType: 'SMS',
        subject: '',
        content: '',
        attachmentId: '',
        showPreview: isAiAgentMaximized,
    });

    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg-agent';
    msgDiv.innerHTML = `
        <div class="msg-agent-header">
            <div class="msg-agent-icon">🤖</div>
            <span style="font-size: 0.8rem; font-weight: 700; color: #3e3e3c;">AI AGENT</span>
        </div>
        <div class="msg-agent-content">
            <div class="msg-agent-text">${escapeAgentHtml(text || 'I opened Send Message for you in chat.')}</div>
            <div class="agent-send-composer-card">
                <div class="agent-send-composer-shell" data-composer-id="${composerId}"></div>
            </div>
        </div>
    `;
    body.appendChild(msgDiv);
    loadAgentSendComposer(composerId);
    scrollAgentChatMessageIntoView(msgDiv);
}

async function toggleAgentSendRecommendationMode(composerId, btn) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    if (!state.recommendationsLoaded && !state.useRecommendations) {
        state.recommendationsLoading = true;
        refreshAgentSendComposer(composerId);
        try {
            const response = await fetchAiAgentWithTimeout('/messaging/recommendations', {}, AI_AGENT_WORKSPACE_TIMEOUT_MS);
            const payload = await response.json();
            if (!response.ok) {
                throw new Error('Failed to load AI recommended recipients.');
            }
            state.recommendedRecipients = Array.isArray(payload) ? payload : [];
            state.recommendationsLoaded = true;
        } catch (error) {
            appendChatMessage('agent', error.message || 'Failed to load AI recommended recipients.');
            state.recommendationsLoading = false;
            refreshAgentSendComposer(composerId);
            return;
        }
        state.recommendationsLoading = false;
    }
    state.useRecommendations = !state.useRecommendations;
    refreshAgentSendComposer(composerId);
}

function filterAgentSendRecipients(composerId, term) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    state.searchTerm = term || '';
    refreshAgentSendComposer(composerId);
}

function toggleAgentSendRecipient(composerId, contactId, checked) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    if (checked) state.selectedContactIds.add(String(contactId));
    else state.selectedContactIds.delete(String(contactId));
    refreshAgentSendComposer(composerId);
}

function toggleAllAgentSendRecipients(composerId, checked) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    const sourceRows = state.useRecommendations ? state.recommendedRecipients : state.defaultRecipients;
    const term = (state.searchTerm || '').toLowerCase().trim();
    const visibleRows = term
        ? sourceRows.filter((item) => JSON.stringify(item || {}).toLowerCase().includes(term))
        : sourceRows;
    visibleRows.forEach((row) => {
        const contactId = String(row.contact_id || '');
        if (!contactId) return;
        if (checked) state.selectedContactIds.add(contactId);
        else state.selectedContactIds.delete(contactId);
    });
    refreshAgentSendComposer(composerId);
}

function applyAgentSendTemplate(composerId, templateId) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    state.templateId = templateId || '';
    const template = state.templates.find((tpl) => tpl.id === state.templateId);
    if (template) {
        state.messageType = template.record_type || 'SMS';
        state.subject = template.subject || '';
        state.content = template.content || '';
        state.attachmentId = template.attachment_id || '';
    } else {
        state.attachmentId = '';
    }
    refreshAgentSendComposer(composerId);
}

function saveAgentSendRecipients(composerId) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    const selectedCount = state.selectedContactIds.size;
    if (!selectedCount) {
        appendChatMessage('agent', 'Select one or more recipients before saving them.');
        return;
    }
    if (!Boolean((state.content || '').trim()) && !Boolean(state.templateId)) {
        appendChatMessage('agent', 'Choose a template or enter message content before saving recipients.');
        return;
    }
    const sourceRows = state.useRecommendations ? state.recommendedRecipients : state.defaultRecipients;
    const selectedRows = sourceRows.filter((row) => state.selectedContactIds.has(String(row.contact_id || '')));
    const names = selectedRows.map((row) => (row.contact || {}).name || 'Recipient');
    const template = state.templates.find((tpl) => tpl.id === state.templateId);
    const templateName = template?.name || 'Custom';
    const recipientPreview = names.slice(0, 3).join(', ');
    const extraCount = Math.max(names.length - 3, 0);
    const recipientLabel = extraCount > 0 ? `${recipientPreview} and ${extraCount} more` : recipientPreview;
    appendChatMessage('agent', `Saved recipients: ${recipientLabel}. Template: ${templateName}. Type: ${state.messageType || 'SMS'}.`);
}

function clearAgentSendComposer(composerId) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    state.searchTerm = '';
    state.useRecommendations = false;
    state.selectedContactIds = new Set();
    state.templateId = '';
    state.messageType = 'SMS';
    state.subject = '';
    state.content = '';
    state.attachmentId = '';
    refreshAgentSendComposer(composerId);
}

function setAgentSendType(composerId, type) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    state.messageType = type;
    if (type === 'SMS') state.subject = '';
    refreshAgentSendComposer(composerId);
}

function setAgentSendSubject(composerId, subject) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    state.subject = subject || '';
}

function setAgentSendContent(composerId, content) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state) return;
    state.content = content || '';
}

async function submitAgentSendComposer(composerId, btn) {
    const state = getAiAgentSendComposerState(composerId);
    if (!state || !state.selectedContactIds.size) return;
    if (!state.templateId && !(state.content || '').trim()) {
        appendChatMessage('agent', 'Choose a template or enter message content before sending.');
        return;
    }
    if (state.messageType === 'MMS' && !state.attachmentId) {
        appendChatMessage('agent', 'MMS requires an image-backed template in AI Agent. Choose an MMS template first.');
        return;
    }
    const selectedIds = Array.from(state.selectedContactIds);
    if (btn) btn.disabled = true;
    try {
        const availabilityResponse = await fetchAiAgentWithTimeout('/messaging/demo-availability', {}, AI_AGENT_WORKSPACE_TIMEOUT_MS);
        const availabilityPayload = await availabilityResponse.json();
        if (!availabilityResponse.ok || !availabilityPayload.available) {
            throw new Error(availabilityPayload.message || '메시지 서비스에 연결할 수 없습니다. 관리자에게 문의해주세요!');
        }
        const response = await fetchAiAgentWithTimeout('/messaging/bulk-send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contact_ids: selectedIds,
                template_id: state.templateId || null,
                content: state.content || '',
                record_type: state.messageType || 'SMS',
                attachment_id: state.attachmentId || null,
                subject: state.messageType === 'SMS' ? null : (state.subject || ''),
            }),
        }, AI_AGENT_WORKSPACE_TIMEOUT_MS);
        const payload = await response.json();
        if (!response.ok || payload.status === 'error') {
            throw new Error(payload.message || 'Failed to send messages.');
        }
        appendChatMessage('agent', `Sent ${payload.sent_count || selectedIds.length} message(s) from AI Agent.`);
    } catch (error) {
        appendChatMessage('agent', error.message || 'Failed to send messages.');
    } finally {
        if (btn) btn.disabled = false;
    }
}

function startTemplateSendFromAgent(templateId) {
    if (!templateId) return;
    appendAgentSendMessageComposer(
        `Template prepared for Send Message. I'll open the messaging screen with template \`${templateId}\` ready.`,
        { templateId }
    );
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
        recordAiAgentDebug('panel-load', { status: response.status });
        return true;
    } catch (error) {
        console.error(error);
        recordAiAgentDebug('panel-load-error', { message: error.message || String(error) });
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

    Object.keys(aiAgentSendComposerState).forEach((composerId) => {
        const state = getAiAgentSendComposerState(composerId);
        if (!state) return;
        state.showPreview = isAiAgentMaximized;
        refreshAgentSendComposer(composerId);
    });
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
    stopAiAgentVoiceRecording({ discard: true });
    aiAgentVoiceTranscribing = false;

    aiAgentConversationId = createConversationId();
    aiAgentSelectionState = {};
    aiAgentActiveSelectionObject = null;
    aiAgentDebugEntries = [];
    sessionStorage.removeItem('aiAgentMessageSelection');
    applyAiAgentLanguageUi();
    recordAiAgentDebug('agent-reset', { conversationId: aiAgentConversationId });
    updateSelectionBar();
}

function updateAiAgentComposerState() {
    const input = document.getElementById('ai-agent-input');
    const clearBtn = document.getElementById('ai-agent-input-clear');
    const micBtn = document.getElementById('ai-agent-mic-btn');
    const sendBtn = document.getElementById('ai-agent-send-btn');
    const hasText = Boolean((input?.value || '').trim());

    if (clearBtn) {
        clearBtn.classList.toggle('is-visible', hasText);
        clearBtn.disabled = aiAgentVoiceRecording || aiAgentVoiceTranscribing;
        clearBtn.setAttribute('aria-hidden', hasText ? 'false' : 'true');
    }

    if (micBtn) {
        micBtn.classList.toggle('is-recording', aiAgentVoiceRecording);
        micBtn.classList.toggle('is-busy', aiAgentVoiceTranscribing);
        micBtn.disabled = aiAgentVoiceTranscribing;
        micBtn.setAttribute('aria-label', aiAgentVoiceRecording ? 'Stop voice input' : 'Start voice input');
        micBtn.setAttribute('title', aiAgentVoiceRecording ? 'Stop voice input' : (aiAgentVoiceTranscribing ? 'Transcribing audio...' : 'Start voice input'));
    }

    if (sendBtn) {
        sendBtn.disabled = aiAgentVoiceTranscribing;
        sendBtn.setAttribute('title', aiAgentVoiceTranscribing ? 'Transcribing audio...' : 'Send message');
    }
}

function clearAiAgentInput() {
    const input = document.getElementById('ai-agent-input');
    if (!input) return;
    input.value = '';
    updateAiAgentComposerState();
    if (typeof input.focus === 'function') input.focus();
}

function applyAiAgentTranscript(text) {
    const input = document.getElementById('ai-agent-input');
    if (!input) return;
    input.value = String(text || '').trim();
    updateAiAgentComposerState();
    if (typeof input.focus === 'function') input.focus();
}

function stopAiAgentRecorderStream() {
    if (!aiAgentRecorderStream || typeof aiAgentRecorderStream.getTracks !== 'function') return;
    aiAgentRecorderStream.getTracks().forEach(track => {
        if (track && typeof track.stop === 'function') {
            track.stop();
        }
    });
    aiAgentRecorderStream = null;
}

async function transcribeAiAgentAudioBlob(audioBlob) {
    if (!audioBlob) return;
    aiAgentVoiceTranscribing = true;
    updateAiAgentComposerState();
    recordAiAgentDebug('voice-transcribe-request', {
        size: audioBlob.size || 0,
        type: audioBlob.type || 'application/octet-stream',
        conversationId: aiAgentConversationId,
    });

    try {
        const payload = new FormData();
        payload.append('audio', audioBlob, audioBlob.name || 'ai-agent-voice.webm');
        payload.append('conversation_id', aiAgentConversationId);
        payload.append('language_preference', aiAgentLanguagePreference);

        const response = await fetch('/ai-agent/api/stt', {
            method: 'POST',
            body: payload,
        });
        const data = await response.json();
        recordAiAgentDebug('voice-transcribe-response', {
            status: response.status,
            ok: response.ok,
            provider: data.provider,
            validator: data.validator,
            textLength: (data.text || '').length,
        });

        if (!response.ok || data.status === 'error' || !data.text) {
            throw new Error(data.text || data.error || 'Unable to transcribe audio right now.');
        }

        applyAiAgentTranscript(data.text);
    } catch (error) {
        recordAiAgentDebug('voice-transcribe-error', {
            message: error.message || String(error),
        });
        appendChatMessage('agent', error.message || 'Voice input is unavailable right now.');
    } finally {
        aiAgentVoiceTranscribing = false;
        updateAiAgentComposerState();
    }
}

async function startAiAgentVoiceRecording() {
    if (aiAgentVoiceRecording || aiAgentVoiceTranscribing) return;
    if (!navigator?.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
        appendChatMessage('agent', 'Voice input is not supported in this browser.');
        return;
    }

    try {
        aiAgentRecorderStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        aiAgentRecorderChunks = [];
        aiAgentMediaRecorder = new MediaRecorder(aiAgentRecorderStream);
        aiAgentMediaRecorder.addEventListener('dataavailable', (event) => {
            if (event.data && event.data.size) {
                aiAgentRecorderChunks.push(event.data);
            }
        });
        aiAgentMediaRecorder.addEventListener('stop', async () => {
            const audioType = aiAgentRecorderChunks[0]?.type || 'audio/webm';
            const audioBlob = new Blob(aiAgentRecorderChunks, { type: audioType });
            stopAiAgentRecorderStream();
            aiAgentRecorderChunks = [];
            await transcribeAiAgentAudioBlob(audioBlob);
        });
        aiAgentMediaRecorder.start();
        aiAgentVoiceRecording = true;
        updateAiAgentComposerState();
        recordAiAgentDebug('voice-recording-started', { conversationId: aiAgentConversationId });
    } catch (error) {
        stopAiAgentRecorderStream();
        aiAgentMediaRecorder = null;
        aiAgentVoiceRecording = false;
        updateAiAgentComposerState();
        appendChatMessage('agent', error.message || 'Microphone access is unavailable.');
    }
}

function stopAiAgentVoiceRecording(options = {}) {
    const discard = options.discard === true;
    if (!aiAgentMediaRecorder) {
        aiAgentVoiceRecording = false;
        stopAiAgentRecorderStream();
        updateAiAgentComposerState();
        return;
    }

    const recorder = aiAgentMediaRecorder;
    aiAgentMediaRecorder = null;
    aiAgentVoiceRecording = false;
    updateAiAgentComposerState();
    recordAiAgentDebug('voice-recording-stopped', { discard });

    if (discard) {
        recorder.onstop = null;
        aiAgentRecorderChunks = [];
        try {
            if (recorder.state && recorder.state !== 'inactive') recorder.stop();
        } catch (error) {
            console.warn(error);
        }
        stopAiAgentRecorderStream();
        return;
    }

    try {
        if (!recorder.state || recorder.state !== 'inactive') {
            recorder.stop();
        } else {
            stopAiAgentRecorderStream();
        }
    } catch (error) {
        stopAiAgentRecorderStream();
        appendChatMessage('agent', error.message || 'Voice input stopped unexpectedly.');
    }
}

function toggleAiAgentVoiceRecording() {
    if (aiAgentVoiceRecording) {
        stopAiAgentVoiceRecording();
        return;
    }
    startAiAgentVoiceRecording();
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
    recordAiAgentDebug('chat-request', {
        query,
        page: pageOverride,
        conversationId: aiAgentConversationId,
        selectionObject: aiAgentActiveSelectionObject,
    });
    const response = await fetchAiAgentWithTimeout('/ai-agent/api/chat', {
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
    const data = await response.json();
    recordAiAgentDebug('chat-response', {
        query,
        status: response.status,
        intent: data.intent,
        objectType: data.object_type,
        recordId: data.record_id,
    });
    return data;
}

async function submitAiAgentFormResponse(payload) {
    recordAiAgentDebug('chat-form-request', {
        objectType: payload.object_type,
        mode: payload.mode,
        recordId: payload.record_id,
        fieldNames: Object.keys(payload.values || {}),
    });
    const response = await fetchAiAgentWithTimeout('/ai-agent/api/form-submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ...payload,
            conversation_id: aiAgentConversationId,
            language_preference: aiAgentLanguagePreference,
        }),
    });
    const data = await response.json();
    recordAiAgentDebug('chat-form-response', {
        status: response.status,
        intent: data.intent,
        objectType: data.object_type,
        recordId: data.record_id,
    });
    return data;
}

function getInlineAiCrudContext(sourceUrl) {
    const pathname = sourceUrl?.pathname || '';
    const recordId = sourceUrl?.searchParams?.get('id') || null;
    if (pathname === '/leads/new-modal') {
        return { objectType: 'lead', mode: recordId ? 'edit' : 'create', recordId };
    }
    if (pathname === '/contacts/new-modal') {
        return { objectType: 'contact', mode: recordId ? 'edit' : 'create', recordId };
    }
    if (pathname === '/opportunities/new-modal') {
        return { objectType: 'opportunity', mode: recordId ? 'edit' : 'create', recordId };
    }
    if (pathname === '/assets/new-modal') {
        return { objectType: 'asset', mode: recordId ? 'edit' : 'create', recordId };
    }
    if (pathname === '/models/new-modal') {
        return { objectType: 'model', mode: recordId ? 'edit' : 'create', recordId };
    }
    if (pathname === '/message_templates/new-modal') {
        return { objectType: 'message_template', mode: recordId ? 'edit' : 'create', recordId };
    }
    if (pathname === '/vehicle_specifications/new-modal' && sourceUrl?.searchParams?.get('type') === 'Brand') {
        return { objectType: 'brand', mode: recordId ? 'edit' : 'create', recordId };
    }
    return null;
}

function hasSelectedInlineFileForAiManagedSubmit(form) {
    if (!form || typeof form.querySelectorAll !== 'function') return false;
    return Array.from(form.querySelectorAll('input[type="file"]')).some((input) => input?.files && input.files.length > 0);
}

function hasPendingInlineImageRemoval(form) {
    if (!form || typeof form.querySelector !== 'function') return false;
    return form.querySelector('input[name="remove_image"]')?.value === 'true';
}

function collectInlineFormValues(form) {
    const formData = new FormData(form);
    const values = {};
    for (const [key, rawValue] of formData.entries()) {
        if (!key || key === 'id') continue;
        if (typeof rawValue !== 'string') continue;
        values[key] = rawValue;
    }
    return values;
}

async function handleAiManagedInlineFormSubmit(container, sourceUrl, submitMode, closeHandler) {
    const context = getInlineAiCrudContext(sourceUrl);
    if (!context) return false;
    const form = container.querySelector('form');
    if (hasSelectedInlineFileForAiManagedSubmit(form)) {
        return false;
    }
    if (context.objectType === 'message_template' && hasPendingInlineImageRemoval(form)) {
        return false;
    }

    const data = await submitAiAgentFormResponse({
        form_id: `${context.objectType}:${context.mode}:${context.recordId || 'session'}`,
        object_type: context.objectType,
        mode: context.mode,
        record_id: context.recordId,
        values: collectInlineFormValues(form),
    });

    if (data.intent === 'OPEN_RECORD') {
        closeHandler();
        if (data.text) {
            appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query, data.chat_card);
        }

        if (submitMode === 'save-new') {
            sourceUrl.searchParams.delete('id');
            await appendAgentInlineFormMessage(`I opened the ${context.objectType} create form here in chat. Fill in the fields you want, then save it.`, `${sourceUrl.pathname}${sourceUrl.search}`, `Create ${context.objectType}`);
            return true;
        }
        return true;
    }

    if (data.intent === 'OPEN_FORM' && data.form?.fields) {
        closeHandler();
        appendAgentSchemaFormMessage(data.text || 'Review the highlighted fields and try again.', data.form);
        return true;
    }

    if (data.text) {
        appendChatMessage('agent', data.text);
        return true;
    }

    return false;
}

function getAiAgentObjectTypeFromPath(pathname) {
    const mappings = [
        ['/leads/', 'lead'],
        ['/contacts/', 'contact'],
        ['/opportunities/', 'opportunity'],
        ['/products/', 'product'],
        ['/assets/', 'asset'],
        ['/vehicle_specifications/', 'brand'],
        ['/models/', 'model'],
        ['/message_templates/', 'message_template'],
    ];
    const match = mappings.find(([prefix]) => String(pathname || '').startsWith(prefix));
    return match ? match[1] : null;
}

function getAiAgentRecordIdFromPath(pathname) {
    const parts = String(pathname || '').split('/').filter(Boolean);
    return parts.length >= 2 ? parts[1] : null;
}

async function resolveAgentOpenRecordFromRedirect(finalUrl) {
    const objectType = getAiAgentObjectTypeFromPath(finalUrl?.pathname);
    const recordId = getAiAgentRecordIdFromPath(finalUrl?.pathname);
    if (!objectType || !recordId) return null;
    try {
        const data = await fetchAiAgentResponse(`Manage ${objectType} ${recordId}`);
        return data?.intent === 'OPEN_RECORD' ? data : null;
    } catch (_error) {
        return null;
    }
}

async function sendAiMessage(queryOverride = null, pageOverride = 1) {
    const input = document.getElementById('ai-agent-input');
    const query = (queryOverride ?? input.value).trim();
    if (!query) return;

    if (!queryOverride) {
        recordQuickGuideActivity(query, query);
        appendChatMessage('user', query);
        input.value = '';
        updateAiAgentComposerState();
    }

    const loadingId = 'loading-' + Date.now();
    appendChatMessage('agent', '<span class="loading-dots">Thinking</span>', loadingId);

    try {
        const data = await fetchAiAgentResponse(query, pageOverride);
        recordAiAgentDebug('chat-handle-intent', {
            intent: data.intent,
            objectType: data.object_type,
            recordId: data.record_id,
        });
        
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
            const fallbackDetailUrl = data.object_type && data.record_id
                ? getAgentObjectRoute(data.object_type, data.record_id, 'detail')
                : null;
            const targetUrl = data.redirect_url || fallbackDetailUrl;
            const preserveChatFocus = data.object_type === 'lead' || data.object_type === 'contact' || data.object_type === 'opportunity' || data.object_type === 'product' || data.object_type === 'asset' || data.object_type === 'brand' || data.object_type === 'model' || data.object_type === 'message_template';
            let appendedMessage = null;
            if (preserveChatFocus && data.text) {
                appendedMessage = appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query, data.chat_card);
            }
            if (targetUrl) {
                const workspaceTitle = data.chat_card?.title || data.form_title || 'Record View';
                recordAiAgentDebug('chat-open-record', {
                    objectType: data.object_type,
                    recordId: data.record_id,
                    targetUrl,
                    preserveChatFocus,
                });
                if (preserveChatFocus) {
                    requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle, { preserveChatFocus }));
                } else {
                    openAgentWorkspace(targetUrl, workspaceTitle);
                }
            }
            if (!preserveChatFocus && data.text) {
                appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query, data.chat_card);
            }
            return;
        }

        // Handle Send Message intent
        if (data.intent === 'SEND_MESSAGE') {
            appendAgentSendMessageComposer(
                data.text,
                {
                    redirectUrl: data.redirect_url,
                    templateId: data.template_id,
                    selection: data.selection,
                }
            );
            return;
        }

        if (data.intent === 'OPEN_FORM' && data.form_url) {
            recordAiAgentDebug('intent-open-form', {
                objectType: data.object_type,
                formUrl: data.form_url,
                title: data.form_title || 'Form',
            });
            appendAgentInlineFormMessage(data.text || 'I opened the form for you.', data.form_url, data.form_title || 'Form');
            return;
        }

        if (data.intent === 'OPEN_FORM' && data.form?.fields) {
            recordAiAgentDebug('intent-open-form-inline', {
                objectType: data.object_type,
                mode: data.form.mode,
                formId: data.form.form_id,
            });
            appendAgentSchemaFormMessage(data.text || 'I opened the form for you.', data.form);
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
        clearAiAgentTransientLoadingState();
        appendChatMessage('agent', "Sorry, I encountered an error connecting to the AI service.");
    }
}

function consumePendingDeleteShortcut(queryText) {
    const pending = window._agentPendingDelete;
    const trimmed = String(queryText || '').trim().toLowerCase();
    if (!pending || !trimmed) return null;

    if (trimmed === 'yes') {
        window._agentPendingDelete = null;
        return {
            displayText: 'Yes',
            actualQuery: pending.ids && pending.ids.length > 1
                ? `[FORCE_DELETE] Delete selected ${pending.objectType} records`
                : `[FORCE_DELETE] Delete ${pending.objectType} ${pending.ids ? pending.ids[0] : pending.recordId}`,
        };
    }

    if (trimmed === 'cancel') {
        window._agentPendingDelete = null;
        return {
            displayText: 'Cancel',
            actualQuery: null,
            cancelOnly: true,
        };
    }

    return null;
}

function appendChatMessage(role, text, id = null, sql = null, results = null, objectType = null, pagination = null, originalQuery = null, chatCard = null) {
    const body = document.getElementById('ai-agent-body');
    if (!body) return null;

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
            return `<button type="button" class="${actionClass}" onclick="event.preventDefault(); event.stopPropagation(); sendQuickMessage('${p1}'); return false;">${p1}</button>`;
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
            innerHTML += `
                <details class="agent-sql-details">
                    <summary class="agent-sql-summary">SQL</summary>
                    <div class="sql-block">${sql}</div>
                </details>
            `;
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
    scrollAgentChatMessageIntoView(msgDiv);
    return msgDiv;
}

function removeExistingAgentInlineForms() {
    document.querySelectorAll('.agent-inline-form-shell').forEach(node => node.remove());
}

function removeExistingAgentSchemaForms() {
    document.querySelectorAll('.agent-chat-form-card').forEach(node => node.remove());
}

function scrollAgentSchemaFormIntoView(target) {
    if (!target) return;
    scrollAgentChatMessageIntoView(target);
}

function appendAgentSchemaFormMessage(text, formSchema) {
    const body = document.getElementById('ai-agent-body');
    if (!body || !formSchema) return;

    removeExistingAgentSchemaForms();

    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg-agent';
    msgDiv.innerHTML = `
        <div class="msg-agent-header">
            <div class="msg-agent-icon">🤖</div>
            <span style="font-size: 0.8rem; font-weight: 700; color: #3e3e3c;">AI AGENT</span>
        </div>
        <div class="msg-agent-content">
            <div class="msg-agent-text">${text}</div>
            ${renderAgentChatCard({ type: 'inline_form', form: formSchema })}
        </div>
    `;
    body.appendChild(msgDiv);
    initAgentFormClearButtons(msgDiv);
    initAgentChatLookupFields(msgDiv);
    scrollAgentSchemaFormIntoView(msgDiv);
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

    scrollAgentChatMessageIntoView(msgDiv);
}

async function loadAgentInlineForm(shell, formUrl, formTitle) {
    if (!shell || !formUrl) return;

    try {
        const response = await fetchAiAgentWithTimeout(formUrl, {}, AI_AGENT_WORKSPACE_TIMEOUT_MS);
        const html = await response.text();
        recordAiAgentDebug('inline-form-fetch', {
            formUrl,
            status: response.status,
            ok: response.ok,
            bytes: html.length,
        });
        const doc = new DOMParser().parseFromString(html, 'text/html');
        shell.innerHTML = extractAgentWorkspaceMarkup(doc, formUrl);
        shell.dataset.modalSourceUrl = formUrl;
        shell.dataset.formTitle = formTitle || 'Form';
        wireAgentFormContainer(shell, formUrl, {
            mode: 'inline',
            onClose: () => shell.remove(),
        });
    } catch (error) {
        console.error(error);
        recordAiAgentDebug('inline-form-error', {
            formUrl,
            message: error.message || String(error),
        });
        shell.innerHTML = '<div class="agent-inline-form-error">Unable to load the form here right now.</div>';
    }
}

function initializeAiAgentTemplateModalUi(container) {
    if (!container || typeof container.querySelector !== 'function') return;
    const form = container.querySelector('form');
    if (!form) return;
    const typeSelect = form.querySelector('select[name="record_type"]');
    const contentTextarea = form.querySelector('textarea[name="content"]');
    const subjectWrapper = form.querySelector('.sf-field-wrapper[data-field="subject"]');
    const imageWrapper = form.querySelector('.sf-field-wrapper[data-field="image"]');
    const byteCounter = form.querySelector('#byte-counter');
    const saveBtn = form.querySelector('button.btn-primary');
    const imageInput = form.querySelector('#modal-form-image-input');
    const removeImageInput = form.querySelector('#modal-form-remove-image');

    if (!typeSelect || !contentTextarea || !subjectWrapper || !imageWrapper || !byteCounter || !saveBtn) {
        return;
    }

    function getByteLength(str) {
        let len = 0;
        for (let i = 0; i < str.length; i++) {
            len += str.charCodeAt(i) > 127 ? 2 : 1;
        }
        return len;
    }

    function renderScopedTemplateImageState() {
        const emptyState = form.querySelector('#modal-form-image-empty');
        const previewWrap = form.querySelector('#modal-form-image-preview-wrap');
        const preview = form.querySelector('#modal-form-image-preview');
        const meta = form.querySelector('#modal-form-image-meta');
        const helper = form.querySelector('#modal-form-image-helper');
        const error = form.querySelector('#modal-form-image-error');
        const removeRequested = removeImageInput?.value === 'true';
        const currentUrl = removeRequested ? '' : (imageInput?.dataset?.currentUrl || '');
        const activeUrl = imageInput?.dataset?.previewUrl || currentUrl;

        if (error) {
            error.style.display = 'none';
            error.textContent = '';
        }
        if (!emptyState || !previewWrap || !preview || !meta) return;
        if (typeSelect.value !== 'MMS') {
            emptyState.style.display = 'none';
            previewWrap.style.display = 'none';
            preview.src = '';
            meta.textContent = '';
            if (helper) helper.textContent = '';
            return;
        }
        if (activeUrl) {
            emptyState.style.display = 'none';
            previewWrap.style.display = 'block';
            preview.src = activeUrl;
            meta.textContent = imageInput?.dataset?.previewName || (currentUrl ? 'Current template image' : 'Selected JPG image');
            if (helper) {
                helper.textContent = imageInput?.dataset?.previewUrl
                    ? 'Image selected. Click Save to apply it.'
                    : '';
            }
            return;
        }
        emptyState.style.display = 'block';
        previewWrap.style.display = 'none';
        preview.src = '';
        meta.textContent = '';
        if (helper) {
            helper.textContent = removeRequested ? 'Image removal staged. Click Save to apply it.' : '';
        }
    }

    function updateScopedTemplateUi() {
        const type = typeSelect.value || 'SMS';
        const content = contentTextarea.value || '';
        const bytes = getByteLength(content);
        const limit = type === 'SMS' ? 90 : 2000;

        if (type === 'SMS' && bytes > 90) {
            typeSelect.value = 'LMS';
            updateScopedTemplateUi();
            return;
        }

        subjectWrapper.style.display = type === 'SMS' ? 'none' : 'flex';
        imageWrapper.style.display = type === 'MMS' ? 'flex' : 'none';
        renderScopedTemplateImageState();

        byteCounter.textContent = `${bytes} / ${limit} bytes (${typeSelect.value})`;
        if (bytes > limit) {
            byteCounter.style.color = '#ea001e';
            saveBtn.disabled = true;
            saveBtn.style.opacity = '0.5';
        } else {
            byteCounter.style.color = '';
            saveBtn.disabled = false;
            saveBtn.style.opacity = '1';
        }
    }

    if (imageInput) {
        imageInput.dataset.currentUrl = imageInput.dataset.currentUrl || '';
        imageInput.dataset.previewUrl = imageInput.dataset.previewUrl || '';
        imageInput.dataset.previewName = imageInput.dataset.previewName || '';
    }
    if (typeSelect.dataset.aiAgentTemplateBound === 'true') {
        updateScopedTemplateUi();
        return;
    }
    typeSelect.dataset.aiAgentTemplateBound = 'true';
    typeSelect.addEventListener('change', updateScopedTemplateUi);
    contentTextarea.addEventListener('input', updateScopedTemplateUi);
    updateScopedTemplateUi();
}

function wireAgentFormContainer(container, formUrl, options = {}) {
    if (!container) return;
    const mode = options.mode || 'inline';
    const closeHandler = typeof options.onClose === 'function'
        ? options.onClose
        : (() => container.remove());

    if (String(formUrl || '').includes('/message_templates/new-modal')) {
        initializeAiAgentTemplateModalUi(container);
    }

    container.querySelectorAll('script').forEach(script => {
        const replacement = document.createElement('script');
        replacement.textContent = script.textContent;
        document.body.appendChild(replacement);
        replacement.remove();
    });

    container.querySelectorAll('[onclick="closeModal()"], .sf-modal-header span[onclick]').forEach(node => {
        node.removeAttribute('onclick');
        node.addEventListener('click', () => closeHandler());
    });

    container.querySelectorAll('form').forEach(form => {
        if (form.dataset.aiAgentInlineEnhanced === 'true') return;
        form.dataset.aiAgentInlineEnhanced = 'true';
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const submitter = event.submitter || document.activeElement;
            const submitMode = submitter?.dataset?.submitMode || 'save';
            const submitButton = submitter || form.querySelector('button[type="submit"]');
            const sourceUrl = new URL(container.dataset.modalSourceUrl || formUrl, window.location.origin);
            const detailLoading = document.getElementById('ai-agent-workspace-loading');

            if (typeof validateForm === 'function' && validateForm(form) === false) {
                recordAiAgentDebug('form-validate', {
                    formUrl,
                    mode,
                    result: 'blocked',
                });
                return;
            }

            if (submitButton) submitButton.disabled = true;
            if (mode === 'workspace' && detailLoading) detailLoading.classList.remove('agent-hidden');
            recordAiAgentDebug('form-submit', {
                formUrl,
                mode,
                submitMode,
                action: form.action || formUrl,
            });

            try {
                const aiManaged = await handleAiManagedInlineFormSubmit(container, sourceUrl, submitMode, closeHandler);
                if (aiManaged) {
                    return;
                }

                const response = await fetchAiAgentWithTimeout(form.action || formUrl, {
                    method: (form.method || 'POST').toUpperCase(),
                    body: new FormData(form),
                    headers: { 'Accept': 'text/html,application/json' },
                    redirect: 'follow',
                });

                const contentType = response.headers.get('content-type') || '';
                recordAiAgentDebug('form-response', {
                    formUrl,
                    status: response.status,
                    redirected: response.redirected,
                    contentType,
                });
                if (contentType.includes('application/json')) {
                    const data = await response.json();
                    if (!response.ok || data.status === 'error') {
                        throw new Error(data.message || 'Failed to save the form.');
                    }
                    appendChatMessage('agent', data.message || 'Form saved successfully.');
                    closeHandler();
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
                        sourceUrl.searchParams.delete('id');
                        if (mode === 'workspace') {
                            openAgentWorkspace(`${sourceUrl.pathname}${sourceUrl.search}`, container.dataset.formTitle || 'Form');
                        } else {
                            await loadAgentInlineForm(container, `${sourceUrl.pathname}${sourceUrl.search}`, container.dataset.formTitle || 'Form');
                        }
                        return;
                    }

                    // Open the saved record directly instead of relying on a second chat turn.
                    // Legacy workspace fallback reference: openAgentWorkspace(finalUrl.pathname, workspaceTitle);
                    const managedOpenRecord = await resolveAgentOpenRecordFromRedirect(finalUrl);
                    closeHandler();
                    if (managedOpenRecord?.text) {
                        appendChatMessage(
                            'agent',
                            managedOpenRecord.text,
                            null,
                            managedOpenRecord.sql,
                            managedOpenRecord.results,
                            managedOpenRecord.object_type,
                            managedOpenRecord.pagination,
                            managedOpenRecord.original_query,
                            managedOpenRecord.chat_card,
                        );
                    } else {
                        appendChatMessage('agent', successMsg);
                    }
                    return;
                }

                const html = await response.text();
                const doc = new DOMParser().parseFromString(html, 'text/html');
                container.innerHTML = extractAgentWorkspaceMarkup(doc, formUrl);
                wireAgentFormContainer(container, formUrl, options);
                appendChatMessage('agent', 'Save did not complete. Review the highlighted form and try again.');
            } catch (error) {
                console.error(error);
                recordAiAgentDebug('form-error', {
                    formUrl,
                    mode,
                    message: error.message || String(error),
                });
                appendChatMessage('agent', error.message || 'Failed to save the form.');
            } finally {
                if (submitButton) submitButton.disabled = false;
                if (mode === 'workspace' && detailLoading) detailLoading.classList.add('agent-hidden');
            }
        });
    });
}

function sendQuickMessage(text) {
    const input = document.getElementById('ai-agent-input');
    if (!input) return;
    if (text === 'Send Message' && !ensureAiAgentMessagingAvailable()) {
        return;
    }
    const deleteShortcut = consumePendingDeleteShortcut(text);
    if (deleteShortcut) {
        appendChatMessage('user', deleteShortcut.displayText);
        if (deleteShortcut.cancelOnly) {
            appendChatMessage('agent', 'Delete request cancelled.');
            return;
        }
        sendAiMessage(deleteShortcut.actualQuery);
        return;
    }
    input.value = text;
    updateAiAgentComposerState();
    sendAiMessage();
}

function sendAiMessageWithDisplay(displayText, actualQuery) {
    recordQuickGuideActivity(actualQuery, displayText);
    appendChatMessage('user', displayText);
    sendAiMessage(actualQuery);
}

document.addEventListener('DOMContentLoaded', () => {
    applyAiAgentLanguageUi();
    updateAiAgentComposerState();
    refreshAiAgentMessagingAvailability();
    const body = document.getElementById('ai-agent-body');
    body?.addEventListener('scroll', updateAiAgentJumpButtonVisibility);
    window.addEventListener('resize', updateAiAgentJumpButtonVisibility);
    updateAiAgentJumpButtonVisibility();
    renderQuickGuideActivityList();
});

function escapeAgentHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

const agentLookupSearchTimers = {};

function closeAgentLookupDropdowns(exceptNode = null) {
    document.querySelectorAll('.agent-chat-lookup').forEach(wrapper => {
        if (exceptNode && wrapper === exceptNode) return;
        wrapper.classList.remove('is-open');
    });
}

async function fetchAgentLookupResults(lookupObject, query) {
    const response = await fetch(`/lookups/search?q=${encodeURIComponent(query || '')}&type=${encodeURIComponent(lookupObject)}`);
    const data = await response.json();
    return Array.isArray(data.results) ? data.results : [];
}

function renderAgentLookupResults(wrapper, items) {
    const dropdown = wrapper?.querySelector('.agent-chat-lookup-dropdown');
    if (!dropdown) return;
    const lookupObject = wrapper?.dataset?.lookupObject || 'Product';
    const visual = getAgentLookupVisual(lookupObject);
    if (!Array.isArray(items) || items.length === 0) {
        dropdown.innerHTML = '<div class="agent-chat-lookup-empty">No results found</div>';
        wrapper.classList.add('is-open');
        return;
    }
    dropdown.innerHTML = items.map(item => `
        <button
            type="button"
            class="agent-chat-lookup-option"
            data-lookup-id="${escapeAgentHtml(item.id)}"
            data-lookup-name="${escapeAgentHtml(item.name)}"
        >
            <span class="agent-chat-lookup-option-icon" style="background:${escapeAgentHtml(visual.color)}">${escapeAgentHtml(visual.text)}</span>
            <span class="agent-chat-lookup-option-copy">
                <span class="agent-chat-lookup-option-name">${escapeAgentHtml(item.name)}</span>
            </span>
        </button>
    `).join('');
    wrapper.classList.add('is-open');
}

function clearAgentLookupSelection(wrapper) {
    if (!wrapper) return;
    const hiddenInput = wrapper.querySelector('.agent-chat-lookup-id');
    const textInput = wrapper.querySelector('.agent-chat-lookup-input');
    if (hiddenInput) hiddenInput.value = '';
    if (textInput) textInput.value = '';
    wrapper.dataset.displayValue = '';
    wrapper.classList.remove('has-value');
    const badge = wrapper.querySelector('.agent-chat-lookup-badge');
    if (badge) badge.classList.remove('is-visible');
    closeAgentLookupDropdowns();
}

function updateAgentFormClearableState(field) {
    const wrapper = field?.closest?.('.agent-chat-form-clearable');
    if (!wrapper) return;
    const hasValue = Boolean(String(field.value || '').trim());
    wrapper.classList.toggle('is-has-value', hasValue);
}

function clearAgentFormField(button) {
    const wrapper = button?.closest?.('.agent-chat-form-clearable');
    const field = wrapper?.querySelector?.('input, textarea');
    if (!field) return;
    field.value = '';
    updateAgentFormClearableState(field);
    if (typeof field.dispatchEvent === 'function' && typeof Event === 'function') {
        field.dispatchEvent(new Event('input', { bubbles: true }));
    }
    field.focus?.();
}

function initAgentFormClearButtons(root) {
    if (!root) return;
    root.querySelectorAll('.agent-chat-form-clearable input, .agent-chat-form-clearable textarea').forEach(field => {
        if (field.dataset.clearEnhanced === 'true') {
            updateAgentFormClearableState(field);
            return;
        }
        field.dataset.clearEnhanced = 'true';
        field.addEventListener('input', () => updateAgentFormClearableState(field));
        updateAgentFormClearableState(field);
    });
}

function setAgentLookupSelection(wrapper, item) {
    if (!wrapper || !item) return;
    const hiddenInput = wrapper.querySelector('.agent-chat-lookup-id');
    const textInput = wrapper.querySelector('.agent-chat-lookup-input');
    if (hiddenInput) hiddenInput.value = item.id || '';
    if (textInput) textInput.value = item.name || '';
    wrapper.dataset.displayValue = item.name || '';
    wrapper.classList.toggle('has-value', !!(item.name || item.id));
    const badge = wrapper.querySelector('.agent-chat-lookup-badge');
    if (badge) {
        const visual = getAgentLookupVisual(wrapper.dataset.lookupObject || 'Product');
        badge.textContent = visual.text;
        badge.style.background = visual.color;
        badge.classList.add('is-visible');
    }
    closeAgentLookupDropdowns();
}

function initAgentChatLookupFields(root) {
    if (!root) return;
    root.querySelectorAll('.agent-chat-lookup').forEach(wrapper => {
        if (wrapper.dataset.lookupEnhanced === 'true') return;
        wrapper.dataset.lookupEnhanced = 'true';
        const lookupObject = wrapper.dataset.lookupObject || 'Product';
        const lookupField = wrapper.dataset.lookupField || '';
        const textInput = wrapper.querySelector('.agent-chat-lookup-input');
        const clearButton = wrapper.querySelector('.agent-chat-lookup-clear');
        const hiddenInput = wrapper.querySelector('.agent-chat-lookup-id');
        const currentDisplay = wrapper.dataset.displayValue || '';
        const badge = wrapper.querySelector('.agent-chat-lookup-badge');
        if (badge) {
            const visual = getAgentLookupVisual(lookupObject);
            badge.textContent = visual.text;
            badge.style.background = visual.color;
            badge.classList.toggle('is-visible', !!(currentDisplay || hiddenInput?.value));
        }

        wrapper.classList.toggle('has-value', !!(currentDisplay || hiddenInput?.value));

        const queueSearch = (query) => {
            clearTimeout(agentLookupSearchTimers[lookupField]);
            agentLookupSearchTimers[lookupField] = setTimeout(async () => {
                const items = await fetchAgentLookupResults(lookupObject, query);
                renderAgentLookupResults(wrapper, items);
            }, 200);
        };

        textInput?.addEventListener('focus', () => {
            closeAgentLookupDropdowns(wrapper);
            queueSearch(textInput.value.trim());
        });

        textInput?.addEventListener('input', () => {
            if (hiddenInput && textInput.value.trim() !== (wrapper.dataset.displayValue || '')) {
                hiddenInput.value = '';
            }
            wrapper.classList.toggle('has-value', !!textInput.value.trim());
            badge?.classList.toggle('is-visible', !!textInput.value.trim());
            queueSearch(textInput.value.trim());
        });

        clearButton?.addEventListener('click', () => clearAgentLookupSelection(wrapper));

        wrapper.addEventListener('click', event => {
            const option = event.target.closest('.agent-chat-lookup-option');
            if (!option) return;
            setAgentLookupSelection(wrapper, {
                id: option.dataset.lookupId || '',
                name: option.dataset.lookupName || '',
            });
        });
    });
}

if (!window.__agentLookupOutsideClickBound) {
    document.addEventListener('click', event => {
        const lookupWrapper = event.target.closest('.agent-chat-lookup');
        closeAgentLookupDropdowns(lookupWrapper);
    });
    window.__agentLookupOutsideClickBound = true;
}

function renderAgentInlineSchemaField(field) {
    if (!field) return '';
    const name = escapeAgentHtml(field.name || '');
    const label = escapeAgentHtml(field.label || field.name || '');
    const required = field.required ? '<span class="agent-chat-form-required">*</span>' : '';
    const error = field.error ? `<div class="agent-chat-form-field-error">${escapeAgentHtml(field.error)}</div>` : '';
    const value = field.value ?? '';
    const layoutClass = field.layout === 'full' ? 'agent-chat-form-field-full' : '';

    if (field.control === 'textarea') {
        return `
            <label class="agent-chat-form-field ${layoutClass || 'agent-chat-form-field-full'}">
                <span class="agent-chat-form-label">${label}${required}</span>
                <div class="agent-chat-form-clearable agent-chat-form-clearable-textarea ${String(value).trim() ? 'is-has-value' : ''}">
                    <textarea name="${name}" class="agent-chat-form-textarea" rows="4" placeholder="${escapeAgentHtml(field.placeholder || '')}">${escapeAgentHtml(value)}</textarea>
                    <button type="button" class="agent-chat-form-clear" onclick="clearAgentFormField(this)" aria-label="Clear field" title="Clear field">&times;</button>
                </div>
                ${error}
            </label>
        `;
    }

    if (field.control === 'select') {
        const options = Array.isArray(field.options) ? field.options : [];
        const optionsHtml = options.map(option => `
            <option value="${escapeAgentHtml(option.value)}" ${String(option.value) === String(value ?? '') ? 'selected' : ''}>${escapeAgentHtml(option.label)}</option>
        `).join('');
        return `
            <label class="agent-chat-form-field ${layoutClass}">
                <span class="agent-chat-form-label">${label}${required}</span>
                <select name="${name}" class="agent-chat-form-select">${optionsHtml}</select>
                ${error}
            </label>
        `;
    }

    if (field.control === 'lookup') {
        const displayValue = field.display_value ?? '';
        return `
            <label class="agent-chat-form-field ${layoutClass}">
                <span class="agent-chat-form-label">${label}${required}</span>
                <div
                    class="agent-chat-lookup ${displayValue || value ? 'has-value' : ''}"
                    data-lookup-field="${name}"
                    data-lookup-object="${escapeAgentHtml(field.lookup_object || 'Product')}"
                    data-display-value="${escapeAgentHtml(displayValue)}"
                >
                    <input type="hidden" name="${name}" class="agent-chat-lookup-id" value="${escapeAgentHtml(value)}">
                    <div class="agent-chat-lookup-input-row">
                        <span class="agent-chat-lookup-badge ${(displayValue || value) ? 'is-visible' : ''}" style="background:${escapeAgentHtml(getAgentLookupVisual(field.lookup_object || 'Product').color)}">${escapeAgentHtml(getAgentLookupVisual(field.lookup_object || 'Product').text)}</span>
                        <input
                            type="text"
                            class="agent-chat-form-input agent-chat-lookup-input"
                            value="${escapeAgentHtml(displayValue)}"
                            placeholder="${escapeAgentHtml(field.placeholder || `Search ${field.lookup_object || label}...`)}"
                            autocomplete="off"
                        >
                        <button type="button" class="agent-chat-form-clear agent-chat-lookup-clear" aria-label="Clear lookup" title="Clear lookup">&times;</button>
                    </div>
                    <div class="agent-chat-lookup-dropdown"></div>
                </div>
                ${error}
            </label>
        `;
    }

    const inputType = field.control === 'number' ? 'number' : field.control === 'email' ? 'email' : field.control === 'tel' ? 'tel' : 'text';
    return `
        <label class="agent-chat-form-field ${layoutClass}">
            <span class="agent-chat-form-label">${label}${required}</span>
            <div class="agent-chat-form-clearable ${String(value).trim() ? 'is-has-value' : ''}">
                <input
                    type="${inputType}"
                    name="${name}"
                    class="agent-chat-form-input"
                    value="${escapeAgentHtml(value)}"
                    placeholder="${escapeAgentHtml(field.placeholder || '')}"
                    ${field.control === 'number' && field.name === 'probability' ? 'min="0" max="100"' : ''}
                >
                <button type="button" class="agent-chat-form-clear" onclick="clearAgentFormField(this)" aria-label="Clear field" title="Clear field">&times;</button>
            </div>
            ${error}
        </label>
    `;
}

function renderAgentInlineSchemaForm(form) {
    if (!form) return '';
    const fields = Array.isArray(form.fields) ? form.fields : [];
    const fieldMarkup = fields.map(renderAgentInlineSchemaField).join('');
    const formError = form.form_error
        ? `<div class="agent-chat-form-error">${escapeAgentHtml(form.form_error)}</div>`
        : '';

    return `
        <div class="agent-chat-form-card" data-form-id="${escapeAgentHtml(form.form_id || '')}">
            <div class="agent-chat-form-meta">
                <span>${escapeAgentHtml((form.mode || 'form').toUpperCase())}</span>
                <span>${escapeAgentHtml(form.object_type || 'record')}</span>
            </div>
            <div class="agent-chat-form-header">
                <strong>${escapeAgentHtml(form.title || 'Form')}</strong>
                ${form.description ? `<span>${escapeAgentHtml(form.description)}</span>` : ''}
            </div>
            ${formError}
            <form
                class="agent-chat-form"
                data-form-id="${escapeAgentHtml(form.form_id || '')}"
                data-object-type="${escapeAgentHtml(form.object_type || '')}"
                data-mode="${escapeAgentHtml(form.mode || 'create')}"
                data-record-id="${escapeAgentHtml(form.record_id || '')}"
                onsubmit="return submitAgentChatForm(event);"
            >
                <div class="agent-chat-form-grid">${fieldMarkup}</div>
                <div class="agent-chat-form-actions">
                    <button type="button" class="agent-paste-action-btn agent-paste-action-secondary" onclick="cancelAgentChatForm(this)">${escapeAgentHtml(form.cancel_label || 'Cancel')}</button>
                    <button type="submit" class="agent-paste-action-btn">${escapeAgentHtml(form.submit_label || 'Save')}</button>
                </div>
            </form>
        </div>
    `;
}

async function submitAgentChatForm(event) {
    event.preventDefault();
    const form = event.target;
    if (!form) return false;

    const formId = form.dataset.formId || '';
    const objectType = form.dataset.objectType || '';
    const mode = form.dataset.mode || 'create';
    const recordId = form.dataset.recordId || null;
    const values = {};
    const submitButton = form.querySelector('button[type="submit"]');
    const card = form.closest('.agent-chat-form-card');

    form.querySelectorAll('input, textarea, select').forEach(field => {
        values[field.name] = field.value;
    });

    if (submitButton) submitButton.disabled = true;
    if (card) card.classList.add('is-submitting');
    recordAiAgentDebug('chat-form-submit', { formId, objectType, mode, recordId });

    try {
        const data = await submitAiAgentFormResponse({
            form_id: formId,
            object_type: objectType,
            mode,
            record_id: recordId,
            values,
        });

        if (data.intent === 'OPEN_RECORD') {
            recordAiAgentDebug('chat-form-open-record', {
                objectType: data.object_type,
                recordId: data.record_id,
                redirectUrl: data.redirect_url,
            });
            clearAiAgentTransientLoadingState();
            if (card) card.remove();
            const fallbackDetailUrl = data.object_type && data.record_id
                ? getAgentObjectRoute(data.object_type, data.record_id, 'detail')
                : null;
            const targetUrl = data.redirect_url || fallbackDetailUrl;
            const skipWorkspaceOpen = data.object_type === 'lead' || data.object_type === 'contact' || data.object_type === 'opportunity';
            let appendedMessage = null;
            if (data.text) {
                appendedMessage = appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query, data.chat_card);
            }
            if (targetUrl && !skipWorkspaceOpen) {
                const workspaceTitle = data.chat_card?.title || data.form_title || 'Record View';
                requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle));
            }
            return false;
        }

        if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {
            recordAiAgentDebug('chat-form-reopen', {
                objectType: data.object_type,
                mode: data.form?.mode,
                fieldCount: (data.form?.fields || []).length,
            });
            clearAiAgentTransientLoadingState();
            const wrapper = document.createElement('div');
            wrapper.innerHTML = renderAgentInlineSchemaForm(data.form);
            const replacementCard = wrapper.firstElementChild;
            if (replacementCard) {
                card.replaceWith(replacementCard);
                initAgentFormClearButtons(replacementCard);
                initAgentChatLookupFields(replacementCard);
                scrollAgentSchemaFormIntoView(replacementCard);
            } else {
                card.outerHTML = renderAgentInlineSchemaForm(data.form);
            }
            return false;
        }

        recordAiAgentDebug('chat-form-chat-response', {
            intent: data.intent,
            objectType: data.object_type,
            recordId: data.record_id,
        });
        clearAiAgentTransientLoadingState();
        appendChatMessage('agent', data.text || 'I could not save the form.');
    } catch (error) {
        console.error(error);
        recordAiAgentDebug('chat-form-submit-error', {
            message: error.message || String(error),
            objectType,
            mode,
            recordId,
        });
        clearAiAgentTransientLoadingState();
        appendChatMessage('agent', 'Failed to save the form.');
    } finally {
        if (submitButton) submitButton.disabled = false;
        if (card) card.classList.remove('is-submitting');
    }

    return false;
}

function cancelAgentChatForm(button) {
    const card = button?.closest('.agent-chat-form-card');
    if (card) {
        card.remove();
    }
    appendChatMessage('agent', 'Form closed.');
}

function renderAgentChatCard(card) {
    if (!card) return '';
    if (card.type === 'inline_form' && card.form) {
        return renderAgentInlineSchemaForm(card.form);
    }
    if (card.type !== 'lead_paste' && card.type !== 'record_paste') return '';
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
        const buttons = card.actions.filter(act => act.action !== 'open').map(act => {
            const label = escapeAgentHtml(act.label || '');
            const tone = act.tone || 'default';
            const btnClass = act.action === 'edit'
                ? 'agent-paste-action-btn agent-paste-action-edit'
                : tone === 'danger'
                ? 'agent-paste-action-btn agent-paste-action-danger'
                : tone === 'secondary'
                    ? 'agent-paste-action-btn agent-paste-action-secondary'
                    : 'agent-paste-action-btn';

            if (act.action === 'edit') {
                if (shouldUseDirectAgentEditForm(objectType)) {
                    return `<button class="${btnClass}" onclick="openAgentEditFormDirect('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')">${label}</button>`;
                }
                const editQuery = `Manage ${escapeAgentQuery(objectType)} ${escapeAgentQuery(recordId)} edit`;
                return `<button class="${btnClass}" onclick="sendAiMessageWithDisplay('Edit ${escapeAgentHtml(displayName)}', '${editQuery}')">${label}</button>`;
            }
            if (act.action === 'delete') {
                return `<button class="${btnClass}" onclick="triggerSnapshotDelete('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')">${label}</button>`;
            }
            if (act.action === 'send_message') {
                const blocked = aiAgentMessagingAvailabilityState.checked && !aiAgentMessagingAvailabilityState.available;
                if (blocked) {
                    return `<button class="${btnClass}" disabled title="${escapeAgentHtml(aiAgentMessagingAvailabilityState.message || 'Message service is unavailable. Contact the administrator.')}">Contact Administrator</button>`;
                }
                return `<button class="${btnClass}" onclick="triggerLeadCardSendMessage('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')">${label}</button>`;
            }
            if (act.action === 'preview_image' && act.url) {
                return `<button class="${btnClass}" onclick="openAgentImagePreview('${escapeAgentQuery(act.url)}', 'Template Preview')">${label}</button>`;
            }
            if (act.action === 'use_in_send') {
                return `<button class="${btnClass}" onclick="startTemplateSendFromAgent('${escapeAgentQuery(recordId)}')">${label}</button>`;
            }
            return `<button type="button" class="${btnClass}" onclick="event.preventDefault(); event.stopPropagation(); sendQuickMessage('${escapeAgentQuery(act.action)} ${escapeAgentQuery(objectType)} ${escapeAgentQuery(recordId)}'); return false;">${label}</button>`;
        }).join('');
        actionButtonsHtml = `<div class="agent-paste-actions">${buttons}</div>`;
    } else if (recordId) {
        // Fallback: legacy hardcoded Edit/Delete if no actions array
        const editQuery = `Manage ${objectType} ${recordId} edit`;
        const editClick = shouldUseDirectAgentEditForm(objectType)
            ? `openAgentEditFormDirect('${escapeAgentQuery(objectType)}', '${escapeAgentQuery(recordId)}', '${escapeAgentHtml(displayName)}')`
            : `sendAiMessageWithDisplay('Edit ${escapeAgentHtml(displayName)}', '${escapeAgentQuery(editQuery)}')`;
        actionButtonsHtml = `
            <div class="agent-paste-actions">
                <button class="agent-paste-action-btn" onclick="${editClick}">Edit</button>
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
    if (!ensureAiAgentMessagingAvailable()) return;
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

function shouldUseAgentChatForm(objectType) {
    return objectType === 'lead'
        || objectType === 'contact'
        || objectType === 'opportunity'
        || objectType === 'product'
        || objectType === 'asset'
        || objectType === 'brand'
        || objectType === 'model'
        || objectType === 'message_template';
}

function renderResultsTable(results, objectType, pagination = null, originalQuery = null) {
    if (!results || results.length === 0) return "";
    if ((pagination && pagination.mode === 'local') || (!pagination && results.length > 30)) {
        const localKey = `agent-local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
        localAgentResultTables[localKey] = {
            results,
            objectType,
            originalQuery,
            searchTerm: pagination?.search_term || '',
        };
        return renderLocalResultsTable(localKey, pagination?.page || 1);
    }

    return renderAgentResultsMarkup(results, objectType, pagination, originalQuery);
}

function renderLocalResultsTable(tableKey, page) {
    const tableState = localAgentResultTables[tableKey];
    if (!tableState) return '';

    const perPage = 30;
    const safePage = Math.max(page, 1);
    const activeResults = Array.isArray(tableState.filteredResults) ? tableState.filteredResults : tableState.results;
    const start = (safePage - 1) * perPage;
    const pagedResults = activeResults.slice(start, start + perPage);
    const pagination = {
        page: safePage,
        per_page: perPage,
        total: activeResults.length,
        total_pages: Math.max(1, Math.ceil(activeResults.length / perPage)),
        object_type: tableState.objectType,
        mode: 'local',
        table_key: tableKey,
        search_term: tableState.searchTerm || '',
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
                    <div class="agent-table-search-wrap">
                        <input type="text" class="agent-table-search" value="${escapeAgentHtml(pagination?.search_term || '')}" placeholder="Search..." oninput="filterAgentTable(this)" onkeydown="handleAgentTableSearch(event, this, '${objectType}')" aria-label="Search in table">
                        <button type="button" class="agent-table-search-clear ${pagination?.search_term ? 'is-visible' : ''}" onclick="clearAgentTableSearch(this)" aria-label="Clear table search" title="Clear table search">&times;</button>
                    </div>
                </div>
                <div class="table-controls-btn-row">
                    <button class="control-btn btn-icon" onclick="selectAllAgentRows(this, '${objectType}')" title="Select All"><span style="font-size:1rem; line-height:1;">✓</span></button>
                    <button class="control-btn btn-icon" onclick="clearAllAgentRows(this, '${objectType}')" title="Clear All"><span style="font-size:1rem; line-height:1;">✕</span></button>
                    <button class="control-btn control-btn-action" onclick="triggerCreateFromTable(this, '${objectType}')">New</button>
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

    if (pagination && pagination.total_pages > 1) {
        html += `
            <div class="agent-pagination">
                <button class="control-btn" ${pagination.page <= 1 ? 'disabled' : ''} onclick="${pagination.mode === 'local' ? `requestLocalAgentPage('${pagination.table_key}', ${pagination.page - 1})` : `requestAgentPage('${escapeAgentQuery(originalQuery || '')}', ${pagination.page - 1})`}">Previous</button>
                <span class="agent-pagination-label">Page ${pagination.page} of ${pagination.total_pages} · ${pagination.total} records${pagination.mode === 'local' ? ' · Local' : ''}</span>
                <button class="control-btn" ${pagination.page >= pagination.total_pages ? 'disabled' : ''} onclick="${pagination.mode === 'local' ? `requestLocalAgentPage('${pagination.table_key}', ${pagination.page + 1})` : `requestAgentPage('${escapeAgentQuery(originalQuery || '')}', ${pagination.page + 1})`}">Next</button>
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
    const clearBtn = input.parentElement?.querySelector?.('.agent-table-search-clear');
    clearBtn?.classList.toggle('is-visible', Boolean(term));
    const tableKey = container.dataset.tableKey;
    if (tableKey && localAgentResultTables[tableKey]) {
        const tableState = localAgentResultTables[tableKey];
        tableState.searchTerm = term;
        tableState.filteredResults = term
            ? tableState.results.filter(row => agentTableRowMatches(row, tableState.objectType, term))
            : tableState.results.slice();
        requestLocalAgentPage(tableKey, 1, {
            focusSearch: true,
            value: input.value,
            selectionStart: typeof input.selectionStart === 'number' ? input.selectionStart : input.value.length,
            selectionEnd: typeof input.selectionEnd === 'number' ? input.selectionEnd : input.value.length,
        });
        return;
    }
    const rows = container.querySelectorAll('table tbody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = term === '' || text.includes(term) ? '' : 'none';
    });
}

function handleAgentTableSearch(event, input, objectType) {
    if (event.key === 'Enter') {
        event.preventDefault();
        filterAgentTable(input);
    }
}

function clearAgentTableSearch(button) {
    const wrapper = button?.closest?.('.agent-table-search-wrap');
    const input = wrapper?.querySelector?.('.agent-table-search');
    if (!input) return;
    input.value = '';
    filterAgentTable(input);
    input.focus?.();
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

function triggerCreateFromTable(btn, objectType) {
    const normalized = String(objectType || '').trim();
    if (!normalized) return;
    sendAiMessageWithDisplay(`Create ${normalized}`, `create ${normalized}`);
}

function _setActiveSelectionFromContainer(container, objectType) {
    aiAgentActiveSelectionObject = objectType;
    aiAgentActiveSelectionContainer = container;
}

function requestLocalAgentPage(tableKey, page, searchState = null) {
    const container = document.querySelector(`.results-container[data-table-key="${tableKey}"]`);
    const markup = renderLocalResultsTable(tableKey, page);
    if (container && markup) {
        container.outerHTML = markup;
        if (searchState?.focusSearch) {
            const nextContainer = document.querySelector(`.results-container[data-table-key="${tableKey}"]`);
            const nextInput = nextContainer?.querySelector?.('.agent-table-search');
            if (nextInput) {
                nextInput.focus();
                nextInput.value = searchState.value || '';
                if (typeof nextInput.setSelectionRange === 'function') {
                    nextInput.setSelectionRange(searchState.selectionStart || 0, searchState.selectionEnd || 0);
                }
            }
        }
    }
    updateAiAgentJumpButtonVisibility();
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
        brand: { detail: `/vehicle_specifications/${recordId}`, edit: `/vehicle_specifications/new-modal?type=Brand&id=${recordId}` },
        message_template: { detail: `/message_templates/${recordId}`, edit: `/message_templates/new-modal?id=${recordId}` },
    };
    return routes[objectType]?.[action] || null;
}

function shouldUseDirectAgentEditForm(objectType) {
    return objectType === 'asset'
        || objectType === 'brand'
        || objectType === 'model'
        || objectType === 'message_template';
}

function buildAgentEditIntro(objectType, displayName = '') {
    const objectLabel = String(objectType || '').replace(/_/g, ' ').trim() || 'record';
    const target = String(displayName || '').trim();
    const suffix = target ? ` for **${target}**` : '';
    return `I opened the ${objectLabel} edit form${suffix} here in chat. Update the fields you want, then save your changes.`;
}

function openAgentEditFormDirect(objectType, recordId, displayName = '') {
    if (!objectType || !recordId) return false;
    const url = getAgentObjectRoute(objectType, recordId, 'edit');
    if (!url) return false;
    appendAgentInlineFormMessage(buildAgentEditIntro(objectType, displayName), url, `Edit ${displayName || objectType}`);
    return true;
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
    if (!ensureAiAgentMessagingAvailable()) return;
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
    const shouldRouteThroughChatOpen = shouldUseAgentChatPaste(selection.object_type)
        || selection.object_type === 'contact'
        || selection.object_type === 'opportunity'
        || selection.object_type === 'product'
        || selection.object_type === 'asset'
        || selection.object_type === 'brand'
        || selection.object_type === 'model'
        || selection.object_type === 'message_template';
    if (shouldRouteThroughChatOpen) {
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
    if (shouldUseDirectAgentEditForm(selection.object_type)) {
        openAgentEditFormDirect(selection.object_type, selection.ids[0], label);
        return;
    }
    if (shouldUseAgentChatForm(selection.object_type)) {
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

function triggerWorkspaceEdit() {
    const panel = document.getElementById('ai-agent-workspace');
    const objectType = panel?.dataset?.recordObjectType || '';
    const recordId = panel?.dataset?.recordId || '';
    const title = panel?.dataset?.recordTitle || recordId;
    if (!objectType || !recordId) {
        appendChatMessage('agent', 'Open a single record first, then choose Edit.');
        return;
    }
    if (shouldUseDirectAgentEditForm(objectType)) {
        openAgentEditFormDirect(objectType, recordId, title);
        return;
    }
    sendAiMessageWithDisplay(`Edit ${title}`, `Manage ${objectType} ${recordId} edit`);
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
