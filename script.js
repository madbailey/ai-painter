const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');
const promptInput = document.getElementById('prompt');
const generateBtn = document.getElementById('generate');  // Corrected ID
const captureBtn = document.getElementById('capture'); // Keep capture
const clearBtn = document.getElementById('clear');     // Keep clear
const downloadLink = document.getElementById('downloadLink');

// API endpoint (replace with your actual server URL)
const API_BASE_URL = 'http://127.0.0.1:5000'; // For local testing
// const API_BASE_URL = 'https://your-heroku-app.herokuapp.com'; // Example for Heroku

// Event listener for the "Generate" button
generateBtn.addEventListener('click', async () => {
    const prompt = promptInput.value;
    if (!prompt) {
        alert('Please enter a prompt.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = result.image_data;
    } catch (error) {
        console.error('Error:', error);
    }
});

// Capture Image (Keep this functionality)
captureBtn.addEventListener('click', () => {
    const image = canvas.toDataURL('image/png');
    downloadLink.href = image;
    downloadLink.download = 'canvas_image.png';
    downloadLink.style.display = 'block';
    downloadLink.click();
    downloadLink.style.display = 'none';
});

// Clear Canvas (Keep this functionality)
clearBtn.addEventListener('click', () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
});
