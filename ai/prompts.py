"""
Simplified prompt construction for different painting phases.
"""

from config.phases import PHASES

def get_initial_composition_prompt(prompt, history_text=""):
    """
    Get simplified prompt for the initial composition phase.
    
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
        
        "Use <think> tags to briefly think about how to approach this drawing.",
        
        "Then provide a JSON array of drawing commands that will create a simple, colorful drawing. Each command should be one of:",
        
        "- {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': '#FF0000', 'width': 3}",
        "- {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': '#00FF00', 'width': 2, 'fill': true}",
        "- {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': '#0000FF', 'width': 2, 'fill': true}",
        "- {'action': 'fill_area', 'x': 100, 'y': 100, 'color': '#FFFF00'}",
        
        "Guidelines:",
        "- Use bold, simple shapes and bright colors",
        "- Create a simplified, cartoon-like representation",
        "- Canvas size is 500x400 pixels",
        "- Include a simple background",
        "- Don't try to create realistic artwork - aim for a simple, clear style",
        
        "Respond with your thinking in <think></think> tags, followed by a valid JSON array of drawing commands.",
    ]

def get_continuation_prompt(prompt, current_phase, current_part, image, history_text="", command_history=None):
    """
    Get simplified prompt for continuing painting phases.
    
    Args:
        prompt (str): User's original prompt
        current_phase (str): Current phase name (e.g., 'composition')
        current_part (int): Current part index within the phase
        image: The current image (will be included in prompt)
        history_text (str): Previous command history summary
        command_history (list): Actual command history objects (unused in simplified version)
        
    Returns:
        list: List of prompt segments for the AI
    """
    phase_info = next((phase for phase in PHASES if phase["name"] == current_phase), PHASES[0])
    
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
        
        f"Current phase: {phase_info['display_name']}",
        
        phase_instruction,
        
        "Use <think> tags to briefly analyze the current drawing and think about how to improve it.",
        
        "Then provide a JSON array of drawing commands that will enhance the current drawing. Each command should be one of:",
        
        "- {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': '#FF0000', 'width': 3}",
        "- {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': '#00FF00', 'width': 2, 'fill': true}",
        "- {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': '#0000FF', 'width': 2, 'fill': true}",
        "- {'action': 'fill_area', 'x': 100, 'y': 100, 'color': '#FFFF00'}",
        "- {'action': 'modify_color', 'target_color': '#FF0000', 'new_color': '#0000FF', 'area_x': 150, 'area_y': 150, 'radius': 50}",
        
        "IMPORTANT:",
        "- DO NOT start from scratch - build on the existing drawing",
        "- Make only 5-10 specific modifications",
        "- Maintain the simple, MS Paint cartoon style",
        "- Use bright, bold colors",
        
        "Respond with your thinking in <think></think> tags, followed by a valid JSON array of drawing commands.",
    ]

def format_command_history(command_history):
    """
    Create a simplified summary of command history.
    
    Args:
        command_history (list): List of previous drawing commands
        
    Returns:
        str: Simple summary of command history
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