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
import random
import math

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
            brush_type = command.get('brush_type', 'round')
            texture = command.get('texture', 'smooth')
            pressure = command.get('pressure', 1.0)  # Pressure affects opacity
            
            if len(points) > 1:
                # Apply painterly effect based on brush type
                if brush_type == 'round':
                    # Create tapered stroke with varying width
                    for i in range(len(points) - 1):
                        # Calculate direction vector
                        x1, y1 = points[i]
                        x2, y2 = points[i+1]
                        
                        # Calculate distance between points
                        dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                        
                        # Draw multiple circles along the path for organic feel
                        steps = max(3, int(dist / 2))
                        for j in range(steps + 1):
                            # Interpolate position
                            t = j / steps
                            x = x1 + (x2 - x1) * t
                            y = y1 + (y2 - y1) * t
                            
                            # Vary width slightly for organic feel
                            point_width = width * (0.8 + 0.4 * (1 - abs(t - 0.5) * 2))
                            
                            # Add slight randomness for texture
                            if texture == 'rough':
                                x += random.uniform(-1, 1)
                                y += random.uniform(-1, 1)
                                point_width *= random.uniform(0.85, 1.15)
                            
                            # Adjust opacity based on pressure
                            point_color = list(color)
                            if len(point_color) == 4:  # RGBA
                                point_color[3] = int(point_color[3] * pressure)
                            
                            # Draw the point as a circle
                            d.ellipse((x - point_width/2, y - point_width/2, 
                                      x + point_width/2, y + point_width/2), 
                                      fill=tuple(point_color))
                
                elif brush_type == 'flat':
                    # Simulate flat brush with more angular strokes
                    for i in range(len(points) - 1):
                        x1, y1 = points[i]
                        x2, y2 = points[i+1]
                        
                        # Calculate angle of line
                        angle = math.atan2(y2 - y1, x2 - x1)
                        
                        # Calculate perpendicular angle for brush width
                        perp_angle = angle + math.pi/2
                        
                        # Draw multiple overlapping rectangles
                        steps = max(3, int(((x2 - x1)**2 + (y2 - y1)**2)**0.5 / 2))
                        for j in range(steps):
                            # Interpolate position
                            t = j / steps
                            x = x1 + (x2 - x1) * t
                            y = y1 + (y2 - y1) * t
                            
                            # Create brush width with perpendicular offset
                            half_width = width / 2
                            if texture == 'rough':
                                half_width *= random.uniform(0.8, 1.2)
                            
                            # Define the rectangle for the brush stamp
                            rect_width = half_width * 2 * 1.5  # Slightly elongated
                            rect_height = half_width * 2
                            
                            # Apply rotation to the rectangle
                            points_rect = [(x - rect_width/2, y - rect_height/2),
                                         (x + rect_width/2, y - rect_height/2),
                                         (x + rect_width/2, y + rect_height/2),
                                         (x - rect_width/2, y + rect_height/2)]
                            
                            # Rotate points
                            rotated_points = []
                            for px, py in points_rect:
                                px_rel, py_rel = px - x, py - y
                                px_rot = px_rel * math.cos(angle) - py_rel * math.sin(angle)
                                py_rot = px_rel * math.sin(angle) + py_rel * math.cos(angle)
                                rotated_points.append((px_rot + x, py_rot + y))
                            
                            # Adjust opacity based on pressure
                            point_color = list(color)
                            if len(point_color) == 4:  # RGBA
                                point_color[3] = int(point_color[3] * pressure)
                            
                            # Draw the polygon
                            d.polygon(rotated_points, fill=tuple(point_color))
                
                elif brush_type == 'splatter':
                    # Create a splatter effect with random dots
                    for i in range(len(points) - 1):
                        x1, y1 = points[i]
                        x2, y2 = points[i+1]
                        distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                        dots = int(distance * width / 10)  # Number of splatter dots
                        
                        for _ in range(dots):
                            # Random position along the line with some deviation
                            t = random.random()
                            x = x1 + (x2 - x1) * t + random.uniform(-width/2, width/2)
                            y = y1 + (y2 - y1) * t + random.uniform(-width/2, width/2)
                            
                            # Random dot size
                            dot_size = random.uniform(1, width/2)
                            
                            # Adjust opacity based on pressure and random factor
                            point_color = list(color)
                            if len(point_color) == 4:  # RGBA
                                point_color[3] = int(point_color[3] * pressure * random.uniform(0.5, 1))
                            
                            # Draw the dot
                            d.ellipse((x - dot_size, y - dot_size, 
                                      x + dot_size, y + dot_size), 
                                      fill=tuple(point_color))
                else:
                    # Default to standard line if brush type not recognized
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
                
        elif action == 'draw_rect' or action == 'draw_circle':
            # Add texture to shapes
            texture = command.get('texture', 'smooth')
            
            if action == 'draw_rect':
                x0 = command.get('x0', 0)
                y0 = command.get('y0', 0)
                x1 = command.get('x1', 100)
                y1 = command.get('y1', 100)
                color = command.get('color', (0, 0, 0, 255))
                
                # Process color as before
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
                
                if texture == 'rough' and fill:
                    # Create textured fill with slightly varied colors
                    for y in range(int(y0), int(y1), 2):
                        for x in range(int(x0), int(x1), 2):
                            # Vary the color slightly for texture
                            r, g, b, a = color if len(color) == 4 else (*color, 255)
                            variation = random.uniform(0.9, 1.1)
                            r = min(255, max(0, int(r * variation)))
                            g = min(255, max(0, int(g * variation)))
                            b = min(255, max(0, int(b * variation)))
                            d.point((x, y), fill=(r, g, b, a))
                else:
                    # Use standard rectangle
                    if fill:
                        d.rectangle([(x0, y0), (x1, y1)], fill=color)
                    else:
                        d.rectangle([(x0, y0), (x1, y1)], outline=color, width=width)
                    
            elif action == 'draw_circle':
                x = command.get('x', 100)
                y = command.get('y', 100)
                radius = command.get('radius', 50)
                color = command.get('color', (0, 0, 0, 255))
                
                # Process color as before
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
                
                if texture == 'rough' and fill:
                    # Create a textured fill for circle
                    for y_pos in range(int(y0), int(y1), 2):
                        for x_pos in range(int(x0), int(x1), 2):
                            # Check if point is inside circle
                            if ((x_pos - x)**2 + (y_pos - y)**2) <= radius**2:
                                # Vary the color slightly for texture
                                r, g, b, a = color if len(color) == 4 else (*color, 255)
                                variation = random.uniform(0.9, 1.1)
                                r = min(255, max(0, int(r * variation)))
                                g = min(255, max(0, int(g * variation)))
                                b = min(255, max(0, int(b * variation)))
                                d.point((x_pos, y_pos), fill=(r, g, b, a))
                else:
                    # Use standard circle
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
                    
            # Initial prompt with expanded command set and painterly approach
            prompt_text = [
                "You are a digital painting assistant capable of creating expressive, painterly artwork. I will give you a prompt, and you will respond with a JSON array of drawing commands that creates organic, artistic strokes rather than rigid digital lines.",
                # Include command history if available
                history_text if history_text else "No previous commands recorded.",
                "First, use <think></think> tags to reason about the drawing as a painter would. Consider:",
                " - What are the main elements and how would a traditional artist approach them?",
                " - What brush types would best represent different elements (round brushes for organic forms, flat brushes for structures)?",
                " - How would brushstrokes be applied - direction, pressure, and texture?",
                " - What painting techniques would suit this subject (wet-on-wet, glazing, impasto, etc.)?",
                " - How would a traditional artist layer and build up the painting?",
                
                "After your reasoning, provide a JSON array of drawing commands. The valid commands are:",
                " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2, 'brush_type': 'round', 'texture': 'smooth', 'pressure': 1.0}",
                " - {'action': 'erase', 'points': [[x1, y1], [x2, y2], ...], 'width': 10}",
                " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue', 'texture': 'smooth'}",
                " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false, 'texture': 'smooth'}",
                " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false, 'texture': 'smooth'}",
                
                "Brush types:",
                " - 'round': Creates tapered, organic strokes with varying width",
                " - 'flat': Creates angular, directional strokes like a flat brush",
                " - 'splatter': Creates a scattered, spray-like effect",
                
                "Texture types:",
                " - 'smooth': Creates clean, even strokes",
                " - 'rough': Adds randomness and texture to strokes and fills",
                
                "Pressure (0.1-1.0):",
                " - Higher values create more opaque strokes",
                " - Lower values create more transparent strokes",
                
                "Available colors: 'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'black', 'white', or hex values like '#FF0000'",
                
                "IMPORTANT: Focus on creating painterly effects by:",
                " - Using shorter, overlapping brush strokes instead of long continuous lines",
                " - Varying brush types, widths, and pressures for different elements",
                " - Using rough textures for natural elements, smooth for manufactured ones",
                " - Building up layers from background to foreground",
                " - Using wider strokes for blocking in shapes, smaller for details",
                
                "Canvas size is 500x400.",
                
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
            
            # Define iteration focus based on stage
            if iteration == 1:
                focus = "Adding more organic brushstrokes and texture to define main forms."
            elif iteration == 2:
                focus = "Layering and building depth with varied brush strokes and colors."
            elif iteration == 3:
                focus = "Adding highlights, shadows, and texture with appropriate brush types."
            else:
                focus = "Refining details and adding final touches with small, precise strokes."

            prompt_text = [
                "Here is the original prompt:",
                prompt,
                "Here is the current drawing:",
                image_part,
                f"The current iteration stage is: {iteration}", 
                f"Focus: {focus}",
                # Include command history if available
                history_text if history_text else "No previous commands recorded.",
                
                "First, use <think></think> tags to analyze the current drawing as an artist would. Consider:",
                " - What painterly techniques would improve what's already there?",
                " - How would traditional painters approach the next layer?",
                " - Where could brush variation add interest and texture?",
                " - What elements need reinforcement or refinement?",
                
                "After your analysis, provide the NEXT set of drawing commands as a JSON array. The valid commands are:",
                " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2, 'brush_type': 'round', 'texture': 'smooth', 'pressure': 1.0}",
                " - {'action': 'erase', 'points': [[x1, y1], [x2, y2], ...], 'width': 10}",
                " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue', 'texture': 'smooth'}",
                " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false, 'texture': 'smooth'}",
                " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false, 'texture': 'smooth'}",
                
                "Brush types:",
                " - 'round': Creates tapered, organic strokes with varying width",
                " - 'flat': Creates angular, directional strokes like a flat brush",
                " - 'splatter': Creates a scattered, spray-like effect",
                
                "Texture types:",
                " - 'smooth': Creates clean, even strokes",
                " - 'rough': Adds randomness and texture to strokes and fills",
                
                "Pressure (0.1-1.0):",
                " - Higher values create more opaque strokes",
                " - Lower values create more transparent strokes",
                
                "IMPORTANT: For this iteration, focus on:",
                focus,
                
                "Remember to use <think>your analysis here</think> before your JSON response. Your final output should include both your thinking and the JSON array, but I will strip out the thinking part before processing.",
            ]

        response = model.generate_content(prompt_text, generation_config=GENERATION_CONFIG)
        # Rest of the function remains the same
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