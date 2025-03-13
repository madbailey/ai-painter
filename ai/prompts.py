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
        
        "This is the COMPOSITION phase. Focus on creating the basic layout and shapes.",
        
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
    Get prompt for continuing painting phases with spatial context preservation.
    
    Args:
        prompt (str): User's original prompt
        current_phase (str): Current phase name (e.g., 'composition')
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
    
    # Get the appropriate instruction based on phase
    phase_instruction = "Add more details and improve the drawing."
    if current_phase == 'color_blocking':
        phase_instruction = "Add colors to the main areas of the drawing."
    elif current_phase == 'detailing':
        phase_instruction = "Add details to make the drawing more interesting."
    elif current_phase == 'final_touches':
        phase_instruction = "Add final touches to complete the drawing."
    
    return [
        "You are a digital painting assistant. Continue improving the drawing based on the user's prompt.",
        
        "Original prompt:",
        prompt,
        
        "Current drawing:",
        image,
        
        "IMPORTANT CANVAS INFORMATION:",
        "- The canvas is 500 pixels wide (x-axis) and 400 pixels tall (y-axis)",
        "- Coordinates (0,0) are at the top-left corner",
        "- Coordinates (500,400) are at the bottom-right corner",
        "- YOU MUST USE THE ENTIRE CANVAS AREA for your modifications",
        "- Look at the current drawing and make changes across the FULL CANVAS",
        
        "Current elements on canvas:",
        spatial_context,
        
        f"Current phase: {phase_info['display_name']}",
        
        phase_instruction,
        
        "Use <think> tags to analyze the current drawing and think about how to improve it.",
        
        "Then provide a JSON array of drawing commands that will enhance the current drawing. Each command should be one of:",
        
        "- {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': '#FF0000', 'width': 3}",
        "- {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': '#00FF00', 'width': 2, 'fill': true}",
        "- {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': '#0000FF', 'width': 2, 'fill': true}",
        "- {'action': 'fill_area', 'x': 100, 'y': 100, 'color': '#FFFF00'}",
        "- {'action': 'modify_color', 'target_color': '#FF0000', 'new_color': '#0000FF', 'area_x': 150, 'area_y': 150, 'radius': 50}",
        
        "IMPORTANT SPATIAL INSTRUCTIONS:",
        "- DO NOT focus only on the top-left corner! Use the entire canvas (0-500 x, 0-400 y)",
        "- Make modifications across the full width and height of the canvas",
        "- Add details to elements throughout the entire drawing",
        "- If adding new elements, place them in appropriate positions relative to existing elements",
        "- Look at the center, right side, and bottom areas of the canvas too",
        
        "Other important guidelines:",
        "- DO NOT start from scratch - build on the existing drawing",
        "- Make only 5-10 specific modifications",
        "- Maintain the simple, MS Paint cartoon style",
        "- Use bright, bold colors",
        
        "Respond with your thinking in <think></think> tags, followed by a valid JSON array of drawing commands.",
    ]

def create_spatial_context(command_history):
    """
    Create a spatial context summary from command history.
    
    Args:
        command_history (list): List of previous drawing commands
        
    Returns:
        str: Summary of what elements exist where on the canvas
    """
    if not command_history or len(command_history) == 0:
        return "No elements detected on canvas yet."
    
    # Initialize regions of the canvas
    regions = {
        "top-left": [],
        "top-right": [],
        "center": [],
        "bottom-left": [],
        "bottom-right": []
    }
    
    for cmd in command_history:
        action = cmd.get('action', '')
        
        if action == 'draw_rect':
            x0 = cmd.get('x0', 0)
            y0 = cmd.get('y0', 0)
            x1 = cmd.get('x1', 0)
            y1 = cmd.get('y1', 0)
            color = cmd.get('color', 'unknown')
            
            # Determine region
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            region = get_region(center_x, center_y)
            
            regions[region].append(f"{color} rectangle")
            
        elif action == 'draw_circle':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            radius = cmd.get('radius', 0)
            color = cmd.get('color', 'unknown')
            
            region = get_region(x, y)
            regions[region].append(f"{color} circle")
            
        elif action == 'fill_area':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            color = cmd.get('color', 'unknown')
            
            region = get_region(x, y)
            regions[region].append(f"{color} fill")
    
    # Create a summary
    summary = "Canvas content overview:\n"
    for region, elements in regions.items():
        if elements:
            summary += f"- {region}: {', '.join(elements[:3])}"
            if len(elements) > 3:
                summary += f" and {len(elements)-3} more"
            summary += "\n"
        else:
            summary += f"- {region}: empty\n"
    
    return summary

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