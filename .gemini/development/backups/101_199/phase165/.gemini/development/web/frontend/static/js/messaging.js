/**
 * Messaging Module - Atomized Functions for GK CRM
 */

window.Messaging = (function() {
    // Private State
    let aiRecommendActive = false;
    let cachedDefaultRecipients = null;
    let currentEditTemplateId = null;

    // --- RECIPIENT MANAGEMENT ---
    const RecipientManager = {
        async toggleAIRecommendations() {
            const btn = document.getElementById('ai-recommend-toggle');
            aiRecommendActive = !aiRecommendActive;

            if (aiRecommendActive) {
                btn.style.background = 'var(--nav-blue)';
                btn.style.color = 'white';
                await this.loadAIRecommendations();
            } else {
                btn.style.background = 'white';
                btn.style.color = 'var(--nav-blue)';
                await this.loadDefaultRecipients();
            }
        },

        async loadAIRecommendations() {
            try {
                const response = await fetch('/messaging/recommendations');
                if (response.ok) {
                    const data = await response.json();
                    this.updateTable(data);
                    showToast(`Found ${data.length} recommended deals.`);
                } else {
                    showToast("Failed to fetch recommendations.", true);
                    aiRecommendActive = false;
                    this.resetToggleBtn();
                }
            } catch (error) {
                console.error("AI Recommend error:", error);
                showToast("An error occurred.", true);
            }
        },

        async loadDefaultRecipients() {
            if (cachedDefaultRecipients) {
                this.updateTable(cachedDefaultRecipients);
                return;
            }

            showToast("Loading all recipients...");
            try {
                const response = await fetch('/messaging/default_recipients');
                if (response.ok) {
                    const data = await response.json();
                    cachedDefaultRecipients = data;
                    this.updateTable(data);
                } else {
                    showToast("Failed to load recipients.", true);
                }
            } catch (error) {
                console.error("Load recipients error:", error);
            }
        },

        updateTable(data) {
            const tbody = document.getElementById('recipient-body');
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-label); padding: 2rem;">No records found.</td></tr>';
                return;
            }

            data.forEach(item => {
                const row = document.createElement('tr');
                row.className = 'recipient-row';
                row.innerHTML = `
                    <td style="text-align: center;"><input type="checkbox" name="selected_recipients" value="${item.contact_id}" data-opp-id="${item.id}" data-name="${item.contact.name}"></td>
                    <td class="search-field">${item.contact.name} (Deal: ${item.name})</td>
                    <td id="status-${item.id}" class="status-cell" style="font-size: 0.75rem; color: #1abc9c; font-weight: 600;"></td>
                    <td class="search-field">${item.contact.phone}</td>
                    <td class="search-field">${item.stage}</td>
                    <td class="search-field">${item.model ? item.model.name : '-'}</td>
                `;
                tbody.appendChild(row);
            });
            
            document.getElementById('select-all').checked = false;
        },

        filter() {
            const query = document.getElementById('recipient-search').value.toLowerCase();
            const rows = document.querySelectorAll('.recipient-row');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        },

        toggleSelectAll(checkbox) {
            const visibleCheckboxes = document.querySelectorAll('.recipient-row[style=""] input[name="selected_recipients"], .recipient-row:not([style]) input[name="selected_recipients"]');
            visibleCheckboxes.forEach(cb => cb.checked = checkbox.checked);
        },

        resetToggleBtn() {
            const btn = document.getElementById('ai-recommend-toggle');
            btn.style.background = 'white';
            btn.style.color = 'var(--nav-blue)';
        },

        getSelected() {
            return Array.from(document.querySelectorAll('input[name="selected_recipients"]:checked'))
                .map(cb => ({ id: cb.value, name: cb.getAttribute('data-name') }));
        }
    };

    // --- TEMPLATE MANAGEMENT ---
    const TemplateManager = {
        apply(templateId) {
            const select = document.getElementById('template-select');
            const option = select.options[select.selectedIndex];
            const content = option.getAttribute('data-content');
            const type = option.getAttribute('data-type');
            const filePath = option.getAttribute('data-file');
            const attId = option.getAttribute('data-att-id');
            const attName = option.getAttribute('data-att-name');
            const attSize = option.getAttribute('data-att-size');
            
            const editBtn = document.getElementById('edit-template-btn');
            const deleteBtn = document.getElementById('delete-template-btn');
            
            if (content) {
                document.getElementById('message-content').value = content;
                editBtn.style.display = 'inline-block';
                deleteBtn.style.display = 'inline-block';
                
                if (type) {
                    const radio = document.querySelector(`input[name="msg_type"][value="${type}"]`);
                    if (radio) {
                        radio.checked = true;
                        UIManager.updateCharLimit();
                    }
                }
                
                if (type === 'MMS' && filePath) {
                    UIManager.showImagePreview(filePath, attId, attName, attSize);
                } else {
                    this.removeImage();
                }
                
                UIManager.updatePreview();
            } else {
                editBtn.style.display = 'none';
                deleteBtn.style.display = 'none';
                this.removeImage();
                UIManager.updatePreview();
            }
        },

        openModal(isEdit) {
            const modal = document.getElementById('template-modal');
            const title = document.getElementById('modal-title');
            const nameInput = document.getElementById('modal-tpl-name');
            const contentInput = document.getElementById('modal-tpl-content');
            const typeSelect = document.getElementById('modal-tpl-type');
            
            const filePathInput = document.getElementById('modal-tpl-file-path');
            const attachmentIdInput = document.getElementById('modal-tpl-attachment-id');
            const previewContainer = document.getElementById('modal-image-preview-container');
            const previewImg = document.getElementById('modal-tpl-preview');
            const fileNameDiv = document.getElementById('modal-tpl-file-name');
            const fileInfoDiv = document.getElementById('modal-tpl-file-info');
            
            if (isEdit) {
                const select = document.getElementById('template-select');
                const option = select.options[select.selectedIndex];
                if (!option.value) return;
                currentEditTemplateId = option.value;
                title.innerText = "Edit Template";
                nameInput.value = option.getAttribute('data-name');
                contentInput.value = option.getAttribute('data-content');
                const type = option.getAttribute('data-type') || "SMS";
                typeSelect.value = type;
                
                const filePath = option.getAttribute('data-file');
                const attId = option.getAttribute('data-att-id');
                const attName = option.getAttribute('data-att-name');
                const attSize = option.getAttribute('data-att-size');

                if (filePath) {
                    filePathInput.value = filePath;
                    attachmentIdInput.value = attId || '';
                    previewImg.src = filePath;
                    fileNameDiv.innerText = attName || 'Attachment';
                    fileInfoDiv.innerText = attSize ? `${(parseInt(attSize)/1024).toFixed(1)} KB` : '';
                    previewContainer.style.display = 'block';
                } else {
                    this.clearModalFile();
                }
                this.toggleModalFileUpload(type);
            } else {
                currentEditTemplateId = null;
                title.innerText = "Create New Template";
                nameInput.value = "";
                contentInput.value = "";
                typeSelect.value = "SMS";
                this.clearModalFile();
                this.toggleModalFileUpload("SMS");
            }
            modal.style.display = 'flex';
        },

        closeModal() {
            document.getElementById('template-modal').style.display = 'none';
        },

        toggleModalFileUpload(type) {
            const fileArea = document.getElementById('modal-file-area');
            fileArea.style.display = (type === 'MMS') ? 'block' : 'none';
        },

        clearModalFile() {
            document.getElementById('modal-tpl-file-path').value = "";
            document.getElementById('modal-tpl-attachment-id').value = "";
            document.getElementById('modal-image-preview-container').style.display = 'none';
        },

        async handleModalUpload(input) {
            const file = input.files[0];
            if (!file) return;
            if (!file.type.startsWith('image/')) {
                showToast("Only image files are allowed.", true);
                input.value = '';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/messaging/templates/upload', { method: 'POST', body: formData });
                if (response.ok) {
                    const result = await response.json();
                    document.getElementById('modal-tpl-file-path').value = result.file_path;
                    document.getElementById('modal-tpl-attachment-id').value = result.attachment_id;
                    document.getElementById('modal-tpl-preview').src = result.file_path;
                    document.getElementById('modal-tpl-file-name').innerText = result.name;
                    document.getElementById('modal-tpl-file-info').innerText = `${(result.size / 1024).toFixed(1)} KB`;
                    document.getElementById('modal-image-preview-container').style.display = 'block';
                    showToast("File uploaded successfully.");
                } else {
                    showToast("Failed to upload file.", true);
                }
            } catch (error) {
                console.error("File upload error:", error);
                showToast("An error occurred during upload.", true);
            }
        },

        async save() {
            const name = document.getElementById('modal-tpl-name').value;
            const content = document.getElementById('modal-tpl-content').value;
            const record_type = document.getElementById('modal-tpl-type').value;
            const file_path = document.getElementById('modal-tpl-file-path').value;
            const attachment_id = document.getElementById('modal-tpl-attachment-id').value;

            if (!name || !content) {
                showToast("Please fill in name and content.", true);
                return;
            }
            if (record_type === 'MMS' && !file_path) {
                showToast("MMS template requires an attachment.", true);
                return;
            }

            const payload = { name, content, record_type, file_path, attachment_id };
            if (currentEditTemplateId) payload.id = currentEditTemplateId;

            try {
                const response = await fetch('/messaging/templates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    sessionStorage.setItem('toastMessage', "Template saved successfully!");
                    location.reload(); 
                } else {
                    const errorData = await response.json();
                    let errorMsg = "Failed to save template.";
                    if (errorData.detail) {
                        errorMsg = Array.isArray(errorData.detail) 
                            ? errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ') 
                            : errorData.detail;
                    }
                    showToast(errorMsg, true);
                }
            } catch (error) {
                console.error("Save Template error:", error);
                showToast("An error occurred.", true);
            }
        },

        async delete() {
            const select = document.getElementById('template-select');
            const templateId = select.value;
            const option = select.options[select.selectedIndex];
            const name = option ? option.getAttribute('data-name') : '';

            if (!templateId) return;

            showConfirmModal(`Delete Template`, `Are you sure you want to delete the template "${name}"?`, async () => {
                await this.executeDelete(templateId);
            });
        },

        async executeDelete(templateId) {
            try {
                const response = await fetch(`/messaging/templates/${templateId}`, { method: 'DELETE' });
                if (response.ok) {
                    sessionStorage.setItem('toastMessage', "Template deleted successfully!");
                    location.reload();
                } else {
                    showToast("Failed to delete template.", true);
                }
            } catch (error) {
                console.error("Delete Template error:", error);
                showToast("An error occurred.", true);
            }
        },

        removeImage() {
            document.getElementById('mms-image').value = '';
            document.getElementById('mms-preview-img').src = '';
            document.getElementById('compose-attachment-id').value = '';
            document.getElementById('image-preview-container').style.display = 'none';
            document.getElementById('preview-mms-img-card').style.display = 'none';
            UIManager.updatePreview();
        }
    };

    // --- UI & PREVIEW ---
    const UIManager = {
        updateCharLimit() {
            const type = document.querySelector('input[name="msg_type"]:checked').value;
            const limitSpan = document.getElementById('char-limit');
            const mmsArea = document.getElementById('mms-attachment-area');
            const mmsInfo = document.getElementById('mms-info');
            
            if (type === 'SMS') {
                limitSpan.innerText = '90';
                mmsArea.style.display = 'none';
                mmsInfo.style.display = 'none';
            } else {
                limitSpan.innerText = '2,000';
                if (type === 'MMS') {
                    mmsArea.style.display = 'block';
                    mmsInfo.style.display = 'inline';
                } else {
                    mmsArea.style.display = 'none';
                    mmsInfo.style.display = 'none';
                }
            }
            this.updatePreview();
        },

        updatePreview() {
            const content = document.getElementById('message-content').value;
            const bubble = document.getElementById('preview-bubble');
            const charCount = document.getElementById('char-count');
            const container = document.getElementById('preview-msg-container');
            const type = document.querySelector('input[name="msg_type"]:checked').value;
            const mmsCard = document.getElementById('preview-mms-img-card');
            const limit = type === 'SMS' ? 90 : 2000;
            
            if (type !== 'MMS') {
                mmsCard.style.display = 'none';
            } else if (document.getElementById('mms-image').files.length > 0 || document.getElementById('mms-preview-img').src) {
                const src = document.getElementById('mms-preview-img').src;
                if (src && !src.endsWith('ui')) {
                     mmsCard.style.display = 'block';
                }
            }

            const size = new Blob([content]).size;
            charCount.innerText = size;
            
            if (type === 'SMS' && size > 90) {
                const lmsRadio = document.querySelector('input[name="msg_type"][value="LMS"]');
                if (lmsRadio) {
                    lmsRadio.checked = true;
                    this.updateCharLimit();
                    return;
                }
            }

            charCount.style.color = size > limit ? '#e74c3c' : '';
            charCount.style.fontWeight = size > limit ? 'bold' : '';

            if (content || mmsCard.style.display !== 'none') {
                container.style.display = 'flex';
                
                if (content) {
                    bubble.innerText = content;
                    bubble.style.display = 'block';
                    bubble.style.borderRadius = '18px';
                    document.getElementById('preview-mms-display').style.borderRadius = '12px';
                } else {
                    // Image only
                    bubble.style.display = 'none';
                    document.getElementById('preview-mms-display').style.borderRadius = '15px';
                }
            } else {
                container.style.display = 'none';
            }
        },

        showImagePreview(filePath, attId, attName, attSize) {
            document.getElementById('image-preview-container').style.display = 'block';
            document.getElementById('mms-preview-img').src = filePath;
            document.getElementById('compose-attachment-id').value = attId || '';
            
            let info = attName || "Template Attachment";
            if (attSize) info += ` (${(parseInt(attSize) / 1024).toFixed(1)} KB)`;
            document.getElementById('image-name').innerText = info;
            
            document.getElementById('preview-mms-display').src = filePath;
            document.getElementById('preview-mms-img-card').style.display = 'block';
        },

        clearAll() {
            document.getElementById('message-content').value = '';
            document.getElementById('template-select').value = '';
            document.getElementById('edit-template-btn').style.display = 'none';
            document.getElementById('delete-template-btn').style.display = 'none';
            TemplateManager.removeImage();
            this.updatePreview();
        }
    };

    // --- MESSAGE SENDING ---
    const MessageSender = {
        async handleUpload(input) {
            const file = input.files[0];
            if (!file) return;
            if (!file.type.startsWith('image/')) {
                showToast("Only image files are allowed.", true);
                input.value = '';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/messaging/templates/upload', { method: 'POST', body: formData });
                if (response.ok) {
                    const result = await response.json();
                    UIManager.showImagePreview(result.file_path, result.attachment_id, result.name, result.size);
                    UIManager.updatePreview();
                    showToast("File uploaded successfully.");
                } else {
                    showToast("Failed to upload file.", true);
                }
            } catch (error) {
                console.error("File upload error:", error);
                showToast("An error occurred during upload.", true);
            }
        },

        validate(content, type, recipients) {
            if (recipients.length === 0) {
                showToast("Please select at least one recipient.", true);
                return false;
            }
            const limit = type === 'SMS' ? 90 : 2000;
            if (new Blob([content]).size > limit) {
                showToast(`Message exceeds the ${type} limit.`, true);
                return false;
            }
            if (type === 'MMS') {
                const previewImg = document.getElementById('preview-mms-display');
                const isHidden = document.getElementById('preview-mms-img-card').style.display === 'none';
                if (!previewImg.src || isHidden || previewImg.src.endsWith('ui')) {
                    showToast("MMS requires a PNG attachment.", true);
                    return false;
                }
            }
            return true;
        },

        async send() {
            const recipients = RecipientManager.getSelected();
            const content = document.getElementById('message-content').value;
            const type = document.querySelector('input[name="msg_type"]:checked').value;
            const templateId = document.getElementById('template-select').value;
            const attachmentId = document.getElementById('compose-attachment-id').value;

            if (!this.validate(content, type, recipients)) return;

            showToast(`Sending ${type} to ${recipients.length} recipients...`);
            
            try {
                const response = await fetch('/messaging/bulk-send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contact_ids: recipients.map(r => r.id),
                        template_id: templateId || null,
                        content: content,
                        record_type: type,
                        attachment_id: attachmentId || null
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    this.showSummary(recipients, type);
                    showToast(`Shipment has been completed.`);
                } else {
                    const error = await response.json();
                    showToast(error.message || "Failed to send messages.", true);
                }
            } catch (error) {
                console.error("Send Message error:", error);
                showToast("An error occurred while sending.", true);
            }
        },

        showSummary(recipients, type) {
            const summaryBody = document.getElementById('summary-table-body');
            summaryBody.innerHTML = '';
            const now = new Date().toLocaleString();
            
            recipients.forEach(r => {
                summaryBody.innerHTML += `
                    <tr>
                        <td><strong>${r.name}</strong></td>
                        <td><span class="badge" style="background: #f0f7ff; color: #0176d3;">${type}</span></td>
                        <td><span style="color: #2ecc71;">Sent</span></td>
                        <td style="font-size: 0.8rem; color: var(--text-label);">${now}</td>
                    </tr>
                `;
            });

            document.getElementById('messaging-main-view').style.display = 'none';
            document.getElementById('messaging-summary-view').style.display = 'flex';
        }
    };

    // Public API
    return {
        recipients: RecipientManager,
        templates: TemplateManager,
        ui: UIManager,
        sender: MessageSender,
        init() {
            const msg = sessionStorage.getItem('toastMessage');
            if (msg) {
                showToast(msg);
                sessionStorage.removeItem('toastMessage');
            }
        }
    };
})();

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => Messaging.init());
