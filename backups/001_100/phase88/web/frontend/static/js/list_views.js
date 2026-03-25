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

function readLeadListViewLayout(storageKey, defaultColumns) {
    try {
        const raw = localStorage.getItem(`${storageKey}_layout`);
        const parsed = raw ? JSON.parse(raw) : {};
        const configuredColumns = Array.isArray(parsed.visibleColumns) ? parsed.visibleColumns : defaultColumns;
        const visibleColumns = defaultColumns.filter((columnKey) => configuredColumns.includes(columnKey));
        return {
            visibleColumns: visibleColumns.length ? visibleColumns : defaultColumns.slice(),
        };
    } catch (_error) {
        return {
            visibleColumns: defaultColumns.slice(),
        };
    }
}

function writeLeadListViewLayout(storageKey, layout) {
    localStorage.setItem(`${storageKey}_layout`, JSON.stringify(layout));
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
    const setupDropdown = document.getElementById(config.setupDropdownId);
    const rows = tbody ? Array.from(tbody.querySelectorAll("tr")) : [];
    const columnHeaders = table ? Array.from(table.querySelectorAll("thead th[data-column-key]")) : [];
    const setupCheckboxes = setupDropdown ? Array.from(setupDropdown.querySelectorAll("input[data-column-key]")) : [];
    const allColumnKeys = columnHeaders.map((header) => header.dataset.columnKey);
    const columnLabels = new Map(columnHeaders.map((header) => [
        header.dataset.columnKey,
        header.dataset.columnLabel || header.textContent.trim(),
    ]));

    if (!tbody || !table || !summary || !selector) {
        return;
    }

    let activeLayout = readLeadListViewLayout(config.storageKey, allColumnKeys);

    function getCurrentView() {
        return selector.value === "recent" ? "recent" : "all";
    }

    function getVisibleRows() {
        return Array.from(tbody.querySelectorAll("tr")).filter((row) => row.style.display !== "none");
    }

    function getVisibleColumns() {
        return activeLayout.visibleColumns.length ? activeLayout.visibleColumns : allColumnKeys;
    }

    function syncSetupCheckboxes() {
        const visibleColumns = getVisibleColumns();
        setupCheckboxes.forEach((checkbox) => {
            checkbox.checked = visibleColumns.includes(checkbox.dataset.columnKey);
        });
    }

    function getPendingVisibleColumns() {
        const selectedColumns = setupCheckboxes
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.dataset.columnKey);
        return allColumnKeys.filter((columnKey) => selectedColumns.includes(columnKey));
    }

    function updateSortLabel() {
        const currentSort = document.getElementById(config.currentSortId);
        if (!currentSort) {
            return;
        }

        const visibleColumns = getVisibleColumns();
        const sortLabel = currentSort.textContent.trim();
        const isVisible = visibleColumns.some((columnKey) => columnLabels.get(columnKey) === sortLabel);
        if (!isVisible) {
            currentSort.textContent = columnLabels.get(visibleColumns[0]) || "Name";
        }
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

    function applyColumnLayout(visibleColumns) {
        const normalizedColumns = allColumnKeys.filter((columnKey) => visibleColumns.includes(columnKey));
        activeLayout = {
            visibleColumns: normalizedColumns.length ? normalizedColumns : allColumnKeys.slice(),
        };

        const activeColumns = getVisibleColumns();

        columnHeaders.forEach((header) => {
            header.style.display = activeColumns.includes(header.dataset.columnKey) ? "" : "none";
        });

        table.querySelectorAll("tbody td[data-column-key]").forEach((cell) => {
            cell.style.display = activeColumns.includes(cell.dataset.columnKey) ? "" : "none";
        });

        syncSetupCheckboxes();
        updateSortLabel();
        updateSummary();
        updateEmptyState();
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

        applyColumnLayout(getVisibleColumns());
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

    window.saveLeadListViewLayout = function saveLeadListViewLayout() {
        const visibleColumns = getPendingVisibleColumns();
        const resolvedColumns = visibleColumns.length ? visibleColumns : allColumnKeys.slice(0, 1);
        writeLeadListViewLayout(config.storageKey, {
            visibleColumns: resolvedColumns,
        });
        applyColumnLayout(resolvedColumns);
        if (setupDropdown) {
            setupDropdown.classList.remove("active");
        }
    };

    window.resetLeadListViewLayout = function resetLeadListViewLayout() {
        localStorage.removeItem(`${config.storageKey}_layout`);
        applyColumnLayout(allColumnKeys.slice());
        if (setupDropdown) {
            setupDropdown.classList.remove("active");
        }
    };

    if (config.currentView === "recent") {
        selector.value = "recent";
    }

    syncSetupCheckboxes();
    applyRecentView();
}
