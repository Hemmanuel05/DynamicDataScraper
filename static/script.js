let statusInterval;
let isScrapingRunning = false;

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startBtn');
    const retryBtn = document.getElementById('retryBtn');
    
    startBtn.addEventListener('click', startScraping);
    retryBtn.addEventListener('click', startScraping);
    
    // Add log entry function
    window.addLogEntry = function(message, type = 'info') {
        const logContainer = document.getElementById('logContainer');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Limit log entries to prevent memory issues
        while (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.firstChild);
        }
    };
});

function startScraping() {
    if (isScrapingRunning) {
        addLogEntry('Scraping is already running', 'warning');
        return;
    }
    
    addLogEntry('Starting scraping process...');
    
    // Show progress section
    document.getElementById('progressSection').classList.remove('d-none');
    document.getElementById('resultsSection').classList.add('d-none');
    document.getElementById('errorSection').classList.add('d-none');
    
    // Disable start button
    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';
    
    // Reset progress
    updateProgress(0, 'Initializing...');
    
    // Start scraping
    fetch('/start_scraping', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            addLogEntry(`Error starting scraper: ${data.error}`, 'error');
            showError(data.error);
        } else {
            addLogEntry('Scraper started successfully');
            isScrapingRunning = true;
            startStatusPolling();
        }
    })
    .catch(error => {
        addLogEntry(`Failed to start scraper: ${error.message}`, 'error');
        showError(`Failed to start scraper: ${error.message}`);
    });
}

function startStatusPolling() {
    statusInterval = setInterval(checkStatus, 2000); // Check every 2 seconds
    checkStatus(); // Initial check
}

function checkStatus() {
    fetch('/status')
    .then(response => response.json())
    .then(status => {
        updateUI(status);
        
        if (!status.running && status.completed) {
            // Scraping completed successfully
            clearInterval(statusInterval);
            isScrapingRunning = false;
            showResults(status);
            addLogEntry('Scraping completed successfully!', 'success');
        } else if (!status.running && status.error) {
            // Scraping failed
            clearInterval(statusInterval);
            isScrapingRunning = false;
            showError(status.error);
            addLogEntry(`Scraping failed: ${status.error}`, 'error');
        } else if (status.running) {
            // Still running - update progress
            updateProgress(status.progress, status.message);
            
            if (status.total_pins > 0) {
                addLogEntry(`Progress: ${status.current_pin}/${status.total_pins} pins processed`);
            }
        }
    })
    .catch(error => {
        addLogEntry(`Error checking status: ${error.message}`, 'error');
    });
}

function updateUI(status) {
    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = `${status.progress}%`;
    progressBar.textContent = `${status.progress}%`;
    
    // Update stats
    document.getElementById('totalPins').textContent = status.total_pins || '-';
    document.getElementById('currentPin').textContent = status.current_pin || '-';
    document.getElementById('statusText').textContent = status.running ? 'Running' : 'Stopped';
    document.getElementById('statusMessage').textContent = status.message || 'Ready';
    
    // Update progress bar color based on progress
    if (status.progress >= 100) {
        progressBar.className = 'progress-bar bg-success';
    } else if (status.error) {
        progressBar.className = 'progress-bar bg-danger';
    } else {
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    }
}

function updateProgress(progress, message) {
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = `${progress}%`;
    progressBar.textContent = `${progress}%`;
    
    document.getElementById('statusMessage').textContent = message;
    
    if (message && message !== 'Ready to start scraping') {
        addLogEntry(message);
    }
}

function showResults(status) {
    document.getElementById('resultsSection').classList.remove('d-none');
    document.getElementById('progressSection').classList.add('d-none');
    document.getElementById('errorSection').classList.add('d-none');
    
    const resultsMessage = document.getElementById('resultsMessage');
    resultsMessage.textContent = status.message;
    
    // Setup download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (status.csv_file) {
        downloadBtn.href = `/download/${status.csv_file}`;
        downloadBtn.classList.remove('d-none');
    }
    
    // Reset start button
    resetStartButton();
}

function showError(error) {
    document.getElementById('errorSection').classList.remove('d-none');
    document.getElementById('progressSection').classList.add('d-none');
    document.getElementById('resultsSection').classList.add('d-none');
    
    document.getElementById('errorMessage').textContent = error;
    
    // Reset start button
    resetStartButton();
}

function resetStartButton() {
    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = false;
    startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start Scraping';
}

// Add some utility functions for better UX
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        addLogEntry('Copied to clipboard', 'success');
    }, function(err) {
        addLogEntry('Failed to copy to clipboard', 'error');
    });
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter to start scraping
    if (e.ctrlKey && e.key === 'Enter' && !isScrapingRunning) {
        startScraping();
    }
    
    // Escape to stop (if we add stop functionality)
    if (e.key === 'Escape' && isScrapingRunning) {
        // Could add stop functionality here
        addLogEntry('Press Ctrl+C in terminal to stop scraping', 'warning');
    }
});

// Auto-scroll log to bottom when new entries are added
const logContainer = document.getElementById('logContainer');
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    });
});

observer.observe(logContainer, {
    childList: true,
    subtree: true
});
