from flask import Flask, request, jsonify, render_template
from models import generate_paint_command, caption_image

app = Flask(__name__, static_folder='static', template_folder='static')


@app.route('/')
def index():
    # Serve index.html from /static
    return app.send_static_file('index.html')

@app.route('/api/paint', methods=['POST'])
def paint():
    # Example: get user prompt or partial image data
    prompt = request.json.get('prompt', '')
    # AI logic from models.py
    command = generate_paint_command(prompt)
    return jsonify({"command": command})

@app.route('/api/caption', methods=['POST'])
def caption():
    # Example: handle an uploaded image or base64 data
    image_data = request.json.get('image')
    # call caption_image(...) from models.py
    ...
    return jsonify({"caption": captioned_text})

if __name__ == "__main__":
    app.run(debug=True)