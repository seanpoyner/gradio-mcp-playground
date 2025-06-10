# Gradio MCP Playground Dashboard Architecture

This document describes the architecture and features of the Gradio MCP Playground Dashboard, which combines the original MCP Playground with an advanced Agent Builder system.

## Features

### 🤖 AI Assistant (Three Modes)
- **Assistant Mode**: General conversational assistant with full access to all connected MCP tools
  - Can perform any task using available MCP servers
  - Natural language interface to MCP capabilities
  - Shows thinking process when using tools
  
- **MCP Agent Mode**: Liam - specialized for MCP development
  - Research and find MCP servers
  - Build custom MCP servers
  - Test server functionality  
  - Install servers from registry
  - Connect and configure servers
  - MCP best practices and troubleshooting
  
- **Agent Builder Mode**: Create custom Gradio agents
  - Uses system prompts from top AI assistants (Claude, GPT, etc.)
  - Generate complete agent implementations
  - Template-based agent creation
  
- Seamless mode switching for different workflows
- Shared model configuration across all modes

### 🔧 Server Builder (Combined)
- **Quick Create**: Simple server creation from templates
- **Pipeline Builder**: Visual workflow builder for complex server connections
- **Templates Gallery**: Browse and use pre-built templates

### 🖥️ Server Management (Unified)
- **Active Servers**: Monitor and control running servers
- **Registry Browser**: Search and install from MCP server registry
- Single source of truth for all server states

### 🔌 MCP Connections (Merged)
- **Quick Connect**: One-click connections to popular servers
- **Active Connections**: Manage all connected MCP servers
- **Custom Connections**: Connect to any MCP server

### 🧪 Tool Testing
- Interactive tool testing interface
- Real-time results
- JSON input/output support

### 📚 Help & Resources
- **Documentation**: Comprehensive guides
- **Examples**: Real-world use cases
- **Agent Monitor**: Control panel for deployed agents

### ⚙️ Settings
- Configure default ports, protocols, and logging
- Manage API tokens securely

## Installation

```bash
# Install with all dependencies including agent components
pip install -e ".[all]"

# Or install agent components separately
cd agent
pip install -r requirements.txt
cd ..
```

## Usage

### Launch the Dashboard

```bash
# Default command now launches the unified dashboard
gmp dashboard

# Or with custom port
gmp dashboard --port 8081

# Create public share link
gmp dashboard --public

# Use legacy dashboard if needed
gmp dashboard --legacy
```

### Running Directly

```python
from gradio_mcp_playground.unified_web_ui import launch_unified_dashboard

# Launch on default port 8080
launch_unified_dashboard()

# Or with custom settings
launch_unified_dashboard(port=8081, share=True)
```

### Example Use Cases by Mode

#### Assistant Mode (General Tasks)
```
User: "Take a screenshot of python.org and save it to my desktop"
User: "Search for the latest news about AI developments"
User: "Create a markdown file with a summary of my project"
User: "What files are in my Documents folder?"
```

#### MCP Agent Mode (MCP Development)
```
User: "How do I create an MCP server for image processing?"
User: "Find all available database-related MCP servers"
User: "Help me troubleshoot why my MCP server isn't connecting"
User: "What's the best practice for handling errors in MCP tools?"
```

#### Agent Builder Mode (Custom Agents)
```
User: "Create a data science agent using Claude's system prompt"
User: "Show me available system prompts"
User: "Build a creative writing agent with GPT's personality"
User: "Generate an agent for customer support"
```

## Key Features

1. **Three Assistant Modes**: 
   - General Assistant with MCP tools for any task
   - MCP Agent (Liam) specialized for MCP development
   - Agent Builder for creating custom Gradio agents
2. **Agent Builder Integration**: Full agent creation system with advanced capabilities
3. **Pipeline Builder**: Visual workflow creation for complex server connections
4. **Agent Control Panel**: Deploy and manage agents with integrated monitoring
5. **Unified State Management**: Single registry and connection manager
6. **Enhanced UI**: Consistent styling and improved layout
7. **Comprehensive Help System**: Organized documentation and tutorials

## Architecture

The unified dashboard:
- Imports components from both `gradio_mcp_playground` and `agent` directories
- Shares state managers (ServerRegistry, MCPConnectionManager)
- Uses conditional imports to gracefully handle missing components
- Maintains backward compatibility with the original dashboard

## Development

### Adding New Features

1. Import the component in `unified_web_ui.py`
2. Add conditional loading with try/except
3. Create the UI tab or section
4. Wire up event handlers
5. Test with and without agent components

### Testing

```bash
# Test unified dashboard creation
python -c "from gradio_mcp_playground.unified_web_ui import create_unified_dashboard; create_unified_dashboard()"

# Run with debug logging
gmp dashboard --unified --log-level debug
```

## Troubleshooting

### Agent components not loading
- Ensure the agent directory is in the Python path
- Check that agent dependencies are installed: `pip install -e ".[all]"`
- Look for import errors in the console

### Pipeline Builder errors
- The PipelineView requires a GMPAgent instance
- Check that the agent initialized correctly
- Verify Hugging Face token if using AI features

### Dashboard not starting
- Check if another process is using the port: `lsof -i :8080` (Unix) or `netstat -ano | findstr :8080` (Windows)
- Try a different port: `gmp dashboard --port 8081`
- Use debug logging: `gmp dashboard --log-level DEBUG`

### Fallback behavior
- If components fail to load, the dashboard provides graceful degradation
- The legacy dashboard can be accessed with: `gmp dashboard --legacy`
- Check console output for specific error messages

## Future Enhancements

1. **Deeper Integration**: Merge duplicate functionality between coding agent and GMP agent
2. **Unified Tool System**: Single tool registry for both systems
3. **Shared Knowledge Base**: Combine knowledge from both agents
4. **Enhanced Pipeline Builder**: Add more visual components
5. **Real-time Collaboration**: Multi-user support for team development