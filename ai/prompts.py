"""
Prompt construction for different painting phases with better context management.
"""

from config.phases import PHASES
from utils.text import get_element_registry_summary, summarize_command_history

def get_initial_composition_prompt(prompt, history_text=""):
    """
    Get the prompt for the initial composition phase.
    
    Args:
        prompt (str): User's original prompt
        history_text (str): Previous command history
        
    Returns:
        list: List of prompt segments for the AI
    """
    current_phase = PHASES[0]  # Composition phase
    current_part_info = current_phase["parts"][0]
    
    return [
        "You are a digital painting assistant capable of creating expressive, MS Paint style artwork. Create simple, bold strokes that are fully opaque with bright colors. Avoid leaving white/blank space in your compositions. Your style resembles children's book illustrations - simple, colorful, and engaging.",
        
        # Include command history if available
        history_text if history_text else "No previous commands recorded.",
        
        "This is the COMPOSITION PHASE (Part 1), focused on establishing the basic structure and layout.",
        
        "Use a three-stage thinking process:",
        
        "1. <think>Consider the input prompt and what your goals are for this drawing. What main elements should be included? What style and colors would work best?</think>",
        
        "2. <visualize>Imagine what you want the completed image to contain. Picture the final composition with all elements in place. How will they be arranged? What colors will dominate?</visualize>",
        
        "3. <decompose>Break down the image into a background and up to three main elements that can be created independently. Identify each element and how it will be positioned in relation to others.</decompose>",
        
        f"Phase Focus: {current_part_info['focus']}",
        
        "After your three-stage thinking process, provide JSON outputs for each element in separate tags:",
        
        "<background>[JSON array of drawing commands for the background]</background>",
        "<element1>[JSON array of drawing commands for the first main element]</element1>",
        "<element2>[JSON array of drawing commands for the second main element (if applicable)]</element2>",
        "<element3>[JSON array of drawing commands for the third main element (if applicable)]</element3>",
        
        "The valid commands for each element are:",
        " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2, 'brush_type': 'round', 'texture': 'smooth', 'pressure': 1.0}",
        " - {'action': 'erase', 'points': [[x1, y1], [x2, y2], ...], 'width': 10}",
        " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue', 'texture': 'smooth'}",
        " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        
        "COMPOSITION PHASE Recommendations:",
        " - Use bold, simple strokes to establish shapes",
        " - Cover the entire canvas, avoiding white/blank space",
        " - Use bright, vibrant colors for visual appeal",
        " - Create distinct elements that can be modified separately in later phases",
        
        "Brush types:",
        " - 'round': Creates tapered, organic strokes with varying width",
        " - 'flat': Creates angular, directional strokes like a flat brush",
        " - 'splatter': Creates a scattered, spray-like effect",
        
        "Canvas size is 500x400.",
        
        "Here is the prompt:",
        prompt,
        
        "Remember to organize your response with the three thinking stages followed by element-specific JSON outputs in their own tags. DO NOT use ```json code blocks inside the element tags.",
    ]

def get_continuation_prompt(prompt, current_phase, current_part, image, history_text="", command_history=None):
    """
    Get the prompt for continuing an in-progress painting with improved context preservation.
    
    Args:
        prompt (str): User's original prompt
        current_phase (str): Current phase name (e.g., 'composition')
        current_part (int): Current part index within the phase
        image: The current image (will be included in prompt)
        history_text (str): Previous command history
        command_history (list): Actual command history objects for better context
        
    Returns:
        list: List of prompt segments for the AI
    """
    phase_info = next((phase for phase in PHASES if phase["name"] == current_phase), PHASES[0])
    current_part_info = phase_info["parts"][current_part]
    
    # Generate a more descriptive history summary if available
    if command_history:
        summarized_history = summarize_command_history(command_history)
    else:
        summarized_history = history_text
    
    # Get a summary of the element registry
    element_registry_summary = get_element_registry_summary()
    
    # Base prompt elements for all non-initial phases/parts
    prompt_text = [
        "You are a digital painting assistant creating MS Paint style artwork. Create simple, bold strokes with bright colors, avoiding white/blank space.",
        
        "Here is the original prompt:",
        prompt,
        
        "Here is the current drawing:",
        image,
        
        f"Current Phase: {phase_info['display_name']} (Part {current_part + 1}/{len(phase_info['parts'])})",
        f"Phase Focus: {current_part_info['focus']}",
        
        "Current elements summary:",
        element_registry_summary,
        
        # Include command history
        summarized_history if summarized_history else "No previous commands recorded.",
        
        f"IMPORTANT: You are now in the {phase_info['display_name'].upper()} PHASE. Do NOT restart from scratch - build upon the existing drawing.",
    ]
    
    # For first parts of each new phase (excluding composition part 1)
    if current_part == 0 and current_phase != 'composition':
        prompt_text.extend([
            "Use the three-stage thinking process:",
            
            "1. <think>Consider the current state of the drawing and what improvements are needed for this phase. What elements need enhancement? How can you maintain the MS Paint style while advancing the drawing?</think>",
            
            "2. <visualize>Imagine how the drawing should evolve in this phase. What changes or additions will take it closer to the final vision?</visualize>",
            
            "3. <decompose>Identify specific areas or elements that need work. Break down your approach into modifications for the background and up to three main elements.</decompose>",
            
            f"{phase_info['display_name'].upper()} PHASE Recommendations:",
        ])
        
        # Phase-specific recommendations
        if current_phase == 'color_blocking':
            prompt_text.extend([
                " - Use bold, vibrant colors to fill all areas",
                " - Ensure no white/blank space remains visible",
                " - Keep colors simple and distinct (MS Paint style)",
                " - Maintain clear boundaries between different elements",
                " - DO NOT erase or redraw the entire image - enhance what's already there",
            ])
        elif current_phase == 'detailing':
            prompt_text.extend([
                " - Add simple details that enhance recognition of elements",
                " - Use contrasting colors for details to make them pop",
                " - Maintain the childlike simplicity of the style",
                " - Add basic shadows or highlights with solid colors",
                " - DO NOT erase or redraw the entire image - enhance what's already there",
            ])
        else:  # final_touches
            prompt_text.extend([
                " - Add final defining details that complete the image",
                " - Ensure all areas have appropriate coloring",
                " - Reinforce the boundaries between elements",
                " - Add simple decorative elements if appropriate",
                " - DO NOT erase or redraw the entire image - enhance what's already there",
            ])
    
    # For second+ parts (improvement and refinement)
    else:
        prompt_text.extend([
            "Use the three-stage thinking process:",
            
            "1. <think>Critically analyze the current drawing. What's working well? What specific areas need improvement?</think>",
            
            "2. <visualize>Imagine how targeted changes would improve the overall composition. How can you enhance the image while maintaining its MS Paint style simplicity?</visualize>",
            
            "3. <decompose>Identify specific elements that need refinement. What modifications will have the biggest impact?</decompose>",
            
            f"YOUR GOAL: {current_part_info['focus']}",
            
            "IMPORTANT: Focus on making TARGETED MODIFICATIONS to specific areas that need improvement. Do NOT redraw the entire image.",
        ])
    
    # Element-based outputs for all continuation prompts
    prompt_text.extend([
        "After your three-stage thinking process, provide JSON outputs for modifications to each element in separate tags:",
        
        "<background_mod>[JSON array of drawing commands to modify the background]</background_mod>",
        "<element1_mod>[JSON array of drawing commands to modify the first main element]</element1_mod>",
        "<element2_mod>[JSON array of drawing commands to modify the second main element (if applicable)]</element2_mod>",
        "<element3_mod>[JSON array of drawing commands to modify the third main element (if applicable)]</element3_mod>",
        
        "Available commands include:",
        
        # Standard commands
        " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2, 'brush_type': 'round', 'texture': 'smooth', 'pressure': 1.0}",
        " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue', 'texture': 'smooth'}",
        
        # Modification commands
        " - {'action': 'erase_area', 'x0': 100, 'y0': 100, 'x1': 200, 'y1': 200}",
        " - {'action': 'modify_color', 'target_color': '#FF0000', 'new_color': '#0000FF', 'area_x': 150, 'area_y': 150, 'radius': 50}",
        " - {'action': 'enhance_detail', 'x': 200, 'y': 200, 'radius': 20, 'technique': 'highlight', 'color': '#FFFFFF'}",
        " - {'action': 'enhance_detail', 'x': 200, 'y': 200, 'radius': 20, 'technique': 'sharpen', 'color': '#000000'}",
        " - {'action': 'soften', 'x': 200, 'y': 200, 'radius': 20}",
        
        "Brush types:",
        " - 'round': Creates tapered, organic strokes with varying width",
        " - 'flat': Creates angular, directional strokes like a flat brush",
        " - 'splatter': Creates a scattered, spray-like effect",
        
        "Remember to organize your response with the three thinking stages followed by element-specific JSON outputs in their own tags. DO NOT use ```json code blocks inside the element tags.",
    ])
    
    return prompt_text

def format_command_history(command_history):
    """
    Format the command history for readability in prompts.
    
    Args:
        command_history (list): List of previous drawing commands
        
    Returns:
        str: Formatted command history as a string
    """
    if not command_history or len(command_history) == 0:
        return ""
    
    # If possible, use the improved summary method
    summary = summarize_command_history(command_history)
    if summary:
        return summary
        
    # Fallback to basic formatting
    history_text = "Previous drawing commands:\n"
    # Only show the last 10 commands to avoid prompt length issues
    for i, cmd in enumerate(command_history[-10:]):
        history_text += f"{i+1}. {str(cmd)}\n"
        
    return history_text