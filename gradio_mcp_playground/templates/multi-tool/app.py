"""{{name}} - Multi-Tool MCP Server

An MCP server with multiple tools organized in tabs.
"""

import base64
import json
from datetime import datetime
from typing import Any, Dict

import gradio as gr


def text_analyzer(text: str) -> Dict[str, Any]:
    """Analyze text and return statistics.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with analysis results
    """
    words = text.split()
    chars = len(text)
    lines = text.count("\n") + 1

    # Simple sentiment placeholder
    positive_words = ["good", "great", "excellent", "happy", "wonderful"]
    negative_words = ["bad", "terrible", "awful", "sad", "horrible"]

    positive_count = sum(1 for word in words if word.lower() in positive_words)
    negative_count = sum(1 for word in words if word.lower() in negative_words)

    if positive_count > negative_count:
        sentiment = "Positive"
    elif negative_count > positive_count:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return {
        "character_count": chars,
        "word_count": len(words),
        "line_count": lines,
        "average_word_length": (
            round(sum(len(word) for word in words) / len(words), 2) if words else 0
        ),
        "sentiment": sentiment,
        "unique_words": len(set(words)),
    }


def json_formatter(json_text: str, indent: int = 2) -> str:
    """Format JSON text for better readability.

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
        return f"Error: Invalid JSON - {str(e)}"


def base64_encoder(text: str) -> str:
    """Encode text to base64.

    Args:
        text: Text to encode

    Returns:
        Base64 encoded string
    """
    encoded_bytes = base64.b64encode(text.encode("utf-8"))
    return encoded_bytes.decode("utf-8")


def base64_decoder(encoded: str) -> str:
    """Decode base64 text.

    Args:
        encoded: Base64 encoded string

    Returns:
        Decoded text
    """
    try:
        decoded_bytes = base64.b64decode(encoded)
        return decoded_bytes.decode("utf-8")
    except Exception as e:
        return f"Error: Invalid base64 - {str(e)}"


def timestamp_converter(timestamp: str, format_type: str = "ISO") -> str:
    """Convert between timestamp formats.

    Args:
        timestamp: Timestamp string or 'now' for current time
        format_type: Output format (ISO, Unix, Custom)

    Returns:
        Formatted timestamp
    """
    try:
        if timestamp.lower() == "now":
            dt = datetime.now()
        else:
            # Try to parse various formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            else:
                # Try parsing as Unix timestamp
                dt = datetime.fromtimestamp(float(timestamp))

        if format_type == "ISO":
            return dt.isoformat()
        elif format_type == "Unix":
            return str(int(dt.timestamp()))
        else:  # Custom
            return dt.strftime("%A, %B %d, %Y at %I:%M %p")

    except Exception as e:
        return f"Error: {str(e)}"


def list_processor(items: str, operation: str = "sort") -> str:
    """Process lists of items.

    Args:
        items: Items separated by newlines
        operation: Operation to perform (sort, reverse, unique, number)

    Returns:
        Processed list
    """
    lines = [line.strip() for line in items.strip().split("\n") if line.strip()]

    if operation == "sort":
        lines.sort()
    elif operation == "reverse":
        lines.reverse()
    elif operation == "unique":
        lines = list(dict.fromkeys(lines))  # Preserve order
    elif operation == "number":
        lines = [f"{i+1}. {line}" for i, line in enumerate(lines)]

    return "\n".join(lines)


# Create interfaces for each tool
text_analyzer_interface = gr.Interface(
    fn=text_analyzer,
    inputs=gr.Textbox(label="Text to Analyze", lines=5, placeholder="Enter text here..."),
    outputs=gr.JSON(label="Analysis Results"),
    title="Text Analyzer",
    description="Analyze text and get statistics",
    examples=[
        ["This is a great example of text analysis! It's wonderful and excellent."],
        ["The weather is neither good nor bad today."],
    ],
)

json_formatter_interface = gr.Interface(
    fn=json_formatter,
    inputs=[
        gr.Textbox(label="JSON Input", lines=5, placeholder='{"key": "value"}'),
        gr.Number(label="Indent Spaces", value=2, precision=0, minimum=0, maximum=8),
    ],
    outputs=gr.Textbox(label="Formatted JSON", lines=10),
    title="JSON Formatter",
    description="Format and validate JSON",
    examples=[
        ['{"name":"John","age":30,"city":"New York"}', 2],
        ['{"users":[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]}', 4],
    ],
)

base64_interface = gr.Interface(
    fn=[base64_encoder, base64_decoder],
    inputs=[
        gr.Textbox(label="Text to Encode", placeholder="Hello, World!"),
        gr.Textbox(label="Base64 to Decode", placeholder="SGVsbG8sIFdvcmxkIQ=="),
    ],
    outputs=[gr.Textbox(label="Encoded Base64"), gr.Textbox(label="Decoded Text")],
    title="Base64 Encoder/Decoder",
    description="Encode and decode base64 strings",
)

timestamp_interface = gr.Interface(
    fn=timestamp_converter,
    inputs=[
        gr.Textbox(label="Timestamp", placeholder="now or 2024-01-01 12:00:00"),
        gr.Radio(choices=["ISO", "Unix", "Custom"], label="Output Format", value="ISO"),
    ],
    outputs=gr.Textbox(label="Converted Timestamp"),
    title="Timestamp Converter",
    description="Convert between different timestamp formats",
    examples=[["now", "ISO"], ["2024-01-01 12:00:00", "Unix"], ["1704110400", "Custom"]],
)

list_processor_interface = gr.Interface(
    fn=list_processor,
    inputs=[
        gr.Textbox(label="Items (one per line)", lines=5, placeholder="apple\nbanana\ncherry"),
        gr.Radio(choices=["sort", "reverse", "unique", "number"], label="Operation", value="sort"),
    ],
    outputs=gr.Textbox(label="Processed List", lines=5),
    title="List Processor",
    description="Process lists of items",
    examples=[["zebra\napple\nbanana\napple", "sort"], ["first\nsecond\nthird", "number"]],
)

# Combine all interfaces
demo = gr.TabbedInterface(
    [
        text_analyzer_interface,
        json_formatter_interface,
        base64_interface,
        timestamp_interface,
        list_processor_interface,
    ],
    ["Text Analyzer", "JSON Formatter", "Base64", "Timestamp", "List Processor"],
    title="{{name}}",
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(server_port={{port}}, mcp_server=True)
