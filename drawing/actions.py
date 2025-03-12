"""
Implementation of different drawing actions.
"""

import random
from PIL import ImageDraw
from drawing.brushes import get_brush_by_type

# Color mapping for named colors
COLOR_MAP = {
    'red': (255, 0, 0, 255),
    'blue': (0, 0, 255, 255),
    'green': (0, 128, 0, 255),
    'yellow': (255, 255, 0, 255),
    'purple': (128, 0, 128, 255),
    'orange': (255, 165, 0, 255),
    'black': (0, 0, 0, 255),
    'white': (255, 255, 255, 255),
}

def parse_color(color):
    """
    Parse color from various formats into RGBA tuple.
    
    Args:
        color: Color in hex string, named color, or RGBA tuple
        
    Returns:
        tuple: RGBA color tuple
    """
    if isinstance(color, tuple):
        return color
        
    if isinstance(color, str):
        # Handle hex format
        if color.startswith('#'):
            color = color.lstrip('#')
            if len(color) == 6:
                r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                return (r, g, b, 255)
            elif len(color) == 8:
                r, g, b, a = tuple(int(color[i:i+2], 16) for i in (0, 2, 4, 6))
                return (r, g, b, a)
        # Handle named colors
        elif color.lower() in COLOR_MAP:
            return COLOR_MAP[color.lower()]
            
    # Default to black if invalid
    return (0, 0, 0, 255)

def parse_points(points_data):
    """
    Parse points data from various formats.
    
    Args:
        points_data: Points as list of coordinates or space-separated string
        
    Returns:
        list: List of (x, y) coordinate tuples
    """
    if isinstance(points_data, str):
        try:
            pairs = points_data.strip().replace(',', ' ').split()
            points = []
            for i in range(0, len(pairs), 2):
                if i+1 < len(pairs):
                    points.append((float(pairs[i]), float(pairs[i+1])))
            return points
        except Exception as e:
            print(f"Error parsing points: {points_data}")
            return []
    elif isinstance(points_data, list):
        return [(p[0], p[1]) for p in points_data if len(p) >= 2]
    return []

def draw_polyline(img, command):
    """
    Draw a polyline with the specified brush type.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Drawing command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    points = parse_points(command.get('points', []))
    if len(points) <= 1:
        return img
        
    color = parse_color(command.get('color', (0, 0, 0, 255)))
    width = command.get('width', 2)
    brush_type = command.get('brush_type', 'round')
    texture = command.get('texture', 'smooth')
    pressure = command.get('pressure', 1.0)
    
    # Get the appropriate brush function and use it
    brush_func = get_brush_by_type(brush_type)
    brush_func(d, points, color, width, texture, pressure)
    
    return img

def erase(img, command):
    """
    Erase along a polyline.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Erasing command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    points = parse_points(command.get('points', []))
    if len(points) <= 1:
        return img
        
    width = command.get('width', 10)  # Eraser usually a bit larger
    
    # Use a standard line for erasing
    d.line(points, fill=(255, 255, 255, 255), width=width)
    
    return img

def fill_area(img, command):
    """
    Fill an area with color.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Fill command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    x = int(command.get('x', 0))
    y = int(command.get('y', 0))
    color = parse_color(command.get('color', (0, 0, 0, 255)))
    
    # Simple fill algorithm - get the target color and flood fill
    try:
        ImageDraw.floodfill(img, (x, y), color)
    except AttributeError:
        # If floodfill is not available in this version of PIL
        print("Floodfill not available in this PIL version")
        pass
    
    return img

def draw_rect(img, command):
    """
    Draw a rectangle.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Rectangle command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    x0 = command.get('x0', 0)
    y0 = command.get('y0', 0)
    x1 = command.get('x1', 100)
    y1 = command.get('y1', 100)
    color = parse_color(command.get('color', (0, 0, 0, 255)))
    width = command.get('width', 2)
    fill = command.get('fill', False)
    texture = command.get('texture', 'smooth')
    
    if texture == 'rough' and fill:
        # Create textured fill with slightly varied colors
        for y in range(int(y0), int(y1), 2):
            for x in range(int(x0), int(x1), 2):
                # Vary the color slightly for texture
                r, g, b, a = color if len(color) == 4 else (*color, 255)
                variation = random.uniform(0.9, 1.1)
                r = min(255, max(0, int(r * variation)))
                g = min(255, max(0, int(g * variation)))
                b = min(255, max(0, int(b * variation)))
                d.point((x, y), fill=(r, g, b, a))
    else:
        # Use standard rectangle
        if fill:
            d.rectangle([(x0, y0), (x1, y1)], fill=color)
        else:
            d.rectangle([(x0, y0), (x1, y1)], outline=color, width=width)
    
    return img

def draw_circle(img, command):
    """
    Draw a circle.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Circle command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    x = command.get('x', 100)
    y = command.get('y', 100)
    radius = command.get('radius', 50)
    color = parse_color(command.get('color', (0, 0, 0, 255)))
    width = command.get('width', 2)
    fill = command.get('fill', False)
    texture = command.get('texture', 'smooth')
    
    x0, y0 = x - radius, y - radius
    x1, y1 = x + radius, y + radius
    
    if texture == 'rough' and fill:
        # Create a textured fill for circle
        for y_pos in range(int(y0), int(y1), 2):
            for x_pos in range(int(x0), int(x1), 2):
                # Check if point is inside circle
                if ((x_pos - x)**2 + (y_pos - y)**2) <= radius**2:
                    # Vary the color slightly for texture
                    r, g, b, a = color if len(color) == 4 else (*color, 255)
                    variation = random.uniform(0.9, 1.1)
                    r = min(255, max(0, int(r * variation)))
                    g = min(255, max(0, int(g * variation)))
                    b = min(255, max(0, int(b * variation)))
                    d.point((x_pos, y_pos), fill=(r, g, b, a))
    else:
        # Use standard circle
        if fill:
            d.ellipse([(x0, y0), (x1, y1)], fill=color)
        else:
            d.ellipse([(x0, y0), (x1, y1)], outline=color, width=width)
    
    return img

def erase_area(img, command):
    """
    Erase a rectangular area.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Erase area command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    x0 = command.get('x0', 0)
    y0 = command.get('y0', 0)
    x1 = command.get('x1', 100)
    y1 = command.get('y1', 100)
    
    # Create a white rectangle with transparency
    transparent_white = (255, 255, 255, 200)  # Semi-transparent white
    d.rectangle([(x0, y0), (x1, y1)], fill=transparent_white)
    
    return img

def modify_color(img, command):
    """
    Modify colors in a circular area.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Modify color command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    target_color = command.get('target_color', '')
    new_color = command.get('new_color', '')
    area_x = command.get('area_x', 0)
    area_y = command.get('area_y', 0)
    radius = command.get('radius', 50)
    
    if not target_color or not new_color:
        return img
        
    # Convert colors to RGB tuples
    target_color = parse_color(target_color)[:3]  # Only use RGB components
    new_color = parse_color(new_color)[:3]
    
    # Get pixel data
    pixel_data = img.load()
    width, height = img.size
    
    # Define the area to modify (circular)
    for x in range(max(0, area_x - radius), min(width, area_x + radius)):
        for y in range(max(0, area_y - radius), min(height, area_y + radius)):
            # Check if point is in the circle
            if ((x - area_x) ** 2 + (y - area_y) ** 2) <= radius ** 2:
                pixel = pixel_data[x, y]
                # Check if this pixel is close to the target color
                if (len(pixel) >= 3 and 
                    abs(pixel[0] - target_color[0]) < 30 and 
                    abs(pixel[1] - target_color[1]) < 30 and 
                    abs(pixel[2] - target_color[2]) < 30):
                    
                    # Preserve alpha if exists
                    alpha = pixel[3] if len(pixel) > 3 else 255
                    new_pixel = new_color + (alpha,)
                    pixel_data[x, y] = new_pixel
    
    return img

def enhance_detail(img, command):
    """
    Enhance detail in an area.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Enhance detail command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    x = command.get('x', 100)
    y = command.get('y', 100)
    radius = command.get('radius', 20)
    technique = command.get('technique', 'highlight')
    color = parse_color(command.get('color', '#FFFFFF'))
    
    if technique == 'highlight':
        # Add a semi-transparent highlight
        highlight_radius = radius / 2
        color = color[:3] + (100,)  # Semi-transparent
        d.ellipse((x - highlight_radius, y - highlight_radius, 
                  x + highlight_radius, y + highlight_radius), 
                  fill=color)
    
    elif technique == 'sharpen':
        # Simulate sharpening by adding small contrasting dots
        color = color[:3] + (100,)  # Semi-transparent
        for _ in range(int(radius * 0.8)):
            dot_x = x + random.uniform(-radius, radius)
            dot_y = y + random.uniform(-radius, radius)
            dot_size = random.uniform(1, 3)
            d.ellipse((dot_x - dot_size, dot_y - dot_size, 
                      dot_x + dot_size, dot_y + dot_size), 
                      fill=color)
    
    return img

def soften(img, command):
    """
    Soften an area.
    
    Args:
        img (PIL.Image): Image to draw on
        command (dict): Soften command parameters
        
    Returns:
        PIL.Image: The modified image
    """
    d = ImageDraw.Draw(img)
    
    x = command.get('x', 100)
    y = command.get('y', 100)
    radius = command.get('radius', 20)
    
    # Simulate softening by adding very transparent overlay
    soft_color = (255, 255, 255, 20)  # Very transparent white
    for i in range(10):
        blur_radius = random.uniform(radius * 0.5, radius * 1.2)
        d.ellipse((x - blur_radius, y - blur_radius, 
                  x + blur_radius, y + blur_radius), 
                  fill=soft_color)
    
    return img

# Action mapping for command processing
ACTION_MAP = {
    'draw_polyline': draw_polyline,
    'erase': erase,
    'fill_area': fill_area,
    'draw_rect': draw_rect,
    'draw_circle': draw_circle,
    'erase_area': erase_area,
    'modify_color': modify_color,
    'enhance_detail': enhance_detail,
    'soften': soften,
}