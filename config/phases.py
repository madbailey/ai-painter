"""
Refined configuration for painting phases with clearer progression.
Each phase represents a specific step in the AI painting process.
"""

PHASES = [
    {
        "name": "sketch",
        "display_name": "Sketch",
        "description": "Initial rough sketch of the composition",
        "parts": [
            {
                "focus": "Create a simple line sketch of the main elements",
                "instruction": "Draw basic outlines and shapes using thin lines. Focus on placement and proportion."
            },
            {
                "focus": "Complete the sketch structure",
                "instruction": "Fill in missing elements and ensure the full canvas is utilized."
            }
        ]
    },
    {
        "name": "refine_lines",
        "display_name": "Refine Lines",
        "description": "Improving line work and structure",
        "parts": [
            {
                "focus": "Strengthen important lines and refine shapes",
                "instruction": "Use thicker lines for main elements. Clean up messy areas. Improve the structure."
            },
            {
                "focus": "Add secondary line details",
                "instruction": "Add structural details like facial features, textures, or pattern outlines."
            }
        ]
    },

    {
        "name": "color_blocking",
        "display_name": "Color Blocking",
        "description": "Adding base colors to defined areas",
        "parts": [
            {
                "focus": "Fill main areas with base colors",
                "instruction": "Add flat colors to the major areas. Start with background, then large objects."
            },
            {
                "focus": "Complete color coverage",
                "instruction": "Fill remaining areas and ensure good color contrast across the canvas."
            }
        ]
    },
    {
        "name": "detail",
        "display_name": "Detail",
        "description": "Adding final details and refinements",
        "parts": [
            {
                "focus": "Add shading, highlights and texture",
                "instruction": "Enhance with simple shading and highlights. Add small details to create interest."
            },
            {
                "focus": "Final refinements",
                "instruction": "Make any final adjustments to complete the artwork and balance the composition."
            }
        ]
    }
]

# AI model configuration
GENERATION_CONFIG = {
    "temperature": 0.7,  # Lower temperature for more consistent output
    "top_p": 0.6,
    "top_k": 40,
    "max_output_tokens": 4096,
}