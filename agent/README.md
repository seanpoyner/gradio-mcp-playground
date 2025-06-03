# GMP Agent - Intelligent MCP Server Builder

GMP Agent is an intelligent coding assistant and GUI application that helps users build, configure, and deploy MCP (Model Context Protocol) servers using the Gradio MCP Playground toolkit. The agent provides a conversational interface for creating sophisticated MCP server pipelines in plain language.

## 🚀 Features

- **Natural Language Interface**: Describe what you want to build in plain language
- **Smart Server Discovery**: Automatically finds and suggests relevant MCP servers from local registry and public sources
- **Pipeline Builder**: Creates complex MCP server workflows using the `gmp` toolkit
- **Expert Knowledge**: Deep understanding of Gradio, MCP protocol, and the GMP application
- **Interactive GUI**: User-friendly Gradio interface for building and managing MCP servers
- **Code Generation**: Generates complete MCP server implementations with proper configuration
- **Real-time Assistance**: Provides ongoing support and troubleshooting during development

## 🎯 Use Cases

### For Developers
- **Rapid Prototyping**: Quickly build MCP servers from natural language descriptions
- **Tool Integration**: Connect multiple MCP servers into powerful workflows
- **Code Enhancement**: Get expert suggestions for improving existing MCP implementations
- **Debugging Support**: Troubleshoot MCP server issues with intelligent assistance

### For Non-Developers
- **No-Code Solutions**: Build functional MCP servers without writing code
- **Template Customization**: Modify existing templates through conversation
- **Automated Deployment**: Handle complex setup and configuration automatically

## 🏗️ Architecture

```
agent/
├── app.py                 # Main Gradio application
├── core/
│   ├── agent.py          # Core agent logic and conversation handling
│   ├── server_builder.py # MCP server pipeline construction
│   ├── registry.py       # Enhanced server discovery and registry
│   └── knowledge.py      # Expert knowledge base for Gradio/MCP
├── ui/
│   ├── chat_interface.py # Chat UI components
│   ├── pipeline_view.py  # Visual pipeline builder
│   └── server_manager.py # Server management interface
├── examples/
│   ├── conversations/    # Example conversation flows
│   └── pipelines/       # Example MCP server pipelines
├── docs/
│   ├── user_guide.md    # Comprehensive user guide
│   └── api_reference.md # API documentation
└── tests/
    ├── test_agent.py    # Agent logic tests
    └── test_builders.py # Builder functionality tests
```

## 🚦 Quick Start

### Installation

```bash
# Navigate to the agent directory
cd agent

# Install dependencies
pip install -r requirements.txt

# Launch the agent
python app.py
```

### First Conversation

1. **Start the Agent**: Run `python app.py` to launch the Gradio interface
2. **Describe Your Goal**: Tell the agent what you want to build:
   - "I need an image processing pipeline that can resize and filter images"
   - "Create a data analysis server that can process CSV files and generate charts"
   - "Build a text summarization tool using local LLMs"
3. **Review Suggestions**: The agent will suggest relevant servers and configurations
4. **Build Pipeline**: Approve the suggested approach and let the agent build your server
5. **Test & Deploy**: Use the built-in testing and deployment tools

## 💬 Example Conversations

### Building a Simple Tool
```
User: I need a calculator that can handle basic math operations

Agent: I'll help you create a calculator MCP server. Based on your needs, I recommend:

1. Using the "calculator" template from the registry
2. Adding support for basic operations (+, -, *, /)
3. Including advanced functions (sin, cos, sqrt)

Would you like me to:
- Create a basic calculator server
- Add a custom UI with multiple operation modes
- Include equation solving capabilities?

User: Yes, create a basic one first

Agent: Perfect! I'm creating a calculator MCP server with:
- Basic arithmetic operations
- Mathematical functions
- Error handling
- Clean Gradio interface

[Building server...]
✅ Calculator server created at ./my-calculator/
🚀 Starting server on port 7860...
```

### Complex Pipeline Creation
```
User: I want to build a content creation pipeline that takes a topic, researches it, writes an article, and generates images

Agent: That's a sophisticated content pipeline! I'll break this down into components:

1. **Research Module**: Web scraping + summarization
2. **Writing Module**: LLM-powered article generation  
3. **Image Module**: AI image generation based on content
4. **Assembly Module**: Combine everything into final output

I found these relevant servers in the registry:
- web-scraper (for research)
- llm-tools (for writing)
- image-generator (for visuals)

Would you like me to create a unified pipeline or separate servers that work together?

User: Create a unified pipeline

Agent: Building your content creation pipeline...
[Detailed progress updates as components are built and integrated]
```

## 🔧 Advanced Features

### Server Discovery
- **Local Registry**: Searches installed gmp templates and user-created servers
- **Public Registry**: Discovers community MCP servers from GitHub and other sources
- **Smart Matching**: Uses semantic search to find relevant servers for your use case
- **Dependency Resolution**: Automatically handles server dependencies and requirements

### Pipeline Building
- **Visual Editor**: Drag-and-drop interface for connecting MCP servers
- **Configuration Management**: Handles complex server configurations automatically
- **Testing Framework**: Built-in testing for individual servers and complete pipelines
- **Deployment Tools**: One-click deployment to various platforms

### Expert Knowledge
- **Gradio Expertise**: Deep knowledge of Gradio components and best practices
- **MCP Protocol**: Complete understanding of MCP server implementation
- **GMP Toolkit**: Expert-level knowledge of all gmp commands and features
- **Best Practices**: Coding standards and optimization recommendations

## 🛠️ Development

### Running in Development Mode

```bash
# Enable auto-reload and debug mode
python app.py --dev

# Run with specific configuration
python app.py --config dev-config.json

# Enable verbose logging
python app.py --log-level debug
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Test specific functionality
python -m pytest tests/test_agent.py -v

# Run integration tests
python -m pytest tests/integration/ -v
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📖 Documentation

- **[User Guide](docs/user_guide.md)**: Complete guide for using the agent
- **[API Reference](docs/api_reference.md)**: Technical documentation for developers
- **[Examples](examples/)**: Sample conversations and pipeline configurations

## 🤝 Integration with GMP

The agent seamlessly integrates with the parent GMP project:

- **Shared Registry**: Uses the same server registry as the main gmp CLI
- **Template System**: Leverages existing gmp templates and can create new ones
- **Configuration**: Inherits gmp configuration and can modify server settings
- **Deployment**: Can deploy servers using gmp deployment infrastructure

## 🚀 Future Roadmap

- **Multi-Modal Support**: Handle images, audio, and video in conversations
- **Collaborative Features**: Multiple users working on the same pipeline
- **Version Control**: Git integration for server and pipeline versioning
- **Marketplace**: Community marketplace for sharing MCP servers and pipelines
- **Cloud Integration**: Native support for cloud deployment platforms

## 📝 License

This project inherits the license from the parent Gradio MCP Playground project.

## 🆘 Support

- **GitHub Issues**: Report bugs and request features
- **Discord**: Join our community for real-time support
- **Documentation**: Check the docs/ directory for detailed guides

---

Built with ❤️ using Gradio and the Model Context Protocol