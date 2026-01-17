// State management
let currentCategory = 'forensic';
let evidenceItems = [];
let uploadedFiles = [];

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const submitBtn = document.getElementById('submitBtn');
const evidenceItemsContainer = document.getElementById('evidenceItems');
const categoryButtons = document.querySelectorAll('.category-btn');
const searchInput = document.getElementById('searchInput');
const sortSelect = document.getElementById('sortSelect');
const modal = document.getElementById('modal');
const closeModal = document.querySelector('.close');
const exportBtn = document.getElementById('exportBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setDefaultDate();
    loadFromLocalStorage();
    renderEvidence();
});

// Set default date and time
function setDefaultDate() {
    const now = new Date();
    document.getElementById('dateCollected').valueAsDate = now;
    document.getElementById('timeCollected').value = now.toTimeString().slice(0, 5);
}

// Category selection
categoryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        categoryButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentCategory = btn.dataset.category;
    });
});

// File upload handlers
browseBtn.addEventListener('click', () => {
    fileInput.click();
});

uploadArea.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

// Handle file selection
function handleFiles(files) {
    const fileArray = Array.from(files);
    uploadedFiles = [...uploadedFiles, ...fileArray];
    displaySelectedFiles();
}

// Display selected files
function displaySelectedFiles() {
    if (uploadedFiles.length === 0) return;

    const existingPreview = document.querySelector('.file-preview');
    if (existingPreview) {
        existingPreview.remove();
    }

    const preview = document.createElement('div');
    preview.className = 'file-preview';
    preview.innerHTML = `
        <strong>Selected Files (${uploadedFiles.length}):</strong>
        <div class="file-list">
            ${uploadedFiles.map((file, index) => `
                <div class="file-chip">
                    <span>${file.name}</span>
                    <button onclick="removeFile(${index})">×</button>
                </div>
            `).join('')}
        </div>
    `;

    uploadArea.after(preview);
}

// Remove file from selection
function removeFile(index) {
    uploadedFiles.splice(index, 1);
    displaySelectedFiles();

    if (uploadedFiles.length === 0) {
        const preview = document.querySelector('.file-preview');
        if (preview) preview.remove();
    }
}

// Submit evidence
submitBtn.addEventListener('click', async () => {
    const caseNumber = document.getElementById('caseNumber').value;
    const description = document.getElementById('evidenceDescription').value;
    const collectedBy = document.getElementById('collectedBy').value;
    const dateCollected = document.getElementById('dateCollected').value;
    const timeCollected = document.getElementById('timeCollected').value;
    const location = document.getElementById('location').value;

    // Validation
    if (!description || !collectedBy || !dateCollected || !location) {
        alert('Please fill in all required fields');
        return;
    }

    if (uploadedFiles.length === 0) {
        alert('Please upload at least one file');
        return;
    }

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = 'Uploading...';

    try {
        // If forensic category, send to backend/Snowflake
        if (currentCategory === 'forensic') {
            const formData = new FormData();
            formData.append('caseNumber', caseNumber || 'N/A');
            formData.append('description', description);
            formData.append('collectedBy', collectedBy);
            formData.append('dateCollected', dateCollected);
            formData.append('timeCollected', timeCollected);
            formData.append('location', location);

            // Append all files
            uploadedFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('http://localhost:3000/api/evidence/forensic', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to upload to backend');
            }

            const result = await response.json();
            console.log('Upload result:', result);

            // Show appropriate message based on storage mode
            if (result.mode === 'snowflake') {
                showNotification('Forensic evidence uploaded to Snowflake! ❄️');
            } else if (result.mode === 'local') {
                showNotification('Evidence saved locally 📁 ' + (result.warning ? '(Snowflake unavailable)' : ''));
            }
        } else {
            // For other categories, just save locally for now
            showNotification('Evidence submitted successfully!');
        }

        // Create evidence object for local display
        const evidence = {
            id: Date.now(),
            caseNumber: caseNumber || 'N/A',
            category: currentCategory,
            description,
            collectedBy,
            dateCollected,
            timeCollected,
            location,
            files: uploadedFiles.map(file => ({
                name: file.name,
                size: formatFileSize(file.size),
                type: file.type || 'Unknown'
            })),
            timestamp: new Date().toISOString(),
            storedIn: currentCategory === 'forensic' ? 'Snowflake' : 'Local'
        };

        evidenceItems.push(evidence);
        saveToLocalStorage();
        renderEvidence();
        resetForm();

    } catch (error) {
        console.error('Error uploading evidence:', error);
        // Still save locally even if server upload fails
        const evidence = {
            id: Date.now(),
            caseNumber: caseNumber || 'N/A',
            category: currentCategory,
            description,
            collectedBy,
            dateCollected,
            timeCollected,
            location,
            files: uploadedFiles.map(file => ({
                name: file.name,
                size: formatFileSize(file.size),
                type: file.type || 'Unknown'
            })),
            timestamp: new Date().toISOString(),
            storedIn: 'Local (server offline)'
        };

        evidenceItems.push(evidence);
        saveToLocalStorage();
        renderEvidence();
        resetForm();

        showNotification('Evidence saved locally (server offline) 📴');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Evidence';
    }
});

// Reset form
function resetForm() {
    document.getElementById('evidenceDescription').value = '';
    document.getElementById('collectedBy').value = '';
    document.getElementById('location').value = '';
    setDefaultDate();
    uploadedFiles = [];
    fileInput.value = '';
    const preview = document.querySelector('.file-preview');
    if (preview) preview.remove();
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Render evidence items
function renderEvidence() {
    let items = [...evidenceItems];

    // Apply search filter
    const searchTerm = searchInput.value.toLowerCase();
    if (searchTerm) {
        items = items.filter(item =>
            item.description.toLowerCase().includes(searchTerm) ||
            item.location.toLowerCase().includes(searchTerm) ||
            item.collectedBy.toLowerCase().includes(searchTerm) ||
            item.caseNumber.toLowerCase().includes(searchTerm)
        );
    }

    // Apply sorting
    const sortValue = sortSelect.value;
    items.sort((a, b) => {
        if (sortValue === 'date-desc') {
            return new Date(b.timestamp) - new Date(a.timestamp);
        } else if (sortValue === 'date-asc') {
            return new Date(a.timestamp) - new Date(b.timestamp);
        } else if (sortValue === 'name') {
            return a.description.localeCompare(b.description);
        }
        return 0;
    });

    // Render
    if (items.length === 0) {
        evidenceItemsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <p>No evidence items found</p>
                <p style="font-size: 12px; margin-top: 10px;">Upload evidence to get started</p>
            </div>
        `;
        return;
    }

    evidenceItemsContainer.innerHTML = items.map(item => `
        <div class="evidence-item" onclick="showDetails(${item.id})">
            <div class="evidence-header">
                <div class="evidence-title">${item.description}</div>
                <div class="evidence-category">${getCategoryName(item.category)}</div>
            </div>
            <div class="evidence-details">
                <div class="evidence-detail">
                    <strong>Case #</strong>
                    <span>${item.caseNumber}</span>
                </div>
                <div class="evidence-detail">
                    <strong>Collected By</strong>
                    <span>${item.collectedBy}</span>
                </div>
                <div class="evidence-detail">
                    <strong>Date</strong>
                    <span>${formatDate(item.dateCollected)} at ${item.timeCollected}</span>
                </div>
                <div class="evidence-detail">
                    <strong>Location</strong>
                    <span>${item.location}</span>
                </div>
                <div class="evidence-detail">
                    <strong>Files</strong>
                    <span>${item.files.length} file(s)</span>
                </div>
                <div class="evidence-detail">
                    <strong>Submitted</strong>
                    <span>${formatDate(item.timestamp.split('T')[0])}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Show evidence details in modal
function showDetails(id) {
    const evidence = evidenceItems.find(item => item.id === id);
    if (!evidence) return;

    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div style="display: grid; gap: 20px;">
            <div>
                <strong style="color: var(--gold);">Case Number:</strong>
                <p>${evidence.caseNumber}</p>
            </div>
            <div>
                <strong style="color: var(--gold);">Category:</strong>
                <p>${getCategoryName(evidence.category)}</p>
            </div>
            <div>
                <strong style="color: var(--gold);">Description:</strong>
                <p>${evidence.description}</p>
            </div>
            <div>
                <strong style="color: var(--gold);">Collected By:</strong>
                <p>${evidence.collectedBy}</p>
            </div>
            <div>
                <strong style="color: var(--gold);">Date & Time:</strong>
                <p>${formatDate(evidence.dateCollected)} at ${evidence.timeCollected}</p>
            </div>
            <div>
                <strong style="color: var(--gold);">Location:</strong>
                <p>${evidence.location}</p>
            </div>
            <div>
                <strong style="color: var(--gold);">Files Attached (${evidence.files.length}):</strong>
                <ul style="margin-top: 10px; padding-left: 20px;">
                    ${evidence.files.map(file => `
                        <li style="margin: 5px 0;">
                            <strong>${file.name}</strong> - ${file.size}
                        </li>
                    `).join('')}
                </ul>
            </div>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--accent-blue);">
                <button onclick="deleteEvidence(${evidence.id})" style="background: var(--danger); color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: 600;">
                    Delete Evidence
                </button>
            </div>
        </div>
    `;

    modal.style.display = 'block';
}

// Delete evidence
function deleteEvidence(id) {
    if (confirm('Are you sure you want to delete this evidence? This action cannot be undone.')) {
        evidenceItems = evidenceItems.filter(item => item.id !== id);
        saveToLocalStorage();
        renderEvidence();
        modal.style.display = 'none';
        showNotification('Evidence deleted');
    }
}

// Get category display name
function getCategoryName(category) {
    const names = {
        'forensic': 'Forensic Data',
        'witness': 'Witness Testimony',
        'images': 'Images/Photos',
        'documents': 'Documents',
        'physical': 'Physical Evidence',
        'digital': 'Digital Evidence',
        'audio': 'Audio/Video'
    };
    return names[category] || category;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success);
        color: white;
        padding: 15px 25px;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Export report
exportBtn.addEventListener('click', () => {
    if (evidenceItems.length === 0) {
        alert('No evidence to export');
        return;
    }

    const caseNumber = document.getElementById('caseNumber').value || 'Unknown';
    const report = generateReport(caseNumber);
    downloadReport(report, caseNumber);
    showNotification('Report exported successfully!');
});

// Generate report
function generateReport(caseNumber) {
    const header = `POLICE DEPARTMENT - EVIDENCE REPORT
${'='.repeat(60)}
Case Number: ${caseNumber}
Generated: ${new Date().toLocaleString()}
Total Evidence Items: ${evidenceItems.length}
${'='.repeat(60)}\n\n`;

    const items = evidenceItems.map((item, index) => `
EVIDENCE ITEM #${index + 1}
${'-'.repeat(60)}
Category: ${getCategoryName(item.category)}
Description: ${item.description}
Collected By: ${item.collectedBy}
Date Collected: ${formatDate(item.dateCollected)} at ${item.timeCollected}
Location: ${item.location}
Files Attached: ${item.files.length}
${item.files.map(f => `  - ${f.name} (${f.size})`).join('\n')}
${'='.repeat(60)}
    `).join('\n');

    return header + items;
}

// Download report
function downloadReport(content, caseNumber) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Evidence_Report_Case_${caseNumber}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Local storage
function saveToLocalStorage() {
    localStorage.setItem('evidenceItems', JSON.stringify(evidenceItems));
}

function loadFromLocalStorage() {
    const stored = localStorage.getItem('evidenceItems');
    if (stored) {
        evidenceItems = JSON.parse(stored);
    }
}

// Search and sort handlers
searchInput.addEventListener('input', renderEvidence);
sortSelect.addEventListener('change', renderEvidence);

// Modal handlers
closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
