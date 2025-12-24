/**
 * Patient Match Tool Controller
 * Matches uploaded CSV data against existing patients and allows download
 */

class PatientMatchTool {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 3;
        this.fileUrl = null;
        this.fileName = null;
        this.columns = [];
        this.columnMapping = {};
        this.previewData = null;

        this.init();
    }

    init() {
        this.setupDropzone();
        this.setupNavigation();
        this.setupDownloadButton();
    }

    // ==================== Dropzone ====================

    setupDropzone() {
        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('fileInput');

        if (!dropzone || !fileInput) return;

        dropzone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadFile(e.target.files[0]);
            }
        });

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
        const validExtensions = ['.csv', '.xlsx', '.xls'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExtensions.includes(ext)) {
            this.showToast('Invalid file type. Please upload CSV or Excel files.', 'error');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            this.showToast('File too large. Maximum size is 10MB.', 'error');
            return;
        }

        this.fileName = file.name;

        const dropzone = document.getElementById('dropzone');
        const progressContainer = document.querySelector('.upload-progress');
        const progressBar = document.getElementById('uploadProgressBar');
        const percentText = document.getElementById('uploadPercent');
        const fileNameText = document.getElementById('uploadFileName');

        dropzone.classList.add('uploading');
        progressContainer.style.display = 'block';
        fileNameText.textContent = file.name;

        try {
            const formData = new FormData();
            formData.append('file', file);

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

                    progressContainer.style.display = 'none';
                    document.querySelector('.file-info').style.display = 'block';
                    document.getElementById('uploadedFileName').textContent = file.name;
                    document.getElementById('uploadedFileSize').textContent = this.formatFileSize(file.size);

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

        if (this.currentStep === 1 && !this.fileUrl) {
            this.showToast('Please upload a file first', 'warning');
            return;
        }

        if (this.currentStep === 1) {
            await this.loadPreview();
        }

        if (this.currentStep === 2) {
            if (!this.validateMapping()) {
                return;
            }
            // Start matching
            this.currentStep++;
            this.updateUI();
            await this.performMatching();
            return;
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
            const response = await fetch('/api/v1/patient/match/preview', {
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

        // Field groups for better organization
        const fieldGroups = [
            {
                name: 'Identity Fields',
                description: 'Map patient identification info (at least name OR location required)',
                fields: [
                    { key: 'firstName', label: 'First Name', hint: 'Patient first name' },
                    { key: 'lastName', label: 'Last Name', hint: 'Patient last name / surname' },
                ]
            },
            {
                name: 'Demographics',
                description: 'Age or date of birth for matching',
                fields: [
                    { key: 'dateOfBirth', label: 'Date of Birth', hint: 'Various date formats supported' },
                    { key: 'age', label: 'Age', hint: 'Will be used for approximate matching' },
                    { key: 'gender', label: 'Gender', hint: 'M/F/Male/Female' },
                ]
            },
            {
                name: 'Location',
                description: 'GPS coordinates for location-based matching',
                fields: [
                    { key: 'latitude', label: 'Latitude', hint: 'GPS latitude coordinate' },
                    { key: 'longitude', label: 'Longitude', hint: 'GPS longitude coordinate' },
                ]
            }
        ];

        let html = '';

        fieldGroups.forEach(group => {
            html += `
            <div class="col-12 mb-3">
                <h6 class="text-muted mb-1"><i class="bi bi-folder me-1"></i>${group.name}</h6>
                <small class="text-muted">${group.description}</small>
            </div>`;

            group.fields.forEach(field => {
                const selectedColumn = this.columnMapping[field.key] || '';

                html += `
                <div class="col-md-6 mb-3">
                    <div class="mapping-row">
                        <div class="mapping-field">
                            <label>${field.label}</label>
                            <small class="text-muted d-block">${field.hint}</small>
                        </div>
                        <i class="bi bi-arrow-right mapping-arrow"></i>
                        <div class="mapping-select" style="flex: 1;">
                            <select class="form-select column-select" data-field="${field.key}">
                                <option value="">-- Not Mapped --</option>
                                ${this.columns.map(col => `
                                    <option value="${col}" ${col === selectedColumn ? 'selected' : ''}>
                                        ${col}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                    </div>
                </div>`;
            });
        });

        container.innerHTML = html;

        // Initialize Select2 on all column selects
        $(container).find('.column-select').select2({
            placeholder: 'Search columns...',
            allowClear: true,
            width: '100%',
            theme: 'default',
            dropdownParent: $(container).closest('.card-body')
        });

        container.querySelectorAll('.column-select').forEach(select => {
            $(select).on('change', (e) => {
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

        let headerHtml = '<tr>';
        this.columns.forEach(col => {
            headerHtml += `<th>${col}</th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

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
        // Need either (firstName or lastName) OR (latitude and longitude)
        const hasName = this.columnMapping.firstName || this.columnMapping.lastName;
        const hasLocation = this.columnMapping.latitude && this.columnMapping.longitude;

        if (!hasName && !hasLocation) {
            this.showToast('Please map either First/Last Name OR Latitude/Longitude coordinates', 'warning');
            return false;
        }
        return true;
    }

    // ==================== Matching ====================

    async performMatching() {
        const progressDiv = document.getElementById('matchingProgress');
        const resultsDiv = document.getElementById('matchResults');

        progressDiv.style.display = 'block';
        resultsDiv.style.display = 'none';

        try {
            const response = await fetch('/api/v1/patient/match/preview', {
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
                throw new Error(error.error || 'Failed to match patients');
            }

            this.previewData = await response.json();

            // Update stats
            const stats = this.previewData.stats || {};
            document.getElementById('statTotal').textContent = stats.total || 0;
            document.getElementById('statMatched').textContent = stats.matched || 0;
            document.getElementById('statUnmatched').textContent = stats.unmatched || 0;
            document.getElementById('statMatchRate').textContent = (stats.match_rate || 0) + '%';

            // Render preview table
            this.renderPreviewTable();

            // Show results
            progressDiv.style.display = 'none';
            resultsDiv.style.display = 'block';

            this.showToast(`Matching complete! ${stats.matched}/${stats.total} matched`, 'success');

        } catch (error) {
            console.error('Matching error:', error);
            progressDiv.style.display = 'none';
            this.showToast('Failed to match patients: ' + error.message, 'error');
        }
    }

    renderPreviewTable() {
        if (!this.previewData || !this.previewData.preview_rows) return;

        const thead = document.getElementById('previewTableHead');
        const tbody = document.getElementById('previewTableBody');

        // Columns: original + match info
        const displayColumns = [...this.columns.slice(0, 4), 'Match Status', 'Matched Patient'];

        let headerHtml = '<tr>';
        displayColumns.forEach(col => {
            headerHtml += `<th style="background-color: var(--bg-secondary, #1f2937); padding: 0.75rem 0.5rem; border-color: var(--border-secondary, #374151);">${col}</th>`;
        });
        headerHtml += '</tr>';
        thead.innerHTML = headerHtml;

        let bodyHtml = '';
        this.previewData.preview_rows.forEach(row => {
            const isMatched = row._matched;
            const rowClass = isMatched ? '' : 'table-warning';

            bodyHtml += `<tr class="${rowClass}">`;
            this.columns.slice(0, 4).forEach(col => {
                bodyHtml += `<td style="padding: 0.5rem; border-color: var(--border-secondary, #374151);">${row[col] || ''}</td>`;
            });

            // Match status
            if (isMatched) {
                bodyHtml += `<td style="padding: 0.5rem;"><span class="badge bg-success">MATCHED</span></td>`;
                bodyHtml += `<td style="padding: 0.5rem;">#${row._match_id} - ${row._match_name}</td>`;
            } else {
                bodyHtml += `<td style="padding: 0.5rem;"><span class="badge bg-warning text-dark">NOT MATCHED</span></td>`;
                bodyHtml += `<td style="padding: 0.5rem;">-</td>`;
            }

            bodyHtml += '</tr>';
        });
        tbody.innerHTML = bodyHtml;
    }

    // ==================== Download ====================

    setupDownloadButton() {
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadCSV());
        }
    }

    async downloadCSV() {
        const downloadBtn = document.getElementById('downloadBtn');
        const originalText = downloadBtn.innerHTML;

        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Preparing...';

        try {
            const response = await fetch('/api/v1/patient/match/download', {
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
                throw new Error(error.error || 'Download failed');
            }

            // Get the blob and trigger download
            const blob = await response.blob();
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'matched_patients.csv';

            if (contentDisposition) {
                const matches = contentDisposition.match(/filename="([^"]+)"/);
                if (matches && matches[1]) {
                    filename = matches[1];
                }
            }

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            this.showToast('Download started!', 'success');

        } catch (error) {
            console.error('Download error:', error);
            this.showToast('Failed to download: ' + error.message, 'error');
        } finally {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = originalText;
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
    window.patientMatchTool = new PatientMatchTool();
});
