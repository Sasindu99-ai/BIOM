/**
 * Data Import Wizard Controller
 * Imports study data entries from CSV/Excel files into a dataset
 */

class DataImportWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.fileUrl = null;
        this.fileName = null;
        this.columns = [];
        this.columnMapping = {
            patientIdentifier: null,
            patientColumn: null,
            variables: {}
        };
        this.previewData = null;
        this.datasetVariables = [];

        this.init();
    }

    init() {
        this.loadDatasetInfo();
        this.setupDropzone();
        this.setupNavigation();
        this.setupImportButton();
    }

    // ==================== Dataset Info ====================

    async loadDatasetInfo() {
        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/details`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                }
            });

            if (!response.ok) throw new Error('Failed to load dataset');

            const result = await response.json();
            const data = result.data || result;
            const dataset = data.dataset?.[0] || {};
            this.datasetVariables = data.variables || [];

            // Update header
            document.getElementById('datasetNameHeader').textContent = dataset.name || 'Dataset';

            // Display variables
            const varsContainer = document.getElementById('datasetVariables');
            if (this.datasetVariables.length > 0) {
                varsContainer.innerHTML = this.datasetVariables.map(v =>
                    `<span class="variable-badge">${v.name}</span>`
                ).join('');
            } else {
                varsContainer.innerHTML = '<span class="text-muted">No variables defined</span>';
            }

        } catch (err) {
            console.error('Error loading dataset info:', err);
        }
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
        const percentLabel = document.getElementById('uploadPercent');
        const fileNameLabel = document.getElementById('uploadFileName');

        dropzone.classList.add('uploading');
        progressContainer.style.display = 'block';
        fileNameLabel.textContent = file.name;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                    percentLabel.textContent = percent + '%';
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200 || xhr.status === 201) {
                    const response = JSON.parse(xhr.responseText);
                    this.fileUrl = response.url || response.file_url || response.path;

                    dropzone.classList.remove('uploading');
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

        // Process step transitions
        if (this.currentStep === 1) {
            await this.parseFile();
        } else if (this.currentStep === 2) {
            if (!this.validateMapping()) {
                return;
            }
            await this.generatePreview();
        }

        this.currentStep++;
        this.updateWizardUI();
    }

    prevStep() {
        if (this.currentStep <= 1) return;
        this.currentStep--;
        this.updateWizardUI();
    }

    updateWizardUI() {
        // Update step indicators
        document.querySelectorAll('.wizard-step').forEach((step, idx) => {
            step.classList.remove('active', 'completed');
            if (idx + 1 < this.currentStep) {
                step.classList.add('completed');
            } else if (idx + 1 === this.currentStep) {
                step.classList.add('active');
            }
        });

        // Update panes
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

    // ==================== File Parsing ====================

    async parseFile() {
        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/preview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({ fileUrl: this.fileUrl })
            });

            if (!response.ok) throw new Error('Failed to parse file');

            const result = await response.json();
            const data = result.data || result;

            this.columns = data.columns || [];
            this.previewData = data;

            this.buildMappingUI();
            this.renderSampleData(data.sampleRows || []);

        } catch (err) {
            console.error('Error parsing file:', err);
            this.showToast('Failed to parse file', 'error');
        }
    }

    buildMappingUI() {
        // Patient identifier mapping
        const patientContainer = document.getElementById('patientMappingContainer');
        patientContainer.innerHTML = `
            <div class="col-md-6">
                <div class="mapping-card">
                    <label>Match by</label>
                    <select class="form-select form-select-sm" id="patientIdentifier">
                        <option value="reference">Patient Reference</option>
                        <option value="name">Patient Name</option>
                    </select>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mapping-card">
                    <label>File Column <span class="text-danger">*</span></label>
                    <select class="form-select form-select-sm" id="patientColumn">
                        <option value="">-- Select Column --</option>
                        ${this.columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                </div>
            </div>
        `;

        // Variable mapping
        const varsContainer = document.getElementById('variableMappingContainer');
        if (this.datasetVariables.length === 0) {
            varsContainer.innerHTML = '<div class="col-12 text-center text-muted py-3">No variables defined for this dataset</div>';
            return;
        }

        varsContainer.innerHTML = this.datasetVariables.map(v => `
            <div class="col-md-6 col-lg-4">
                <div class="mapping-card">
                    <label>${v.name} <span class="badge bg-secondary ms-1" style="font-size: 0.65rem;">${v.type || 'TEXT'}</span></label>
                    <select class="form-select form-select-sm variable-mapping" data-variable-id="${v.id}">
                        <option value="">-- Skip --</option>
                        ${this.columns.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                </div>
            </div>
        `).join('');
    }

    renderSampleData(rows) {
        const thead = document.getElementById('sampleDataHead');
        const tbody = document.getElementById('sampleDataBody');

        if (rows.length === 0) {
            thead.innerHTML = '';
            tbody.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">No data</td></tr>';
            return;
        }

        thead.innerHTML = '<tr>' + this.columns.map(c => `<th>${c}</th>`).join('') + '</tr>';
        tbody.innerHTML = rows.slice(0, 5).map(row =>
            '<tr>' + this.columns.map(c => `<td>${row[c] || ''}</td>`).join('') + '</tr>'
        ).join('');
    }

    validateMapping() {
        const patientColumn = document.getElementById('patientColumn').value;
        if (!patientColumn) {
            this.showToast('Please select a column for patient identification', 'warning');
            return false;
        }

        // Check if at least one variable is mapped
        const variableMappings = document.querySelectorAll('.variable-mapping');
        let hasMapping = false;
        variableMappings.forEach(select => {
            if (select.value) hasMapping = true;
        });

        if (!hasMapping) {
            this.showToast('Please map at least one variable', 'warning');
            return false;
        }

        // Store mappings
        this.columnMapping.patientIdentifier = document.getElementById('patientIdentifier').value;
        this.columnMapping.patientColumn = patientColumn;
        this.columnMapping.variables = {};

        variableMappings.forEach(select => {
            if (select.value) {
                this.columnMapping.variables[select.dataset.variableId] = select.value;
            }
        });

        return true;
    }

    // ==================== Preview ====================

    async generatePreview() {
        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/preview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    fileUrl: this.fileUrl,
                    mapping: this.columnMapping,
                    preview: true
                })
            });

            if (!response.ok) throw new Error('Failed to generate preview');

            const result = await response.json();
            const data = result.data || result;

            this.previewData = data;
            this.renderPreview(data);

        } catch (err) {
            console.error('Error generating preview:', err);
            this.showToast('Failed to generate preview', 'error');
        }
    }

    renderPreview(data) {
        // Update stats
        document.getElementById('statTotal').textContent = data.total || 0;
        document.getElementById('statNew').textContent = data.newCount || 0;
        document.getElementById('statDuplicates').textContent = data.updateCount || 0;
        document.getElementById('statErrors').textContent = data.errorCount || 0;

        // Show errors if any
        const errorsSection = document.getElementById('errorsSection');
        const errorsList = document.getElementById('errorsList');

        if (data.errors && data.errors.length > 0) {
            errorsSection.style.display = 'block';
            errorsList.innerHTML = data.errors.map(err => `
                <div class="error-item">
                    <i class="bi bi-exclamation-circle"></i>
                    <span>Row ${err.row}: ${err.message}</span>
                </div>
            `).join('');
        } else {
            errorsSection.style.display = 'none';
        }

        // Render preview table
        const mappedVars = Object.entries(this.columnMapping.variables).map(([varId, colName]) => {
            const variable = this.datasetVariables.find(v => v.id == varId);
            return { id: varId, name: variable?.name || colName, column: colName };
        });

        const thead = document.getElementById('previewTableHead');
        const tbody = document.getElementById('previewTableBody');

        thead.innerHTML = `<tr>
            <th>#</th>
            <th>Patient</th>
            <th>Status</th>
            ${mappedVars.map(v => `<th>${v.name}</th>`).join('')}
        </tr>`;

        const rows = data.rows || [];
        tbody.innerHTML = rows.slice(0, 50).map((row, idx) => `
            <tr class="${row.status === 'new' ? 'new-row' : row.status === 'update' ? 'update-row' : row.status === 'error' ? 'error-row' : ''}">
                <td>${idx + 1}</td>
                <td>${row.patientName || row.patientRef || 'Unknown'}</td>
                <td>
                    <span class="badge ${row.status === 'new' ? 'bg-success' : row.status === 'update' ? 'bg-warning' : 'bg-danger'}">
                        ${row.status === 'new' ? 'New' : row.status === 'update' ? 'Update' : 'Error'}
                    </span>
                </td>
                ${mappedVars.map(v => `<td>${row.values?.[v.id] || '-'}</td>`).join('')}
            </tr>
        `).join('');
    }

    // ==================== Import ====================

    setupImportButton() {
        const startBtn = document.getElementById('startImportBtn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.executeImport());
        }
    }

    async executeImport() {
        document.getElementById('importPending').style.display = 'none';
        document.getElementById('importProgress').style.display = 'block';

        const progressBar = document.getElementById('importProgressBar');
        const statusText = document.getElementById('importStatus');

        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    fileUrl: this.fileUrl,
                    mapping: this.columnMapping
                })
            });

            if (!response.ok) throw new Error('Import failed');

            const result = await response.json();
            const data = result.data || result;

            // Show completion
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importComplete').style.display = 'block';

            document.getElementById('liveImported').textContent = data.imported || 0;
            document.getElementById('liveUpdated').textContent = data.updated || 0;
            document.getElementById('liveSkipped').textContent = data.skipped || 0;
            document.getElementById('liveFailed').textContent = data.failed || 0;

            document.getElementById('importSummary').textContent =
                `Successfully imported ${data.imported || 0} new entries and updated ${data.updated || 0} existing entries.`;

        } catch (err) {
            console.error('Import error:', err);
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importPending').style.display = 'block';
            this.showToast('Import failed: ' + err.message, 'error');
        }
    }

    // ==================== Utilities ====================

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showToast(message, type = 'info') {
        if (typeof onUtil === 'function') {
            onUtil(() => {
                if (typeof thread === 'function') {
                    thread(() => {
                        if (typeof UTIL !== 'undefined' && UTIL.Toast) {
                            new UTIL.Toast().ok(message, type.charAt(0).toUpperCase() + type.slice(1), type);
                        }
                    });
                }
            });
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.dataImportWizard = new DataImportWizard();
});
