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
        this.totalRows = 0;  // For background job

        // Background job tracking
        this.currentJobId = null;
        this.pollInterval = null;

        this.init();
    }

    init() {
        this.loadDatasetInfo();
        this.setupDropzone();
        this.setupNavigation();
        this.setupImportButton();
        this.setupBackNavigation();
        this.restoreStateFromUrl();  // Restore wizard state from URL params
    }

    // ==================== URL State Management ====================

    restoreStateFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const fileUrl = params.get('file');
        const step = parseInt(params.get('step')) || 1;
        const fileName = params.get('name');

        if (fileUrl) {
            this.fileUrl = fileUrl;
            this.fileName = fileName || 'Restored file';

            // Restore job ID if present
            const jobId = params.get('job');
            if (jobId) {
                this.currentJobId = parseInt(jobId);
            }

            // Show file info on step 1
            document.querySelector('.file-info').style.display = 'block';
            document.getElementById('uploadedFileName').textContent = this.fileName;
            document.getElementById('uploadedFileSize').textContent = 'from previous session';
            document.getElementById('nextBtn').disabled = false;

            // If step > 1, navigate to that step
            if (step > 1) {
                this.navigateToStep(step);
            }
        }
    }

    updateUrlState() {
        const params = new URLSearchParams(window.location.search);
        
        if (this.fileUrl) {
            params.set('file', this.fileUrl);
            params.set('step', this.currentStep);
            if (this.fileName) {
                params.set('name', this.fileName);
            }
            if (this.currentJobId) {
                params.set('job', this.currentJobId);
            }
        } else {
            params.delete('file');
            params.delete('step');
            params.delete('name');
            params.delete('job');
        }

        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.replaceState({ step: this.currentStep, wizardActive: true }, '', newUrl);
    }

    async navigateToStep(targetStep) {
        // Navigate through wizard steps programmatically
        if (targetStep <= 1) return;

        // First, parse the file if we need to go past step 1
        if (targetStep > 1 && this.fileUrl) {
            await this.parseFile();
            this.currentStep = 2;
            this.updateWizardUI();

            if (targetStep > 2) {
                // Auto-validate and go to step 3
                if (this.validateMapping()) {
                    this.currentStep = 3;
                    this.updateWizardUI();
                    await this.generatePreview();
                }
            }
        }
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

                    // Update URL with file info for refresh persistence
                    this.updateUrlState();

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
            // Create pending job when moving from Step 1 to Step 2
            if (!this.currentJobId) {
                try {
                    await this.createPendingJob();
                } catch (err) {
                    this.showToast('Failed to create import job: ' + err.message, 'error');
                    return;
                }
            }
            await this.parseFile();
        } else if (this.currentStep === 2) {
            if (!this.validateMapping()) {
                return;
            }
            // Navigate to Step 3 first, then load preview (shows loading state)
            this.currentStep++;
            this.updateWizardUI();
            this.showStep3Loading(true);
            await this.generatePreview();
            this.showStep3Loading(false);
            return; // Already incremented and updated UI
        }

        this.currentStep++;
        this.updateWizardUI();
    }

    async createPendingJob() {
        console.log('[IMPORT] Creating pending job for file:', this.fileUrl);

        const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({
                fileUrl: this.fileUrl,
                fileName: this.fileName,
                mapping: {},  // Empty mapping = pending job
                columnTypes: {},
                totalRows: 0
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.message || 'Failed to create job');
        }

        const result = await response.json();
        const job = result.data || result;
        this.currentJobId = job.id;

        console.log('[IMPORT] Created pending job:', job.id);

        // Update URL with job ID
        this.updateUrlState();

        this.showToast('Import job created', 'info');
    }

    showStep3Loading(show) {
        const loading = document.getElementById('step3Loading');
        const content = document.getElementById('step3Content');
        if (loading) loading.style.display = show ? 'block' : 'none';
        if (content) content.style.display = show ? 'none' : 'block';
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

        // Persist step in URL
        this.updateUrlState();
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
            this.renderSampleData(data.previewData || []);

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
        console.log('renderSampleData called with rows:', rows);
        console.log('this.columns:', this.columns);
        console.log('this.dataColumns:', this.dataColumns);

        const thead = document.getElementById('sampleDataHead');
        const tbody = document.getElementById('sampleDataBody');

        console.log('thead element:', thead);
        console.log('tbody element:', tbody);

        if (!rows || rows.length === 0) {
            console.log('No rows to render');
            if (thead) thead.innerHTML = '';
            if (tbody) tbody.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">No data</td></tr>';
            return;
        }

        // Use dataColumns if available, otherwise use columns
        const columnsToShow = this.dataColumns && this.dataColumns.length > 0 ? this.dataColumns : this.columns;
        console.log('columnsToShow:', columnsToShow);

        if (thead) thead.innerHTML = '<tr>' + columnsToShow.map(c => `<th>${c}</th>`).join('') + '</tr>';
        if (tbody) tbody.innerHTML = rows.slice(0, 5).map(row =>
            '<tr>' + columnsToShow.map(c => `<td>${row[c] || ''}</td>`).join('') + '</tr>'
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
            // Store total rows for background job
            this.totalRows = data.stats?.total || data.totalRows || 0;
            this.renderPreview(data);

        } catch (err) {
            console.error('Error generating preview:', err);
            this.showToast('Failed to generate preview', 'error');
        }
    }

    renderPreview(data) {
        // Extract stats - backend returns stats in a nested object
        const stats = data.stats || {};

        // Update record stats
        document.getElementById('statTotal').textContent = stats.total || data.totalRows || 0;
        document.getElementById('statNew').textContent = stats.new || 0;
        document.getElementById('statDuplicates').textContent = stats.update || 0;
        document.getElementById('statErrors').textContent = stats.errors || 0;

        // Update file duplicates
        const fileDuplicatesEl = document.getElementById('statFileDuplicates');
        if (fileDuplicatesEl) fileDuplicatesEl.textContent = stats.fileDuplicates || 0;

        // Update patient stats
        const uniquePatientsEl = document.getElementById('statUniquePatients');
        const patientsExistingEl = document.getElementById('statPatientsExisting');
        const patientsToCreateEl = document.getElementById('statPatientsToCreate');

        if (uniquePatientsEl) uniquePatientsEl.textContent = stats.uniquePatients || 0;
        if (patientsExistingEl) patientsExistingEl.textContent = stats.patientsExisting || 0;
        if (patientsToCreateEl) patientsToCreateEl.textContent = stats.patientsToCreate || 0;

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

        // Backend returns previewData, not rows - also row fields use underscore prefix
        const rows = data.previewData || data.rows || [];
        tbody.innerHTML = rows.slice(0, 50).map((row, idx) => {
            // Map backend field names (with underscore prefix) to frontend names
            const rowNumber = row._row_number || row.rowNumber || (idx + 2);
            const status = row._status || row.status || 'new';
            const patientName = row._patient_name || row.patientName || row.patientRef || 'Unknown';
            const fileDuplicateOf = row._file_duplicate_of || row.fileDuplicateOf || '';
            const fileGroup = row._file_group || row.fileGroup || '';

            const isDuplicate = !!fileDuplicateOf;
            const statusClass = status === 'new' ? 'new-row' : status === 'update' ? 'update-row' : status === 'will_create' ? 'new-row' : status === 'error' ? 'error-row' : '';
            const rowClass = isDuplicate ? 'duplicate-row' : statusClass;

            // Determine display status
            const displayStatus = status === 'will_create' ? 'New' : status === 'new' ? 'New' : status === 'update' ? 'Update' : 'Error';
            const badgeClass = (status === 'new' || status === 'will_create') ? 'bg-success' : status === 'update' ? 'bg-warning' : 'bg-danger';

            return `
            <tr class="${rowClass}">
                <td>${rowNumber}</td>
                <td>${patientName}</td>
                <td>
                    <span class="badge ${badgeClass}">
                        ${displayStatus}
                    </span>
                </td>
                <td>
                    ${isDuplicate
                    ? `<span class="badge bg-secondary" title="Duplicate of row ${fileDuplicateOf}"><i class="bi bi-files me-1"></i>${fileGroup}</span>`
                    : fileGroup
                        ? `<span class="badge bg-info">${fileGroup}</span>`
                        : '-'
                }
                </td>
                ${mappedVars.map(v => `<td>${row[this.columnMapping.variables[v.id]] || row.values?.[v.id] || '-'}</td>`).join('')}
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
        console.log('[IMPORT] ===== executeImport() via Background Job =====');
        console.log('[IMPORT] fileUrl:', this.fileUrl);
        console.log('[IMPORT] columnMapping:', JSON.stringify(this.columnMapping, null, 2));

        document.getElementById('importPending').style.display = 'none';
        document.getElementById('importProgress').style.display = 'block';

        const progressBar = document.getElementById('importProgressBar');
        const statusText = document.getElementById('importStatus');

        try {
            let response;
            let job;

            if (this.currentJobId) {
                // Update and start existing pending job
                console.log('[IMPORT] Updating existing job:', this.currentJobId);
                response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs/${this.currentJobId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN
                    },
                    body: JSON.stringify({
                        mapping: this.columnMapping,
                        columnTypes: this.columnTypes,
                        totalRows: this.totalRows
                    })
                });
            } else {
                // Create and start new job (fallback if no pending job)
                console.log('[IMPORT] Creating new job');
                response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN
                    },
                    body: JSON.stringify({
                        fileUrl: this.fileUrl,
                        fileName: this.fileName,
                        mapping: this.columnMapping,
                        columnTypes: this.columnTypes,
                        totalRows: this.totalRows
                    })
                });
            }

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.message || 'Failed to start import job');
            }

            const result = await response.json();
            job = result.data || result;
            this.currentJobId = job.id;

            console.log('[IMPORT] Job started:', job);
            statusText.textContent = 'Import job started...';

            // Add pause/cancel controls
            this.showJobControls(job.id);

            // Start polling for progress
            this.startProgressPolling(progressBar, statusText);

        } catch (err) {
            console.error('[IMPORT] Error:', err);
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importPending').style.display = 'block';
            this.showToast('Import failed: ' + err.message, 'error');
        }
    }

    showJobControls(jobId) {
        // Insert controls after progress bar
        let controlsContainer = document.querySelector('.import-controls');
        if (!controlsContainer) {
            controlsContainer = document.createElement('div');
            controlsContainer.className = 'import-controls';
            const progressSection = document.getElementById('importProgress');
            if (progressSection) {
                progressSection.appendChild(controlsContainer);
            }
        }
        
        controlsContainer.innerHTML = `
            <div class="mt-3 d-flex gap-2 justify-content-center">
                <button id="pauseImportBtn" class="btn btn-warning">
                    <i class="bi bi-pause-fill me-1"></i> Pause
                </button>
                <button id="cancelImportBtn" class="btn btn-outline-danger">
                    <i class="bi bi-x-lg me-1"></i> Cancel
                </button>
            </div>
        `;

        document.getElementById('pauseImportBtn')?.addEventListener('click', () => this.pauseJob());
        document.getElementById('cancelImportBtn')?.addEventListener('click', () => this.cancelJob());
    }

    startProgressPolling(progressBar, statusText) {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(async () => {
            await this.pollJobStatus(progressBar, statusText);
        }, 2000);

        // Initial poll
        this.pollJobStatus(progressBar, statusText);
    }

    async pollJobStatus(progressBar, statusText) {
        if (!this.currentJobId) {
            this.stopPolling();
            return;
        }

        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs/${this.currentJobId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                }
            });

            if (!response.ok) throw new Error('Failed to get job status');

            const result = await response.json();
            const job = result.data || result;

            this.updateProgressUI(job, progressBar, statusText);

            // Check terminal states
            if (['COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED'].includes(job.status)) {
                this.stopPolling();
                this.handleJobComplete(job);
            }

        } catch (err) {
            console.error('[IMPORT] Poll error:', err);
        }
    }

    updateProgressUI(job, progressBar, statusText) {
        const percent = job.progress_percent || 0;
        progressBar.style.width = percent + '%';
        progressBar.textContent = percent + '%';

        if (job.status === 'RUNNING') {
            statusText.textContent = `Processing row ${job.processed_rows} of ${job.total_rows}`;
        } else if (job.status === 'PAUSED') {
            statusText.textContent = `Paused at row ${job.processed_rows} (${job.paused_reason || 'manual'})`;
        } else {
            statusText.textContent = job.status;
        }

        // Update live stats
        const liveImported = document.getElementById('liveImported');
        const liveUpdated = document.getElementById('liveUpdated');
        const liveSkipped = document.getElementById('liveSkipped');

        if (liveImported) liveImported.textContent = job.imported_count || 0;
        if (liveUpdated) liveUpdated.textContent = job.updated_count || 0;
        if (liveSkipped) liveSkipped.textContent = job.skipped_count || 0;
    }

    handleJobComplete(job) {
        if (job.status === 'COMPLETED') {
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importComplete').style.display = 'block';

            document.getElementById('liveImported').textContent = job.imported_count || 0;
            document.getElementById('liveUpdated').textContent = job.updated_count || 0;
            document.getElementById('liveSkipped').textContent = job.skipped_count || 0;
            document.getElementById('liveFailed').textContent = job.error_count || 0;

            let summary = `Successfully imported ${job.imported_count || 0} new entries and updated ${job.updated_count || 0} existing entries.`;
            if (job.patients_created > 0) {
                summary += ` Created ${job.patients_created} new patients.`;
            }
            if (job.variables_created > 0) {
                summary += ` Created ${job.variables_created} new variables.`;
            }
            document.getElementById('importSummary').textContent = summary;

            this.showToast('Import completed successfully!', 'success');

        } else if (job.status === 'PAUSED') {
            let controlsContainer = document.querySelector('.import-controls');
            if (controlsContainer) {
                controlsContainer.innerHTML = `
                    <div class="mt-3 d-flex gap-2 justify-content-center">
                        <button id="resumeImportBtn" class="btn btn-success">
                            <i class="bi bi-play-fill me-1"></i> Resume
                        </button>
                        <button id="cancelImportBtn" class="btn btn-outline-danger">
                            <i class="bi bi-x-lg me-1"></i> Cancel
                        </button>
                    </div>
                    <p class="text-muted mt-2 small text-center">
                        <i class="bi bi-info-circle me-1"></i>
                        ${job.paused_reason === 'consecutive_errors' 
                            ? 'Paused due to multiple consecutive errors.'
                            : 'Import paused. You can resume or cancel.'}
                    </p>
                `;
                document.getElementById('resumeImportBtn')?.addEventListener('click', () => this.resumeJob());
                document.getElementById('cancelImportBtn')?.addEventListener('click', () => this.cancelJob());
            }
            this.showToast(`Import paused (${job.paused_reason || 'manual'})`, 'warning');

        } else if (job.status === 'FAILED') {
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importPending').style.display = 'block';
            this.showToast('Import failed: ' + (job.errors?.[0]?.error || 'Unknown error'), 'error');

        } else if (job.status === 'CANCELLED') {
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importPending').style.display = 'block';
            this.showToast('Import cancelled', 'info');
        }
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    async pauseJob() {
        if (!this.currentJobId) return;
        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs/${this.currentJobId}/pause`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN }
            });
            if (response.ok) {
                this.showToast('Pausing import...', 'info');
            }
        } catch (err) {
            console.error('[IMPORT] Pause error:', err);
        }
    }

    async resumeJob() {
        if (!this.currentJobId) return;
        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs/${this.currentJobId}/resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN }
            });
            if (response.ok) {
                this.showToast('Resuming import...', 'info');
                const progressBar = document.getElementById('importProgressBar');
                const statusText = document.getElementById('importStatus');
                this.showJobControls(this.currentJobId);
                this.startProgressPolling(progressBar, statusText);
            }
        } catch (err) {
            console.error('[IMPORT] Resume error:', err);
        }
    }

    async cancelJob() {
        if (!this.currentJobId) return;
        if (!confirm('Are you sure you want to cancel this import?')) return;
        try {
            const response = await fetch(`/api/v1/dataset/${DATASET_ID}/import/jobs/${this.currentJobId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN }
            });
            if (response.ok) {
                this.stopPolling();
                document.getElementById('importProgress').style.display = 'none';
                document.getElementById('importPending').style.display = 'block';
                this.showToast('Import cancelled', 'info');
            }
        } catch (err) {
            console.error('[IMPORT] Cancel error:', err);
        }
    }

    handleImportEvent(eventType, data, progressBar, statusText) {
        console.log(`[DEBUG EVENT] handleImportEvent called: type=${eventType}, data=`, data);

        if (eventType === 'progress') {
            // Update progress bar
            const percent = data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;
            console.log(`[DEBUG EVENT] Progress: ${data.current}/${data.total} = ${percent}%`);
            console.log(`[DEBUG EVENT] Updating progressBar:`, progressBar, `width to ${percent}%`);
            progressBar.style.width = percent + '%';
            progressBar.textContent = percent + '%';

            // Update status text
            statusText.textContent = `Processing row ${data.current} of ${data.total}`;
            console.log(`[DEBUG EVENT] Updated statusText: "${statusText.textContent}"`);

            // Update live stats
            const liveImported = document.getElementById('liveImported');
            const liveUpdated = document.getElementById('liveUpdated');
            const liveSkipped = document.getElementById('liveSkipped');
            console.log(`[DEBUG EVENT] Live stat elements: imported=${liveImported}, updated=${liveUpdated}, skipped=${liveSkipped}`);

            if (liveImported) liveImported.textContent = data.imported || 0;
            if (liveUpdated) liveUpdated.textContent = data.updated || 0;
            if (liveSkipped) liveSkipped.textContent = data.skipped || 0;
            console.log(`[DEBUG EVENT] Updated live stats: imported=${data.imported || 0}, updated=${data.updated || 0}, skipped=${data.skipped || 0}`);

        } else if (eventType === 'complete') {
            console.log('[DEBUG EVENT] Import complete event received');
            // Show completion
            document.getElementById('importProgress').style.display = 'none';
            document.getElementById('importComplete').style.display = 'block';

            document.getElementById('liveImported').textContent = data.imported || 0;
            document.getElementById('liveUpdated').textContent = data.updated || 0;
            document.getElementById('liveSkipped').textContent = data.skipped || 0;
            document.getElementById('liveFailed').textContent = (data.errors || []).length;

            // Build summary message
            let summary = `Successfully imported ${data.imported || 0} new entries and updated ${data.updated || 0} existing entries.`;
            if (data.duplicatesSkipped > 0) {
                summary += ` Skipped ${data.duplicatesSkipped} duplicate rows.`;
            }
            if (data.patientsCreated > 0) {
                summary += ` Created ${data.patientsCreated} new patients.`;
            }
            if (data.variablesCreated > 0) {
                summary += ` Created ${data.variablesCreated} new variables.`;
            }
            document.getElementById('importSummary').textContent = summary;
            console.log('[DEBUG EVENT] Completion summary:', summary);

        } else if (eventType === 'error') {
            console.error('[DEBUG EVENT] Import error event:', data.message);
            this.showToast('Import error: ' + data.message, 'error');
        } else {
            console.warn(`[DEBUG EVENT] Unknown event type: ${eventType}`);
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
