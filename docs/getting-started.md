# Getting Started with Gradio MCP Playground

Welcome to Gradio MCP Playground! This guide will help you get up and running quickly.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Basic knowledge of Python and Gradio

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install gradio-mcp-playground
```

### Option 2: Install from Source

```bash
git clone https://github.com/gradio-mcp-playground/gradio-mcp-playground.git
cd gradio-mcp-playground
pip install -e .
```

## Quick Start

### 1. Run Setup

After installation, run the setup wizard:

```bash
gmp setup
```

This will:
- Check your environment
- Create configuration files
- Set up default preferences

### 2. Create Your First MCP Server

Create a simple MCP server using a template:

```bash
gmp server create hello-world --template basic
```

This creates a new directory called `hello-world` with a basic Gradio MCP server.

### 3. Start the Server

Navigate to the server directory and start it:

```bash
cd hello-world
gmp server start hello-world
```

Your server will start on the default port (7860) and be accessible at `http://localhost:7860`.

### 4. Test the MCP Connection

In a new terminal, connect to your server as an MCP client:

```bash
gmp client connect http://localhost:7860
```

## Understanding MCP Servers

### What is MCP?

Model Context Protocol (MCP) is a standardized protocol for communication between AI models and tools. It allows:

- Standardized tool discovery
- Type-safe function calling
- Support for multiple transport layers (STDIO, SSE)
- Integration with various AI assistants

### Gradio + MCP

Gradio MCP Playground makes it easy to:

1. **Create MCP Servers**: Any Gradio app can become an MCP server
2. **Expose Tools**: Functions in your Gradio app become callable tools
3. **Test Locally**: Debug and test your MCP servers before deployment
4. **Deploy Easily**: One-command deployment to Hugging Face Spaces

## Creating a Custom MCP Server

Here's a simple example of a custom MCP server:

```python
import gradio as gr

def translate_text(text: str, target_language: str) -> str:
    """Translate text to another language.
    
    Args:
        text: Text to translate
        target_language: Target language code (e.g., 'es', 'fr', 'de')
        
    Returns:
        Translated text
    """
    # Your translation logic here
    # This is a placeholder - integrate with a real translation service
    translations = {
        "es": "Hola Mundo",
        "fr": "Bonjour le Monde",
        "de": "Hallo Welt"
    }
    
    if text.lower() == "hello world" and target_language in translations:
        return translations[target_language]
    
    return f"Translation of '{text}' to {target_language}"

# Create Gradio interface
demo = gr.Interface(
    fn=translate_text,
    inputs=[
        gr.Textbox(label="Text to Translate"),
        gr.Textbox(label="Target Language", placeholder="es, fr, de, etc.")
    ],
    outputs=gr.Textbox(label="Translation"),
    title="Translation Tool",
    description="Translate text between languages"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
```

## Using the Web Dashboard

Start the web dashboard for visual management:

```bash
gmp dashboard
```

The dashboard provides:
- Server management (start/stop/delete)
- Connection testing
- Registry browsing
- Configuration editing
- Deployment tools

## Connecting from AI Assistants

### Claude Desktop

1. Add your server to Claude Desktop's configuration:

```json
{
  "mcpServers": {
    "my-gradio-server": {
      "command": "python",
      "args": ["/path/to/your/server/app.py"],
      "env": {}
    }
  }
}
```

2. Restart Claude Desktop
3. Your tools will be available in Claude

### Cursor

Similar to Claude Desktop, add your server configuration to Cursor's MCP settings.

### Using the Gradio Client

For programmatic access:

```python
from gradio_mcp_playground import GradioMCPClient

# Connect to server
client = GradioMCPClient()
client.connect("http://localhost:7860")

# List available tools
tools = client.list_tools()
print(tools)

# Call a tool
result = client.call_tool("translate_text", {
    "text": "Hello World",
    "target_language": "es"
})
print(result)
```

## Deployment

### Deploy to Hugging Face Spaces

1. Configure your Hugging Face token:

```bash
gmp setup  # Enter your HF token when prompted
```

2. Deploy your server:

```bash
gmp deploy my-server --public
```

Your server will be deployed to Hugging Face Spaces and accessible via a public URL.

## Common Patterns

### Multi-Tool Server

Create a server with multiple tools:

```python
import gradio as gr

def tool1(input1: str) -> str:
    return f"Tool 1: {input1}"

def tool2(input2: str) -> str:
    return f"Tool 2: {input2}"

# Create interfaces
interface1 = gr.Interface(fn=tool1, inputs="text", outputs="text")
interface2 = gr.Interface(fn=tool2, inputs="text", outputs="text")

# Combine with tabs
demo = gr.TabbedInterface(
    [interface1, interface2],
    ["Tool 1", "Tool 2"]
)

demo.launch(mcp_server=True)
```

### Custom Components

Use Gradio's custom components:

```python
import gradio as gr

def process_image(image, threshold: float = 0.5):
    """Process an image with a threshold.
    
    Args:
        image: Input image
        threshold: Processing threshold (0-1)
        
    Returns:
        Processed image
    """
    # Your image processing logic
    return image

demo = gr.Interface(
    fn=process_image,
    inputs=[
        gr.Image(type="pil"),
        gr.Slider(0, 1, value=0.5, label="Threshold")
    ],
    outputs=gr.Image(type="pil"),
    title="Image Processor"
)

demo.launch(mcp_server=True)
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Use a different port with `--port` flag
2. **Import errors**: Ensure all dependencies are installed
3. **MCP not working**: Check that `mcp_server=True` is set in launch()

### Debug Mode

Enable debug logging:

```bash
export GRADIO_LOG_LEVEL=DEBUG
gmp server start my-server
```

## Next Steps

- Explore the [templates](templates.md) for more examples
- Read about [advanced features](advanced.md)
- Learn about [deployment options](deployment.md)
- Join our [Discord community](https://discord.gg/gradio-mcp)

## Getting Help

- Check the [documentation](https://gradio-mcp-playground.readthedocs.io)
- Browse [GitHub issues](https://github.com/gradio-mcp-playground/gradio-mcp-playground/issues)
- Ask in the [community forum](https://discuss.gradio.app)
