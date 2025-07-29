// JavaScript for DANDI External Resources form

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation
    const form = document.getElementById('resourceForm');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }

    // ORCID validation
    const orcidInput = document.getElementById('contributor_identifier');
    if (orcidInput) {
        orcidInput.addEventListener('blur', function() {
            const orcidValue = this.value.trim();
            if (orcidValue && !isValidORCID(orcidValue)) {
                this.setCustomValidity('Please enter a valid ORCID URL (e.g., https://orcid.org/0000-0000-0000-0000)');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // URL validation for resource URL
    const resourceUrlInput = document.getElementById('resource_url');
    if (resourceUrlInput) {
        resourceUrlInput.addEventListener('blur', function() {
            const urlValue = this.value.trim();
            if (urlValue && !isValidURL(urlValue)) {
                this.setCustomValidity('Please enter a valid URL starting with http:// or https://');
            } else {
                this.setCustomValidity('');
            }
        });
    }

    // Auto-format ORCID input
    if (orcidInput) {
        orcidInput.addEventListener('input', function() {
            let value = this.value.trim();
            
            // If user enters just the numeric part, auto-format to full ORCID URL
            const numericPattern = /^\d{4}-?\d{4}-?\d{4}-?\d{3}[\dX]?$/;
            if (numericPattern.test(value.replace(/-/g, ''))) {
                // Remove existing dashes and format
                const cleaned = value.replace(/-/g, '');
                if (cleaned.length >= 15) {
                    const formatted = cleaned.substring(0, 4) + '-' + 
                                    cleaned.substring(4, 8) + '-' + 
                                    cleaned.substring(8, 12) + '-' + 
                                    cleaned.substring(12, 16);
                    this.value = 'https://orcid.org/' + formatted;
                }
            }
        });
    }

    // Form auto-save to localStorage (optional feature)
    const formInputs = form ? form.querySelectorAll('input, select, textarea') : [];
    formInputs.forEach(input => {
        // Load saved value
        const savedValue = localStorage.getItem('dandi_form_' + input.name);
        if (savedValue && input.type !== 'submit') {
            input.value = savedValue;
        }

        // Save on change
        input.addEventListener('change', function() {
            if (this.type !== 'submit') {
                localStorage.setItem('dandi_form_' + this.name, this.value);
            }
        });
    });
});

// Clear form function
function clearForm() {
    const form = document.getElementById('resourceForm');
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
        
        // Clear localStorage
        const formInputs = form.querySelectorAll('input, select, textarea');
        formInputs.forEach(input => {
            localStorage.removeItem('dandi_form_' + input.name);
        });
        
        // Clear custom validity messages
        formInputs.forEach(input => {
            input.setCustomValidity('');
        });
    }
}

// ORCID validation function
function isValidORCID(orcid) {
    const orcidPattern = /^https:\/\/orcid\.org\/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/;
    return orcidPattern.test(orcid);
}

// URL validation function
function isValidURL(url) {
    const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/;
    return urlPattern.test(url);
}

// Show loading state on form submission
function showLoadingState() {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    }
}

// Reset loading state
function resetLoadingState() {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'SAVE ITEM <i class="fas fa-arrow-right ms-1"></i>';
    }
}

// Add loading state to form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('resourceForm');
    if (form) {
        form.addEventListener('submit', function() {
            if (form.checkValidity()) {
                showLoadingState();
            }
        });
    }
});

// Resource management functions (for future enhancement)
function removeResource(resourceId) {
    if (confirm('Are you sure you want to remove this resource?')) {
        // Implementation for removing resources
        console.log('Removing resource:', resourceId);
    }
}

function editResource(resourceId) {
    // Implementation for editing resources
    console.log('Editing resource:', resourceId);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to submit form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const form = document.getElementById('resourceForm');
        if (form) {
            form.dispatchEvent(new Event('submit', { cancelable: true }));
        }
    }
    
    // Escape to clear form
    if (event.key === 'Escape') {
        clearForm();
    }
});
