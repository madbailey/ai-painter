const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');
const promptInput = document.getElementById('prompt');
const generateBtn = document.getElementById('generate');
const captureBtn = document.getElementById('capture');
const clearBtn = document.getElementById('clear');
const downloadLink = document.getElementById('downloadLink');
const statusDiv = document.getElementById('status');
const manualClearBtn = document.getElementById('manual-clear');
const manualSaveBtn = document.getElementById('manual-save');
const brushSizeSlider = document.getElementById('brush-size');
const sizeValueSpan = document.getElementById('size-value');
const fillToggle = document.getElementById('fill-toggle');

// Mode switching
const modeButtons = document.querySelectorAll('.mode-button');
const aiTools = document.getElementById('ai-tools');
const manualTools = document.getElementById('manual-tools');

// Tool selection
const tools = document.querySelectorAll('.tool');
const colorOptions = document.querySelectorAll('.color-option');

// Drawing state for manual mode
let isDrawingManual = false;
let lastX = 0;
let lastY = 0;
let currentTool = 'brush';
let currentColor = '#000000';
let brushSize = 2;
let fillShapes = false;
let drawingMode = 'ai'; // 'ai' or 'manual'

// Initialize polyline tracking
window.currentPolyline = null;

// Shape drawing state
let startX = 0;
let startY = 0;

// Initialize canvas
function initCanvas() {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}
initCanvas();

const API_BASE_URL = 'http://127.0.0.1:5000';

// AI Drawing Mode Functions
function setStatus(message, type = 'info') {
    statusDiv.textContent = message;
    statusDiv.className = type;
    statusDiv.style.display = 'block';
}

function clearStatus() {
    statusDiv.textContent = '';
    statusDiv.style.display = 'none';
}

let isDrawing = false;
let currentImageData = null;
let commandQueue = [];
let currentIteration = 0;
let prompt = '';
let drawingTimerId = null;
let commandHistory = []; // Add this array to store command history

async function processNextCommand() {
    // ALWAYS clear the timer at the VERY BEGINNING.
    if (drawingTimerId) {
        clearTimeout(drawingTimerId);
        drawingTimerId = null; // Set to null immediately.
    }

    console.log(`processNextCommand called. Queue length: ${commandQueue.length}, isDrawing: ${isDrawing}, drawingTimerId: ${drawingTimerId}`);

    if (!commandQueue.length) {
        console.log("Command queue is empty.");
        if (isDrawing) {
            console.log("Calling getMoreCommands from processNextCommand");
            await getMoreCommands();
        } else {
            console.log("isDrawing is false, not getting more commands.");
            setStatus('Drawing complete!', 'success');
            setTimeout(clearStatus, 3000);
        }
        return;
    }

    const command = commandQueue.shift();
    console.log("Processing command:", command);
    
    // Add command to history
    commandHistory.push(command);

    try {
        const response = await fetch(`${API_BASE_URL}/draw_command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command, image_data: currentImageData })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log("Draw command result:", result);

        if (result.error) {
            console.error('Server error:', result.error);
        } else {
            currentImageData = result.image_data;
            const img = new Image();
            img.onload = () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                console.log("Image updated. Scheduling next command.");
                // Only set the timeout if the queue is NOT empty
                if(commandQueue.length > 0){
                    drawingTimerId = setTimeout(processNextCommand, 200);
                } else if (isDrawing){
                    // If the queue IS empty, but we expect more, get them
                    getMoreCommands()
                }
            };
            img.onerror = () => {
                console.error('Error loading image');
                 if(commandQueue.length > 0){
                    drawingTimerId = setTimeout(processNextCommand, 200);
                } else if (isDrawing) {
                     getMoreCommands()
                }
            };
            img.src = currentImageData;
        }

    } catch (error) {
        console.error('Error executing command:', error);
          if(commandQueue.length > 0){
            drawingTimerId = setTimeout(processNextCommand, 200);
         } else if (isDrawing){
             getMoreCommands();
         }
    }
}

async function getMoreCommands() {
    console.log(`getMoreCommands called. Iteration: ${currentIteration}, isDrawing: ${isDrawing}`);

    try {
        setStatus(`Thinking... (iteration ${currentIteration + 1})`, 'loading');

        const response = await fetch(`${API_BASE_URL}/get_commands`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                prompt: prompt, 
                iteration: currentIteration, 
                current_image: currentImageData,
                command_history: commandHistory // Send the command history
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log("getMoreCommands result:", result);

        if (result.error) {
            console.error('Server error:', result.error);
            setStatus(`Error: ${result.error}`, 'error');
            isDrawing = false;
            return;
        }

        currentIteration++;

        if (!result.has_more) {
            console.log("has_more is false. Setting isDrawing to false.");
            isDrawing = false;
        }

        commandQueue = [...commandQueue, ...result.commands];
        console.log(`Commands added to queue. New queue length: ${commandQueue.length}`);

        setStatus(`Drawing... (iteration ${currentIteration})`, 'info');

        //  Only call processNextCommand if drawingTimerId is null AND the queue is not empty
        if (drawingTimerId === null && commandQueue.length > 0) {
            console.log("drawingTimerId is null and queue has commands. Starting processNextCommand.");
            processNextCommand();
        } else {
            console.log("drawingTimerId exists or queue is empty, not starting processNextCommand.");
        }

    } catch (error) {
        console.error('Error getting commands:', error);
        setStatus(`Error: ${error.message}`, 'error');
        isDrawing = false;
    }
}

// Manual drawing functions
function startDraw(e) {
    if (drawingMode !== 'manual') return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentTool === 'brush' || currentTool === 'eraser') {
        isDrawingManual = true;
        lastX = x;
        lastY = y;
        
        // Draw a dot at the starting point
        ctx.beginPath();
        ctx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
        if (currentTool === 'eraser') {
            ctx.fillStyle = 'white';
        } else {
            ctx.fillStyle = currentColor;
        }
        ctx.fill();
    } else if (currentTool === 'fill') {
        // Use the backend for fill operation
        const command = {
            action: 'fill_area',
            x: x,
            y: y,
            color: currentColor
        };
        
        // Add fill command to history
        commandHistory.push(command);
        console.log("Added fill command to history:", command);
        
        // Save current canvas state before fill
        currentImageData = canvas.toDataURL('image/png');
        
        // Call API to perform fill
        fetch(`${API_BASE_URL}/draw_command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command, image_data: currentImageData })
        })
        .then(response => response.json())
        .then(result => {
            if (result.image_data) {
                const img = new Image();
                img.onload = () => {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.drawImage(img, 0, 0);
                };
                img.src = result.image_data;
                currentImageData = result.image_data;
            }
        })
        .catch(error => console.error('Error:', error));
    } else if (currentTool === 'rect' || currentTool === 'circle') {
        isDrawingManual = true;
        startX = x;
        startY = y;
    }
}

function draw(e) {
    if (!isDrawingManual || drawingMode !== 'manual') return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentTool === 'brush' || currentTool === 'eraser') {
        // Draw line
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.lineWidth = brushSize;
        ctx.lineCap = 'round';
        
        if (currentTool === 'eraser') {
            ctx.strokeStyle = 'white';
        } else {
            ctx.strokeStyle = currentColor;
        }
        
        ctx.stroke();
        
        // Track line segments for command history
        if (!window.currentPolyline) {
            window.currentPolyline = {
                action: currentTool === 'eraser' ? 'erase' : 'draw_polyline',
                points: [[lastX, lastY]],
                color: currentTool === 'eraser' ? 'white' : currentColor,
                width: brushSize
            };
        }
        
        // Add point to current polyline (limiting to avoid too many points)
        if (window.currentPolyline.points.length < 20) {
            window.currentPolyline.points.push([x, y]);
        } else if (window.currentPolyline.points.length === 20) {
            // If we reach 20 points, finish this polyline and start a new one
            commandHistory.push(window.currentPolyline);
            window.currentPolyline = {
                action: currentTool === 'eraser' ? 'erase' : 'draw_polyline',
                points: [[x, y]],
                color: currentTool === 'eraser' ? 'white' : currentColor,
                width: brushSize
            };
        }
        
        lastX = x;
        lastY = y;
    } else if (currentTool === 'rect' || currentTool === 'circle') {
        // For preview, we can just redraw the canvas from the saved state
        if (!currentImageData) {
            currentImageData = canvas.toDataURL('image/png');
        }
        
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            
            // Draw preview rectangle or circle
            if (currentTool === 'rect') {
                if (fillShapes) {
                    ctx.fillStyle = currentColor;
                    ctx.fillRect(startX, startY, x - startX, y - startY);
                } else {
                    ctx.strokeStyle = currentColor;
                    ctx.lineWidth = brushSize;
                    ctx.strokeRect(startX, startY, x - startX, y - startY);
                }
            } else if (currentTool === 'circle') {
                const radiusX = Math.abs(x - startX);
                const radiusY = Math.abs(y - startY);
                const radius = Math.max(radiusX, radiusY);
                
                ctx.beginPath();
                ctx.arc(startX, startY, radius, 0, Math.PI * 2);
                if (fillShapes) {
                    ctx.fillStyle = currentColor;
                    ctx.fill();
                } else {
                    ctx.strokeStyle = currentColor;
                    ctx.lineWidth = brushSize;
                    ctx.stroke();
                }
            }
        };
        img.src = currentImageData;
    }
}

function endDraw() {
    if (drawingMode !== 'manual') return;
    
    if (isDrawingManual) {
        // Handle polyline commands
        if ((currentTool === 'brush' || currentTool === 'eraser') && window.currentPolyline) {
            // Add the current polyline to the command history
            if (window.currentPolyline.points.length > 1) {
                commandHistory.push(window.currentPolyline);
                console.log("Added polyline to history:", window.currentPolyline);
            }
            window.currentPolyline = null;
        }
        
        // Handle shape commands
        if (currentTool === 'rect' || currentTool === 'circle') {
            let manualCommand = null;
            
            if (currentTool === 'rect') {
                manualCommand = {
                    action: 'draw_rect',
                    x0: startX,
                    y0: startY,
                    x1: lastX,
                    y1: lastY,
                    color: currentColor,
                    width: brushSize,
                    fill: fillShapes
                };
            } else if (currentTool === 'circle') {
                const radius = Math.max(
                    Math.abs(lastX - startX),
                    Math.abs(lastY - startY)
                );
                manualCommand = {
                    action: 'draw_circle',
                    x: startX,
                    y: startY,
                    radius: radius,
                    color: currentColor,
                    width: brushSize,
                    fill: fillShapes
                };
            }
            
            if (manualCommand) {
                commandHistory.push(manualCommand);
                console.log("Added manual command to history:", manualCommand);
            }
        }
        
        // Update the current image data to include the shape
        currentImageData = canvas.toDataURL('image/png');
    }
    
    isDrawingManual = false;
}

// Event Listeners for Manual Drawing
canvas.addEventListener('mousedown', startDraw);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseup', endDraw);
canvas.addEventListener('mouseout', endDraw);

// Update brush size display
brushSizeSlider.addEventListener('input', function() {
    brushSize = this.value;
    sizeValueSpan.textContent = brushSize;
});

// Fill toggle
fillToggle.addEventListener('change', function() {
    fillShapes = this.checked;
});

// Tool selection
tools.forEach(tool => {
    tool.addEventListener('click', function() {
        tools.forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        currentTool = this.dataset.tool;
    });
});

// Color selection
colorOptions.forEach(option => {
    option.addEventListener('click', function() {
        colorOptions.forEach(o => o.classList.remove('active'));
        this.classList.add('active');
        currentColor = this.dataset.color;
    });
});

// Mode switching
modeButtons.forEach(button => {
    button.addEventListener('click', function() {
        modeButtons.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        
        drawingMode = this.dataset.mode;
        
        if (drawingMode === 'ai') {
            aiTools.style.display = 'block';
            manualTools.style.display = 'none';
        } else {
            aiTools.style.display = 'none';
            manualTools.style.display = 'block';
        }
    });
});

// AI Drawing Mode Event Listeners
generateBtn.addEventListener('click', async () => {
    prompt = promptInput.value;
    if (!prompt) {
        alert('Please enter a prompt.');
        return;
    }

    if (isDrawing) {
        alert('Drawing in progress. Please wait or clear.');
        return;
    }

    console.log("Starting or continuing drawing.");
    isDrawing = true;
    currentIteration = 0;
    commandQueue = [];
    commandHistory = []; // Clear command history for new drawing
    if (drawingTimerId) {
        clearTimeout(drawingTimerId);
        drawingTimerId = null;
    }

    // Preserve existing drawing if there is one
    // Just use the current canvas state as the starting point
    currentImageData = canvas.toDataURL('image/png');

    generateBtn.disabled = true;
    // Check if we're starting from an empty canvas or enhancing existing work
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const isEmpty = !Array.from(imageData.data).some((channel, i) => (i % 4 !== 3) && channel !== 255); // Check if all non-alpha channels are white
    
    if (isEmpty) {
        setStatus('Getting initial commands...', 'loading');
        commandHistory = []; // Clear history for a blank canvas
    } else {
        setStatus('Enhancing your drawing...', 'loading');
        // If we're enhancing, we keep the existing command history
    }

    try {
        await getMoreCommands();
    } catch (error) {
        console.error('Error:', error);
        setStatus(`Failed to generate: ${error.message}`, 'error');
        isDrawing = false;
    } finally {
        generateBtn.disabled = false;
    }
});

captureBtn.addEventListener('click', () => {
    const image = canvas.toDataURL('image/png');
    downloadLink.href = image;
    downloadLink.download = 'canvas_image.png';
    downloadLink.style.display = 'block';
    downloadLink.click();
    downloadLink.style.display = 'none';
    setStatus('Image saved!', 'success');
    setTimeout(clearStatus, 3000);
});

clearBtn.addEventListener('click', () => {
    console.log("Clearing canvas.");
    if (isDrawing) {
        isDrawing = false;
        commandQueue = [];
        if (drawingTimerId) {
            clearTimeout(drawingTimerId);
            drawingTimerId = null;
        }
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    initCanvas();
    currentImageData = canvas.toDataURL('image/png');
    setStatus('Canvas cleared', 'info');
    setTimeout(clearStatus, 2000);
});

// Manual mode clear and save
manualClearBtn.addEventListener('click', () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    initCanvas();
    currentImageData = canvas.toDataURL('image/png');
});

manualSaveBtn.addEventListener('click', () => {
    const image = canvas.toDataURL('image/png');
    downloadLink.href = image;
    downloadLink.download = 'manual_drawing.png';
    downloadLink.style.display = 'block';
    downloadLink.click();
    downloadLink.style.display = 'none';
});