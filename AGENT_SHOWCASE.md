# 🛝 Gradio MCP Playground - Agent Showcase

**Open-source MCP tools without expensive LLM subscriptions**

## 🌟 Overview

The Gradio MCP Playground is a comprehensive platform that democratizes access to Model Context Protocol (MCP) technology. Our mission is to enable developers, students, and enthusiasts to build, manage, and deploy AI agents and MCP servers without financial barriers.

## 🎯 Key Features

### 1. 🛝 Unified Dashboard
A single, intuitive web interface for complete MCP server lifecycle management:
- **AI Assistant Tab**: Three specialized AI modes
- **Server Builder**: Visual pipeline creation
- **Server Management**: Real-time monitoring
- **MCP Connections**: Easy integration with existing servers
- **Help & Resources**: Built-in documentation

### 2. 🤖 Three AI Assistant Modes

#### General Assistant (Adam)
- Conversational AI with access to all connected MCP tools
- Screenshot capture, web search, file operations
- General-purpose help for any task

#### MCP Agent (Liam)
- Specialized in MCP development
- Pipeline creation and troubleshooting
- Server optimization and best practices

#### Agent Builder (Arthur)
- Create custom Gradio agents
- Uses proven system prompts from top AI assistants
- Advanced autonomous agent development

### 3. 🔧 Visual Pipeline Builder
- Drag-and-drop interface for complex workflows
- Connect multiple MCP servers
- Configure data flow between components
- Test pipelines in real-time
- Export pipeline configurations

### 4. 🖥️ Agent Control Panel
The control panel (`agent/ui/control_panel.py`) provides:
- **Live Agent Dashboard**: Real-time status monitoring
- **Quick Actions**: Deploy, stop, and manage agents
- **Code Editor**: Built-in Python editor with validation
- **Agent Health Monitor**: Track performance metrics

### 5. 📦 Pre-built Agent Templates

#### Twitter Blog Agent
- Monitors blog directories for new posts
- AI-powered Twitter thread generation
- Automated posting with proper reply chains
- Rate limiting and error handling

#### Web Scraper Pro
- Multi-format content extraction
- Custom CSS selector support
- Batch processing capabilities
- Export to CSV, JSON, Excel

#### Data Processor Pro
- Advanced data analysis and transformation
- CSV/Excel processing
- Data visualization
- Statistical analysis

## 🚀 Getting Started

### Installation
```bash
# Install the package
pip install gradio-mcp-playground

# Or install with all extras
pip install "gradio-mcp-playground[all]"

# Launch the unified dashboard
gmp dashboard
```

### Quick Agent Creation
```bash
# Create from templates
gmp create calculator my-calc-server
gmp create image-generator my-image-server

# List available templates
gmp templates

# Deploy to production
gmp deploy my-server
```

## 💡 Example Use Cases

### 1. Content Creation Pipeline
Connect these agents in sequence:
- **Web Scraper** → Gather research material
- **Data Processor** → Analyze and summarize
- **Twitter Agent** → Create and post threads

### 2. Data Analysis Workflow
- **File Monitor** → Watch for new CSV files
- **Data Processor** → Clean and analyze data
- **Report Generator** → Create visualizations
- **Email Sender** → Distribute reports

### 3. AI-Powered Automation
- **Screenshot Tool** → Capture web pages
- **Image Analyzer** → Extract information
- **LLM Processor** → Generate insights
- **Database Writer** → Store results

## 🏗️ Technical Architecture

### Core Components
```
gradio-mcp-playground/
├── gradio_mcp_playground/     # Main package
│   ├── unified_web_ui.py      # Unified dashboard
│   ├── coding_agent.py        # AI assistant implementation
│   └── mcp_connection_manager.py
├── agent/                     # Agent system
│   ├── app.py                # Agent platform
│   ├── core/                 # Core logic
│   │   ├── agent.py
│   │   ├── agent_builder.py
│   │   └── agent_runner.py
│   ├── ui/                   # UI components
│   │   ├── control_panel.py
│   │   ├── pipeline_view.py
│   │   └── chat_interface.py
│   └── agents/              # Agent templates
│       ├── twitter_blog_agent.py
│       ├── web_scraper_pro.py
│       └── data_processor_pro.py
```

### Key Technologies
- **Frontend**: Gradio 4.31+ with custom components
- **Protocol**: Model Context Protocol (MCP) by Anthropic
- **AI Models**: Support for Hugging Face models (Qwen, Mixtral, Zephyr)
- **Storage**: Secure credential management with AES-256 encryption
- **Deployment**: Optimized for local, cloud, and Hugging Face Spaces

## 🔒 Security Features
- Encrypted API key storage
- Secure credential management
- Sandboxed agent execution
- Rate limiting and error handling
- Input validation and sanitization

## 📊 Performance Highlights
- **Fast Agent Deployment**: < 5 seconds from template to running server
- **Low Resource Usage**: Optimized for running multiple agents
- **Scalable Architecture**: Handle 100+ concurrent connections
- **Real-time Monitoring**: Sub-second status updates

## 🌍 Community & Ecosystem
- **Open Source**: MIT licensed, community-driven development
- **No API Keys Required**: Use without expensive subscriptions
- **Template Library**: Growing collection of pre-built agents
- **Active Development**: Regular updates and new features

## 🚀 Deployment Options

### Local Development
```bash
python agent/app.py --dev
```

### Production Deployment
```bash
# Docker
docker build -t gmp-agent .
docker run -p 8080:8080 gmp-agent

# Hugging Face Spaces
gmp deploy --platform huggingface
```

## 📈 Future Roadmap
- [ ] Advanced multi-agent orchestration
- [ ] Custom model integration (local LLMs)
- [ ] Visual debugging tools
- [ ] Agent marketplace
- [ ] Enterprise features

## 🤝 Contributing
We welcome contributions! The project is designed to be extensible:
- Create new agent templates
- Add MCP server implementations
- Improve documentation
- Report bugs and suggest features

## 📚 Resources
- **GitHub**: [github.com/seanpoyner/gradio-mcp-playground](https://github.com/seanpoyner/gradio-mcp-playground)
- **Documentation**: Comprehensive guides in `/docs`
- **Examples**: Working examples in `/examples`
- **Support**: GitHub Issues and Discussions

---

**Made with ❤️ to democratize AI agent technology for everyone**

No expensive subscriptions required - just creativity and curiosity!