"""
Configuration for painting phases.
Each phase represents a step in the AI painting process.
"""

PHASES = [
    {
        "name": "composition",
        "display_name": "Composition",
        "description": "Setting up the basic forms and layout",
        "parts": [
            {
                "focus": "Create the foundational elements and layout. Establish the main shapes and compositional structure.",
                "instruction": "Focus on creating the overall composition and basic shapes. Establish the main elements and their arrangement."
            },
            {
                "focus": "Review and refine the composition. Adjust proportions and placement as needed.",
                "instruction": "Look at the current composition and identify what's working and what needs adjustment. Use modification commands to improve balance and structure."
            }
        ]
    },
    {
        "name": "color_blocking",
        "display_name": "Color Blocking",
        "description": "Establishing main color areas and base tones",
        "parts": [
            {
                "focus": "Add primary colors and establish the main color areas.",
                "instruction": "Create a foundation of base tones and broad color zones. Focus on larger brush strokes to define major color regions."
            },
            {
                "focus": "Refine colors and improve color harmony. Adjust color areas that don't work well.",
                "instruction": "Evaluate the current color scheme. Use modification commands to adjust colors that clash or areas that need better definition."
            }
        ]
    },
    {
        "name": "detailing",
        "display_name": "Detailing",
        "description": "Adding definition, mid-tones and texture",
        "parts": [
            {
                "focus": "Add details, shadows, and mid-tones to the existing elements.",
                "instruction": "Use smaller brushes for refinement. Define edges more clearly and add secondary elements."
            },
            {
                "focus": "Enhance specific details and add definition where needed.",
                "instruction": "Identify areas that lack detail or definition. Use targeted commands to enhance only those specific areas."
            }
        ]
    },
    {
        "name": "final_touches",
        "display_name": "Final Touches",
        "description": "Refining details and adding highlights",
        "parts": [
            {
                "focus": "Add final highlights, texture details, and refinements.",
                "instruction": "Focus on smaller, precise strokes to enhance realism and polish. Emphasize focal points."
            },
            {
                "focus": "Make final adjustments and corrections to complete the artwork.",
                "instruction": "Do a final review of the entire piece. Address any remaining issues or inconsistencies with targeted modifications."
            }
        ]
    }
]

# AI model configuration
GENERATION_CONFIG = {
    "temperature": 0.4,  # Lower temperature for more deterministic output
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 4096,
}