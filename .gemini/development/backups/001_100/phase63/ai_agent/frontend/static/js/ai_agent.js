let isAiAgentMinimized = false;
let isAiAgentMaximized = false;
let agentTableStyle = 'default';
let aiAgentConversationId = createConversationId();
let aiAgentSelectionState = {};
let aiAgentActiveSelectionObject = null;
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
`;

function normalizeObjectLabel(objectType, count) {
    if (!objectType) return 'records';
    const label = objectType.replace('_', ' ');
    return count === 1 ? label : `${label}s`;
}

function summarizeSelectionIds(ids) {
    if (!ids || !ids.length) return 'Select records to prepare bulk actions.';
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
        detail.textContent = 'Select records to prepare bulk actions.';
        return;
    }

    const count = selection.ids.length;
    const label = normalizeObjectLabel(selection.object_type, count);
    summary.textContent = `${count} ${label} selected`;
    detail.textContent = summarizeSelectionIds(selection.ids);
    bar.classList.remove('is-hidden');
}

function createConversationId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
    }
    return `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toggleAiAgent() {
    const win = document.getElementById('ai-agent-window');
    if (win.classList.contains('agent-hidden')) {
        win.classList.remove('agent-hidden');
        if (!isAiAgentMinimized) {
            win.style.height = isAiAgentMaximized ? '100%' : '700px';
        }
    } else {
        win.classList.add('agent-hidden');
    }
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
    updateSelectionBar();
}

function minimizeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    const container = document.querySelector('.ai-agent-main-container');
    const footer = document.getElementById('ai-agent-footer');
    const resetBtn = document.getElementById('ai-agent-reset-btn');
    
    if (isAiAgentMinimized) {
        container.style.display = 'flex';
        footer.style.display = 'flex';
        win.style.height = isAiAgentMaximized ? '100%' : '700px';
        win.classList.remove('agent-minimized');
        if (resetBtn) resetBtn.style.display = 'inline-flex';
        isAiAgentMinimized = false;
    } else {
        container.style.display = 'none';
        footer.style.display = 'none';
        win.style.height = 'auto';
        win.classList.add('agent-minimized');
        if (resetBtn) resetBtn.style.display = 'none';
        isAiAgentMinimized = true;
    }
}

function maximizeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    if (isAiAgentMaximized) {
        win.style.width = isAiAgentMinimized ? '310px' : '950px';
        win.style.height = isAiAgentMinimized ? 'auto' : '700px';
        win.style.bottom = '24px';
        win.style.right = '24px';
        win.style.borderRadius = '12px';
        isAiAgentMaximized = false;
    } else {
        win.style.width = isAiAgentMinimized ? '310px' : '100%';
        win.style.height = isAiAgentMinimized ? 'auto' : '100%';
        win.style.bottom = '0';
        win.style.right = '0';
        win.style.borderRadius = '0';
        isAiAgentMaximized = true;
    }
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
        const response = await fetch('/ai-agent/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                conversation_id: aiAgentConversationId,
                page: pageOverride,
                per_page: 50,
                selection: buildSelectionPayload(),
            })
        });
        const data = await response.json();
        
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
            window.location.href = data.redirect_url || '/send';
            return;
        }

        if (data.text) {
            appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type, data.pagination, data.original_query);
        } else {
            appendChatMessage('agent', "I'm sorry, I couldn't process that request.");
        }
    } catch (error) {
        console.error("AI Agent Error:", error);
        const loadingIndicator = document.getElementById(loadingId);
        if (loadingIndicator) loadingIndicator.remove();
        appendChatMessage('agent', "Sorry, I encountered an error connecting to the AI service.");
    }
}

function appendChatMessage(role, text, id = null, sql = null, results = null, objectType = null, pagination = null, originalQuery = null) {
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
            return `<button class="btn" style="padding: 4px 12px; margin: 4px; font-size: 0.75rem; border-radius: 12px; background: white; border: 1px solid #0176d3; color: #0176d3; cursor: pointer;" onclick="sendQuickMessage('${p1}')">${p1}</button>`;
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

        innerHTML += `</div>`;
        msgDiv.innerHTML = innerHTML;
    }

    body.appendChild(msgDiv);
    updateSelectionBar();
    
    setTimeout(() => {
        msgDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
}

function sendQuickMessage(text) {
    const input = document.getElementById('ai-agent-input');
    if (!input) return;
    input.value = text;
    sendAiMessage();
}

function renderResultsTable(results, objectType, pagination = null, originalQuery = null) {
    if (!results || results.length === 0) return "";
    const selectedIds = getSelectedIds(objectType);
    
    let html = `
        <div class="results-container" data-object-type="${objectType || ''}">
            <div class="table-controls">
                <button class="control-btn" onclick="selectAllAgentRows(this, '${objectType}')">✅ Select All</button>
                <button class="control-btn" onclick="clearAllAgentRows(this, '${objectType}')">❌ Clear All</button>
                <span class="agent-selection-label">Selected: <strong>${selectedIds.length}</strong></span>
                <span style="font-size: 0.75rem; color: #706e6b; margin-left: auto; display: flex; align-items: center;">Click headers to sort</span>
            </div>
            <div style="overflow-x: auto;">
                <table class="agent-table agent-table-${agentTableStyle}">
                    <thead>
                        <tr>
                            <th style="width: 40px;">Sel.</th>
                            <th style="width: 40px;">No.</th>
    `;
    
    const keys = Object.keys(results[0]).filter(k => !['id', 'created_at', 'updated_at', 'deleted_at', 'record_id'].includes(k));
    keys.forEach((k, idx) => {
        html += `<th onclick="sortAgentTable(this, ${idx + 2})" style="cursor: pointer; position: relative; padding-right: 20px;">
                    ${k.replace('_', ' ')}
                    <span class="sort-icon" style="position: absolute; right: 4px; opacity: 0.3;">⇅</span>
                 </th>`;
    });
    html += '</tr></thead><tbody>';

    const rowStart = pagination ? ((pagination.page - 1) * pagination.per_page) + 1 : 1;

    results.forEach((row, index) => {
        const rowId = row.id || row.ID || "";
        const isChecked = selectedIds.includes(rowId);
        html += `<tr data-record-id="${rowId}" onclick="selectAgentRecord('${rowId}', '${objectType}')" style="cursor: pointer;">
                    <td><input type="checkbox" ${isChecked ? 'checked' : ''} onclick="toggleAgentRowSelection(event, '${objectType}', '${rowId}')"></td>
                    <td style="color: #666; font-size: 0.75rem;">${rowStart + index}</td>`;
        keys.forEach(k => {
            let val = row[k] || "-";
            if (k === 'name' || k === 'first_name') {
                html += `<td><strong style="color: #0176d3;">${val}</strong></td>`;
            } else {
                html += `<td>${val}</td>`;
            }
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';

    if (pagination && pagination.total_pages > 1 && originalQuery) {
        html += `
            <div class="agent-pagination">
                <button class="control-btn" ${pagination.page <= 1 ? 'disabled' : ''} onclick="requestAgentPage('${escapeAgentQuery(originalQuery)}', ${pagination.page - 1})">Previous</button>
                <span class="agent-pagination-label">Page ${pagination.page} of ${pagination.total_pages} · ${pagination.total} records</span>
                <button class="control-btn" ${pagination.page >= pagination.total_pages ? 'disabled' : ''} onclick="requestAgentPage('${escapeAgentQuery(originalQuery)}', ${pagination.page + 1})">Next</button>
            </div>
        `;
    }

    html += '</div>';
    return html;
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
    return {
        object_type: aiAgentActiveSelectionObject,
        ids: ids,
    };
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
    const label = container.querySelector('.agent-selection-label strong');
    if (label) {
        label.textContent = getSelectedIds(objectType).length;
    }
}

function toggleAgentRowSelection(event, objectType, recordId) {
    event.stopPropagation();
    if (!objectType || !recordId) return;
    aiAgentActiveSelectionObject = objectType;
    const bucket = ensureSelectionBucket(objectType);
    if (event.target.checked) {
        bucket.add(recordId);
    } else {
        bucket.delete(recordId);
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
    aiAgentActiveSelectionObject = objectType;
    table.querySelectorAll('tbody tr').forEach(row => {
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (!checkbox) return;
        const recordId = row.getAttribute('data-record-id');
        checkbox.checked = true;
        if (recordId) bucket.add(recordId);
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
    updateSelectionLabel(btn.closest('.results-container'), objectType);
    updateSelectionBar();
}

function clearActiveSelection() {
    Object.keys(aiAgentSelectionState).forEach(objectType => {
        aiAgentSelectionState[objectType].clear();
    });
    aiAgentActiveSelectionObject = null;
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
        appendChatMessage('agent', 'Select one or more records first, then try sending a message again.');
        return;
    }
    sendAiMessage('Send Message');
}

function selectAgentRecord(recordId, objectType) {
    if (!recordId) return;
    const input = document.getElementById('ai-agent-input');
    input.value = `Manage ${objectType} ${recordId}`;
    sendAiMessage();
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
            if (typeof showToast === 'function') showToast("AI Recommendations updated successfully!");
        } else {
            if (typeof showToast === 'function') showToast("Server error loading recommendations.", true);
        }
    } catch (error) { 
        console.error(error); 
        if (typeof showToast === 'function') showToast("Network error loading recommendations.", true);
    }
    finally { btn.innerText = originalText; btn.disabled = false; }
}
