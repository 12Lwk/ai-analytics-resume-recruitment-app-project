// Resume Upload Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeUploadArea();
    initializeFormValidation();
});

let selectedFiles = [];

function initializeUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');

    // Click to browse files
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // Form submission
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', function(e) {
        if (selectedFiles.length === 0) {
            e.preventDefault();
            alert('Please select at least one file to upload.');
            return;
        }

        // Show processing modal
        showProcessingModal();
    });
}

function handleFiles(files) {
    const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
    const maxSize = 5 * 1024 * 1024; // 5MB

    Array.from(files).forEach(file => {
        // Check file type
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            alert(`File "${file.name}" has an unsupported format. Please use PDF, DOC, DOCX, or TXT files.`);
            return;
        }

        // Check file size
        if (file.size > maxSize) {
            alert(`File "${file.name}" is too large. Maximum file size is 5MB.`);
            return;
        }

        // Check for duplicates
        if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            alert(`File "${file.name}" is already selected.`);
            return;
        }

        selectedFiles.push(file);
    });

    updateFilesList();
    updateUploadButton();
}

function updateFilesList() {
    const selectedFilesDiv = document.getElementById('selected-files');
    const filesList = document.getElementById('files-list');

    if (selectedFiles.length === 0) {
        selectedFilesDiv.style.display = 'none';
        return;
    }

    selectedFilesDiv.style.display = 'block';
    filesList.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';

        const fileExtension = file.name.split('.').pop().toLowerCase();
        const fileIcon = getFileIcon(fileExtension);

        fileItem.innerHTML = `
            <div class="file-info-item">
                <div class="file-icon">
                    <i class="bi ${fileIcon}"></i>
                </div>
                <div class="file-details">
                    <h6>${file.name}</h6>
                    <p>${formatFileSize(file.size)} • ${fileExtension.toUpperCase()}</p>
                </div>
            </div>
            <button type="button" class="remove-file" onclick="removeFile(${index})" title="Remove file">
                <i class="bi bi-x-lg"></i>
            </button>
        `;

        filesList.appendChild(fileItem);
    });
}

function getFileIcon(extension) {
    const icons = {
        'pdf': 'bi-file-earmark-pdf',
        'doc': 'bi-file-earmark-word',
        'docx': 'bi-file-earmark-word',
        'txt': 'bi-file-earmark-text'
    };
    return icons[extension] || 'bi-file-earmark';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFilesList();
    updateUploadButton();

    // Clear file input
    const fileInput = document.getElementById('file-input');
    fileInput.value = '';
}

function clearFiles() {
    selectedFiles = [];
    updateFilesList();
    updateUploadButton();

    // Clear file input
    const fileInput = document.getElementById('file-input');
    fileInput.value = '';

    // Clear form fields
    document.querySelector('input[name="job_title"]').value = '';
    document.querySelector('select[name="department"]').value = '';
    document.querySelector('input[name="tags"]').value = '';
}

function updateUploadButton() {
    const uploadBtn = document.getElementById('upload-btn');
    uploadBtn.disabled = selectedFiles.length === 0;

    if (selectedFiles.length > 0) {
        uploadBtn.innerHTML = `
            <i class="bi bi-upload"></i>
            Upload & Process (${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''})
        `;
    } else {
        uploadBtn.innerHTML = `
            <i class="bi bi-upload"></i>
            Upload & Process
        `;
    }
}

function initializeFormValidation() {
    // Real-time validation for tags input
    const tagsInput = document.querySelector('input[name="tags"]');
    if (tagsInput) {
        tagsInput.addEventListener('input', function() {
            // Remove invalid characters and format tags
            let value = this.value;
            value = value.replace(/[^a-zA-Z0-9,\s-_]/g, ''); // Allow only alphanumeric, commas, spaces, hyphens, underscores
            this.value = value;
        });
    }
}

function showProcessingModal() {
    const modal = new bootstrap.Modal(document.getElementById('processingModal'));
    modal.show();

    // Simulate progress
    const progressBar = document.getElementById('progress-bar');
    let progress = 0;

    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;

        progressBar.style.width = progress + '%';

        if (progress >= 90) {
            clearInterval(interval);
        }
    }, 200);

    // Hide modal after form submission completes
    setTimeout(() => {
        modal.hide();
    }, 3000);
}

// File validation helpers
function validateFileType(file) {
    const allowedTypes = ['application/pdf', 'application/msword',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'text/plain'];
    return allowedTypes.includes(file.type) ||
           file.name.toLowerCase().match(/\.(pdf|doc|docx|txt)$/);
}

function validateFileSize(file, maxSizeMB = 5) {
    return file.size <= maxSizeMB * 1024 * 1024;
}

// Utility functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to messages container or create one
    let messagesContainer = document.querySelector('.messages-container');
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages-container';
        document.querySelector('.resume-upload-container').insertBefore(
            messagesContainer,
            document.querySelector('.upload-layout')
        );
    }

    messagesContainer.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Enhanced drag and drop visual feedback
function enhanceDragDropFeedback() {
    const uploadArea = document.getElementById('upload-area');

    uploadArea.addEventListener('dragenter', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        // Only remove dragover if we're leaving the upload area entirely
        if (!this.contains(e.relatedTarget)) {
            this.classList.remove('dragover');
        }
    });
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', function() {
    enhanceDragDropFeedback();

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + U to open file dialog
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            document.getElementById('file-input').click();
        }

        // Escape to clear files
        if (e.key === 'Escape') {
            clearFiles();
        }
    });
});