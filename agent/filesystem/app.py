"""filesystem - Basic Gradio MCP Server

A simple MCP server with a single tool.
"""

import gradio as gr


def process_text(text: str) -> str:
    """Process the input text.
    
    Args:
        text: Input text to process
        
    Returns:
        Processed text result
    """
    # Your processing logic here
    return f"Processed: {text.upper()}"


# Create Gradio interface
demo = gr.Interface(
    fn=process_text,
    inputs=gr.Textbox(label="Input Text"),
    outputs=gr.Textbox(label="Result"),
    title="filesystem",
    description="A simple MCP server that processes text"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port=7866,
        mcp_server=True
    )
