function toggleAllCheckboxes(source) {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = source.checked;
    });
    updateDeleteButtonState();
}

function updateDeleteButtonState() {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    const deleteBtn = document.getElementById('bulk-delete-btn');
    if (deleteBtn) {
        if (checkboxes.length > 0) {
            deleteBtn.style.display = 'inline-block';
            deleteBtn.innerText = `Delete (${checkboxes.length})`;
        } else {
            deleteBtn.style.display = 'none';
        }
    }
}

function confirmBulkDelete(objectType) {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);
    
    if (ids.length === 0) return;

    const title = `Delete ${objectType}s`;
    const message = `Are you sure you want to delete ${ids.length} ${objectType.toLowerCase()}(s)?`;

    showConfirmModal(title, message, () => {
        executeBulkDelete(ids, objectType);
    });
}

function executeBulkDelete(ids, objectType) {
    fetch('/bulk/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            ids: ids,
            object_type: objectType
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            if (typeof showToast === 'function') {
                showToast(data.message || `Deleted ${ids.length} items.`, false);
                setTimeout(() => window.location.reload(), 1500);
            } else {
                window.location.reload();
            }
        } else {
            if (typeof showToast === 'function') {
                showToast(data.message || "Bulk delete failed.", true);
            } else {
                alert("Bulk delete failed: " + data.message);
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (typeof showToast === 'function') {
            showToast("An error occurred during bulk delete.", true);
        } else {
            alert("An error occurred during bulk delete.");
        }
    });
}

