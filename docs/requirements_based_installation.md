# Requirements-Based Server Installation

This document describes the improved MCP server installation system that uses the server registry to automatically detect and prompt for required arguments before installation.

## Overview

The system now follows a strict workflow:

1. **Check Requirements First**: Before attempting any installation, the agent uses `check_server_requirements()` to determine what's needed
2. **Prompt for Missing Values**: If any arguments or API keys are required, the agent asks the user for them
3. **Validate and Install**: Only after all requirements are satisfied does the installation proceed

## Key Features

### 1. Automatic Requirements Detection

The system uses the server registry to automatically detect:
- Required arguments (e.g., `path` for filesystem, `vault_path1` for Obsidian)
- Optional arguments (e.g., `vault_path2` for Obsidian)
- Environment variables (e.g., `BRAVE_API_KEY`, `GITHUB_TOKEN`)

### 2. Smart Prompting

When requirements are detected, the agent:
- Shows exactly what's needed with clear descriptions
- Indicates whether API keys are already stored securely
- Provides links to obtain API keys
- Gives example commands with proper syntax

### 3. Natural Language Input Support

Users can provide requirements in natural language:

```
# API Keys
"my brave api key is BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh"
"install brave search with key YOUR_KEY"
"my github token is ghp_1234567890"

# Paths
"use path /home/user/workspace"
"my obsidian vault is at /path/to/vault"

# Other Parameters
"use timezone America/New_York"
```

## Agent Workflow

### Example 1: Installing Brave Search

```
User: I want to search the web

Agent: I'll help you search the web. Let me check what's required for the Brave Search server...
[Calls: check_server_requirements("brave-search")]

📋 Requirements for Brave Search Server

Required Environment Variables:
- BRAVE_API_KEY: Your Brave Search API key
  ❌ Not yet provided
  📝 Get your API key from: https://brave.com/search/api/

Agent: I need your Brave Search API key to install this server. 
Please get your free API key from https://brave.com/search/api/ and provide it.

Example: "my brave api key is YOUR_KEY_HERE"

User: my brave api key is BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh

Agent: Perfect! Let me install the Brave Search server with your API key...
[Calls: install_mcp_server_from_registry(server_id='brave-search', token='BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh')]
```

### Example 2: Installing Filesystem Server

```
User: I need to access files on my computer

Agent: I'll help you set up file access. Let me check the requirements...
[Calls: check_server_requirements("filesystem")]

📋 Requirements for Filesystem Server

Required Arguments:
- path: Directory path to provide access to

Agent: Which directory would you like to provide access to?

Example: "use path /home/user/workspace"

User: use path /home/sean/projects

Agent: Great! I'll install the filesystem server with access to /home/sean/projects...
[Calls: install_mcp_server_from_registry(server_id='filesystem', path='/home/sean/projects')]
```

### Example 3: Installing Memory Server (No Requirements)

```
User: I want to use the memory server

Agent: Let me check what's required for the memory server...
[Calls: check_server_requirements("memory")]

📋 Requirements for Memory Server

Required Arguments: None
Required Environment Variables: None

Agent: Good news! The memory server has no requirements. I'll install it now...
[Calls: install_mcp_server_from_registry(server_id='memory')]
```

## Technical Implementation

### Registry Structure

Each server in the registry defines:

```python
{
    "server-id": {
        "name": "Server Name",
        "description": "...",
        "required_args": ["arg1", "arg2"],  # Required arguments
        "optional_args": ["opt1", "opt2"],  # Optional arguments
        "env_vars": {                        # Required environment variables
            "ENV_VAR_NAME": "Description of what this is"
        },
        "setup_help": "Additional setup instructions",
        "args_template": [...]               # Command template
    }
}
```

### New Tools

#### check_server_requirements(server_id)

This tool:
- Fetches server information from the registry
- Checks which arguments and environment variables are required
- Verifies if API keys are already stored securely
- Returns formatted information about all requirements

#### Enhanced install_mcp_server_from_registry()

The installation function now:
- Validates all required arguments are provided
- Retrieves stored API keys from secure storage
- Provides detailed error messages for missing requirements
- Stores API keys securely after successful installation

### Chat UI Enhancements

The web UI now:
- Parses natural language input for common patterns
- Enhances error messages with helpful prompts
- Detects when the agent is showing requirements
- Adds user-friendly examples for providing information

## Benefits

1. **No Failed Installations**: By checking requirements first, we avoid installation failures due to missing arguments

2. **Better User Experience**: Clear prompts and natural language support make it easy to provide required information

3. **Security**: API keys are stored securely and reused automatically

4. **Flexibility**: Supports various input formats and patterns

5. **Discoverability**: Users learn what's needed before attempting installation

## Server-Specific Requirements

| Server | Required Args | Environment Variables | Notes |
|--------|--------------|----------------------|-------|
| memory | None | None | Installs directly |
| filesystem | path | None | Needs directory path |
| brave-search | None | BRAVE_API_KEY | Needs API key from brave.com |
| github | None | GITHUB_TOKEN | Needs personal access token |
| obsidian | vault_path1 | None | Needs vault directory |
| time | timezone | None | Needs IANA timezone |
| sqlite | database_path | None | Needs .db file path |
| postgres | None | POSTGRES_* vars | Needs connection details |

## Future Improvements

1. **Validation**: Add validation for paths, timezones, and API key formats
2. **Defaults**: Suggest sensible defaults for common parameters
3. **Batch Installation**: Support installing multiple servers with shared requirements
4. **Configuration Profiles**: Save common configurations for reuse