"""
Prompt construction for different painting phases.
"""

from config.phases import PHASES

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
        "You are a digital painting assistant capable of creating expressive, painterly artwork. I will give you a prompt, and you will respond with a JSON array of drawing commands that creates organic, artistic strokes rather than rigid digital lines.",
        # Include command history if available
        history_text if history_text else "No previous commands recorded.",
        "First, use <think></think> tags to reason about the drawing as a painter would. This is the COMPOSITION PHASE (Part 1), focused on establishing the basic structure and layout. Consider:",
        " - What are the main elements of the composition and how should they be arranged?",
        " - How will you establish the basic forms, proportions, and spatial relationships?",
        " - What simple shapes will help build the foundation of the scene?",
        " - How would a traditional artist start blocking in the main elements?",
        
        f"Phase Focus: {current_part_info['focus']}",
        
        "After your reasoning, provide a JSON array of drawing commands. The valid commands are:",
        " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2, 'brush_type': 'round', 'texture': 'smooth', 'pressure': 1.0}",
        " - {'action': 'erase', 'points': [[x1, y1], [x2, y2], ...], 'width': 10}",
        " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue', 'texture': 'smooth'}",
        " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        
        "COMPOSITION PHASE Recommendations:",
        " - Use light, sketchy strokes to establish proportions",
        " - Focus on outlines and basic forms rather than details",
        " - Use muted colors or grayscale for initial blocking",
        " - Establish the horizon line and main spatial elements",
        
        "Brush types:",
        " - 'round': Creates tapered, organic strokes with varying width",
        " - 'flat': Creates angular, directional strokes like a flat brush",
        " - 'splatter': Creates a scattered, spray-like effect",
        
        "Canvas size is 500x400.",
        
        "Here is the prompt:",
        prompt,
        
        "Remember to use <think>your reasoning here</think> before your JSON response. Your final output should include both your thinking and the JSON array, but I will strip out the thinking part before processing.",
    ]

def get_continuation_prompt(prompt, current_phase, current_part, image, history_text=""):
    """
    Get the prompt for continuing an in-progress painting.
    
    Args:
        prompt (str): User's original prompt
        current_phase (str): Current phase name (e.g., 'composition')
        current_part (int): Current part index within the phase
        image: The current image (will be included in prompt)
        history_text (str): Previous command history
        
    Returns:
        list: List of prompt segments for the AI
    """
    phase_info = next((phase for phase in PHASES if phase["name"] == current_phase), PHASES[0])
    current_part_info = phase_info["parts"][current_part]
    
    # Base prompt elements for all non-initial phases/parts
    prompt_text = [
        "Here is the original prompt:",
        prompt,
        "Here is the current drawing:",
        image,
        f"Current Phase: {phase_info['display_name']} (Part {current_part + 1}/{len(phase_info['parts'])})",
        f"Phase Focus: {current_part_info['focus']}",
        # Include command history
        history_text if history_text else "No previous commands recorded.",
    ]
    
    # For first parts of each phase (excluding composition part 1)
    if current_part == 0 and current_phase != 'composition':
        prompt_text.extend([
            f"First, use <think></think> tags to analyze the current drawing as an artist would. This is the {phase_info['display_name'].upper()} PHASE (Part 1). Consider:",
            " - What are the key elements already established in the drawing?",
            " - How will you build upon the existing foundation?",
            f" - What specific techniques will you use to accomplish the phase goal: {current_part_info['focus']}",
            
            f"{phase_info['display_name'].upper()} PHASE Recommendations:",
        ])
        
        # Phase-specific recommendations
        if current_phase == 'color_blocking':
            prompt_text.extend([
                " - Use broader strokes with medium to large brushes",
                " - Focus on establishing main color areas rather than blending",
                " - Use flat brush for efficient coverage of larger areas",
                " - Consider the overall color relationships and balance",
            ])
        elif current_phase == 'detailing':
            prompt_text.extend([
                " - Use medium to small brushes for precise application",
                " - Add shadows and mid-tones to create volume",
                " - Refine edges between color areas",
                " - Begin adding smaller elements and features",
            ])
        else:  # final_touches
            prompt_text.extend([
                " - Use small brushes for precise details",
                " - Add highlights and reflections",
                " - Enhance focal areas with additional detail",
                " - Make subtle adjustments to color and contrast",
            ])
    
    # For second+ parts (diff-style refinement)
    else:
        prompt_text.extend([
            f"First, use <think></think> tags to critically analyze the current drawing. This is {phase_info['display_name'].upper()} PHASE (Part {current_part + 1}/{len(phase_info['parts'])}), focused on refinement and improvement.",
            
            "CAREFULLY EXAMINE THE CURRENT DRAWING AND IDENTIFY:",
            " - What elements are working well and should be preserved?",
            " - What specific areas need improvement or refinement?",
            " - What elements are missing or inconsistent with the prompt?",
            " - Where could you make targeted changes to significantly improve the artwork?",
            
            f"YOUR GOAL: {current_part_info['focus']}",
            
            "IMPORTANT: Instead of redrawing everything, focus on making TARGETED MODIFICATIONS to specific areas that need improvement.",
        ])
    
    # Command sets for all non-initial phases/parts
    prompt_text.extend([
        "After your analysis, provide a JSON array of drawing commands. Available commands include:",
        
        # Standard commands
        " - {'action': 'draw_polyline', 'points': [[x1, y1], [x2, y2], ...], 'color': 'red', 'width': 2, 'brush_type': 'round', 'texture': 'smooth', 'pressure': 1.0}",
        " - {'action': 'draw_rect', 'x0': 50, 'y0': 50, 'x1': 150, 'y1': 150, 'color': 'green', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        " - {'action': 'draw_circle', 'x': 100, 'y': 100, 'radius': 50, 'color': 'yellow', 'width': 2, 'fill': false, 'texture': 'smooth'}",
        " - {'action': 'fill_area', 'x': 100, 'y': 100, 'color': 'blue', 'texture': 'smooth'}",
        
        # Diff-style commands (for part 2+)
        " - {'action': 'erase_area', 'x0': 100, 'y0': 100, 'x1': 200, 'y1': 200}",
        " - {'action': 'modify_color', 'target_color': '#FF0000', 'new_color': '#0000FF', 'area_x': 150, 'area_y': 150, 'radius': 50}",
        " - {'action': 'enhance_detail', 'x': 200, 'y': 200, 'radius': 20, 'technique': 'highlight', 'color': '#FFFFFF'}",
        " - {'action': 'enhance_detail', 'x': 200, 'y': 200, 'radius': 20, 'technique': 'sharpen', 'color': '#000000'}",
        " - {'action': 'soften', 'x': 200, 'y': 200, 'radius': 20}",
        
        "Brush types:",
        " - 'round': Creates tapered, organic strokes with varying width",
        " - 'flat': Creates angular, directional strokes like a flat brush",
        " - 'splatter': Creates a scattered, spray-like effect",
        
        "Remember to use <think>your analysis here</think> before your JSON response.",
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
        
    history_text = "Previous drawing commands:\n"
    # Only show the last 10 commands to avoid prompt length issues
    for i, cmd in enumerate(command_history[-10:]):
        history_text += f"{i+1}. {str(cmd)}\n"
        
    return history_text