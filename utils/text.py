"""
Simplified text processing utilities.
"""

import re
import json

def extract_thinking(text):
    """
    Extract content within <think></think> tags.
    
    Args:
        text (str): Text that may contain thinking tags
        
    Returns:
        str: The content within thinking tags, or empty string if none found
    """
    thinking = ""
    if '<think>' in text and '</think>' in text:
        pattern = r"<think>([\s\S]*?)</think>"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            thinking = matches[0].strip()
    return thinking

def clean_json_string(json_str):
    """
    Clean JSON string and remove thinking tags.
    
    Args:
        json_str (str): Raw JSON string that may contain markdown, 
                        thinking tags, or other formatting
                        
    Returns:
        str: Cleaned JSON string
    """
    # Look for JSON code blocks with ```json ... ``` pattern
    if '```json' in json_str and '```' in json_str:
        json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_matches = re.findall(json_block_pattern, json_str, re.DOTALL)
        if json_matches:
            json_str = json_matches[0].strip()
            print(f"Extracted JSON from code block: {json_str[:100]}...")
    
    # If no JSON code blocks found, remove thinking tags first
    elif '<think>' in json_str and '</think>' in json_str:
        thinking_pattern = r'<think>[\s\S]*?</think>'
        json_str = re.sub(thinking_pattern, "", json_str, flags=re.DOTALL)
        
        # Then try to find JSON array
        array_pattern = r'\[\s*{[\s\S]*}\s*\]'
        array_matches = re.findall(array_pattern, json_str, re.DOTALL)
        if array_matches:
            json_str = array_matches[0].strip()
            print(f"Extracted JSON array after removing thinking tags: {json_str[:100]}...")
    
    # If we still don't have valid JSON, try to clean up what we have
    if not json_str.strip().startswith('['):
        # Look for any JSON array anywhere in the string
        array_pattern = r'\[([\s\S]*?)\]'
        array_matches = re.findall(array_pattern, json_str, re.DOTALL)
        if array_matches:
            for match in array_matches:
                # Check if this match contains object definitions
                if '{' in match and '}' in match:
                    json_str = '[' + match + ']'
                    print(f"Found JSON array with brute force: {json_str[:100]}...")
                    break
    
    # Remove comments (// style)
    json_str = re.sub(r'//.*?($|\n|\r)', '', json_str)
    
    # Replace single quotes with double quotes if needed
    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    # Fix trailing commas before closing brackets (common LLM error)
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r',\s*}', '}', json_str)

    json_str = json_str.strip()
    print(f"Cleaned JSON string: {json_str[:100]}...")
    
    # Validate JSON
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse: {e}")
        print(f"Full cleaned JSON: {json_str}")
        
        # Advanced error correction
        try:
            # Check if array is missing opening or closing bracket
            if not json_str.startswith('['):
                json_str = '[' + json_str
            if not json_str.endswith(']'):
                json_str = json_str + ']'
                
            # Check for missing commas between objects
            json_str = re.sub(r'}\s*{', '},{', json_str)
            
            # Try again after bracket fixes
            json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Still couldn't parse JSON after fixes: {e}")
            
            # Last resort: extract valid objects individually
            try:
                pattern = r'{[^{}]*}'
                matches = re.findall(pattern, json_str)
                if matches:
                    valid_objects = []
                    for obj_str in matches:
                        try:
                            # Test if this object parses correctly
                            json.loads(obj_str)
                            valid_objects.append(obj_str)
                        except json.JSONDecodeError:
                            # Skip invalid objects
                            pass
                    
                    if valid_objects:
                        # Reconstruct a valid array
                        json_str = '[' + ','.join(valid_objects) + ']'
                        # Final test
                        json.loads(json_str)
                    else:
                        return "[]"
                else:
                    return "[]"
            except Exception:
                return "[]"
        
    return json_str
def summarize_command_history(command_history, max_commands=5):
    """
    Create a concise summary of command history for context preservation.
    
    Args:
        command_history (list): List of previous drawing commands
        max_commands (int): Maximum number of commands to include
        
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

def get_element_registry_summary():
    """
    Placeholder for compatibility - in the simplified version, we don't use the element registry.
    
    Returns:
        str: Empty string placeholder
    """
    return ""