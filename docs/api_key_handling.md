# API Key Handling in Gradio MCP Playground

This document describes the improved API key handling in the Gradio MCP Playground chat interface.

## Overview

The chat UI now provides a more user-friendly experience when installing MCP servers that require API keys (like Brave Search or GitHub). Instead of failing with cryptic errors, the system now:

1. **Prompts users for API keys** when needed
2. **Accepts natural language input** for API keys
3. **Provides helpful instructions** on how to obtain API keys
4. **Stores API keys securely** for future use

## Features

### 1. Natural Language API Key Input

Users can provide API keys in various natural formats:

- `install brave search with key YOUR_API_KEY`
- `install brave search with token YOUR_API_KEY`
- `my brave api key is YOUR_API_KEY`
- `brave key = YOUR_API_KEY`
- `install github with token YOUR_TOKEN`

The chat interface automatically parses these patterns and converts them to the proper installation commands.

### 2. Clear Error Messages

When an API key is missing, instead of showing a technical error, the interface displays:

```
🔑 **Brave Search API Key Required**

To use Brave Search, you need to provide an API key.

🌐 **Get your API key:**
1. Visit https://brave.com/search/api/
2. Sign up for a free account
3. Copy your API key

🔧 **To install with your key:**
Please type: `install brave search with key YOUR_API_KEY_HERE`

Or use the exact command:
`install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`
```

### 3. Secure Storage

API keys are automatically stored securely using AES encryption after the first use. This means users don't need to re-enter their API keys for subsequent installations.

### 4. Agent Behavior

The coding agent has been updated to:
- Always ask users for API keys before attempting to install servers that require them
- Never try to install API-key-required servers without user confirmation
- Provide helpful links to obtain API keys

## Supported Servers

The following servers require API keys:

| Server | Required Key | How to Get |
|--------|--------------|------------|
| Brave Search | BRAVE_API_KEY | https://brave.com/search/api/ |
| GitHub | GITHUB_TOKEN | https://github.com/settings/tokens |

## Technical Implementation

### Chat UI (web_ui.py)

1. **Message Preprocessing**: Before sending messages to the agent, the UI checks for natural language API key patterns and converts them to proper commands.

2. **Response Enhancement**: After receiving a response from the agent, the UI checks for API key errors and enhances them with helpful instructions.

### MCP Management Tool (mcp_management_tool.py)

1. **Enhanced Error Messages**: When API keys are missing, the tool returns detailed instructions on how to obtain and provide them.

2. **Secure Storage Integration**: The tool automatically stores and retrieves API keys using the secure storage system.

### Coding Agent (coding_agent.py)

1. **Updated System Prompt**: The agent is instructed to always ask users for API keys before attempting installations.

2. **Workflow Documentation**: Clear step-by-step workflows for each server that requires API keys.

## Example Usage

### Scenario 1: User wants to search the web

```
User: Search the web for information about MCP servers
Agent: I need to use Brave Search for this. Let me install it first.
       [Agent attempts to use brave_search]
UI: 🔑 **Brave Search API Key Required**
    To use Brave Search, you need to provide an API key.
    [Instructions on how to get and provide the key]

User: install brave search with key BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh
Agent: [Successfully installs and uses Brave Search]
```

### Scenario 2: User provides key upfront

```
User: my brave api key is BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh
UI: [Converts to: I have your Brave API key. Let me install the brave search server...]
Agent: [Installs Brave Search with the provided key]
```

## Security Considerations

1. **Encryption**: All API keys are stored encrypted using AES-256 encryption
2. **File Permissions**: Encrypted key files are created with restrictive permissions (0600)
3. **No Logging**: API keys are never logged or displayed in full
4. **Secure Deletion**: Keys can be securely deleted when no longer needed

## Future Improvements

1. **Modal Dialog**: Add a proper modal dialog for API key input
2. **Key Validation**: Validate API keys before attempting installation
3. **Multiple Keys**: Support for multiple API keys per service
4. **Key Rotation**: Automatic key rotation reminders