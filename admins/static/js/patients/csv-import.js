/**
 * CSV Import Wizard Controller
 */

class CSVImportWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.fileUrl = null;
        this.fileName = null;
        this.columns = [];
        this.columnMapping = {};
        this.previewData = null;
        this.duplicates = [];
        this.duplicateActions = {};

        this.init();
    }

    init() {
        this.setupDropzone();
        this.setupNavigation();
        this.setupImportButton();
    }

    // ==================== Dropzone ====================

    setupDropzone() {
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('fileInput');

        if (!dropzone || !fileInput) return;

        // Click to browse
        dropzone.addEventListener('click', () => fileInput.click());

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadFile(e.target.files[0]);
            }
        });

        // Drag and drop
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');

            if (e.dataTransfer.files.length > 0) {
                this.uploadFile(e.dataTransfer.files[0]);
            }
        });
    }

    async uploadFile(file) {
        // Validate file type
        const validTypes = ['text/csv', 'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        const validExtensions = ['.csv', '.xlsx', '.xls'];

        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(ext)) {
            this.showToast('Invalid file type. Please upload CSV or Excel files.', 'error');
            return;
        }

        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            this.showToast('File too large. Maximum size is 10MB.', 'error');
            return;
        }

        this.fileName = file.name;

        // Show progress
        const dropzone = document.getElementById('dropzone');
        const progressContainer = document.querySelector('.upload-progress');
        const progressBar = document.getElementById('uploadProgressBar');
        const percentText = document.getElementById('uploadPercent');
        const fileNameText = document.getElementById('uploadFileName');

        dropzone.classList.add('uploading');
        progressContainer.style.display = 'block';
        fileNameText.textContent = file.name;

        try {
            // Create FormData
            const formData = new FormData();
            formData.append('file', file);

            // Upload with progress
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                    percentText.textContent = percent + '%';
                }
            });

            xhr.onload = () => {
                if (xhr.status === 200 || xhr.status === 201) {
                    const response = JSON.parse(xhr.responseText);
                    this.fileUrl = response.url || response.file_url || response.path;

                    // Show success
                    progressContainer.style.display = 'none';
                    document.querySelector('.file-info').style.display = 'block';
                    document.getElementById('uploadedFileName').textContent = file.name;
                    document.getElementById('uploadedFileSize').textContent = this.formatFileSize(file.size);

                    // Enable next button
                    document.getElementById('nextBtn').disabled = false;

                    this.showToast('File uploaded successfully!', 'success');
                } else {
                    throw new Error('Upload failed');
                }
            };

            xhr.onerror = () => {
                throw new Error('Upload failed');
            };

            xhr.open('POST', '/api/v1/media/upload-stream');
            xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
            xhr.send(formData);

        } catch (error) {
            console.error('Upload error:', error);
            dropzone.classList.remove('uploading');
            progressContainer.style.display = 'none';
            this.showToast('Failed to upload file: ' + error.message, 'error');
        }
    }

    // ==================== Navigation ====================

    setupNavigation() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        prevBtn.addEventListener('click', () => this.prevStep());
        nextBtn.addEventListener('click', () => this.nextStep());
    }

    async nextStep() {
        if (this.currentStep >= this.totalSteps) return;

        // Validate current step before proceeding
        if (this.currentStep === 1 && !this.fileUrl) {
            this.showToast('Please upload a file first', 'warning');
            return;
        }

        if (this.currentStep === 1) {
            // Load column mapping from file
            await this.loadPreview();
        }

        if (this.currentStep === 2) {
            // Validate column mapping
            if (!this.validateMapping()) {
                return;
            }
            // Refresh preview with mapping
            await this.loadPreviewWithMapping();
        }

        this.currentStep++;
        this.updateUI();
    }

    prevStep() {
        if (this.currentStep <= 1) return;
        this.currentStep--;
        this.updateUI();
    }

    updateUI() {
        // Update step indicators
        document.querySelectorAll('.wizard-step').forEach((step, idx) => {
            const stepNum = idx + 1;
            step.classList.remove('active', 'completed');

            if (stepNum < this.currentStep) {
                step.classList.add('completed');
            } else if (stepNum === this.currentStep) {
                step.classList.add('active');
            }
        });

        // Update connectors
        document.querySelectorAll('.wizard-connector').forEach((conn, idx) => {
            if (idx + 1 < this.currentStep) {
                conn.classList.add('completed');
            } else {
                conn.classList.remove('completed');
            }
        });

        // Show current pane
        document.querySelectorAll('.wizard-pane').forEach((pane, idx) => {
            pane.classList.remove('active');
            if (idx + 1 === this.currentStep) {
                pane.classList.add('active');
            }
        });

        // Update navigation buttons
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        prevBtn.style.display = this.currentStep > 1 ? 'inline-block' : 'none';

        if (this.currentStep === this.totalSteps) {
            nextBtn.style.display = 'none';
        } else {
            nextBtn.style.display = 'inline-block';
            nextBtn.disabled = false;
        }
    }

    // ==================== Column Mapping ====================

    async loadPreview() {
        try {
            const response = await fetch('/api/v1/patient/import/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    file_url: this.fileUrl
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to load preview');
            }

            this.previewData = await response.json();
            this.columns = this.previewData.columns || [];
            this.columnMapping = this.previewData.final_mapping || {};

            this.renderColumnMapping();
            this.renderSampleData();

        } catch (error) {
            console.error('Preview error:', error);
            this.showToast('Failed to load file preview: ' + error.message, 'error');
        }
    }

    renderColumnMapping() {
        const container = document.getElementById('columnMappingContainer');
        const patientFields = [
            { key: 'firstName', label: 'First Name', required: true },
            { key: 'lastName', label: 'Last Name', required: false },
            { key: 'dateOfBirth', label: 'Date of Birth', required: false },
            { key: 'gender', label: 'Gender', required: false },
            { key: 'notes', label: 'Notes', required: false }
        ];

        let html = '';

        patientFields.forEach(field => {
            const selectedColumn = this.columnMapping[field.key] || '';

            html += `
        <div class="col-md-6 mb-3">
          <div class="mapping-row">
            <div class="mapping-field">
              <label>
                ${field.label}
                ${field.required ? '<span class="required">*</span>' : ''}
              </label>
            </div>
            <i class="bi bi-arrow-right mapping-arrow"></i>
            <div class="mapping-select">
              <select class="form-select form-select-sm" data-field="${field.key}">
                <option value="">-- Select Column --</option>
                ${this.columns.map(col => `
                  <option value="${col}" ${col === selectedColumn ? 'selected' : ''}>
                    ${col}
                  </option>
                `).join('')}
              </select>
            </div>
          </div>
        </div>
      `;
        });

        container.innerHTML = html;

        // Add change listeners
        container.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', (e) => {
                const field = e.target.dataset.field;
                const value = e.target.value;
                if (value) {
                    this.columnMapping[field] = value;
                } else {
                    delete this.columnMapping[field];
                }
            });
        });
    }

    renderSampleData() {
        if (!this.previewData || !this.previewData.preview_rows) return;

        const thead = document.getElementById('sampleDataHead');
        const tbody = document.getElementById('sampleDataBody');

        // Header
        let headerHtml = '<tr>';
        this.columns.forEach(col => {
            headerHtml += `<th>${col}</th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

        // Body (first 3 rows)
        let bodyHtml = '';
        this.previewData.preview_rows.slice(0, 3).forEach(row => {
            bodyHtml += '<tr>';
            this.columns.forEach(col => {
                bodyHtml += `<td>${row[col] || ''}</td>`;
            });
            bodyHtml += '</tr>';
        });
        tbody.innerHTML = bodyHtml;
    }

    validateMapping() {
        // Need at least firstName or lastName mapped
        if (!this.columnMapping.firstName && !this.columnMapping.lastName) {
            this.showToast('Please map at least First Name or Last Name', 'warning');
            return false;
        }
        return true;
    }

    // ==================== Preview ====================

    async loadPreviewWithMapping() {
        try {
            const response = await fetch('/api/v1/patient/import/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    file_url: this.fileUrl,
                    column_mapping: this.columnMapping
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to load preview');
            }

            this.previewData = await response.json();
            this.duplicates = this.previewData.duplicates || [];

            this.renderPreviewStats();
            this.renderDuplicates();
            this.renderPreviewTable();

        } catch (error) {
            console.error('Preview error:', error);
            this.showToast('Failed to load preview: ' + error.message, 'error');
        }
    }

    renderPreviewStats() {
        const stats = this.previewData.stats || {};

        document.getElementById('statTotal').textContent = stats.total || 0;
        document.getElementById('statNew').textContent = stats.new || 0;
        document.getElementById('statDuplicates').textContent = stats.duplicates || 0;
        document.getElementById('statErrors').textContent = stats.errors || 0;
    }

    renderDuplicates() {
        const container = document.getElementById('duplicatesList');
        const section = document.getElementById('duplicatesSection');

        if (this.duplicates.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        let html = '';
        this.duplicates.forEach(dup => {
            const confidence = Math.round(dup.match_confidence * 100);

            html += `
        <div class="duplicate-item">
          <div class="duplicate-info">
            <span class="duplicate-row-num">Row ${dup.row_index + 1}</span>
            <span class="duplicate-match">
              Matches: <strong>${dup.match_name}</strong>
              <span class="duplicate-confidence">(${confidence}% match)</span>
            </span>
          </div>
          <div class="duplicate-action">
            <select class="form-select form-select-sm" data-row="${dup.row_index}">
              <option value="skip" selected>Skip (Don't import)</option>
              <option value="create">Import as New</option>
              <option value="update">Update Existing</option>
            </select>
          </div>
        </div>
      `;
        });

        container.innerHTML = html;

        // Add change listeners
        container.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', (e) => {
                const rowIndex = e.target.dataset.row;
                this.duplicateActions[rowIndex] = e.target.value;
            });

            // Set default action
            this.duplicateActions[select.dataset.row] = 'skip';
        });
    }

    renderPreviewTable() {
        if (!this.previewData || !this.previewData.preview_rows) return;

        const thead = document.getElementById('previewTableHead');
        const tbody = document.getElementById('previewTableBody');

        // Get mapped columns only
        const mappedColumns = Object.values(this.columnMapping).filter(Boolean);

        // Header
        let headerHtml = '<tr><th>#</th>';
        mappedColumns.forEach(col => {
            headerHtml += `<th>${col}</th>`;
        });
        headerHtml += '<th>Status</th></tr>';
        thead.innerHTML = headerHtml;

        // Build duplicate and error sets
        const duplicateRows = new Set(this.duplicates.map(d => d.row_index));
        const errorRows = new Set((this.previewData.validation_errors || []).map(e => e.row_index));

        // Body
        let bodyHtml = '';
        this.previewData.preview_rows.forEach(row => {
            const rowIdx = row._row_index;
            let rowClass = '';
            let status = '<span class="badge bg-success">New</span>';

            if (duplicateRows.has(rowIdx)) {
                rowClass = 'duplicate-row';
                status = '<span class="badge bg-warning">Duplicate</span>';
            } else if (errorRows.has(rowIdx)) {
                rowClass = 'error-row';
                status = '<span class="badge bg-danger">Error</span>';
            }

            bodyHtml += `<tr class="${rowClass}">`;
            bodyHtml += `<td>${rowIdx + 1}</td>`;
            mappedColumns.forEach(col => {
                bodyHtml += `<td>${row[col] || ''}</td>`;
            });
            bodyHtml += `<td>${status}</td>`;
            bodyHtml += '</tr>';
        });
        tbody.innerHTML = bodyHtml;
    }

    // ==================== Import Execution ====================

    setupImportButton() {
        const startBtn = document.getElementById('startImportBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.executeImport());
        }
    }

    async executeImport() {
        const pendingDiv = document.getElementById('importPending');
        const progressDiv = document.getElementById('importProgress');
        const completeDiv = document.getElementById('importComplete');

        pendingDiv.style.display = 'none';
        progressDiv.style.display = 'block';

        try {
            const response = await fetch('/api/v1/patient/import/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    file_url: this.fileUrl,
                    column_mapping: this.columnMapping,
                    duplicate_actions: this.duplicateActions
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Import failed');
            }

            const result = await response.json();

            // Update stats
            document.getElementById('liveImported').textContent = result.imported || 0;
            document.getElementById('liveUpdated').textContent = result.updated || 0;
            document.getElementById('liveSkipped').textContent = result.skipped || 0;
            document.getElementById('liveFailed').textContent = result.failed || 0;

            // Complete
            document.getElementById('importProgressBar').style.width = '100%';

            setTimeout(() => {
                progressDiv.style.display = 'none';
                completeDiv.style.display = 'block';

                // Summary
                const total = result.imported + result.updated + result.skipped + result.failed;
                document.getElementById('importSummary').textContent =
                    `Imported ${result.imported}, Updated ${result.updated}, Skipped ${result.skipped}, Failed ${result.failed} of ${total} total rows.`;

                // Failed download
                if (result.failed_rows_file) {
                    document.getElementById('failedDownload').style.display = 'block';
                    document.getElementById('downloadFailedBtn').href = '/media/' + result.failed_rows_file;
                }

                this.showToast('Import completed successfully!', 'success');
            }, 500);

        } catch (error) {
            console.error('Import error:', error);
            progressDiv.style.display = 'none';
            pendingDiv.style.display = 'block';
            this.showToast('Import failed: ' + error.message, 'error');
        }
    }

    // ==================== Utilities ====================

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    showToast(message, type = 'info') {
        if (typeof UTIL !== 'undefined' && UTIL.Toast) {
            new UTIL.Toast().ok(message, type.charAt(0).toUpperCase() + type.slice(1), type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.csvImportWizard = new CSVImportWizard();
});
