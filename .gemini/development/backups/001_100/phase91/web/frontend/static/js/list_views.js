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

function normalizeLeadListColumns(columns, allColumnKeys) {
    const orderedColumns = allColumnKeys.filter((columnKey) => columns.includes(columnKey));
    return orderedColumns.length ? orderedColumns : allColumnKeys.slice();
}

function normalizeLeadListFilters(filters) {
    return {
        searchTerm: typeof filters?.searchTerm === "string" ? filters.searchTerm : "",
        status: typeof filters?.status === "string" ? filters.status : "all",
    };
}

function readLeadListViewCustomViews(storageKey, allColumnKeys) {
    try {
        const raw = localStorage.getItem(`${storageKey}_custom_views`);
        const parsed = raw ? JSON.parse(raw) : [];
        if (!Array.isArray(parsed)) {
            return [];
        }

        return parsed
            .filter((view) => view && typeof view.id === "string" && typeof view.label === "string")
            .map((view) => ({
                id: view.id,
                label: view.label,
                source: view.source === "recent" ? "recent" : "all",
                visibleColumns: normalizeLeadListColumns(Array.isArray(view.visibleColumns) ? view.visibleColumns : allColumnKeys, allColumnKeys),
                filters: normalizeLeadListFilters(view.filters),
                editable: true,
            }));
    } catch (_error) {
        return [];
    }
}

function writeLeadListViewCustomViews(storageKey, views) {
    localStorage.setItem(`${storageKey}_custom_views`, JSON.stringify(views));
}

function buildLeadListViewId(label) {
    const slug = label
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "") || "custom-view";
    return `custom-${slug}-${Date.now()}`;
}

function confirmLeadListAction(title, message, onConfirm) {
    if (typeof showConfirmModal === "function") {
        showConfirmModal(title, message, onConfirm);
        return;
    }

    if (window.confirm(message)) {
        onConfirm();
    }
}

function initializeLeadListView(config) {
    const tbody = document.getElementById(config.tableBodyId);
    const table = document.querySelector(config.tableSelector);
    const summary = document.getElementById(config.summaryId);
    const emptyState = document.getElementById(config.emptyStateId);
    const selector = document.getElementById(config.selectorId);
    const pinButton = document.getElementById(config.pinButtonId);
    const searchInput = document.getElementById(config.searchInputId);
    const chip = document.getElementById(config.currentViewChipId);
    const viewSummary = document.getElementById(config.currentViewSummaryId);
    const setupDropdown = document.getElementById(config.setupDropdownId);
    const setupNameInput = document.getElementById(config.setupNameInputId);
    const setupSourceInput = document.getElementById(config.setupSourceInputId);
    const setupSearchTermInput = document.getElementById(config.setupSearchTermInputId);
    const setupStatusFilterInput = document.getElementById(config.setupStatusFilterInputId);
    const setupColumnList = document.getElementById(config.setupColumnListId);
    const saveViewButton = document.getElementById(config.saveViewButtonId);
    const deleteViewButton = document.getElementById(config.deleteViewButtonId);
    const setupMeta = document.getElementById(config.setupMetaId);
    const rows = tbody ? Array.from(tbody.querySelectorAll("tr")) : [];
    const headerRow = table ? table.querySelector("thead tr") : null;
    const columnHeaders = table ? Array.from(table.querySelectorAll("thead th[data-column-key]")) : [];
    const allColumnKeys = columnHeaders.map((header) => header.dataset.columnKey);
    const columnLabels = new Map(columnHeaders.map((header) => [
        header.dataset.columnKey,
        header.dataset.columnLabel || header.textContent.trim(),
    ]));

    if (!tbody || !table || !summary || !selector || !headerRow) {
        return;
    }

    const requestedViewId = new URL(window.location.href).searchParams.get("view");
    const pinnedViewId = localStorage.getItem(`${config.storageKey}_pinned_view`);
    const builtinViews = [
        {
            id: "all",
            label: config.allLabel || "All Leads",
            source: "all",
            visibleColumns: allColumnKeys.slice(),
            filters: normalizeLeadListFilters({}),
            editable: false,
        },
        {
            id: "recent",
            label: config.recentLabel || "Recently Viewed",
            source: "recent",
            visibleColumns: allColumnKeys.slice(),
            filters: normalizeLeadListFilters({}),
            editable: false,
        },
    ];
    const state = {
        customViews: readLeadListViewCustomViews(config.storageKey, allColumnKeys),
        activeViewId: requestedViewId || pinnedViewId || localStorage.getItem(`${config.storageKey}_active_view`) || config.currentView || "all",
    };
    let draggedColumnItem = null;

    function getAllViews() {
        return builtinViews.concat(state.customViews);
    }

    function getViewById(viewId) {
        return getAllViews().find((view) => view.id === viewId) || builtinViews[0];
    }

    function getActiveView() {
        return getViewById(state.activeViewId);
    }

    function getVisibleRows() {
        return Array.from(tbody.querySelectorAll("tr")).filter((row) => row.style.display !== "none");
    }

    function getColumnItems() {
        return setupColumnList ? Array.from(setupColumnList.querySelectorAll("[data-column-key]")) : [];
    }

    function getOrderedColumnKeysFromSetup() {
        return getColumnItems().map((item) => item.dataset.columnKey);
    }

    function getPinnedViewId() {
        return localStorage.getItem(`${config.storageKey}_pinned_view`);
    }

    function persistCustomViews() {
        writeLeadListViewCustomViews(config.storageKey, state.customViews);
    }

    function syncSelectorOptions() {
        const activeView = getActiveView();
        selector.innerHTML = getAllViews()
            .map((view) => `<option value="${view.id}">${view.label}</option>`)
            .join("");
        selector.value = activeView.id;
    }

    function reorderSetupList(columnOrder) {
        if (!setupColumnList) {
            return;
        }

        const remainingColumns = allColumnKeys.filter((columnKey) => !columnOrder.includes(columnKey));
        const finalOrder = columnOrder.concat(remainingColumns);
        const itemMap = new Map(getColumnItems().map((item) => [item.dataset.columnKey, item]));
        const fragment = document.createDocumentFragment();

        finalOrder.forEach((columnKey) => {
            const item = itemMap.get(columnKey);
            if (item) {
                fragment.appendChild(item);
            }
        });

        setupColumnList.innerHTML = "";
        setupColumnList.appendChild(fragment);
    }

    function bindColumnDragAndDrop() {
        getColumnItems().forEach((item) => {
            if (item.dataset.dragBound === "true") {
                return;
            }

            item.dataset.dragBound = "true";

            item.addEventListener("dragstart", () => {
                draggedColumnItem = item;
                item.classList.add("dragging");
            });

            item.addEventListener("dragend", () => {
                item.classList.remove("dragging");
                draggedColumnItem = null;
            });

            item.addEventListener("dragover", (event) => {
                event.preventDefault();
                if (!draggedColumnItem || draggedColumnItem === item) {
                    return;
                }

                const rect = item.getBoundingClientRect();
                const insertAfter = event.clientY > rect.top + rect.height / 2;
                if (insertAfter) {
                    item.after(draggedColumnItem);
                } else {
                    item.before(draggedColumnItem);
                }
            });
        });
    }

    function syncPinButton() {
        if (!pinButton) {
            return;
        }

        const activeView = getActiveView();
        const isPinned = getPinnedViewId() === activeView.id;
        pinButton.textContent = isPinned ? "Pinned" : "Pin";
        pinButton.classList.toggle("is-pinned", isPinned);
    }

    function syncSetupForm() {
        const activeView = getActiveView();
        const visibleColumns = activeView.visibleColumns || allColumnKeys;

        if (setupNameInput) {
            setupNameInput.value = activeView.editable ? activeView.label : "";
            setupNameInput.placeholder = activeView.editable ? "Enter a list view name" : `${activeView.label} (clone to customize)`;
        }

        if (setupSourceInput) {
            setupSourceInput.value = activeView.source;
        }

        if (setupSearchTermInput) {
            setupSearchTermInput.value = activeView.filters.searchTerm;
        }

        if (setupStatusFilterInput) {
            setupStatusFilterInput.value = activeView.filters.status;
        }

        reorderSetupList(visibleColumns);
        bindColumnDragAndDrop();

        getColumnItems().forEach((item) => {
            const checkbox = item.querySelector("input[data-column-key]");
            if (checkbox) {
                checkbox.checked = visibleColumns.includes(item.dataset.columnKey);
            }
        });

        if (saveViewButton) {
            saveViewButton.disabled = !activeView.editable;
        }

        if (deleteViewButton) {
            deleteViewButton.disabled = !activeView.editable;
        }

        if (setupMeta) {
            setupMeta.textContent = activeView.editable
                ? `Editing ${activeView.label}. Save Changes updates this view for your user.`
                : "Built-in views can be cloned into your own custom layouts.";
        }

        syncPinButton();
    }

    function reorderTableColumns(orderedVisibleColumns) {
        const remainingColumns = allColumnKeys.filter((columnKey) => !orderedVisibleColumns.includes(columnKey));
        const finalOrder = orderedVisibleColumns.concat(remainingColumns);
        const actionHeader = headerRow.lastElementChild;
        const headerMap = new Map(columnHeaders.map((header) => [header.dataset.columnKey, header]));

        finalOrder.forEach((columnKey) => {
            const header = headerMap.get(columnKey);
            if (header) {
                headerRow.insertBefore(header, actionHeader);
            }
        });

        rows.forEach((row) => {
            const actionCell = row.lastElementChild;
            const cellMap = new Map(Array.from(row.querySelectorAll("td[data-column-key]")).map((cell) => [cell.dataset.columnKey, cell]));
            finalOrder.forEach((columnKey) => {
                const cell = cellMap.get(columnKey);
                if (cell) {
                    row.insertBefore(cell, actionCell);
                }
            });
        });
    }

    function updateSummary() {
        const activeView = getActiveView();
        const visibleCount = getVisibleRows().length;
        const statusFilterLabel = activeView.filters.status === "all" ? activeView.label : `${activeView.label} / ${activeView.filters.status}`;

        if (viewSummary) {
            viewSummary.textContent = activeView.source === "recent" ? "Showing your recently opened leads" : `Filtered by ${statusFilterLabel}`;
        }

        if (chip) {
            chip.textContent = activeView.label;
        }

        summary.innerHTML = `${visibleCount} items - Sorted by <span id="${config.currentSortId}">${document.getElementById(config.currentSortId)?.textContent || "Name"}</span> - <span id="${config.currentViewSummaryId}">${activeView.source === "recent" ? "Showing your recently opened leads" : `Filtered by ${statusFilterLabel}`}</span> - Updated just now`;
    }

    function updateEmptyState() {
        const visibleCount = getVisibleRows().length;
        const activeView = getActiveView();
        const shouldShowEmpty = activeView.source === "recent" && visibleCount === 0;
        emptyState.style.display = shouldShowEmpty ? "flex" : "none";
        table.style.display = shouldShowEmpty ? "none" : "table";
    }

    function updateSortLabel() {
        const currentSort = document.getElementById(config.currentSortId);
        const activeView = getActiveView();
        if (!currentSort) {
            return;
        }

        const isVisible = activeView.visibleColumns.some((columnKey) => columnLabels.get(columnKey) === currentSort.textContent.trim());
        if (!isVisible) {
            currentSort.textContent = columnLabels.get(activeView.visibleColumns[0]) || "Name";
        }
    }

    function applyColumnLayout(visibleColumns) {
        const normalizedColumns = normalizeLeadListColumns(visibleColumns, allColumnKeys);
        reorderTableColumns(normalizedColumns);

        columnHeaders.forEach((header) => {
            header.style.display = normalizedColumns.includes(header.dataset.columnKey) ? "" : "none";
        });

        table.querySelectorAll("tbody td[data-column-key]").forEach((cell) => {
            cell.style.display = normalizedColumns.includes(cell.dataset.columnKey) ? "" : "none";
        });

        updateSortLabel();
        updateSummary();
        updateEmptyState();
    }

    function applyRowOrdering() {
        const activeView = getActiveView();
        const recentRecords = readRecentListViewRecords(config.storageKey);
        const rowMap = new Map(rows.map((row) => [row.dataset.recordId, row]));
        const orderedRecentRows = recentRecords.map((record) => rowMap.get(record.id)).filter(Boolean);

        tbody.innerHTML = "";
        if (activeView.source === "recent") {
            orderedRecentRows.forEach((row) => tbody.appendChild(row));
        } else {
            rows.forEach((row) => tbody.appendChild(row));
        }
    }

    function applySearchFilter() {
        const activeView = getActiveView();
        const query = (searchInput?.value || "").trim().toLowerCase();
        const statusFilter = activeView.filters.status;

        Array.from(tbody.querySelectorAll("tr")).forEach((row) => {
            const text = row.innerText.toLowerCase();
            const rowStatusCell = row.querySelector('td[data-column-key="status"]');
            const rowStatus = rowStatusCell ? rowStatusCell.innerText.trim() : "";
            const matchesQuery = !query || text.includes(query);
            const matchesStatus = statusFilter === "all" || rowStatus === statusFilter;
            row.style.display = matchesQuery && matchesStatus ? "" : "none";
        });

        updateSummary();
        updateEmptyState();
    }

    function getFormColumns() {
        return normalizeLeadListColumns(
            getColumnItems()
                .filter((item) => {
                    const checkbox = item.querySelector("input[data-column-key]");
                    return checkbox && checkbox.checked;
                })
                .map((item) => item.dataset.columnKey),
            allColumnKeys,
        );
    }

    function getFormFilters() {
        return normalizeLeadListFilters({
            searchTerm: setupSearchTermInput?.value || "",
            status: setupStatusFilterInput?.value || "all",
        });
    }

    function updateUrl(viewId) {
        const url = new URL(window.location.href);
        url.searchParams.set("view", viewId);
        window.history.replaceState({}, "", url.toString());
    }

    function renderView() {
        const activeView = getActiveView();
        localStorage.setItem(`${config.storageKey}_active_view`, activeView.id);
        syncSelectorOptions();
        syncSetupForm();

        if (searchInput) {
            searchInput.value = activeView.filters.searchTerm;
        }

        applyRowOrdering();
        applyColumnLayout(activeView.visibleColumns);
        applySearchFilter();
        updateUrl(activeView.id);
    }

    function saveCustomView(viewId, updates) {
        state.customViews = state.customViews.map((view) => {
            if (view.id !== viewId) {
                return view;
            }
            return {
                ...view,
                ...updates,
            };
        });
        persistCustomViews();
    }

    window.applyLeadListView = function applyLeadListView(viewId) {
        state.activeViewId = getViewById(viewId).id;
        renderView();
    };

    window.refreshLeadListView = function refreshLeadListView() {
        renderView();
        if (typeof showToast === "function") {
            showToast("Lead list refreshed.");
        }
    };

    window.filterLeadListView = function filterLeadListView(query) {
        if (searchInput && searchInput.value !== query) {
            searchInput.value = query;
        }
        applySearchFilter();
    };

    window.toggleLeadListViewPin = function toggleLeadListViewPin() {
        const activeView = getActiveView();
        const isPinned = getPinnedViewId() === activeView.id;
        const title = isPinned ? "Unpin list view" : "Pin list view";
        const message = isPinned
            ? `Remove ${activeView.label} as your pinned default list view?`
            : `Pin ${activeView.label} as your default list view?`;

        confirmLeadListAction(title, message, () => {
            if (isPinned) {
                localStorage.removeItem(`${config.storageKey}_pinned_view`);
            } else {
                localStorage.setItem(`${config.storageKey}_pinned_view`, activeView.id);
            }
            syncPinButton();
            if (typeof showToast === "function") {
                showToast(isPinned ? "List view unpinned." : `Pinned ${activeView.label}.`);
            }
        });
    };

    window.saveNewLeadListView = function saveNewLeadListView() {
        const label = (setupNameInput?.value || "").trim();
        if (!label) {
            if (typeof showToast === "function") {
                showToast("Add a view name before saving.", true);
            }
            return;
        }

        confirmLeadListAction("Create list view", `Create ${label}?`, () => {
            const newView = {
                id: buildLeadListViewId(label),
                label,
                source: setupSourceInput?.value === "recent" ? "recent" : "all",
                visibleColumns: getFormColumns(),
                filters: getFormFilters(),
                editable: true,
            };

            state.customViews = state.customViews.concat(newView);
            persistCustomViews();
            state.activeViewId = newView.id;
            renderView();

            if (typeof showToast === "function") {
                showToast(`Saved ${label}.`);
            }
        });
    };

    window.saveLeadListViewLayout = function saveLeadListViewLayout() {
        const activeView = getActiveView();
        if (!activeView.editable) {
            if (typeof showToast === "function") {
                showToast("Clone this built-in view to create your own version.", true);
            }
            return;
        }

        const label = (setupNameInput?.value || "").trim() || activeView.label;
        saveCustomView(activeView.id, {
            label,
            source: setupSourceInput?.value === "recent" ? "recent" : "all",
            visibleColumns: getFormColumns(),
            filters: getFormFilters(),
        });
        renderView();

        if (typeof showToast === "function") {
            showToast(`Updated ${label}.`);
        }
    };

    window.cloneLeadListView = function cloneLeadListView() {
        const activeView = getActiveView();
        const label = `${activeView.label} Copy`;

        confirmLeadListAction("Clone list view", `Create a copy of ${activeView.label}?`, () => {
            const newView = {
                id: buildLeadListViewId(label),
                label,
                source: setupSourceInput?.value === "recent" ? "recent" : activeView.source,
                visibleColumns: getFormColumns(),
                filters: getFormFilters(),
                editable: true,
            };

            state.customViews = state.customViews.concat(newView);
            persistCustomViews();
            state.activeViewId = newView.id;
            renderView();

            if (typeof showToast === "function") {
                showToast(`Cloned ${activeView.label}.`);
            }
        });
    };

    window.deleteLeadListView = function deleteLeadListView() {
        const activeView = getActiveView();
        if (!activeView.editable) {
            if (typeof showToast === "function") {
                showToast("Built-in views cannot be deleted.", true);
            }
            return;
        }

        confirmLeadListAction("Delete list view", `Delete ${activeView.label}?`, () => {
            state.customViews = state.customViews.filter((view) => view.id !== activeView.id);
            persistCustomViews();

            if (getPinnedViewId() === activeView.id) {
                localStorage.removeItem(`${config.storageKey}_pinned_view`);
            }

            state.activeViewId = "all";
            renderView();

            if (typeof showToast === "function") {
                showToast(`Deleted ${activeView.label}.`);
            }
        });
    };

    window.resetLeadListViewLayout = function resetLeadListViewLayout() {
        syncSetupForm();
    };

    state.activeViewId = getViewById(state.activeViewId).id;
    bindColumnDragAndDrop();
    renderView();
}
