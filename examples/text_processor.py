"""Simple Text Processor - Example Gradio MCP Server

This example shows how to create a basic text processing tool.
"""

import gradio as gr


def process_text(text: str, operation: str) -> str:
    """Process text with various operations.
    
    Args:
        text: Input text to process
        operation: Operation to perform (uppercase, lowercase, reverse, count_words)
        
    Returns:
        Processed text result
    """
    if operation == "uppercase":
        return text.upper()
    elif operation == "lowercase":
        return text.lower()
    elif operation == "reverse":
        return text[::-1]
    elif operation == "count_words":
        word_count = len(text.split())
        char_count = len(text)
        return f"Words: {word_count}, Characters: {char_count}"
    else:
        return "Unknown operation"


# Create Gradio interface
demo = gr.Interface(
    fn=process_text,
    inputs=[
        gr.Textbox(label="Input Text", lines=3),
        gr.Radio(
            choices=["uppercase", "lowercase", "reverse", "count_words"],
            label="Operation",
            value="uppercase"
        )
    ],
    outputs=gr.Textbox(label="Result", lines=3),
    title="Text Processor",
    description="Process text with various operations"
)

if __name__ == "__main__":
    demo.launch(mcp_server=True)
