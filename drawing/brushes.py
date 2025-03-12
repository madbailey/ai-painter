"""
Brush implementations for different artistic styles and effects.
"""

import random
import math
from PIL import ImageDraw

def draw_round_brush(d, points, color, width, texture, pressure):
    """
    Draw with a round brush that creates tapered, organic strokes.
    
    Args:
        d (PIL.ImageDraw): The drawing context
        points (list): List of (x, y) coordinates
        color (tuple): RGBA color tuple
        width (int): Base width of the brush
        texture (str): 'smooth' or 'rough'
        pressure (float): Pressure value affecting opacity
    """
    for i in range(len(points) - 1):
        # Calculate direction vector
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        
        # Calculate distance between points
        dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        # Draw multiple circles along the path for organic feel
        steps = max(3, int(dist / 2))
        for j in range(steps + 1):
            # Interpolate position
            t = j / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            
            # Vary width slightly for organic feel
            point_width = width * (0.8 + 0.4 * (1 - abs(t - 0.5) * 2))
            
            # Add slight randomness for texture
            if texture == 'rough':
                x += random.uniform(-1, 1)
                y += random.uniform(-1, 1)
                point_width *= random.uniform(0.85, 1.15)
            
            # Adjust opacity based on pressure
            point_color = list(color)
            if len(point_color) == 4:  # RGBA
                point_color[3] = int(point_color[3] * pressure)
            
            # Draw the point as a circle
            d.ellipse((x - point_width/2, y - point_width/2, 
                      x + point_width/2, y + point_width/2), 
                      fill=tuple(point_color))

def draw_flat_brush(d, points, color, width, texture, pressure):
    """
    Draw with a flat brush that creates angular, directional strokes.
    
    Args:
        d (PIL.ImageDraw): The drawing context
        points (list): List of (x, y) coordinates
        color (tuple): RGBA color tuple
        width (int): Base width of the brush
        texture (str): 'smooth' or 'rough'
        pressure (float): Pressure value affecting opacity
    """
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        
        # Calculate angle of line
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Calculate perpendicular angle for brush width
        perp_angle = angle + math.pi/2
        
        # Draw multiple overlapping rectangles
        steps = max(3, int(((x2 - x1)**2 + (y2 - y1)**2)**0.5 / 2))
        for j in range(steps):
            # Interpolate position
            t = j / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            
            # Create brush width with perpendicular offset
            half_width = width / 2
            if texture == 'rough':
                half_width *= random.uniform(0.8, 1.2)
            
            # Define the rectangle for the brush stamp
            rect_width = half_width * 2 * 1.5  # Slightly elongated
            rect_height = half_width * 2
            
            # Apply rotation to the rectangle
            points_rect = [(x - rect_width/2, y - rect_height/2),
                         (x + rect_width/2, y - rect_height/2),
                         (x + rect_width/2, y + rect_height/2),
                         (x - rect_width/2, y + rect_height/2)]
            
            # Rotate points
            rotated_points = []
            for px, py in points_rect:
                px_rel, py_rel = px - x, py - y
                px_rot = px_rel * math.cos(angle) - py_rel * math.sin(angle)
                py_rot = px_rel * math.sin(angle) + py_rel * math.cos(angle)
                rotated_points.append((px_rot + x, py_rot + y))
            
            # Adjust opacity based on pressure
            point_color = list(color)
            if len(point_color) == 4:  # RGBA
                point_color[3] = int(point_color[3] * pressure)
            
            # Draw the polygon
            d.polygon(rotated_points, fill=tuple(point_color))

def draw_splatter_brush(d, points, color, width, texture, pressure):
    """
    Draw with a splatter brush that creates scattered, spray-like effects.
    
    Args:
        d (PIL.ImageDraw): The drawing context
        points (list): List of (x, y) coordinates
        color (tuple): RGBA color tuple
        width (int): Base width of the brush
        texture (str): Not used for splatter brush
        pressure (float): Pressure value affecting opacity
    """
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        dots = int(distance * width / 10)  # Number of splatter dots
        
        for _ in range(dots):
            # Random position along the line with some deviation
            t = random.random()
            x = x1 + (x2 - x1) * t + random.uniform(-width/2, width/2)
            y = y1 + (y2 - y1) * t + random.uniform(-width/2, width/2)
            
            # Random dot size
            dot_size = random.uniform(1, width/2)
            
            # Adjust opacity based on pressure and random factor
            point_color = list(color)
            if len(point_color) == 4:  # RGBA
                point_color[3] = int(point_color[3] * pressure * random.uniform(0.5, 1))
            
            # Draw the dot
            d.ellipse((x - dot_size, y - dot_size, 
                      x + dot_size, y + dot_size), 
                      fill=tuple(point_color))

def get_brush_by_type(brush_type):
    """
    Factory function to get the appropriate brush function by type.
    
    Args:
        brush_type (str): The type of brush ('round', 'flat', 'splatter')
        
    Returns:
        function: The brush drawing function
    """
    brushes = {
        'round': draw_round_brush,
        'flat': draw_flat_brush,
        'splatter': draw_splatter_brush
    }
    return brushes.get(brush_type, draw_round_brush)  # Default to round brush