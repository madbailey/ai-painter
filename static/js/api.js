/**
 * API class provides a programmatic interface for controlling the canvas
 */
class CanvasAPI {
    constructor(canvas, tools) {
        this.canvas = canvas;
        this.tools = tools;
        this.sessionId = generateId();
        
        // Define API endpoints
        this.endpoints = {
            // Canvas state management
            getState: this.getState.bind(this),
            clear: this.clear.bind(this),
            undo: this.undo.bind(this),
            redo: this.redo.bind(this),
            
            // Drawing operations
            drawLine: this.drawLine.bind(this),
            drawRectangle: this.drawRectangle.bind(this),
            drawCircle: this.drawCircle.bind(this),
            drawBrush: this.drawBrush.bind(this),
            
            // Tool settings
            setColor: this.setColor.bind(this),
            setLineWidth: this.setLineWidth.bind(this),
            setTool: this.setTool.bind(this)
        };
        
        // Expose API globally
        window.msPaintAPI = this.endpoints;
        
        // Initialize
        this.init();
    }
    
    init() {
        // Log API initialization
        updateStatus('API Ready');
        console.log('MS Paint API initialized with session ID:', this.sessionId);
    }
    
    // API Methods
    
    getState() {
        logAPICall('getState', {});
        return this.canvas.getImageData();
    }
    
    clear() {
        logAPICall('clear', {});
        this.canvas.clear();
        updateStatus('Canvas cleared via API');
        return this.getState();
    }
    
    undo() {
        logAPICall('undo', {});
        const success = this.canvas.undo();
        updateStatus(success ? 'Undo via API' : 'Cannot undo - at earliest state');
        return this.getState();
    }
    
    redo() {
        logAPICall('redo', {});
        const success = this.canvas.redo();
        updateStatus(success ? 'Redo via API' : 'Cannot redo - at latest state');
        return this.getState();
    }
    
    drawLine(x1, y1, x2, y2, color = this.canvas.color, width = this.canvas.lineWidth) {
        logAPICall('drawLine', { x1, y1, x2, y2, color, width });
        
        // Save current state
        const prevColor = this.canvas.color;
        const prevWidth = this.canvas.lineWidth;
        
        // Set new properties
        this.canvas.setColor(color);
        this.canvas.setLineWidth(width);
        
        // Draw the line
        this.canvas.drawLine(x1, y1, x2, y2);
        
        // Restore previous state
        this.canvas.setColor(prevColor);
        this.canvas.setLineWidth(prevWidth);
        
        // Save to history
        this.canvas.saveState();
        
        updateStatus(`Drew line from (${x1},${y1}) to (${x2},${y2})`);
        return this.getState();
    }
    
    drawRectangle(x, y, width, height, color = this.canvas.color, lineWidth = this.canvas.lineWidth, fill = false) {
        logAPICall('drawRectangle', { x, y, width, height, color, lineWidth, fill });
        
        // Save current state
        const prevColor = this.canvas.color;
        const prevWidth = this.canvas.lineWidth;
        
        // Set new properties
        this.canvas.setColor(color);
        this.canvas.setLineWidth(lineWidth);
        
        // Draw the rectangle
        this.canvas.drawRectangle(x, y, width, height, color, lineWidth, fill);
        
        // Restore previous state
        this.canvas.setColor(prevColor);
        this.canvas.setLineWidth(prevWidth);
        
        // Save to history
        this.canvas.saveState();
        
        updateStatus(`Drew ${fill ? 'filled ' : ''}rectangle at (${x},${y})`);
        return this.getState();
    }
    
    drawCircle(x, y, radius, color = this.canvas.color, lineWidth = this.canvas.lineWidth, fill = false) {
        logAPICall('drawCircle', { x, y, radius, color, lineWidth, fill });
        
        // Save current state
        const prevColor = this.canvas.color;
        const prevWidth = this.canvas.lineWidth;
        
        // Set new properties
        this.canvas.setColor(color);
        this.canvas.setLineWidth(lineWidth);
        
        // Draw the circle
        this.canvas.drawCircle(x, y, radius, color, lineWidth, fill);
        
        // Restore previous state
        this.canvas.setColor(prevColor);
        this.canvas.setLineWidth(prevWidth);
        
        // Save to history
        this.canvas.saveState();
        
        updateStatus(`Drew ${fill ? 'filled ' : ''}circle at (${x},${y})`);
        return this.getState();
    }
    
    drawBrush(x, y, size = this.canvas.lineWidth, color = this.canvas.color) {
        logAPICall('drawBrush', { x, y, size, color });
        
        // Save current state
        const prevColor = this.canvas.color;
        const prevWidth = this.canvas.lineWidth;
        
        // Set new properties
        this.canvas.setColor(color);
        this.canvas.setLineWidth(size);
        
        // Draw brush dot (small circle)
        this.canvas.drawCircle(x, y, size / 2, color, size, true);
        
        // Restore previous state
        this.canvas.setColor(prevColor);
        this.canvas.setLineWidth(prevWidth);
        
        // Don't save state for individual brush strokes (too many updates)
        // Let the canvas handle this when drawing stops
        
        updateStatus(`Drew brush at (${x},${y})`);
        return this.getState();
    }
    
    setColor(color) {
        logAPICall('setColor', { color });
        this.tools.selectColor(color);
        updateStatus(`Color set to ${color}`);
        return color;
    }
    
    setLineWidth(width) {
        logAPICall('setLineWidth', { width });
        width = parseInt(width);
        this.canvas.setLineWidth(width);
        
        // Update brush size slider
        const brushSize = document.getElementById('brushSize');
        const brushSizeDisplay = document.getElementById('brushSizeDisplay');
        if (brushSize && brushSizeDisplay) {
            brushSize.value = width;
            brushSizeDisplay.textContent = `${width}px`;
        }
        
        updateStatus(`Line width set to ${width}px`);
        return width;
    }
    
    setTool(tool) {
        logAPICall('setTool', { tool });
        
        if (this.tools.tools.some(t => t.id === tool)) {
            this.tools.selectTool(tool);
            updateStatus(`Tool set to ${tool}`);
            return tool;
        } else {
            updateStatus(`Invalid tool: ${tool}`);
            return null;
        }
    }
}