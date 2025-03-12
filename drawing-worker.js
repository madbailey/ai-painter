/**
 * Web Worker for processing drawing commands
 * This worker handles the API calls to process drawing commands,
 * allowing the main thread to remain responsive during painting.
 */

// Cache for API base URL
let API_BASE_URL = 'http://127.0.0.1:5000';

/**
 * Process a single drawing command
 * @param {Object} command - The drawing command to process
 * @param {string} imageData - The current image data URI
 * @returns {Promise} - Promise that resolves with the updated image data
 */
async function processCommand(command, imageData) {
  try {
    const response = await fetch(`${API_BASE_URL}/draw_command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: command, image_data: imageData })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }
    
    return result.image_data;
  } catch (error) {
    console.error('Worker: Error processing command:', error);
    throw error;
  }
}

/**
 * Get commands from the AI for a specific phase/part
 * @param {Object} params - Parameters for the AI command generation
 * @returns {Promise} - Promise that resolves with the AI commands and phase info
 */
async function getCommands(params) {
  try {
    const response = await fetch(`${API_BASE_URL}/get_commands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }
    
    return result;
  } catch (error) {
    console.error('Worker: Error getting commands:', error);
    throw error;
  }
}

// Message handler
self.onmessage = async function(e) {
  const { type, data } = e.data;
  
  try {
    switch (type) {
      case 'init':
        // Set the API base URL
        API_BASE_URL = data.apiBaseUrl;
        self.postMessage({ type: 'init_complete' });
        break;
        
      case 'process_command':
        const { command, imageData } = data;
        const updatedImageData = await processCommand(command, imageData);
        self.postMessage({ 
          type: 'command_processed',
          data: {
            command,
            imageData: updatedImageData
          }
        });
        break;
        
      case 'get_commands':
        const result = await getCommands(data);
        self.postMessage({
          type: 'commands_received',
          data: result
        });
        break;
        
      default:
        console.error('Worker: Unknown message type:', type);
    }
  } catch (error) {
    self.postMessage({
      type: 'error',
      error: error.message
    });
  }
};