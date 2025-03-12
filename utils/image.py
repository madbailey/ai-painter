"""
Image utility functions for converting between data URIs and PIL Images.
"""

import base64
from io import BytesIO
from PIL import Image

def data_uri_to_image(uri):
    """
    Convert a data URI to a PIL Image.
    
    Args:
        uri (str): Data URI string starting with 'data:image/'
        
    Returns:
        PIL.Image: The converted image
    """
    _, encoded = uri.split(",", 1)
    data = base64.b64decode(encoded)
    return Image.open(BytesIO(data))

def image_to_data_uri(image, format="PNG"):
    """
    Convert a PIL Image to a data URI.
    
    Args:
        image (PIL.Image): The image to convert
        format (str): The image format (default: PNG)
        
    Returns:
        str: Data URI representation of the image
    """
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/{format.lower()};base64,{img_str}"