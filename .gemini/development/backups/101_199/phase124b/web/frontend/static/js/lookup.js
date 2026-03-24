/**
 * Salesforce-style Dynamic Lookup Component
 */

function initLookup(containerId, objectType, fieldName, initialValueId = null, initialValueName = null) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Create HTML structure
    container.innerHTML = `
        <div class="sf-lookup-container">
            <input type="hidden" name="${fieldName}" id="lookup-id-${fieldName}" value="${initialValueId || ''}">
            <div class="sf-lookup-input-wrapper">
                <input type="text" class="sf-lookup-input" id="lookup-input-${fieldName}" 
                       placeholder="Search ${objectType}..." autocomplete="off" 
                       value="${initialValueName || ''}">
                <span class="sf-lookup-icon">🔍</span>
            </div>
            <div class="sf-lookup-dropdown" id="lookup-dropdown-${fieldName}">
                <div class="lookup-results" id="lookup-results-${fieldName}"></div>
                <div class="lookup-new-btn" onclick="openModal('/${objectType.toLowerCase()}s/new')">
                    <span>+ New ${objectType}</span>
                </div>
            </div>
        </div>
    `;

    const input = document.getElementById(`lookup-input-${fieldName}`);
    const dropdown = document.getElementById(`lookup-dropdown-${fieldName}`);
    const resultsCont = document.getElementById(`lookup-results-${fieldName}`);
    const idInput = document.getElementById(`lookup-id-${fieldName}`);

    // Fetch and show results
    const search = async (query) => {
        const response = await fetch(`/lookups/search?q=${encodeURIComponent(query)}&type=${objectType}`);
        const data = await response.json();
        
        resultsCont.innerHTML = '';
        if (data.results.length === 0) {
            resultsCont.innerHTML = '<div class="lookup-section-header" style="padding: 12px 16px; color: #706e6b; font-size: 0.75rem; border-bottom: 1px solid #f3f2f2;">No results found</div>';
        } else {
            resultsCont.innerHTML = '<div class="lookup-section-header" style="padding: 12px 16px; color: #706e6b; font-size: 0.75rem; border-bottom: 1px solid #f3f2f2;">Results</div>';
            data.results.forEach(item => {
                const div = document.createElement('div');
                div.className = 'lookup-item';
                div.style = 'display: flex; align-items: center; padding: 8px 16px; cursor: pointer; transition: background 0.1s;';
                div.innerHTML = `
                    <div class="lookup-item-icon" style="background: ${getIconColor(objectType)}; width: 24px; height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem; margin-right: 12px;">
                        ${getIconText(objectType)}
                    </div>
                    <div class="lookup-item-info">
                        <span class="lookup-item-name" style="color: #0176d3; font-size: 0.875rem;">${item.name}</span>
                        ${item.price ? `<span class="lookup-item-meta" style="color: #444; font-size: 0.75rem; margin-left: 8px;">${item.price.toLocaleString()} KRW</span>` : ''}
                    </div>
                `;
                div.onmouseover = () => div.style.backgroundColor = '#f3f2f2';
                div.onmouseout = () => div.style.backgroundColor = 'transparent';
                div.onclick = () => selectItem(item);
                resultsCont.appendChild(div);
            });
        }
        dropdown.style.display = 'block';
    };

    const selectItem = (item) => {
        const oldId = idInput.value;
        input.value = item.name;
        idInput.value = item.id;
        dropdown.style.display = 'none';
        
        const event = new CustomEvent('lookupSelected', { detail: { item, fieldName, oldId } });
        container.dispatchEvent(event);

        saveRecent(objectType, item);
    };

    const showRecent = () => {
        const recent = getRecent(objectType);
        resultsCont.innerHTML = '';
        if (recent.length > 0) {
            resultsCont.innerHTML = '<div class="lookup-section-header" style="padding: 12px 16px; color: #706e6b; font-size: 0.75rem;">Recent Items</div>';
            recent.forEach(item => {
                const div = document.createElement('div');
                div.className = 'lookup-item';
                div.style = 'display: flex; align-items: center; padding: 8px 16px; cursor: pointer; transition: background 0.1s;';
                div.innerHTML = `
                    <div class="lookup-item-icon" style="background: ${getIconColor(objectType)}; width: 24px; height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem; margin-right: 12px;">
                        ${getIconText(objectType)}
                    </div>
                    <div class="lookup-item-info">
                        <span class="lookup-item-name" style="color: #0176d3; font-size: 0.875rem;">${item.name}</span>
                    </div>
                `;
                div.onmouseover = () => div.style.backgroundColor = '#f3f2f2';
                div.onmouseout = () => div.style.backgroundColor = 'transparent';
                div.onclick = () => selectItem(item);
                resultsCont.appendChild(div);
            });
        } else {
            resultsCont.innerHTML = '<div class="lookup-section-header" style="padding: 12px 16px; color: #706e6b; font-size: 0.75rem;">Start typing to search...</div>';
        }
        dropdown.style.display = 'block';
    };

    // Event Listeners
    input.onfocus = () => {
        if (!input.value) showRecent();
        else search(input.value);
    };

    let debounceTimer;
    input.oninput = () => {
        clearTimeout(debounceTimer);
        idInput.value = ''; // Reset ID while typing
        if (!input.value) {
            showRecent();
            return;
        }
        debounceTimer = setTimeout(() => search(input.value), 300);
    };

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Helpers
    function getIconColor(type) {
        const colors = {
            'Lead': '#49a5e1',
            'Contact': '#a094ed',
            'Opportunity': '#fcb95b',
            'Asset': '#3ba755',
            'Product': '#b781d3',
            'Brand': '#54698d',
            'Model': '#e094ed',
            'MessageSend': '#00a1e0'
        };
        return colors[type] || '#54698d';
    }

    function getIconText(type) {
        const texts = {
            'Lead': 'LQ', 'Contact': 'C', 'Opportunity': 'O',
            'Asset': 'AS', 'Product': 'P', 'Brand': 'B', 'Model': 'M',
            'MessageSend': 'MS'
        };
        return texts[type] || 'R';
    }

    function saveRecent(type, item) {
        let recent = JSON.parse(localStorage.getItem(`recent_${type}`) || '[]');
        recent = [item, ...recent.filter(i => i.id !== item.id)].slice(0, 5);
        localStorage.setItem(`recent_${type}`, JSON.stringify(recent));
    }

    function getRecent(type) {
        return JSON.parse(localStorage.getItem(`recent_${type}`) || '[]');
    }
}
