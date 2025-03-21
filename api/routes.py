"""
API routes for the Flask application with improved element tracking.
"""

import json
import re
from io import BytesIO
from flask import request, jsonify, send_file
from PIL import Image

from utils.image import data_uri_to_image, image_to_data_uri
from utils.text import clean_json_string, extract_thinking, summarize_command_history
from drawing.processor import process_drawing_command
from ai.model import get_model
from ai.prompts import get_initial_sketch_prompt, get_continuation_prompt, format_command_history
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

    @app.route('/reset_drawing', methods=['POST'])
    def reset_drawing():
        """Reset drawing state"""
        return jsonify({'status': 'Drawing state reset'})

    @app.route('/get_commands', methods=['POST'])
    def get_commands():
        """Get drawing commands from Gemini with spatial awareness"""
        data = request.get_json()
        prompt = data.get('prompt')
        current_phase = data.get('phase', 'sketch')  # Default to sketch phase
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
            if current_phase == 'sketch' and current_part == 0:
                # Initial sketch, first part
                prompt_text = get_initial_sketch_prompt(prompt, history_text)
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
                    history_text,
                    command_history
                )

            # Generate content from AI
            print(f"Sending prompt to AI (Phase: {current_phase}, Part: {current_part})")
            response = model.generate_content(prompt_text, generation_config=GENERATION_CONFIG)
            print(f"Raw Gemini Response (Phase: {current_phase}, Part: {current_part}):")
            print(response.text[:200] + "...") # Only print beginning to avoid console clutter
            
            # Extract thinking for UI display
            thinking = extract_thinking(response.text)
            if thinking:
                print(f"Extracted thinking from AI response")
            
            # Clean the JSON string
            cleaned_json = clean_json_string(response.text)
            
            # Try to parse commands
            try:
                commands = json.loads(cleaned_json)
                if not isinstance(commands, list):
                    commands = [commands] if commands else []
            except json.JSONDecodeError:
                print("Failed to parse JSON response, returning empty command list")
                commands = []
                
            print(f"Returning {len(commands)} drawing commands for phase {current_phase}, part {current_part}")
                
            return jsonify({
                'commands': commands, 
                'current_phase': current_phase,
                'current_part': current_part,
                'next_phase': next_phase,
                'next_part': next_part,
                'has_more': has_more,
                'thinking': thinking  # Include the thinking for UI display
            })

        except Exception as e:
            import traceback
            print(f"Error: {e}")
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500