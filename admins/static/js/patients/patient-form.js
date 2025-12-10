/**
 * Patient Form Main Controller
 * Coordinates the patient add form interactions
 */

import { RowManager } from './row-manager.js';
import { validateRow } from './validation.js';

// Get CSRF token
const getCsrfToken = () => {
    // Try from meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) return metaTag.content;

    // Try from input field
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;

    // Try from cookie
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

    return cookieValue || '';
};

// Initialize when DOM is ready
function initPatientForm() {
    const csrf = getCsrfToken();

    if (!csrf) {
        console.error('CSRF token not found');
        return;
    }

    // Initialize row manager
    const rowManager = new RowManager('patientsContainer', 'patientRowTemplate', csrf);

    // Add initial row
    rowManager.addRow();

    // Add Row button
    const addRowBtn = document.getElementById('addRowBtn');
    if (addRowBtn) {
        addRowBtn.addEventListener('click', () => {
            rowManager.addRow();
        });
    }

    // Form submission (Save All)
    const form = document.getElementById('addPatientForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleSaveAll(rowManager);
        });
    }

    // Keyboard shortcut (Ctrl+N to add row)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            rowManager.addRow();
        }
    });
}

/**
 * Handle Save All action
 */
async function handleSaveAll(rowManager) {
    const saveBtn = document.getElementById('saveAllBtn');
    if (!saveBtn) return;

    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    try {
        const unsavedRows = rowManager.getUnsavedRows();

        if (unsavedRows.length === 0) {
            alert('No unsaved patients to save');
            return;
        }

        // Validate all rows first
        const validRows = [];
        const invalidRows = [];

        for (const row of unsavedRows) {
            const validation = validateRow(row);
            if (validation.isValid && validation.hasName) {
                validRows.push(row);
            } else {
                invalidRows.push(row);
                row.classList.add('shake');
                setTimeout(() => row.classList.remove('shake'), 400);
            }
        }

        if (invalidRows.length > 0) {
            alert(`${invalidRows.length} patient(s) have validation errors. Please fix them before saving.`);
            return;
        }

        if (validRows.length === 0) {
            alert('No valid patients to save. Please ensure at least one name is provided for each patient.');
            return;
        }

        // Save all valid rows
        let successCount = 0;
        let failCount = 0;

        for (const row of validRows) {
            const rowId = row.dataset.rowId;
            const saved = await rowManager.saveRow(rowId);
            if (saved) {
                successCount++;
            } else {
                failCount++;
            }
        }

        // Show result
        if (successCount > 0) {
            const message = failCount > 0
                ? `Saved ${successCount} patient(s). ${failCount} failed.`
                : `Successfully saved ${successCount} patient(s)!`;
            alert(message);
        } else {
            alert('Failed to save patients. Please try again.');
        }

    } catch (error) {
        console.error('Save All error:', error);
        alert('Error saving patients: ' + error.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPatientForm);
} else {
    initPatientForm();
}
