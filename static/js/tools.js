/**
 * Tools class manages drawing tools and UI controls
 */
class Tools {
    constructor(canvas) {
        this.canvas = canvas;
        this.tools = [
            { id: 'brush', name: 'Brush', icon: 'brush' },
            { id: 'line', name: 'Line', icon: 'line' },
            { id: 'rectangle', name: 'Rectangle', icon: 'rectangle' },
            { id: 'circle', name: 'Circle', icon: 'circle' },
            { id: 'eraser', name: 'Eraser', icon: 'eraser' },
            { id: 'undo', name: 'Undo', icon: 'undo' },
            { id: 'redo', name: 'Redo', icon: 'redo' },
            { id: 'clear', name: 'Clear', icon: 'clear' }
        ];
        this.activeTool = 'brush';
        
        this.colors = [
            '#000000', '#ffffff', '#ff0000', '#00ff00', '#0000ff',
            '#ffff00', '#00ffff', '#ff00ff', '#c0c0c0', '#808080',
            '#800000', '#808000', '#008000', '#800080', '#008080',
            '#ffa500', '#a52a2a', '#f5f5dc', '#ffc0cb', '#20b2aa'
        ];
        this.activeColor = '#000000';
        
        this.init();
    }

    init() {
        this.createToolbar();
        this.createColorPalette();
        this.setupBrushSizeControl();
    }

    createToolbar() {
        const toolbar = document.getElementById('toolbar');
        
        // Create tool buttons
        this.tools.forEach(tool => {
            const button = document.createElement('div');
            button.className = `tool ${tool.id === this.activeTool ? 'active' : ''}`;
            button.dataset.tool = tool.id;
            button.title = tool.name;
            
            const iconElement = document.createElement('div');
            iconElement.className = 'tool-icon';
            button.appendChild(iconElement);
            
            if (tool.id === 'undo' || tool.id === 'redo' || tool.id === 'clear') {
                button.addEventListener('click', () => this.handleUtilityTool(tool.id));
            } else {
                button.addEventListener('click', () => this.selectTool(tool.id));
            }
            
            toolbar.appendChild(button);
        });
    }

    createColorPalette() {
        const palette = document.getElementById('colorPalette');
        
        this.colors.forEach(color => {
            const colorEl = document.createElement('div');
            colorEl.className = `color ${color === this.activeColor ? 'active' : ''}`;
            colorEl.style.backgroundColor = color;
            colorEl.dataset.color = color;
            colorEl.addEventListener('click', () => this.selectColor(color));
            palette.appendChild(colorEl);
        });
    }

    setupBrushSizeControl() {
        const brushSize = document.getElementById('brushSize');
        const brushSizeDisplay = document.getElementById('brushSizeDisplay');
        
        brushSize.addEventListener('input', () => {
            const size = brushSize.value;
            brushSizeDisplay.textContent = `${size}px`;
            this.canvas.setLineWidth(parseInt(size));
        });
    }

    selectTool(toolId) {
        this.activeTool = toolId;
        this.canvas.setTool(toolId);
        
        // Update UI
        document.querySelectorAll('.tool').forEach(el => {
            if (el.dataset.tool === toolId) {
                el.classList.add('active');
            } else if (el.dataset.tool && !['undo', 'redo', 'clear'].includes(el.dataset.tool)) {
                el.classList.remove('active');
            }
        });
        
        updateStatus(`Tool: ${toolId}`);
    }

    handleUtilityTool(toolId) {
        switch (toolId) {
            case 'undo':
                this.canvas.undo();
                updateStatus('Undo');
                break;
            case 'redo':
                this.canvas.redo();
                updateStatus('Redo');
                break;
            case 'clear':
                if (confirm('Are you sure you want to clear the canvas?')) {
                    this.canvas.clear();
                    updateStatus('Canvas cleared');
                }
                break;
        }
    }

    selectColor(color) {
        this.activeColor = color;
        this.canvas.setColor(color);
        
        // Update UI
        document.querySelectorAll('.color').forEach(el => {
            if (el.dataset.color === color) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
        
        updateStatus(`Color: ${color}`);
    }
}