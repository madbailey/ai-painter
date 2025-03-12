"""
API routes for the Flask application.
"""

import json
import re
from io import BytesIO
from flask import request, jsonify, send_file
from PIL import Image

from utils.image import data_uri_to_image, image_to_data_uri
from utils.text import clean_json_string, extract_thinking
from drawing.processor import process_drawing_command
from ai.model import get_model
from ai.prompts import get_initial_composition_prompt, get_continuation_prompt, format_command_history
from config.phases import PHASES, GENERATION_CONFIG

def register_routes(app):
    """
    Register API routes with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/draw_command', methods=['POST'])
    def draw_command():
        """Process a drawing command"""
        data = request.get_json()
        command = data.get('command', {})
        image_data = data.get('image_data')
        
        if not image_data or not command or 'action' not in command:
            return jsonify({'error': 'Invalid command or data'}), 400
            
        updated_image_data = process_drawing_command(image_data, command)
        return jsonify({'image_data': updated_image_data})

    @app.route('/get_commands', methods=['POST'])
    def get_commands():
        """Get drawing commands from Gemini"""
        data = request.get_json()
        prompt = data.get('prompt')
        current_phase = data.get('phase', 'composition')  # Default to composition phase
        current_part = data.get('part', 0)  # Default to first part (0-indexed)
        current_image = data.get('current_image')
        command_history = data.get('command_history', [])

        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        try:
            # Format the command history for readability
            history_text = format_command_history(command_history)
                
            # Find the current phase details
            phase_info = next((phase for phase in PHASES if phase["name"] == current_phase), PHASES[0])
            
            # Determine next part or phase
            next_part = current_part + 1
            next_phase = current_phase
            
            # If we've reached the end of parts for this phase, move to the next phase
            if next_part >= len(phase_info["parts"]):
                next_part = 0
                phase_index = next((i for i, p in enumerate(PHASES) if p["name"] == current_phase), 0)
                if phase_index < len(PHASES) - 1:
                    next_phase = PHASES[phase_index + 1]["name"]
            
            has_more = not (next_phase == PHASES[-1]["name"] and next_part == len(PHASES[-1]["parts"]) - 1)
            
            # Get the AI model
            model = get_model()
            if not model:
                return jsonify({'error': 'AI model not initialized'}), 500
            
            # Build different prompts based on phase and part
            if current_phase == 'composition' and current_part == 0:
                # Initial composition, first part
                prompt_text = get_initial_composition_prompt(prompt, history_text)
            else:
                # All other phases and parts
                if not current_image:
                    return jsonify({'error': 'No current image provided'}), 400
                
                img = data_uri_to_image(current_image)
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                image_part = {"mime_type": "image/png", "data": buffered.getvalue()}
                
                prompt_text = get_continuation_prompt(
                    prompt, 
                    current_phase, 
                    current_part, 
                    image_part, 
                    history_text
                )

            # Generate content from AI
            response = model.generate_content(prompt_text, generation_config=GENERATION_CONFIG)
            print(f"Raw Gemini Response (Phase: {current_phase}, Part: {current_part}):")
            print(response.text)
            
            # Extract and print thinking if present
            thinking = extract_thinking(response.text)
            if thinking:
                print(f"\nGemini's Reasoning:\n{'-'*50}\n{thinking}\n{'-'*50}")
            
            # Clean and parse the JSON response
            commands_str = clean_json_string(response.text)

            try:
                commands = json.loads(commands_str)
                if not isinstance(commands, list):
                    raise ValueError("Response is not a JSON array")
                    
                return jsonify({
                    'commands': commands, 
                    'current_phase': current_phase,
                    'current_part': current_part,
                    'next_phase': next_phase,
                    'next_part': next_part,
                    'has_more': has_more,
                    'thinking': thinking  # Include the thinking for UI display
                })
                
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                # Attempt aggressive cleaning
                clean_attempt = re.sub(r'[^{}[\],:"0-9a-zA-Z_\-\.\s]', '', commands_str)
                print(f"Aggressive clean: {clean_attempt[:100]}...")
                
                try:
                    commands = json.loads(clean_attempt)
                    return jsonify({
                        'commands': commands, 
                        'current_phase': current_phase,
                        'current_part': current_part,
                        'next_phase': next_phase,
                        'next_part': next_part,
                        'has_more': has_more,
                        'thinking': thinking
                    })
                except:
                    raise ValueError(f"Could not parse JSON: {e}")

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'error': str(e)}), 500