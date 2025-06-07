# Using Gradio MCP Playground as an MCP Server

You can run the Gradio MCP Playground itself as an MCP server, allowing you to manage your MCP servers directly from Claude Desktop or other MCP clients.

## Setup

### 1. Install Dependencies

```bash
pip install mcp
```

### 2. Configure Claude Desktop

Add this to your Claude Desktop configuration file (`~/.config/claude/claude_desktop_config.json` on macOS/Linux or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "gradio-mcp-playground": {
      "command": "python",
      "args": [
        "-m",
        "gradio_mcp_playground.cli",
        "mcp"
      ],
      "env": {}
    }
  }
}
```

### 3. Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the new MCP server.

## Available Tools

Once configured, you'll have access to these tools through Claude:

### Server Management
- **`list_servers`** - List all MCP servers (Claude Desktop and local)
- **`get_server_info`** - Get detailed information about a specific server
- **`get_server_logs`** - Get logs for troubleshooting servers

### Local Server Control
- **`start_local_server`** - Start a local Gradio MCP server
- **`stop_local_server`** - Stop a local Gradio MCP server
- **`create_server`** - Create a new server from a template
- **`delete_local_server`** - Delete a local server

### Templates and Registry
- **`list_templates`** - List available server templates
- **`search_registry`** - Search for server templates

## Example Usage

Once the MCP server is running, you can ask Claude:

```
"List all my MCP servers"
"Show me the logs for the filesystem server"
"Create a new server called 'my-tool' using the basic template"
"Get detailed information about the github server"
"Start my local server called 'test-server'"
```

## Features

### Real-time Server Status
- Shows actual status of Claude Desktop managed servers
- Displays error information from log files
- Tracks last activity timestamps

### Smart Server Management
- Distinguishes between Claude Desktop and local servers
- Only allows control of local servers (Claude Desktop servers are read-only)
- Prevents accidental deletion of Claude Desktop servers

### Log Integration
- Access to actual Claude Desktop server logs
- Error detection and reporting
- Recent activity monitoring

### Template System
- Pre-built templates for common use cases
- Easy server creation from templates
- Customizable server configurations

## Troubleshooting

### Server Not Appearing in Claude
1. Check that the configuration is valid JSON
2. Verify the python path is correct
3. Ensure `gradio_mcp_playground` is installed
4. Restart Claude Desktop

### Permission Issues
- Make sure the python environment has access to MCP packages
- Check that the working directory is accessible

### Log Access Issues
- Verify Claude Desktop log directory permissions
- Check that the user account matches between WSL and Windows (if applicable)

## Alternative Invocation

You can also run the MCP server directly:

```bash
# Direct invocation
python -m gradio_mcp_playground.cli mcp

# Or using the installed CLI
gmp mcp
```

This is useful for testing or integration with other MCP clients.