"""Gradio MCP Playground Web UI

Web-based dashboard for managing Gradio MCP servers.
"""

import json
from pathlib import Path

# Optional imports
try:
    import gradio as gr

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

# Always available imports
from .config_manager import ConfigManager
from .registry import ServerRegistry

# Optional imports that depend on other modules
try:
    from .server_manager import GradioMCPServer

    HAS_SERVER_MANAGER = True
except ImportError:
    HAS_SERVER_MANAGER = False

try:
    from .client_manager import GradioMCPClient, MCPConnectionManager

    HAS_CLIENT_MANAGER = True
except ImportError:
    HAS_CLIENT_MANAGER = False

try:
    from .coding_agent import CodingAgent

    HAS_CODING_AGENT = True
except ImportError:
    HAS_CODING_AGENT = False


def create_dashboard():
    """Create the Gradio MCP Playground dashboard"""
    if not HAS_GRADIO:
        raise ImportError("Gradio is required for web dashboard functionality")

    config_manager = ConfigManager()
    registry = ServerRegistry()

    # Only create connection manager if client manager is available
    if HAS_CLIENT_MANAGER:
        connection_manager = MCPConnectionManager()
    else:
        connection_manager = None

    # Initialize coding agent if available
    if HAS_CODING_AGENT:
        try:
            coding_agent = CodingAgent()
        except ImportError as e:
            coding_agent = None
            coding_agent_error = str(e)
    else:
        coding_agent = None
        coding_agent_error = "LlamaIndex not available"

    with gr.Blocks(title="Gradio MCP Playground", theme=gr.themes.Soft(), css="""
        .mcp-connection-card {
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 16px;
            margin: 8px;
            background: #fafbfc;
        }
        .mcp-connection-card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .mcp-server-icon {
            font-size: 2em;
            margin-bottom: 8px;
        }
        .mcp-status-connected {
            color: #28a745;
            font-weight: bold;
        }
        .mcp-status-disconnected {
            color: #dc3545;
            font-weight: bold;
        }
    """) as dashboard:
        gr.Markdown(
            """
            # 🚀 Gradio MCP Playground
            
            Build, manage, and deploy Gradio applications as Model Context Protocol (MCP) servers.
            """
        )

        with gr.Tabs():
            # AI Assistant Tab
            with gr.Tab("🤖 AI Assistant"):
                if coding_agent:
                    gr.Markdown("### AI Coding Assistant")
                    gr.Markdown(
                        "Get help with MCP development, code analysis, and Gradio applications."
                    )

                    # Model configuration section
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("#### Model Configuration")

                            hf_token_input = gr.Textbox(
                                label="HuggingFace API Token",
                                type="password",
                                placeholder="Enter your HuggingFace API token...",
                                info="Get your token from https://huggingface.co/settings/tokens",
                            )

                        with gr.Column(scale=1):
                            model_dropdown = gr.Dropdown(
                                label="Select Model",
                                choices=list(coding_agent.get_available_models().keys()),
                                value="Qwen/Qwen2.5-Coder-32B-Instruct",  # Default to coding specialist model
                                info="Choose a model for the AI assistant",
                            )

                    with gr.Row():
                        configure_btn = gr.Button("🔧 Configure Model", variant="primary")
                        reset_chat_btn = gr.Button("🔄 Reset Chat", variant="secondary")

                    # Token management section
                    if config_manager.has_secure_storage():
                        with gr.Row():
                            save_token_btn = gr.Button(
                                "💾 Save Token", variant="secondary", size="sm"
                            )
                            clear_token_btn = gr.Button(
                                "🗑️ Clear Saved Token", variant="stop", size="sm"
                            )

                        token_status = gr.Textbox(
                            label="Token Status",
                            value="Checking for saved token...",
                            interactive=False,
                            visible=True,
                        )
                    else:
                        token_status = gr.Textbox(
                            label="Token Status",
                            value="Secure storage not available",
                            interactive=False,
                            visible=True,
                        )

                    config_status = gr.Textbox(
                        label="Configuration Status",
                        value="Not configured - please enter your HuggingFace token and configure a model",
                        interactive=False,
                    )

                    # Model info display
                    model_info = gr.JSON(label="Selected Model Information", visible=False)

                    # Chat interface
                    gr.Markdown("#### Chat Interface")
                    chatbot = gr.Chatbot(
                        label="AI Coding Assistant",
                        height=400,
                        show_copy_button=True,
                        type="messages",
                    )

                    with gr.Row():
                        chat_input = gr.Textbox(
                            label="Message",
                            placeholder="Ask about MCP development, code analysis, or Gradio...",
                            scale=4,
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)
                    
                    with gr.Row():
                        show_thinking = gr.Checkbox(
                            label="🧠 Show AI Thinking Steps", 
                            value=False,
                            info="Display the AI's reasoning process step-by-step"
                        )

                    # Quick action buttons
                    gr.Markdown("#### Quick Actions")
                    with gr.Row():
                        help_mcp_btn = gr.Button("❓ MCP Help", variant="secondary")
                        help_gradio_btn = gr.Button("🎨 Gradio Help", variant="secondary")
                        analyze_btn = gr.Button("🔍 Analyze Code", variant="secondary")
                        best_practices_btn = gr.Button("📋 Best Practices", variant="secondary")

                    # Code analysis section
                    with gr.Accordion("Code Analysis", open=False):
                        code_input = gr.Textbox(
                            label="Code to Analyze",
                            lines=10,
                            placeholder="Paste your code here for analysis...",
                        )
                        language_select = gr.Dropdown(
                            label="Language",
                            choices=["python", "javascript", "typescript", "java", "cpp"],
                            value="python",
                        )
                        analyze_code_btn = gr.Button("🔍 Analyze Code", variant="primary")

                else:
                    gr.Markdown("### AI Assistant Unavailable")
                    if "coding_agent_error" in locals():
                        gr.Markdown(f"**Error:** {coding_agent_error}")
                    gr.Markdown(
                        """
                    To use the AI coding assistant, you need to install the AI dependencies:
                    
                    ```bash
                    pip install -e ".[ai]"
                    ```
                    
                    Or install manually:
                    ```bash
                    pip install llama-index llama-index-llms-huggingface-api llama-index-embeddings-huggingface
                    ```
                    
                    Then restart the dashboard.
                    """
                    )

            # Server Management Tab
            with gr.Tab("🖥️ Server Management"):
                gr.Markdown("### MCP Server Management Dashboard")

                with gr.Tabs():
                    # Available Servers Tab
                    with gr.Tab("📋 Available Servers"):
                        with gr.Row():
                            with gr.Column(scale=3):
                                servers_list = gr.Dataframe(
                                    headers=[
                                        "Name",
                                        "Status",
                                        "Source",
                                        "Command",
                                        "Last Seen",
                                        "Errors",
                                    ],
                                    label="All MCP Servers",
                                    interactive=False,
                                )
                                refresh_servers_btn = gr.Button("🔄 Refresh", variant="secondary")

                            with gr.Column(scale=1):
                                gr.Markdown("### Server Actions")
                                server_dropdown = gr.Dropdown(
                                    label="Select Server", 
                                    choices=[], 
                                    value=None, 
                                    interactive=True,
                                    allow_custom_value=False,
                                    info="Select a server to manage"
                                )
                                selected_server = gr.Textbox(
                                    label="Selected Server", interactive=False
                                )

                                with gr.Row():
                                    start_btn = gr.Button(
                                        "▶️ Start", variant="primary", visible=False
                                    )
                                    stop_btn = gr.Button("⏹️ Stop", variant="stop", visible=False)
                                    refresh_logs_btn = gr.Button(
                                        "📋 View Logs", variant="secondary"
                                    )

                                with gr.Row():
                                    info_btn = gr.Button("ℹ️ Info")
                                    delete_btn = gr.Button("🗑️ Delete", variant="stop")

                        server_info_output = gr.JSON(label="Server Information", visible=False)
                        server_logs_output = gr.Textbox(
                            label="Server Logs", lines=20, visible=False, max_lines=20
                        )

                    # Active Connections Tab
                    with gr.Tab("🔗 Active Connections"):
                        with gr.Row():
                            with gr.Column(scale=3):
                                connections_list = gr.Dataframe(
                                    headers=[
                                        "Name",
                                        "URL",
                                        "Protocol",
                                        "Status",
                                        "Connected Since",
                                    ],
                                    label="Active MCP Connections",
                                    interactive=False,
                                )
                                refresh_connections_btn = gr.Button(
                                    "🔄 Refresh Connections", variant="secondary"
                                )

                            with gr.Column(scale=1):
                                gr.Markdown("### Connection Actions")
                                connection_dropdown = gr.Dropdown(
                                    label="Select Connection",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                )
                                selected_connection = gr.Textbox(
                                    label="Selected Connection", interactive=False
                                )

                                with gr.Row():
                                    disconnect_btn = gr.Button("🔌 Disconnect", variant="stop")
                                    test_conn_btn = gr.Button("🧪 Test", variant="secondary")

                        connection_info_output = gr.JSON(label="Connection Details", visible=False)

                    # Create New Server Tab
                    with gr.Tab("➕ Create Server"):
                        gr.Markdown("### Create New MCP Server")

                        # Template selection
                        with gr.Row():
                            template_dropdown = gr.Dropdown(
                                choices=registry.list_templates(),
                                label="Server Template",
                                value="basic",
                                info="Choose a template for your new server",
                            )
                            template_info_btn = gr.Button("ℹ️ Template Info", variant="secondary")

                        template_info_output = gr.JSON(label="Template Information", visible=False)

                        # Server configuration
                        with gr.Row():
                            new_server_name = gr.Textbox(
                                label="Server Name",
                                placeholder="my-mcp-server",
                                info="Choose a unique name for your server",
                            )
                            create_port = gr.Number(
                                label="Port",
                                value=config_manager.default_port,
                                precision=0,
                                info="Port number for the server (optional)",
                            )

                        create_server_btn = gr.Button(
                            "🚀 Create Server", variant="primary", size="lg"
                        )
                        create_output = gr.Textbox(label="Creation Output", visible=False)

                    # Connect to Server Tab
                    with gr.Tab("🔗 Connect to Server"):
                        gr.Markdown("### Connect to External MCP Server")

                        with gr.Row():
                            with gr.Column():
                                connect_url = gr.Textbox(
                                    label="Server URL",
                                    placeholder="http://localhost:7860",
                                    info="URL of the MCP server to connect to",
                                )
                                connection_name = gr.Textbox(
                                    label="Connection Name",
                                    placeholder="my-server-connection",
                                    info="Name for this connection (optional)",
                                )
                                connection_protocol = gr.Dropdown(
                                    choices=["auto", "stdio", "sse"],
                                    label="Protocol",
                                    value="auto",
                                    info="Communication protocol to use",
                                )

                            with gr.Column():
                                gr.Markdown("#### Quick Actions")
                                test_server_btn = gr.Button(
                                    "🧪 Test Connection", variant="secondary"
                                )
                                connect_server_btn = gr.Button("🔗 Connect", variant="primary")

                        connection_output = gr.Textbox(label="Connection Output", visible=False)

            # Registry Tab
            with gr.Tab("📦 Registry"):
                gr.Markdown("### Browse Available MCP Servers")

                with gr.Row():
                    search_query = gr.Textbox(
                        label="Search", placeholder="Search for servers...", scale=3
                    )
                    category_filter = gr.Dropdown(
                        choices=["all"] + registry.list_categories(),
                        label="Category",
                        value="all",
                        scale=1,
                    )

                search_btn = gr.Button("🔍 Search", variant="primary")

                search_results = gr.JSON(label="Search Results")

                # Server details
                with gr.Row():
                    selected_registry_server = gr.Textbox(label="Selected Server ID", visible=False)
                    install_from_registry_btn = gr.Button(
                        "📥 Install Selected", variant="primary", visible=False
                    )

            # Tools Testing Tab
            with gr.Tab("🧪 Tool Testing"):
                gr.Markdown("### Test MCP Tools")

                with gr.Row():
                    test_server_url = gr.Textbox(
                        label="Server URL", placeholder="http://localhost:7860"
                    )
                    test_protocol = gr.Dropdown(
                        choices=["auto", "stdio", "sse"], label="Protocol", value="auto"
                    )
                    connect_test_btn = gr.Button("🔗 Connect", variant="primary")

                tools_list = gr.JSON(label="Available Tools", visible=False)

                with gr.Row():
                    tool_name = gr.Textbox(label="Tool Name")
                    tool_args = gr.Textbox(
                        label="Arguments (JSON)", placeholder='{"param": "value"}', lines=3
                    )

                call_tool_btn = gr.Button("🚀 Call Tool", variant="primary")
                tool_result = gr.JSON(label="Tool Result")

            # MCP Connections Tab
            with gr.Tab("🔌 MCP Connections"):
                gr.Markdown("### 🔌 Multiple MCP Server Connections")
                gr.Markdown("Connect to multiple MCP servers simultaneously for enhanced capabilities")
                
                # Predefined MCP server configurations
                predefined_servers = {
                    "memory": {
                        "name": "Memory Server",
                        "url": "python -m mcp_server_memory",
                        "protocol": "stdio",
                        "description": "Persistent memory storage for conversations and data",
                        "icon": "🧠"
                    },
                    "sequential-thinking": {
                        "name": "Sequential Thinking",
                        "url": "python -m mcp_server_sequential_thinking",
                        "protocol": "stdio", 
                        "description": "Step-by-step reasoning and problem solving",
                        "icon": "🤔"
                    },
                    "filesystem": {
                        "name": "File System",
                        "url": "npx @modelcontextprotocol/server-filesystem /",
                        "protocol": "stdio",
                        "description": "File system access and manipulation",
                        "icon": "📁"
                    },
                    "brave-search": {
                        "name": "Brave Search",
                        "url": "python -m mcp_server_brave_search",
                        "protocol": "stdio",
                        "description": "Web search capabilities using Brave",
                        "icon": "🔍"
                    },
                    "github": {
                        "name": "GitHub",
                        "url": "python -m mcp_server_github",
                        "protocol": "stdio",
                        "description": "GitHub repository and issue management",
                        "icon": "🐙"
                    },
                    "time": {
                        "name": "Time Server",
                        "url": "python -m mcp_server_time",
                        "protocol": "stdio",
                        "description": "Time and date utilities",
                        "icon": "⏰"
                    }
                }

                with gr.Tabs():
                    # Quick Connect Tab
                    with gr.Tab("⚡ Quick Connect"):
                        gr.Markdown("### 🚀 Quick Connect to Common MCP Servers")
                        
                        # Connection status states for each server
                        server_statuses = {}
                        server_buttons = {}
                        
                        # Create cards for first 3 servers
                        server_install_buttons = {}
                        with gr.Row():
                            for i, (server_id, server_info) in enumerate(list(predefined_servers.items())[:3]):
                                with gr.Column():
                                    with gr.Group():
                                        gr.Markdown(f"### {server_info['icon']} {server_info['name']}")
                                        gr.Markdown(server_info['description'])
                                        
                                        server_statuses[server_id] = gr.Textbox(
                                            label="Status",
                                            value="Not Connected",
                                            interactive=False,
                                            elem_id=f"status_{server_id}"
                                        )
                                        
                                        with gr.Row():
                                            server_buttons[server_id] = gr.Button(
                                                f"Connect",
                                                variant="primary",
                                                elem_id=f"connect_{server_id}",
                                                scale=1
                                            )
                                            
                                            server_install_buttons[server_id] = gr.Button(
                                                f"Auto-Install & Connect",
                                                variant="secondary",
                                                elem_id=f"install_{server_id}",
                                                scale=1
                                            )
                        
                        # Create cards for remaining servers
                        with gr.Row():
                            for i, (server_id, server_info) in enumerate(list(predefined_servers.items())[3:]):
                                with gr.Column():
                                    with gr.Group():
                                        gr.Markdown(f"### {server_info['icon']} {server_info['name']}")
                                        gr.Markdown(server_info['description'])
                                        
                                        server_statuses[server_id] = gr.Textbox(
                                            label="Status",
                                            value="Not Connected",
                                            interactive=False,
                                            elem_id=f"status_{server_id}"
                                        )
                                        
                                        with gr.Row():
                                            server_buttons[server_id] = gr.Button(
                                                f"Connect",
                                                variant="primary",
                                                elem_id=f"connect_{server_id}",
                                                scale=1
                                            )
                                            
                                            server_install_buttons[server_id] = gr.Button(
                                                f"Auto-Install & Connect",
                                                variant="secondary",
                                                elem_id=f"install_{server_id}",
                                                scale=1
                                            )
                        
                        # Bulk actions
                        with gr.Row():
                            connect_all_mcp_btn = gr.Button("🔗 Connect All", variant="primary")
                            disconnect_all_mcp_btn = gr.Button("🔌 Disconnect All", variant="stop")
                            refresh_mcp_status_btn = gr.Button("🔄 Refresh Status")
                        
                        mcp_bulk_status = gr.Textbox(
                            label="Bulk Action Status",
                            interactive=False,
                            lines=3
                        )
                        
                        # Installation progress display
                        gr.Markdown("### 📦 Installation Progress")
                        mcp_install_progress = gr.Textbox(
                            label="Installation Progress",
                            interactive=False,
                            lines=8,
                            visible=False
                        )

                    # Active MCP Connections Tab
                    with gr.Tab("🔗 Active MCP Connections"):
                        gr.Markdown("### 📊 Active MCP Server Connections")
                        
                        # MCP Connection list
                        mcp_connections_table = gr.Dataframe(
                            headers=["Server", "Type", "Status", "Tools", "URL"],
                            datatype=["str", "str", "str", "number", "str"],
                            interactive=False,
                            label="Active MCP Connections"
                        )
                        
                        # MCP Connection details
                        with gr.Row():
                            with gr.Column(scale=2):
                                selected_mcp_connection = gr.Dropdown(
                                    label="Select MCP Connection",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                    allow_custom_value=True
                                )
                                
                                mcp_connection_details = gr.JSON(
                                    label="Connection Details",
                                    value={}
                                )
                                
                                mcp_available_tools = gr.Dataframe(
                                    headers=["Tool Name", "Description", "Parameters"],
                                    datatype=["str", "str", "str"],
                                    interactive=False,
                                    label="Available Tools"
                                )
                            
                            with gr.Column(scale=1):
                                gr.Markdown("### Actions")
                                
                                test_mcp_connection_btn = gr.Button("🧪 Test Connection")
                                disconnect_mcp_btn = gr.Button("🔌 Disconnect", variant="stop")
                                reconnect_mcp_btn = gr.Button("🔄 Reconnect")
                                
                                gr.Markdown("### Tool Testing")
                                
                                mcp_tool_name = gr.Dropdown(
                                    label="Select Tool",
                                    choices=[],
                                    interactive=True
                                )
                                
                                mcp_tool_args = gr.JSON(
                                    label="Tool Arguments",
                                    value={}
                                )
                                
                                call_mcp_tool_btn = gr.Button("📞 Call Tool", variant="primary")
                                
                                mcp_tool_result = gr.JSON(
                                    label="Tool Result",
                                    value={}
                                )

                    # Custom MCP Connection Tab
                    with gr.Tab("➕ Custom MCP Connection"):
                        gr.Markdown("### 🔧 Connect to Custom MCP Server")
                        
                        with gr.Row():
                            with gr.Column():
                                custom_mcp_name = gr.Textbox(
                                    label="Connection Name",
                                    placeholder="my-custom-server",
                                    value=""
                                )
                                
                                custom_mcp_url = gr.Textbox(
                                    label="Server URL/Command",
                                    placeholder="python -m my_mcp_server or http://localhost:8080/mcp",
                                    value="",
                                    lines=2
                                )
                                
                                custom_mcp_protocol = gr.Radio(
                                    label="Protocol",
                                    choices=["auto", "stdio", "sse", "gradio"],
                                    value="auto"
                                )
                                
                                custom_mcp_description = gr.Textbox(
                                    label="Description (optional)",
                                    placeholder="What does this server do?",
                                    value="",
                                    lines=2
                                )
                                
                                custom_mcp_connect_btn = gr.Button("🔗 Connect", variant="primary")
                            
                            with gr.Column():
                                gr.Markdown("### 📖 Connection Guide")
                                gr.Markdown("""
                                **Supported Protocols:**
                                - **stdio**: Command-line MCP servers (e.g., `python -m server`)
                                - **sse**: HTTP SSE endpoints (e.g., `http://localhost:8080/mcp`)
                                - **gradio**: Gradio server endpoints
                                - **auto**: Automatically detect protocol
                                
                                **Examples:**
                                - Memory: `python -m mcp_server_memory`
                                - Custom script: `python /path/to/my_server.py`
                                - HTTP endpoint: `http://localhost:8080/mcp/sse`
                                - Gradio app: `http://localhost:7860`
                                """)
                        
                        custom_mcp_status = gr.Textbox(
                            label="Connection Status",
                            interactive=False,
                            lines=3
                        )

            # Settings Tab
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### Gradio MCP Playground Settings")

                with gr.Column():
                    settings_port = gr.Number(
                        label="Default Port", value=config_manager.default_port, precision=0
                    )
                    settings_auto_reload = gr.Checkbox(
                        label="Auto-reload on file changes", value=config_manager.auto_reload
                    )
                    settings_protocol = gr.Dropdown(
                        choices=["auto", "stdio", "sse"],
                        label="Default MCP Protocol",
                        value=config_manager.mcp_protocol,
                    )
                    settings_log_level = gr.Dropdown(
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        label="Log Level",
                        value=config_manager.log_level,
                    )
                    settings_hf_token = gr.Textbox(
                        label="Hugging Face Token (for deployment)",
                        type="password",
                        value=config_manager.hf_token or "",
                    )

                save_settings_btn = gr.Button("💾 Save Settings", variant="primary")
                settings_output = gr.Textbox(label="Settings Output", visible=False)

        # Event handlers

        # AI Assistant event handlers
        def test_hf_token_only(hf_token):
            """Test HuggingFace token without LlamaIndex"""
            import requests

            clean_token = hf_token.strip()
            headers = {
                "Authorization": f"Bearer {clean_token}",
                "Content-Type": "application/json",
                "User-Agent": "gradio-mcp-playground/0.1.0",
            }

            try:
                # Test model access first (more reliable than whoami for some tokens)
                test_model = "microsoft/DialoGPT-medium"
                model_url = f"https://huggingface.co/api/models/{test_model}"
                model_response = requests.get(model_url, headers=headers, timeout=10)

                if model_response.status_code == 200:
                    # Try whoami as secondary validation
                    try:
                        response = requests.get(
                            "https://huggingface.co/api/whoami", headers=headers, timeout=5
                        )
                        if response.status_code == 200:
                            user_info = response.json()
                            return True, f"Token valid for user: {user_info.get('name', 'Unknown')}"
                        else:
                            return (
                                True,
                                "Token valid (can access models, whoami endpoint has limited permissions)",
                            )
                    except:
                        return True, "Token valid (can access models)"
                else:
                    return (
                        False,
                        f"Cannot access models: {model_response.status_code} - {model_response.text[:100]}",
                    )

            except Exception as e:
                return False, f"Network error: {str(e)}"

        if coding_agent:

            def configure_model(hf_token, model_name):
                """Configure the AI model"""
                if not hf_token.strip():
                    return "Please enter a valid HuggingFace API token", gr.update(visible=False)

                # First test the token independently
                token_valid, token_msg = test_hf_token_only(hf_token)
                if not token_valid:
                    return f"❌ Token Error: {token_msg}", gr.update(visible=False)

                result = coding_agent.configure_model(hf_token.strip(), model_name)

                if result["success"]:
                    # Save token securely if configuration was successful
                    if config_manager.has_secure_storage():
                        config_manager.save_secure_token("huggingface", hf_token.strip())

                    model_details = coding_agent.get_available_models()[model_name]
                    status_msg = f"✅ Configured: {result['model']}\n{result['description']}"

                    # Enhanced model details for display
                    enhanced_details = {
                        "name": model_details["name"],
                        "description": model_details["description"],
                        "context_window": f"{model_details['context_window']:,} tokens",
                        "size": model_details.get("size", "Unknown"),
                        "strengths": model_details.get("strengths", []),
                        "status": "✅ Ready for coding assistance",
                    }

                    return status_msg, gr.update(visible=True, value=enhanced_details)
                else:
                    return f"❌ Error: {result['error']}", gr.update(visible=False)

        else:

            def configure_model(hf_token, model_name):
                """Test token when LlamaIndex not available"""
                if not hf_token.strip():
                    return "Please enter a valid HuggingFace API token", gr.update(visible=False)

                token_valid, token_msg = test_hf_token_only(hf_token)
                if token_valid:
                    return (
                        f"✅ Token is valid! {token_msg}\nInstall LlamaIndex to use the AI assistant.",
                        gr.update(visible=False),
                    )
                else:
                    return f"❌ {token_msg}", gr.update(visible=False)

        if coding_agent:

            def send_message(message, history, show_thinking_steps):
                """Send message to AI assistant"""
                if not coding_agent.is_configured():
                    bot_response = (
                        "Please configure a model first by providing your HuggingFace token."
                    )
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": bot_response})
                    return history, ""
                
                if show_thinking_steps:
                    # Use the detailed method that shows thinking steps
                    steps, bot_response = coding_agent.chat_with_steps(message)
                    
                    # Combine thinking steps with final response
                    if steps:
                        thinking_section = "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                        full_response = thinking_section + "## 💬 Final Response\n\n" + bot_response
                    else:
                        full_response = bot_response
                else:
                    # Use the regular chat method
                    full_response = coding_agent.chat(message)

                # Convert to messages format for new Gradio chatbot
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": full_response})
                return history, ""

            def reset_conversation():
                """Reset the conversation"""
                if coding_agent:
                    coding_agent.reset_conversation()
                return []

            def quick_mcp_help(history, show_thinking_steps):
                """Quick MCP help"""
                message = "What is MCP and how do I get started with MCP development?"
                if coding_agent.is_configured():
                    if show_thinking_steps:
                        steps, response = coding_agent.chat_with_steps(message)
                        if steps:
                            thinking_section = "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            response = thinking_section + "## 💬 Final Response\n\n" + response
                    else:
                        response = coding_agent.chat(message)
                else:
                    response = "Please configure a model first."
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return history

            def quick_gradio_help(history, show_thinking_steps):
                """Quick Gradio help"""
                message = (
                    "How do I create a basic Gradio interface and what are the main components?"
                )
                if coding_agent.is_configured():
                    if show_thinking_steps:
                        steps, response = coding_agent.chat_with_steps(message)
                        if steps:
                            thinking_section = "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            response = thinking_section + "## 💬 Final Response\n\n" + response
                    else:
                        response = coding_agent.chat(message)
                else:
                    response = "Please configure a model first."
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return history

            def quick_analyze_help(history, show_thinking_steps):
                """Quick code analysis help"""
                message = "How can I analyze my code for potential issues and improvements?"
                if coding_agent.is_configured():
                    if show_thinking_steps:
                        steps, response = coding_agent.chat_with_steps(message)
                        if steps:
                            thinking_section = "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            response = thinking_section + "## 💬 Final Response\n\n" + response
                    else:
                        response = coding_agent.chat(message)
                else:
                    response = "Please configure a model first."
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return history

            def quick_best_practices(history, show_thinking_steps):
                """Quick best practices"""
                message = "What are the best practices for MCP server development?"
                if coding_agent.is_configured():
                    if show_thinking_steps:
                        steps, response = coding_agent.chat_with_steps(message)
                        if steps:
                            thinking_section = "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            response = thinking_section + "## 💬 Final Response\n\n" + response
                    else:
                        response = coding_agent.chat(message)
                else:
                    response = "Please configure a model first."
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return history

            def analyze_code_directly(code, language, history, show_thinking_steps):
                """Analyze code directly"""
                if not code.strip():
                    return history

                message = f"Please analyze this {language} code for issues and improvements:\n\n```{language}\n{code}\n```"
                if coding_agent.is_configured():
                    if show_thinking_steps:
                        steps, response = coding_agent.chat_with_steps(message)
                        if steps:
                            thinking_section = "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            response = thinking_section + "## 💬 Final Response\n\n" + response
                    else:
                        response = coding_agent.chat(message)
                else:
                    response = "Please configure a model first."

                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return history

        def update_server_dropdown():
            """Update the server dropdown with current servers"""
            try:
                servers = config_manager.list_servers()
                server_names = [server.get("name", "Unknown") for server in servers]
                # Ensure we always return a valid state
                if not server_names:
                    return gr.update(choices=[], value=None)
                else:
                    return gr.update(choices=server_names, value=None)
            except Exception as e:
                print(f"DEBUG: Error updating server dropdown: {e}")
                return gr.update(choices=[], value=None)

        def on_server_dropdown_change(selected_name):
            """Handle server selection from dropdown"""
            print(f"DEBUG: Selected server from dropdown: {selected_name}")

            # Check if this is a Claude Desktop server
            servers = config_manager.list_servers()
            selected_server = None
            for server in servers:
                if server.get("name") == selected_name:
                    selected_server = server
                    break

            # Show/hide start/stop buttons based on server source
            if selected_server and selected_server.get("source") == "claude_desktop":
                return selected_name, gr.update(visible=False), gr.update(visible=False)
            else:
                return selected_name, gr.update(visible=True), gr.update(visible=True)

        def refresh_servers():
            """Refresh the servers list"""
            servers = config_manager.list_servers()
            data = []
            for server in servers:
                # Determine status with appropriate emoji
                status = server.get("status_message", "Unknown")
                if server.get("running"):
                    if server.get("source") == "claude_desktop":
                        status_display = f"🟢 {status}"
                    else:
                        status_display = "🟢 Running"
                elif server.get("errors"):
                    status_display = f"🔴 {status}"
                else:
                    status_display = f"⚫ {status}"

                # Format source
                source = server.get("source", "local")
                source_display = "Claude Desktop" if source == "claude_desktop" else "Local"

                # Format command for display
                command = server.get("command", server.get("path", "N/A"))
                if server.get("args"):
                    command += f" {' '.join(server.get('args', [])[:2])}{'...' if len(server.get('args', [])) > 2 else ''}"
                if len(command) > 50:
                    command = command[:47] + "..."

                # Format last seen
                last_seen = server.get("last_seen")
                if last_seen:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                        last_seen_display = dt.strftime("%H:%M:%S")
                    except:
                        last_seen_display = "Recent"
                else:
                    last_seen_display = "N/A"

                # Format errors
                errors = server.get("errors", [])
                error_display = f"{len(errors)} errors" if errors else "None"

                data.append(
                    [
                        server.get("name", "Unknown"),
                        status_display,
                        source_display,
                        command,
                        last_seen_display,
                        error_display,
                    ]
                )
            return data

        def refresh_connections():
            """Refresh the connections list"""
            if connection_manager:
                connections = connection_manager.list_connections()
                data = []
                for conn in connections:
                    status = "🟢 Connected" if conn.get("connected") else "⚫ Disconnected"
                    data.append(
                        [
                            conn.get("name", "Unknown"),
                            conn.get("url", "N/A"),
                            conn.get("protocol", "auto"),
                            status,
                        ]
                    )
                return data
            else:
                return []

        def create_server(name, template, port):
            """Create a new server"""
            try:
                if not name:
                    return gr.update(visible=True, value="❌ Server name is required")

                # Create server directory
                server_dir = Path.cwd() / name

                # Create from template
                server_config = registry.create_from_template(template, name, server_dir, port=port)

                # Register server
                config_manager.add_server(server_config)

                return gr.update(
                    visible=True,
                    value=f"✅ Server '{name}' created successfully!\n\nLocation: {server_dir}",
                )
            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error: {str(e)}")

        def start_server(selected):
            """Start a selected server (only for local servers)"""
            if not selected:
                return

            server = config_manager.get_server(selected)
            if server and server.get("source") != "claude_desktop":
                if HAS_SERVER_MANAGER:
                    server_mgr = GradioMCPServer(Path(server["path"]))
                    server_mgr.start(port=server.get("port", 7860))
            return refresh_servers()

        def stop_server(selected):
            """Stop a selected server (only for local servers)"""
            if not selected:
                return

            server = config_manager.get_server(selected)
            if server and server.get("source") != "claude_desktop":
                if HAS_SERVER_MANAGER:
                    server_mgr = GradioMCPServer(Path(server["path"]))
                    server_mgr.stop()
            return refresh_servers()

        def show_server_info(selected):
            """Show detailed server information"""
            if not selected:
                return gr.update(visible=False)

            servers = config_manager.list_servers()
            server = None
            for s in servers:
                if s.get("name") == selected:
                    server = s
                    break

            if server:
                # Enhanced info display with status and errors
                info = {
                    "name": server.get("name"),
                    "source": server.get("source", "local"),
                    "status": server.get("status_message", "Unknown"),
                    "running": server.get("running", False),
                    "last_seen": server.get("last_seen"),
                    "command": server.get("command"),
                    "args": server.get("args"),
                    "env": server.get("env"),
                    "errors": server.get("errors", []),
                    "path": server.get("path"),
                    "port": server.get("port"),
                    "template": server.get("template"),
                }
                return gr.update(visible=True, value=info)
            return gr.update(visible=False)

        def delete_server(selected):
            """Delete a selected server (only for local servers)"""
            if not selected:
                return refresh_servers()

            try:
                # Check if this is a Claude Desktop server
                servers = config_manager.list_servers()
                selected_server = None
                for server in servers:
                    if server.get("name") == selected:
                        selected_server = server
                        break

                # Don't allow deletion of Claude Desktop servers
                if selected_server and selected_server.get("source") == "claude_desktop":
                    return refresh_servers()

                # Get server config to find directory (for local servers)
                server_config = config_manager.get_server(selected)
                if not server_config:
                    return refresh_servers()

                # Remove from registry
                success = config_manager.remove_server(selected)

                if success and HAS_SERVER_MANAGER:
                    # Also delete files if directory exists
                    server_directory = server_config.get("directory")
                    if server_directory and Path(server_directory).exists():
                        try:
                            result = GradioMCPServer.delete_server(
                                Path(server_directory),
                                force=True,  # In UI, we force deletion for simplicity
                            )
                            # Note: In a more sophisticated UI, we'd show a confirmation dialog
                        except Exception:
                            pass  # If file deletion fails, we already removed from registry

                return refresh_servers()
            except Exception:
                return refresh_servers()

        def view_server_logs(selected):
            """View logs for the selected server"""
            if not selected:
                return "No server selected"

            servers = config_manager.list_servers()
            server = None
            for s in servers:
                if s.get("name") == selected:
                    server = s
                    break

            if not server:
                return "Server not found"

            logs_content = ""

            if server.get("source") == "claude_desktop":
                # Read Claude Desktop logs
                import os

                if os.name == "nt":
                    # Native Windows
                    claude_logs_path = Path.home() / "AppData/Roaming/Claude/logs"
                else:
                    # WSL or Linux - look for Windows user directory
                    # Try multiple possible usernames
                    possible_users = [
                        os.environ.get("USER", ""),
                        os.environ.get("USERNAME", ""),
                        "seanp",  # fallback
                    ]

                    claude_logs_path = None
                    for user in possible_users:
                        if user:
                            logs_path = Path(f"/mnt/c/Users/{user}/AppData/Roaming/Claude/logs")
                            if logs_path.exists():
                                claude_logs_path = logs_path
                                break

                    if not claude_logs_path:
                        logs_content = "Claude Desktop logs directory not found"
                        return logs_content

                log_file = claude_logs_path / f"mcp-server-{selected}.log"

                if log_file.exists():
                    try:
                        with open(log_file, encoding="utf-8") as f:
                            lines = f.readlines()
                            # Show last 50 lines
                            recent_lines = lines[-50:] if len(lines) > 50 else lines
                            logs_content = "".join(recent_lines)
                    except Exception as e:
                        logs_content = f"Error reading log file: {str(e)}"
                else:
                    logs_content = "No log file found for this server"
            else:
                # For local servers, check if there's a log file
                server_path = server.get("path")
                if server_path:
                    log_file = Path(server_path).parent / "server.log"
                    if log_file.exists():
                        try:
                            with open(log_file, encoding="utf-8") as f:
                                logs_content = f.read()
                        except Exception as e:
                            logs_content = f"Error reading log file: {str(e)}"
                    else:
                        logs_content = "No log file found for this local server"
                else:
                    logs_content = "Server path not configured"

            return logs_content

        def search_registry(query, category):
            """Search the server registry"""
            if category == "all":
                category = None

            if query:
                results = registry.search(query, category)
            elif category:
                results = registry.get_by_category(category)
            else:
                results = registry.get_all()

            return results

        def test_connection(url, protocol):
            """Test a connection to an MCP server"""
            if not HAS_CLIENT_MANAGER:
                return gr.update(visible=True, value={"error": "Client manager not available"})

            try:
                result = GradioMCPClient.test_connection(url, protocol)
                if result["success"]:
                    return gr.update(visible=True, value=result["tools"])
                else:
                    return gr.update(visible=True, value={"error": result["error"]})
            except Exception as e:
                return gr.update(visible=True, value={"error": str(e)})

        def call_tool(url, protocol, tool_name, args_json):
            """Call a tool on an MCP server"""
            if not HAS_CLIENT_MANAGER:
                return {"success": False, "error": "Client manager not available"}

            try:
                args = json.loads(args_json) if args_json else {}

                client = GradioMCPClient()
                client.connect(url, protocol)
                result = client.call_tool(tool_name, args)
                client.disconnect()

                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def save_token_manually(hf_token):
            """Save token manually to secure storage"""
            if not config_manager.has_secure_storage():
                return "❌ Secure storage not available"

            if not hf_token.strip():
                return "❌ Please enter a token to save"

            success = config_manager.save_secure_token("huggingface", hf_token.strip())
            if success:
                return "✅ Token saved securely"
            else:
                return "❌ Failed to save token"

        def clear_saved_token():
            """Clear saved token from secure storage"""
            if not config_manager.has_secure_storage():
                return "❌ Secure storage not available", ""

            success = config_manager.delete_secure_token("huggingface")
            if success:
                return "🗑️ Token cleared from secure storage", ""
            else:
                return "❌ Failed to clear token", ""

        def load_saved_token_on_startup():
            """Load saved token and update UI on startup"""
            if not config_manager.has_secure_storage():
                return "", "Secure storage not available"

            saved_token = config_manager.load_secure_token("huggingface")
            if saved_token:
                return saved_token, "✅ Token loaded from secure storage"
            else:
                return "", "No saved token found"

        def refresh_connections():
            """Refresh the active connections list"""
            if connection_manager:
                connections = connection_manager.list_connections()
                data = []
                for conn in connections:
                    status = "🟢 Connected" if conn.get("connected") else "⚫ Disconnected"
                    connected_since = conn.get("connected_since", "Unknown")
                    data.append(
                        [
                            conn.get("name", "Unknown"),
                            conn.get("url", "N/A"),
                            conn.get("protocol", "auto"),
                            status,
                            connected_since,
                        ]
                    )
                return data
            else:
                return []

        def get_template_info(template_name):
            """Get information about a server template"""
            try:
                template_info = registry.get_template_info(template_name)
                if template_info:
                    return gr.update(visible=True, value=template_info)
                else:
                    return gr.update(
                        visible=True, value={"error": f"Template '{template_name}' not found"}
                    )
            except Exception as e:
                return gr.update(visible=True, value={"error": str(e)})

        def test_server_connection(url, protocol):
            """Test connection to a server"""
            if not HAS_CLIENT_MANAGER:
                return gr.update(visible=True, value="❌ Client manager not available")

            try:
                result = GradioMCPClient.test_connection(url, protocol)
                if result["success"]:
                    return gr.update(
                        visible=True,
                        value=f"✅ Connection successful:\n{json.dumps(result, indent=2)}",
                    )
                else:
                    return gr.update(visible=True, value=f"❌ Connection failed: {result['error']}")
            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error testing connection: {str(e)}")

        def connect_to_server(url, name, protocol):
            """Connect to an MCP server"""
            if not HAS_CLIENT_MANAGER:
                return gr.update(visible=True, value="❌ Client manager not available")

            try:
                if connection_manager:
                    # Use the connection name or generate one from URL
                    conn_name = (
                        name if name.strip() else f"server-{url.split('//')[-1].replace(':', '-')}"
                    )

                    # Test connection first
                    result = GradioMCPClient.test_connection(url, protocol)
                    if result["success"]:
                        # Save the connection
                        connection_manager.save_connection(conn_name, url, protocol)
                        return gr.update(
                            visible=True, value=f"✅ Connected to '{conn_name}' at {url}"
                        )
                    else:
                        return gr.update(
                            visible=True, value=f"❌ Failed to connect: {result['error']}"
                        )
                else:
                    return gr.update(visible=True, value="❌ Connection manager not available")
            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error connecting: {str(e)}")

        def disconnect_from_server(connection_name):
            """Disconnect from a server"""
            if not connection_manager:
                return "❌ Connection manager not available"

            try:
                # Remove the connection
                success = connection_manager.remove_connection(connection_name)
                if success:
                    return f"🔌 Disconnected from '{connection_name}'"
                else:
                    return f"❌ Failed to disconnect from '{connection_name}'"
            except Exception as e:
                return f"❌ Error disconnecting: {str(e)}"

        def update_connection_dropdown():
            """Update the connection dropdown with current connections"""
            if connection_manager:
                connections = connection_manager.list_connections()
                connection_names = [conn.get("name", "Unknown") for conn in connections]
                return gr.update(choices=connection_names, value=None)
            else:
                return gr.update(choices=[], value=None)

        def on_connection_dropdown_change(selected_name):
            """Handle connection selection from dropdown"""
            return selected_name

        def save_settings(port, auto_reload, protocol, log_level, hf_token):
            """Save settings"""
            try:
                config_manager.set("default_port", port)
                config_manager.set("auto_reload", auto_reload)
                config_manager.set("mcp_protocol", protocol)
                config_manager.set("log_level", log_level)
                if hf_token:
                    config_manager.set("hf_token", hf_token)

                return gr.update(visible=True, value="✅ Settings saved successfully!")
            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error: {str(e)}")

        # MCP Connection functions
        def install_and_connect_mcp(server_id):
            """Install MCP server package and connect"""
            import subprocess
            import time
            
            server_info = predefined_servers.get(server_id)
            if not server_info:
                return "❌ Unknown server"
            
            # For now, let's focus on getting filesystem working since it shows potential
            if server_id == "filesystem":
                progress = f"📦 Installing {server_info['name']}...\n"
                
                # Check if we have Node.js for filesystem server
                try:
                    node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
                    if node_result.returncode != 0:
                        return progress + "❌ Node.js not found. Please install Node.js first: https://nodejs.org/"
                    
                    progress += f"✅ Node.js detected: {node_result.stdout.strip()}\n"
                    
                    # Check if npm is available
                    npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10, shell=True)
                    if npm_result.returncode != 0:
                        return progress + f"❌ npm not found. Node.js is installed but npm is missing.\n\nTry:\n1. Restart your terminal/PowerShell as Administrator\n2. Or reinstall Node.js from https://nodejs.org/\n3. Or check PATH: where npm"
                    
                    progress += f"✅ npm detected: {npm_result.stdout.strip()}\n"
                    
                    # Install the filesystem server
                    progress += "📦 Installing @modelcontextprotocol/server-filesystem...\n"
                    
                    install_result = subprocess.run(
                        ["npm", "install", "-g", "@modelcontextprotocol/server-filesystem"],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        shell=True  # Use shell on Windows to help find npm
                    )
                    
                    if install_result.returncode != 0:
                        stderr_output = install_result.stderr or "No error details"
                        stdout_output = install_result.stdout or "No output"
                        return progress + f"❌ Installation failed:\n\nSTDERR:\n{stderr_output}\n\nSTDOUT:\n{stdout_output}\n\nTry running this command manually in your terminal:\nnpm install -g @modelcontextprotocol/server-filesystem"
                    
                    progress += "✅ Package installed successfully!\n\n"
                    progress += "🔌 Testing filesystem access...\n"
                    
                    # Test basic filesystem access
                    import os
                    test_dir = os.getcwd()
                    files = os.listdir(test_dir)
                    
                    progress += f"✅ Filesystem access working - found {len(files)} items in current directory\n\n"
                    
                    # Store connection info
                    if not hasattr(quick_connect_mcp, 'connections'):
                        quick_connect_mcp.connections = {}
                    
                    quick_connect_mcp.connections[server_id] = {
                        'name': server_info['name'],
                        'url': server_info['url'],
                        'protocol': server_info['protocol'],
                        'status': 'connected',
                        'tools': ['read_file', 'write_file', 'list_directory', 'create_directory']
                    }
                    
                    # Connect to coding agent if available
                    if coding_agent:
                        progress += "🤖 Connecting to coding agent...\n"
                        try:
                            coding_agent.add_mcp_connection(server_id, {
                                'name': server_info['name'],
                                'tools': ['read_file', 'write_file', 'list_directory', 'create_directory']
                            })
                            progress += "✅ Connected to coding agent!\n\n"
                        except Exception as e:
                            progress += f"⚠️ Coding agent connection failed: {str(e)}\n\n"
                    
                    progress += "🎉 Filesystem server setup completed successfully!\n"
                    progress += "You can now use filesystem tools in the AI Assistant."
                    
                    return progress
                    
                except FileNotFoundError:
                    # If npm/node not found, fall back to Python-only filesystem
                    progress += "⚠️ Node.js/npm not found, using Python filesystem instead...\n\n"
                    
                    # Test basic filesystem access
                    try:
                        import os
                        test_dir = os.getcwd()
                        files = os.listdir(test_dir)
                        
                        progress += f"✅ Python filesystem access working - found {len(files)} items in current directory\n\n"
                        
                        # Store connection info
                        if not hasattr(quick_connect_mcp, 'connections'):
                            quick_connect_mcp.connections = {}
                        
                        quick_connect_mcp.connections[server_id] = {
                            'name': server_info['name'],
                            'url': server_info['url'],
                            'protocol': server_info['protocol'],
                            'status': 'connected',
                            'tools': ['read_file', 'write_file', 'list_directory', 'create_directory']
                        }
                        
                        # Connect to coding agent if available
                        if coding_agent:
                            progress += "🤖 Connecting to coding agent...\n"
                            try:
                                coding_agent.add_mcp_connection(server_id, {
                                    'name': server_info['name'],
                                    'tools': ['read_file', 'write_file', 'list_directory', 'create_directory']
                                })
                                progress += "✅ Connected to coding agent!\n\n"
                            except Exception as e:
                                progress += f"⚠️ Coding agent connection failed: {str(e)}\n\n"
                        
                        progress += "🎉 Python filesystem server setup completed successfully!\n"
                        progress += "You can now use filesystem tools in the AI Assistant."
                        
                        return progress
                        
                    except Exception as e:
                        return progress + f"❌ Python filesystem error: {str(e)}"
                        
                except subprocess.TimeoutExpired:
                    return progress + "❌ Installation timed out"
                except Exception as e:
                    return progress + f"❌ Error: {str(e)}"
            
            else:
                # For other servers, show installation command
                install_commands = {
                    "memory": "pip install mcp-server-memory",
                    "sequential-thinking": "pip install mcp-server-sequential-thinking", 
                    "brave-search": "pip install mcp-server-brave-search",
                    "github": "pip install mcp-server-github",
                    "time": "pip install mcp-server-time"
                }
                
                cmd = install_commands.get(server_id, f"pip install mcp-server-{server_id}")
                
                return f"""📦 To install {server_info['name']}, run:

{cmd}

Then restart the dashboard and click 'Connect' to use the server.

Note: Auto-install is currently only implemented for the filesystem server.
For others, please install manually using the command above."""

        def quick_connect_mcp(server_id):
            """Quick connect to a predefined MCP server (with auto-install option)"""
            if not HAS_CLIENT_MANAGER:
                return "❌ MCP client manager not available"
            
            try:
                server_info = predefined_servers.get(server_id)
                if not server_info:
                    return "❌ Unknown server"
                
                # Try to connect using the actual MCP client
                try:
                    # Use the existing connection manager to make a real MCP connection
                    result = GradioMCPClient.test_connection(server_info['url'], server_info['protocol'])
                    
                    if result.get("success"):
                        # Store the connection info
                        if not hasattr(quick_connect_mcp, 'connections'):
                            quick_connect_mcp.connections = {}
                        
                        # Save the connection for reuse
                        connection_manager.save_connection(server_id, server_info['url'], server_info['protocol'])
                        
                        # Get available tools from the connection
                        tools = result.get("tools", [])
                        tool_names = [tool.get("name", "unknown") for tool in tools] if tools else []
                        
                        quick_connect_mcp.connections[server_id] = {
                            'name': server_info['name'],
                            'url': server_info['url'],
                            'protocol': server_info['protocol'],
                            'status': 'connected',
                            'tools': tool_names,
                            'client_info': result
                        }
                        
                        # Connect to coding agent if available
                        if coding_agent:
                            try:
                                coding_agent.add_mcp_connection(server_id, {
                                    'name': server_info['name'],
                                    'client': connection_manager.get_connection(server_id),
                                    'tools': tool_names
                                })
                                return f"✅ Connected to {server_info['name']} and coding agent ({len(tool_names)} tools available)"
                            except Exception as e:
                                return f"✅ Connected to {server_info['name']} ({len(tool_names)} tools) but failed to link to coding agent: {str(e)}"
                        else:
                            return f"✅ Connected to {server_info['name']} ({len(tool_names)} tools available)"
                    else:
                        error_msg = result.get("error", "Unknown error")
                        return f"❌ Failed to connect to {server_info['name']}: {error_msg}"
                        
                except Exception as e:
                    # If real connection fails, provide helpful error message
                    install_cmd = "npm install -g @modelcontextprotocol/server-filesystem" if server_id == "filesystem" else f"pip install mcp-server-{server_id}"
                    return f"❌ Failed to connect to {server_info['name']}: {str(e)}\n\nClick 'Auto-Install & Connect' to install automatically"
                    
            except Exception as e:
                return f"❌ Error: {str(e)}"

        def connect_all_mcp_servers():
            """Connect to all predefined MCP servers"""
            if not HAS_CLIENT_MANAGER or not connection_manager:
                return "❌ Connection manager not available"
            
            results = []
            success_count = 0
            
            for server_id, server_info in predefined_servers.items():
                result = quick_connect_mcp(server_id)
                if "✅" in result:
                    success_count += 1
                results.append(f"{server_info['icon']} {server_info['name']}: {result}")
            
            summary = f"Connected to {success_count}/{len(predefined_servers)} servers\n\n"
            return summary + "\n".join(results)

        def disconnect_all_mcp_servers():
            """Disconnect all MCP connections"""
            if not HAS_CLIENT_MANAGER or not connection_manager:
                return "❌ Connection manager not available"
            
            try:
                connections = connection_manager.list_connections()
                count = len(connections)
                for conn in connections:
                    connection_manager.remove_connection(conn.get('name', ''))
                return f"✅ Disconnected {count} servers"
            except Exception as e:
                return f"❌ Error disconnecting: {str(e)}"

        def refresh_mcp_status():
            """Refresh status of all MCP connections"""
            if not HAS_CLIENT_MANAGER or not connection_manager:
                return "❌ Connection manager not available"
            
            try:
                connections = connection_manager.list_connections()
                status_lines = []
                
                for conn in connections:
                    status = "🟢 Connected" if conn.get('connected') else "🔴 Disconnected"
                    status_lines.append(f"{conn.get('name', 'Unknown')}: {status}")
                
                return "\n".join(status_lines) if status_lines else "No connections found"
            except Exception as e:
                return f"❌ Error refreshing status: {str(e)}"

        def get_mcp_connections_data():
            """Get MCP connections data for the table"""
            data = []
            
            # Check if we have any connections stored
            if hasattr(quick_connect_mcp, 'connections'):
                for server_id, conn_info in quick_connect_mcp.connections.items():
                    server_info = predefined_servers.get(server_id, {})
                    status_icon = "🟢" if conn_info['status'] == 'connected' else "🟡"
                    status_text = "Connected" if conn_info['status'] == 'connected' else "Simulated"
                    
                    data.append([
                        f"{server_info.get('icon', '🔌')} {conn_info['name']}",
                        "MCP Server",
                        f"{status_icon} {status_text}",
                        len(conn_info.get('tools', [])),
                        conn_info['url']
                    ])
            
            return data

        def get_mcp_connection_choices():
            """Get list of MCP connection names for dropdown"""
            choices = []
            
            # Check if we have any connections stored
            if hasattr(quick_connect_mcp, 'connections'):
                for server_id, conn_info in quick_connect_mcp.connections.items():
                    choices.append(server_id)
            
            return choices

        def load_mcp_connection_details(connection_name):
            """Load details for a selected MCP connection"""
            if not connection_name:
                return {}, [], []
            
            # Check if we have this connection stored
            if hasattr(quick_connect_mcp, 'connections') and connection_name in quick_connect_mcp.connections:
                conn_info = quick_connect_mcp.connections[connection_name]
                
                details = {
                    "name": connection_name,
                    "url": conn_info['url'],
                    "protocol": conn_info['protocol'],
                    "status": conn_info['status'],
                    "connected": conn_info['status'] == 'connected'
                }
                
                # Get tools data
                tools_data = []
                tool_names = []
                
                for tool in conn_info.get('tools', []):
                    tools_data.append([
                        tool,
                        f"Tool for {conn_info['name']}",
                        "{}"  # Empty parameters for demo
                    ])
                    tool_names.append(tool)
                
                return details, tools_data, tool_names
            
            return {"error": "Connection not found"}, [], []

        def test_mcp_connection(connection_name):
            """Test an MCP connection"""
            if not HAS_CLIENT_MANAGER or not connection_name:
                return {"error": "Invalid connection"}
            
            connections = connection_manager.list_connections()
            selected_conn = None
            
            for conn in connections:
                if conn.get('name') == connection_name:
                    selected_conn = conn
                    break
            
            if not selected_conn:
                return {"error": "Connection not found"}
            
            try:
                result = GradioMCPClient.test_connection(selected_conn.get('url'), selected_conn.get('protocol'))
                return {"status": "connected" if result["success"] else "error", "result": result}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        def disconnect_mcp_connection(connection_name):
            """Disconnect a specific MCP connection"""
            if not connection_name:
                return get_mcp_connections_data(), get_mcp_connection_choices()
            
            try:
                # Remove from our stored connections
                if hasattr(quick_connect_mcp, 'connections') and connection_name in quick_connect_mcp.connections:
                    del quick_connect_mcp.connections[connection_name]
            except Exception as e:
                pass
            
            return get_mcp_connections_data(), get_mcp_connection_choices()

        def call_mcp_tool(connection_name, tool_name, tool_args):
            """Call a tool on an MCP connection"""
            if not connection_name or not tool_name:
                return {"error": "Missing connection name or tool name"}
            
            # Check if we have this connection
            if not hasattr(quick_connect_mcp, 'connections') or connection_name not in quick_connect_mcp.connections:
                return {"error": "Connection not found"}
            
            conn_info = quick_connect_mcp.connections[connection_name]
            
            try:
                # For filesystem connection, implement actual operations
                if connection_name == "filesystem":
                    import os
                    
                    if tool_name == "list_directory":
                        path = tool_args.get('path', '.')
                        try:
                            files = os.listdir(path)
                            return {
                                "success": True, 
                                "result": {
                                    "files": files, 
                                    "path": os.path.abspath(path),
                                    "count": len(files)
                                }
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    
                    elif tool_name == "read_file":
                        path = tool_args.get('path', '')
                        if not path:
                            return {"success": False, "error": "Path is required"}
                        
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            return {
                                "success": True, 
                                "result": {
                                    "content": content, 
                                    "path": os.path.abspath(path),
                                    "size": len(content)
                                }
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    
                    elif tool_name == "write_file":
                        path = tool_args.get('path', '')
                        content = tool_args.get('content', '')
                        if not path:
                            return {"success": False, "error": "Path is required"}
                        
                        try:
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            return {
                                "success": True, 
                                "result": {
                                    "message": f"File written successfully",
                                    "path": os.path.abspath(path),
                                    "bytes_written": len(content.encode('utf-8'))
                                }
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    
                    elif tool_name == "create_directory":
                        path = tool_args.get('path', '')
                        if not path:
                            return {"success": False, "error": "Path is required"}
                        
                        try:
                            os.makedirs(path, exist_ok=True)
                            return {
                                "success": True, 
                                "result": {
                                    "message": f"Directory created successfully",
                                    "path": os.path.abspath(path)
                                }
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}
                    
                    else:
                        return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                # For other connections, show installation instructions
                else:
                    return {
                        "success": False, 
                        "error": f"MCP server '{connection_name}' not fully implemented.\n\nTo install real MCP servers, run:\npip install mcp-server-{connection_name}\n\nThen restart the dashboard."
                    }
                    
            except Exception as e:
                return {"success": False, "error": str(e)}

        def connect_custom_mcp(name, url, protocol, description):
            """Connect to a custom MCP server"""
            if not HAS_CLIENT_MANAGER or not connection_manager:
                return "❌ Connection manager not available"
            
            if not name or not url:
                return "❌ Please provide both name and URL"
            
            try:
                result = GradioMCPClient.test_connection(url, protocol)
                if result["success"]:
                    connection_manager.save_connection(name, url, protocol)
                    return f"✅ Connected to {name}"
                else:
                    return f"❌ Failed to connect: {result['error']}"
            except Exception as e:
                return f"❌ Error: {str(e)}"

        # Connect event handlers

        # AI Assistant event connections
        if coding_agent:
            configure_btn.click(
                configure_model,
                inputs=[hf_token_input, model_dropdown],
                outputs=[config_status, model_info],
            )

            # Chat functionality
            send_btn.click(
                send_message, inputs=[chat_input, chatbot, show_thinking], outputs=[chatbot, chat_input]
            )

            chat_input.submit(
                send_message, inputs=[chat_input, chatbot, show_thinking], outputs=[chatbot, chat_input]
            )

            reset_chat_btn.click(reset_conversation, outputs=chatbot)

            # Quick action buttons
            help_mcp_btn.click(quick_mcp_help, inputs=[chatbot, show_thinking], outputs=chatbot)
            help_gradio_btn.click(quick_gradio_help, inputs=[chatbot, show_thinking], outputs=chatbot)
            analyze_btn.click(quick_analyze_help, inputs=[chatbot, show_thinking], outputs=chatbot)
            best_practices_btn.click(quick_best_practices, inputs=[chatbot, show_thinking], outputs=chatbot)

            # Direct code analysis
            analyze_code_btn.click(
                analyze_code_directly,
                inputs=[code_input, language_select, chatbot, show_thinking],
                outputs=chatbot,
            )

            # Token management connections (only if secure storage is available)
            if config_manager.has_secure_storage():
                save_token_btn.click(
                    save_token_manually, inputs=hf_token_input, outputs=token_status
                )

                clear_token_btn.click(clear_saved_token, outputs=[token_status, hf_token_input])

        refresh_servers_btn.click(refresh_servers, outputs=servers_list)

        # Enhanced server management connections
        template_info_btn.click(
            get_template_info, inputs=template_dropdown, outputs=template_info_output
        )

        test_server_btn.click(
            test_server_connection,
            inputs=[connect_url, connection_protocol],
            outputs=connection_output,
        )

        connect_server_btn.click(
            connect_to_server,
            inputs=[connect_url, connection_name, connection_protocol],
            outputs=connection_output,
        ).then(refresh_connections, outputs=connections_list).then(
            update_connection_dropdown, outputs=connection_dropdown
        )

        # Connection management
        refresh_connections_btn.click(refresh_connections, outputs=connections_list)
        refresh_connections_btn.click(update_connection_dropdown, outputs=connection_dropdown)

        connection_dropdown.change(
            on_connection_dropdown_change, inputs=connection_dropdown, outputs=selected_connection
        )

        disconnect_btn.click(disconnect_from_server, inputs=selected_connection).then(
            refresh_connections, outputs=connections_list
        ).then(update_connection_dropdown, outputs=connection_dropdown)

        # Note: test_conn_btn functionality would need connection URL from selected connection
        # This would require additional connection management functionality

        create_server_btn.click(
            create_server,
            inputs=[new_server_name, template_dropdown, create_port],
            outputs=create_output,
        ).then(refresh_servers, outputs=servers_list).then(
            update_server_dropdown, outputs=server_dropdown
        )

        # Server selection handling

        # Initialize dropdown and servers list on load - will be handled at the end
        # demo.load calls moved to end of function

        # Update dropdown when servers are refreshed
        refresh_servers_btn.click(update_server_dropdown, outputs=server_dropdown)

        # Handle server selection
        server_dropdown.change(
            on_server_dropdown_change,
            inputs=server_dropdown,
            outputs=[selected_server, start_btn, stop_btn],
        )

        start_btn.click(start_server, inputs=selected_server).then(
            refresh_servers, outputs=servers_list
        )
        stop_btn.click(stop_server, inputs=selected_server).then(
            refresh_servers, outputs=servers_list
        )
        info_btn.click(show_server_info, inputs=selected_server, outputs=server_info_output)
        delete_btn.click(delete_server, inputs=selected_server, outputs=servers_list)
        refresh_logs_btn.click(
            view_server_logs, inputs=selected_server, outputs=server_logs_output
        ).then(lambda: gr.update(visible=True), outputs=server_logs_output)

        search_btn.click(
            search_registry, inputs=[search_query, category_filter], outputs=search_results
        )

        connect_test_btn.click(
            test_connection, inputs=[test_server_url, test_protocol], outputs=tools_list
        )

        call_tool_btn.click(
            call_tool,
            inputs=[test_server_url, test_protocol, tool_name, tool_args],
            outputs=tool_result,
        )

        save_settings_btn.click(
            save_settings,
            inputs=[
                settings_port,
                settings_auto_reload,
                settings_protocol,
                settings_log_level,
                settings_hf_token,
            ],
            outputs=settings_output,
        )

        # MCP Connections event handlers
        
        # Quick connect individual server buttons
        for server_id in predefined_servers.keys():
            if server_id in server_buttons and server_id in server_statuses:
                server_buttons[server_id].click(
                    fn=lambda sid=server_id: quick_connect_mcp(sid),
                    outputs=[server_statuses[server_id]]
                ).then(
                    fn=get_mcp_connections_data,
                    outputs=[mcp_connections_table]
                ).then(
                    fn=get_mcp_connection_choices,
                    outputs=[selected_mcp_connection]
                )
                
            # Auto-install buttons
            if server_id in server_install_buttons:
                def create_install_handler(sid):
                    def install_handler():
                        return install_and_connect_mcp(sid)
                    return install_handler
                
                server_install_buttons[server_id].click(
                    fn=lambda: gr.update(visible=True),
                    outputs=[mcp_install_progress]
                ).then(
                    fn=create_install_handler(server_id),
                    outputs=[mcp_install_progress]
                ).then(
                    fn=get_mcp_connections_data,
                    outputs=[mcp_connections_table]
                ).then(
                    fn=get_mcp_connection_choices,
                    outputs=[selected_mcp_connection]
                )

        # Bulk MCP actions
        connect_all_mcp_btn.click(
            connect_all_mcp_servers,
            outputs=[mcp_bulk_status]
        )

        disconnect_all_mcp_btn.click(
            disconnect_all_mcp_servers,
            outputs=[mcp_bulk_status]
        )

        refresh_mcp_status_btn.click(
            refresh_mcp_status,
            outputs=[mcp_bulk_status]
        )

        # Active MCP connections management
        selected_mcp_connection.change(
            load_mcp_connection_details,
            inputs=[selected_mcp_connection],
            outputs=[mcp_connection_details, mcp_available_tools, mcp_tool_name]
        )

        test_mcp_connection_btn.click(
            test_mcp_connection,
            inputs=[selected_mcp_connection],
            outputs=[mcp_connection_details]
        )

        disconnect_mcp_btn.click(
            disconnect_mcp_connection,
            inputs=[selected_mcp_connection],
            outputs=[mcp_connections_table, selected_mcp_connection]
        )

        # MCP tool calling
        call_mcp_tool_btn.click(
            call_mcp_tool,
            inputs=[selected_mcp_connection, mcp_tool_name, mcp_tool_args],
            outputs=[mcp_tool_result]
        )

        # Custom MCP connection
        custom_mcp_connect_btn.click(
            connect_custom_mcp,
            inputs=[custom_mcp_name, custom_mcp_url, custom_mcp_protocol, custom_mcp_description],
            outputs=[custom_mcp_status]
        )

        # Load initial data
        dashboard.load(refresh_servers, outputs=servers_list)
        dashboard.load(refresh_connections, outputs=connections_list)
        dashboard.load(update_server_dropdown, outputs=server_dropdown)
        dashboard.load(update_connection_dropdown, outputs=connection_dropdown)
        
        # Load initial MCP connections data
        dashboard.load(get_mcp_connections_data, outputs=mcp_connections_table)
        dashboard.load(get_mcp_connection_choices, outputs=selected_mcp_connection)

        # Load saved token on startup
        if coding_agent and config_manager.has_secure_storage():
            dashboard.load(load_saved_token_on_startup, outputs=[hf_token_input, token_status])

    return dashboard


def launch_dashboard(port: int = 8080, share: bool = False):
    """Launch the Gradio MCP Playground dashboard"""
    dashboard = create_dashboard()
    dashboard.launch(
        server_port=port,
        share=share,
        server_name="127.0.0.1",
        show_api=False,
        prevent_thread_lock=False,
    )
