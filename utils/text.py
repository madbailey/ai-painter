"""
Text processing utilities with improved element tracking and command history integration.
"""

import re
import json
import copy

# Keep track of elements across phases
ELEMENT_REGISTRY = {
    "background": [],
    "element1": [],
    "element2": [],
    "element3": []
}

def reset_element_registry():
    """Reset the element registry to empty state."""
    global ELEMENT_REGISTRY
    ELEMENT_REGISTRY = {
        "background": [],
        "element1": [],
        "element2": [],
        "element3": []
    }

def update_element_registry(element_name, commands):
    """
    Update the element registry with new commands.
    
    Args:
        element_name (str): Name of the element (background, element1, etc.)
        commands (list): List of commands for this element
    """
    global ELEMENT_REGISTRY
    if element_name in ELEMENT_REGISTRY:
        # For modification commands, we want to append rather than replace
        if isinstance(commands, list):
            ELEMENT_REGISTRY[element_name].extend(commands)
        else:
            ELEMENT_REGISTRY[element_name].append(commands)

def extract_thinking(text):
    """
    Extract content within the three thinking stages:
    <think></think>, <visualize></visualize>, and <decompose></decompose>
    
    Args:
        text (str): Text that may contain thinking tags
        
    Returns:
        str: The combined content from all thinking tags, or empty string if none found
    """
    thinking = []
    
    # Extract content from each thinking stage
    patterns = [
        r"<think>([\s\S]*?)</think>",
        r"<visualize>([\s\S]*?)</visualize>",
        r"<decompose>([\s\S]*?)</decompose>"
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            stage_name = ["THINKING", "VISUALIZING", "DECOMPOSING"][i]
            content = matches[0].strip()
            thinking.append(f"--- {stage_name} ---\n{content}")
    
    return "\n\n".join(thinking)

def extract_element_json(text, phase_name="composition", part=0):
    """
    Extract JSON arrays from element tags in the text and update the element registry.
    
    Args:
        text (str): Text containing element tags with JSON content
        phase_name (str): Current phase name
        part (int): Current part index
        
    Returns:
        list: List of commands extracted from all elements
    """
    all_commands = []
    is_initial_phase = (phase_name == "composition" and part == 0)
    
    # Clear registry if starting fresh
    if is_initial_phase:
        reset_element_registry()
    
    # Track which elements we've found in this response
    found_elements = set()
    
    # Initial composition - extract from background and elements
    if is_initial_phase:
        element_patterns = [
            (r"<background>([\s\S]*?)</background>", "background"),
            (r"<element1>([\s\S]*?)</element1>", "element1"), 
            (r"<element2>([\s\S]*?)</element2>", "element2"),
            (r"<element3>([\s\S]*?)</element3>", "element3")
        ]
        
        for pattern, elem_name in element_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Clean the JSON content
                    cleaned_json = clean_json_string(match)
                    element_commands = json.loads(cleaned_json)
                    
                    if isinstance(element_commands, list):
                        # Record which elements we found
                        found_elements.add(elem_name)
                        
                        # Update the element registry
                        update_element_registry(elem_name, element_commands)
                        
                        # Add commands to the output
                        all_commands.extend(element_commands)
                    else:
                        # If it's a single command object, add it
                        found_elements.add(elem_name)
                        update_element_registry(elem_name, [element_commands])
                        all_commands.append(element_commands)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON from element {elem_name}: {e}")
    
    # Continuation phases - extract from modification tags
    else:
        mod_patterns = [
            (r"<background_mod>([\s\S]*?)</background_mod>", "background"),
            (r"<element1_mod>([\s\S]*?)</element1_mod>", "element1"),
            (r"<element2_mod>([\s\S]*?)</element2_mod>", "element2"),
            (r"<element3_mod>([\s\S]*?)</element3_mod>", "element3")
        ]
        
        for pattern, elem_name in mod_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Skip empty modifications
                    if not match.strip() or match.strip() == "[]":
                        continue
                        
                    # Clean the JSON content
                    cleaned_json = clean_json_string(match)
                    element_commands = json.loads(cleaned_json)
                    
                    # Record which elements we found
                    found_elements.add(elem_name)
                    
                    if isinstance(element_commands, list):
                        # Update the element registry
                        update_element_registry(elem_name, element_commands)
                        
                        # Add commands to the output
                        all_commands.extend(element_commands)
                    else:
                        # If it's a single command object, add it
                        update_element_registry(elem_name, [element_commands])
                        all_commands.append(element_commands)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON from element {elem_name}: {e}")
    
    # If no elements were found, try the old method as fallback
    if not found_elements:
        print("No elements found, trying fallback method")
        try:
            # Clean the JSON string from the entire response
            cleaned_json = clean_json_string(text)
            fallback_commands = json.loads(cleaned_json)
            
            if isinstance(fallback_commands, list):
                all_commands = fallback_commands
            else:
                all_commands = [fallback_commands]
        except:
            print("Fallback method also failed")
    
    print(f"Extracted {len(all_commands)} commands from {len(found_elements)} elements")
    for elem_name in found_elements:
        print(f"- {elem_name}: {len(ELEMENT_REGISTRY[elem_name])} commands")
    
    return all_commands

def get_element_registry_summary():
    """
    Get a summary of the element registry for debugging.
    
    Returns:
        str: Text summary of elements and command counts
    """
    summary = "Element Registry Summary:\n"
    for elem_name, commands in ELEMENT_REGISTRY.items():
        summary += f"- {elem_name}: {len(commands)} commands\n"
    return summary

def summarize_command_history(command_history, max_commands=5):
    """
    Create a concise summary of command history for context preservation.
    
    Args:
        command_history (list): List of previous drawing commands
        max_commands (int): Maximum number of commands to include per element
        
    Returns:
        str: Formatted summary of command history by element
    """
    # Group commands by action type to identify elements
    actions_by_type = {}
    
    for cmd in command_history:
        action = cmd.get('action', 'unknown')
        if action not in actions_by_type:
            actions_by_type[action] = []
        actions_by_type[action].append(cmd)
    
    # Create a summary text
    summary = "Command History Summary:\n"
    
    # Summarize background commands (fill_area, etc.)
    if 'fill_area' in actions_by_type:
        fill_cmds = actions_by_type['fill_area'][-max_commands:]
        summary += f"Background: {len(fill_cmds)} fill commands, "
        summary += f"most recent color: {fill_cmds[-1].get('color', 'unknown')}\n"
    
    # Summarize drawing commands (shapes, etc.)
    for action in ['draw_rect', 'draw_circle', 'draw_polyline']:
        if action in actions_by_type:
            draw_cmds = actions_by_type[action][-max_commands:]
            summary += f"{action}: {len(draw_cmds)} commands, "
            if action == 'draw_rect':
                summary += f"most recent: {draw_cmds[-1].get('color', 'unknown')} rectangle at "
                summary += f"({draw_cmds[-1].get('x0', '?')},{draw_cmds[-1].get('y0', '?')})\n"
            elif action == 'draw_circle':
                summary += f"most recent: {draw_cmds[-1].get('color', 'unknown')} circle at "
                summary += f"({draw_cmds[-1].get('x', '?')},{draw_cmds[-1].get('y', '?')})\n"
            else:
                summary += f"most recent: {draw_cmds[-1].get('color', 'unknown')} line\n"
    
    # Summarize modification commands
    for action in ['modify_color', 'enhance_detail', 'erase_area', 'soften']:
        if action in actions_by_type:
            mod_cmds = actions_by_type[action][-max_commands:]
            summary += f"{action}: {len(mod_cmds)} commands\n"
    
    return summary

def clean_json_string(json_str):
    """
    Clean JSON string and handle common formatting issues.
    
    Args:
        json_str (str): Raw JSON string that may contain markdown or other formatting
                        
    Returns:
        str: Cleaned JSON string
    """
    # Clean code blocks if present
    if '```' in json_str:
        pattern = r"```(?:json)?([\s\S]*?)```"
        matches = re.findall(pattern, json_str, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
           json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    # Replace single quotes with double quotes if needed
    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    json_str = json_str.strip()
    print(f"Cleaned JSON string: {json_str[:100]}...")
    
    # Try to fix common JSON errors
    # 1. Fix missing commas after closing quotes in property values
    json_str = re.sub(r':\s*"([^"]*)"(?=\s*})', r': "\1",', json_str)
    json_str = re.sub(r':\s*"([^"]*)"(?=\s*")', r': "\1",', json_str)
    
    # 2. Remove trailing commas before closing brackets (valid in JS, not in JSON)
    json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
    
    # 3. Fix duplicate properties by keeping the last one
    # This is harder to do with regex alone, so we'll try parsing and fixing
    try:
        # First attempt to parse
        json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Warning: JSON error: {e}")
        
        if "Duplicate key" in str(e):
            # Try to fix duplicate key issues
            try:
                # Convert to a more lenient parser that overwrites duplicates
                import ast
                # Replace "null" with "None" for Python parsing
                py_str = json_str.replace('null', 'None').replace('true', 'True').replace('false', 'False')
                # Use ast.literal_eval to parse it as Python (overwrites duplicates)
                data = ast.literal_eval(py_str)
                # Convert back to JSON
                json_str = json.dumps(data)
            except:
                print("Could not fix duplicate keys")
        
        # If we still have errors, try more aggressive cleaning
        try:
            json.loads(json_str)
        except:
            print("Attempting aggressive cleaning")
            
            # Try to find and parse individual valid commands
            pattern = r"\{\s*\"action\":[^\}]+\}"
            commands = re.findall(pattern, json_str, re.DOTALL)
            valid_commands = []
            
            for cmd in commands:
                try:
                    # Add missing commas and fix quotes
                    fixed_cmd = re.sub(r':\s*"([^"]*)"(?=\s*})', r': "\1"', cmd)
                    fixed_cmd = re.sub(r':\s*"([^"]*)"(?=\s*")', r': "\1",', fixed_cmd)
                    # Try to parse it
                    json.loads(fixed_cmd)
                    valid_commands.append(fixed_cmd)
                except:
                    print(f"Could not fix command: {cmd[:30]}...")
            
            if valid_commands:
                json_str = "[" + ",".join(valid_commands) + "]"
                print(f"Constructed JSON array with {len(valid_commands)} valid commands")
    
    # Validate final JSON
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        print(f"Error: Final JSON is still invalid: {e}")
        # Return an empty array as fallback to prevent server crash
        return "[]"