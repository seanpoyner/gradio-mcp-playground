# Gradio MCP Playground

**Tags**: agent-demo-track

A comprehensive AI agent management platform built with Gradio that showcases powerful applications of AI agents. Build, manage, deploy, and monitor AI-powered tools and services through an intuitive web interface.

## 🎥 Video Overview

**[Watch the Platform Demo →](https://example.com/demo-video)**

See how to build, test, and deploy AI agents in under 5 minutes using our comprehensive platform. This video demonstrates the complete agent lifecycle from creation to production deployment.

## 🤖 Agentic Demo Features

This Gradio app demonstrates a complete AI agent ecosystem with:

- **🤖 Agent Builder** - Visual interface for creating AI agents from templates
- **🔍 Agent Discovery** - Browse, search, and install community-built agents  
- **🧪 Agent Testing** - Real-time testing and debugging of agent functionality
- **📊 Agent Monitoring** - Live dashboard showing agent performance and usage
- **🚀 Agent Deployment** - One-click deployment to multiple cloud platforms
- **🛠️ Agent Management** - Complete lifecycle management of AI agents
- **📦 Template Library** - Pre-built agent templates for common use cases
- **☁️ Cloud Integration** - Native integration with Hugging Face Spaces and other platforms

## 🌟 Agent Use Cases Demonstrated

- **Content Creation Agents** - Image generation, text processing, creative writing
- **Data Analysis Agents** - CSV analysis, visualization, statistical reporting  
- **Productivity Agents** - File processing, API integration, workflow automation
- **Development Agents** - Code analysis, testing, deployment automation
- **Communication Agents** - Translation, summarization, multi-language chat
- **Custom Workflow Agents** - Multi-step automated business processes

## 🚀 Quick Start

### Installation

```bash
pip install gradio-mcp-playground
```

Or install with all extras:

```bash
pip install "gradio-mcp-playground[all]"
```

**🔧 Troubleshooting Installation:**

If you see "mcp (optional) missing - some features will be limited":

```bash
# Install MCP dependency specifically
pip install mcp>=1.0.0

# Or install everything at once
pip install -e .

# Check what's missing
python check_dependencies.py
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

# Start the unified dashboard (default)
gmp dashboard

# Or explicitly start unified dashboard
gmp dashboard --unified

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

## 🌐 Unified Web Dashboard

The Gradio MCP Playground features a comprehensive unified dashboard that combines server management with AI agent capabilities:

```bash
# Start the unified dashboard (default)
gmp dashboard

# Or start on a custom port
gmp dashboard --port 8081
```

### Dashboard Features:

**🤖 AI Assistant (Three Modes)**
- **Assistant Mode**: General conversational assistant with full MCP tool access
- **MCP Agent Mode**: Specialized agent (Liam) for MCP development and troubleshooting
- **Agent Builder Mode**: Create custom Gradio agents using system prompts from top AI assistants

**🔧 Server Management**
- Real-time server status monitoring
- Visual server creation wizard
- Pipeline builder for complex workflows
- Template gallery with pre-built servers

**🔌 MCP Connections**
- Quick connect to popular servers
- Active connection management
- Custom server connections

**🧪 Tool Testing**
- Interactive tool testing interface
- Real-time results
- JSON input/output support

**📊 Monitoring & Deployment**
- Performance metrics
- One-click deployment
- Agent monitoring dashboard

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

- [Getting Started Guide](docs/getting-started.md) - Quick start with the unified dashboard
- [User Guide](docs/user_guide.md) - Comprehensive guide to all features
- [Configuration Guide](docs/configuration.md) - Configure prompts, models, and settings
- [MCP Server Types](docs/mcp_server_types.md) - Understanding different server implementations
- [API Key Handling](docs/api_key_handling.md) - Secure API key management
- [Unified Dashboard Guide](UNIFIED_DASHBOARD.md) - Complete guide to the unified interface

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

## 🔧 Troubleshooting

### Common Issues

**"mcp (optional) missing - some features will be limited"**

This means the MCP package is not installed. Install it with:

```bash
pip install mcp>=1.0.0
```

**"ModuleNotFoundError: No module named 'gradio_mcp_playground'"**

The package isn't installed in development mode. Install with:

```bash
pip install -e .
```

**CLI commands not working**

Make sure you've installed the package properly:

```bash
# Check what's missing
python check_dependencies.py

# Install all dependencies
pip install -e .

# Test CLI
gmp --help
```

**Windows installation issues**

Use these commands on Windows:

```cmd
pip install --user -e .
pip install --user mcp>=1.0.0 gradio>=4.44.0
```

### Getting Help

- 🧪 Run automated tests: `python run_all_tests.py`
- 📋 Check QA/QC checklist: `QA_QC_CHECKLIST.md`
- 🔍 Test imports: `python test_imports.py`
- 📊 Check dependencies: `python check_dependencies.py`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Gradio](https://gradio.app/) - The amazing ML app framework
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that makes this possible
- [Anthropic](https://anthropic.com/) - For creating MCP and Claude
- The open-source community for inspiration and contributions

## 🎬 Agentic Demo Showcase

**Track**: agent-demo-track

This Space demonstrates a comprehensive AI agent management platform showcasing:

### 📽️ Video Demonstration
**[Watch the Complete Platform Demo →](https://example.com/demo-video)**

The video walkthrough shows:
- Creating custom AI agents from templates
- Real-time agent testing and debugging  
- Deploying agents to production environments
- Monitoring agent performance and usage
- Managing the complete agent lifecycle

### 🏆 Demo Highlights

1. **Visual Agent Builder** - Build AI agents without code using templates
2. **Agent Marketplace** - Discover and install community agents
3. **Real-time Testing** - Test agents directly in the browser
4. **Performance Monitoring** - Live dashboards showing agent metrics
5. **One-click Deployment** - Deploy to Hugging Face Spaces, AWS, and more
6. **Complete Ecosystem** - End-to-end agent development platform

## 🔗 Links

- [🎥 Platform Demo Video](https://example.com/demo-video)
- [📦 PyPI Package](https://pypi.org/project/gradio-mcp-playground/)
- [💻 GitHub Repository](https://github.com/yourusername/gradio-mcp-playground)
- [📚 Documentation](https://gradio-mcp-playground.readthedocs.io/)
- [💬 Discord Community](https://discord.gg/gradio-mcp)

---

**Made with ❤️ for the AI agent community | Track: agent-demo-track**
