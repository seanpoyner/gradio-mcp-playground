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
short_description: Build AI agents visually - No code required!
---

# 🛝 Gradio MCP Playground

<div align="center">
  
  [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground)
  [![GitHub](https://img.shields.io/badge/GitHub-Repository-black)](https://github.com/seanpoyner/gradio-mcp-playground)
  [![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
  [![Hackathon](https://img.shields.io/badge/HF%20MCP%20Hackathon-2025-orange)](https://huggingface.co/hackathon)
  
  **Transform any Python function into an AI agent in seconds!**
  
  [Try Demo](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground) | [Documentation](https://github.com/seanpoyner/gradio-mcp-playground/wiki) | [Report Bug](https://github.com/seanpoyner/gradio-mcp-playground/issues)

</div>

## 🏆 Hugging Face MCP Hackathon Submission

This project democratizes AI agent development by providing a visual, no-code platform for creating, testing, and deploying MCP (Model Context Protocol) agents. Built with Gradio, it makes agent creation accessible to everyone - from beginners to experts.

## ✨ What Makes This Special?

- **🚀 Zero to Agent in 30 Seconds** - Choose a template, customize, and deploy
- **🎨 Visual Builder** - No coding required with our drag-and-drop interface
- **🤖 AI-Powered Assistance** - Three specialized AI modes to guide you
- **🔌 Live MCP Integration** - Connect and test real MCP servers instantly
- **📦 One-Click Deploy** - Deploy to production with a single button

## 🎥 Demo Video

[Watch our 2-minute demo](https://youtu.be/demo-link) to see the playground in action!

## 🌟 Key Features

### 🛝 AI Assistant Hub
Three specialized AI assistants help you at every step:

- **Adam (General)** - Your friendly AI companion with MCP superpowers
- **Liam (MCP Agent)** - Expert in MCP development and troubleshooting  
- **Arthur (Agent Builder)** - Architect for complex agent systems

### 🏗️ Visual Server Builder
Create MCP servers without writing code:

- **Template Gallery** - Pre-built templates for common use cases
- **Live Code Generation** - See your Python code as you build
- **Instant Testing** - Test your tools without deployment
- **Custom Templates** - Start from scratch or modify existing ones

### 🔌 MCP Connections
Connect to any MCP server with ease:

- **Quick Connect** - One-click connection to popular servers
- **Tool Discovery** - Automatically discover available tools
- **Live Testing** - Execute tools and see results in real-time
- **Activity Monitoring** - Track all tool executions

### 📦 Server Management
Professional-grade server management:

- **Dashboard View** - Monitor all your servers at a glance
- **One-Click Deploy** - Deploy to Hugging Face Spaces instantly
- **Version Control** - Track changes and rollback if needed
- **Share & Collaborate** - Share your agents with the community

## 🚀 Quick Start

### Try the Demo (No Installation)

Visit our [Hugging Face Space](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground) to try the platform instantly!

### Local Installation (Full Features)

```bash
# Clone repository
git clone https://github.com/seanpoyner/gradio-mcp-playground
cd gradio-mcp-playground

# Install dependencies  
pip install -e ".[all]"

# Run the unified dashboard
gmp dashboard

# Or run with custom port
gmp dashboard --port 8081
```

## 💡 Use Cases

### For Developers
- **Rapid Prototyping** - Test ideas without boilerplate code
- **API Integration** - Wrap any API as an MCP server
- **Tool Development** - Create reusable tools for AI assistants

### For Businesses
- **Custom Assistants** - Build domain-specific AI agents
- **Workflow Automation** - Create multi-step processes
- **Team Collaboration** - Share tools across your organization

### For Educators
- **Teaching AI Concepts** - Visual way to explain agent architectures
- **Student Projects** - Let students build without infrastructure worries
- **Interactive Demos** - Show real AI capabilities in action

### For Researchers
- **Protocol Testing** - Experiment with MCP implementations
- **Tool Benchmarking** - Compare different approaches
- **Rapid Experimentation** - Test hypotheses quickly

## 📸 Screenshots

<div align="center">
  <img src="https://github.com/seanpoyner/gradio-mcp-playground/assets/demo/assistant.png" width="45%" alt="AI Assistant">
  <img src="https://github.com/seanpoyner/gradio-mcp-playground/assets/demo/builder.png" width="45%" alt="Server Builder">
</div>

## 🛠️ Technical Implementation

### Architecture
- **Frontend**: Gradio 4.31.0 with custom themes
- **Backend**: Python with async support
- **Protocol**: Model Context Protocol (MCP) 
- **Deployment**: Hugging Face Spaces compatible

### Key Technologies
- **Gradio** - Interactive web UI framework
- **MCP** - Standardized protocol for AI tools
- **AsyncIO** - High-performance async operations
- **Pydantic** - Data validation and serialization

## 🎯 Why This Matters

The Model Context Protocol (MCP) is powerful but can be complex to implement. Our playground removes these barriers:

1. **Accessibility** - No need to understand protocol details
2. **Speed** - Build in minutes instead of hours
3. **Learning** - See how MCP works through examples
4. **Community** - Share and discover agents easily

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- **Hugging Face** - For hosting and the MCP Hackathon
- **Gradio Team** - For the amazing framework
- **Anthropic** - For the Model Context Protocol
- **Community** - For feedback and contributions

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/seanpoyner/gradio-mcp-playground/issues)
- **Discussions**: [Join the conversation](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground/discussions)
- **Twitter**: [@seanpoyner](https://twitter.com/seanpoyner)

---

<div align="center">
  <b>Made with ❤️ for the Hugging Face MCP Hackathon 2025</b>
  <br>
  <i>Empowering everyone to build AI agents</i>
</div>