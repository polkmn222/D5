let isAiAgentMinimized = false;
let isAiAgentMaximized = false;
let agentTableStyle = 'default';
let aiAgentConversationId = createConversationId();

function createConversationId() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
    }
    return `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toggleAiAgent() {
    const win = document.getElementById('ai-agent-window');
    if (win.style.display === 'none' || win.style.display === '') {
        win.style.display = 'flex';
        if (!isAiAgentMinimized) {
            win.style.height = isAiAgentMaximized ? '100%' : '700px';
        }
    } else {
        win.style.display = 'none';
    }
}

function resetAiAgent() {
    const win = document.getElementById('ai-agent-window');
    const body = document.getElementById('ai-agent-body');
    
    body.innerHTML = `
        <div style="text-align: center; color: #706e6b; font-size: 0.75rem; margin-bottom: 20px; font-weight: 500;">SESSION RESTARTED</div>
        <div class="msg-agent">
            <div class="msg-agent-header">
                <div class="msg-agent-icon">🤖</div>
                <span style="font-size: 0.8rem; font-weight: 700; color: #3e3e3c;">AI AGENT</span>
            </div>
            <div class="msg-agent-content">
                <div class="msg-agent-text">Hello! I'm your AI Agent. I've been reset and I'm ready to help you again.</div>
            </div>
        </div>
    `;

    aiAgentConversationId = createConversationId();
    
    isAiAgentMinimized = false;
    isAiAgentMaximized = false;
    win.style.display = 'none';
    win.style.width = '950px';
    win.style.height = '700px';
    win.style.bottom = '24px';
    win.style.right = '24px';
    win.style.borderRadius = '12px';
    
    const container = document.querySelector('.ai-agent-main-container');
    const footer = document.getElementById('ai-agent-footer');
    container.style.display = 'flex';
    footer.style.display = 'flex';
}

function minimizeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    const container = document.querySelector('.ai-agent-main-container');
    const footer = document.getElementById('ai-agent-footer');
    
    if (isAiAgentMinimized) {
        container.style.display = 'flex';
        footer.style.display = 'flex';
        win.style.height = isAiAgentMaximized ? '100%' : '700px';
        isAiAgentMinimized = false;
    } else {
        container.style.display = 'none';
        footer.style.display = 'none';
        win.style.height = 'auto';
        isAiAgentMinimized = true;
    }
}

function maximizeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    if (isAiAgentMaximized) {
        win.style.width = '950px';
        win.style.height = isAiAgentMinimized ? 'auto' : '700px';
        win.style.bottom = '24px';
        win.style.right = '24px';
        win.style.borderRadius = '12px';
        isAiAgentMaximized = false;
    } else {
        win.style.width = '100%';
        win.style.height = isAiAgentMinimized ? 'auto' : '100%';
        win.style.bottom = '0';
        win.style.right = '0';
        win.style.borderRadius = '0';
        isAiAgentMaximized = true;
    }
}

async function sendAiMessage() {
    const input = document.getElementById('ai-agent-input');
    const query = input.value.trim();
    if (!query) return;

    appendChatMessage('user', query);
    input.value = '';

    const loadingId = 'loading-' + Date.now();
    appendChatMessage('agent', '<span class="loading-dots">Thinking</span>', loadingId);

    try {
        const response = await fetch('/ai-agent/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, conversation_id: aiAgentConversationId })
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
            window.location.href = '/send';
            return;
        }

        if (data.text) {
            appendChatMessage('agent', data.text, null, data.sql, data.results, data.object_type);
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

function appendChatMessage(role, text, id = null, sql = null, results = null, objectType = null) {
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
            innerHTML += renderResultsTable(results, objectType);
        }

        innerHTML += `</div>`;
        msgDiv.innerHTML = innerHTML;
    }

    body.appendChild(msgDiv);
    
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

function renderResultsTable(results, objectType) {
    if (!results || results.length === 0) return "";
    
    let html = `
        <div class="results-container">
            <div class="table-controls">
                <button class="control-btn" onclick="selectAllAgentRows(this)">✅ Select All</button>
                <button class="control-btn" onclick="clearAllAgentRows(this)">❌ Clear All</button>
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

    results.forEach((row, index) => {
        const rowId = row.id || row.ID || "";
        html += `<tr onclick="selectAgentRecord('${rowId}', '${objectType}')" style="cursor: pointer;">
                    <td><input type="checkbox" onclick="event.stopPropagation()"></td>
                    <td style="color: #666; font-size: 0.75rem;">${index + 1}</td>`;
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
    
    html += '</tbody></table></div></div>';
    return html;
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

function selectAllAgentRows(btn) {
    const table = btn.closest('.results-container').querySelector('table');
    table.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
}

function clearAllAgentRows(btn) {
    const table = btn.closest('.results-container').querySelector('table');
    table.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
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
