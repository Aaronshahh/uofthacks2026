/**
 * Footwear RAG Agent - Frontend Application
 */

// API Configuration
const API_BASE = window.location.origin;

// State
let selectedFile = null;

// DOM Element references (initialized after DOM loads)
let uploadArea, fileInput, filePreview, fileName, fileSize, removeFile;
let analyzeBtn, resultsSection, resultsMeta, casesGrid, emptyState;
let systemStatus, recordCount, toast, toastMessage, toastClose;

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing...');
    
    // Get DOM elements after DOM is ready
    uploadArea = document.getElementById('uploadArea');
    fileInput = document.getElementById('fileInput');
    filePreview = document.getElementById('filePreview');
    fileName = document.getElementById('fileName');
    fileSize = document.getElementById('fileSize');
    removeFile = document.getElementById('removeFile');
    analyzeBtn = document.getElementById('analyzeBtn');
    resultsSection = document.getElementById('resultsSection');
    resultsMeta = document.getElementById('resultsMeta');
    casesGrid = document.getElementById('casesGrid');
    emptyState = document.getElementById('emptyState');
    systemStatus = document.getElementById('systemStatus');
    recordCount = document.getElementById('recordCount');
    toast = document.getElementById('toast');
    toastMessage = document.getElementById('toastMessage');
    toastClose = document.getElementById('toastClose');
    
    console.log('DOM elements:', {
        uploadArea: !!uploadArea,
        fileInput: !!fileInput,
        analyzeBtn: !!analyzeBtn
    });
    
    try {
        initEventListeners();
        checkSystemHealth();
        console.log('Initialization complete');
        window.appInitialized = true;
    } catch (error) {
        console.error('Initialization error:', error);
        showToast('Failed to initialize application');
    }
});

function initEventListeners() {
    console.log('Setting up event listeners...');
    
    // File upload - click handler
    if (uploadArea && fileInput) {
        // Click to upload
        uploadArea.addEventListener('click', function(e) {
            console.log('Upload area clicked');
            fileInput.click();
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        
        // File selection
        fileInput.addEventListener('change', handleFileSelect);
        
        console.log('File upload listeners attached');
    } else {
        console.error('Upload area or file input not found!', { uploadArea, fileInput });
    }
    
    // File preview - remove button
    if (removeFile) {
        removeFile.addEventListener('click', function(e) {
            e.stopPropagation();
            clearFile();
        });
    }
    
    // Analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeFootprint);
    } else {
        console.error('Analyze button not found!');
    }
    
    // Toast close
    if (toastClose) {
        toastClose.addEventListener('click', hideToast);
    }
    
    console.log('Event listeners setup complete');
}

// ============================================
// File Handling
// ============================================

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    console.log('File input changed');
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    console.log('Processing file:', file.name, file.type, file.size);
    
    // Validate file type
    const validTypes = ['image/tiff', 'image/png', 'image/jpeg', 'image/jpg'];
    const validExtensions = ['.tiff', '.tif', '.png', '.jpg', '.jpeg'];
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
    );
    
    // Also accept if type is empty but extension is valid (some browsers don't set type for TIFF)
    if (!hasValidType && !hasValidExtension) {
        console.warn('Invalid file type:', file.type, file.name);
        showToast('Invalid file type. Please upload a TIFF, PNG, or JPEG image.');
        return;
    }
    
    selectedFile = file;
    showFilePreview(file);
    console.log('File accepted:', file.name);
}

function showFilePreview(file) {
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);
    if (filePreview) filePreview.style.display = 'flex';
    if (analyzeBtn) analyzeBtn.disabled = false;
    console.log('File preview shown');
}

function clearFile() {
    console.log('Clearing file');
    selectedFile = null;
    if (fileInput) fileInput.value = '';
    if (filePreview) filePreview.style.display = 'none';
    if (analyzeBtn) analyzeBtn.disabled = true;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ============================================
// API Calls
// ============================================

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        
        updateSystemStatus(data);
        updateRecordCount(data.record_count);
    } catch (error) {
        console.error('Health check failed:', error);
        updateSystemStatus({ status: 'error', database_connected: false });
    }
}

async function analyzeFootprint() {
    if (!selectedFile) {
        showToast('Please select a file first');
        return;
    }
    
    console.log('Starting analysis for:', selectedFile.name);
    
    // Show loading state
    setLoading(true);
    
    try {
        const formData = new FormData();
        formData.append('image', selectedFile);
        
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
        }
        
        const result = await response.json();
        console.log('Analysis result:', result);
        displayResults(result);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        showToast(error.message || 'Analysis failed. Please try again.');
    } finally {
        setLoading(false);
    }
}

// ============================================
// UI Updates
// ============================================

function updateSystemStatus(data) {
    if (!systemStatus) return;
    
    const statusDot = systemStatus.querySelector('.status-dot');
    const statusText = systemStatus.querySelector('.status-text');
    
    if (data.database_connected) {
        if (statusDot) statusDot.className = 'status-dot connected';
        if (statusText) statusText.textContent = 'Connected';
    } else {
        if (statusDot) statusDot.className = 'status-dot error';
        if (statusText) statusText.textContent = 'Disconnected';
    }
}

function updateRecordCount(count) {
    if (recordCount) {
        recordCount.textContent = `Database: ${(count || 0).toLocaleString()} records`;
    }
}

function setLoading(loading) {
    if (!analyzeBtn) return;
    
    const btnText = analyzeBtn.querySelector('.btn-text');
    const btnLoading = analyzeBtn.querySelector('.btn-loading');
    
    if (loading) {
        if (btnText) btnText.style.display = 'none';
        if (btnLoading) btnLoading.style.display = 'flex';
        analyzeBtn.disabled = true;
    } else {
        if (btnText) btnText.style.display = 'inline';
        if (btnLoading) btnLoading.style.display = 'none';
        analyzeBtn.disabled = !selectedFile;
    }
}

function displayResults(result) {
    // Hide empty state
    if (emptyState) emptyState.style.display = 'none';
    
    // Show results section
    if (resultsSection) resultsSection.style.display = 'block';
    
    // Update meta info
    if (resultsMeta && result.query_metadata) {
        const meta = result.query_metadata;
        resultsMeta.textContent = `${meta.results_found} cases found in ${meta.processing_time_ms.toFixed(1)}ms`;
    }
    
    // Clear previous results
    if (casesGrid) {
        casesGrid.innerHTML = '';
        
        // Create case cards
        const cases = result.cases;
        
        if (cases.case_a) {
            casesGrid.appendChild(createCaseCard(cases.case_a, 'a'));
        }
        if (cases.case_b) {
            casesGrid.appendChild(createCaseCard(cases.case_b, 'b'));
        }
        if (cases.case_c) {
            casesGrid.appendChild(createCaseCard(cases.case_c, 'c'));
        }
    }
    
    // Scroll to results
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
}

function createCaseCard(caseData, caseType) {
    const card = document.createElement('div');
    card.className = `case-card case-${caseType}`;
    
    const similarityPercent = (caseData.similarity_score * 100).toFixed(1);
    
    card.innerHTML = `
        <div class="case-header">
            <span class="case-label">${caseData.case_label}</span>
            <span class="similarity-badge">${similarityPercent}% match</span>
        </div>
        <div class="case-body">
            <div class="case-id">ID: ${caseData.id}</div>
            <div class="metadata-grid">
                ${createMetadataItems(caseData.metadata)}
            </div>
        </div>
    `;
    
    return card;
}

function createMetadataItems(metadata) {
    return Object.entries(metadata)
        .map(([key, value]) => `
            <div class="metadata-item">
                <div class="metadata-label">${formatLabel(key)}</div>
                <div class="metadata-value">${formatValue(value)}</div>
            </div>
        `)
        .join('');
}

function formatLabel(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .trim();
}

function formatValue(value) {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    if (typeof value === 'number') {
        return Number.isInteger(value) ? value.toString() : value.toFixed(2);
    }
    return value.toString();
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message) {
    if (!toast || !toastMessage) {
        console.error('Toast error:', message);
        alert(message);
        return;
    }
    
    toastMessage.textContent = message;
    toast.style.display = 'flex';
    
    // Auto-hide after 5 seconds
    setTimeout(hideToast, 5000);
}

function hideToast() {
    if (toast) {
        toast.style.display = 'none';
    }
}
