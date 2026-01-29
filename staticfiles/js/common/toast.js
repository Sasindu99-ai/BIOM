/**
 * Toast Notification System
 * Professional toast notifications with theme support
 */

/**
 * Show a toast notification
 * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
 * @param {string} message - Message to display
 * @param {number} duration - Duration in milliseconds (default: 5000)
 * @param {object} options - Additional options
 */
export function showToast(type, message, duration = 5000, options = {}) {
    const toastContainer = document.getElementById('toastContainer');

    if (!toastContainer) {
        console.error('Toast container not found. Make sure to include toast_container component in your template.');
        return;
    }

    const toastId = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const toast = document.createElement('div');

    // Set Bootstrap toast classes
    toast.className = `toast align-items-center border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.id = toastId;

    // Get theme-aware colors
    const colors = getToastColors(type);

    // Build toast HTML
    toast.innerHTML = `
    <div class="d-flex" style="background-color: ${colors.bg}; color: ${colors.text}; border-radius: 0.375rem;">
      <div class="toast-body d-flex align-items-center">
        <i class="bi bi-${getIcon(type)} me-2" style="font-size: 1.25rem;"></i>
        <span>${escapeHtml(message)}</span>
      </div>
      <button type="button" 
              class="btn-close me-2 m-auto" 
              data-bs-dismiss="toast" 
              aria-label="Close"
              style="filter: brightness(0) invert(1);"></button>
    </div>
  `;

    toastContainer.appendChild(toast);

    // Initialize Bootstrap toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });

    // Show the toast
    bsToast.show();

    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });

    // Return toast ID for potential manipulation
    return toastId;
}

/**
 * Get icon for toast type
 */
function getIcon(type) {
    const icons = {
        success: 'check-circle-fill',
        error: 'x-circle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill'
    };
    return icons[type] || 'info-circle-fill';
}

/**
 * Get theme-aware colors for toast
 */
function getToastColors(type) {
    const theme = document.documentElement.getAttribute('data-color-theme');
    const isDark = theme !== 'light';

    const colors = {
        success: {
            bg: isDark ? '#065f46' : '#10b981',
            text: '#ffffff'
        },
        error: {
            bg: isDark ? '#991b1b' : '#ef4444',
            text: '#ffffff'
        },
        warning: {
            bg: isDark ? '#92400e' : '#f59e0b',
            text: '#ffffff'
        },
        info: {
            bg: isDark ? '#1e40af' : '#3b82f6',
            text: '#ffffff'
        }
    };

    return colors[type] || colors.info;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Convenience methods
 */
export const toast = {
    success: (message, duration) => showToast('success', message, duration),
    error: (message, duration) => showToast('error', message, duration),
    warning: (message, duration) => showToast('warning', message, duration),
    info: (message, duration) => showToast('info', message, duration)
};

/**
 * Get CSRF token from anywhere in the page
 */
export function getCsrfToken() {
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
}
