/**
 * Modal Controller
 * Utility for showing confirmation modals
 */

/**
 * Show a confirmation modal
 * @param {object} options - Modal configuration
 * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
 */
export function showConfirmModal(options = {}) {
    const {
        title = 'Confirm Action',
        message = 'Are you sure you want to proceed?',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        confirmClass = 'btn-danger',
        onConfirm = null,
        onCancel = null
    } = options;

    return new Promise((resolve) => {
        // Create modal ID
        const modalId = `confirmModal-${Date.now()}`;

        // Create modal element
        const modalElement = document.createElement('div');
        modalElement.className = 'modal fade';
        modalElement.id = modalId;
        modalElement.setAttribute('tabindex', '-1');
        modalElement.setAttribute('aria-hidden', 'true');

        modalElement.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${escapeHtml(title)}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p class="mb-0">${escapeHtml(message)}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              ${escapeHtml(cancelText)}
            </button>
            <button type="button" class="btn ${confirmClass}" id="${modalId}-confirm">
              ${escapeHtml(confirmText)}
            </button>
          </div>
        </div>
      </div>
    `;

        // Append to body
        document.body.appendChild(modalElement);

        // Initialize Bootstrap modal
        const modal = new bootstrap.Modal(modalElement);

        // Confirm button handler
        const confirmBtn = modalElement.querySelector(`#${modalId}-confirm`);
        confirmBtn.addEventListener('click', () => {
            if (onConfirm) onConfirm();
            modal.hide();
            resolve(true);
        });

        // Cancel/close handlers
        const handleCancel = () => {
            if (onCancel) onCancel();
            resolve(false);
        };

        modalElement.addEventListener('hidden.bs.modal', handleCancel);

        // Cleanup after modal is hidden
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        }, { once: true });

        // Show modal
        modal.show();
    });
}

/**
 * Show a delete confirmation modal
 * @param {string} itemName - Name of item to delete
 * @returns {Promise<boolean>}
 */
export async function confirmDelete(itemName) {
    return showConfirmModal({
        title: 'Confirm Deletion',
        message: `Are you sure you want to delete "${itemName}"? This action cannot be undone.`,
        confirmText: 'Delete',
        confirmClass: 'btn-danger'
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
