"""Basic Gradio MCP Server Template

A simple example of a Gradio app that works as an MCP server.
"""

import gradio as gr


def process_text(text: str, operation: str = "uppercase") -> str:
    """Process text with various operations.
    
    Args:
        text: The input text to process
        operation: The operation to perform (uppercase, lowercase, reverse, length)
        
    Returns:
        The processed text result
    """
    if operation == "uppercase":
        return text.upper()
    elif operation == "lowercase":
        return text.lower()
    elif operation == "reverse":
        return text[::-1]
    elif operation == "length":
        return f"Text length: {len(text)} characters"
    else:
        return f"Unknown operation: {operation}"


# Create Gradio interface
demo = gr.Interface(
    fn=process_text,
    inputs=[
        gr.Textbox(label="Input Text", placeholder="Enter text to process..."),
        gr.Radio(
            choices=["uppercase", "lowercase", "reverse", "length"],
            label="Operation",
            value="uppercase"
        )
    ],
    outputs=gr.Textbox(label="Result"),
    title="Text Processor",
    description="A simple MCP server that processes text with various operations",
    examples=[
        ["Hello World!", "uppercase"],
        ["GRADIO MCP", "lowercase"],
        ["Gradio", "reverse"],
        ["Count my characters", "length"]
    ]
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
