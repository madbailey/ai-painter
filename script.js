// Initialize canvas and UI elements
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

// Initialize drawing worker if supported
let drawingWorker = null;
if (window.Worker) {
  try {
    drawingWorker = new Worker('drawing-worker.js');
    console.log('Drawing worker initialized');
    
    // Set up worker message handling
    drawingWorker.onmessage = function(e) {
      const { type, data, error } = e.data;
      
      switch (type) {
        case 'init_complete':
          console.log('Worker initialization complete');
          break;
          
        case 'command_processed':
          handleCommandProcessed(data.command, data.imageData);
          break;
          
        case 'commands_received':
          handleCommandsReceived(data);
          break;
          
        case 'error':
          console.error('Worker error:', error);
          setStatus(`Error: ${error}`, 'error');
          isDrawing = false;
          break;
      }
    };
    
    // Initialize worker with API base URL
    drawingWorker.postMessage({
      type: 'init',
      data: {
        apiBaseUrl: 'http://127.0.0.1:5000'
      }
    });
  } catch (error) {
    console.error('Failed to initialize drawing worker:', error);
    drawingWorker = null;
  }
} else {
  console.log('Web Workers not supported in this browser. Falling back to direct API calls.');
}

//phase definitions
const PHASES = [
  {
    name: 'composition',
    displayName: 'Composition',
    description: 'Setting up the basic forms and layout',
    parts: 2
  },
  {
    name: 'color_blocking',
    displayName: 'Color Blocking',
    description: 'Establishing main color areas and base tones',
    parts: 2
  },
  {
    name: 'detailing',
    displayName: 'Detailing',
    description: 'Adding definition, mid-tones and texture',
    parts: 2
  },
  {
    name: 'final_touches',
    displayName: 'Final Touches',
    description: 'Refining details and adding highlights',
    parts: 2
  }
];



let currentPhase = 'composition';
let currentPhaseIndex = 0;
let currentPart = 0;
let nextPartToTransition = 0;
let nextPhaseToTransition = null;

// Drawing state for manual mode
let isDrawingManual = false;
let lastX = 0;
let lastY = 0;
let currentTool = 'brush';
let currentColor = '#000000';
let brushSize = 2;
let fillShapes = false;
let drawingMode = 'ai'; // 'ai' or 'manual'
let currentBrushType = 'round';  // Default brush type
let currentTexture = 'smooth';   // Default texture
let currentPressure = 1.0;     

// Initialize polyline tracking
window.currentPolyline = null;

// Shape drawing state
let startX = 0;
let startY = 0;

function createPhaseIndicator() {
  // Create phase indicator container if it doesn't exist
  if (!document.getElementById('phase-indicator')) {
    const indicatorContainer = document.createElement('div');
    indicatorContainer.id = 'phase-indicator';
    indicatorContainer.className = 'phase-indicator';
    indicatorContainer.style.cssText = 'display: flex; justify-content: space-between; margin-bottom: 15px; background-color: white; padding: 10px; border-radius: 4px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);';
    
    // Create indicators for each phase
    PHASES.forEach((phase, index) => {
      const phaseElement = document.createElement('div');
      phaseElement.id = `phase-${phase.name}`;
      phaseElement.className = 'phase-step';
      phaseElement.dataset.phase = phase.name;
      
      // Add main phase content
      phaseElement.innerHTML = `
        <div class="phase-number" style="width: 28px; height: 28px; border-radius: 50%; background-color: #e0e0e0; display: flex; align-items: center; justify-content: center; margin: 0 auto 5px;">${index + 1}</div>
        <div class="phase-name" style="font-size: 12px; text-align: center;">${phase.displayName}</div>
        <div class="phase-parts" style="display: flex; justify-content: center; margin-top: 5px;"></div>
      `;
      
      // Add the part indicators
      const partsContainer = phaseElement.querySelector('.phase-parts');
      for (let i = 0; i < phase.parts; i++) {
        const partDot = document.createElement('div');
        partDot.className = 'part-indicator';
        partDot.dataset.part = i;
        partDot.style.cssText = 'width: 8px; height: 8px; border-radius: 50%; background-color: #e0e0e0; margin: 0 2px; transition: all 0.3s;';
        partsContainer.appendChild(partDot);
      }
      
      phaseElement.style.cssText = 'flex: 1; padding: 5px; opacity: 0.6; cursor: pointer;';
      
      // Add event listener to allow clicking on phases
      phaseElement.addEventListener('click', () => {
        if (isDrawing) return; // Prevent changing phases during active drawing
        
        const clickedPhaseIndex = PHASES.findIndex(p => p.name === phase.name);
        const currentPhaseIndex = PHASES.findIndex(p => p.name === currentPhase);
        
        // Only allow moving to completed phases or the next phase
        if (clickedPhaseIndex <= currentPhaseIndex || clickedPhaseIndex === currentPhaseIndex + 1) {
          if (confirm(`Switch to ${phase.displayName} phase?`)) {
            setCurrentPhase(phase.name);
            currentPart = 0; // Reset to first part of the selected phase
            updatePhaseIndicator();
          }
        } else {
          alert("You must complete the current phase before moving to this phase.");
        }
      });
      
      indicatorContainer.appendChild(phaseElement);
    });
    
    // Add connecting lines between phases
    for (let i = 0; i < PHASES.length - 1; i++) {
      const connector = document.createElement('div');
      connector.className = 'phase-connector';
      connector.style.cssText = 'flex: 0.5; height: 2px; background-color: #e0e0e0; margin-top: 12px;';
      indicatorContainer.insertBefore(connector, indicatorContainer.children[i*2 + 1]);
    }
    
    // Insert before canvas container
    const canvasContainer = document.getElementById('canvas-container');
    canvasContainer.parentNode.insertBefore(indicatorContainer, canvasContainer);
    
    // Add thinking container
    const thinkingContainer = document.createElement('div');
    thinkingContainer.id = 'ai-thinking';
    thinkingContainer.className = 'ai-thinking';
    thinkingContainer.style.cssText = 'display: none; margin-top: 10px; background-color: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 14px; line-height: 1.5; max-height: 150px; overflow-y: auto;';
    
    // Add toggle button
    const thinkingToggle = document.createElement('button');
    thinkingToggle.id = 'thinking-toggle';
    thinkingToggle.className = 'thinking-toggle';
    thinkingToggle.textContent = 'Show AI Thinking';
    thinkingToggle.style.cssText = 'margin-top: 10px; padding: 5px 10px; background-color: #f1f1f1; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; cursor: pointer;';
    thinkingToggle.addEventListener('click', () => {
      const aiThinking = document.getElementById('ai-thinking');
      if (aiThinking.style.display === 'none') {
        aiThinking.style.display = 'block';
        thinkingToggle.textContent = 'Hide AI Thinking';
      } else {
        aiThinking.style.display = 'none';
        thinkingToggle.textContent = 'Show AI Thinking';
      }
    });
    
    // Add below the controls
    const controls = document.getElementById('ai-tools');
    controls.appendChild(thinkingToggle);
    controls.appendChild(thinkingContainer);
  }
}


function updatePhaseIndicator() {
  PHASES.forEach(phase => {
    const phaseElement = document.getElementById(`phase-${phase.name}`);
    if (phaseElement) {
      // Update phase styling
      if (phase.name === currentPhase) {
        phaseElement.style.opacity = '1';
        phaseElement.querySelector('.phase-number').style.backgroundColor = '#4285f4';
        phaseElement.querySelector('.phase-number').style.color = 'white';
      } else {
        const phaseIndex = PHASES.findIndex(p => p.name === phase.name);
        const currentIndex = PHASES.findIndex(p => p.name === currentPhase);
        
        if (phaseIndex < currentIndex) {
          // Completed phases
          phaseElement.style.opacity = '1';
          phaseElement.querySelector('.phase-number').style.backgroundColor = '#0f9d58';
          phaseElement.querySelector('.phase-number').style.color = 'white';
        } else {
          // Future phases
          phaseElement.style.opacity = '0.6';
          phaseElement.querySelector('.phase-number').style.backgroundColor = '#e0e0e0';
          phaseElement.querySelector('.phase-number').style.color = 'black';
        }
      }
      
      // Update part indicators
      const partIndicators = phaseElement.querySelectorAll('.part-indicator');
      partIndicators.forEach((indicator, partIndex) => {
        if (phase.name === currentPhase) {
          if (partIndex < currentPart) {
            // Completed parts of current phase
            indicator.style.backgroundColor = '#0f9d58';
          } else if (partIndex === currentPart) {
            // Current part
            indicator.style.backgroundColor = '#4285f4';
          } else {
            // Future parts
            indicator.style.backgroundColor = '#e0e0e0';
          }
        } else if (phase.name === nextPhaseToTransition) {
          // Highlight the first part of the next phase if transitioning
          if (partIndex === 0) {
            indicator.style.backgroundColor = '#ffa000';  // Orange for next up
          } else {
            indicator.style.backgroundColor = '#e0e0e0';
          }
        } else {
          const phaseIndex = PHASES.findIndex(p => p.name === phase.name);
          const currentIndex = PHASES.findIndex(p => p.name === currentPhase);
          
          if (phaseIndex < currentIndex) {
            // Completed phase - all parts are green
            indicator.style.backgroundColor = '#0f9d58';
          } else {
            // Future phase - all parts are gray
            indicator.style.backgroundColor = '#e0e0e0';
          }
        }
      });
    }
  });
  
  // Update connectors
  const connectors = document.querySelectorAll('.phase-connector');
  const currentIndex = PHASES.findIndex(p => p.name === currentPhase);
  
  connectors.forEach((connector, index) => {
    if (index < currentIndex) {
      connector.style.backgroundColor = '#0f9d58';
    } else {
      connector.style.backgroundColor = '#e0e0e0';
    }
  });
  
  // Update status text with current phase and part
  const currentPhaseObj = PHASES.find(p => p.name === currentPhase);
  if (currentPhaseObj) {
    setStatus(`${currentPhaseObj.displayName} - Part ${currentPart + 1}/${currentPhaseObj.parts}: ${currentPhaseObj.description}`, 'info');
  }
}

function setCurrentPhase(phaseName, part = 0) {
  if (PHASES.some(p => p.name === phaseName)) {
    currentPhase = phaseName;
    currentPhaseIndex = PHASES.findIndex(p => p.name === phaseName);
    currentPart = part;
  }
}
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

function updateBrushPreview() {
  const previewCanvas = document.getElementById('brush-preview');
  if (!previewCanvas) return;
  
  const previewCtx = previewCanvas.getContext('2d');
  previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);
  
  // Draw a sample stroke
  const centerY = previewCanvas.height / 2;
  
  if (currentTool === 'brush') {
      if (currentBrushType === 'round') {
          // Show a tapered stroke
          previewCtx.beginPath();
          previewCtx.moveTo(10, centerY);
          previewCtx.lineTo(previewCanvas.width - 10, centerY);
          previewCtx.lineWidth = brushSize;
          previewCtx.lineCap = 'round';
          previewCtx.strokeStyle = currentColor;
          previewCtx.stroke();
          
          // Add some dots to simulate tapering
          const gradient = previewCtx.createLinearGradient(10, 0, previewCanvas.width - 10, 0);
          gradient.addColorStop(0, currentColor);
          gradient.addColorStop(0.5, currentColor);
          gradient.addColorStop(1, currentColor);
          
          previewCtx.fillStyle = gradient;
          const steps = 5;
          for (let i = 0; i < steps; i++) {
              const x = 10 + (previewCanvas.width - 20) * (i / (steps - 1));
              const size = brushSize * (0.7 + 0.6 * Math.sin(Math.PI * (i / (steps - 1))));
              previewCtx.beginPath();
              previewCtx.arc(x, centerY, size / 2, 0, Math.PI * 2);
              previewCtx.fill();
          }
      } else if (currentBrushType === 'flat') {
          // Show an angled flat brush stroke
          const angle = Math.PI / 4; // 45 degrees
          const length = previewCanvas.width - 20;
          const startX = 10;
          const startY = centerY;
          const endX = startX + length * Math.cos(angle);
          const endY = startY + length * Math.sin(angle);
          
          // Draw the main stroke direction
          previewCtx.beginPath();
          previewCtx.moveTo(startX, startY);
          previewCtx.lineTo(endX, endY);
          previewCtx.setLineDash([5, 3]);
          previewCtx.strokeStyle = '#888';
          previewCtx.lineWidth = 1;
          previewCtx.stroke();
          previewCtx.setLineDash([]);
          
          // Draw some rectangular brush stamps
          const steps = 5;
          for (let i = 0; i < steps; i++) {
              const t = i / (steps - 1);
              const x = startX + (endX - startX) * t;
              const y = startY + (endY - startY) * t;
              
              // Create a rectangle for the brush stamp
              const rect_width = brushSize * 1.5;
              const rect_height = brushSize;
              
              previewCtx.save();
              previewCtx.translate(x, y);
              previewCtx.rotate(angle);
              previewCtx.fillStyle = currentColor;
              previewCtx.fillRect(-rect_width/2, -rect_height/2, rect_width, rect_height);
              previewCtx.restore();
          }
      } else if (currentBrushType === 'splatter') {
          // Show a spray pattern
          const centerX = previewCanvas.width / 2;
          const radius = brushSize * 2;
          const dots = brushSize * 5;
          
          for (let i = 0; i < dots; i++) {
              const angle = Math.random() * Math.PI * 2;
              const distance = Math.random() * radius;
              const x = centerX + distance * Math.cos(angle);
              const y = centerY + distance * Math.sin(angle);
              const dotSize = Math.random() * brushSize / 3 + 1;
              
              previewCtx.beginPath();
              previewCtx.arc(x, y, dotSize, 0, Math.PI * 2);
              previewCtx.fillStyle = currentColor;
              previewCtx.fill();
          }
      }
  } else if (currentTool === 'eraser') {
      // Show eraser preview
      previewCtx.beginPath();
      previewCtx.arc(previewCanvas.width / 2, centerY, brushSize / 2, 0, Math.PI * 2);
      previewCtx.fillStyle = 'white';
      previewCtx.strokeStyle = '#888';
      previewCtx.lineWidth = 1;
      previewCtx.fill();
      previewCtx.stroke();
  }
  
  // Indicate texture
  if (currentTexture === 'rough') {
      previewCtx.font = '10px Arial';
      previewCtx.fillStyle = '#888';
      previewCtx.textAlign = 'center';
      previewCtx.fillText('Rough texture', previewCanvas.width / 2, previewCanvas.height - 5);
  }
  
  // Indicate pressure
  const alpha = Math.round(currentPressure * 255).toString(16).padStart(2, '0');
  previewCtx.font = '10px Arial';
  previewCtx.fillStyle = '#888';
  previewCtx.textAlign = 'center';
  previewCtx.fillText(`Pressure: ${currentPressure.toFixed(1)}`, previewCanvas.width / 2, 15);
}


/**
 * Handle processed command result from worker
 * @param {Object} command - The drawing command that was processed
 * @param {string} updatedImageData - Updated image data URI
 */
function handleCommandProcessed(command, updatedImageData) {
  if (!updatedImageData) {
    console.error('No updated image data received');
    return;
  }
  
  currentImageData = updatedImageData;
  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    console.log("Image updated. Scheduling next command.");
    
    // Only set the timeout if the queue is NOT empty
    if (commandQueue.length > 0) {
      drawingTimerId = setTimeout(processNextCommand, 200);
    } else {
      // If the queue IS empty, processNextCommand will handle phase transitions
      processNextCommand();
    }
  };
  
  img.onerror = () => {
    console.error('Error loading image');
    if (commandQueue.length > 0) {
      drawingTimerId = setTimeout(processNextCommand, 200);
    } else {
      processNextCommand();
    }
  };
  
  img.src = currentImageData;
}

/**
 * Handle commands received from AI
 * @param {Object} result - Result data from the worker
 */
function handleCommandsReceived(result) {
  console.log("getMoreCommands result:", result);

  if (result.error) {
    console.error('Server error:', result.error);
    setStatus(`Error: ${result.error}`, 'error');
    isDrawing = false;
    return;
  }

  // Update phase information
  if (result.next_phase && result.next_phase !== currentPhase) {
    // Store the next phase to transition to after processing commands
    nextPhaseToTransition = result.next_phase;
  } else {
    nextPhaseToTransition = null;
  }

  if (!result.has_more) {
    console.log("has_more is false. Setting isDrawing to false.");
    isDrawing = false;
  }

  // Update the thinking container if available
  if (result.thinking) {
    const thinkingContainer = document.getElementById('ai-thinking');
    const thinkingToggle = document.getElementById('thinking-toggle');
    if (thinkingContainer) {
      thinkingContainer.textContent = result.thinking;
      thinkingContainer.style.display = 'block';
    }
    if (thinkingToggle) {
      thinkingToggle.style.display = 'block';
      thinkingToggle.textContent = 'Hide AI Thinking';
    }
  }

  commandQueue = [...commandQueue, ...result.commands];
  console.log(`Commands added to queue. New queue length: ${commandQueue.length}`);

  updatePhaseIndicator();

  // Only call processNextCommand if drawingTimerId is null AND the queue is not empty
  if (drawingTimerId === null && commandQueue.length > 0) {
    console.log("drawingTimerId is null and queue has commands. Starting processNextCommand.");
    processNextCommand();
  } else {
    console.log("drawingTimerId exists or queue is empty, not starting processNextCommand.");
  }
}

async function processNextCommand() {
  // ALWAYS clear the timer 
  if (drawingTimerId) {
    clearTimeout(drawingTimerId);
    drawingTimerId = null; // Set to null immediately.
  }

  console.log(`processNextCommand called. Queue length: ${commandQueue.length}, isDrawing: ${isDrawing}, phase: ${currentPhase}, part: ${currentPart}`);

  if (!commandQueue.length) {
    console.log("Command queue is empty.");
    
    // If we have a next phase to transition to, do it now
    if (nextPhaseToTransition) {
      console.log(`Transitioning to next phase: ${nextPhaseToTransition}`);
      setCurrentPhase(nextPhaseToTransition);
      nextPhaseToTransition = null;
      updatePhaseIndicator();
      
      if (isDrawing) {
        console.log(`Starting new phase: ${currentPhase}`);
        await getMoreCommands();
      }
    } else if (isDrawing) {
      console.log("Calling getMoreCommands from processNextCommand");
      await getMoreCommands();
    } else {
      console.log("isDrawing is false, not getting more commands.");
      const finalPhase = PHASES[PHASES.length - 1].name;
      if (currentPhase === finalPhase) {
        setStatus('Drawing complete!', 'success');
      } else {
        setStatus(`Phase ${currentPhase} complete. Click Generate to continue to next phase.`, 'success');
      }
    }
    return;
  }

  // Get the next command from the queue
  const command = commandQueue.shift();
  console.log("Processing command:", command);
  
  // Add command to history
  commandHistory.push(command);

  // Process the command using the worker if available, otherwise fallback to direct API call
  if (drawingWorker) {
    drawingWorker.postMessage({
      type: 'process_command',
      data: {
        command: command,
        imageData: currentImageData
      }
    });
  } else {
    // Fallback to direct API call if worker is not available
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

      if (result.error) {
        console.error('Server error:', result.error);
      } else {
        handleCommandProcessed(command, result.image_data);
      }
    } catch (error) {
      console.error('Error executing command:', error);
      if (commandQueue.length > 0) {
        drawingTimerId = setTimeout(processNextCommand, 200);
      } else {
        processNextCommand();
      }
    }
  }
}

async function getMoreCommands() {
  console.log(`getMoreCommands called. Phase: ${currentPhase}, Part: ${currentPart}, isDrawing: ${isDrawing}`);

  try {
    const currentPhaseObj = PHASES.find(p => p.name === currentPhase);
    setStatus(`Working on ${currentPhaseObj.displayName}...`, 'loading');

    const requestData = { 
      prompt: prompt, 
      phase: currentPhase,
      part: currentPart,
      current_image: currentImageData,
      command_history: commandHistory
    };

    // Use the worker if available, otherwise fallback to direct API call
    if (drawingWorker) {
      drawingWorker.postMessage({
        type: 'get_commands',
        data: requestData
      });
    } else {
      // Fallback to direct API call
      const response = await fetch(`${API_BASE_URL}/get_commands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      handleCommandsReceived(result);
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
              width: brushSize,
              brush_type: currentBrushType,  // Add brush type
              texture: currentTexture,       // Add texture
              pressure: currentPressure      // Add pressure
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
              width: brushSize,
              brush_type: currentBrushType,
              texture: currentTexture,
              pressure: currentPressure
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
                  fill: fillShapes,
                  texture: currentTexture  // Add texture
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
                  fill: fillShapes,
                  texture: currentTexture  // Add texture
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
function updateAllBrushSettings() {
  updateBrushPreview();
  
  // Update the current polyline if it exists
  if (window.currentPolyline) {
      window.currentPolyline.brush_type = currentBrushType;
      window.currentPolyline.texture = currentTexture;
      window.currentPolyline.pressure = currentPressure;
  }
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

document.addEventListener('DOMContentLoaded', function() {
  // Add event listeners for brush type buttons
  const brushTypeButtons = document.querySelectorAll('.brush-type-btn');
  if (brushTypeButtons) {
      brushTypeButtons.forEach(btn => {
          btn.addEventListener('click', function() {
              brushTypeButtons.forEach(b => b.classList.remove('active'));
              this.classList.add('active');
              currentBrushType = this.dataset.brushType;
              updateAllBrushSettings();
          });
      });
  }
  
  // Add event listener for texture toggle
  const textureToggle = document.getElementById('texture-toggle');
  if (textureToggle) {
      textureToggle.addEventListener('change', function() {
          currentTexture = this.checked ? 'rough' : 'smooth';
          updateAllBrushSettings();
      });
  }
  
  // Add event listener for pressure slider
  const pressureSlider = document.getElementById('pressure-slider');
  const pressureValue = document.getElementById('pressure-value');
  if (pressureSlider && pressureValue) {
      pressureSlider.addEventListener('input', function() {
          currentPressure = parseFloat(this.value);
          pressureValue.textContent = currentPressure.toFixed(1);
          updateAllBrushSettings();
      });
  }
  
  // Initial update of the brush preview
  updateAllBrushSettings();
  createPhaseIndicator();
  updatePhaseIndicator();
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
  
  // If starting fresh, reset to composition phase
  // If continuing, use the current phase
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const isEmpty = !Array.from(imageData.data).some((channel, i) => (i % 4 !== 3) && channel !== 255);
  
  if (isEmpty) {
      setCurrentPhase('composition');
      currentPart = 0;  // Make sure to reset part to 0
      commandHistory = []; // Clear history for a blank canvas
  }
  
  commandQueue = [];
  nextPhaseToTransition = null;
  nextPartToTransition = null;
  
  if (drawingTimerId) {
      clearTimeout(drawingTimerId);
      drawingTimerId = null;
  }

  // Hide any previous AI thinking
  const aiThinking = document.getElementById('ai-thinking');
  if (aiThinking) {
      aiThinking.style.display = 'none';
  }
  
  const thinkingToggle = document.getElementById('thinking-toggle');
  if (thinkingToggle) {
      thinkingToggle.textContent = 'Show AI Thinking';
      thinkingToggle.style.display = 'none';
  }
  
  // Preserve existing drawing if there is one
  currentImageData = canvas.toDataURL('image/png');

  generateBtn.disabled = true;
  
  try {
      // Create phase indicator on first generate
      createPhaseIndicator();
      updatePhaseIndicator();
      
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