"""
Main application entry point for AI Painter.

This file initializes the Flask application, configures the AI model,
and sets up the routes for the API endpoints.
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

from api.routes import register_routes
from ai.model import initialize_model

# Load environment variables from .env file
load_dotenv()

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    CORS(app)
    
    # Initialize the AI model
    initialize_model()
    
    # Register API routes
    register_routes(app)
    
    # Serve static files
    @app.route('/')
    def index():
        return send_from_directory('.', 'index.html')
        
    @app.route('/<path:path>')
    def static_files(path):
        return send_from_directory('.', path)
    
    return app

if __name__ == '__main__':
    app = create_app()
    debug_mode = os.environ.get("DEBUG", "True").lower() in ("true", "1", "t")
    app.run(debug=debug_mode, port=5000)