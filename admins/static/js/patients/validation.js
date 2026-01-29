/**
 * Patient Form Validation Module
 * Provides comprehensive client-side validation for patient data
 */

export const validationRules = {
    name: {
        minLength: 2,
        maxLength: 50,
        pattern: /^[A-Za-z\s'-]+$/,
        message: '2-50 letters, spaces, hyphens, apostrophes only'
    },
    dob: {
        validator: (value) => {
            if (!value) return { valid: true };

            const date = new Date(value);
            const today = new Date();
            const maxAge = new Date();
            maxAge.setFullYear(today.getFullYear() - 150);

            if (date >= today) {
                return { valid: false, message: 'Date of birth cannot be in the future' };
            }

            if (date < maxAge) {
                return { valid: false, message: 'Date of birth cannot be more than 150 years ago' };
            }

            return { valid: true };
        }
    },
    notes: {
        maxLength: 500,
        message: 'Notes cannot exceed 500 characters'
    }
};

/**
 * Validate a single field
 */
export function validateField(fieldType, value, rules = validationRules) {
    const rule = rules[fieldType];

    // No rule or no value
    if (!rule || !value) {
        return { valid: true };
    }

    // Custom validator function
    if (rule.validator) {
        return rule.validator(value);
    }

    // Min length check
    if (rule.minLength && value.length < rule.minLength) {
        return { valid: false, message: rule.message };
    }

    // Max length check
    if (rule.maxLength && value.length > rule.maxLength) {
        return { valid: false, message: rule.message };
    }

    // Pattern check
    if (rule.pattern && !rule.pattern.test(value)) {
        return { valid: false, message: rule.message };
    }

    return { valid: true };
}

/**
 * Validate an entire patient row
 * Returns: { isValid: boolean, hasName: boolean, errors: array }
 */
export function validateRow(rowElement) {
    const inputs = rowElement.querySelectorAll('[data-validate]');
    let isValid = true;
    let hasName = false;
    const errors = [];

    inputs.forEach(input => {
        const fieldType = input.dataset.validate;
        const result = validateField(fieldType, input.value);

        // Update UI
        updateValidationUI(input, result);

        // Track validity
        if (!result.valid) {
            isValid = false;
            errors.push({ field: input.name, message: result.message });
        }

        // Check if at least one name is provided
        if ((input.name === 'firstName' || input.name === 'lastName') && input.value.trim()) {
            hasName = true;
        }
    });

    return { isValid, hasName, errors };
}

/**
 * Update validation UI for an input
 * Only uses validation icon, no is-valid class
 */
function updateValidationUI(input, result) {
    const container = input.closest('.input-with-validation');
    if (!container) return;

    const icon = container.querySelector('.validation-icon');
    const feedback = container.querySelector('.invalid-feedback');

    if (result.valid && input.value) {
        // Valid state - show only icon, no class on input
        input.classList.remove('is-invalid');
        container.classList.add('has-validation');

        if (icon) {
            icon.innerHTML = '<i class="bi bi-check-circle text-success"></i>';
        }

        if (feedback) {
            feedback.textContent = '';
            feedback.style.display = 'none';
        }
    } else if (!result.valid) {
        // Invalid state - add class for red border and show error
        input.classList.add('is-invalid');
        container.classList.add('has-validation');

        if (icon) {
            icon.innerHTML = '<i class="bi bi-x-circle text-danger"></i>';
        }

        if (feedback) {
            feedback.textContent = result.message || 'Invalid input';
            feedback.style.display = 'block';
        }
    } else {
        // No value - clear everything
        input.classList.remove('is-invalid');
        container.classList.remove('has-validation');

        if (icon) {
            icon.innerHTML = '';
        }

        if (feedback) {
            feedback.textContent = '';
            feedback.style.display = 'none';
        }
    }
}

/**
 * Clear all validation from a row
 */
export function clearRowValidation(rowElement) {
    const inputs = rowElement.querySelectorAll('[data-validate]');
    inputs.forEach(input => {
        input.classList.remove('is-invalid');
        const container = input.closest('.input-with-validation');
        if (container) {
            container.classList.remove('has-validation');
            const icon = container.querySelector('.validation-icon');
            const feedback = container.querySelector('.invalid-feedback');
            if (icon) icon.innerHTML = '';
            if (feedback) {
                feedback.textContent = '';
                feedback.style.display = 'none';
            }
        }
    });
}
