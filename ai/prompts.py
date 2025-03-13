"""
Improved prompt construction with better spatial awareness for painting phases.
"""

from config.phases import PHASES

def get_initial_composition_prompt(prompt, history_text=""):
    """
    Get prompt for the initial composition phase with clear canvas dimensions.
    
    Args:
        prompt (str): User's original prompt
        history_text (str): Previous command history summary
        
    Returns:
        list: List of prompt segments for the AI
    """
    return [
        "You are a digital painting assistant. Create a simple, cartoonish MS Paint style artwork based on the user's text prompt.",
        
        "Here is the prompt:",
        prompt,
        
        "This is the SKETCH phase. Focus on creating the basic layout and shapes.",
        
        "IMPORTANT CANVAS INFORMATION:",
        "- The canvas is 500 pixels wide (x-axis) and 400 pixels tall (y-axis)",
        "- Coordinates (0,0) are at the top-left corner",
        "- Coordinates (500,400) are at the bottom-right corner",
        "- YOU MUST USE THE ENTIRE CANVAS AREA for your composition",
        "- Place objects across the full width (0-500) and height (0-400)",
        
        "Use <think> tags to plan your drawing. Consider what elements will go in each area of the canvas.",
        
        "Then provide a JSON array of drawing commands that will create a simple, colorful drawing. Each command should be one of:",
        
        "- {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': '#FF0000', 'width': 3}",
        "- {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': '#00FF00', 'width': 2, 'fill': true}",
        "- {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': '#0000FF', 'width': 2, 'fill': true}",
        "- {'action': 'fill_area', 'x': 100, 'y': 100, 'color': '#FFFF00'}",
        
        "Guidelines:",
        "- Use bold, simple shapes and bright colors",
        "- Create a simplified, cartoon-like representation",
        "- START with a background that covers the ENTIRE 500x400 canvas",
        "- Place main elements across the full canvas area, not just in one corner",
        "- Make sure to use a variety of x,y coordinates spanning from (0,0) to (500,400)",
        "- Don't try to create realistic artwork - aim for a simple, clear style",
        
        "Respond with your thinking in <think></think> tags, followed by a valid JSON array of drawing commands.",
    ]

def get_continuation_prompt(prompt, current_phase, current_part, image, history_text="", command_history=None):
    """
    Get prompt for continuing painting phases with enhanced spatial context preservation.
    
    Args:
        prompt (str): User's original prompt
        current_phase (str): Current phase name (e.g., 'sketch')
        current_part (int): Current part index within the phase
        image: The current image (will be included in prompt)
        history_text (str): Previous command history summary
        command_history (list): Actual command history objects
        
    Returns:
        list: List of prompt segments for the AI
    """
    phase_info = next((phase for phase in PHASES if phase["name"] == current_phase), PHASES[0])
    
    # Create a spatial context based on previous commands
    spatial_context = create_spatial_context(command_history)
    
    return [
        "You are a digital painting assistant. Continue improving the drawing based on the user's prompt.",
        
        "Original prompt:",
        prompt,
        
        "Current drawing:",
        image,
        
        "IMPORTANT: Your task is to CONTINUE and ENHANCE the current drawing, not to redraw it or start over.",
        
        "IMPORTANT CANVAS INFORMATION:",
        "- The canvas is 500 pixels wide (x-axis) and 400 pixels tall (y-axis)",
        "- Coordinates (0,0) are at the top-left corner",
        "- Coordinates (500,400) are at the bottom-right corner",
        
        "DETAILED CURRENT ELEMENTS ON CANVAS:",
        spatial_context,
        
        f"Current phase: {phase_info['display_name']} (Phase {PHASES.index(phase_info)+1} of {len(PHASES)})",
        f"Current part: {current_part+1} of {len(phase_info['parts'])}",
        
        "Use <think> tags to analyze the current drawing. Consider:",
        "1. What has already been drawn",
        "2. What elements need enhancement based on the current phase",
        "3. How to avoid overwriting or contradicting existing elements",
        "4. How to ensure continuity with the earlier versions",
        
        "Then provide a JSON array of drawing commands that will enhance the current drawing. Each command should be one of:",
        
        "- {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': '#FF0000', 'width': 3}",
        "- {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': '#00FF00', 'width': 2, 'fill': true}",
        "- {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': '#0000FF', 'width': 2, 'fill': true}",
        "- {'action': 'fill_area', 'x': 100, 'y': 100, 'color': '#FFFF00'}",
        "- {'action': 'modify_color', 'target_color': '#FF0000', 'new_color': '#0000FF', 'area_x': 150, 'area_y': 150, 'radius': 50}",
        
        "CRITICAL RULES:",
        "- DO NOT start from scratch - build on the existing drawing",
        "- DO NOT redraw major elements that already exist",
        "- DO NOT contradict or overwrite the existing drawing",
        "- DO focus on enhancing and detailing what's already there",
        "- ALWAYS position new elements in relation to existing ones",
        "- Make only 5-10 specific modifications per response",
        
        "For this specific phase, focus on:",
        f"{phase_info['parts'][current_part]['focus']}",
        
        "Respond with your thinking in <think></think> tags, followed by a valid JSON array of drawing commands.",
    ]

def create_spatial_context(command_history):
    """
    Create a detailed spatial context summary from command history.
    
    Args:
        command_history (list): List of previous drawing commands
        
    Returns:
        str: Detailed summary of what elements exist where on the canvas
    """
    if not command_history or len(command_history) == 0:
        return "No elements detected on canvas yet."
    
    # Track specific elements by type and location
    elements = []
    bg_color = None
    
    for i, cmd in enumerate(command_history):
        action = cmd.get('action', '')
        
        # Extract background color (usually the first filled rectangle covering the entire canvas)
        if action == 'draw_rect' and i < 5:  # Check early commands
            x0 = cmd.get('x0', 0)
            y0 = cmd.get('y0', 0)
            x1 = cmd.get('x1', 0)
            y1 = cmd.get('y1', 0)
            fill = cmd.get('fill', False)
            
            # If this covers most of the canvas, it's likely the background
            if x0 <= 10 and y0 <= 10 and x1 >= 490 and y1 >= 390 and fill:
                bg_color = cmd.get('color', 'unknown')
                elements.append(f"Background: {bg_color} rectangle covering the entire canvas")
                continue
        
        if action == 'draw_rect':
            x0 = cmd.get('x0', 0)
            y0 = cmd.get('y0', 0)
            x1 = cmd.get('x1', 0)
            y1 = cmd.get('y1', 0)
            color = cmd.get('color', 'unknown')
            fill = cmd.get('fill', False)
            
            width = abs(x1 - x0)
            height = abs(y1 - y0)
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            
            position = get_position_description(center_x, center_y)
            size_desc = get_size_description(width, height)
            
            elements.append(f"{size_desc} {color} rectangle in the {position} ({x0},{y0} to {x1},{y1}), {'filled' if fill else 'outlined'}")
            
        elif action == 'draw_circle':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            radius = cmd.get('radius', 0)
            color = cmd.get('color', 'unknown')
            fill = cmd.get('fill', False)
            
            position = get_position_description(x, y)
            size_desc = get_size_description(radius * 2, radius * 2)
            
            elements.append(f"{size_desc} {color} circle at {position} (center: {x},{y}, radius: {radius}), {'filled' if fill else 'outlined'}")
            
        elif action == 'draw_polyline':
            points = cmd.get('points', [])
            color = cmd.get('color', 'unknown')
            width = cmd.get('width', 1)
            
            if len(points) < 2:
                continue
                
            # Calculate center of polyline
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            
            position = get_position_description(center_x, center_y)
            
            # Estimate size of polyline
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            width_line = max_x - min_x
            height_line = max_y - min_y
            size_desc = get_size_description(width_line, height_line)
            
            elements.append(f"{size_desc} {color} line in the {position} (from {points[0]} to {points[-1]})")
    
    # Create a summary with a max of 15 elements to avoid overloading
    if len(elements) > 15:
        main_elements = elements[:15]
        summary = "Canvas content overview (showing 15 of {} elements):\n".format(len(elements))
        summary += "\n".join(f"- {element}" for element in main_elements)
    else:
        summary = "Canvas content overview ({} elements):\n".format(len(elements))
        summary += "\n".join(f"- {element}" for element in elements)
    
    # Add a note about background if detected
    if bg_color:
        summary += f"\n\nBackground color: {bg_color}"
    
    return summary

def get_position_description(x, y):
    """Provide a human-readable position description"""
    horizontal = "left" if x < 167 else "middle" if x < 333 else "right"
    vertical = "top" if y < 133 else "middle" if y < 266 else "bottom"
    return f"{vertical}-{horizontal}"

def get_size_description(width, height):
    """Provide a size description based on dimensions"""
    size = max(width, height)
    if size < 20:
        return "Small"
    elif size < 100:
        return "Medium"
    else:
        return "Large"
    
def get_region(x, y):
    """
    Determine which region of the canvas a point belongs to.
    
    Args:
        x (float): X coordinate
        y (float): Y coordinate
        
    Returns:
        str: Region name
    """
    if x < 250:
        if y < 200:
            return "top-left"
        else:
            return "bottom-left"
    else:
        if y < 200:
            return "top-right"
        else:
            return "bottom-right"
    
    return "center"  # Fallback

def format_command_history(command_history):
    """
    Create a concise summary of command history for context preservation.
    
    Args:
        command_history (list): List of previous drawing commands
        
    Returns:
        str: Formatted summary of command history
    """
    if not command_history or len(command_history) == 0:
        return ""
        
    # Count commands by type
    counts = {}
    recent_colors = set()
    
    # Only process the last 20 commands to keep it manageable
    recent_commands = command_history[-20:]
    
    for cmd in recent_commands:
        action = cmd.get('action', 'unknown')
        if action not in counts:
            counts[action] = 0
        counts[action] += 1
        
        # Track colors used
        if 'color' in cmd:
            recent_colors.add(cmd['color'])
    
    # Create a summary
    summary = "Recent drawing actions: "
    for action, count in counts.items():
        summary += f"{action} ({count}), "
    
    summary += f"\nRecent colors: {', '.join(list(recent_colors)[:5])}"
    
    return summary