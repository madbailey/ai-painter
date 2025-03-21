"""
Improved prompt construction with better spatial awareness for painting phases.
"""

from config.phases import PHASES

def get_initial_sketch_prompt(prompt, history_text=""):
    """Creates initial sketch prompt with optimized token usage"""
    return [
        "Digital painting assistant. Create a simple sketch based on the prompt.",
        
        f"Prompt: {prompt}",
        
        "PHASE: SKETCH - Initial line drawing",
        "FOCUS: Create a simple line sketch of the main elements",
        
        "CANVAS: 500×400px. (0,0)=top-left, (500,400)=bottom-right",
        "USE ENTIRE CANVAS! Distribute elements across all regions (TL/TR/BL/BR)",
        
        "JSON Commands:",
        "{'action':'draw_polyline','points':[[x,y],...],'color':'#000000','width':1}",
        "{'action':'draw_rect','x0':N,'y0':N,'x1':N,'y1':N,'color':'#000000','width':1,'fill':false}",
        "{'action':'draw_circle','x':N,'y':N,'radius':N,'color':'#000000','width':1,'fill':false}",
        
        "- SKETCH PHASE: Please use thin black lines only (width:1)",
        "- Please no FILL or COLOR in this phase - only outlines!",
        "- Try to plan the entire 500×400px composition",
        "- Include all major elements from the prompt",
        "- Simple cartoon-like style, not realistic",
        
        "Respond with <think></think> tags, then JSON array of commands wrapped in ```json``` blocks."
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
    
    # Create compressed spatial and command summaries
    spatial_context = create_spatial_context(command_history)
    cmd_summary = format_command_history(command_history)
    
    # Phase-specific instructions without repeating main prompt content
    phase_instructions = {
        'sketch': "Create simple outline of main elements with thin lines",
        'refine_lines': "Strengthen important lines and add structural details",
        'color_blocking': "Fill outlined areas with flat base colors",
        'detail': "Add shading, highlights, and small details"
    }
    
    instruction = phase_instructions.get(current_phase, "Improve the drawing")
    
    # Part-specific focus to give more direction
    if phase_info and 'parts' and len(phase_info['parts']) > current_part:
        part_focus = phase_info['parts'][current_part]['focus']
    else:
        part_focus = "Continue working on the current phase"
    
    return [
        "Digital painting assistant.",
        
        f"PHASE: {phase_info['display_name']} - {instruction}",
        f"FOCUS: {part_focus}",
        
        "Current drawing:",
        image,
        
        "CANVAS: 500×400px | STATUS:",
        spatial_context,
        cmd_summary,
        
        "AVAILABLE COMMANDS:",
        "{'action':'draw_polyline','points':[[x,y],...],'color':'#HEX','width':N}",
        "{'action':'draw_rect','x0':N,'y0':N,'x1':N,'y1':N,'color':'#HEX','fill':bool}",
        "{'action':'draw_circle','x':N,'y':N,'radius':N,'color':'#HEX','fill':bool}",
        "{'action':'fill_area','x':N,'y':N,'color':'#HEX'}",
        "{'action':'modify_color','target_color':'#HEX','new_color':'#HEX','area_x':N,'area_y':N}",
        
        "⚠️ CRITICAL:",
        "- Work across ENTIRE 500×400px canvas",
        "- Make 5-8 specific changes to progress the drawing",
        "- Keep style simple and cartoonish",
        "- Respond in this format: ```json [commands] ```",

        "Respond with <think></think> tags, then only a valid JSON array of commands inside ```json and ``` tags."
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
        return "Canvas: empty"
    
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
    """Maps coordinates to canvas regions using shorter region codes"""
    if x < 250:
        return "TL" if y < 200 else "BL"
    else:
        return "TR" if y < 200 else "BR"

def format_command_history(command_history):
    """Creates minimal summary of recent drawing activity"""
    if not command_history or len(command_history) == 0:
        return ""
        
    # Count commands and colors from last 10 commands only
    counts = {}
    recent_colors = set()
    
    for cmd in command_history[-10:]:
        action = cmd.get('action', '')
        # Use abbreviated action names
        action_short = action.replace('draw_', '').replace('_', '')[:5]
        
        counts[action_short] = counts.get(action_short, 0) + 1
        
        if 'color' in cmd:
            recent_colors.add(cmd['color'])
    
    # Create compact summary
    actions = " ".join(f"{a}:{c}" for a, c in counts.items())
    colors = "/".join(list(recent_colors)[:3])
    
    return f"Hist: {actions} Col: {colors}"