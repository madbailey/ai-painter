from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw
from io import BytesIO
import base64
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

app = Flask(__name__)
CORS(app)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-002')

# Configure Gemini with a timeout
GENERATION_CONFIG = {
    "temperature": 0.4,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048
}

def data_uri_to_image(uri):
    _, encoded = uri.split(",", 1)
    data = base64.b64decode(encoded)
    return Image.open(BytesIO(data))

def image_to_data_uri(image, format="PNG"):
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/{format.lower()};base64,{img_str}"

def clean_json_string(json_str):
    """Clean up JSON string that might use single quotes instead of double quotes or contain markdown formatting"""
    # Remove markdown code blocks if present
    if '```' in json_str:
        # First try extracting the content between ```json and ```
        pattern = r"```(?:json)?([\s\S]*?)```"
        matches = re.findall(pattern, json_str, re.DOTALL)
        if matches:
            # Take the content of the first code block
            json_str = matches[0].strip()
        else:
            # Fallback: just remove the ```json and ``` markers
            json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    # Check if the JSON uses single quotes instead of double quotes
    if "'" in json_str and '"' not in json_str:
        # Replace single quotes with double quotes for JSON compliance
        json_str = json_str.replace("'", '"')
    
    # Additional cleanup: remove any leading/trailing whitespace or newlines
    json_str = json_str.strip()
    
    # Debug print to see what we're trying to parse
    print(f"Cleaned JSON string: {json_str[:100]}...")
    
    return json_str

def process_drawing_command(image_data, command):
    """Process a single drawing command and return the updated image data"""
    action = command.get('action', '')
    start_x = int(command.get('start_x', 0))
    start_y = int(command.get('start_y', 0))
    end_x = int(command.get('end_x', 0))
    end_y = int(command.get('end_y', 0))
    
    # Ensure coordinates are in the correct order (start < end)
    if start_x > end_x:
        start_x, end_x = end_x, start_x
    if start_y > end_y:
        start_y, end_y = end_y, start_y
        
    img = data_uri_to_image(image_data)
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)

    try:
        if action == 'draw_line':
            d.line([(start_x, start_y), (end_x, end_y)], fill=(0, 0, 0, 255), width=2)
        elif action == 'draw_rect':
            d.rectangle([(start_x, start_y), (end_x, end_y)], outline=(0, 0, 0, 255), width=2)
        elif action == 'draw_circle':
            d.ellipse([(start_x, start_y), (end_x, end_y)], outline=(0, 0, 0, 255), width=2)
        elif action == 'draw_triangle':
            # Draw a triangle using three lines
            # Calculate the third point (assuming an isosceles triangle)
            third_x = end_x - (end_x - start_x)  # Reflect end_x around start_x
            third_y = end_y
            
            # Draw the three sides of the triangle
            d.line([(start_x, start_y), (end_x, end_y)], fill=(0, 0, 0, 255), width=2)
            d.line([(end_x, end_y), (third_x, third_y)], fill=(0, 0, 0, 255), width=2)
            d.line([(third_x, third_y), (start_x, start_y)], fill=(0, 0, 0, 255), width=2)
        elif action == 'erase':
            d.rectangle([(start_x, start_y), (end_x, end_y)], fill=(255, 255, 255, 255))
        elif action == 'draw_arc':
            # Treat arc as a partial circle/ellipse
            d.arc([(start_x, start_y), (end_x, end_y)], 0, 180, fill=(0, 0, 0, 255), width=2)
    except Exception as e:
        print(f"Drawing error: {e} for command {action} with coords ({start_x}, {start_y}, {end_x}, {end_y})")
        # Continue without crashing
        pass

    return image_to_data_uri(img)

@app.route('/draw', methods=['POST'])
def draw():
    """Draw a single command on an image"""
    data = request.get_json()
    image_data = data['image_data']
    command = {
        'action': data['action'],
        'start_x': data.get('start_x', 0),
        'start_y': data.get('start_y', 0),
        'end_x': data.get('end_x', 0),
        'end_y': data.get('end_y', 0)
    }
    
    updated_image_data = process_drawing_command(image_data, command)
    return jsonify({'image_data': updated_image_data})

@app.route('/draw_command', methods=['POST'])
def draw_command():
    """Process a drawing command and return the updated image"""
    data = request.get_json()
    command = data.get('command', {})
    image_data = data.get('image_data')
    
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400
    
    if not command or 'action' not in command:
        return jsonify({'error': 'Invalid command'}), 400
        
    updated_image_data = process_drawing_command(image_data, command)
    return jsonify({'image_data': updated_image_data})

@app.route('/get_commands', methods=['POST'])
def get_commands():
    """Get drawing commands from Gemini"""
    data = request.get_json()
    prompt = data.get('prompt')
    iteration = data.get('iteration', 0)
    current_image = data.get('current_image')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        if iteration == 0:
            # First iteration - just use the prompt
            response = model.generate_content(
                [
                    "You are a drawing assistant. I will give you a prompt, and you will respond with a JSON array of drawing commands. Each command is a dictionary. Valid commands are:",
                    " - {'action': 'draw_line', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                    " - {'action': 'draw_rect', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                    " - {'action': 'draw_circle', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                    " - {'action': 'draw_triangle', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                    " - {'action': 'draw_arc', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                    "Here is the prompt:",
                    prompt,
                    "Respond with a JSON array and *nothing* else. Use double quotes for property names and string values, not single quotes. The response must be pure JSON. DO NOT include ```json or any markdown formatting.",
                ],
                generation_config=GENERATION_CONFIG
            )
        else:
            # Subsequent iterations - use the image and prompt
            if not current_image:
                return jsonify({'error': 'No current image provided for iteration'}), 400
                
            img = data_uri_to_image(current_image)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            image_part = {
                "mime_type": "image/png",
                "data": buffered.getvalue()
            }
            
            response = model.generate_content(
                [
                    "Here is the original prompt:",
                    prompt,
                    "Here is the current state of the drawing:",
                    image_part,
                    "Provide the *next* set of drawing commands as a JSON array. Use ONLY these exact formats with DOUBLE QUOTES, not single quotes:",
                    " - {\"action\": \"draw_line\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_rect\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_circle\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_triangle\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_arc\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    "Respond ONLY with the JSON array. DO NOT include any markdown formatting like ```json. Return JUST the array.",
                ],
                generation_config=GENERATION_CONFIG
            )
        
        print(f"Raw Gemini Response (Iteration {iteration}):")
        print(response.text)
        
        # Clean and parse the JSON
        commands_str = clean_json_string(response.text)
        commands = json.loads(commands_str)
        
        if not isinstance(commands, list):
            raise ValueError("Response is not a JSON array")
            
        # Return the parsed commands
        return jsonify({
            'commands': commands,
            'iteration': iteration + 1,
            'has_more': iteration < 1  # Limit to 2 iterations
        })
        
    except Exception as e:
        print(f"Error getting commands: {e}")
        
        # Return a fallback set of commands
        fallback_commands = []
        if iteration == 0:
            fallback_commands = [
                {"action": "draw_circle", "start_x": 150, "start_y": 100, "end_x": 250, "end_y": 200},
                {"action": "draw_circle", "start_x": 180, "start_y": 130, "end_x": 190, "end_y": 140},
                {"action": "draw_circle", "start_x": 210, "start_y": 130, "end_x": 220, "end_y": 140},
                {"action": "draw_arc", "start_x": 180, "start_y": 150, "end_x": 220, "end_y": 170}
            ]
        else:
            fallback_commands = [
                {"action": "draw_line", "start_x": 150, "start_y": 150, "end_x": 250, "end_y": 150},
                {"action": "draw_rect", "start_x": 140, "start_y": 90, "end_x": 260, "end_y": 210}
            ]
            
        return jsonify({
            'commands': fallback_commands,
            'iteration': iteration + 1,
            'has_more': iteration < 1,
            'fallback': True
        })

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a complete drawing directly"""
    data = request.get_json()
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    # Start with a blank canvas
    canvas_width = 500
    canvas_height = 400
    img = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
    image_data = image_to_data_uri(img)
    
    # Store the drawing sequence for animation
    drawing_sequence = [image_data]
    all_commands = []
    
    try:
        # Get initial commands
        response = model.generate_content(
            [
                "You are a drawing assistant. I will give you a prompt, and you will respond with a JSON array of drawing commands. Each command is a dictionary. Valid commands are:",
                " - {'action': 'draw_line', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                " - {'action': 'draw_rect', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                " - {'action': 'draw_circle', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                " - {'action': 'draw_triangle', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                " - {'action': 'draw_arc', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
                "Here is the prompt:",
                prompt,
                "Respond with a JSON array and *nothing* else. Use double quotes for property names and string values, not single quotes. The response must be pure JSON. DO NOT include ```json or any markdown formatting.",
            ],
            generation_config=GENERATION_CONFIG
        )
        
        print("Raw Gemini Response (First Iteration):")
        print(response.text)
        
        # Process the first set of commands
        try:
            # Parse the commands
            commands_str = clean_json_string(response.text)
            commands = json.loads(commands_str)
            
            if not isinstance(commands, list):
                raise ValueError("Gemini did not return a JSON array.")
            
            # Process each command in sequence
            for command in commands:
                # Update the image data with this command
                image_data = process_drawing_command(image_data, command)
                # Add to the sequence for animation
                drawing_sequence.append(image_data)
            
            all_commands.extend(commands)
            
            # Get a second iteration of commands
            img_for_gemini = data_uri_to_image(image_data)
            buffered = BytesIO()
            img_for_gemini.save(buffered, format="PNG")
            image_part = {
                "mime_type": "image/png",
                "data": buffered.getvalue()
            }
            
            response2 = model.generate_content(
                [
                    "Here is the original prompt:",
                    prompt,
                    "Here is the current state of the drawing:",
                    image_part,
                    "Provide the *next* set of drawing commands as a JSON array. Use ONLY these exact formats with DOUBLE QUOTES, not single quotes:",
                    " - {\"action\": \"draw_line\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_rect\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_circle\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_triangle\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    " - {\"action\": \"draw_arc\", \"start_x\": int, \"start_y\": int, \"end_x\": int, \"end_y\": int}",
                    "Respond ONLY with the JSON array. DO NOT include any markdown formatting like ```json. Return JUST the array.",
                ],
                generation_config=GENERATION_CONFIG
            )
            
            print("Raw Gemini Response (Second Iteration):")
            print(response2.text)
            
            # Process the second set of commands
            try:
                # Parse the commands
                commands_str2 = clean_json_string(response2.text)
                commands2 = json.loads(commands_str2)
                
                if not isinstance(commands2, list):
                    raise ValueError("Gemini did not return a JSON array in second iteration.")
                
                # Process each command in sequence
                for command in commands2:
                    # Update the image data with this command
                    image_data = process_drawing_command(image_data, command)
                    # Add to the sequence for animation
                    drawing_sequence.append(image_data)
                
                all_commands.extend(commands2)
                
            except Exception as e:
                print(f"Error processing second iteration: {e}")
                # Continue with just the first iteration results
        
        except Exception as e:
            print(f"Error processing first iteration: {e}")
            return jsonify({'error': f"Error processing drawing commands: {str(e)}"}), 500
        
        # Return the final image and the sequence for animation
        return jsonify({
            'image_data': image_data,
            'drawing_sequence': drawing_sequence,
            'commands': all_commands
        })
        
    except Exception as e:
        print(f"Error generating drawing: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)