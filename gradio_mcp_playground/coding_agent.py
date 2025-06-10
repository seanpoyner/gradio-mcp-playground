"""LlamaIndex Coding Agent for Gradio MCP Playground

Provides an intelligent coding assistant that can help with MCP server development,
code analysis, and general programming tasks.
"""

from typing import Any, Dict
import logging

# Configure logging to reduce verbosity
logging.getLogger("llama_index").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

# Optional imports
try:
    from llama_index.core import Settings
    from llama_index.core.agent import ReActAgent
    from llama_index.core.memory import ChatMemoryBuffer
    from llama_index.core.tools import FunctionTool
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .prompt_manager import get_prompt_manager
from .conversation_manager import ConversationManager

if HAS_LLAMAINDEX:

    class CodingAgent:
        """LlamaIndex-powered coding agent for MCP development assistance"""

        def __init__(self):
            self.agent = None
            self.llm = None
            self.current_model = None
            self.hf_token = None
            self.conversation_manager = ConversationManager(max_context_length=30000)
            self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
            self.mcp_connections = {}  # Store MCP connections
            self.mcp_client_manager = None  # MCP client manager for external servers

            # Get prompt manager
            self.prompt_manager = get_prompt_manager()

            # Load available models from configuration
            self.available_models = self.prompt_manager.get_available_models()

            self._setup_tools()

            # Load configured MCP servers after tools are set up
            self._load_configured_mcp_servers()

        def _setup_tools(self):
            """Setup tools for the coding agent"""
            self.tools = [
                self._create_mcp_help_tool(),
                self._create_code_analyzer_tool(),
                self._create_gradio_helper_tool(),
                self._create_registry_search_tool(),  # Add registry search tool
                self._create_check_server_requirements_tool(),  # Add requirements checker
            ]

            # Add MCP server management tools
            self._add_mcp_management_tools()

        def _create_mcp_help_tool(self) -> FunctionTool:
            """Create tool for MCP-specific help and guidance"""

            def mcp_help(query: str) -> str:
                """Provide help and guidance about MCP (Model Context Protocol) development.

                Args:
                    query: Question about MCP development, servers, or tools
                """
                query_lower = query.lower()

                # Check for specific server queries
                servers_to_check = {
                    "memory": ["memory", "server", "mcp"],
                    "filesystem": ["filesystem", "file system"],
                    "sequential_thinking": ["sequential", "thinking"],
                    "brave_search": ["brave", "search"],
                    "github": ["github"],
                    "time": ["time", "server"],
                }

                for server_id, keywords in servers_to_check.items():
                    if any(keyword in query_lower for keyword in keywords):
                        server_info = self.prompt_manager.get_mcp_knowledge(server_id)
                        if server_info:
                            return server_info.get("description", f"Information about {server_id}")

                # Check for general queries
                general_knowledge = self.prompt_manager.get_mcp_knowledge()

                if "what is mcp" in query_lower or "what's mcp" in query_lower:
                    return general_knowledge.get("what_is_mcp", "MCP information not found")
                elif "server" in query_lower:
                    return general_knowledge.get("mcp_server", "Server information not found")
                elif "tool" in query_lower:
                    return general_knowledge.get("mcp_tools", "Tools information not found")
                elif "gradio" in query_lower:
                    return general_knowledge.get(
                        "gradio_integration", "Gradio integration information not found"
                    )
                elif "best practice" in query_lower or "practices" in query_lower:
                    practices = self.prompt_manager.get_best_practices()
                    return "MCP Best Practices:\n" + "\n".join(
                        [f"• {practice}" for practice in practices]
                    )
                else:
                    what_is_mcp = general_knowledge.get("what_is_mcp", "")
                    return f"Here's general guidance about MCP development: {what_is_mcp} For specific help, ask about MCP servers, tools, or best practices."

            return FunctionTool.from_defaults(fn=mcp_help, name="mcp_help")

        def _create_code_analyzer_tool(self) -> FunctionTool:
            """Create tool for analyzing code"""

            def analyze_code(code: str, language: str = "python") -> str:
                """Analyze code for potential issues, improvements, and best practices.

                Args:
                    code: The code to analyze
                    language: Programming language (default: python)
                """
                try:
                    lines = code.split("\n")
                    analysis = {
                        "line_count": len(lines),
                        "suggestions": [],
                        "potential_issues": [],
                        "security_notes": [],
                    }

                    # Basic Python analysis
                    if language.lower() == "python":
                        for i, line in enumerate(lines, 1):
                            line_stripped = line.strip()

                            # Check for common issues
                            if "print(" in line_stripped and "debug" not in line_stripped.lower():
                                analysis["suggestions"].append(
                                    f"Line {i}: Consider using logging instead of print for production code"
                                )

                            if "except:" in line_stripped:
                                analysis["potential_issues"].append(
                                    f"Line {i}: Bare except clause - consider catching specific exceptions"
                                )

                            if "eval(" in line_stripped or "exec(" in line_stripped:
                                analysis["security_notes"].append(
                                    f"Line {i}: Use of eval/exec can be dangerous - validate inputs carefully"
                                )

                            if "TODO" in line_stripped or "FIXME" in line_stripped:
                                analysis["suggestions"].append(
                                    f"Line {i}: Contains TODO/FIXME comment"
                                )

                    result = f"Code Analysis ({language}):\n"
                    result += f"Lines of code: {analysis['line_count']}\n\n"

                    if analysis["potential_issues"]:
                        result += (
                            "Potential Issues:\n"
                            + "\n".join([f"• {issue}" for issue in analysis["potential_issues"]])
                            + "\n\n"
                        )

                    if analysis["security_notes"]:
                        result += (
                            "Security Notes:\n"
                            + "\n".join([f"• {note}" for note in analysis["security_notes"]])
                            + "\n\n"
                        )

                    if analysis["suggestions"]:
                        result += (
                            "Suggestions:\n"
                            + "\n".join(
                                [f"• {suggestion}" for suggestion in analysis["suggestions"]]
                            )
                            + "\n"
                        )

                    if not any(
                        [
                            analysis["potential_issues"],
                            analysis["security_notes"],
                            analysis["suggestions"],
                        ]
                    ):
                        result += "No obvious issues found. Code looks good!"

                    return result

                except Exception as e:
                    return f"Error analyzing code: {str(e)}"

            return FunctionTool.from_defaults(fn=analyze_code, name="analyze_code")

        def _create_gradio_helper_tool(self) -> FunctionTool:
            """Create tool for Gradio-specific help"""

            def gradio_help(component_type: str = "") -> str:
                """Get help with Gradio components and best practices.

                Args:
                    component_type: Specific Gradio component to get help with
                """
                if component_type:
                    component_help = self.prompt_manager.get_gradio_help(component_type.lower())
                    if component_help:
                        description = component_help.get("description", "")
                        example = component_help.get("example", "")
                        if example:
                            return f"{description}\n\nExample:\n{example}"
                        return description
                    else:
                        # Get list of available components
                        all_components = [
                            "textbox",
                            "button",
                            "dropdown",
                            "slider",
                            "file",
                            "dataframe",
                            "plot",
                            "interface",
                            "blocks",
                        ]
                        return f"No specific help found for '{component_type}'. Available components: {', '.join(all_components)}"
                else:
                    # Return general tips
                    general_help = self.prompt_manager.get_gradio_help()
                    tips = general_help.get("general_tips", [])
                    if tips:
                        return "Gradio tips:\n" + "\n".join([f"• {tip}" for tip in tips])
                    return "Gradio tips: Use clear labels, provide examples, handle errors gracefully, test with different inputs."

            return FunctionTool.from_defaults(fn=gradio_help, name="gradio_help")





        def _create_registry_search_tool(self) -> FunctionTool:
            """Create tool to search MCP server registry"""

            def search_mcp_registry(query: str) -> str:
                """Search the MCP server registry for servers matching a query.

                Args:
                    query: Search query (e.g., "obsidian", "database", "api")

                Returns:
                    List of matching MCP servers with descriptions
                """
                try:
                    from .registry import ServerRegistry

                    registry = ServerRegistry()

                    # Search for matching servers
                    results = registry.search_mcp_servers(query)

                    if not results:
                        return f"No MCP servers found matching '{query}'"

                    output = f"🔍 Found {len(results)} MCP servers matching '{query}':\n\n"
                    for server in results[:10]:  # Limit to 10 results
                        output += f"**{server['id']}** ({server['category']})\n"
                        output += f"📝 {server['description']}\n"

                        # Show required parameters
                        if server.get("required_args"):
                            output += f"📋 Required args: {', '.join(server['required_args'])}\n"

                        # Show environment variables needed
                        if server.get("env_vars"):
                            output += f"🔑 Requires: {', '.join(server['env_vars'].keys())}\n"

                        output += f"💡 Install: install_mcp_server_from_registry(server_id='{server['id']}')\n"
                        output += "-" * 50 + "\n\n"

                    return output
                except Exception as e:
                    return f"Error searching registry: {str(e)}"

            return FunctionTool.from_defaults(fn=search_mcp_registry, name="search_mcp_registry")

        def _create_check_server_requirements_tool(self) -> FunctionTool:
            """Create tool to check server requirements before installation"""

            def check_server_requirements(server_id: str) -> str:
                """Check what requirements are needed to install an MCP server.

                Args:
                    server_id: ID of the server to check (e.g., 'brave-search', 'filesystem')

                Returns:
                    Information about required arguments and environment variables
                """
                try:
                    from .registry import ServerRegistry
                    from .secure_storage import SecureTokenStorage

                    registry = ServerRegistry()
                    storage = SecureTokenStorage()

                    # Get server info
                    server_info = registry.get_server_info(server_id)
                    if not server_info:
                        return f"❌ Server '{server_id}' not found in registry"

                    output = f"📋 **Requirements for {server_info['name']}**\n\n"

                    # Check required arguments
                    required_args = server_info.get("required_args", [])
                    if required_args:
                        output += "**Required Arguments:**\n"
                        for arg in required_args:
                            output += f"- `{arg}`: "
                            if arg == "path":
                                output += "Directory path to provide access to\n"
                            elif arg == "timezone":
                                output += "Timezone (e.g., 'UTC', 'America/New_York')\n"
                            elif arg == "vault_path1":
                                output += "Path to your Obsidian vault\n"
                            else:
                                output += "Required value\n"

                    # Check environment variables
                    env_vars = server_info.get("env_vars", {})
                    if env_vars:
                        output += "\n**Required Environment Variables:**\n"

                        # Check if we have stored keys
                        stored_keys = storage.retrieve_server_keys(server_id)

                        for env_var, description in env_vars.items():
                            output += f"- `{env_var}`: {description}\n"

                            # Check if we already have this key stored
                            if env_var in stored_keys:
                                output += "  ✅ Already stored securely\n"
                            else:
                                output += "  ❌ Not yet provided\n"

                                # Add instructions for getting the key
                                if server_id == "brave-search":
                                    output += "  📝 Get your API key from: https://brave.com/search/api/\n"
                                elif server_id == "github":
                                    output += "  📝 Create a token at: https://github.com/settings/tokens\n"

                    # Add setup help
                    if server_info.get("setup_help"):
                        output += f"\n**Setup Help:** {server_info['setup_help']}\n"

                    # Add example installation command
                    output += "\n**Example Installation:**\n```\n"

                    # Build example command
                    example_args = {}
                    for arg in required_args:
                        if arg == "path":
                            # Use actual home directory instead of generic path
                            import os
                            example_args[arg] = os.path.join(os.path.expanduser("~"), "workspace")
                        elif arg == "timezone":
                            example_args[arg] = "UTC"
                        elif arg == "vault_path1":
                            # Use actual path example
                            import os
                            example_args[arg] = os.path.join(os.path.expanduser("~"), "Documents/ObsidianVault")
                        else:
                            example_args[arg] = f"YOUR_{arg.upper()}"

                    # Add tokens for env vars
                    if "BRAVE_API_KEY" in env_vars:
                        example_args["token"] = "YOUR_BRAVE_API_KEY"
                    elif "GITHUB_TOKEN" in env_vars:
                        example_args["token"] = "YOUR_GITHUB_TOKEN"

                    # Format the command
                    if example_args:
                        args_str = ", ".join([f"{k}='{v}'" for k, v in example_args.items()])
                        output += f"install_mcp_server_from_registry(server_id='{server_id}', {args_str})\n"
                    else:
                        output += f"install_mcp_server_from_registry(server_id='{server_id}')\n"

                    output += "```"

                    return output

                except Exception as e:
                    return f"Error checking requirements: {str(e)}"

            return FunctionTool.from_defaults(
                fn=check_server_requirements, name="check_server_requirements"
            )

        def _add_mcp_management_tools(self):
            """Add MCP server management tools to the agent"""
            try:
                from .mcp_management_tool import create_mcp_management_tools

                mcp_tools = create_mcp_management_tools()
                self.tools.extend(mcp_tools)

                print("DEBUG: Added MCP server management tools to coding agent")
            except ImportError as e:
                print(f"DEBUG: Could not add MCP management tools: {e}")
            except Exception as e:
                print(f"DEBUG: Error adding MCP management tools: {e}")

        def _load_configured_mcp_servers(self):
            """Load MCP servers from configuration with caching support"""
            try:
                import json
                import os
                from pathlib import Path

                from .mcp_server_config import MCPServerConfig
                from .mcp_working_client import MCPServerProcess, create_mcp_tools_for_server
                from .secure_storage import SecureTokenStorage

                config = MCPServerConfig()
                servers = config.list_servers()

                # Initialize secure storage for retrieving stored tokens
                storage = SecureTokenStorage()

                # Also check Claude Desktop config
                claude_config_path = None
                if os.name == "nt":
                    claude_config_path = Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
                else:
                    # WSL/Linux - check for Windows path
                    possible_paths = [
                        Path("/home/sean/.config/Claude/claude_desktop_config.json"),
                        Path("/mnt/c/Users/seanp/AppData/Roaming/Claude/claude_desktop_config.json"),
                        Path(f"/mnt/c/Users/{os.environ.get('USER', 'seanp')}/AppData/Roaming/Claude/claude_desktop_config.json"),
                    ]
                    for path in possible_paths:
                        if path.exists():
                            claude_config_path = path
                            break

                # Load servers from Claude Desktop if available
                if claude_config_path and claude_config_path.exists():
                    try:
                        with open(claude_config_path) as f:
                            claude_config = json.load(f)
                            if "mcpServers" in claude_config:
                                # Import Claude Desktop servers into our local config
                                for server_name, server_config in claude_config["mcpServers"].items():
                                    if server_name not in servers:
                                        # Extract environment variables that might contain API keys
                                        env_vars = server_config.get("env", {})

                                        # Store API keys securely
                                        if env_vars:
                                            for env_key, env_value in env_vars.items():
                                                # Common API key patterns
                                                if any(pattern in env_key.upper() for pattern in ["TOKEN", "KEY", "SECRET", "API"]):
                                                    storage.store_key(server_name, env_key, env_value)
                                                    print(f"  🔐 Encrypted {env_key} for {server_name}")

                                        # Add server to our local config (without sensitive env vars)
                                        config.add_server(
                                            name=server_name,
                                            command=server_config.get("command"),
                                            args=server_config.get("args"),
                                            env={}  # Don't store env vars in plain text
                                        )

                                        servers[server_name] = server_config
                                        print(f"  📎 Imported {server_name} from Claude Desktop config")
                    except Exception as e:
                        print(f"Warning: Could not load Claude Desktop config: {e}")

                if not servers:
                    print("No MCP servers configured")
                    return

                print(f"Found {len(servers)} configured MCP servers:")
                for server_name in servers:
                    print(f"  - {server_name}")

                # Check if cache is available
                try:
                    from .cache_manager import get_cache_manager
                    cache_manager = get_cache_manager()
                    if cache_manager.enabled:
                        cache_stats = cache_manager.get_cache_stats()
                        if cache_stats['files']['servers'] > 0:
                            print(f"\n📦 Cache enabled ({cache_stats['files']['servers']} servers cached)")
                except:
                    pass
                
                # Load MCP servers using the working approach
                print("\n🔌 Loading MCP server tools...")

                if not hasattr(self, "mcp_tools"):
                    self.mcp_tools = {}

                if not hasattr(self, "_mcp_servers"):
                    self._mcp_servers = {}

                loaded_count = 0
                for server_name, server_config in servers.items():
                    try:
                        command = server_config.get("command", "")
                        args = server_config.get("args", [])
                        env = server_config.get("env", {})

                        # Check for stored API keys for this server
                        stored_keys = storage.retrieve_server_keys(server_name)

                        # If no env vars in config, check stored keys
                        if not env and stored_keys:
                            env = stored_keys
                            print(f"   🔑 Using stored encrypted keys for {server_name}")
                        elif stored_keys:
                            # Merge stored keys with config env vars (stored keys take precedence)
                            env.update(stored_keys)
                            print(f"   🔑 Merged encrypted keys for {server_name}")

                        # Skip servers that require API keys if none found
                        required_env_vars = {
                            "github": ["GITHUB_TOKEN"],
                            "brave-search": ["BRAVE_API_KEY"],
                            "figma": ["FIGMA_TOKEN"],
                            "openai": ["OPENAI_API_KEY"],
                        }

                        if server_name in required_env_vars:
                            missing_vars = [var for var in required_env_vars[server_name] if var not in env]
                            if missing_vars:
                                print(f"   ⚠️  Skipping {server_name} - missing required: {', '.join(missing_vars)}")
                                continue

                        # Create and start server
                        server = MCPServerProcess(server_name, command, args, env)

                        if server.start() and server.initialize():
                            # Create tools
                            server_tools = create_mcp_tools_for_server(server)

                            if server_tools:
                                # Add tools to agent
                                self.tools.extend(server_tools)
                                self.mcp_tools[server_name] = server_tools
                                self._mcp_servers[server_name] = server


                                loaded_count += len(server_tools)
                                print(f"   ✅ Loaded {len(server_tools)} tools from {server_name}")
                            else:
                                print(f"   ⚠️  No tools created for {server_name}")
                                server.stop()
                        else:
                            print(f"   ❌ Failed to start/initialize {server_name}")

                    except Exception as e:
                        print(f"   ❌ Error loading {server_name}: {e}")

                if loaded_count > 0:
                    print(f"\n✅ Successfully loaded {loaded_count} MCP tools!")
                    print("   Tools are now available in the chat")
                else:
                    print("\n⚠️  No MCP tools were loaded")
                    print("   Servers may need to be installed first")

            except Exception as e:
                print(f"Error loading MCP servers: {e}")
                import traceback

                traceback.print_exc()

        def configure_model(self, hf_token: str, model_name: str) -> Dict[str, Any]:
            """Configure the LLM model for the agent"""
            try:
                if not HAS_REQUESTS:
                    return {
                        "success": False,
                        "error": "requests library required for HuggingFace API",
                    }

                # Clean and validate the token
                clean_token = hf_token.strip()
                print(
                    f"DEBUG: Attempting to configure model {model_name} with token length {len(clean_token)}"
                )
                print(f"DEBUG: Token starts with: {clean_token[:10]}...")

                # Validate HuggingFace token
                headers = {
                    "Authorization": f"Bearer {clean_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "gradio-mcp-playground/0.1.0",
                }

                print(f"DEBUG: Request headers: {dict(headers)}")

                try:
                    # Test model access directly instead of whoami (some tokens have limited permissions)
                    model_url = f"https://huggingface.co/api/models/{model_name}"
                    model_response = requests.get(model_url, headers=headers, timeout=10)
                    print(f"DEBUG: Model access test status: {model_response.status_code}")

                    if model_response.status_code == 200:
                        print(f"DEBUG: Model {model_name} is accessible")

                        # Try whoami as secondary validation (but don't fail if it doesn't work)
                        try:
                            response = requests.get(
                                "https://huggingface.co/api/whoami", headers=headers, timeout=5
                            )
                            if response.status_code == 200:
                                user_info = response.json()
                                print(f"DEBUG: HF user info: {user_info}")
                            else:
                                print("DEBUG: Whoami failed but model access works - continuing")
                        except Exception:
                            print(
                                "DEBUG: Whoami endpoint failed but model access works - continuing"
                            )

                    else:
                        print(f"DEBUG: Model access error: {model_response.text[:200]}")
                        return {
                            "success": False,
                            "error": f"Token cannot access model {model_name}. Status: {model_response.status_code}",
                        }

                except requests.exceptions.RequestException as e:
                    print(f"DEBUG: Network exception: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Network error connecting to HuggingFace API: {str(e)}",
                    }

                # Validate model
                if model_name not in self.available_models:
                    return {
                        "success": False,
                        "error": f"Model '{model_name}' not supported. Available models: {list(self.available_models.keys())}",
                    }

                print(f"DEBUG: Creating HuggingFaceInferenceAPI with model {model_name}")

                # Configure LLM
                self.hf_token = clean_token
                self.current_model = model_name

                try:
                    print(f"DEBUG: Creating HuggingFaceInferenceAPI for {model_name}")

                    # Get model defaults from configuration
                    model_defaults = self.prompt_manager.get_model_defaults()

                    self.llm = HuggingFaceInferenceAPI(
                        model_name=model_name,
                        token=clean_token,
                        context_window=self.available_models[model_name]["context_window"],
                        timeout=model_defaults.get("timeout", 60.0),
                        max_new_tokens=model_defaults.get("max_new_tokens", 2048),
                        temperature=model_defaults.get("temperature", 0.7),
                        top_p=model_defaults.get("top_p", 0.95),
                    )
                    print("DEBUG: HuggingFaceInferenceAPI created successfully")

                    # Test the model with a simple prompt (but don't fail if test fails)
                    try:
                        print("DEBUG: Testing model with simple prompt...")
                        test_response = self.llm.complete("Hello, can you help with coding?")
                        print(f"DEBUG: Model test successful: {str(test_response)[:100]}...")
                    except Exception as test_e:
                        print(f"DEBUG: Model test failed, but continuing: {test_e}")
                        # Don't fail configuration - some models might work in chat mode but not complete mode
                        print("DEBUG: Continuing with model configuration despite test failure")

                except Exception as e:
                    print(f"DEBUG: HuggingFaceInferenceAPI creation failed: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Failed to create HuggingFace API client: {str(e)}",
                    }

                # Set global settings
                try:
                    Settings.llm = self.llm
                    print("DEBUG: LLM settings configured")

                    Settings.embed_model = HuggingFaceEmbedding(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                    print("DEBUG: Embedding model configured")
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to configure LlamaIndex settings: {str(e)}",
                    }

                # Create agent
                try:
                    # Get all tools including MCP tools
                    all_tools = list(self.tools)  # Copy base tools

                    # Add any MCP tools that were loaded from config
                    if hasattr(self, "mcp_tools"):
                        for server_tools in self.mcp_tools.values():
                            all_tools.extend(server_tools)
                            print(f"DEBUG: Added {len(server_tools)} tools from MCP servers")

                    # Get system prompt from configuration
                    system_prompt = self.prompt_manager.get_system_prompt("coding_agent.main")

                    self.agent = ReActAgent.from_tools(
                        tools=all_tools,
                        llm=self.llm,
                        memory=self.memory,
                        verbose=True,
                        max_iterations=100,  # Allow for complex multi-step operations
                        system_prompt=system_prompt,
                    )
                    print("DEBUG: ReActAgent created successfully")
                except Exception as e:
                    return {"success": False, "error": f"Failed to create ReAct agent: {str(e)}"}

                return {
                    "success": True,
                    "model": self.available_models[model_name]["name"],
                    "description": self.available_models[model_name]["description"],
                }

            except Exception as e:
                import traceback

                print(f"DEBUG: Unexpected error in configure_model: {str(e)}")
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        def _preprocess_message(self, message: str) -> str:
            """Preprocess user message to replace generic references with specific paths"""
            try:
                from .environment_config import get_environment_info
                env_info = get_environment_info()

                # Determine the appropriate home directory based on environment
                if 'wsl' in env_info and 'windows_user_home' in env_info['wsl']:
                    # In WSL, use Windows home for Windows programs
                    home_dir = env_info['wsl']['windows_user_home']
                elif env_info['os']['is_windows']:
                    # Native Windows
                    home_dir = env_info['paths']['home']
                else:
                    # Linux/Mac
                    home_dir = env_info['paths']['home']

                # Replace common phrases with actual paths
                replacements = [
                    ("my home directory", home_dir),
                    ("my home folder", home_dir),
                    ("my home", home_dir),
                    ("~/", home_dir + r"\\"),  # For Windows paths (raw string)
                    ("~", home_dir),
                ]

                processed = message
                for phrase, replacement in replacements:
                    # Case-insensitive replacement
                    import re
                    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                    processed = pattern.sub(replacement, processed)

                # Also add explicit hint about the home directory and file paths
                if any(phrase in message.lower() for phrase in ["home dir", "home folder", "save", "screenshot", "file", "path"]):
                    if 'wsl' in env_info:
                        processed += f"\n\n(IMPORTANT: Use Windows paths for files. The Windows home directory is {home_dir}. For example, save files as {home_dir}\\filename.png, NOT /home/user/filename.png)"
                    else:
                        processed += f"\n\n(Note: The home directory is {home_dir})"

                return processed

            except Exception as e:
                # If preprocessing fails, just return original message
                print(f"Warning: Message preprocessing failed: {e}")
                return message

        def chat(self, message: str) -> str:
            """Send a message to the coding agent"""
            if not self.agent:
                return "Please configure a model first by providing your HuggingFace API token and selecting a model."

            try:
                # Preprocess the message to replace "my home directory" with actual path
                processed_message = self._preprocess_message(message)

                # Check if user is introducing themselves
                if any(phrase in message.lower() for phrase in ["my name is", "i am", "i'm"]):
                    # Check if memory server is available
                    if "memory" in self.mcp_connections:
                        # Store the conversation automatically
                        try:
                            from datetime import datetime

                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                            self.agent.chat(
                                f"memory_store_conversation(topic='User Introduction', content='User message: {message} - Timestamp: {timestamp}')"
                            )
                        except Exception:
                            pass  # Silently fail if memory storage doesn't work

                # Check current context size and compact if needed
                try:
                    # Get current conversation from memory
                    chat_history = self.memory.get()
                    if chat_history and len(str(chat_history)) > 25000:
                        # Context is getting large, reset memory with summary
                        print("DEBUG: Compacting conversation history due to context size")
                        self.memory.reset()
                        self.memory.put({"role": "system", "content": "Previous conversation context was compacted. Continue helping the user."})
                except Exception as e:
                    print(f"DEBUG: Error checking context size: {e}")
                
                response = self.agent.chat(processed_message)
                response_str = str(response)

                # Truncate very long responses to prevent UI issues
                if len(response_str) > 15000:
                    response_str = response_str[:15000] + "\n\n... (response truncated for display)"

                return response_str
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg and "not found" in error_msg.lower():
                    return f"❌ Model endpoint not available. Try using 'Zephyr 7B Beta' which is confirmed to work.\n\nOriginal error: {error_msg}"
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    return f"❌ Authentication failed. Please check your HuggingFace token has the correct permissions.\n\nOriginal error: {error_msg}"
                elif "503" in error_msg or "temporarily unavailable" in error_msg.lower():
                    return f"❌ Model is temporarily unavailable. Please try again in a few minutes.\n\nOriginal error: {error_msg}"
                else:
                    return f"❌ Error processing message: {error_msg}\n\n💡 Try switching to 'Zephyr 7B Beta' model which is confirmed to work."

        def chat_with_steps(self, message: str):
            """Send a message to the coding agent and return both steps and final response"""
            if not self.agent:
                return (
                    [],
                    "Please configure a model first by providing your HuggingFace API token and selecting a model.",
                )

            try:
                # Preprocess the message to replace "my home directory" with actual path
                processed_message = self._preprocess_message(message)

                # Create a custom handler to capture steps
                steps = []

                # Override the agent's step method to capture thinking
                original_step = getattr(self.agent, "_run_step", None)

                def capture_step(step_input, **kwargs):
                    """Capture reasoning steps"""
                    if hasattr(step_input, "input"):
                        user_input = str(step_input.input)
                        if user_input and user_input != "None":
                            steps.append(f"🤔 **Input**: {user_input}")

                    # Call original step method
                    result = original_step(step_input, **kwargs) if original_step else None

                    # Extract thinking and action from the step
                    if result and hasattr(result, "output"):
                        output_str = str(result.output)

                        # Parse ReAct format (Thought: ... Action: ... Action Input: ... Observation: ...)
                        lines = output_str.split("\n")
                        current_section = None
                        section_content = []

                        for line in lines:
                            line = line.strip()
                            if line.startswith("Thought:"):
                                if current_section and section_content:
                                    steps.append(
                                        f"💭 **{current_section}**: {' '.join(section_content)}"
                                    )
                                current_section = "Thought"
                                section_content = [line[8:].strip()]  # Remove "Thought:" prefix
                            elif line.startswith("Action:"):
                                if current_section and section_content:
                                    steps.append(
                                        f"💭 **{current_section}**: {' '.join(section_content)}"
                                    )
                                current_section = "Action"
                                section_content = [line[7:].strip()]  # Remove "Action:" prefix
                            elif line.startswith("Action Input:"):
                                if current_section and section_content:
                                    steps.append(
                                        f"🎯 **{current_section}**: {' '.join(section_content)}"
                                    )
                                current_section = "Action Input"
                                section_content = [
                                    line[13:].strip()
                                ]  # Remove "Action Input:" prefix
                            elif line.startswith("Observation:"):
                                if current_section and section_content:
                                    steps.append(
                                        f"📝 **{current_section}**: {' '.join(section_content)}"
                                    )
                                current_section = "Observation"
                                obs_content = line[12:].strip()  # Remove "Observation:" prefix
                                
                                # Process observation to handle images
                                if self.conversation_manager and len(obs_content) > 1000:
                                    obs_content = self.conversation_manager.process_tool_observation(obs_content)
                                
                                section_content = [obs_content]
                            elif line and current_section:
                                section_content.append(line)

                        # Add the last section
                        if current_section and section_content:
                            icon = (
                                "🎯"
                                if current_section == "Action"
                                else "📝" if current_section == "Observation" else "💭"
                            )
                            steps.append(
                                f"{icon} **{current_section}**: {' '.join(section_content)}"
                            )

                    return result

                # Temporarily override the step method
                if hasattr(self.agent, "_run_step"):
                    self.agent._run_step = capture_step

                # Get the response
                response = self.agent.chat(processed_message)
                response_str = str(response)

                # Restore original method
                if original_step:
                    self.agent._run_step = original_step

                # Truncate very long responses to prevent UI issues
                if len(response_str) > 15000:
                    response_str = response_str[:15000] + "\n\n... (response truncated for display)"

                return steps, response_str

            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg and "not found" in error_msg.lower():
                    return (
                        [],
                        f"❌ Model endpoint not available. Try using 'Zephyr 7B Beta' which is confirmed to work.\n\nOriginal error: {error_msg}",
                    )
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    return (
                        [],
                        f"❌ Authentication failed. Please check your HuggingFace token has the correct permissions.\n\nOriginal error: {error_msg}",
                    )
                elif "503" in error_msg or "temporarily unavailable" in error_msg.lower():
                    return (
                        [],
                        f"❌ Model is temporarily unavailable. Please try again in a few minutes.\n\nOriginal error: {error_msg}",
                    )
                else:
                    return (
                        [],
                        f"❌ Error processing message: {error_msg}\n\n💡 Try switching to 'Zephyr 7B Beta' model which is confirmed to work.",
                    )

        def get_available_models(self) -> Dict[str, Dict[str, Any]]:
            """Get list of available models"""
            return self.available_models

        def cleanup(self):
            """Clean up resources including MCP servers"""
            if hasattr(self, "_mcp_servers"):
                for server_name, server in self._mcp_servers.items():
                    try:
                        server.stop()
                        print(f"Stopped MCP server: {server_name}")
                    except Exception:
                        pass
                self._mcp_servers.clear()

        def reset_conversation(self):
            """Reset the conversation memory"""
            self.memory.reset()
            if self.agent:
                self.agent.reset()

        def is_configured(self) -> bool:
            """Check if agent is properly configured"""
            return self.agent is not None and self.llm is not None

        def add_mcp_connection(self, connection_id: str, connection_info: Dict[str, Any]):
            """Add an MCP connection to the coding agent"""
            try:
                self.mcp_connections[connection_id] = connection_info

                # For external MCP servers, try to connect and get actual tools
                # Include all known registry servers
                external_servers = [
                    "obsidian",
                    "filesystem",
                    "github",
                    "time",
                    "brave-search",
                    "memory",
                    "sequential-thinking",
                    "puppeteer",
                    "everything",
                    "azure",
                    "office-powerpoint",
                    "office-word",
                    "excel",
                    "quickchart",
                    "screenshotone",
                    "figma",
                    "pg-cli-server",
                ]
                if connection_id in external_servers:
                    self._connect_to_external_mcp_server(connection_id, connection_info)
                else:
                    # Only create placeholder tools if not an external server
                    if connection_info.get("tools"):
                        self._create_mcp_tools(connection_id, connection_info)

                # Recreate agent with new tools if already configured
                if self.is_configured():
                    self._recreate_agent_with_mcp_tools()

            except Exception as e:
                raise Exception(f"Failed to add MCP connection {connection_id}: {str(e)}") from e

        def _connect_to_external_mcp_server(self, server_id: str, connection_info: Dict[str, Any]):
            """Connect to an external MCP server and create tools"""
            try:
                from .mcp_working_client import MCPServerProcess, create_mcp_tools_for_server

                # Extract command and args from connection info
                command_str = connection_info.get("command", "")
                if command_str:
                    parts = command_str.split()
                    command = parts[0] if parts else None
                    args = parts[1:] if len(parts) > 1 else []
                else:
                    command = connection_info.get("command", "")
                    args = connection_info.get("args", [])

                # Get environment variables
                env = connection_info.get("env", {})

                # Create and start server using the working client
                server = MCPServerProcess(server_id, command, args, env)

                if server.start() and server.initialize():
                    # Create tools using the working implementation
                    mcp_tools = create_mcp_tools_for_server(server)

                    if mcp_tools:
                        # Store tools for this server
                        if not hasattr(self, "mcp_tools"):
                            self.mcp_tools = {}
                        self.mcp_tools[server_id] = mcp_tools

                        # Store the server process for cleanup
                        if not hasattr(self, "_mcp_servers"):
                            self._mcp_servers = {}
                        self._mcp_servers[server_id] = server

                        print(f"✅ Connected to {server_id} MCP server with {len(mcp_tools)} tools")

                        # List the tool names for debugging
                        tool_names = [tool.name for tool in mcp_tools if hasattr(tool, "name")]
                        print(f"   Available tools: {', '.join(tool_names)}")
                    else:
                        print(f"⚠️ No tools created for {server_id}")
                        server.stop()
                else:
                    print(f"❌ Failed to start/initialize {server_id}")
                    # Fall back to direct implementation tools
                    self._create_mcp_tools(server_id, connection_info)
                    print(f"Using direct implementation for {server_id} tools")

            except Exception as e:
                print(f"Failed to connect to {server_id} MCP server: {str(e)}")
                import traceback

                traceback.print_exc()
                # Fall back to direct implementation tools
                self._create_mcp_tools(server_id, connection_info)
                print(f"Using direct implementation for {server_id} tools")
        def _create_mcp_tools(self, connection_id: str, connection_info: Dict[str, Any]):
            """Create placeholder LlamaIndex tools for MCP connections
            
            This method only creates placeholder tools. Actual functionality
            should come from MCP servers via _connect_to_external_mcp_server.
            """
            tools = []

            # Create placeholder tools for all connections
            for tool_name in connection_info.get("tools", []):

                def create_placeholder_tool(conn_id, tool_n):
                    def placeholder_func(**kwargs) -> str:
                        """Placeholder MCP tool"""
                        return f"Tool {tool_n} from {conn_id} called with args: {kwargs}\n\nNote: This is a placeholder. Install the actual MCP server for full functionality."

                    return FunctionTool.from_defaults(
                        fn=placeholder_func,
                        name=f"{conn_id}_{tool_n}",
                        description=f"Call {tool_n} tool from {connection_info['name']} MCP server",
                    )

                tools.append(create_placeholder_tool(connection_id, tool_name))

            # Store tools for this connection
            if not hasattr(self, "mcp_tools"):
                self.mcp_tools = {}
            self.mcp_tools[connection_id] = tools


        def _recreate_agent_with_mcp_tools(self):
            """Recreate the agent with MCP tools included"""
            if not self.is_configured():
                return

            try:
                # Get all base tools first
                all_tools = list(self.tools)  # Start with original tools

                # Add MCP tools
                if hasattr(self, "mcp_tools"):
                    for connection_tools in self.mcp_tools.values():
                        all_tools.extend(connection_tools)

                # Get the system prompt from configuration
                system_prompt = self.prompt_manager.get_system_prompt("coding_agent.main")

                # Recreate agent with all tools
                self.agent = ReActAgent.from_tools(
                    tools=all_tools,
                    llm=self.llm,
                    memory=self.memory,
                    verbose=True,
                    max_iterations=100,  # Keep the same max iterations
                    system_prompt=system_prompt,
                )

            except Exception:
                # If recreation fails, just continue with existing agent
                pass

        def get_mcp_connections(self) -> Dict[str, Any]:
            """Get all MCP connections"""
            return self.mcp_connections

        def remove_mcp_connection(self, connection_id: str):
            """Remove an MCP connection"""
            if connection_id in self.mcp_connections:
                del self.mcp_connections[connection_id]

            if hasattr(self, "mcp_tools") and connection_id in self.mcp_tools:
                del self.mcp_tools[connection_id]

            # Recreate agent without this connection's tools
            if self.is_configured():
                self._recreate_agent_with_mcp_tools()

else:
    # Dummy class when LlamaIndex is not available
    class CodingAgent:
        def __init__(self):
            raise ImportError(
                "LlamaIndex is required for coding agent functionality. Install with: pip install -e '.[ai]'"
            )

        def get_available_models(self):
            return {}
