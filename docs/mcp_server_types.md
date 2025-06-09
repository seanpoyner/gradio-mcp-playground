# MCP Server Types and Usage

This document explains the different types of MCP servers and how they can be used within the Gradio MCP Playground.

## Overview

There are two main categories of MCP servers in the Gradio MCP Playground:

1. **External MCP Servers** - Run as separate processes and communicate via stdio protocol
2. **Integrated Tools** - Built directly into the coding agent for use within the chat

## External MCP Servers

These servers run as external processes and are designed for use with MCP clients like Claude Desktop. They **cannot** be accessed directly from within the Gradio chat interface.

### Examples:
- **Obsidian** - Manages Obsidian vault notes
- **Filesystem** (via registry) - File system access
- **GitHub** - GitHub API access
- **Time** - Timezone utilities
- **SQLite/Postgres** - Database access

### How to Use External Servers:

1. **Installation**: Use `install_mcp_server_from_registry()` to start the server
2. **External Access**: Configure your MCP client (e.g., Claude Desktop) with the provided command
3. **Cannot use in chat**: These servers are not accessible from the Gradio chat interface

### Workarounds for Chat Access:

For Obsidian vaults:
```python
# List vault contents
list_home_directory(subdirectory='vault-name')

# Read a specific note
read_project_file('vault-name/Daily Notes/2024-01-01.md')
```

For filesystem access:
```python
# Use built-in file tools
list_home_directory()
read_project_file('path/to/file.txt')
```

## Integrated Tools

These tools are built directly into the coding agent and can be used within the chat interface.

### Available Integrated Tools:

1. **Brave Search** (`brave_search`)
   - Web search functionality
   - Requires API key on first use
   - Works both in chat and as external MCP server

2. **Memory Server** (`memory_*`)
   - `memory_store_conversation()` - Store conversations
   - `memory_retrieve_conversation()` - Retrieve conversations
   - `memory_search_conversations()` - Search conversations
   - Works both in chat and as external MCP server

3. **File Tools** (always available)
   - `list_home_directory()` - List directory contents
   - `read_project_file()` - Read file contents
   - `create_directory()` - Create directories

4. **MCP Management Tools**
   - `search_mcp_registry()` - Find MCP servers
   - `check_server_requirements()` - Check installation requirements
   - `install_mcp_server_from_registry()` - Install servers
   - `stop_mcp_registry_server()` - Stop running servers

## Understanding the Distinction

### Why Some Servers are External Only

MCP servers installed from the registry (npm packages) run as separate Node.js processes and communicate using the stdio protocol. This design:

1. **Isolation**: Keeps server code separate from the Python environment
2. **Compatibility**: Works with any MCP client that supports stdio
3. **Security**: Servers run with limited permissions
4. **Standardization**: Follows the MCP specification

### When to Use Each Type

**Use External MCP Servers when:**
- You need the functionality in Claude Desktop or other MCP clients
- You want to run the server continuously in the background
- You need the full feature set of the MCP server

**Use Integrated Tools when:**
- You need immediate access within the Gradio chat
- You want to prototype or test functionality
- You need to combine multiple tools in a workflow

## Example Scenarios

### Scenario 1: Accessing Obsidian Vault

```
User: What's in my Obsidian vault?

❌ Wrong approach:
Agent: [Tries to use Obsidian MCP server from chat - fails]

✅ Correct approach:
Agent: I'll help you explore your Obsidian vault. Since the Obsidian MCP server runs externally, I'll use the file tools to access your vault.
[Uses: list_home_directory(subdirectory='seans-vault')]
```

### Scenario 2: Web Search

```
User: Search the web for Python tutorials

✅ Works in chat:
Agent: I'll search for Python tutorials using Brave Search.
[Uses: brave_search(query='Python tutorials')]
```

### Scenario 3: Setting Up for Claude Desktop

```
User: I want to use Obsidian in Claude Desktop

✅ Correct approach:
Agent: I'll install the Obsidian MCP server for you.
[Uses: install_mcp_server_from_registry(server_id='obsidian', vault_path1='/path/to/vault')]
[Provides configuration for Claude Desktop]
```

## Technical Details

### External MCP Server Architecture

```
Gradio App (Python)
    ↓
Spawns Process
    ↓
MCP Server (Node.js)
    ↓
stdio communication
    ↓
External MCP Client (Claude Desktop)
```

### Integrated Tools Architecture

```
Gradio App (Python)
    ↓
Coding Agent
    ↓
Direct Function Calls
    ↓
Immediate Response
```

## Future Improvements

1. **MCP Client Integration**: Add a built-in MCP client to the coding agent that can communicate with external servers
2. **Proxy Tools**: Create proxy tools that bridge between the chat and external servers
3. **Unified Interface**: Develop a unified interface that abstracts the difference between external and integrated tools