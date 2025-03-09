/**
 * Utility functions for MS Paint AI
 */

// Generate a unique ID
function generateId() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Format JSON for display
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// Log API calls to the UI
function logAPICall(endpoint, params) {
    const apiLog = document.getElementById('apiLog');
    if (apiLog) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            endpoint,
            params
        };
        apiLog.textContent = formatJSON(logEntry);
    }
}

// Update API status display
function updateStatus(status) {
    const statusElement = document.getElementById('status');
    if (statusElement) {
        statusElement.textContent = status;
    }
}

// Save canvas state to localStorage
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, data);
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

// Load canvas state from localStorage
function loadFromLocalStorage(key) {
    try {
        return localStorage.getItem(key);
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return null;
    }
}

// Debounce function to limit how often a function can be called
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}