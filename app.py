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

# Configure Gemini
GENERATION_CONFIG = {
    "temperature": 0.4,  # Lower temperature for more deterministic output
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
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
    """Clean JSON string and remove thinking tags"""
    # First remove any <think></think> tags and their content
    if '<think>' in json_str and '</think>' in json_str:
        pattern = r"<think>[\s\S]*?</think>"
        json_str = re.sub(pattern, "", json_str, flags=re.DOTALL)
    
    # Clean code blocks
    if '```' in json_str:
        pattern = r"```(?:json)?([\s\S]*?)```"
        matches = re.findall(pattern, json_str, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
           json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    # Replace single quotes with double quotes if needed
    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    json_str = json_str.strip()
    print(f"Cleaned JSON string: {json_str[:100]}...")
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse: {e}")
        print(f"Full cleaned JSON: {json_str}")
    return json_str

def process_drawing_command(image_data, command):
    """Process drawing command"""
    action = command.get('action', '')
    img = data_uri_to_image(image_data)
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)

    try:
        if action == 'draw_polyline':
            points_data = command.get('points', [])
            if isinstance(points_data, str):
                try:
                    pairs = points_data.strip().replace(',', ' ').split()
                    points = []
                    for i in range(0, len(pairs), 2):
                        if i+1 < len(pairs):
                            points.append((float(pairs[i]), float(pairs[i+1])))
                except:
                    print(f"Error parsing points: {points_data}")
                    points = []
            else:
                points = [(p[0], p[1]) for p in points_data if len(p) >= 2]
            
            color = command.get('color', (0, 0, 0, 255))
            if isinstance(color, str):
                # Handle color in hex format or named colors
                if color.startswith('#'):
                    # Convert hex to RGBA
                    color = color.lstrip('#')
                    if len(color) == 6:
                        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                        color = (r, g, b, 255)
                    elif len(color) == 8:
                        r, g, b, a = tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
                        color = (r, g, b, a)
                elif color in {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white'}:
                    # Handle common color names
                    color_map = {
                        'red': (255, 0, 0, 255),
                        'blue': (0, 0, 255, 255),
                        'green': (0, 128, 0, 255),
                        'yellow': (255, 255, 0, 255),
                        'purple': (128, 0, 128, 255),
                        'orange': (255, 165, 0, 255),
                        'black': (0, 0, 0, 255),
                        'white': (255, 255, 255, 255),
                    }
                    color = color_map.get(color.lower(), (0, 0, 0, 255))
                    
            width = command.get('width', 2)
            
            if len(points) > 1:
                d.line(points, fill=color, width=width)
                
        elif action == 'erase':
            points_data = command.get('points', [])
            if isinstance(points_data, str):
                try:
                    pairs = points_data.strip().replace(',', ' ').split()
                    points = []
                    for i in range(0, len(pairs), 2):
                        if i+1 < len(pairs):
                            points.append((float(pairs[i]), float(pairs[i+1])))
                except:
                    print(f"Error parsing points: {points_data}")
                    points = []
            else:
                points = [(p[0], p[1]) for p in points_data if len(p) >= 2]
            
            width = command.get('width', 10)  # Eraser usually a bit larger
            
            if len(points) > 1:
                d.line(points, fill=(255, 255, 255, 255), width=width)
                
        elif action == 'fill_area':
            x = int(command.get('x', 0))
            y = int(command.get('y', 0))
            color = command.get('color', (0, 0, 0, 255))
            
            if isinstance(color, str):
                # Same color handling as above
                if color.startswith('#'):
                    color = color.lstrip('#')
                    if len(color) == 6:
                        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                        color = (r, g, b, 255)
                    elif len(color) == 8:
                        r, g, b, a = tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
                        color = (r, g, b, a)
                elif color in {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white'}:
                    color_map = {
                        'red': (255, 0, 0, 255),
                        'blue': (0, 0, 255, 255),
                        'green': (0, 128, 0, 255),
                        'yellow': (255, 255, 0, 255),
                        'purple': (128, 0, 128, 255),
                        'orange': (255, 165, 0, 255),
                        'black': (0, 0, 0, 255),
                        'white': (255, 255, 255, 255),
                    }
                    color = color_map.get(color.lower(), (0, 0, 0, 255))
            
            # Simple fill algorithm - get the target color and flood fill
            try:
                ImageDraw.floodfill(img, (x, y), color)
            except AttributeError:
                # If floodfill is not available in this version of PIL
                print("Floodfill not available in this PIL version")
                pass
                
        elif action == 'draw_rect':
            x0 = command.get('x0', 0)
            y0 = command.get('y0', 0)
            x1 = command.get('x1', 100)
            y1 = command.get('y1', 100)
            color = command.get('color', (0, 0, 0, 255))
            
            if isinstance(color, str):
                # Same color handling as above
                if color.startswith('#'):
                    color = color.lstrip('#')
                    if len(color) == 6:
                        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                        color = (r, g, b, 255)
                    elif len(color) == 8:
                        r, g, b, a = tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
                        color = (r, g, b, a)
                elif color in {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white'}:
                    color_map = {
                        'red': (255, 0, 0, 255),
                        'blue': (0, 0, 255, 255),
                        'green': (0, 128, 0, 255),
                        'yellow': (255, 255, 0, 255),
                        'purple': (128, 0, 128, 255),
                        'orange': (255, 165, 0, 255),
                        'black': (0, 0, 0, 255),
                        'white': (255, 255, 255, 255),
                    }
                    color = color_map.get(color.lower(), (0, 0, 0, 255))
                    
            width = command.get('width', 2)
            fill = command.get('fill', False)
            
            if fill:
                d.rectangle([(x0, y0), (x1, y1)], fill=color)
            else:
                d.rectangle([(x0, y0), (x1, y1)], outline=color, width=width)
                
        elif action == 'draw_circle':
            x = command.get('x', 100)
            y = command.get('y', 100)
            radius = command.get('radius', 50)
            color = command.get('color', (0, 0, 0, 255))
            
            if isinstance(color, str):
                # Same color handling as above
                if color.startswith('#'):
                    color = color.lstrip('#')
                    if len(color) == 6:
                        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                        color = (r, g, b, 255)
                    elif len(color) == 8:
                        r, g, b, a = tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
                        color = (r, g, b, a)
                elif color in {'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white'}:
                    color_map = {
                        'red': (255, 0, 0, 255),
                        'blue': (0, 0, 255, 255),
                        'green': (0, 128, 0, 255),
                        'yellow': (255, 255, 0, 255),
                        'purple': (128, 0, 128, 255),
                        'orange': (255, 165, 0, 255),
                        'black': (0, 0, 0, 255),
                        'white': (255, 255, 255, 255),
                    }
                    color = color_map.get(color.lower(), (0, 0, 0, 255))
                    
            width = command.get('width', 2)
            fill = command.get('fill', False)
            
            x0, y0 = x - radius, y - radius
            x1, y1 = x + radius, y + radius
            
            if fill:
                d.ellipse([(x0, y0), (x1, y1)], fill=color)
            else:
                d.ellipse([(x0, y0), (x1, y1)], outline=color, width=width)

    except Exception as e:
        print(f"Drawing error: {e} for command {action}")
        pass  # Don't crash on drawing errors

    return image_to_data_uri(img)

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
    iteration = data.get('iteration', 0)
    current_image = data.get('current_image')
    command_history = data.get('command_history', [])

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        if iteration == 0:
            # Format the command history for readability
            history_text = ""
            if command_history and len(command_history) > 0:
                history_text = "Previous drawing commands:\n"
                for i, cmd in enumerate(command_history):
                    history_text += f"{i+1}. {json.dumps(cmd)}\n"
                    
            # Initial prompt with expanded command set and reasoning in thinking tags
            prompt_text = [
                "You are a drawing assistant. I will give you a prompt, and you will respond with a JSON array of drawing commands after carefully reasoning about what to draw.",
                # Include command history if available
                history_text if history_text else "No previous commands recorded.",
                "First, use <think></think> tags to reason about the drawing. Consider:",
                " - What are the main elements needed for this drawing?",
                " - How would you position these elements on a 500x400 canvas?",
                " - What colors would work best for this drawing?",
                " - What drawing order makes sense (background first, then main elements, then details)?",
                "After your reasoning, provide a JSON array of drawing commands. The valid commands are:",
                " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2}  // Create lines with specified color and width",
                " - {'action': 'erase', 'points': [[x1, y1], [x2, y2], ...], 'width': 10}  // Erase along the specified line path",
                " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue'}  // Fill area at (x,y) with specified color",
                " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false}  // Draw rectangle",
                " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false}  // Draw circle",
                "Available colors: 'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white', or hex values like '#FF0000'",
                "Limit yourself to 10 points per polyline. Canvas size is 500x400.",
                "Here is the prompt:",
                prompt,
                "Remember to use <think>your reasoning here</think> before your JSON response. Your final output should include both your thinking and the JSON array, but I will strip out the thinking part before processing.",
            ]
        else:
            # Iteration prompt (refined instructions)
            if not current_image:
                return jsonify({'error': 'No current image provided'}), 400
            img = data_uri_to_image(current_image)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            image_part = {"mime_type": "image/png", "data": buffered.getvalue()}

            # Format the command history for readability
            history_text = ""
            if command_history and len(command_history) > 0:
                history_text = "Previous drawing commands:\n"
                for i, cmd in enumerate(command_history):
                    history_text += f"{i+1}. {json.dumps(cmd)}\n"
            
            # Create a description of the current state
            if iteration == 1:
                description = "The drawing currently contains basic shapes."
            elif iteration == 2:
                description = "The drawing has several shapes and lines that are starting to resemble the desired image, but it needs refinement."
            elif iteration == 3:
                description = "The drawing is closer, but still needs improvement in shape and color."
            else:
                description = "The drawing is an attempt, but needs further adjustments."

            prompt_text = [
                "Here is the original prompt:",
                prompt,
                "Here is the current drawing:",
                image_part,
                f"The current state of the drawing is: {description}", # Add the description
                # Include command history if available
                history_text if history_text else "No previous commands recorded.",
                "First, use <think></think> tags to analyze the current drawing and reason about what to add or improve. Consider:",
                " - What elements from the prompt are missing or need enhancement?",
                " - How can you build upon what's already drawn?",
                " - What colors or details would improve the current state?",
                f" - For this iteration ({iteration}), focus on: " + 
                ("Adding colors and details to the shapes." if iteration < 3 else "Refining the details and adding final touches."),
                "After your analysis, provide the NEXT set of drawing commands as a JSON array. The valid commands are:",
                " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2}",
                " - {'action': 'erase', 'points': [[x1, y1], [x2, y2], ...], 'width': 10}",
                " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue'}",
                " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false}",
                " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false}",
                "Remember to use <think>your analysis here</think> before your JSON response. Your final output should include both your thinking and the JSON array, but I will strip out the thinking part before processing.",
            ]

        response = model.generate_content(prompt_text, generation_config=GENERATION_CONFIG)
        print(f"Raw Gemini Response (Iteration {iteration}):")
        print(response.text)
        
        # Extract and print thinking if present
        thinking = ""
        if '<think>' in response.text and '</think>' in response.text:
            think_pattern = r"<think>([\s\S]*?)</think>"
            think_matches = re.findall(think_pattern, response.text, re.DOTALL)
            if think_matches:
                thinking = think_matches[0].strip()
                print(f"\nGemini's Reasoning:\n{'-'*50}\n{thinking}\n{'-'*50}")
        
        commands_str = clean_json_string(response.text)

        try:
            commands = json.loads(commands_str)
            if not isinstance(commands, list):
                raise ValueError("Response is not a JSON array")
            return jsonify({'commands': commands, 'iteration': iteration + 1, 'has_more': iteration < 5})  # Limit iterations
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Attempt aggressive cleaning
            clean_attempt = re.sub(r'[^{}[\],:"0-9a-zA-Z_\-\.\s]', '', commands_str)
            print(f"Aggressive clean: {clean_attempt[:100]}...")
            try:
                commands = json.loads(clean_attempt)
                return jsonify({'commands': commands, 'iteration': iteration + 1, 'has_more': iteration < 5})
            except:
                raise ValueError(f"Could not parse JSON: {e}")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)