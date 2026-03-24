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
    const orderedColumns = allColumnKeys.filter((columnKey) => Array.isArray(columns) && columns.includes(columnKey));
    return orderedColumns.length ? orderedColumns : allColumnKeys.slice();
}

function normalizeLeadListFilters(filters) {
    const normalizedConditions = Array.isArray(filters?.conditions)
        ? filters.conditions
            .filter((condition) => condition && condition.field && condition.operator)
            .map((condition) => ({
                field: String(condition.field),
                operator: String(condition.operator),
                value: String(condition.value || ""),
            }))
        : [];

    return {
        searchTerm: String(filters?.searchTerm || ""),
        logic: String(filters?.logic || "and").toLowerCase() === "or" ? "or" : "and",
        conditions: normalizedConditions,
    };
}

function normalizeLeadListView(view, allColumnKeys) {
    return {
        id: String(view.id),
        label: String(view.label || "Untitled View"),
        source: view.source === "recent" ? "recent" : "all",
        visibleColumns: normalizeLeadListColumns(view.visibleColumns, allColumnKeys),
        filters: normalizeLeadListFilters(view.filters),
        editable: Boolean(view.editable),
        isPinned: Boolean(view.isPinned),
    };
}

async function requestLeadListView(url, method, payload) {
    const response = await fetch(url, {
        method,
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: payload ? JSON.stringify(payload) : undefined,
    });
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) {
        const text = await response.text();
        throw new Error(`List view request failed (${response.status}). ${text.slice(0, 80)}`);
    }
    const data = await response.json();
    if (!response.ok || data.status === "error") {
        throw new Error(data.message || "Lead list view request failed");
    }
    return data;
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

function escapeLeadListViewHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function initializeObjectListView(config) {
    const tbody = document.getElementById(config.tableBodyId);
    const table = document.querySelector(config.tableSelector);
    const summary = document.getElementById(config.summaryId);
    const emptyState = document.getElementById(config.emptyStateId);
    const selector = document.getElementById(config.selectorId);
    const selectorButton = document.getElementById(config.selectorButtonId);
    const selectorMenu = document.getElementById(config.selectorMenuId);
    const pinButton = document.getElementById(config.pinButtonId);
    const searchInput = document.getElementById(config.searchInputId);
    const chip = document.getElementById(config.currentViewChipId);
    const viewSummary = document.getElementById(config.currentViewSummaryId);
    const setupDropdown = document.getElementById(config.setupDropdownId);
    const setupNameInput = document.getElementById(config.setupNameInputId);
    const setupSourceInput = document.getElementById(config.setupSourceInputId);
    const setupSearchTermInput = document.getElementById(config.setupSearchTermInputId);
    const setupFilterLogicInput = document.getElementById(config.setupFilterLogicInputId);
    const setupFilterList = document.getElementById(config.setupFilterListId);
    const setupColumnList = document.getElementById(config.setupColumnListId);
    const saveViewButton = document.getElementById(config.saveViewButtonId);
    const deleteViewButton = document.getElementById(config.deleteViewButtonId);
    const setupMeta = document.getElementById(config.setupMetaId);
    const rows = tbody ? Array.from(tbody.querySelectorAll("tr")) : [];
    const headerRow = table ? table.querySelector("thead tr") : null;
    const columnHeaders = table ? Array.from(table.querySelectorAll("thead th[data-column-key]")) : [];
    const allColumnKeys = columnHeaders.map((header) => header.dataset.columnKey);
    const objectDisplayName = config.objectDisplayName || "Lead";
    const objectApiPath = config.objectApiPath || "/leads/views";
    const recentSummaryText = config.recentSummaryText || `Showing your recently opened ${objectDisplayName.toLowerCase()}s`;
    const applyViewFunctionName = config.applyViewFunctionName || `apply${objectDisplayName}ListView`;
    const refreshViewFunctionName = config.refreshViewFunctionName || `refresh${objectDisplayName}ListView`;
    const filterViewFunctionName = config.filterViewFunctionName || `filter${objectDisplayName}ListView`;
    const addFilterFunctionName = config.addFilterFunctionName || `add${objectDisplayName}ListViewFilterCondition`;
    const removeFilterFunctionName = config.removeFilterFunctionName || `remove${objectDisplayName}ListViewFilterCondition`;
    const togglePinFunctionName = config.togglePinFunctionName || `toggle${objectDisplayName}ListViewPin`;
    const saveNewViewFunctionName = config.saveNewViewFunctionName || `saveNew${objectDisplayName}ListView`;
    const saveViewFunctionName = config.saveViewFunctionName || `save${objectDisplayName}ListViewLayout`;
    const cloneViewFunctionName = config.cloneViewFunctionName || `clone${objectDisplayName}ListView`;
    const deleteViewFunctionName = config.deleteViewFunctionName || `delete${objectDisplayName}ListView`;
    const resetViewFunctionName = config.resetViewFunctionName || `reset${objectDisplayName}ListViewLayout`;
    const columnLabels = new Map(columnHeaders.map((header) => [
        header.dataset.columnKey,
        header.dataset.columnLabel || header.textContent.trim(),
    ]));
    const fieldOptions = Array.isArray(config.fieldOptions) && config.fieldOptions.length
        ? config.fieldOptions
        : allColumnKeys.map((columnKey) => ({ value: columnKey, label: columnLabels.get(columnKey) || columnKey }));
    const defaultFilterCondition = config.defaultFilterCondition || { field: fieldOptions[0]?.value || "name", operator: "contains", value: "" };
    const defaultViews = [
        { id: "all", label: config.allLabel || "All Leads", source: "all", visibleColumns: allColumnKeys, filters: normalizeLeadListFilters({}), editable: false, isPinned: false },
        { id: "recent", label: config.recentLabel || "Recently Viewed", source: "recent", visibleColumns: allColumnKeys, filters: normalizeLeadListFilters({}), editable: false, isPinned: false },
    ];

    if (!tbody || !table || !summary || !selector || !headerRow) {
        return;
    }

    const state = {
        savedViews: (Array.isArray(config.savedViews) && config.savedViews.length ? config.savedViews : defaultViews).map((view) => normalizeLeadListView(view, allColumnKeys)),
        activeViewId: config.currentView || config.pinnedViewId || "all",
        rowDisplayLimit: config.initialRowLimit || 50,
    };
    let draggedColumnItem = null;
    let isLoadingMoreRows = false;
    let listMoreLoader = null;

    function getAllViews() {
        return state.savedViews.length ? state.savedViews : defaultViews;
    }

    function getViewById(viewId) {
        return getAllViews().find((view) => view.id === viewId) || getAllViews()[0];
    }

    function getActiveView() {
        return getViewById(state.activeViewId);
    }

    function getVisibleRows() {
        return Array.from(tbody.querySelectorAll("tr")).filter((row) => row.style.display !== "none");
    }

    function getFilteredRows() {
        return Array.from(tbody.querySelectorAll("tr")).filter((row) => row.dataset.filterVisible !== "false");
    }

    function ensureListMoreLoader() {
        if (!table || listMoreLoader) {
            return;
        }
        listMoreLoader = document.createElement("div");
        listMoreLoader.className = "sf-list-view-more-loader";
        listMoreLoader.style.display = "none";
        listMoreLoader.innerHTML = '<span class="sf-list-view-more-spinner"></span><span>Loading more…</span>';
        table.insertAdjacentElement("afterend", listMoreLoader);
    }

    function getColumnItems() {
        return setupColumnList ? Array.from(setupColumnList.querySelectorAll(".sf-list-view-column-item")) : [];
    }

    function syncSelectorOptions() {
        const activeView = getActiveView();
        selector.innerHTML = getAllViews().map((view) => `<option value="${view.id}">${view.label}</option>`).join("");
        selector.value = activeView.id;
        if (selectorButton) {
            selectorButton.dataset.noLoading = "true";
            selectorButton.querySelector('[data-current-view-label]')?.replaceChildren(document.createTextNode(activeView.label));
        }
        if (selectorMenu) {
            selectorMenu.innerHTML = getAllViews().map((view) => `
                <button type="button" class="sf-dropdown-item sf-list-view-option${view.id === activeView.id ? ' is-active' : ''}" data-view-id="${escapeLeadListViewHtml(view.id)}">
                    <span class="sf-list-view-option-check">${view.id === activeView.id ? '✓' : ''}</span>
                    <span>${escapeLeadListViewHtml(view.label)}</span>
                </button>
            `).join("");
            selectorMenu.querySelectorAll('[data-view-id]').forEach((button) => {
                button.dataset.noLoading = "true";
                button.addEventListener('click', () => {
                    applyViewById(button.dataset.viewId);
                    const dropdown = button.closest('.sf-dropdown');
                    if (dropdown) {
                        dropdown.classList.remove('active');
                    }
                });
            });
        }
    }

    function applyViewById(viewId) {
        state.activeViewId = getViewById(viewId).id;
        renderView();
    }

    function reorderSetupList(columnOrder) {
        if (!setupColumnList) {
            return;
        }

        const itemMap = new Map(getColumnItems().map((item) => [item.dataset.columnKey, item]));
        const finalOrder = columnOrder.concat(allColumnKeys.filter((columnKey) => !columnOrder.includes(columnKey)));
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

    function renderFilterConditions(conditions) {
        if (!setupFilterList) {
            return;
        }

        const normalizedConditions = conditions.length ? conditions : [defaultFilterCondition];
        const filterFieldOptionsHtml = fieldOptions.map((option) => `<option value="${escapeLeadListViewHtml(option.value)}">${escapeLeadListViewHtml(option.label)}</option>`).join("");
        setupFilterList.innerHTML = normalizedConditions.map((condition) => `
            <div class="sf-list-view-filter-row">
                <select class="sf-list-view-form-input" data-filter-field>
                    ${filterFieldOptionsHtml.replace(`value="${escapeLeadListViewHtml(condition.field)}"`, `value="${escapeLeadListViewHtml(condition.field)}" selected`)}
                </select>
                <select class="sf-list-view-form-input" data-filter-operator>
                    <option value="contains" ${condition.operator === "contains" ? "selected" : ""}>contains</option>
                    <option value="equals" ${condition.operator === "equals" ? "selected" : ""}>equals</option>
                    <option value="not_equals" ${condition.operator === "not_equals" ? "selected" : ""}>does not equal</option>
                    <option value="starts_with" ${condition.operator === "starts_with" ? "selected" : ""}>starts with</option>
                    <option value="ends_with" ${condition.operator === "ends_with" ? "selected" : ""}>ends with</option>
                </select>
                <input class="sf-list-view-form-input" data-filter-value value="${escapeLeadListViewHtml(condition.value)}" placeholder="Filter value">
                <button type="button" class="sf-list-view-remove-filter" onclick="window.${removeFilterFunctionName}(this)">Remove</button>
            </div>
        `).join("");
    }

    function getFilterConditionsFromForm() {
        if (!setupFilterList) {
            return [];
        }

        return Array.from(setupFilterList.querySelectorAll(".sf-list-view-filter-row"))
            .map((row) => ({
                field: row.querySelector("[data-filter-field]")?.value || "name",
                operator: row.querySelector("[data-filter-operator]")?.value || "contains",
                value: row.querySelector("[data-filter-value]")?.value || "",
            }))
            .filter((condition) => condition.value.trim());
    }

    function syncPinButton() {
        if (!pinButton) {
            return;
        }

        const activeView = getActiveView();
        pinButton.textContent = activeView.isPinned ? "Pinned" : "Pin";
        pinButton.classList.toggle("is-pinned", activeView.isPinned);
    }

    function syncSetupForm() {
        const activeView = getActiveView();
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
        if (setupFilterLogicInput) {
            setupFilterLogicInput.value = activeView.filters.logic;
        }

        reorderSetupList(activeView.visibleColumns);
        bindColumnDragAndDrop();
        getColumnItems().forEach((item) => {
            const checkbox = item.querySelector("input[data-column-key]");
            if (checkbox) {
                checkbox.checked = activeView.visibleColumns.includes(item.dataset.columnKey);
            }
        });

        renderFilterConditions(activeView.filters.conditions);

        if (saveViewButton) {
            saveViewButton.disabled = !activeView.editable;
        }
        if (deleteViewButton) {
            deleteViewButton.disabled = !activeView.editable;
        }
        if (setupMeta) {
            setupMeta.textContent = activeView.editable
                ? `Editing ${activeView.label}. Save Changes updates the database-backed view for this test user.`
                : "Built-in views can be cloned into your own custom layouts.";
        }

        syncPinButton();
    }

    function reorderTableColumns(orderedVisibleColumns) {
        const orderedColumns = orderedVisibleColumns.concat(allColumnKeys.filter((columnKey) => !orderedVisibleColumns.includes(columnKey)));
        const actionHeader = headerRow.lastElementChild;
        const headerMap = new Map(columnHeaders.map((header) => [header.dataset.columnKey, header]));

        orderedColumns.forEach((columnKey) => {
            const header = headerMap.get(columnKey);
            if (header) {
                headerRow.insertBefore(header, actionHeader);
            }
        });

        rows.forEach((row) => {
            const actionCell = row.lastElementChild;
            const cellMap = new Map(Array.from(row.querySelectorAll("td[data-column-key]")).map((cell) => [cell.dataset.columnKey, cell]));
            orderedColumns.forEach((columnKey) => {
                const cell = cellMap.get(columnKey);
                if (cell) {
                    row.insertBefore(cell, actionCell);
                }
            });
        });
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

    function updateSummary() {
        const activeView = getActiveView();
        const visibleCount = getFilteredRows().length;
        const filterCopy = activeView.filters.conditions.length
            ? `${activeView.label} (${activeView.filters.logic.toUpperCase()} filters)`
            : activeView.label;

        if (viewSummary) {
            viewSummary.textContent = activeView.source === "recent" ? recentSummaryText : `Filtered by ${filterCopy}`;
        }
        if (chip) {
            chip.textContent = activeView.label;
        }

        summary.innerHTML = `${visibleCount} items - Sorted by <span id="${config.currentSortId}">${document.getElementById(config.currentSortId)?.textContent || "Name"}</span> - <span id="${config.currentViewSummaryId}">${activeView.source === "recent" ? recentSummaryText : `Filtered by ${filterCopy}`}</span> - Updated just now`;
    }

    function updateEmptyState() {
        const visibleCount = getFilteredRows().length;
        const activeView = getActiveView();
        const shouldShowEmpty = activeView.source === "recent" && visibleCount === 0;
        emptyState.style.display = shouldShowEmpty ? "flex" : "none";
        table.style.display = shouldShowEmpty ? "none" : "table";
    }

    function applyRowWindowing() {
        const filteredRows = getFilteredRows();
        filteredRows.forEach((row, index) => {
            row.style.display = index < state.rowDisplayLimit ? "" : "none";
        });
        ensureListMoreLoader();
        if (listMoreLoader) {
            listMoreLoader.style.display = filteredRows.length > state.rowDisplayLimit || isLoadingMoreRows ? "flex" : "none";
            listMoreLoader.querySelector('span:last-child').textContent = isLoadingMoreRows ? 'Loading more…' : 'Scroll to load more';
        }
    }

    function getRowValue(row, field) {
        const cell = row.querySelector(`td[data-column-key="${field}"]`);
        return cell ? cell.innerText.trim() : "";
    }

    function matchesCondition(row, condition) {
        const actualValue = getRowValue(row, condition.field).toLowerCase();
        const expectedValue = String(condition.value || "").toLowerCase();
        if (!expectedValue) {
            return true;
        }

        switch (condition.operator) {
        case "equals":
            return actualValue === expectedValue;
        case "not_equals":
            return actualValue !== expectedValue;
        case "starts_with":
            return actualValue.startsWith(expectedValue);
        case "ends_with":
            return actualValue.endsWith(expectedValue);
        default:
            return actualValue.includes(expectedValue);
        }
    }

    function applyFilters() {
        const activeView = getActiveView();
        const query = (searchInput?.value || "").trim().toLowerCase();
        const conditions = activeView.filters.conditions || [];

        Array.from(tbody.querySelectorAll("tr")).forEach((row) => {
            const text = row.innerText.toLowerCase();
            const matchesSearch = !query || text.includes(query);
            const conditionMatches = !conditions.length || (activeView.filters.logic === "or"
                ? conditions.some((condition) => matchesCondition(row, condition))
                : conditions.every((condition) => matchesCondition(row, condition)));
            row.dataset.filterVisible = matchesSearch && conditionMatches ? "true" : "false";
        });

        applyRowWindowing();
        updateSummary();
        updateEmptyState();
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

    function getFormColumns() {
        return normalizeLeadListColumns(
            getColumnItems()
                .filter((item) => item.querySelector("input[data-column-key]")?.checked)
                .map((item) => item.dataset.columnKey),
            allColumnKeys,
        );
    }

    function getFormFilters() {
        return normalizeLeadListFilters({
            searchTerm: setupSearchTermInput?.value || "",
            logic: setupFilterLogicInput?.value || "and",
            conditions: getFilterConditionsFromForm(),
        });
    }

    function buildPayload(labelOverride) {
        return {
            label: labelOverride || setupNameInput?.value || getActiveView().label,
            source: setupSourceInput?.value || "all",
            visibleColumns: getFormColumns(),
            filters: getFormFilters(),
        };
    }

    function replaceView(view) {
        const normalizedView = normalizeLeadListView(view, allColumnKeys);
        const existingIndex = state.savedViews.findIndex((item) => item.id === normalizedView.id);
        if (existingIndex >= 0) {
            state.savedViews[existingIndex] = normalizedView;
        } else {
            state.savedViews.push(normalizedView);
        }
    }

    function applyPinnedState(pinnedViewId) {
        state.savedViews = state.savedViews.map((view) => ({
            ...view,
            isPinned: view.id === pinnedViewId,
        }));
    }

    function updateUrl(viewId) {
        const url = new URL(window.location.href);
        url.searchParams.set("view", viewId);
        window.history.replaceState({}, "", url.toString());
    }

    function renderView() {
        const activeView = getActiveView();
        state.rowDisplayLimit = config.initialRowLimit || 50;
        syncSelectorOptions();
        syncSetupForm();
        if (searchInput) {
            searchInput.value = activeView.filters.searchTerm;
        }
        applyRowOrdering();
        applyColumnLayout(activeView.visibleColumns);
        applyFilters();
        updateUrl(activeView.id);
    }

    window.addEventListener("scroll", () => {
        const filteredRows = getFilteredRows();
        if (isLoadingMoreRows || filteredRows.length <= state.rowDisplayLimit) {
            return;
        }
        if (window.innerHeight + window.scrollY < document.body.offsetHeight - 180) {
            return;
        }
        isLoadingMoreRows = true;
        applyRowWindowing();
        setTimeout(() => {
            state.rowDisplayLimit += config.initialRowLimit || 50;
            isLoadingMoreRows = false;
            applyRowWindowing();
            updateSummary();
        }, 350);
    });

    window[applyViewFunctionName] = function applyObjectListView(viewId) {
        applyViewById(viewId);
    };

    window[refreshViewFunctionName] = function refreshObjectListView() {
        renderView();
        if (typeof showToast === "function") {
            showToast(`${objectDisplayName} list refreshed.`);
        }
    };

    window[filterViewFunctionName] = function filterObjectListView(query) {
        if (searchInput && searchInput.value !== query) {
            searchInput.value = query;
        }
        applyFilters();
    };

    window[addFilterFunctionName] = function addObjectListViewFilterCondition() {
        const activeFilters = getFilterConditionsFromForm();
        activeFilters.push(defaultFilterCondition);
        renderFilterConditions(activeFilters);
    };

    window[removeFilterFunctionName] = function removeObjectListViewFilterCondition(button) {
        button.closest(".sf-list-view-filter-row")?.remove();
    };

    window[togglePinFunctionName] = function toggleObjectListViewPin() {
        const activeView = getActiveView();
        const shouldPin = !activeView.isPinned;

        requestLeadListView(`${objectApiPath}/${activeView.id}/pin`, "POST", { pinned: shouldPin }).then((data) => {
            applyPinnedState(data.pinned_view_id || "");
            renderView();
            if (typeof showToast === "function") {
                showToast(shouldPin ? `${activeView.label} is now pinned.` : "Pin removed.");
            }
        }).catch((error) => {
            if (typeof showToast === "function") {
                showToast(error.message, true);
            }
        });
    };

    window[saveNewViewFunctionName] = function saveNewObjectListView() {
        const label = (setupNameInput?.value || "").trim();
        if (!label) {
            if (typeof showToast === "function") {
                showToast("Add a view name before saving.", true);
            }
            return;
        }

        confirmLeadListAction("Create list view", `Create ${label}?`, async () => {
            try {
                const data = await requestLeadListView(objectApiPath, "POST", buildPayload(label));
                replaceView(data.view);
                state.activeViewId = data.view.id;
                renderView();
                if (typeof showToast === "function") {
                    showToast(`Saved ${label}.`);
                }
            } catch (error) {
                if (typeof showToast === "function") {
                    showToast(error.message, true);
                }
            }
        });
    };

    window[saveViewFunctionName] = function saveObjectListViewLayout() {
        const activeView = getActiveView();
        if (!activeView.editable) {
            if (typeof showToast === "function") {
                showToast("Clone this built-in view to create your own version.", true);
            }
            return;
        }

        requestLeadListView(`${objectApiPath}/${activeView.id}`, "PUT", buildPayload()).then((data) => {
            replaceView(data.view);
            state.activeViewId = data.view.id;
            renderView();
            if (typeof showToast === "function") {
                showToast(`Updated ${data.view.label}.`);
            }
        }).catch((error) => {
            if (typeof showToast === "function") {
                showToast(error.message, true);
            }
        });
    };

    window[cloneViewFunctionName] = function cloneObjectListView() {
        const activeView = getActiveView();
        const label = `${activeView.label} Copy`;
        confirmLeadListAction("Clone list view", `Create a copy of ${activeView.label}?`, async () => {
            try {
                const data = await requestLeadListView(objectApiPath, "POST", buildPayload(label));
                replaceView(data.view);
                state.activeViewId = data.view.id;
                renderView();
                if (typeof showToast === "function") {
                    showToast(`Cloned ${activeView.label}.`);
                }
            } catch (error) {
                if (typeof showToast === "function") {
                    showToast(error.message, true);
                }
            }
        });
    };

    window[deleteViewFunctionName] = function deleteObjectListView() {
        const activeView = getActiveView();
        if (!activeView.editable) {
            if (typeof showToast === "function") {
                showToast("Built-in views cannot be deleted.", true);
            }
            return;
        }

        confirmLeadListAction("Delete list view", `Delete ${activeView.label}?`, async () => {
            try {
                await requestLeadListView(`${objectApiPath}/${activeView.id}`, "DELETE");
                state.savedViews = state.savedViews.filter((view) => view.id !== activeView.id);
                state.activeViewId = "all";
                renderView();
                if (typeof showToast === "function") {
                    showToast(`Deleted ${activeView.label}.`);
                }
            } catch (error) {
                if (typeof showToast === "function") {
                    showToast(error.message, true);
                }
            }
        });
    };

    window[resetViewFunctionName] = function resetObjectListViewLayout() {
        syncSetupForm();
    };

    state.activeViewId = getViewById(state.activeViewId).id;
    bindColumnDragAndDrop();
    renderView();
}

function initializeLeadListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Lead",
        objectApiPath: "/leads/views",
        recentSummaryText: "Showing your recently opened leads",
        applyViewFunctionName: "applyLeadListView",
        refreshViewFunctionName: "refreshLeadListView",
        filterViewFunctionName: "filterLeadListView",
        addFilterFunctionName: "addLeadListViewFilterCondition",
        removeFilterFunctionName: "removeLeadListViewFilterCondition",
        togglePinFunctionName: "toggleLeadListViewPin",
        saveNewViewFunctionName: "saveNewLeadListView",
        saveViewFunctionName: "saveLeadListViewLayout",
        cloneViewFunctionName: "cloneLeadListView",
        deleteViewFunctionName: "deleteLeadListView",
        resetViewFunctionName: "resetLeadListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "email", label: "Email" },
            { value: "phone", label: "Phone" },
            { value: "model", label: "Model" },
            { value: "status", label: "Status" },
            { value: "created", label: "Created" },
        ],
        defaultFilterCondition: { field: "status", operator: "equals", value: "New" },
        ...config,
    });
}

function initializeContactListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Contact",
        objectApiPath: "/contacts/views",
        recentSummaryText: "Showing your recently opened contacts",
        applyViewFunctionName: "applyContactListView",
        refreshViewFunctionName: "refreshContactListView",
        filterViewFunctionName: "filterContactListView",
        addFilterFunctionName: "addContactListViewFilterCondition",
        removeFilterFunctionName: "removeContactListViewFilterCondition",
        togglePinFunctionName: "toggleContactListViewPin",
        saveNewViewFunctionName: "saveNewContactListView",
        saveViewFunctionName: "saveContactListViewLayout",
        cloneViewFunctionName: "cloneContactListView",
        deleteViewFunctionName: "deleteContactListView",
        resetViewFunctionName: "resetContactListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "email", label: "Email" },
            { value: "phone", label: "Phone" },
            { value: "tier", label: "Tier" },
            { value: "created", label: "Created" },
        ],
        defaultFilterCondition: { field: "tier", operator: "contains", value: "" },
        ...config,
    });
}

function initializeOpportunityListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Opportunity",
        objectApiPath: "/opportunities/views",
        recentSummaryText: "Showing your recently opened opportunities",
        applyViewFunctionName: "applyOpportunityListView",
        refreshViewFunctionName: "refreshOpportunityListView",
        filterViewFunctionName: "filterOpportunityListView",
        addFilterFunctionName: "addOpportunityListViewFilterCondition",
        removeFilterFunctionName: "removeOpportunityListViewFilterCondition",
        togglePinFunctionName: "toggleOpportunityListViewPin",
        saveNewViewFunctionName: "saveNewOpportunityListView",
        saveViewFunctionName: "saveOpportunityListViewLayout",
        cloneViewFunctionName: "cloneOpportunityListView",
        deleteViewFunctionName: "deleteOpportunityListView",
        resetViewFunctionName: "resetOpportunityListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "amount", label: "Amount" },
            { value: "stage", label: "Stage" },
            { value: "model", label: "Model" },
            { value: "created", label: "Created" },
        ],
        defaultFilterCondition: { field: "stage", operator: "contains", value: "Prospecting" },
        ...config,
    });
}

function initializeProductListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Product",
        objectApiPath: "/products/views",
        recentSummaryText: "Showing your recently opened products",
        applyViewFunctionName: "applyProductListView",
        refreshViewFunctionName: "refreshProductListView",
        filterViewFunctionName: "filterProductListView",
        addFilterFunctionName: "addProductListViewFilterCondition",
        removeFilterFunctionName: "removeProductListViewFilterCondition",
        togglePinFunctionName: "toggleProductListViewPin",
        saveNewViewFunctionName: "saveNewProductListView",
        saveViewFunctionName: "saveProductListViewLayout",
        cloneViewFunctionName: "cloneProductListView",
        deleteViewFunctionName: "deleteProductListView",
        resetViewFunctionName: "resetProductListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "brand", label: "Brand" },
            { value: "model", label: "Model" },
            { value: "base_price", label: "Base Price" },
            { value: "category", label: "Category" },
        ],
        defaultFilterCondition: { field: "category", operator: "contains", value: "" },
        ...config,
    });
}

function initializeAssetListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Asset",
        objectApiPath: "/assets/views",
        recentSummaryText: "Showing your recently opened assets",
        applyViewFunctionName: "applyAssetListView",
        refreshViewFunctionName: "refreshAssetListView",
        filterViewFunctionName: "filterAssetListView",
        addFilterFunctionName: "addAssetListViewFilterCondition",
        removeFilterFunctionName: "removeAssetListViewFilterCondition",
        togglePinFunctionName: "toggleAssetListViewPin",
        saveNewViewFunctionName: "saveNewAssetListView",
        saveViewFunctionName: "saveAssetListViewLayout",
        cloneViewFunctionName: "cloneAssetListView",
        deleteViewFunctionName: "deleteAssetListView",
        resetViewFunctionName: "resetAssetListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "vin", label: "Vin" },
            { value: "price", label: "Price" },
            { value: "status", label: "Status" },
        ],
        defaultFilterCondition: { field: "status", operator: "contains", value: "Active" },
        ...config,
    });
}

function initializeBrandListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Brand",
        objectApiPath: "/vehicle_specifications/views",
        recentSummaryText: "Showing your recently opened brands",
        applyViewFunctionName: "applyBrandListView",
        refreshViewFunctionName: "refreshBrandListView",
        filterViewFunctionName: "filterBrandListView",
        addFilterFunctionName: "addBrandListViewFilterCondition",
        removeFilterFunctionName: "removeBrandListViewFilterCondition",
        togglePinFunctionName: "toggleBrandListViewPin",
        saveNewViewFunctionName: "saveNewBrandListView",
        saveViewFunctionName: "saveBrandListViewLayout",
        cloneViewFunctionName: "cloneBrandListView",
        deleteViewFunctionName: "deleteBrandListView",
        resetViewFunctionName: "resetBrandListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "type", label: "Type" },
            { value: "description", label: "Description" },
        ],
        defaultFilterCondition: { field: "type", operator: "contains", value: "Brand" },
        ...config,
    });
}

function initializeModelListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Model",
        objectApiPath: "/models/views",
        recentSummaryText: "Showing your recently opened models",
        applyViewFunctionName: "applyModelListView",
        refreshViewFunctionName: "refreshModelListView",
        filterViewFunctionName: "filterModelListView",
        addFilterFunctionName: "addModelListViewFilterCondition",
        removeFilterFunctionName: "removeModelListViewFilterCondition",
        togglePinFunctionName: "toggleModelListViewPin",
        saveNewViewFunctionName: "saveNewModelListView",
        saveViewFunctionName: "saveModelListViewLayout",
        cloneViewFunctionName: "cloneModelListView",
        deleteViewFunctionName: "deleteModelListView",
        resetViewFunctionName: "resetModelListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "brand", label: "Brand" },
            { value: "description", label: "Description" },
        ],
        defaultFilterCondition: { field: "brand", operator: "contains", value: "" },
        ...config,
    });
}

function initializeMessageListView(config) {
    return initializeObjectListView({
        objectDisplayName: "Message",
        objectApiPath: "/messages/views",
        recentSummaryText: "Showing your recently opened messages",
        applyViewFunctionName: "applyMessageListView",
        refreshViewFunctionName: "refreshMessageListView",
        filterViewFunctionName: "filterMessageListView",
        addFilterFunctionName: "addMessageListViewFilterCondition",
        removeFilterFunctionName: "removeMessageListViewFilterCondition",
        togglePinFunctionName: "toggleMessageListViewPin",
        saveNewViewFunctionName: "saveNewMessageListView",
        saveViewFunctionName: "saveMessageListViewLayout",
        cloneViewFunctionName: "cloneMessageListView",
        deleteViewFunctionName: "deleteMessageListView",
        resetViewFunctionName: "resetMessageListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "direction", label: "Direction" },
            { value: "status", label: "Status" },
            { value: "created_at", label: "Created At" },
        ],
        defaultFilterCondition: { field: "status", operator: "contains", value: "Sent" },
        ...config,
    });
}

function initializeMessageTemplateListView(config) {
    return initializeObjectListView({
        objectDisplayName: "MessageTemplate",
        objectApiPath: "/message_templates/views",
        recentSummaryText: "Showing your recently opened templates",
        applyViewFunctionName: "applyMessageTemplateListView",
        refreshViewFunctionName: "refreshMessageTemplateListView",
        filterViewFunctionName: "filterMessageTemplateListView",
        addFilterFunctionName: "addMessageTemplateListViewFilterCondition",
        removeFilterFunctionName: "removeMessageTemplateListViewFilterCondition",
        togglePinFunctionName: "toggleMessageTemplateListViewPin",
        saveNewViewFunctionName: "saveNewMessageTemplateListView",
        saveViewFunctionName: "saveMessageTemplateListViewLayout",
        cloneViewFunctionName: "cloneMessageTemplateListView",
        deleteViewFunctionName: "deleteMessageTemplateListView",
        resetViewFunctionName: "resetMessageTemplateListViewLayout",
        fieldOptions: [
            { value: "name", label: "Name" },
            { value: "subject", label: "Subject" },
            { value: "content", label: "Content" },
            { value: "type", label: "Type" },
        ],
        defaultFilterCondition: { field: "type", operator: "contains", value: "SMS" },
        ...config,
    });
}
