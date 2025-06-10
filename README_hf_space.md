---
title: Gradio MCP Playground
emoji: 🛝
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.31.0
app_file: app.py
pinned: true
license: apache-2.0
tags:
  - mcp
  - agents
  - gradio
  - hackathon
short_description: Open-source MCP tools without expensive LLM subscriptions!
---

# 🛝 Gradio MCP Playground

<div align="center">
  
  [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground)
  [![GitHub](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/seanpoyner/gradio-mcp-playground)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Hackathon](https://img.shields.io/badge/HF%20MCP%20Hackathon-2025-orange)](https://huggingface.co/hackathon)
  
  **Open-source access to MCP tools without expensive LLM subscriptions**
  
  [Try Demo](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground) | [Documentation](https://github.com/seanpoyner/gradio-mcp-playground) | [Report Bug](https://github.com/seanpoyner/gradio-mcp-playground/issues)

</div>

## 🎯 Our Mission

This project was created to solve a critical problem: **Most MCP tools require expensive LLM API subscriptions**, limiting access for developers, students, and enthusiasts. 

We believe everyone should be able to:
- **🎆 Experiment with MCP servers** without financial barriers
- **👩‍💻 Learn AI agent development** through hands-on experience  
- **🌈 Build and deploy tools** using Gradio's intuitive interface
- **🤝 Contribute to the open-source ecosystem** regardless of budget

## ✨ What is Gradio MCP Playground?

A comprehensive platform for building, managing, and deploying Model Context Protocol (MCP) servers using Gradio. This playground democratizes access to MCP technology, allowing developers and enthusiasts to "play" with MCP servers, agents, and LLM-tool integrations while showcasing the powerful features of Gradio.

### Key Benefits

- **💰 No API Keys Required** - Use the demo features without any LLM subscriptions
- **🚀 Zero to Agent in Minutes** - Create functional MCP servers quickly
- **🎨 Visual Development** - Build complex agents through an intuitive UI
- **📚 Learning Platform** - Understand MCP concepts through interactive examples
- **🌍 Community Driven** - Share and discover agents built by others

## 🏆 Features Overview

### 🛝 AI Assistant Hub
Three specialized AI assistants to guide your journey:

- **Adam (General Assistant)** - Your friendly companion with access to MCP tools like screenshots, web search, and file operations
- **Liam (MCP Specialist)** - Expert in MCP development, server creation, and pipeline building
- **Arthur (Agent Builder)** - Architect for sophisticated autonomous agents and custom implementations

### 🔧 Server Builder
Create MCP servers without extensive coding:

- **Quick Create** - Build servers from templates in seconds
- **Pipeline Builder** - Visual drag-and-drop interface for complex workflows
- **Templates Gallery** - Pre-built templates for common use cases:
  - Calculator (arithmetic operations)
  - Text Processor (text manipulation)
  - Image Generator (AI image creation)
  - Data Analyzer (CSV/data analysis)
  - Web Scraper (data extraction)
  - API Wrapper (turn any API into MCP)

### 🖥️ Server Management
Professional-grade server lifecycle management:

- **Active Servers** - Monitor running MCP servers in real-time
- **Server Registry** - Browse and install community servers
- **Quick Deploy** - One-click deployment to Hugging Face Spaces
- **Performance Monitoring** - Track server health and usage

### 🔌 MCP Connections
Connect to any MCP server with ease:

- **Quick Connect** - Pre-configured connections to popular servers:
  - Filesystem (file operations)
  - Memory (persistent storage)
  - GitHub (repository management)
  - Brave Search (web search)
- **Custom Connections** - Connect to any MCP server via stdio or SSE
- **Tool Discovery** - Automatically discover and test available tools
- **Activity Log** - Track all tool executions and results

### 🤖 Agent Control Panel
Build and manage autonomous agents:

- **Agent Creation** - Visual interface for building AI agents
- **Agent Templates** - Start from proven agent architectures
- **Testing Suite** - Real-time testing and debugging
- **Deployment Options** - Deploy agents to various platforms

### 📚 Help & Resources
Comprehensive documentation and support:

- **Interactive Tutorials** - Step-by-step guides
- **API Reference** - Complete documentation
- **Video Guides** - Visual learning resources
- **Community Forum** - Get help and share knowledge

## 🚀 Quick Start

### Try the Demo (This Space)

This Hugging Face Space provides a **demo version** showcasing all features. Some functionality is limited in the demo - for full features, install locally.

### Local Installation (Full Features)

```bash
# Clone the repository
git clone https://github.com/seanpoyner/gradio-mcp-playground
cd gradio-mcp-playground

# Install with all dependencies
pip install -e ".[all]"

# Launch the unified dashboard
gmp dashboard

# Or start on a custom port
gmp dashboard --port 8081
```

### CLI Tools

Powerful command-line tools for automation:

```bash
# Create servers from templates
gmp create calculator my-calc-server
gmp create image-generator my-image-server

# List available templates
gmp templates

# Manage servers
gmp server list              # List all servers
gmp server start my-server   # Start a server
gmp server stop my-server    # Stop a server

# Connect to MCP servers
gmp connect filesystem /path/to/directory
gmp connect github --token YOUR_GITHUB_TOKEN

# Deploy servers
gmp deploy my-server         # Deploy to Hugging Face Spaces
```

## 💡 Use Cases

### For Developers
- **Rapid Prototyping** - Test MCP concepts without setup overhead
- **Tool Development** - Create reusable tools for AI assistants
- **API Integration** - Wrap any API as an MCP server
- **Learning Platform** - Understand MCP through hands-on examples

### For Educators & Students
- **Free Learning** - No expensive API keys needed
- **Interactive Teaching** - Demonstrate AI concepts visually
- **Student Projects** - Build without infrastructure worries
- **Research Platform** - Experiment with MCP implementations

### For Enthusiasts
- **Explore MCP** - Play with cutting-edge AI technology
- **Build Tools** - Create useful automation tools
- **Share Creations** - Contribute to the community
- **Learn by Doing** - Hands-on experience with AI agents

### For Businesses
- **Proof of Concepts** - Test ideas before investing
- **Custom Assistants** - Build domain-specific agents
- **Team Collaboration** - Share tools internally
- **Cost-Effective Development** - Prototype without API costs

## 🛠️ Creating MCP Servers

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

## 📊 Architecture & Technology

### Core Technologies
- **Frontend**: Gradio 4.31.0 with custom themes and components
- **Backend**: Python with async support for high performance
- **Protocol**: Model Context Protocol (MCP) by Anthropic
- **Deployment**: Optimized for Hugging Face Spaces

### Key Components
- **Unified Dashboard** - Single interface for all MCP operations
- **MCP Client Manager** - Handles connections to multiple servers
- **Template Engine** - Generates server code from templates
- **Pipeline Builder** - Visual workflow creation
- **Agent Framework** - Autonomous agent construction

### Security & Performance
- **Secure Storage** - Encrypted credential management
- **Rate Limiting** - Prevent API abuse
- **Caching** - Optimized response times
- **Error Handling** - Graceful failure recovery

## 🤝 Project Team & Contributors

### Core Team
- **Sean Poyner** - Project Lead & Creator
- **Ranadeep Laskar ([@flickinshots](https://github.com/flickinshots))** - Project Member & Collaborator

We welcome contributions from the community! See our [Contributing Guide](CONTRIBUTING.md) for details.

## 📈 Roadmap

### Current Features (v1.0)
- ✅ Unified Dashboard
- ✅ CLI Tools
- ✅ Template Library
- ✅ Basic MCP Connections
- ✅ HF Space Deployment

### Coming Soon (v1.1)
- 🔄 Advanced Pipeline Builder
- 🔄 More Server Templates
- 🔄 Enhanced Agent Capabilities
- 🔄 Community Marketplace
- 🔄 Mobile-Responsive UI

### Future Vision (v2.0)
- 🔮 Multi-Agent Orchestration
- 🔮 Custom Model Integration
- 🔮 Enterprise Features
- 🔮 Advanced Analytics
- 🔮 Plugin System

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Special Thanks To
- **Hugging Face** - For hosting this space and organizing the MCP Hackathon
- **Gradio Team** - For the amazing framework that makes this possible
- **Anthropic** - For creating the Model Context Protocol
- **Open Source Community** - For inspiration and support

### Built With
- [Gradio](https://gradio.app) - The UI framework powering our interface
- [Model Context Protocol](https://github.com/anthropics/mcp) - The protocol enabling tool integration
- [Python](https://python.org) - Our primary development language

## 📞 Support & Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/seanpoyner/gradio-mcp-playground/issues)
- **Discussions**: [Join the conversation](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground/discussions)
- **Documentation**: [Full docs on GitHub](https://github.com/seanpoyner/gradio-mcp-playground)

---

<div align="center">
  <b>Made with ❤️ to democratize MCP technology for everyone</b>
  <br>
  <i>No expensive subscriptions required - just creativity and curiosity!</i>
</div>