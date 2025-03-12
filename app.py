from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw
from io import BytesIO
import base64
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests  # Make sure requests is imported
import json  # Import json

load_dotenv()

app = Flask(__name__)
CORS(app)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-002')

def data_uri_to_image(uri):
    _, encoded = uri.split(",", 1)
    data = base64.b64decode(encoded)
    return Image.open(BytesIO(data))

def image_to_data_uri(image, format="PNG"):
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/{format.lower()};base64,{img_str}"

@app.route('/draw', methods=['POST'])
def draw():
    data = request.get_json()
    image_data = data['image_data']
    action = data['action']
    start_x = int(data.get('start_x', 0))
    start_y = int(data.get('start_y', 0))
    end_x = int(data.get('end_x', 0))
    end_y = int(data.get('end_y', 0))

    img = data_uri_to_image(image_data)
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img)

    if action == 'draw_line':
        d.line([(start_x, start_y), (end_x, end_y)], fill=(0, 0, 0, 255), width=2)
    elif action == 'draw_rect':
        d.rectangle([(start_x, start_y), (end_x, end_y)], outline=(0, 0, 0, 255), width=2)
    elif action == 'draw_circle':
        d.ellipse([(start_x, start_y), (end_x, end_y)], outline=(0, 0, 0, 255), width=2)
    elif action == 'erase':
        d.rectangle([(start_x, start_y), (end_x, end_y)], fill=(255, 255, 255, 255))

    updated_image_data = image_to_data_uri(img)
    return jsonify({'image_data': updated_image_data})

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.get_json().get('prompt')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    canvas_width = 500
    canvas_height = 400
    img = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
    image_data = image_to_data_uri(img)

    response = model.generate_content(
        [
            "You are a drawing assistant.  I will give you a prompt, and you will respond with a JSON array of drawing commands. Each command is a dictionary.  Valid commands are:",
            " - {'action': 'draw_line', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
            " - {'action': 'draw_rect', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
            " - {'action': 'draw_circle', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
            " - {'action': 'erase', 'start_x': int, 'start_y': int, 'end_x': int, 'end_y': int}",
            "Here is the prompt:",
            prompt,
            "Respond with a JSON array and *nothing* else.  Do *not* include any introductory text, explanations, or Markdown formatting (like ```json```).  The response *must* be *pure* JSON that can be directly parsed by Python's `json.loads()` function.", # More emphatic instruction
        ]
    )

    # --- PRINT THE RAW RESPONSE HERE ---
    print("Raw Gemini Response:")
    print(response.text)
    # -----------------------------------


    max_iterations = 5
    for iteration in range(max_iterations):
        try:
            commands_str = response.text
            if commands_str.startswith("```json"):
                commands_str = commands_str[7:]  # Remove "```json"
                if commands_str.endswith("```"):
                    commands_str = commands_str[:-3]  # Remove "```"
            commands_str = commands_str.strip() #Removes any whitespace
            commands = json.loads(commands_str)  # Now parse the cleaned string
            if not isinstance(commands, list):
                raise ValueError("Gemini did not return a JSON array.")

        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing Gemini response: {e}")
            # Print the problematic string for further analysis:
            print(f"Problematic string: {response.text}")
            return jsonify({'error': 'Invalid response from Gemini'}), 500

        for command in commands:
            command['image_data'] = image_data
            draw_response = requests.post(f'http://127.0.0.1:5000/draw', json=command)
            if draw_response.status_code != 200:
                return jsonify({'error': 'Error executing drawing command'}), 500
            image_data = draw_response.json()['image_data']

        if iteration < max_iterations - 1:
            img_for_gemini = data_uri_to_image(image_data)
            buffered = BytesIO()
            img_for_gemini.save(buffered, format="PNG")
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
                    "Provide the *next* set of drawing commands as a JSON array, as before.  Refine the drawing based on its current state. Do not repeat previous commands.",
                     "Respond ONLY with the JSON array. Do not include any other text.",
                ]
            )
            # --- PRINT THE RAW RESPONSE HERE (Inside Loop) ---
            print(f"Raw Gemini Response (Iteration {iteration + 1}):")
            print(response.text)
            # -----------------------------------

    return jsonify({'image_data': image_data})


if __name__ == '__main__':
    app.run(debug=True, port=5000)