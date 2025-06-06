# Getting Started with Gradio MCP Playground

Welcome to Gradio MCP Playground! This guide will help you get started with creating and managing Gradio applications as Model Context Protocol (MCP) servers.

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher (for some MCP features)
- Git

### Install from PyPI

```bash
pip install gradio-mcp-playground
```

### Install from Source

```bash
git clone https://github.com/seanpoyner/gradio-mcp-playground.git
cd gradio-mcp-playground
pip install -e .
```

## Quick Start

### 1. Run Setup

First, run the setup wizard to configure your environment:

```bash
gmp setup
```

This will:
- Check for required dependencies
- Create configuration files
- Set up your environment

### 2. Create Your First Server

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

Your server is now running at `http://localhost:7860` and is available as an MCP server!

### 4. Test with an MCP Client

You can test your server with any MCP-compatible client:

- **Claude Desktop**: Add the server to your Claude Desktop configuration
- **Cursor**: Use the MCP integration in Cursor
- **Cline**: Connect via the Cline interface

## Creating a Simple MCP Server

Here's a minimal example of a Gradio MCP server:

```python
import gradio as gr

def greet(name: str) -> str:
    """Greet someone by name.
    
    Args:
        name: The person's name
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}! Welcome to Gradio MCP."

# Create Gradio interface
demo = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="Name"),
    outputs=gr.Textbox(label="Greeting"),
    title="Greeting Service",
    description="A simple MCP server that greets people"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
```

## Basic Server Management

### Listing Servers

See all your registered servers:

```bash
gmp server list
```

### Server Information

Get detailed information about a server:

```bash
gmp server info hello-world
```

### Stopping Servers

Stop a running server:

```bash
gmp server stop hello-world
```

### Deleting Servers

Remove a server when you no longer need it:

```bash
# Remove from registry (keeps files)
gmp server delete hello-world

# Remove completely (including files)
gmp server delete hello-world --files
```

## Using the Dashboard

Launch the web dashboard to manage your servers visually:

```bash
gmp dashboard
```

The dashboard provides:
- Server management (create, start, stop, delete)
- Connection management
- Registry browsing
- Configuration editing

## Next Steps

- [Creating MCP Servers](creating-servers.md) - Learn how to build more complex servers
- [Client Integration](client-integration.md) - Connect your servers to MCP clients
- [Deployment Guide](deployment.md) - Deploy your servers to production
- [API Reference](api-reference.md) - Detailed API documentation

## Getting Help

- Open an issue on [GitHub](https://github.com/gradio-mcp-playground/gradio-mcp-playground/issues)
- Join our [Discord community](https://discord.gg/gradio-mcp)

## Examples

Explore the `examples/` directory for more complex examples:

- `weather_server.py` - Weather information service
- `calculator_server.py` - Mathematical operations
- `image_generator.py` - AI image generation
- `data_analyzer.py` - CSV data analysis

## Tips

1. **Use Type Hints**: Add type hints to your functions for better MCP integration
2. **Write Docstrings**: Good docstrings become tool descriptions in MCP
3. **Handle Errors**: Return helpful error messages for better user experience
4. **Test Locally**: Always test your server locally before deployment
5. **Use Templates**: Start with templates and customize them for your needs

Happy building with Gradio MCP Playground! 🚀
