document.addEventListener('DOMContentLoaded', function() {
    // Enhanced input focus effects
    const inputs = document.querySelectorAll('.form-input, .form-select');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
            createRipple(this);
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.parentElement.classList.remove('focused');
            }
            validateField(this);
        });
        
        // Check if input has value on page load
        if (input.value !== '') {
            input.parentElement.classList.add('focused');
        }
        
        // Real-time validation with consistent colors
        input.addEventListener('input', function() {
            if (this.value.length > 0) {
                this.style.borderColor = '#667eea';
                this.classList.remove('error');
            } else {
                this.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }
            
            // Real-time password matching
            if (this.name === 'password2') {
                checkPasswordMatch();
            }
        });
    });
    
    // Enhanced form validation
    const form = document.querySelector('form');
    const submitBtn = document.querySelector('.register-btn');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            // Validate all required fields
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    showFieldError(field, 'This field is required');
                    addShakeEffect(field);
                } else {
                    clearFieldError(field);
                }
            });
            
            // Email validation
            const email = form.querySelector('input[name="email"]');
            if (email.value && !isValidEmail(email.value)) {
                isValid = false;
                showFieldError(email, 'Please enter a valid email address');
                addShakeEffect(email);
            }
            
            // Password validation
            const password1 = form.querySelector('input[name="password1"]');
            const password2 = form.querySelector('input[name="password2"]');
            
            if (password1.value && password1.value.length < 8) {
                isValid = false;
                showFieldError(password1, 'Password must be at least 8 characters');
                addShakeEffect(password1);
            }
            
            if (password1.value !== password2.value) {
                isValid = false;
                showFieldError(password2, 'Passwords do not match');
                addShakeEffect(password2);
            }
            
            if (!isValid) {
                e.preventDefault();
                showError('Please correct the errors above');
                return;
            }
            
            // Add futuristic loading state
            submitBtn.innerHTML = '<span class="loading"></span> Creating Account...';
            submitBtn.disabled = true;
            
            // Add scanning effect
            addScanningEffect();
        });
    }
    
    // Smooth entrance animation
    const container = document.querySelector('.register-container');
    if (container) {
        container.style.opacity = '0';
        container.style.transform = 'translateY(50px) scale(0.95)';
        
        setTimeout(() => {
            container.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0) scale(1)';
        }, 100);
    }
    
    // Auto-hide alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'all 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 8000);
    });
});

function validateField(field) {
    if (field.hasAttribute('required') && !field.value.trim()) {
        field.classList.add('error');
        return false;
    }
    
    if (field.type === 'email' && field.value && !isValidEmail(field.value)) {
        field.classList.add('error');
        return false;
    }
    
    field.classList.remove('error');
    field.classList.add('success');
    return true;
}

function checkPasswordMatch() {
    const password1 = document.querySelector('input[name="password1"]');
    const password2 = document.querySelector('input[name="password2"]');
    
    if (password1.value && password2.value) {
        if (password1.value === password2.value) {
            password2.classList.remove('error');
            password2.classList.add('success');
        } else {
            password2.classList.remove('success');
            password2.classList.add('error');
        }
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showFieldError(field, message) {
    field.classList.add('error');
    
    // Remove existing error message
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = '#ff9999';
    errorDiv.style.fontSize = '11px';
    errorDiv.style.marginTop = '5px';
    errorDiv.textContent = message;
    
    field.parentElement.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('error');
    const errorDiv = field.parentElement.querySelector('.field-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function createRipple(element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = '50%';
    ripple.style.top = '50%';
    ripple.style.transform = 'translate(-50%, -50%) scale(0)';
    ripple.style.position = 'absolute';
    ripple.style.borderRadius = '50%';
    ripple.style.background = 'rgba(102, 126, 234, 0.3)';
    ripple.style.pointerEvents = 'none';
    ripple.style.animation = 'ripple 0.6s ease-out';
    
    element.style.position = 'relative';
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function addShakeEffect(element) {
    element.style.animation = 'shake 0.5s ease-in-out';
    setTimeout(() => {
        element.style.animation = '';
    }, 500);
}

function addScanningEffect() {
    const scanner = document.createElement('div');
    scanner.style.position = 'fixed';
    scanner.style.top = '0';
    scanner.style.left = '0';
    scanner.style.width = '100%';
    scanner.style.height = '3px';
    scanner.style.background = 'linear-gradient(90deg, transparent, #667eea, transparent)';
    scanner.style.zIndex = '9999';
    scanner.style.animation = 'scan 2s ease-in-out';
    
    document.body.appendChild(scanner);
    
    setTimeout(() => {
        scanner.remove();
    }, 2000);
}

function createParticle(x, y) {
    const particle = document.createElement('div');
    particle.style.position = 'fixed';
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';
    particle.style.width = '4px';
    particle.style.height = '4px';
    particle.style.background = 'rgba(255, 255, 255, 0.6)';
    particle.style.borderRadius = '50%';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '1000';
    particle.style.animation = 'particle 1s ease-out forwards';
    
    document.body.appendChild(particle);
    
    setTimeout(() => {
        particle.remove();
    }, 1000);
}

function showError(message) {
    // Remove existing error alerts
    const existingAlerts = document.querySelectorAll('.alert-danger');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new error alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${message}`;
    
    // Insert before form
    const form = document.querySelector('form');
    form.parentNode.insertBefore(alert, form);
    
    // Entrance animation
    alert.style.transform = 'translateX(-100%)';
    alert.style.opacity = '0';
    setTimeout(() => {
        alert.style.transition = 'all 0.3s ease';
        alert.style.transform = 'translateX(0)';
        alert.style.opacity = '1';
    }, 10);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.style.transition = 'all 0.3s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(100%)';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: translate(-50%, -50%) scale(2);
            opacity: 0;
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    @keyframes scan {
        0% { transform: translateY(-100vh); }
        100% { transform: translateY(100vh); }
    }
`;
document.head.appendChild(style);
