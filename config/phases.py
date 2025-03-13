"""
Refined configuration for painting phases with clearer progression.
Each phase represents a specific step in the AI painting process.
"""

PHASES = [
    {
        "name": "sketch",
        "display_name": "Sketch",
        "description": "Setting up the basic forms and layout",
        "parts": [
            {
                "focus": "Create the foundational elements and layout. Establish the main shapes and positions of key elements from the prompt.",
                "instruction": "Focus on creating simple shapes to establish the overall composition. Use basic forms to define the main elements from the prompt. Use shape tools and brush strokes to create outlines of the final scene"
            },
            {
                "focus": "Refine the composition by adjusting shapes, proportions, and placement. Do not redraw - enhance what's there. Avoid minor details, and just make sure the basic, platonic ideals of the prompt can be represented.",
                "instruction": "Look at the current composition and improve proportions and relationships between elements. Make adjustments to enhance rather than redraw."
            }
        ]
    },

    {
        "name": "detailing",
        "display_name": "Detailing",
        "description": "Adding definition, mid-tones and texture",
        "parts": [
            {
                "focus": "Take the basic shapes laid out previously, and fill in a few key small details. The goal is not  hyper-realism, but intentionality and character. You should express yourself and your personality with this.",
                "instruction": "Enhance the existing elements with details that better define them, and emphasize themes and meaning. Focus on adding features that you think communicate something, not every single little detail."
            },
            {
                "focus": "Add texture and surface details to create more visual interest. Focus on smaller elements that enhance realism.",
 "instruction": "Build on the existing shapes. Introduce mid-tone shading, subtle textures, or small highlights. Each added detail should serve a purpose—if it doesn’t convey mood, character, or thematic meaning, skip it. Retain the overall simplicity."            }
        ]
    },
    {
    "name": "color_blocking",
    "display_name": "Color Blocking",
    "description": "Introduce bold, flat colors to the major shapes. Establish the basic palette without intricate textures.",
    "parts": [
        {
        "focus": "Apply simple, flat colors to each main shape from the Sketch phase. Keep edges clean but do not refine shading or fine textures yet.",
        "instruction": "Select one or two main colors per shape. Fill areas uniformly to clarify the composition and distinguish elements. No highlights, shadows, or intricate blending—just flat color."
        }
    ]
    },
    {
        "name": "final_touches",
        "display_name": "Final Touches",
        "description": "Refining details and adding highlights",
        "parts": [
            {
                "focus": "Consider the piece as it exists now, accept it for what it is, and strive to adjust it minimally in key ways to evoke the feeling of a completed art piece.",
                "instruction": "Your drawings should be simple, rather than hoping for photo-realism, make the precise adjustments that contexutalize and enhance the artistic quality of the drawing."
            },
            {
                "focus": "Make final refinements to complete the simple artwork. Focus on small adjustments that harmonize the whole piece.",
                "instruction": "Make subtle final adjustments to complete the drawing. Focus on creating a cohesive, finished work without overwriting previous elements."
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