// Settings page functionality

// Tab switching and initialization
document.addEventListener('DOMContentLoaded', function() {
    const navItems = document.querySelectorAll('.nav-item[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active class from all nav items and tab contents
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));

            // Add active class to clicked nav item
            this.classList.add('active');

            // Show corresponding tab content
            const tabId = this.getAttribute('data-tab');
            const targetTab = document.getElementById(tabId);
            if (targetTab) {
                targetTab.classList.add('active');
            }
        });
    });

    // Initialize auto-detection features
    initializeAutoDetection();
    setupRoleCapitalization();
});

// Photo upload functionality
function handlePhotoUpload() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.querySelector('.profile-photo img');
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    };
    
    input.click();
}

// Initialize all auto-detection features
function initializeAutoDetection() {
    autoDetectLocation();
    autoDetectDeviceInfo();
    autoDetectBrowserInfo();
}

// Auto-detect location functionality (automatic on page load)
function autoDetectLocation() {
    const addressField = document.getElementById('address-field');
    const locationBadge = document.querySelector('.form-group:has(#address-field) .auto-detect-badge');

    if (!navigator.geolocation) {
        addressField.value = 'Geolocation not supported by this browser';
        if (locationBadge) {
            locationBadge.textContent = 'Not available';
            locationBadge.style.background = '#ef4444';
        }
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            // Use reverse geocoding to get readable address
            reverseGeocode(lat, lng, function(address) {
                addressField.value = address || `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                if (locationBadge) {
                    locationBadge.textContent = 'Detected ✓';
                    locationBadge.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
                    locationBadge.style.animation = 'none';
                }
            });
        },
        function(error) {
            addressField.value = `Location error: ${error.message}`;
            if (locationBadge) {
                locationBadge.textContent = 'Failed';
                locationBadge.style.background = '#ef4444';
                locationBadge.style.animation = 'none';
            }
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

// Reverse geocoding function (simplified version)
function reverseGeocode(lat, lng, callback) {
    // For demo purposes, we'll use a simple format
    // In production, you might want to use a proper geocoding service
    const address = `Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    callback(address);
}

// Auto-detect device information
function autoDetectDeviceInfo() {
    const deviceField = document.getElementById('device-info-field');
    const deviceBadge = document.querySelector('.form-group:has(#device-info-field) .auto-detect-badge');

    try {
        const deviceInfo = {
            platform: navigator.userAgentData?.platform || navigator.platform || 'Unknown',
            userAgent: navigator.userAgent || 'Unknown',
            language: navigator.language || 'Unknown',
            cookieEnabled: navigator.cookieEnabled ? 'Yes' : 'No',
            onLine: navigator.onLine ? 'Yes' : 'No',
            screenResolution: `${screen.width}x${screen.height}`,
            colorDepth: `${screen.colorDepth}-bit`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown'
        };

        const deviceText = `Platform: ${deviceInfo.platform}
Language: ${deviceInfo.language}
Screen: ${deviceInfo.screenResolution} (${deviceInfo.colorDepth})
Timezone: ${deviceInfo.timezone}
Cookies: ${deviceInfo.cookieEnabled}
Online: ${deviceInfo.onLine}`;

        deviceField.value = deviceText;

        if (deviceBadge) {
            deviceBadge.textContent = 'Detected ✓';
            deviceBadge.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            deviceBadge.style.animation = 'none';
        }
    } catch (error) {
        deviceField.value = `Device detection error: ${error.message}`;
        if (deviceBadge) {
            deviceBadge.textContent = 'Failed';
            deviceBadge.style.background = '#ef4444';
            deviceBadge.style.animation = 'none';
        }
    }
}

// Auto-detect browser information
function autoDetectBrowserInfo() {
    const browserField = document.getElementById('browser-info-field');
    const browserBadge = document.querySelector('.form-group:has(#browser-info-field) .auto-detect-badge');

    try {
        const browserInfo = getBrowserInfo();
        const browserText = `Browser: ${browserInfo.name} ${browserInfo.version}
Engine: ${browserInfo.engine}
OS: ${browserInfo.os}
Mobile: ${browserInfo.mobile ? 'Yes' : 'No'}
Touch Support: ${browserInfo.touchSupport ? 'Yes' : 'No'}
WebGL: ${browserInfo.webgl ? 'Supported' : 'Not supported'}`;

        browserField.value = browserText;

        if (browserBadge) {
            browserBadge.textContent = 'Detected ✓';
            browserBadge.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            browserBadge.style.animation = 'none';
        }
    } catch (error) {
        browserField.value = `Browser detection error: ${error.message}`;
        if (browserBadge) {
            browserBadge.textContent = 'Failed';
            browserBadge.style.background = '#ef4444';
            browserBadge.style.animation = 'none';
        }
    }
}

// Get detailed browser information
function getBrowserInfo() {
    const ua = navigator.userAgent;
    const info = {
        name: 'Unknown',
        version: 'Unknown',
        engine: 'Unknown',
        os: 'Unknown',
        mobile: /Mobile|Android|iPhone|iPad/.test(ua),
        touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        webgl: !!window.WebGLRenderingContext
    };

    // Detect browser
    if (ua.includes('Chrome') && !ua.includes('Edg')) {
        info.name = 'Chrome';
        info.version = ua.match(/Chrome\/([0-9.]+)/)?.[1] || 'Unknown';
        info.engine = 'Blink';
    } else if (ua.includes('Firefox')) {
        info.name = 'Firefox';
        info.version = ua.match(/Firefox\/([0-9.]+)/)?.[1] || 'Unknown';
        info.engine = 'Gecko';
    } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
        info.name = 'Safari';
        info.version = ua.match(/Version\/([0-9.]+)/)?.[1] || 'Unknown';
        info.engine = 'WebKit';
    } else if (ua.includes('Edg')) {
        info.name = 'Edge';
        info.version = ua.match(/Edg\/([0-9.]+)/)?.[1] || 'Unknown';
        info.engine = 'Blink';
    }

    // Detect OS
    if (ua.includes('Windows')) info.os = 'Windows';
    else if (ua.includes('Mac')) info.os = 'macOS';
    else if (ua.includes('Linux')) info.os = 'Linux';
    else if (ua.includes('Android')) info.os = 'Android';
    else if (ua.includes('iPhone') || ua.includes('iPad')) info.os = 'iOS';

    return info;
}

// Role capitalization functionality
function setupRoleCapitalization() {
    const roleInput = document.querySelector('.role-input');
    if (roleInput && !roleInput.readOnly) {
        roleInput.addEventListener('input', function() {
            const value = this.value;
            if (value.length > 0) {
                this.value = value.charAt(0).toUpperCase() + value.slice(1);
            }
        });

        // Also capitalize on page load if there's existing content
        if (roleInput.value.length > 0) {
            roleInput.value = roleInput.value.charAt(0).toUpperCase() + roleInput.value.slice(1);
        }
    }
}

// Handle responsive sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.settings-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

// Smooth scrolling for anchor links
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href^="#"]')) {
        e.preventDefault();
        const target = document.querySelector(e.target.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
});

// Auto-refresh location and device info periodically (every 5 minutes)
setInterval(function() {
    if (document.getElementById('address-field')) {
        autoDetectLocation();
    }
}, 300000); // 5 minutes

// Update online status in real-time
window.addEventListener('online', function() {
    autoDetectDeviceInfo();
});

window.addEventListener('offline', function() {
    autoDetectDeviceInfo();
});

// Password form functionality
function togglePassword(button) {
    const input = button.parentElement.querySelector('.password-input');
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

function resetPasswordForm() {
    const form = document.getElementById('password-form');
    if (form) {
        form.reset();
        updatePasswordStrength('');
        updatePasswordMatch();
        updatePasswordRequirements('');
    }
}

// Password strength checker
function checkPasswordStrength(password) {
    let score = 0;
    let feedback = [];

    // Length check
    if (password.length >= 8) score += 1;
    else feedback.push('At least 8 characters');

    // Uppercase check
    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push('Uppercase letter');

    // Lowercase check
    if (/[a-z]/.test(password)) score += 1;
    else feedback.push('Lowercase letter');

    // Number check
    if (/\d/.test(password)) score += 1;
    else feedback.push('Number');

    // Special character check
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
    else feedback.push('Special character');

    return { score, feedback };
}

function updatePasswordStrength(password) {
    const strengthElement = document.getElementById('password-strength');
    const strengthText = strengthElement.querySelector('.strength-text');

    if (!password) {
        strengthElement.className = 'password-strength';
        strengthText.textContent = 'Password strength';
        return;
    }

    const { score } = checkPasswordStrength(password);

    // Remove existing strength classes
    strengthElement.classList.remove('strength-weak', 'strength-fair', 'strength-good', 'strength-strong');

    if (score <= 2) {
        strengthElement.classList.add('strength-weak');
        strengthText.textContent = 'Weak password';
    } else if (score === 3) {
        strengthElement.classList.add('strength-fair');
        strengthText.textContent = 'Fair password';
    } else if (score === 4) {
        strengthElement.classList.add('strength-good');
        strengthText.textContent = 'Good password';
    } else {
        strengthElement.classList.add('strength-strong');
        strengthText.textContent = 'Strong password';
    }
}

function updatePasswordMatch() {
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const matchElement = document.getElementById('password-match');

    if (!confirmPassword) {
        matchElement.textContent = '';
        matchElement.className = 'password-match';
        return;
    }

    if (newPassword === confirmPassword) {
        matchElement.textContent = '✓ Passwords match';
        matchElement.className = 'password-match match';
    } else {
        matchElement.textContent = '✗ Passwords do not match';
        matchElement.className = 'password-match no-match';
    }
}

function updatePasswordRequirements(password) {
    const requirements = [
        { id: 'req-length', test: (p) => p.length >= 8 },
        { id: 'req-uppercase', test: (p) => /[A-Z]/.test(p) },
        { id: 'req-lowercase', test: (p) => /[a-z]/.test(p) },
        { id: 'req-number', test: (p) => /\d/.test(p) },
        { id: 'req-special', test: (p) => /[!@#$%^&*(),.?":{}|<>]/.test(p) }
    ];

    requirements.forEach(req => {
        const element = document.getElementById(req.id);
        if (element) {
            if (req.test(password)) {
                element.classList.add('valid');
            } else {
                element.classList.remove('valid');
            }
        }
    });
}

// Initialize password form event listeners
document.addEventListener('DOMContentLoaded', function() {
    const newPasswordInput = document.getElementById('new-password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const passwordForm = document.getElementById('password-form');

    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', function() {
            updatePasswordStrength(this.value);
            updatePasswordRequirements(this.value);
            updatePasswordMatch();
        });
    }

    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', updatePasswordMatch);
    }

    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            if (newPassword !== confirmPassword) {
                e.preventDefault();
                alert('Passwords do not match!');
                return false;
            }

            if (newPassword.length < 8) {
                e.preventDefault();
                alert('Password must be at least 8 characters long!');
                return false;
            }

            // Show loading state
            const submitBtn = document.getElementById('change-password-btn');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Changing Password...';
                submitBtn.disabled = true;
            }
        });
    }
});

// Notification form functionality
function resetNotificationForm() {
    const form = document.getElementById('notifications-form');
    if (form) {
        // Reset all checkboxes to default values
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            // Set default values based on notification type
            if (checkbox.name === 'email_alerts' || checkbox.name === 'application_updates') {
                checkbox.checked = true;
            } else {
                checkbox.checked = false;
            }
        });

        // Reset select fields to defaults
        const emailFrequency = form.querySelector('select[name="email_frequency"]');
        if (emailFrequency) emailFrequency.value = 'daily';

        const timezone = form.querySelector('select[name="timezone_pref"]');
        if (timezone) timezone.value = 'UTC';

        const notificationTime = form.querySelector('input[name="notification_time"]');
        if (notificationTime) notificationTime.value = '09:00';

        const phoneNumber = form.querySelector('input[name="phone_number"]');
        if (phoneNumber) phoneNumber.value = '';
    }
}

// Verification functionality
function downloadBackupCodes() {
    const codes = document.querySelectorAll('.backup-code');
    let content = 'Two-Factor Authentication Backup Codes\n';
    content += '=====================================\n\n';
    content += 'Save these codes in a safe place. Each code can only be used once.\n\n';

    codes.forEach((code, index) => {
        content += `${index + 1}. ${code.textContent}\n`;
    });

    content += '\n\nGenerated on: ' + new Date().toLocaleDateString();

    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function printBackupCodes() {
    const codes = document.querySelectorAll('.backup-code');
    let content = '<html><head><title>Backup Codes</title>';
    content += '<style>';
    content += 'body { font-family: Arial, sans-serif; padding: 20px; }';
    content += 'h1 { color: #333; }';
    content += '.code { display: inline-block; margin: 5px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; }';
    content += '</style></head><body>';
    content += '<h1>Two-Factor Authentication Backup Codes</h1>';
    content += '<p>Save these codes in a safe place. Each code can only be used once.</p>';

    codes.forEach((code, index) => {
        content += `<div class="code">${code.textContent}</div>`;
        if ((index + 1) % 2 === 0) content += '<br>';
    });

    content += '<p style="margin-top: 20px;"><small>Generated on: ' + new Date().toLocaleDateString() + '</small></p>';
    content += '</body></html>';

    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.print();
}

// Enhanced form validation for verification forms
document.addEventListener('DOMContentLoaded', function() {
    // Phone verification form validation
    const phoneForm = document.querySelector('.phone-verification-form');
    if (phoneForm) {
        phoneForm.addEventListener('submit', function(e) {
            const phoneInput = this.querySelector('input[name="phone_number"]');
            const phoneValue = phoneInput.value.trim();

            if (!phoneValue) {
                e.preventDefault();
                alert('Please enter a phone number.');
                phoneInput.focus();
                return false;
            }

            // Basic phone number validation
            const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            if (!phoneRegex.test(phoneValue.replace(/[\s\-\(\)]/g, ''))) {
                e.preventDefault();
                alert('Please enter a valid phone number.');
                phoneInput.focus();
                return false;
            }
        });
    }

    // Identity verification form validation
    const identityForm = document.querySelector('.identity-verification-form');
    if (identityForm) {
        identityForm.addEventListener('submit', function(e) {
            const documentType = this.querySelector('select[name="document_type"]').value;
            const documentNumber = this.querySelector('input[name="document_number"]').value.trim();

            if (!documentType) {
                e.preventDefault();
                alert('Please select a document type.');
                return false;
            }

            if (!documentNumber) {
                e.preventDefault();
                alert('Please enter the document number.');
                return false;
            }

            if (documentNumber.length < 5) {
                e.preventDefault();
                alert('Document number seems too short. Please check and try again.');
                return false;
            }
        });
    }

    // Notification form enhancements
    const notificationForm = document.getElementById('notifications-form');
    if (notificationForm) {
        // Add change listeners to notification toggles
        const toggles = notificationForm.querySelectorAll('input[type="checkbox"]');
        toggles.forEach(toggle => {
            toggle.addEventListener('change', function() {
                // Add visual feedback for changes
                const item = this.closest('.notification-item');
                if (item) {
                    item.style.transform = 'scale(1.02)';
                    setTimeout(() => {
                        item.style.transform = 'scale(1)';
                    }, 200);
                }
            });
        });

        // Form submission with loading state
        notificationForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Saving...';
                submitBtn.disabled = true;
            }
        });
    }

    // Security level calculation
    updateSecurityLevel();
});

function updateSecurityLevel() {
    const levelFill = document.querySelector('.level-fill');
    const levelText = document.querySelector('.level-text');

    if (!levelFill || !levelText) return;

    let score = 0;
    let maxScore = 4;

    // Check email verification (always considered verified for demo)
    score += 1;

    // Check phone verification
    const phoneVerified = document.querySelector('.verification-badge.verified');
    if (phoneVerified) score += 1;

    // Check identity verification
    const identityVerified = document.querySelector('.method-icon.identity-verify + .method-details .verification-badge.verified');
    if (identityVerified) score += 1;

    // Check two-factor authentication
    const twoFactorEnabled = document.querySelector('.method-icon.two-factor + .method-details .verification-badge.verified');
    if (twoFactorEnabled) score += 1;

    const percentage = Math.round((score / maxScore) * 100);
    levelFill.style.width = percentage + '%';

    let levelLabel = 'Weak';
    if (percentage >= 75) levelLabel = 'Strong';
    else if (percentage >= 50) levelLabel = 'Good';
    else if (percentage >= 25) levelLabel = 'Fair';

    levelText.textContent = `${levelLabel} (${percentage}%)`;

    // Update level fill color based on score
    if (percentage >= 75) {
        levelFill.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    } else if (percentage >= 50) {
        levelFill.style.background = 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)';
    } else if (percentage >= 25) {
        levelFill.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
    } else {
        levelFill.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    }
}
