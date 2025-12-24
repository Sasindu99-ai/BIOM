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
        this.dataColumns = [];      // Columns that can be mapped to variables
        this.systemColumns = [];    // System columns to skip (from patient match output)
        this.patientSuggestions = {}; // Auto-detected patient column mappings
        this.variableSuggestions = {}; // Auto-detected variable column mappings
        this.columnTypes = {};      // Detected column data types
        this.columnMapping = {
            patient: {
                reference: '',
                firstName: '',
                lastName: '',
                dateOfBirth: '',
                age: '',
                gender: '',
                latitude: '',
                longitude: ''
            },
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
        this.setupBackNavigation();
    }

    setupBackNavigation() {
        // Push initial state
        window.history.pushState({ step: 1, wizardActive: true }, '', window.location.href);

        // Handle back button
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.wizardActive && this.currentStep > 1) {
                e.preventDefault();
                this.prevStep();
                window.history.pushState({ step: this.currentStep, wizardActive: true }, '', window.location.href);
            }
        });
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
            this.dataColumns = data.dataColumns || this.columns;
            this.systemColumns = data.systemColumns || [];
            this.patientSuggestions = data.patientSuggestions || {};
            this.variableSuggestions = data.variableSuggestions || {};
            this.columnTypes = data.columnTypes || {};
            this.previewData = data;

            // Apply auto-suggestions to columnMapping
            for (const [field, column] of Object.entries(this.patientSuggestions)) {
                this.columnMapping.patient[field] = column;
            }
            for (const [varId, column] of Object.entries(this.variableSuggestions)) {
                this.columnMapping.variables[varId] = column;
            }

            this.buildMappingUI();
            this.renderSampleData(data.sampleRows || []);

        } catch (err) {
            console.error('Error parsing file:', err);
            this.showToast('Failed to parse file', 'error');
        }
    }

    buildMappingUI() {
        const columnOptions = this.columns.map(c => `<option value="${c}">${c}</option>`).join('');

        // Patient identifier mapping - organized in groups
        const patientContainer = document.getElementById('patientMappingContainer');
        patientContainer.innerHTML = `
            <!-- Identity Group -->
            <div class="col-12 mb-2">
                <small class="text-muted fw-semibold">IDENTITY</small>
            </div>
            <div class="col-md-4">
                <div class="mapping-card">
                    <label>Patient Reference</label>
                    <select class="form-select form-select-sm patient-field" data-field="reference">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>
            <div class="col-md-4">
                <div class="mapping-card">
                    <label>First Name</label>
                    <select class="form-select form-select-sm patient-field" data-field="firstName">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>
            <div class="col-md-4">
                <div class="mapping-card">
                    <label>Last Name</label>
                    <select class="form-select form-select-sm patient-field" data-field="lastName">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>

            <!-- Demographics Group -->
            <div class="col-12 mt-3 mb-2">
                <small class="text-muted fw-semibold">DEMOGRAPHICS</small>
            </div>
            <div class="col-md-4">
                <div class="mapping-card">
                    <label>Date of Birth</label>
                    <select class="form-select form-select-sm patient-field" data-field="dateOfBirth">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>
            <div class="col-md-4">
                <div class="mapping-card">
                    <label>Age</label>
                    <select class="form-select form-select-sm patient-field" data-field="age">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>
            <div class="col-md-4">
                <div class="mapping-card">
                    <label>Gender</label>
                    <select class="form-select form-select-sm patient-field" data-field="gender">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>

            <!-- Location Group -->
            <div class="col-12 mt-3 mb-2">
                <small class="text-muted fw-semibold">LOCATION</small>
            </div>
            <div class="col-md-6">
                <div class="mapping-card">
                    <label>Latitude</label>
                    <select class="form-select form-select-sm patient-field" data-field="latitude">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mapping-card">
                    <label>Longitude</label>
                    <select class="form-select form-select-sm patient-field" data-field="longitude">
                        <option value="">-- Skip --</option>
                        ${columnOptions}
                    </select>
                </div>
            </div>
        `;

        // Show system columns info if any
        if (this.systemColumns.length > 0) {
            patientContainer.insertAdjacentHTML('beforeend', `
                <div class="col-12 mt-3">
                    <div class="alert alert-warning py-2" style="font-size: 0.85rem;">
                        <i class="bi bi-info-circle me-1"></i>
                        <strong>${this.systemColumns.length} system columns</strong> detected (from patient match output) and will be skipped:
                        <span class="text-muted">${this.systemColumns.slice(0, 5).join(', ')}${this.systemColumns.length > 5 ? '...' : ''}</span>
                    </div>
                </div>
            `);
        }

        // Variable mapping - separate matched and unmatched
        const varsContainer = document.getElementById('variableMappingContainer');

        // Categorize variables into matched and unmatched
        const matchedVars = this.datasetVariables.filter(v => this.columnMapping.variables[v.id]);
        const unmatchedVars = this.datasetVariables.filter(v => !this.columnMapping.variables[v.id]);

        // Get unmapped data columns (for auto-create preview)
        const mappedPatientCols = Object.values(this.columnMapping.patient).filter(c => c);
        const mappedVarCols = Object.values(this.columnMapping.variables).filter(c => c);
        const allMappedCols = new Set([...mappedPatientCols, ...mappedVarCols, ...this.systemColumns]);
        const unmappedCols = this.dataColumns.filter(col => !allMappedCols.has(col));

        let variablesHtml = '';

        // Unmatched variables (prominent - needs mapping)
        if (unmatchedVars.length > 0) {
            variablesHtml += `
                <div class="col-12 mb-2">
                    <small class="text-muted fw-semibold">UNMAPPED VARIABLES</small>
                    <span class="badge bg-warning ms-2">${unmatchedVars.length}</span>
                </div>
            `;
            variablesHtml += unmatchedVars.map(v => `
                <div class="col-md-6 col-lg-4">
                    <div class="mapping-card">
                        <label>${v.name} <span class="badge bg-secondary ms-1" style="font-size: 0.65rem;">${v.type || 'TEXT'}</span></label>
                        <select class="form-select form-select-sm variable-mapping" data-variable-id="${v.id}">
                            <option value="">-- Skip --</option>
                            ${columnOptions}
                        </select>
                    </div>
                </div>
            `).join('');
        }

        // Matched variables (collapsible - already mapped)
        if (matchedVars.length > 0) {
            variablesHtml += `
                <div class="col-12 mt-3 mb-2">
                    <a data-bs-toggle="collapse" href="#matchedVarsCollapse" role="button" aria-expanded="false" class="text-decoration-none">
                        <small class="text-muted fw-semibold">MATCHED VARIABLES</small>
                        <span class="badge bg-success ms-2">${matchedVars.length}</span>
                        <i class="bi bi-chevron-down ms-1"></i>
                    </a>
                </div>
                <div class="collapse" id="matchedVarsCollapse">
                    <div class="row">
            `;
            variablesHtml += matchedVars.map(v => `
                <div class="col-md-6 col-lg-4">
                    <div class="mapping-card border-success">
                        <label>${v.name} <span class="badge bg-secondary ms-1" style="font-size: 0.65rem;">${v.type || 'TEXT'}</span></label>
                        <select class="form-select form-select-sm variable-mapping" data-variable-id="${v.id}">
                            <option value="">-- Skip --</option>
                            ${columnOptions}
                        </select>
                    </div>
                </div>
            `).join('');
            variablesHtml += `</div></div>`;
        }

        // Unmapped columns (will be auto-created as new variables)
        if (unmappedCols.length > 0) {
            variablesHtml += `
                <div class="col-12 mt-3 mb-2">
                    <a data-bs-toggle="collapse" href="#newVarsCollapse" role="button" aria-expanded="false" class="text-decoration-none">
                        <small class="text-muted fw-semibold">NEW VARIABLES (auto-create)</small>
                        <span class="badge bg-info ms-2">${unmappedCols.length}</span>
                        <i class="bi bi-chevron-down ms-1"></i>
                    </a>
                    <small class="text-muted d-block">These columns will be created as new variables</small>
                </div>
                <div class="collapse show" id="newVarsCollapse">
                    <div class="row">
            `;
            variablesHtml += unmappedCols.map(col => {
                const type = this.columnTypes[col] || 'TEXT';
                const typeBadge = {
                    'NUMBER': 'bg-primary',
                    'DATE': 'bg-info',
                    'BOOLEAN': 'bg-warning',
                    'TEXT': 'bg-secondary'
                }[type] || 'bg-secondary';
                return `
                    <div class="col-md-6 col-lg-4">
                        <div class="mapping-card border-info" style="opacity: 0.8;">
                            <label>${col} <span class="badge ${typeBadge} ms-1" style="font-size: 0.65rem;">${type}</span></label>
                            <div class="text-muted small"><i class="bi bi-plus-circle me-1"></i>Will be created</div>
                        </div>
                    </div>
                `;
            }).join('');
            variablesHtml += `</div></div>`;
        }

        if (this.datasetVariables.length === 0 && unmappedCols.length === 0) {
            variablesHtml = '<div class="col-12 text-center text-muted py-3">No variables detected.</div>';
        }

        varsContainer.innerHTML = variablesHtml;

        // Apply saved selections to dropdowns
        this.applySelections();

        // Initialize Select2 on all dropdowns
        this.initSelect2();
    }

    applySelections() {
        // Apply patient field selections
        document.querySelectorAll('.patient-field').forEach(select => {
            const field = select.dataset.field;
            const value = this.columnMapping.patient[field];
            if (value) {
                select.value = value;
            }
        });

        // Apply variable selections
        document.querySelectorAll('.variable-mapping').forEach(select => {
            const varId = select.dataset.variableId;
            const value = this.columnMapping.variables[varId];
            if (value) {
                select.value = value;
            }
        });
    }

    initSelect2() {
        // Check if Select2 is available
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $('.patient-field, .variable-mapping').select2({
                theme: 'bootstrap-5',
                width: '100%',
                placeholder: '-- Select Column --',
                allowClear: true
            });
        }
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
        // Collect patient field mappings
        const patientFields = {};
        document.querySelectorAll('.patient-field').forEach(select => {
            const field = select.dataset.field;
            const value = select.value;
            if (value) {
                patientFields[field] = value;
            }
        });

        // Check if at least one patient identifier is mapped
        const hasReference = !!patientFields.reference;
        const hasName = !!(patientFields.firstName || patientFields.lastName);
        const hasLocation = !!(patientFields.latitude && patientFields.longitude);

        if (!hasReference && !hasName && !hasLocation) {
            this.showToast('Please map at least one patient identifier (Reference, Name, or Location)', 'warning');
            return false;
        }

        // Collect variable mappings
        const variableMappings = document.querySelectorAll('.variable-mapping');
        let hasVariableMapping = false;
        const varMappingObj = {};
        variableMappings.forEach(select => {
            if (select.value) {
                hasVariableMapping = true;
                varMappingObj[select.dataset.variableId] = select.value;
            }
        });

        // Get unmapped columns count (will be auto-created)
        const mappedPatientCols = Object.values(patientFields).filter(c => c);
        const mappedVarCols = Object.values(varMappingObj).filter(c => c);
        const allMappedCols = new Set([...mappedPatientCols, ...mappedVarCols, ...this.systemColumns]);
        const unmappedCols = this.dataColumns.filter(col => !allMappedCols.has(col));

        // Must have either variable mappings or unmapped columns to create
        if (!hasVariableMapping && unmappedCols.length === 0) {
            this.showToast('No data to import - no variables mapped and no new columns detected', 'warning');
            return false;
        }

        // Store mappings
        this.columnMapping.patient = patientFields;
        this.columnMapping.variables = varMappingObj;

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

        // Update info about file duplicates if the elements exist
        const uniquePatientsEl = document.getElementById('statUniquePatients');
        const fileDuplicatesEl = document.getElementById('statFileDuplicates');
        if (uniquePatientsEl) uniquePatientsEl.textContent = data.uniquePatients || 0;
        if (fileDuplicatesEl) fileDuplicatesEl.textContent = data.fileDuplicates || 0;

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
            <th>Duplicate</th>
            ${mappedVars.map(v => `<th>${v.name}</th>`).join('')}
        </tr>`;

        const rows = data.rows || [];
        tbody.innerHTML = rows.slice(0, 50).map((row, idx) => {
            const isDuplicate = !!row.fileDuplicateOf;
            const statusClass = row.status === 'new' ? 'new-row' : row.status === 'update' ? 'update-row' : row.status === 'error' ? 'error-row' : '';
            const rowClass = isDuplicate ? 'duplicate-row' : statusClass;

            return `
            <tr class="${rowClass}">
                <td>${row.rowNumber || (idx + 2)}</td>
                <td>${row.patientName || row.patientRef || 'Unknown'}</td>
                <td>
                    <span class="badge ${row.status === 'new' ? 'bg-success' : row.status === 'update' ? 'bg-warning' : 'bg-danger'}">
                        ${row.status === 'new' ? 'New' : row.status === 'update' ? 'Update' : 'Error'}
                    </span>
                </td>
                <td>
                    ${isDuplicate
                    ? `<span class="badge bg-secondary" title="Duplicate of row ${row.fileDuplicateOf}"><i class="bi bi-files me-1"></i>${row.fileGroup}</span>`
                    : row.fileGroup
                        ? `<span class="badge bg-info">${row.fileGroup}</span>`
                        : '-'
                }
                </td>
                ${mappedVars.map(v => `<td>${row.values?.[v.id] || '-'}</td>`).join('')}
            </tr>
        `}).join('');
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
                    mapping: this.columnMapping,
                    columnTypes: this.columnTypes
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

            // Build summary message
            let summary = `Successfully imported ${data.imported || 0} new entries and updated ${data.updated || 0} existing entries.`;
            if (data.duplicatesSkipped > 0) {
                summary += ` Skipped ${data.duplicatesSkipped} duplicate rows.`;
            }
            if (data.variablesCreated > 0) {
                summary += ` Created ${data.variablesCreated} new variables.`;
            }
            document.getElementById('importSummary').textContent = summary;

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
