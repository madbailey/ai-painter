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
    """Clean JSON string"""
    if '```' in json_str:
        pattern = r"```(?:json)?([\s\S]*?)```"
        matches = re.findall(pattern, json_str, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
           json_str = json_str.replace("```json", "").replace("```", "").strip()
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
            if len(points) > 1:
                d.line(points, fill=(0, 0, 0, 255), width=2)

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

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        if iteration == 0:
            # Initial prompt (only draw_polyline)
            prompt_text = [
                "You are a drawing assistant. I will give you a prompt, and you will respond with a JSON array of drawing commands. The ONLY valid command is:",
                " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...]}  // Use an ARRAY of [x, y] pairs. Limit yourself to 10 points per polyline.",
                "Here is the prompt:",
                prompt,
                "IMPORTANT: Return ONLY a JSON array and NOTHING else. No markdown.  Output ONLY the JSON.",
            ]
        else:
            # Iteration prompt (refined instructions)
            if not current_image:
                return jsonify({'error': 'No current image provided'}), 400
            img = data_uri_to_image(current_image)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            image_part = {"mime_type": "image/png", "data": buffered.getvalue()}

            # Create a description of the current state
            if iteration == 1:
                description = "The drawing currently contains a few disconnected lines."
            elif iteration == 2:
                description = "The drawing has some lines that are starting to resemble the desired shape, but it needs refinement."
            elif iteration == 3:
                description = "The drawing is closer, but still needs significant improvement in connecting and shaping the lines."
            else:
                description = "The drawing is an attempt, but needs further adjustments."

            prompt_text = [
                "Here is the original prompt:",
                prompt,
                "Here is the current drawing:",
                image_part,
                f"The current state of the drawing is: {description}", # Add the description
                "Provide the NEXT set of drawing commands as a JSON array. The ONLY valid command is:",
                " - {\"action\": \"draw_polyline\", \"points\": [[x1, y1], [x2, y2], ...]} // Limit to 10 points per polyline.",
                f"For this iteration ({iteration}), focus on: ",
                # Specific instructions based on iteration (examples)
                " - Connecting existing lines to form closed shapes." if iteration < 3 else  " - Refining the shape and adding details." ,
                "CRUCIAL: Return ONLY the JSON array. No markdown. JUST the JSON.",
            ]

        response = model.generate_content(prompt_text, generation_config=GENERATION_CONFIG)
        print(f"Raw Gemini Response (Iteration {iteration}):")
        print(response.text)
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