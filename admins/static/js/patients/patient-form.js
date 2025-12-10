/**
 * Patient Form Main Controller
 * Uses UTIL.import() for dynamic module loading without type="module"
 */

(async function () {
    try {
        // Dynamic imports using UTIL - get module exports
        const [rowManagerModule, validationModule] = await Promise.all([
            UTIL.import('/static/js/patients/row-manager.js', 1),
            UTIL.import('/static/js/patients/validation.js', 1)
        ]);

        const RowManager = rowManagerModule.RowManager;
        const validateRow = validationModule.validateRow;

        // Get CSRF token
        const getCsrfToken = () => {
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            if (metaTag) return metaTag.content;

            const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (input) return input.value;

            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];

            return cookieValue || '';
        };

        const csrf = getCsrfToken();
        if (!csrf) {
            console.error('CSRF token not found');
            return;
        }

        // Find the form in current context (handles both popup and full page)
        const form = document.getElementById('addPatientForm');
        if (!form) {
            console.error('Add patient form not found');
            return;
        }

        // Get container and template from within the form context
        const container = form.querySelector('#patientsContainer');
        const template = document.getElementById('patientRowTemplate');

        if (!container || !template) {
            console.error('Container or template not found');
            return;
        }

        // Initialize row manager with elements from current context
        const rowManager = new RowManager(container, template, csrf);

        // Add initial row
        rowManager.addRow();

        // Add row button
        const addRowBtn = document.getElementById('addRowBtn');
        if (addRowBtn) {
            addRowBtn.addEventListener('click', () => {
                rowManager.addRow();
            });
        }

        // Alt+N shortcut to add row (Ctrl+N conflicts with browser)
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key === 'n') {
                e.preventDefault();
                rowManager.addRow();
            }
        });

        // Form submission (Save All) - reuse form variable from above
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const unsavedRows = rowManager.getUnsavedRows();

                if (unsavedRows.length === 0) {
                    new UTIL.Toast().ok('No patients to save. Please add at least one patient.', 'No Data', 'warning');
                    return;
                }

                // Validate all rows first
                let allValid = true;
                let hasAtLeastOneName = false;

                unsavedRows.forEach(row => {
                    const validation = validateRow(row);
                    if (!validation.hasName || !validation.isValid) {
                        allValid = false;
                        row.classList.add('shake');
                        setTimeout(() => row.classList.remove('shake'), 400);
                    }
                    if (validation.hasName) {
                        hasAtLeastOneName = true;
                    }
                });

                if (!hasAtLeastOneName) {
                    new UTIL.Toast().ok('Please enter at least one patient with a name (first or last name required)', 'Required', 'warning');
                    return;
                }

                if (!allValid) {
                    new UTIL.Toast().ok('Please fix validation errors before saving', 'Validation Error', 'error');
                    return;
                }

                // Show loading
                const saveBtn = document.getElementById('saveAllBtn');
                const originalHtml = saveBtn.innerHTML;
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

                try {
                    // Save all rows
                    const savePromises = unsavedRows.map(row => {
                        const rowId = row.dataset.rowId;
                        return rowManager.saveRow(rowId);
                    });

                    const results = await Promise.all(savePromises);
                    const successCount = results.filter(r => r).length;

                    if (successCount === unsavedRows.length) {
                        new UTIL.Toast().ok(`Successfully saved ${successCount} patient(s)!`, 'Success', 'success');

                        // Redirect or refresh
                        setTimeout(() => {
                            window.location.href = '/dashboard/patients/';
                        }, 1000);
                    } else {
                        new UTIL.Toast().ok(`Saved ${successCount} out of ${unsavedRows.length} patients. Please check errors.`, 'Partial Success', 'warning');
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = originalHtml;
                    }
                } catch (error) {
                    console.error('Save all error:', error);
                    new UTIL.Toast().ok('Error saving patients: ' + error.message, 'Save Error', 'error');
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = originalHtml;
                }
            });
        }

        // Unsaved changes warning
        window.addEventListener('beforeunload', (e) => {
            const unsavedRows = rowManager.getUnsavedRows();
            if (unsavedRows.length > 0) {
                e.preventDefault();
                e.returnValue = 'You have unsaved patients. Are you sure you want to leave?';
            }
        });

        console.log('Patient form initialized successfully');
    } catch (error) {
        console.error('Failed to initialize patient form:', error);
    }
})();
