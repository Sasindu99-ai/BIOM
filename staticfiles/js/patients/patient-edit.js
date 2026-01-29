/**
 * Patient Edit Form Controller
 * Loads patient data, manages form, and handles updates
 * Uses UTIL.import() for dynamic module loading
 */

(async function () {
    // Dynamic import using UTIL
    const profileUploadModule = await UTIL.import('/static/js/patients/profile-upload.js', 1);
    const ProfileUploader = profileUploadModule.ProfileUploader;

    const patientId = document.getElementById('patientId')?.value;
    let currentPhotoUrl = null;
    let photoChanged = false; // Track if photo was changed
    let uploader = null;

    // Get CSRF token
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content ||
        document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
        '';

    /**
     * Load patient data from API
     */
    async function loadPatientData() {
        try {
            const response = await fetch(`/api/v1/patient/${patientId}`, {
                headers: { 'X-CSRFToken': csrf }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const patient = (await response.json())[0];

            // Update header with patient name
            const fullName = patient.fullName;
            const headerElement = document.getElementById('patientNameHeader');
            if (headerElement) {
                headerElement.textContent = ` - ${fullName}`;
            }

            // Pre-fill form fields
            document.getElementById('firstName').value = patient.firstName || '';
            document.getElementById('lastName').value = patient.lastName || '';
            document.getElementById('dateOfBirth').value = patient.dateOfBirth || '';
            document.getElementById('gender').value = patient.gender || '';
            document.getElementById('notes').value = patient.notes || '';

            // Store photo URL for later
            currentPhotoUrl = patient.photo;

            // Show form, hide loading
            document.getElementById('loadingState').style.display = 'none';
            document.getElementById('editPatientForm').style.display = 'block';

            // Set existing photo after uploader is ready
            if (currentPhotoUrl && uploader) {
                setTimeout(() => {
                    uploader.setExistingPhoto(currentPhotoUrl);
                }, 100);
            }

        } catch (error) {
            console.error('Failed to load patient:', error);
            document.getElementById('loadingState').innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Failed to load patient data: ${error.message}
                </div>
                <a href="/dashboard/patients/" class="btn btn-secondary">
                    <i class="bi bi-arrow-left me-1"></i> Back to List
                </a>
            `;
        }
    }

    /**
     * Handle form submission
     */
    async function handleSubmit(e) {
        e.preventDefault();

        const saveBtn = document.getElementById('saveBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

        try {
            // Get form data
            const formData = {
                firstName: document.getElementById('firstName').value.trim(),
                lastName: document.getElementById('lastName').value.trim(),
                dateOfBirth: document.getElementById('dateOfBirth').value || null,
                gender: document.getElementById('gender').value || null,
                notes: document.getElementById('notes').value.trim() || null,
            };

            // Handle photo field
            if (photoChanged) {
                if (uploader) {
                    const photoUrl = uploader.getPhotoUrl();
                    // If photoUrl is null, user removed the photo, so send null to delete it
                    formData.photo = photoUrl; // Will be null if removed, or new URL if uploaded
                }
            }
            // If photoChanged is false, don't include photo field at all (no changes)

            // Validate
            if (!formData.firstName && !formData.lastName) {
                new UTIL.Toast().ok('Please provide at least a first name or last name', 'Required Field', 'warning');
                return;
            }

            // Send update request
            const response = await fetch(`/api/v1/patient/${patientId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                new UTIL.Toast().ok('Patient updated successfully!', 'Success', 'success');
                // Redirect to list
                setTimeout(() => {
                    window.location.href = '/dashboard/patients/';
                }, 500);
            } else {
                throw new Error(result.message || 'Failed to update patient');
            }

        } catch (error) {
            console.error('Update error:', error);
            new UTIL.Toast().ok('Error updating patient: ' + error.message, 'Update Error', 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }

    /**
     * Initialize edit form
     */
    function init() {
        if (!patientId) {
            console.error('No patient ID provided');
            return;
        }

        if (!csrf) {
            console.error('CSRF token not found');
            return;
        }

        // Initialize photo uploader
        uploader = new ProfileUploader({
            onUploadStart: () => {
                document.getElementById('saveBtn').disabled = true;
            },
            onUploadComplete: (url) => {
                document.getElementById('saveBtn').disabled = false;
                currentPhotoUrl = url; // Will be null if removed
                photoChanged = true; // Mark photo as changed (uploaded or removed)
            },
            onUploadFail: () => {
                document.getElementById('saveBtn').disabled = false;
            }
        });
        uploader.init(); // Initialize the uploader

        // Load patient data
        loadPatientData();

        // Form submission
        const form = document.getElementById('editPatientForm');
        if (form) {
            form.addEventListener('submit', handleSubmit);
        }

        // Unsaved changes warning
        let formChanged = false;
        if (form) {
            form.addEventListener('input', () => {
                formChanged = true;
            });
        }

        window.addEventListener('beforeunload', (e) => {
            if (formChanged) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
