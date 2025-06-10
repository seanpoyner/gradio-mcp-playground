# 🛝 Gradio MCP Playground

**Open-source access to MCP tools without expensive LLM subscriptions**

A comprehensive platform for building, managing, and deploying Model Context Protocol (MCP) servers using Gradio. This playground is designed to democratize access to MCP technology, allowing developers and enthusiasts to experiment with MCP servers, agents, and LLM-tool integrations while showcasing the powerful features of Gradio.

## 🌟 Overview

### Why Gradio MCP Playground?

This project was created to solve a critical problem: **Most MCP tools require expensive LLM API subscriptions**, limiting access for developers, students, and enthusiasts. Our mission is to:

- **🎆 Democratize MCP Technology** - Free, open-source access to MCP tools
- **👩‍💻 Enable Learning & Experimentation** - "Play" with MCP servers without financial barriers
- **🌈 Showcase Gradio's Power** - Demonstrate how Gradio simplifies complex AI interfaces
- **🤝 Build Community** - Foster collaboration in the MCP ecosystem

### Features

Gradio MCP Playground provides a complete ecosystem for working with MCP servers:

- **🛝 Unified Dashboard** - Web-based interface for complete MCP server lifecycle management
- **🛠️ CLI Tools** - Powerful command-line tools for server creation and management
- **🤖 AI Assistants** - Built-in AI agents for development assistance
- **📦 Template Library** - Pre-built templates for common use cases
- **🔌 MCP Connections** - Easy integration with existing MCP servers
- **🚀 One-Click Deployment** - Deploy to production environments instantly

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

### Launch the Dashboard

```bash
# Start the unified dashboard (recommended)
gmp dashboard

# Or start on a custom port
gmp dashboard --port 8081
```

The dashboard provides:
- **AI Assistant with 3 modes**: General assistant, MCP specialist (Liam), and Agent builder (Arthur)
- **Server Builder**: Create servers from templates with visual pipeline builder
- **Server Management**: Monitor, start, stop, and configure MCP servers
- **MCP Connections**: Connect to and manage multiple MCP servers
- **Help & Resources**: Built-in documentation and tutorials

## 📖 Dashboard Features

### 🛝 AI Assistant Tab

Three specialized AI assistants to help you:

1. **General Assistant (Adam)** - Conversational AI with access to all connected MCP tools
2. **MCP Agent (Liam)** - Specialized in MCP development, server creation, and troubleshooting
3. **Agent Builder (Arthur)** - Create custom Gradio agents using proven system prompts

### 🔧 Server Builder Tab

- **Quick Create**: Build servers from templates in seconds
- **Pipeline Builder**: Visual drag-and-drop interface for complex workflows
- **Templates Gallery**: Browse and use pre-built server templates
- **Custom Servers**: Create custom MCP servers with your own code

### 🖥️ Server Management Tab

- **Active Servers**: Monitor running MCP servers in real-time
- **Server Registry**: Browse and install servers from the community registry
- **Quick Install**: One-click installation of popular servers

### 🔌 MCP Connections Tab

- **Quick Connect**: Connect to popular servers like Filesystem, Memory, GitHub, and Brave Search
- **Active Connections**: Manage and monitor connected MCP servers
- **Custom Connections**: Connect to any MCP server via stdio or SSE

### 📚 Help & Resources Tab

- **User Guides**: Comprehensive documentation for all features
- **Quick Start**: Get up and running in minutes
- **Tutorials**: Step-by-step guides for common tasks
- **API Reference**: Complete API documentation

## 🛠️ CLI Tools

The Gradio MCP Playground includes powerful CLI tools for server management:

```bash
# Set up the playground
gmp setup

# Create servers from templates
gmp create calculator my-calc-server
gmp create image-generator my-image-server

# List available templates
gmp templates

# Manage servers
gmp server list              # List all servers
gmp server start my-server   # Start a server
gmp server stop my-server    # Stop a server
gmp server delete my-server  # Delete a server

# Connect to MCP servers
gmp connect filesystem /path/to/directory
gmp connect github --token YOUR_GITHUB_TOKEN

# Deploy servers
gmp deploy my-server         # Deploy to Hugging Face Spaces
```

## 📦 Available Templates

Create servers from these pre-built templates:

- **`basic`** - Simple single-tool server
- **`calculator`** - Mathematical operations server
- **`image-generator`** - AI image generation server
- **`data-analyzer`** - CSV/data analysis server
- **`file-processor`** - File manipulation server
- **`web-scraper`** - Web scraping and data extraction
- **`llm-tools`** - LLM-powered tools (summarization, translation, etc.)
- **`api-wrapper`** - Wrap any API as an MCP server
- **`multi-tool`** - Server with multiple tools in tabs

## 💡 Creating MCP Servers

### Basic Example

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

### Multi-Tool Server

```python
import gradio as gr

def summarize_text(text: str, max_length: int = 100) -> str:
    """Summarize a long text."""
    return text[:max_length] + "..."

def translate_text(text: str, target_language: str = "es") -> str:
    """Translate text to another language."""
    # Translation logic here
    return f"Translated: {text}"

# Create tabbed interface with multiple tools
demo = gr.TabbedInterface(
    [
        gr.Interface(fn=summarize_text, inputs=["text", "number"], outputs="text"),
        gr.Interface(fn=translate_text, inputs=["text", "text"], outputs="text")
    ],
    ["Summarizer", "Translator"]
)

# Launch as MCP server
demo.launch(mcp_server=True)
```

## 🤖 Agent Platform (agent/app.py)

The playground also includes a comprehensive agent demonstration platform:

```bash
# Navigate to the agent directory
cd agent

# Run the agent platform
python app.py
```

This demonstrates:
- **Agent Creation**: Visual interface for building AI agents
- **Agent Discovery**: Browse and install community agents
- **Agent Testing**: Real-time testing and debugging
- **Agent Monitoring**: Performance dashboards
- **Agent Deployment**: One-click cloud deployment

### Agent Use Cases

- **Content Creation Agents** - Image generation, text processing
- **Data Analysis Agents** - CSV analysis, visualization
- **Productivity Agents** - File processing, API integration
- **Development Agents** - Code analysis, testing
- **Communication Agents** - Translation, summarization
- **Custom Workflow Agents** - Multi-step automation

## 🚀 Deployment Options

### Hugging Face Spaces

```bash
# Deploy a server to Hugging Face Spaces
gmp deploy my-server --platform huggingface

# Or use the dashboard
# Go to Server Management → Deploy → Select server → Deploy to HF Spaces
```

### Local Development

```bash
# Run locally
python my_server.py

# Or use the CLI
gmp server start my-server
```

### Docker

```bash
# Build Docker image
docker build -t my-mcp-server .

# Run container
docker run -p 7860:7860 my-mcp-server
```

## 📊 Monitoring & Analytics

The dashboard provides real-time monitoring:

- **Server Status**: Health checks and uptime monitoring
- **Performance Metrics**: Response times and resource usage
- **Usage Analytics**: Tool call frequency and patterns
- **Error Tracking**: Error logs and debugging information

## 🔧 Configuration

Configure servers via `servers/config.json`:

```json
{
  "default_port": 7860,
  "auto_reload": true,
  "mcp_protocol": "stdio",
  "log_level": "INFO"
}
```

Or use environment variables:

```bash
export GMP_DEFAULT_PORT=8080
export GMP_AUTO_RELOAD=true
export HF_TOKEN=your_token_here
```

## 📚 Documentation

- [Getting Started Guide](docs/getting-started.md) - Quick start with the dashboard
- [User Guide](docs/user_guide.md) - Comprehensive guide to all features
- [Dashboard Architecture](docs/dashboard_architecture.md) - Technical details
- [Configuration Guide](docs/configuration.md) - Configure prompts and settings
- [MCP Server Types](docs/mcp_server_types.md) - Understanding server implementations
- [API Key Handling](docs/api_key_handling.md) - Secure API key management
- [Performance Optimization](docs/performance_optimization.md) - Speed up your dashboard

## 💻 Development

```bash
# Clone the repository
git clone https://github.com/yourusername/gradio-mcp-playground.git
cd gradio-mcp-playground

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Project Team & Acknowledgments

### Core Team
- **Sean Poyner** - Project Lead & Creator
- **Ranadeep Laskar ([@RanL703](https://github.com/RanL703))** - Project Member & Collaborator

### Special Thanks
- Built with [Gradio](https://gradio.app) by Hugging Face
- Implements the [Model Context Protocol](https://github.com/anthropics/mcp) by Anthropic
- Inspired by the open-source AI community

---

**Made with ❤️ by the Gradio MCP Playground team to bring MCP tools to everyone**
