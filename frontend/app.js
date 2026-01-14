// Project AETHER Frontend Application

const API_BASE = 'http://localhost:8000';

// DOM Elements
const textTab = document.querySelector('[data-tab="text"]');
const fileTab = document.querySelector('[data-tab="file"]');
const textInput = document.getElementById('text-input');
const fileInput = document.getElementById('file-input');
const fileUploadArea = document.getElementById('file-upload-area');
const filePreview = document.getElementById('file-preview');
const showUpdatesCheckbox = document.getElementById('show-updates');
const analyzeBtn = document.getElementById('analyze-btn');
const progressSection = document.getElementById('progress-section');
const progressUpdates = document.getElementById('progress-updates');
const resultsSection = document.getElementById('results-section');
const finalReport = document.getElementById('final-report');
const historyList = document.getElementById('history-list');
const refreshHistoryBtn = document.getElementById('refresh-history');

// Tab switching
textTab.addEventListener('click', () => switchTab('text'));
fileTab.addEventListener('click', () => switchTab('file'));

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    if (tab === 'text') {
        textTab.classList.add('active');
        document.getElementById('text-tab').classList.add('active');
    } else {
        fileTab.classList.add('active');
        document.getElementById('file-tab').classList.add('active');
    }
}

// File upload
fileUploadArea.addEventListener('click', () => fileInput.click());
fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.style.background = '#f0f0ff';
});
fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.style.background = 'white';
});
fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.style.background = 'white';
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

async function handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const content = e.target.result;
        filePreview.innerHTML = `
            <strong>File: ${file.name}</strong>
            <p>Size: ${(file.size / 1024).toFixed(2)} KB</p>
            <p>Preview: ${content.substring(0, 200)}...</p>
        `;
        filePreview.classList.remove('hidden');
        textInput.value = content;
    };
    reader.readAsText(file);
}

// Analyze button
analyzeBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    if (!text) {
        alert('Please enter text or upload a file');
        return;
    }
    
    const showUpdates = showUpdatesCheckbox.checked;
    
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';
    
    // Clear previous results
    progressSection.classList.remove('hidden');
    progressUpdates.innerHTML = '';
    resultsSection.classList.add('hidden');
    
    try {
        if (showUpdates) {
            try {
                await analyzeWithUpdates(text);
            } catch (sseError) {
                console.warn('SSE connection failed, falling back to non-streaming mode:', sseError);
                addProgressUpdate('warning', 'Real-time updates unavailable, using standard mode...');
                await analyzeWithoutUpdates(text);
            }
        } else {
            await analyzeWithoutUpdates(text);
        }
    } catch (error) {
        console.error('Analysis error:', error);
        const errorMsg = error?.message || error?.toString() || 'Unknown error occurred';
        addProgressUpdate('error', `Error: ${errorMsg}`);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Document';
    }
});

async function analyzeWithUpdates(text) {
    // Use EventSource for streaming updates
    const sessionId = Date.now().toString();
    const url = `${API_BASE}/api/analyze/stream/${sessionId}?text=${encodeURIComponent(text)}&show_updates=true`;
    
    // First, verify server is accessible
    try {
        const healthCheck = await fetch(`${API_BASE}/`, { method: 'GET', signal: AbortSignal.timeout(3000) });
        if (!healthCheck.ok) {
            throw new Error(`Server returned status ${healthCheck.status}`);
        }
    } catch (error) {
        console.error('Server health check failed:', error);
        throw new Error(`Cannot connect to server at ${API_BASE}. Please ensure the server is running. Error: ${error.message}`);
    }
    
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(url);
        let hasConnected = false;
        let connectionTimeout;
        let errorCount = 0;
        
        // Set a timeout for initial connection
        connectionTimeout = setTimeout(() => {
            if (!hasConnected && eventSource.readyState === EventSource.CONNECTING) {
                eventSource.close();
                reject(new Error('Connection timeout: Server did not respond within 10 seconds. The server may be overloaded or the endpoint may be misconfigured.'));
            }
        }, 10000); // 10 second timeout
        
        // Track when connection is established
        eventSource.onopen = () => {
            hasConnected = true;
            clearTimeout(connectionTimeout);
            console.log('SSE connection established');
        };
        
        eventSource.onmessage = (event) => {
            try {
                if (!event.data) {
                    console.warn('Received empty SSE message');
                    return;
                }
                
                const parsed = JSON.parse(event.data);
                
                if (parsed.event === 'connected') {
                    hasConnected = true;
                    clearTimeout(connectionTimeout);
                    const msg = parsed.data?.message || 'Connected';
                    addProgressUpdate('info', msg);
                } else if (parsed.event === 'progress') {
                    const update = parsed.data || {};
                    addProgressUpdate(
                        update.stage || 'progress', 
                        update.message || 'Processing...', 
                        update.data || {}
                    );
                } else if (parsed.event === 'complete') {
                    clearTimeout(connectionTimeout);
                    eventSource.close();
                    const result = parsed.data || {};
                    displayResults(result);
                    loadHistory();
                    resolve(result);
                } else if (parsed.event === 'error') {
                    clearTimeout(connectionTimeout);
                    eventSource.close();
                    const errorData = parsed.data || {};
                    const errorMsg = errorData.error || 'Unknown error occurred';
                    reject(new Error(errorMsg));
                }
            } catch (error) {
                console.error('Error processing SSE message:', error, event);
                clearTimeout(connectionTimeout);
                eventSource.close();
                reject(new Error(error?.message || 'Failed to process server response'));
            }
        };
        
        eventSource.onerror = (event) => {
            errorCount++;
            console.error('EventSource error:', event, 'readyState:', eventSource.readyState, 'errorCount:', errorCount);
            
            // Don't reject immediately on first error - EventSource may retry
            // But if we get multiple errors quickly, something is wrong
            if (eventSource.readyState === EventSource.CLOSED) {
                clearTimeout(connectionTimeout);
                let errorMsg = 'Connection to server was closed.';
                
                if (!hasConnected) {
                    errorMsg = `Failed to connect to server at ${API_BASE}. `;
                    errorMsg += 'Please check: 1) Server is running, 2) CORS is enabled, 3) The endpoint exists.';
                } else {
                    errorMsg = 'Connection to server was lost. The server may have stopped or encountered an error.';
                }
                
                eventSource.close();
                reject(new Error(errorMsg));
            } else if (errorCount > 3 && !hasConnected) {
                // If we've had multiple errors and never connected, give up
                clearTimeout(connectionTimeout);
                eventSource.close();
                reject(new Error(`Failed to establish connection after ${errorCount} attempts. Please check server logs.`));
            }
            // If still connecting, EventSource will retry automatically
        };
    });
}

async function analyzeWithoutUpdates(text) {
    const response = await fetch(`${API_BASE}/api/analyze/text`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            show_updates: false
        })
    });
    
    if (!response.ok) {
        // Try to get error details from response
        let errorMsg = `HTTP error! status: ${response.status}`;
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMsg = errorData.detail;
            } else if (errorData.error) {
                errorMsg = errorData.error;
            } else if (errorData.message) {
                errorMsg = errorData.message;
            }
        } catch (e) {
            // If response isn't JSON, use status text
            errorMsg = `HTTP error! status: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMsg);
    }
    
    const result = await response.json();
    
    // Check if result indicates failure
    if (result.success === false) {
        const errorMsg = result.error || 'Analysis failed for unknown reason';
        throw new Error(errorMsg);
    }
    
    displayResults(result);
    loadHistory();
    return result;
}

function addProgressUpdate(stage, message, data = {}) {
    const item = document.createElement('div');
    item.className = `progress-item ${stage}`;
    
    let content = `<strong>${stage.toUpperCase().replace('_', ' ')}</strong>: ${message}`;
    
    if (data.factors) {
        content += `<br><small>Found ${data.factors.length} factors</small>`;
    }
    
    if (data.factor) {
        content += `<br><small>Factor: ${data.factor.name}</small>`;
    }
    
    item.innerHTML = content;
    progressUpdates.appendChild(item);
    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function displayResults(result) {
    if (!result.success) {
        finalReport.textContent = `Error: ${result.error}`;
        resultsSection.classList.remove('hidden');
        return;
    }
    
    const report = result.final_report?.report || 'No report generated';
    finalReport.textContent = report;
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// History
refreshHistoryBtn.addEventListener('click', loadHistory);

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/history?limit=20`);
        const data = await response.json();
        
        historyList.innerHTML = '';
        
        if (data.history.length === 0) {
            historyList.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">No analysis history yet</p>';
            return;
        }
        
        data.history.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.addEventListener('click', () => viewHistoryItem(item.id));
            
            const date = new Date(item.created_at).toLocaleString();
            
            let keyPointsHtml = '';
            if (item.key_points && item.key_points.length > 0) {
                keyPointsHtml = `
                    <div class="history-item-key-points">
                        <ul>
                            ${item.key_points.map(kp => `<li>${kp}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            historyItem.innerHTML = `
                <div class="history-item-header">
                    <div class="history-item-title">Analysis #${item.id}</div>
                    <div class="history-item-date">${date}</div>
                </div>
                <div class="history-item-preview">
                    ${item.input_preview || 'Document analyzed'}
                </div>
                <div style="margin-top: 10px; color: #667eea; font-size: 0.9em;">
                    ${item.factors_count || 0} factors identified
                </div>
                ${keyPointsHtml}
            `;
            
            historyList.appendChild(historyItem);
        });
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

async function viewHistoryItem(analysisId) {
    try {
        const response = await fetch(`${API_BASE}/api/history/${analysisId}`);
        const data = await response.json();
        
        if (data.final_report) {
            finalReport.textContent = data.final_report;
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        console.error('Error loading history item:', error);
        alert('Could not load analysis details');
    }
}

// Load history on page load
loadHistory();

