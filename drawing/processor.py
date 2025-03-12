"""
Main drawing processor for handling drawing commands.
"""

from PIL import Image
from utils.image import data_uri_to_image, image_to_data_uri
from drawing.actions import ACTION_MAP

def process_drawing_command(image_data, command):
    """
    Process a drawing command and apply it to the image.
    
    Args:
        image_data (str): Data URI of the image
        command (dict): Drawing command with action and parameters
        
    Returns:
        str: Updated image as data URI
    """
    action = command.get('action', '')
    
    # Skip if no action or unknown action
    if not action or action not in ACTION_MAP:
        print(f"Unknown or missing action: {action}")
        return image_data
    
    try:
        # Convert data URI to image
        img = data_uri_to_image(image_data)
        img = img.convert("RGBA")
        
        # Process the drawing action
        action_func = ACTION_MAP[action]
        img = action_func(img, command)
        
        # Convert back to data URI
        updated_image_data = image_to_data_uri(img)
        return updated_image_data
        
    except Exception as e:
        print(f"Drawing error: {e} for command {action}")
        # Return original image data if there's an error
        return image_data