"""
Improved prompt construction with better spatial awareness for painting phases.
"""

from config.phases import PHASES

def get_initial_composition_prompt(prompt, history_text=""):
    """Creates initial composition prompt with optimized token usage"""
    return [
        "You are a digital painting assistant. Create a simple, cartoonish MS Paint style artwork.",
        
        f"Prompt: {prompt}",
        
        "PHASE: COMPOSITION - Basic layout and shapes",
        
        "CANVAS: 500×400px. (0,0)=top-left, (500,400)=bottom-right",
        "USE ENTIRE CANVAS! Distribute elements across all regions (TL/TR/BL/BR)",
        
        "JSON Commands:",
        "{'action':'draw_polyline','points':[[x1,y1],[x2,y2],...],'color':'#HEX','width':N}",
        "{'action':'draw_rect','x0':N,'y0':N,'x1':N,'y1':N,'color':'#HEX','width':N,'fill':bool}",
        "{'action':'draw_circle','x':N,'y':N,'radius':N,'color':'#HEX','width':N,'fill':bool}",
        "{'action':'fill_area','x':N,'y':N,'color':'#HEX'}",
        
        "IMPORTANT:",
        "- START with background covering ALL 500×400px",
        "- Use ALL canvas regions, not just top-left",
        "- Use bold shapes and bright colors",
        "- Simple cartoon-like style, not realistic",
        
        "Respond with <think></think> tags, then valid JSON array."
    ]

def get_continuation_prompt(prompt, current_phase, current_part, image, history_text="", command_history=None):
    """Creates optimized continuation prompt with enhanced spatial awareness"""
    phase_info = next((phase for phase in PHASES if phase["name"] == current_phase), PHASES[0])
    
    # Create compressed spatial and command summaries
    spatial_context = create_spatial_context(command_history)
    cmd_summary = format_command_history(command_history)
    
    # Phase-specific instructions, kept concise
    phase_instructions = {
        'composition': "Create basic layout and shapes",
        'color_blocking': "Add colors to main areas",
        'detailing': "Add details to make more interesting",
        'final_touches': "Add final touches to complete drawing"
    }
    
    instruction = phase_instructions.get(current_phase, "Improve the drawing")
    
    return [
        "Digital painting assistant. Continue improving drawing.",
        
        f"Prompt: {prompt}",
        
        "Current drawing:",
        image,
        
        f"PHASE: {phase_info['display_name']} - {instruction}",
        
        "CANVAS: 500×400px. CURRENT STATUS:",
        spatial_context,
        cmd_summary,
        
        "JSON Commands:",
        "{'action':'draw_polyline','points':[[x,y],...],'color':'#HEX','width':N}",
        "{'action':'draw_rect','x0':N,'y0':N,'x1':N,'y1':N,'color':'#HEX','fill':bool}",
        "{'action':'draw_circle','x':N,'y':N,'radius':N,'color':'#HEX','fill':bool}",
        "{'action':'fill_area','x':N,'y':N,'color':'#HEX'}",
        "{'action':'modify_color','target_color':'#HEX','new_color':'#HEX','area_x':N,'area_y':N}",
        
        "SPATIAL RULES:",
        "⚠️ USE ALL REGIONS (TL/TR/BL/BR) - DON'T FOCUS ONLY ON TOP-LEFT!",
        "- Update elements across ENTIRE canvas (0-500×0-400)",
        "- Add 5-10 specific modifications to EXISTING drawing",
        "- Maintain MS Paint cartoon style with bright colors",
        
        "Respond with <think></think> tags, then JSON array."
    ]

def create_spatial_context(command_history):
    """Summarizes canvas elements by region, optimized for token efficiency"""
    if not command_history or len(command_history) == 0:
        return "Canvas: empty"
    
    # Track element count per region (using 4 regions only to reduce tokens)
    regions = {"TL": [], "TR": [], "BL": [], "BR": []}
    
    # Process only last 20 commands to reduce token usage
    for cmd in command_history[-20:]:
        action = cmd.get('action', '')
        color = cmd.get('color', '')
        
        if action == 'draw_rect':
            center_x = (cmd.get('x0', 0) + cmd.get('x1', 0)) / 2
            center_y = (cmd.get('y0', 0) + cmd.get('y1', 0)) / 2
            region = get_region(center_x, center_y)
            regions[region].append(f"{color} rect")
            
        elif action == 'draw_circle':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            region = get_region(x, y)
            regions[region].append(f"{color} circ")
            
        elif action == 'fill_area':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            region = get_region(x, y)
            regions[region].append(f"{color} fill")
            
        elif action == 'draw_polyline':
            points = cmd.get('points', [])
            if points and len(points) > 0:
                # Use first point to determine region
                x, y = points[0][0], points[0][1]
                region = get_region(x, y)
                regions[region].append(f"{color} line")
    
    # Create compact summary
    summary = "Canvas: "
    for region, elements in regions.items():
        if elements:
            count = len(elements)
            summary += f"{region}({count}) "
    
    # Note empty regions
    empty = [r for r, e in regions.items() if not e]
    if empty:
        summary += f"Empty: {','.join(empty)}"
        
    return summary

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