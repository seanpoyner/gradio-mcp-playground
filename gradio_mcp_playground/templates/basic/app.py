"""Basic Gradio MCP Server Template

A simple single-function MCP server.
"""

import gradio as gr


def process_text(text: str) -> str:
    """Process the input text.

    Args:
        text: Input text to process

    Returns:
        Processed text result
    """
    # Example: Convert to uppercase and add a greeting
    processed = f"Hello! You said: {text.upper()}"
    return processed


# Create Gradio interface
demo = gr.Interface(
    fn=process_text,
    inputs=gr.Textbox(label="Enter your text", placeholder="Type something here..."),
    outputs=gr.Textbox(label="Processed Result"),
    title="Basic Text Processor",
    description="A simple MCP server that processes text input",
    examples=[["Hello world"], ["Gradio MCP is awesome"], ["Testing the server"]],
)

# Launch as MCP server
if __name__ == "__main__":
    import os

    # Use port from environment variable or default to 7860
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
    # The mcp_server=True flag enables MCP protocol support
    demo.launch(
        server_port=port, mcp_server=True, server_name="0.0.0.0"  # Allow external connections
    )
