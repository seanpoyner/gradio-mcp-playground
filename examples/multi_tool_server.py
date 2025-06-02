"""Multi-Tool Gradio MCP Server Example

This example shows how to create a Gradio MCP server with multiple tools
organized in tabs.
"""

import gradio as gr
import json
import base64
from datetime import datetime


def text_analyzer(text: str) -> str:
    """Analyze text and return statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        JSON string with text statistics
    """
    words = text.split()
    chars = len(text)
    lines = text.count('\n') + 1
    
    stats = {
        "character_count": chars,
        "word_count": len(words),
        "line_count": lines,
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "unique_words": len(set(words))
    }
    
    return json.dumps(stats, indent=2)


def json_formatter(json_text: str, indent: int = 2) -> str:
    """Format JSON text with proper indentation.
    
    Args:
        json_text: JSON string to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    try:
        parsed = json.loads(json_text)
        return json.dumps(parsed, indent=indent, sort_keys=True)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"


def base64_encoder(text: str, decode: bool = False) -> str:
    """Encode or decode Base64 text.
    
    Args:
        text: Text to encode/decode
        decode: If True, decode the text; otherwise encode
        
    Returns:
        Encoded or decoded text
    """
    try:
        if decode:
            decoded_bytes = base64.b64decode(text)
            return decoded_bytes.decode('utf-8')
        else:
            encoded_bytes = base64.b64encode(text.encode('utf-8'))
            return encoded_bytes.decode('utf-8')
    except Exception as e:
        return f"Error: {str(e)}"


def timestamp_converter(timestamp: str, format: str = "iso") -> str:
    """Convert timestamps between different formats.
    
    Args:
        timestamp: Timestamp string or 'now' for current time
        format: Output format (iso, unix, readable)
        
    Returns:
        Formatted timestamp
    """
    try:
        if timestamp.lower() == "now":
            dt = datetime.now()
        else:
            # Try to parse as Unix timestamp
            try:
                dt = datetime.fromtimestamp(float(timestamp))
            except:
                # Try to parse as ISO format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        if format == "iso":
            return dt.isoformat()
        elif format == "unix":
            return str(int(dt.timestamp()))
        elif format == "readable":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(dt)
            
    except Exception as e:
        return f"Error: {str(e)}"


# Create individual interfaces
text_interface = gr.Interface(
    fn=text_analyzer,
    inputs=gr.Textbox(label="Text to Analyze", lines=5),
    outputs=gr.Textbox(label="Analysis Results"),
    title="Text Analyzer",
    description="Analyze text and get statistics",
    examples=[
        ["Hello world! This is a test."],
        ["The quick brown fox jumps over the lazy dog.\nThis is a second line."]
    ]
)

json_interface = gr.Interface(
    fn=json_formatter,
    inputs=[
        gr.Textbox(label="JSON Text", lines=5),
        gr.Number(label="Indent Spaces", value=2, precision=0)
    ],
    outputs=gr.Textbox(label="Formatted JSON", lines=10),
    title="JSON Formatter",
    description="Format and validate JSON",
    examples=[
        ['{"name":"John","age":30,"city":"New York"}', 2],
        ['{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}', 4]
    ]
)

base64_interface = gr.Interface(
    fn=base64_encoder,
    inputs=[
        gr.Textbox(label="Input Text"),
        gr.Checkbox(label="Decode (unchecked = encode)")
    ],
    outputs=gr.Textbox(label="Output"),
    title="Base64 Encoder/Decoder",
    description="Encode or decode Base64 text",
    examples=[
        ["Hello, World!", False],
        ["SGVsbG8sIFdvcmxkIQ==", True]
    ]
)

timestamp_interface = gr.Interface(
    fn=timestamp_converter,
    inputs=[
        gr.Textbox(label="Timestamp (or 'now')", value="now"),
        gr.Dropdown(["iso", "unix", "readable"], label="Output Format", value="iso")
    ],
    outputs=gr.Textbox(label="Converted Timestamp"),
    title="Timestamp Converter",
    description="Convert between timestamp formats",
    examples=[
        ["now", "iso"],
        ["1703001600", "readable"],
        ["2023-12-19T12:00:00", "unix"]
    ]
)

# Combine all interfaces into a tabbed interface
demo = gr.TabbedInterface(
    [text_interface, json_interface, base64_interface, timestamp_interface],
    ["Text Analyzer", "JSON Formatter", "Base64", "Timestamps"],
    title="Multi-Tool MCP Server"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port=7860,
        mcp_server=True,
        server_name="0.0.0.0"
    )
