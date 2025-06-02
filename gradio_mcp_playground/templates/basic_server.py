"""Letter Counter - Basic Gradio MCP Server Template

A simple MCP server that counts letters in text.
"""

import gradio as gr


def count_letters(text: str, letter: str) -> str:
    """Count occurrences of a letter in text.
    
    Args:
        text: The text to search in
        letter: The letter to count
        
    Returns:
        A message with the count
    """
    if not text:
        return "Please provide some text."
    
    if not letter or len(letter) != 1:
        return "Please provide a single letter to count."
    
    count = text.lower().count(letter.lower())
    
    return f"The letter '{letter}' appears {count} time(s) in the text."


# Create Gradio interface
demo = gr.Interface(
    fn=count_letters,
    inputs=[
        gr.Textbox(label="Text", placeholder="Enter some text..."),
        gr.Textbox(label="Letter", placeholder="Enter a letter to count", max_lines=1)
    ],
    outputs=gr.Textbox(label="Result"),
    title="Letter Counter",
    description="Count how many times a letter appears in text",
    examples=[
        ["Hello, World!", "l"],
        ["The quick brown fox jumps over the lazy dog", "o"],
        ["Gradio MCP Playground", "a"]
    ]
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
