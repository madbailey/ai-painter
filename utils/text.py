"""
Text processing utilities, including JSON cleaning and validation.
"""

import re
import json

def clean_json_string(json_str):
    """
    Clean JSON string and remove thinking tags with enhanced error handling.
    
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