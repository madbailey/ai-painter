/**
 * Main application entry point
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize canvas
    const canvas = new Canvas();
    
    // Initialize tools
    const tools = new Tools(canvas);
    
    // Initialize API
    const api = new CanvasAPI(canvas, tools);
    
    // Responsive canvas sizing
    function resizeCanvas() {
        const container = document.querySelector('.canvas-container');
        if (container) {
            const containerWidth = container.clientWidth;
            const containerHeight = container.clientHeight;
            
            // Only resize if necessary
            if (containerWidth !== canvas.canvas.width || containerHeight !== canvas.canvas.height) {
                // Save current canvas content
                const imageData = canvas.getImageData();
                
                // Resize canvas
                canvas.canvas.width = containerWidth;
                canvas.canvas.height = containerHeight;
                canvas.tempCanvas.width = containerWidth;
                canvas.tempCanvas.height = containerHeight;
                
                // Restore content
                const img = new Image();
                img.onload = () => {
                    canvas.ctx.drawImage(img, 0, 0);
                };
                img.src = imageData;
            }
        }
    }
    
    // Resize on window size change
    window.addEventListener('resize', debounce(resizeCanvas, 250));
    
    // Example of creating an API function definition for ML models
    function generateApiFunctionDefinitions() {
        return [
            {
                name: "getState",
                description: "Get the current state of the canvas as a data URL",
                parameters: {}
            },
            {
                name: "clear",
                description: "Clear the canvas",
                parameters: {}
            },
            {
                name: "drawLine",
                description: "Draw a line on the canvas",
                parameters: {
                    x1: "Starting X coordinate (number)",
                    y1: "Starting Y coordinate (number)",
                    x2: "Ending X coordinate (number)",
                    y2: "Ending Y coordinate (number)",
                    color: "Color in hex format (optional, e.g. '#ff0000')",
                    width: "Line width in pixels (optional, default: 5)"
                }
            },
            {
                name: "drawRectangle",
                description: "Draw a rectangle on the canvas",
                parameters: {
                    x: "Top-left X coordinate (number)",
                    y: "Top-left Y coordinate (number)",
                    width: "Width in pixels (number)",
                    height: "Height in pixels (number)",
                    color: "Color in hex format (optional, e.g. '#ff0000')",
                    lineWidth: "Line width in pixels (optional, default: 5)",
                    fill: "Whether to fill the rectangle (optional, boolean, default: false)"
                }
            },
            {
                name: "drawCircle",
                description: "Draw a circle on the canvas",
                parameters: {
                    x: "Center X coordinate (number)",
                    y: "Center Y coordinate (number)",
                    radius: "Radius in pixels (number)",
                    color: "Color in hex format (optional, e.g. '#ff0000')",
                    lineWidth: "Line width in pixels (optional, default: 5)",
                    fill: "Whether to fill the circle (optional, boolean, default: false)"
                }
            },
            {
                name: "drawBrush",
                description: "Draw a brush stroke at a point",
                parameters: {
                    x: "X coordinate (number)",
                    y: "Y coordinate (number)",
                    size: "Brush size in pixels (optional, default: 5)",
                    color: "Color in hex format (optional, e.g. '#ff0000')"
                }
            },
            {
                name: "setColor",
                description: "Set the current drawing color",
                parameters: {
                    color: "Color in hex format (e.g. '#ff0000')"
                }
            },
            {
                name: "setLineWidth",
                description: "Set the current line width",
                parameters: {
                    width: "Width in pixels (number)"
                }
            },
            {
                name: "setTool",
                description: "Set the current drawing tool",
                parameters: {
                    tool: "Tool name (string, one of: 'brush', 'line', 'rectangle', 'circle', 'eraser')"
                }
            }
        ];
    }
    
    // Log API function definitions (can be copied for ML model integration)
    console.log('API Function Definitions:', generateApiFunctionDefinitions());
    
    // Welcome message
    console.log(
        "%c MS Paint AI Ready! ",
        "background: #4CAF50; color: white; font-size: 16px; padding: 10px;"
    );
});