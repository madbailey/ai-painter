# AI Painter

An AI-powered digital painting application that combines a web-based canvas for drawing with AI-generated artwork based on text prompts.

## Features

- AI-assisted drawing based on text prompts
- Manual drawing with various brush tools and effects
- Structured painting process (Composition � Color Blocking � Detailing � Final Touches)
- Multiple brush types: round, flat, splatter
- Texture options: smooth, rough
- Pressure sensitivity support
- Web worker support for improved performance

## Project Structure

```
/ai-painter/
   app.py                 # Main application entry point
   config/                # Configuration files
      phases.py          # Painting phases configuration
   utils/                 # Utility functions
      image.py           # Image processing utilities
      text.py            # Text processing utilities
   drawing/               # Drawing functionality
      processor.py       # Command processing logic
      brushes.py         # Brush implementations
      actions.py         # Drawing action implementations
   ai/                    # AI integration
      model.py           # AI model setup
      prompts.py         # Prompt generation for phases
   api/                   # API endpoints
      routes.py          # Flask routes
   drawing-worker.js      # Web worker for better performance
   index.html             # Web interface
   script.js              # Frontend JavaScript
   requirements.txt       # Python dependencies
```

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   export GOOGLE_API_KEY=your_api_key
   ```
   Or create a `.env` file with the API key.

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to `http://127.0.0.1:5000`

## Technologies Used

- Backend: Python, Flask
- Frontend: HTML, CSS, JavaScript
- AI: Google's Gemini API (Gemini-1.5-flash-002 model)
- Image Processing: Pillow (PIL Fork)
- Performance: Web Workers for parallel processing