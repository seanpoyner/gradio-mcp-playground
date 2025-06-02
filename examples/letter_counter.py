"""Letter Counter - Example Gradio MCP Server

A simple example showing how to create a Gradio app that works as an MCP server.
"""

import gradio as gr


def count_letters(text: str, letter: str) -> int:
    """Count occurrences of a specific letter in text.
    
    Args:
        text: The text to search in
        letter: The letter to count
        
    Returns:
        Number of occurrences
    """
    return text.lower().count(letter.lower())


# Create the Gradio interface
demo = gr.Interface(
    fn=count_letters,
    inputs=[
        gr.Textbox(label="Text", placeholder="Enter some text..."),
        gr.Textbox(label="Letter", placeholder="Enter a letter to count...", max_lines=1)
    ],
    outputs=gr.Number(label="Count"),
    title="Letter Counter",
    description="Count how many times a letter appears in text",
    examples=[
        ["Hello, World!", "l"],
        ["Gradio is awesome", "a"],
        ["MCP servers are powerful", "e"]
    ]
)

# Launch as an MCP server
if __name__ == "__main__":
    # The mcp_server=True parameter makes this available as an MCP server
    demo.launch(mcp_server=True)
