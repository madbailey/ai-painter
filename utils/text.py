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
    # First remove any <think></think> tags and their content
    if '<think>' in json_str and '</think>' in json_str:
        pattern = r"<think>[\s\S]*?</think>"
        json_str = re.sub(pattern, "", json_str, flags=re.DOTALL)
    
    # Clean code blocks
    if '```' in json_str:
        pattern = r"```(?:json)?([\s\S]*?)```"
        matches = re.findall(pattern, json_str, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
            json_str = json_str.replace("```json", "").replace("```", "").strip()
    
    # Remove comments (// style) - CRITICAL FIX
    json_str = re.sub(r'//.*?($|\n|\r)', '', json_str)
    
    # Replace single quotes with double quotes if needed
    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    # Replace JavaScript booleans with JSON booleans if needed
    json_str = json_str.replace("true", "true").replace("false", "false")
    
    # Fix common true/false issues
    json_str = re.sub(r':\s*true\s*([,}])', r':true\1', json_str)
    json_str = re.sub(r':\s*false\s*([,}])', r':false\1', json_str)
    
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