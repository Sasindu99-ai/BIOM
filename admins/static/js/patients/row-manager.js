/**
 * Patient Row Manager Module
 * Handles CRUD operations for patient rows
 */

import { validateRow, clearRowValidation } from './validation.js';

export class RowManager {
    constructor(containerId, templateId, csrfToken) {
        this.container = document.getElementById(containerId);
        this.template = document.getElementById(templateId);
        this.csrf = csrfToken;
        this.rowCounter = 0;
    }

    /**
     * Add a new patient row
     */
    addRow() {
        this.rowCounter++;

        // Clone template
        const clone = this.template.content.cloneNode(true);
        const row = clone.querySelector('.patient-row');
        row.dataset.rowId = this.rowCounter;
        row.classList.add('fade-in');

        // Attach event listeners
        this.attachEventListeners(row);

        // Append to container
        this.container.appendChild(clone);

        // Focus first input
        const firstInput = row.querySelector('input[name="firstName"]');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }

        return row;
    }

    /**
     * Remove a patient row
     */
    removeRow(rowId) {
        const row = this.container.querySelector(`[data-row-id="${rowId}"]`);
        if (!row) return;

        // Animate out
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';

        setTimeout(() => row.remove(), 200);
    }

    /**
     * Save a single patient row
     */
    async saveRow(rowId) {
        const row = this.container.querySelector(`[data-row-id="${rowId}"]`);
        if (!row) return false;

        // Check if already saved
        if (row.classList.contains('saved')) {
            return true;
        }

        // Validate
        const validation = validateRow(row);

        if (!validation.hasName) {
            row.classList.add('shake');
            setTimeout(() => row.classList.remove('shake'), 400);
            alert('Please enter at least a first name or last name');
            return false;
        }

        if (!validation.isValid) {
            row.classList.add('shake');
            setTimeout(() => row.classList.remove('shake'), 400);
            const errorMessages = validation.errors.map(e => e.message).join('\n');
            alert('Please fix validation errors:\n' + errorMessages);
            return false;
        }

        // Get save button
        const saveBtn = row.querySelector('.btn-save');
        if (!saveBtn) return false;

        // Show loading
        const originalHtml = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            // Collect data
            const data = this.collectRowData(row);

            // Save to server
            const savedPatient = await this.saveToServer(data);

            if (savedPatient) {
                this.markRowSaved(row, savedPatient);
                return true;
            } else {
                throw new Error('Failed to save patient');
            }
        } catch (error) {
            console.error('Save error:', error);
            alert('Error saving patient: ' + error.message);
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalHtml;
            return false;
        }
    }

    /**
     * Collect data from a row
     */
    collectRowData(row) {
        const inputs = row.querySelectorAll('[name]');
        const data = {};

        inputs.forEach(input => {
            if (input.value && input.value.trim()) {
                data[input.name] = input.value.trim();
            }
        });

        return data;
    }

    /**
     * Save patient data to server
     */
    async saveToServer(data) {
        try {
            const response = await fetch('/api/v1/patient/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrf
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Server error: ${response.status}`);
            }

            const result = await response.json();
            return Array.isArray(result) ? result[0] : result;
        } catch (error) {
            console.error('API error:', error);
            throw error;
        }
    }

    /**
     * Mark a row as saved
     */
    markRowSaved(row, patientData) {
        row.classList.add('saved');

        // Update ID display
        const idCell = row.querySelector('.patient-row-id');
        if (idCell) {
            idCell.innerHTML = `<span class="patient-id">#${patientData.id}</span>`;
        }

        // Disable all inputs
        const inputs = row.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.disabled = true;
            input.readOnly = true;
        });

        // Clear validation state
        clearRowValidation(row);

        // Remove action buttons
        const actions = row.querySelector('.row-actions');
        if (actions) {
            actions.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill"></i> Saved</span>';
        }
    }

    /**
     * Attach event listeners to a row
     */
    attachEventListeners(row) {
        // Save button
        const saveBtn = row.querySelector('[data-action="save"]');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const rowId = row.dataset.rowId;
                await this.saveRow(rowId);
            });
        }

        // Remove button
        const removeBtn = row.querySelector('[data-action="remove"]');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                const rowId = row.dataset.rowId;
                this.removeRow(rowId);
            });
        }

        // Prevent Enter key from submitting form
        const textInputs = row.querySelectorAll('input[type="text"], input[type="date"]');
        textInputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.moveToNextInput(row, e.target);
                }
            });
        });

        // Real-time validation on blur
        const validateInputs = row.querySelectorAll('[data-validate]');
        validateInputs.forEach(input => {
            input.addEventListener('blur', () => {
                validateRow(row);
            });

            // Clear invalid state on input
            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    input.classList.remove('is-invalid');
                    const container = input.closest('.input-with-validation');
                    if (container) {
                        const feedback = container.querySelector('.invalid-feedback');
                        if (feedback) feedback.textContent = '';
                    }
                }
            });
        });
    }

    /**
     * Move focus to next input in row
     */
    moveToNextInput(row, currentInput) {
        const allInputs = Array.from(row.querySelectorAll('input:not([disabled]), select:not([disabled]), textarea:not([disabled])'));
        const currentIndex = allInputs.indexOf(currentInput);

        if (currentIndex >= 0 && currentIndex < allInputs.length - 1) {
            allInputs[currentIndex + 1].focus();
        }
    }

    /**
     * Get all unsaved rows
     */
    getUnsavedRows() {
        return Array.from(this.container.querySelectorAll('.patient-row:not(.saved)'));
    }

    /**
     * Get all saved rows
     */
    getSavedRows() {
        return Array.from(this.container.querySelectorAll('.patient-row.saved'));
    }
}
