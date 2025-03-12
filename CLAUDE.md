# AI Painter Build Commands and Guidelines

## Building and Running
- Install dependencies: `pip install -r requirements.txt`
- Set environment variables: `export GOOGLE_API_KEY=your_key_here` (or use .env file)
- Run the app: `python app.py`
- Production deployment: `gunicorn app:app`

## Code Style Guidelines

### Python
- Object-oriented approach with clear function separation
- Clean error handling with try/except blocks
- JSON validation and cleaning for AI responses
- Descriptive variable names (snake_case)
- Docstrings for functions and modules

### JavaScript
- Event-driven programming for UI interactions
- Clear state management
- Async/await for API calls with proper error handling
- camelCase variable names

### HTML/CSS
- Semantic HTML5 elements
- CSS classes with descriptive names
- Mobile-responsive design

### Additional Notes
- Use Pillow for image manipulation
- Handle errors and edge cases gracefully
- Display loading states for long-running operations
- Maintain separation between UI and application logic