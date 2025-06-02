# Gradio MCP Playground

A comprehensive toolkit for building, managing, and deploying Gradio applications as Model Context Protocol (MCP) servers. Create AI-powered tools that can be used by Claude Desktop, Cursor, Cline, and other MCP-compatible clients.

## 🌟 Features

- **🚀 Quick Server Creation** - Transform any Gradio app into an MCP server with one line of code
- **📦 Template Library** - Pre-built templates for common MCP use cases
- **🔍 Server Discovery** - Browse and search available Gradio MCP servers
- **🛠️ Dual Interface** - Both CLI and web UI for managing your MCP servers
- **☁️ Easy Deployment** - One-command deployment to Hugging Face Spaces
- **🔄 Protocol Support** - Full support for both STDIO and SSE communication
- **🧪 Testing Tools** - Built-in tools for testing and debugging MCP connections
- **📊 Monitoring Dashboard** - Real-time monitoring of server status and connections

## 🚀 Quick Start

### Installation

```bash
pip install gradio-mcp-playground
```

Or install with all extras:

```bash
pip install "gradio-mcp-playground[all]"
```

### Create Your First MCP Server

```python
import gradio as gr

def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

# Create a Gradio interface
demo = gr.Interface(fn=greet, inputs="text", outputs="text")

# Launch as an MCP server
demo.launch(mcp_server=True)
```

That's it! Your Gradio app is now an MCP server that can be used by any MCP client.

### Using the CLI

```bash
# Set up the playground
gmp setup

# Create a new MCP server from a template
gmp server create --template calculator

# List all running servers
gmp server list

# Start the web dashboard
gmp dashboard

# Deploy to Hugging Face Spaces
gmp deploy my-mcp-server
```

## 💡 Usage Examples

### 1. Image Generation Server

```python
import gradio as gr
from diffusers import StableDiffusionPipeline

def generate_image(prompt: str) -> str:
    """Generate an image from a text prompt.
    
    Args:
        prompt: Text description of the image to generate
        
    Returns:
        Path to the generated image
    """
    # Your image generation logic here
    return "path/to/image.png"

demo = gr.Interface(
    fn=generate_image,
    inputs=gr.Textbox(label="Prompt"),
    outputs=gr.Image(label="Generated Image"),
    title="AI Image Generator"
)

demo.launch(mcp_server=True)
```

### 2. Data Analysis Server

```python
import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt

def analyze_csv(file_path: str, column: str) -> tuple:
    """Analyze a CSV file and create visualizations.
    
    Args:
        file_path: Path to the CSV file
        column: Column name to analyze
        
    Returns:
        Summary statistics and a plot
    """
    df = pd.read_csv(file_path)
    stats = df[column].describe().to_string()
    
    plt.figure(figsize=(10, 6))
    df[column].hist()
    plt.title(f"Distribution of {column}")
    plt.savefig("plot.png")
    
    return stats, "plot.png"

demo = gr.Interface(
    fn=analyze_csv,
    inputs=[
        gr.File(label="CSV File"),
        gr.Textbox(label="Column to Analyze")
    ],
    outputs=[
        gr.Textbox(label="Statistics"),
        gr.Image(label="Distribution Plot")
    ],
    title="CSV Data Analyzer"
)

demo.launch(mcp_server=True)
```

## 🛠️ Advanced Features

### Custom MCP Server Configuration

```python
import gradio as gr
from gradio_mcp_playground import MCPServer

# Create a custom MCP server with multiple tools
mcp_server = MCPServer(
    name="multi-tool-server",
    version="1.0.0",
    description="A server with multiple AI tools"
)

@mcp_server.tool()
def summarize_text(text: str, max_length: int = 100) -> str:
    """Summarize a long text."""
    return text[:max_length] + "..."

@mcp_server.tool()
def translate_text(text: str, target_language: str = "es") -> str:
    """Translate text to another language."""
    # Translation logic here
    return f"Translated: {text}"

# Create Gradio interface
demo = gr.TabbedInterface(
    [
        gr.Interface(fn=summarize_text, inputs=["text", "number"], outputs="text"),
        gr.Interface(fn=translate_text, inputs=["text", "text"], outputs="text")
    ],
    ["Summarizer", "Translator"]
)

# Launch with custom MCP server
demo.launch(mcp_server=mcp_server)
```

### Client Connections

```python
from gradio_mcp_playground import MCPClient

# Connect to a Gradio MCP server
client = MCPClient()
await client.connect("http://localhost:7860/mcp")

# List available tools
tools = await client.list_tools()
print(f"Available tools: {tools}")

# Call a tool
result = await client.call_tool(
    "greet",
    {"name": "World"}
)
print(result)
```

## 📦 Available Templates

The playground comes with several pre-built templates:

- **`basic`** - Simple single-tool server
- **`calculator`** - Mathematical operations server
- **`image-generator`** - AI image generation server
- **`data-analyzer`** - CSV/data analysis server
- **`file-processor`** - File manipulation server
- **`web-scraper`** - Web scraping and data extraction
- **`llm-tools`** - LLM-powered tools (summarization, translation, etc.)
- **`api-wrapper`** - Wrap any API as an MCP server

Create a server from a template:

```bash
gmp server create my-calculator --template calculator
```

## 🌐 Web Dashboard

The Gradio MCP Playground includes a web-based dashboard for visual management:

```bash
gmp dashboard
```

Features:
- Real-time server status monitoring
- Visual server creation wizard
- Tool testing interface
- Configuration editor
- Connection logs viewer
- One-click deployment

## 🚀 Deployment

### Deploy to Hugging Face Spaces

```bash
# Configure your Hugging Face token
gmp config set hf_token YOUR_TOKEN

# Deploy your server
gmp deploy my-server --public
```

### Docker Deployment

```bash
# Build Docker image
gmp docker build my-server

# Run container
gmp docker run my-server -p 7860:7860
```

## 🔧 Configuration

Configure the playground using the CLI or by editing `~/.gradio-mcp/config.json`:

```json
{
  "default_port": 7860,
  "auto_reload": true,
  "hf_token": "YOUR_HF_TOKEN",
  "mcp_protocol": "stdio",
  "log_level": "INFO"
}
```

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Creating MCP Servers](docs/creating-servers.md)
- [Client Integration](docs/client-integration.md)
- [Deployment Guide](docs/deployment.md)
- [API Reference](docs/api-reference.md)
- [Troubleshooting](docs/troubleshooting.md)

## 💻 Development

```bash
# Clone the repository
git clone https://github.com/yourusername/gradio-mcp-playground.git
cd gradio-mcp-playground

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Start development server
gmp dev
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Gradio](https://gradio.app/) - The amazing ML app framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that makes this possible
- [Anthropic](https://anthropic.com/) - For creating MCP and Claude
- The open-source community for inspiration and contributions

## 🔗 Links

- [PyPI Package](https://pypi.org/project/gradio-mcp-playground/)
- [GitHub Repository](https://github.com/yourusername/gradio-mcp-playground)
- [Documentation](https://gradio-mcp-playground.readthedocs.io/)
- [Discord Community](https://discord.gg/gradio-mcp)

---

**Made with ❤️ for the Gradio and MCP communities**
