# AI Painter Codebase Guidelines

## Setup and Running
- Install dependencies: `pip install -r requirements.txt`
- Set environment variable: `export GOOGLE_API_KEY=your_key_here` (or create .env file)
- Run development server: `python app.py`
- Production deployment: `gunicorn app:app`

## Project Structure
- `app.py`: Main entry point
- `ai/`: Model initialization and prompt generation
- `api/`: Flask routes and endpoints
- `drawing/`: Command processing and brush actions
- `utils/`: Image and text utilities
- `config/`: Application configuration
- Frontend: `index.html`, `script.js`, `drawing-worker.js`

## Style Guidelines

### Python
- Module-level docstrings explaining purpose
- Function docstrings with parameter descriptions
- snake_case for variables and functions
- Explicit error handling with try/except
- Import order: standard library → third-party → local modules

### JavaScript
- camelCase for variables and functions
- Async/await pattern for API calls
- Use Web Workers for performance-intensive operations
- Event-driven architecture with clear state management
- Consistent error handling with Promise.catch()

### General Principles
- Separation of concerns between modules
- Defensive programming with proper validation
- Clear logging for debugging purposes
- RESTful API design for backend communications
- Graceful error handling with user feedback