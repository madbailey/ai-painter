const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');
const promptInput = document.getElementById('prompt');
const generateBtn = document.getElementById('generate');
const captureBtn = document.getElementById('capture');
const clearBtn = document.getElementById('clear');
const downloadLink = document.getElementById('downloadLink');
const statusDiv = document.getElementById('status');

// Initialize canvas
function initCanvas() {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}
initCanvas();

const API_BASE_URL = 'http://127.0.0.1:5000';

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
            body: JSON.stringify({ prompt: prompt, iteration: currentIteration, current_image: currentImageData })
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

    console.log("Starting new drawing.");
    isDrawing = true;
    currentIteration = 0;
    commandQueue = [];
    if (drawingTimerId) {
        clearTimeout(drawingTimerId);
        drawingTimerId = null;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    initCanvas();
    currentImageData = canvas.toDataURL('image/png');

    generateBtn.disabled = true;
    setStatus('Getting initial commands...', 'loading');

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