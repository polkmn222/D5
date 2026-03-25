function readRecentListViewRecords(storageKey) {
    try {
        const raw = localStorage.getItem(storageKey);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
        return [];
    }
}

function writeRecentListViewRecords(storageKey, records) {
    localStorage.setItem(storageKey, JSON.stringify(records.slice(0, 20)));
}

function rememberRecentlyViewedRecord(storageKey, record) {
    if (!storageKey || !record || !record.id) {
        return;
    }

    const records = readRecentListViewRecords(storageKey).filter((item) => item.id !== record.id);
    records.unshift({
        id: record.id,
        name: record.name || "",
        url: record.url || "",
        viewed_at: new Date().toISOString(),
    });
    writeRecentListViewRecords(storageKey, records);
}

function initializeLeadListView(config) {
    const tbody = document.getElementById(config.tableBodyId);
    const table = document.querySelector(config.tableSelector);
    const summary = document.getElementById(config.summaryId);
    const emptyState = document.getElementById(config.emptyStateId);
    const selector = document.getElementById(config.selectorId);
    const searchInput = document.getElementById(config.searchInputId);
    const chip = document.getElementById(config.currentViewChipId);
    const viewSummary = document.getElementById(config.currentViewSummaryId);
    const rows = tbody ? Array.from(tbody.querySelectorAll("tr")) : [];

    if (!tbody || !table || !summary || !selector) {
        return;
    }

    function getCurrentView() {
        return selector.value === "recent" ? "recent" : "all";
    }

    function getVisibleRows() {
        return Array.from(tbody.querySelectorAll("tr")).filter((row) => row.style.display !== "none");
    }

    function updateSummary() {
        const visibleCount = getVisibleRows().length;
        const currentView = getCurrentView();
        if (viewSummary) {
            viewSummary.textContent = currentView === "recent" ? "Showing your recently opened leads" : "Filtered by All Leads";
        }
        if (chip) {
            chip.textContent = currentView === "recent" ? config.recentLabel : config.allLabel;
        }
        summary.innerHTML = `${visibleCount} items • Sorted by <span id="${config.currentSortId}">${document.getElementById(config.currentSortId)?.textContent || "Name"}</span> • <span id="${config.currentViewSummaryId}">${currentView === "recent" ? "Showing your recently opened leads" : "Filtered by All Leads"}</span> • Updated just now`;
    }

    function updateEmptyState() {
        const visibleCount = getVisibleRows().length;
        const currentView = getCurrentView();
        const shouldShowEmpty = currentView === "recent" && visibleCount === 0;
        emptyState.style.display = shouldShowEmpty ? "flex" : "none";
        table.style.display = shouldShowEmpty ? "none" : "table";
    }

    function applySearchFilter() {
        const query = (searchInput?.value || "").trim().toLowerCase();
        Array.from(tbody.querySelectorAll("tr")).forEach((row) => {
            const text = row.innerText.toLowerCase();
            row.style.display = query && !text.includes(query) ? "none" : "";
        });
        updateSummary();
        updateEmptyState();
    }

    function applyRecentView() {
        const recentRecords = readRecentListViewRecords(config.storageKey);
        const rowMap = new Map(rows.map((row) => [row.dataset.recordId, row]));
        const orderedRows = recentRecords.map((record) => rowMap.get(record.id)).filter(Boolean);

        tbody.innerHTML = "";
        if (getCurrentView() === "recent") {
            orderedRows.forEach((row) => tbody.appendChild(row));
        } else {
            rows.forEach((row) => tbody.appendChild(row));
        }
        applySearchFilter();
    }

    window.applyLeadListView = function applyLeadListView(viewName) {
        const url = new URL(window.location.href);
        url.searchParams.set("view", viewName === "recent" ? "recent" : "all");
        window.location.href = url.toString();
    };

    window.refreshLeadListView = function refreshLeadListView() {
        window.location.reload();
    };

    window.filterLeadListView = function filterLeadListView(query) {
        if (searchInput && searchInput.value !== query) {
            searchInput.value = query;
        }
        applySearchFilter();
    };

    if (config.currentView === "recent") {
        selector.value = "recent";
    }

    applyRecentView();
}
