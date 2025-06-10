# Configuration System

The Gradio MCP Playground uses a YAML-based configuration system for managing prompts, knowledge bases, and other text content. This makes the system more maintainable and allows for easy customization without modifying code.

## Configuration Structure

All configuration files are located in `gradio_mcp_playground/config/`:

```
config/
├── prompts/
│   └── system_prompts.yaml      # System prompts for agents
├── knowledge/
│   └── mcp_servers.yaml        # MCP server knowledge base
├── models.yaml                 # LLM model configurations
├── gradio_components.yaml      # Gradio component help
└── server_guidance.yaml        # Server-specific guidance messages
```

## Configuration Files

### 1. System Prompts (`prompts/system_prompts.yaml`)

Contains system prompts used by the coding agent:

```yaml
coding_agent:
  main: |
    You are a coding assistant helping with MCP server management...
    
tool_descriptions:
  mcp_help: "Provide help and guidance about MCP development"
  analyze_code: "Analyze code for potential issues"
```

### 2. Model Configuration (`models.yaml`)

Defines available LLM models and their settings:

```yaml
models:
  "Qwen/Qwen2.5-Coder-32B-Instruct":
    name: "Qwen2.5 Coder 32B (CODING SPECIALIST)"
    description: "Specialized 32B coding model"
    context_window: 32768
    size: "32B parameters"
    strengths:
      - "Code generation"
      - "Code analysis"

defaults:
  temperature: 0.7
  max_new_tokens: 2048
  timeout: 60.0
```

### 3. MCP Knowledge Base (`knowledge/mcp_servers.yaml`)

Contains information about MCP servers:

```yaml
general:
  what_is_mcp: "MCP (Model Context Protocol) is..."
  
servers:
  github:
    description: "The GitHub server provides access to..."
    category: "Development"
    
best_practices:
  - "Always validate inputs in your MCP tools"
  - "Handle errors gracefully"
```

### 4. Server Guidance (`server_guidance.yaml`)

Provides user-facing messages for server operations:

```yaml
servers:
  github:
    success: |
      **✅ GitHub tools are now available!**
      You can use:
      - `github_list_repos()` - List your repositories
      
  filesystem:
    success: |
      **✅ Filesystem tools are now available!**
      Access path: {path}
```

## Using the Prompt Manager

The `PromptManager` class provides easy access to all configuration:

```python
from gradio_mcp_playground.prompt_manager import get_prompt_manager

# Get the global prompt manager instance
pm = get_prompt_manager()

# Load system prompt
system_prompt = pm.get_system_prompt("coding_agent.main")

# Get model configuration
model_config = pm.get_model_config("Qwen/Qwen2.5-Coder-32B-Instruct")

# Get MCP knowledge
github_info = pm.get_mcp_knowledge("github")

# Get server guidance with variable substitution
guidance = pm.get_server_guidance("filesystem", "success", path="/home/user")
```

## Customizing Configuration

### Adding New Prompts

1. Edit the appropriate YAML file
2. Add your new content following the existing structure
3. Access it using the prompt manager

Example - adding a new tool description:

```yaml
# In system_prompts.yaml
tool_descriptions:
  my_new_tool: "Description of what the tool does"
```

### Adding New Servers

1. Add server info to `mcp_servers.yaml`:

```yaml
servers:
  my_server:
    description: "What this server does"
    category: "Category"
```

2. Add guidance messages to `server_guidance.yaml`:

```yaml
servers:
  my_server:
    success: |
      **✅ My Server is ready!**
      Available tools: ...
```

### Environment-Specific Configuration

You can override configuration by creating a `config.local/` directory:

```
config.local/
├── prompts/
│   └── system_prompts.yaml  # Override specific prompts
└── models.yaml              # Override model settings
```

The prompt manager will check local configuration first.

## Benefits

1. **Maintainability**: Prompts and text are separate from code
2. **Customization**: Easy to modify without changing Python files
3. **Version Control**: Track changes to prompts separately
4. **Localization**: Easy to translate or customize for different contexts
5. **Testing**: Can test with different prompt configurations

## Best Practices

1. Keep YAML files well-organized with clear sections
2. Use descriptive keys that explain the content's purpose
3. Include comments in YAML files to document usage
4. Use variable substitution for dynamic content
5. Test configuration changes before deploying

## Troubleshooting

If configuration is not loading:

1. Check YAML syntax (use a YAML validator)
2. Verify file paths are correct
3. Clear the prompt manager cache: `pm.reload()`
4. Check for error messages in console output

## Future Enhancements

- Support for multiple languages
- Environment-specific overrides
- Hot-reloading of configuration changes
- Configuration validation schemas
- Web UI for configuration management