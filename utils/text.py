"""
Text processing utilities, including JSON cleaning and validation.
"""

import re
import json

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
    
    # Replace single quotes with double quotes if needed
    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')

    json_str = json_str.strip()
    print(f"Cleaned JSON string: {json_str[:100]}...")
    
    # Validate JSON
    try:
        json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse: {e}")
        print(f"Full cleaned JSON: {json_str}")
        
    return json_str

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