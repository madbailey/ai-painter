/**
 * Canvas class handles all drawing operations
 */
class Canvas {
    constructor() {
        this.canvas = document.getElementById('paintCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.lastX = 0;
        this.lastY = 0;
        this.color = '#000000';
        this.lineWidth = 5;
        this.tool = 'brush';
        this.history = [];
        this.currentStep = -1;
        this.maxHistorySteps = 50;
        this.tempCanvas = document.createElement('canvas');
        this.tempCtx = this.tempCanvas.getContext('2d');
        this.tempCanvas.width = this.canvas.width;
        this.tempCanvas.height = this.canvas.height;
        
        this.init();
    }

    init() {
        // Save initial canvas state (blank canvas)
        this.saveState();
        
        // Set up event listeners
        this.canvas.addEventListener('mousedown', this.startDrawing.bind(this));
        this.canvas.addEventListener('mousemove', this.draw.bind(this));
        this.canvas.addEventListener('mouseup', this.stopDrawing.bind(this));
        this.canvas.addEventListener('mouseout', this.stopDrawing.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Z for undo
            if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                this.undo();
            }
            // Ctrl+Y for redo
            if (e.ctrlKey && e.key === 'y') {
                e.preventDefault();
                this.redo();
            }
        });
    }

    startDrawing(e) {
        this.isDrawing = true;
        this.startX = e.offsetX;
        this.startY = e.offsetY;
        this.lastX = e.offsetX;
        this.lastY = e.offsetY;
        
        // For brush tool, start drawing immediately
        if (this.tool === 'brush' || this.tool === 'eraser') {
            this.ctx.beginPath();
            this.ctx.moveTo(this.lastX, this.lastY);
            this.ctx.lineTo(this.lastX, this.lastY);
            this.ctx.strokeStyle = this.tool === 'eraser' ? '#ffffff' : this.color;
            this.ctx.lineWidth = this.lineWidth;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            this.ctx.stroke();
        }
    }

    draw(e) {
        if (!this.isDrawing) return;
        
        const currentX = e.offsetX;
        const currentY = e.offsetY;
        
        switch (this.tool) {
            case 'brush':
                this.drawBrush(currentX, currentY);
                break;
            case 'eraser':
                this.drawEraser(currentX, currentY);
                break;
            case 'line':
                this.drawPreviewLine(currentX, currentY);
                break;
            case 'rectangle':
                this.drawPreviewRectangle(currentX, currentY);
                break;
            case 'circle':
                this.drawPreviewCircle(currentX, currentY);
                break;
        }
        
        this.lastX = currentX;
        this.lastY = currentY;
    }

    stopDrawing() {
        if (!this.isDrawing) return;
        
        if (this.tool === 'line') {
            this.drawLine(this.startX, this.startY, this.lastX, this.lastY);
        } else if (this.tool === 'rectangle') {
            this.drawRectangle(
                Math.min(this.startX, this.lastX),
                Math.min(this.startY, this.lastY),
                Math.abs(this.lastX - this.startX),
                Math.abs(this.lastY - this.startY)
            );
        } else if (this.tool === 'circle') {
            const radius = Math.sqrt(
                Math.pow(this.lastX - this.startX, 2) + 
                Math.pow(this.lastY - this.startY, 2)
            );
            this.drawCircle(this.startX, this.startY, radius);
        }
        
        this.isDrawing = false;
        this.saveState();
    }

    drawBrush(x, y) {
        this.ctx.beginPath();
        this.ctx.moveTo(this.lastX, this.lastY);
        this.ctx.lineTo(x, y);
        this.ctx.strokeStyle = this.color;
        this.ctx.lineWidth = this.lineWidth;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.stroke();
    }

    drawEraser(x, y) {
        this.ctx.beginPath();
        this.ctx.moveTo(this.lastX, this.lastY);
        this.ctx.lineTo(x, y);
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = this.lineWidth;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.stroke();
    }

    drawPreviewLine(x, y) {
        // Clear the previous preview
        this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
        
        // Draw current canvas state to temp canvas
        this.tempCtx.drawImage(this.canvas, 0, 0);
        
        // Draw the preview line
        this.tempCtx.beginPath();
        this.tempCtx.moveTo(this.startX, this.startY);
        this.tempCtx.lineTo(x, y);
        this.tempCtx.strokeStyle = this.color;
        this.tempCtx.lineWidth = this.lineWidth;
        this.tempCtx.lineCap = 'round';
        this.tempCtx.lineJoin = 'round';
        this.tempCtx.stroke();
        
        // Clear the main canvas and draw the temp canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.tempCanvas, 0, 0);
    }

    drawPreviewRectangle(x, y) {
        // Clear the previous preview
        this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
        
        // Draw current canvas state to temp canvas
        this.tempCtx.drawImage(this.canvas, 0, 0);
        
        // Draw the preview rectangle
        const width = x - this.startX;
        const height = y - this.startY;
        
        this.tempCtx.beginPath();
        this.tempCtx.rect(this.startX, this.startY, width, height);
        this.tempCtx.strokeStyle = this.color;
        this.tempCtx.lineWidth = this.lineWidth;
        this.tempCtx.stroke();
        
        // Clear the main canvas and draw the temp canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.tempCanvas, 0, 0);
    }

    drawPreviewCircle(x, y) {
        // Clear the previous preview
        this.tempCtx.clearRect(0, 0, this.tempCanvas.width, this.tempCanvas.height);
        
        // Draw current canvas state to temp canvas
        this.tempCtx.drawImage(this.canvas, 0, 0);
        
        // Calculate radius
        const radius = Math.sqrt(
            Math.pow(x - this.startX, 2) + 
            Math.pow(y - this.startY, 2)
        );
        
        // Draw the preview circle
        this.tempCtx.beginPath();
        this.tempCtx.arc(this.startX, this.startY, radius, 0, Math.PI * 2);
        this.tempCtx.strokeStyle = this.color;
        this.tempCtx.lineWidth = this.lineWidth;
        this.tempCtx.stroke();
        
        // Clear the main canvas and draw the temp canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.tempCanvas, 0, 0);
    }

    drawLine(x1, y1, x2, y2, color = this.color, width = this.lineWidth) {
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = width;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.stroke();
    }

    drawRectangle(x, y, width, height, color = this.color, width = this.lineWidth, fill = false) {
        this.ctx.beginPath();
        this.ctx.rect(x, y, width, height);
        
        if (fill) {
            this.ctx.fillStyle = color;
            this.ctx.fill();
        } else {
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = width;
            this.ctx.stroke();
        }
    }

    drawCircle(x, y, radius, color = this.color, width = this.lineWidth, fill = false) {
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);
        
        if (fill) {
            this.ctx.fillStyle = color;
            this.ctx.fill();
        } else {
            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = width;
            this.ctx.stroke();
        }
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.saveState();
    }

    saveState() {
        // Trim history if we've done new actions after undoing
        if (this.currentStep < this.history.length - 1) {
            this.history = this.history.slice(0, this.currentStep + 1);
        }
        
        // Save current state
        this.currentStep++;
        this.history.push(this.canvas.toDataURL());
        
        // Limit history size to prevent memory issues
        if (this.history.length > this.maxHistorySteps) {
            this.history.shift();
            this.currentStep--;
        }
    }

    undo() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.loadState(this.history[this.currentStep]);
            return true;
        }
        return false;
    }

    redo() {
        if (this.currentStep < this.history.length - 1) {
            this.currentStep++;
            this.loadState(this.history[this.currentStep]);
            return true;
        }
        return false;
    }

    loadState(dataURL) {
        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.drawImage(img, 0, 0);
        };
        img.src = dataURL;
    }

    setColor(color) {
        this.color = color;
    }

    setLineWidth(width) {
        this.lineWidth = width;
    }

    setTool(tool) {
        this.tool = tool;
    }

    getImageData() {
        return this.canvas.toDataURL('image/png');
    }
}