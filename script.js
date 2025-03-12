const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');
const promptInput = document.getElementById('prompt');
const generateBtn = document.getElementById('generate');
const captureBtn = document.getElementById('capture');
const clearBtn = document.getElementById('clear');
const downloadLink = document.getElementById('downloadLink');
const statusDiv = document.getElementById('status');

// Initialize canvas with white background
function initCanvas() {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

// Run initialization
initCanvas();

// API endpoint
const API_BASE_URL = 'http://127.0.0.1:5000'; // For local testing

// Function to set status message
function setStatus(message, type = 'info') {
    statusDiv.textContent = message;
    statusDiv.className = type;
    statusDiv.style.display = 'block';
}

// Function to clear status message
function clearStatus() {
    statusDiv.textContent = '';
    statusDiv.style.display = 'none';
}

// Global state
let isDrawing = false;
let currentImageData = null;
let commandQueue = [];
let currentIteration = 0;
let prompt = '';
let drawingTimerId = null;

// Process the next command in the queue
async function processNextCommand() {
  if (!commandQueue.length) {
      if (currentIteration >= 0) {
          // If we've completed an iteration, get more commands
          await getMoreCommands();
      } else {
          // If we're done with all iterations
          isDrawing = false;
          setStatus('Drawing complete!', 'success');
          setTimeout(clearStatus, 3000);
          generateBtn.textContent = 'Generate with Gemini';
          generateBtn.disabled = false;
      }
      return;
  }

  const command = commandQueue.shift();
  
  try {
      console.log("Processing command:", command);
      setStatus(`Drawing... (${commandQueue.length} commands remaining)`, 'info');
      
      const response = await fetch(`${API_BASE_URL}/draw_command`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({
              command: command,
              image_data: currentImageData
          }),
          // Add timeout to fetch to prevent hanging
          signal: AbortSignal.timeout(5000) // 5 second timeout
      });

      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.error) {
          console.error('Server error:', result.error);
          // Don't stop on error, continue with next command
          if (drawingTimerId) clearTimeout(drawingTimerId);
          drawingTimerId = setTimeout(processNextCommand, 100);
          return;
      }
      
      // Update the current image data
      currentImageData = result.image_data;
      
      // Display the updated image directly without creating a new Image object
      const img = new Image();
      img.onload = () => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0);
          
          // Process the next command after a short delay (for animation effect)
          if (drawingTimerId) clearTimeout(drawingTimerId);
          drawingTimerId = setTimeout(processNextCommand, 200);
      };
      img.onerror = () => {
          console.error('Error loading image');
          // Continue anyway
          if (drawingTimerId) clearTimeout(drawingTimerId);
          drawingTimerId = setTimeout(processNextCommand, 100);
      };
      img.src = currentImageData;
      
  } catch (error) {
      console.error('Error executing command:', error);
      // Continue with next command even if there's an error
      if (drawingTimerId) clearTimeout(drawingTimerId);
      drawingTimerId = setTimeout(processNextCommand, 100);
  }
}

// Get more commands from the server
async function getMoreCommands() {
    try {
        setStatus(`Thinking about the next drawing steps (iteration ${currentIteration + 1})...`, 'loading');
        
        const response = await fetch(`${API_BASE_URL}/get_commands`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                iteration: currentIteration,
                current_image: currentImageData
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.error) {
            console.error('Server error:', result.error);
            setStatus(`Error: ${result.error}`, 'error');
            isDrawing = false;
            return;
        }
        
        // Update iteration counter
        currentIteration = result.iteration;
        
        // Add commands to the queue
        commandQueue = [...commandQueue, ...result.commands];
        
        setStatus(`Drawing iteration ${currentIteration}...`, 'info');
        
        // Start processing commands if not already doing so
        if (drawingTimerId === null) {
            processNextCommand();
        }
        
        // If no more iterations, indicate we're done
        if (!result.has_more) {
            // We'll finish the queue, but won't request more after that
            currentIteration = -1;
        }
        
    } catch (error) {
        console.error('Error getting commands:', error);
        setStatus(`Error: ${error.message}`, 'error');
        isDrawing = false;
    }
}

// Event listener for the "Generate" button
generateBtn.addEventListener('click', async () => {
    prompt = promptInput.value;
    if (!prompt) {
        alert('Please enter a prompt.');
        return;
    }
    
    // Don't allow starting a new drawing if one is in progress
    if (isDrawing) {
        alert('A drawing is already in progress. Please wait or clear the canvas.');
        return;
    }
    
    // Reset state
    isDrawing = true;
    currentIteration = 0;
    commandQueue = [];
    if (drawingTimerId) {
        clearTimeout(drawingTimerId);
        drawingTimerId = null;
    }
    
    // Clear canvas and initialize
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    initCanvas();
    
    // Get the initial canvas data
    currentImageData = canvas.toDataURL('image/png');
    
    // Show loading indication
    generateBtn.disabled = true;
    setStatus('Getting initial drawing commands...', 'loading');
    
    try {
        // Start the command generation and drawing process
        await getMoreCommands();
    } catch (error) {
        console.error('Error:', error);
        setStatus(`Failed to generate: ${error.message}`, 'error');
        isDrawing = false;
    } finally {
        // Reset button state
        generateBtn.disabled = false;
    }
});

// Capture Image
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

// Clear Canvas
clearBtn.addEventListener('click', () => {
    // Stop any current drawing
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