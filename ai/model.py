"""
AI model configuration and initialization.
"""

import os
import google.generativeai as genai
from config.phases import GENERATION_CONFIG

model = None

def initialize_model():
    """
    Initialize the Gemini AI model with API key.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global model
    
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY not found in environment variables")
            return False
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("AI model initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing AI model: {e}")
        return False

def get_model():
    """
    Get the initialized AI model.
    
    Returns:
        GenerativeModel: The initialized model or None if not initialized
    """
    global model
    if not model:
        initialize_model()
    return model