/**
 * Profile Photo Uploader
 * Handles profile photo selection, immediate upload with progress, and preview
 */

export class ProfileUploader {
    constructor(options = {}) {
        this.photoInput = document.getElementById(options.inputId || 'profilePhotoInput');
        this.preview = document.getElementById(options.previewId || 'photoPreview');
        this.uploadBtn = document.getElementById(options.uploadBtnId || 'uploadPhotoBtn');
        this.removeBtn = document.getElementById(options.removeBtnId || 'removePhotoBtn');
        this.progressCircle = document.getElementById('uploadProgressCircle');
        this.progressRing = document.getElementById('uploadProgressRing');

        this.currentFile = null;
        this.uploadedUrl = null;
        this.isUploading = false;
        this.uploadProgress = 0;
        this.maxSize = options.maxSize || 5 * 1024 * 1024; // 5MB default
        this.defaultImage = options.defaultImage || '/static/img/default-avatar.png';
        this.onUploadStart = options.onUploadStart || null;
        this.onUploadComplete = options.onUploadComplete || null;
        this.onUploadError = options.onUploadError || null;
    }

    init() {
        if (!this.photoInput || !this.preview) {
            console.error('Profile uploader elements not found');
            return;
        }

        // Upload button triggers file input
        this.uploadBtn?.addEventListener('click', () => {
            this.photoInput.click();
        });

        // File selection handler - upload immediately
        this.photoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });

        // Remove button handler
        this.removeBtn?.addEventListener('click', () => {
            this.removePhoto();
        });

        // Drag and drop on preview
        this.preview.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.preview.parentElement.classList.add('drag-over');
        });

        this.preview.addEventListener('dragleave', () => {
            this.preview.parentElement.classList.remove('drag-over');
        });

        this.preview.addEventListener('drop', (e) => {
            e.preventDefault();
            this.preview.parentElement.classList.remove('drag-over');

            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });
    }

    async handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            this.showError('Please select an image file');
            return;
        }

        // Validate file size
        if (file.size > this.maxSize) {
            const sizeMB = (this.maxSize / 1024 / 1024).toFixed(1);
            this.showError(`Image must be less than ${sizeMB}MB`);
            return;
        }

        // Show preview immediately
        const reader = new FileReader();
        reader.onload = (e) => {
            this.preview.src = e.target.result;
        };
        reader.readAsDataURL(file);

        this.currentFile = file;

        // Upload immediately
        await this.uploadPhoto();
    }

    async uploadPhoto() {
        if (!this.currentFile || this.isUploading) {
            return this.uploadedUrl;
        }

        this.isUploading = true;
        this.uploadProgress = 0;

        // Notify upload start
        if (this.onUploadStart) {
            this.onUploadStart();
        }

        // Show progress ring
        if (this.progressCircle) {
            this.progressCircle.style.display = 'block';
        }

        const formData = new FormData();
        formData.append('file', this.currentFile);

        // Get CSRF token
        const csrfToken = this.getCsrfToken();

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            // Progress tracking
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    this.uploadProgress = (e.loaded / e.total) * 100;
                    this.updateProgressRing(this.uploadProgress);
                }
            });

            // Upload complete
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const result = JSON.parse(xhr.responseText);
                        this.uploadedUrl = result.file_url || result.url;

                        // Update to complete state (blue border)
                        this.updateProgressRing(100, true);
                        this.isUploading = false;

                        // Show remove button
                        if (this.removeBtn) {
                            this.removeBtn.style.display = 'inline-block';
                        }

                        // Notify completion
                        if (this.onUploadComplete) {
                            this.onUploadComplete(this.uploadedUrl);
                        }

                        resolve(this.uploadedUrl);
                    } catch (error) {
                        this.handleUploadError('Invalid server response');
                        reject(error);
                    }
                } else {
                    this.handleUploadError('Upload failed');
                    reject(new Error('Upload failed'));
                }
            });

            // Upload error
            xhr.addEventListener('error', () => {
                this.handleUploadError('Network error during upload');
                reject(new Error('Network error'));
            });

            // Send request
            xhr.open('POST', '/api/v1/media/upload-stream');
            xhr.setRequestHeader('X-CSRFToken', csrfToken);
            xhr.send(formData);
        });
    }

    updateProgressRing(progress, isComplete = false) {
        if (!this.progressRing) return;

        const radius = 88; // Adjust based on your SVG size
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (progress / 100) * circumference;

        this.progressRing.style.strokeDashoffset = offset;

        // Change color when complete
        if (isComplete) {
            this.progressRing.style.stroke = '#3b82f6'; // Solid blue
            this.progressRing.style.strokeWidth = '4';
        } else {
            this.progressRing.style.stroke = '#60a5fa'; // Light blue during upload
            this.progressRing.style.strokeWidth = '6';
        }
    }

    handleUploadError(message) {
        this.isUploading = false;
        this.uploadProgress = 0;

        // Hide progress ring
        if (this.progressCircle) {
            this.progressCircle.style.display = 'none';
        }

        // Reset preview
        this.preview.src = this.defaultImage;
        this.photoInput.value = '';
        this.currentFile = null;

        this.showError(message);

        if (this.onUploadError) {
            this.onUploadError(message);
        }
    }

    removePhoto() {
        this.preview.src = this.defaultImage;
        this.photoInput.value = '';
        this.currentFile = null;
        this.uploadedUrl = null;
        this.isUploading = false;
        this.uploadProgress = 0;

        // Hide remove button and progress
        if (this.removeBtn) {
            this.removeBtn.style.display = 'none';
        }

        if (this.progressCircle) {
            this.progressCircle.style.display = 'none';
        }

        // Notify removal
        if (this.onUploadComplete) {
            this.onUploadComplete(null);
        }
    }

    getPhotoUrl() {
        return this.uploadedUrl;
    }

    hasPhoto() {
        return this.uploadedUrl !== null;
    }

    isCurrentlyUploading() {
        return this.isUploading;
    }

    showError(message) {
        // Use the toast system if available
        if (window.showToast) {
            window.showToast('error', message);
        } else {
            alert(message);
        }
    }

    getCsrfToken() {
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
}
