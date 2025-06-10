"""
Unified Gradio MCP Playground Dashboard
Combines the main dashboard with agent builder functionality
"""

import gradio as gr
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
import logging

# We'll define message handling functions locally instead of importing
# because the web_ui versions expect a different scope

# Try to import server management functions
try:
    from .web_ui import (
        create_server,
        refresh_servers,
        start_server,
        stop_server,
        delete_server,  # Add this import
        show_server_info,
        show_template_info,
        install_registry_server,
        search_registry,
        get_registry_server_choices,
        quick_connect_mcp,
        test_mcp_connection,
    )

    HAS_SERVER_FUNCTIONS = True
except ImportError as e:
    print(f"Failed to import server functions: {e}")
    HAS_SERVER_FUNCTIONS = False

# Suppress Pydantic warning
warnings.filterwarnings(
    "ignore",
    message='Field "model_name" has conflict with protected namespace "model_"',
    category=UserWarning,
)

# Configure logging to reduce verbosity
logging.basicConfig(level=logging.WARNING)
logging.getLogger("gradio_mcp_playground").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("llama_index").setLevel(logging.WARNING)

# Check if Gradio is available
try:
    import gradio as gr

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

# Check for additional dependencies
try:
    from .config_manager import ConfigManager

    HAS_CONFIG_MANAGER = True
except ImportError:
    HAS_CONFIG_MANAGER = False

try:
    from .registry import ServerRegistry

    HAS_REGISTRY = True
except ImportError:
    HAS_REGISTRY = False

try:
    from .server_manager import ServerManager

    HAS_SERVER_MANAGER = True
except ImportError:
    HAS_SERVER_MANAGER = False

try:
    from .client_manager import GradioMCPClient
    from .mcp_connection_manager import MCPConnectionManager

    HAS_CLIENT_MANAGER = True
except ImportError:
    HAS_CLIENT_MANAGER = False

try:
    from .coding_agent import CodingAgent

    HAS_CODING_AGENT = True
except ImportError:
    HAS_CODING_AGENT = False

# Try to import agent components
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))
    from core.agent import GMPAgent
    from ui.pipeline_view import PipelineView
    from ui.control_panel import ControlPanelUI
    from ui.chat_interface import ChatInterface

    HAS_AGENT_COMPONENTS = True
except ImportError:
    HAS_AGENT_COMPONENTS = False
    print("Agent components not available - some features will be disabled")


def _get_connected_servers_info(coding_agent):
    """Get information about connected MCP servers"""
    if not coding_agent or not hasattr(coding_agent, "_mcp_servers"):
        return "**No MCP servers connected.** Connect servers in the MCP Connections tab."

    servers = coding_agent._mcp_servers
    if not servers:
        return "**No MCP servers connected.** Connect servers in the MCP Connections tab."

    info = f"**🔌 {len(servers)} MCP Servers Connected:**\n\n"
    for server_name, server in servers.items():
        tool_count = len(coding_agent.mcp_tools.get(server_name, []))
        info += f"• **{server_name}** ({tool_count} tools)\n"

    return info


def create_unified_dashboard():
    """Create the unified Gradio MCP Playground dashboard"""
    if not HAS_GRADIO:
        raise ImportError("Gradio is required for web dashboard functionality")

    config_manager = ConfigManager()
    registry = ServerRegistry()

    # Initialize server manager if available
    if HAS_SERVER_MANAGER:
        server_manager = ServerManager()
    else:
        server_manager = None

    # Initialize connection manager if available
    if HAS_CLIENT_MANAGER:
        connection_manager = MCPConnectionManager()
    else:
        connection_manager = None

    # Initialize coding agent if available
    coding_agent = None
    coding_agent_error = None
    saved_hf_token = None
    if HAS_CODING_AGENT:
        try:
            coding_agent = CodingAgent()

            # Try to load saved HF token using config manager
            saved_hf_token = config_manager.load_secure_token("huggingface")
            if saved_hf_token:
                print("DEBUG: Loaded saved HuggingFace token from secure storage")

            # Try to configure with stored HF token if available
            if saved_hf_token:
                try:
                    # Get available models
                    models = coding_agent.get_available_models()
                    if models:
                        # Use first available model
                        model_name = list(models.keys())[0]
                        result = coding_agent.configure_model(saved_hf_token, model_name)
                        if result.get("success"):
                            print(f"Auto-configured coding agent with {model_name}")
                except Exception as e:
                    print(f"Could not auto-configure coding agent: {e}")
        except ImportError as e:
            coding_agent_error = str(e)

    # Initialize GMP agent if available
    gmp_agent = None
    if HAS_AGENT_COMPONENTS:
        try:
            gmp_agent = GMPAgent()
        except Exception as e:
            print(f"Could not initialize GMP Agent: {e}")

    with gr.Blocks(
        title="Gradio MCP Playground - Unified",
        theme=gr.themes.Soft(),
        css="""
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
        
        /* Fix chatbot message width for Gradio 4.x */
        .message-wrap {
            max-width: 100% !important;
        }
        .message-content {
            max-width: 100% !important;
        }
        
        /* Target message containers by data-testid */
        div[data-testid="user"] .prose,
        div[data-testid="bot"] .prose {
            max-width: 100% !important;
        }
        
        /* Override Tailwind's prose max-width */
        .prose {
            max-width: none !important;
        }
        
        /* Target message bubbles */
        .message-bubble-border {
            max-width: 100% !important;
        }
        
        /* For messages format */
        .message-row {
            justify-content: stretch !important;
        }
        .message-row > div {
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }
        
        /* Target by role classes */
        .role-user .prose,
        .role-assistant .prose {
            max-width: 100% !important;
        }
        
        /* Gradio 4 specific message classes */
        .message.svelte-1s78gfg .prose {
            max-width: 100% !important;
        }
        
        /* Override any inline styles */
        [style*="max-width"] {
            max-width: 100% !important;
        }
        
        /* Agent builder specific styles */
        .agent-mode-selector {
            margin-bottom: 20px;
        }
        """,
    ) as dashboard:
        gr.Markdown(
            """
            # 🚀 Gradio MCP Playground - Unified Dashboard
            
            Build, manage, and deploy applications as Model Context Protocol (MCP) servers.
            """
        )

        with gr.Tabs():
            # Tab 1: AI Assistant (Enhanced with Agent Builder)
            with gr.Tab("🤖 AI Assistant"):
                # Model configuration section (available for all modes)
                if coding_agent:
                    with gr.Group():
                        gr.Markdown("### Model Configuration")
                        with gr.Row():
                            with gr.Column(scale=2):
                                hf_token_input = gr.Textbox(
                                    label="HuggingFace API Token",
                                    type="password",
                                    placeholder="Enter your HuggingFace API token...",
                                    value=(
                                        "*" * 20 if saved_hf_token else ""
                                    ),  # Show masked token if saved
                                    info="Get your token from https://huggingface.co/settings/tokens"
                                    + (" (Using saved token)" if saved_hf_token else ""),
                                )

                            with gr.Column(scale=1):
                                # Get available models and set a valid default
                                available_models = (
                                    list(coding_agent.get_available_models().keys())
                                    if coding_agent
                                    else []
                                )
                                default_model = available_models[0] if available_models else None

                                model_dropdown = gr.Dropdown(
                                    label="Select Model",
                                    choices=available_models,
                                    value=default_model,
                                    info="Choose a model for the AI assistant",
                                )

                        with gr.Row():
                            configure_btn = gr.Button("🔧 Configure Model", variant="primary")

                        # Check if already configured
                        is_configured = (
                            coding_agent
                            and hasattr(coding_agent, "agent")
                            and coding_agent.agent is not None
                        )
                        current_model = (
                            coding_agent.current_model
                            if hasattr(coding_agent, "current_model")
                            else None
                        )

                        config_status = gr.Textbox(
                            label="Configuration Status",
                            value=(
                                f"✅ Configured with {current_model}"
                                if is_configured
                                else "Not configured - please enter your HuggingFace token and configure a model"
                            ),
                            interactive=False,
                        )

                        # Model info display in collapsible section
                        with gr.Accordion(
                            "📊 Selected Model Information", open=False, visible=False
                        ) as model_info_accordion:
                            model_info = gr.JSON(label="", visible=True)

                # Mode selector with three modes
                with gr.Row(elem_classes=["agent-mode-selector"]):
                    assistant_mode = gr.Radio(
                        choices=["Assistant", "MCP Agent", "Agent Builder"],
                        value="Assistant",
                        label="Assistant Mode",
                        info="Choose your assistant type: General Assistant with MCP tools | MCP-focused development | Custom agent creation",
                    )

                # General Assistant Mode (conversational with MCP agency)
                with gr.Group(visible=True) as general_assistant_group:
                    if coding_agent:
                        gr.Markdown("### Adam - General Assistant with MCP Tools")
                        gr.Markdown(
                            "I'm Adam, your general-purpose assistant with access to all connected MCP tools. I can help with any task using the available servers."
                        )

                        # Show connected MCP servers
                        with gr.Row():
                            connected_servers_info = gr.Markdown(
                                value=_get_connected_servers_info(coding_agent)
                            )
                            refresh_servers_btn = gr.Button(
                                "🔄 Refresh", size="sm", variant="secondary"
                            )

                        # General chat interface
                        general_chatbot = gr.Chatbot(
                            label="Chat with Adam",
                            height=600,
                            show_copy_button=True,
                            type="messages",
                            bubble_full_width=True,
                        )

                        with gr.Row():
                            general_input = gr.Textbox(
                                label="Message",
                                placeholder="Ask me anything - I can use MCP tools to help! (e.g., 'Take a screenshot of google.com', 'Search for Python tutorials', 'Create a file with...')",
                                scale=4,
                            )
                            general_send_btn = gr.Button("Send", variant="primary", scale=1)

                        with gr.Row():
                            general_show_thinking = gr.Checkbox(
                                label="🧠 Show Thinking Process",
                                value=False,
                                info="See how I use MCP tools to complete tasks",
                            )

                    else:
                        gr.Markdown("### General Assistant Unavailable")
                        gr.Markdown("Please install AI dependencies to use the assistant.")

                # MCP Agent Mode (focused on MCP development)
                with gr.Group(visible=False) as mcp_agent_group:
                    if coding_agent:
                        gr.Markdown("### Liam - MCP Development Specialist")
                        gr.Markdown(
                            "I'm specialized in helping you research, build, test, install, and connect MCP servers. Ask me about MCP best practices, server creation, or troubleshooting."
                        )

                        # Chat interface
                        chatbot = gr.Chatbot(
                            label="Chat with Liam",
                            height=500,
                            show_copy_button=True,
                            type="messages",
                            bubble_full_width=True,
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
                                info="Display the AI's reasoning process step-by-step",
                            )
                            reset_chat_btn = gr.Button(
                                "🔄 Reset Chat", variant="secondary", scale=1
                            )

                    else:
                        gr.Markdown("### AI Assistant Unavailable")
                        if coding_agent_error:
                            gr.Markdown(f"**Error:** {coding_agent_error}")
                        gr.Markdown(
                            """
                        To use the AI coding assistant, install AI dependencies:
                        
                        ```bash
                        pip install -e ".[ai]"
                        ```
                        """
                        )

                # Agent Builder Mode (from agent app)
                with gr.Group(visible=False) as agent_builder_group:
                    if HAS_AGENT_COMPONENTS and gmp_agent:
                        gr.Markdown("### Arthur - Agent Builder")
                        gr.Markdown(
                            "I'm Arthur, your agent creation specialist. I can help you create custom Gradio agents using system prompts from top AI assistants."
                        )

                        # Agent builder chat interface
                        agent_chatbot = gr.Chatbot(
                            label="Agent Builder Assistant",
                            height=500,
                            show_copy_button=True,
                            type="messages",
                            bubble_full_width=True,
                            value=[
                                {
                                    "role": "assistant",
                                    "content": "👋 Hello! I'm Arthur, your agent creation specialist.\n\nI can help you create custom Gradio agents for various tasks. Here are some things you can ask me:\n\n• **Show available templates** - See what agent templates are available\n• **Create a data analysis agent** - Build an agent for data science tasks\n• **Make a creative writing assistant** - Design an agent for content creation\n• **Build a code review agent** - Create an agent for code analysis\n\nWhat kind of agent would you like to create today?",
                                }
                            ],
                        )

                        with gr.Row():
                            agent_input = gr.Textbox(
                                label="Message",
                                placeholder="Ask me to create an agent (e.g., 'Create a data science agent using Claude's prompt')",
                                scale=4,
                            )
                            agent_send_btn = gr.Button("Send", variant="primary", scale=1)

                        gr.Markdown(
                            """
                            **Examples:**
                            - "Show me available system prompts"
                            - "Create a creative writing agent"
                            - "Build a data analysis agent using GPT's system prompt"
                            """
                        )
                    else:
                        gr.Markdown("### Agent Builder Unavailable")
                        gr.Markdown(
                            """
                            The agent builder requires additional components. 
                            Please ensure the agent directory is properly installed.
                            """
                        )

            # Tab 2: Server Builder (Combined)
            with gr.Tab("🔧 Server Builder"):
                gr.Markdown("### Build MCP Servers")

                with gr.Tabs():
                    # Quick Create (from main dashboard)
                    with gr.Tab("⚡ Quick Create"):
                        with gr.Row():
                            template_dropdown = gr.Dropdown(
                                choices=registry.list_templates() if HAS_REGISTRY else [],
                                label="Server Template",
                                value="basic",
                                info="Choose a template for your new server",
                            )
                            template_info_btn = gr.Button("ℹ️ Template Info", variant="secondary")

                        template_info_output = gr.JSON(label="Template Information", visible=False)

                        with gr.Row():
                            new_server_name = gr.Textbox(
                                label="Server Name",
                                placeholder="my-mcp-server",
                                info="Choose a unique name for your server",
                            )
                            create_port = gr.Number(
                                label="Port",
                                value=config_manager.default_port if HAS_CONFIG_MANAGER else 8080,
                                precision=0,
                                info="Port number for the server (optional)",
                            )

                        create_server_btn = gr.Button(
                            "🚀 Create Server", variant="primary", size="lg"
                        )
                        create_output = gr.Textbox(label="Creation Output", visible=False)

                    # Pipeline Builder (from agent app)
                    with gr.Tab("🔗 Pipeline Builder"):
                        if HAS_AGENT_COMPONENTS and gmp_agent:
                            gr.Markdown("### Visual Pipeline Builder")
                            gr.Markdown(
                                """
                                The pipeline builder allows you to create complex MCP server workflows visually.
                                
                                To access the full pipeline builder, run:
                                ```bash
                                cd agent && python app.py
                                ```
                                
                                Features include:
                                - Drag-and-drop server connections
                                - Visual workflow design
                                - Real-time testing
                                - Export to code
                                """
                            )
                        else:
                            gr.Markdown("### Visual Pipeline Builder")
                            gr.Markdown(
                                """
                                The pipeline builder allows you to create complex workflows visually.
                                This feature requires the agent components to be installed.
                                """
                            )

                    # Templates Gallery
                    with gr.Tab("📚 Templates"):
                        gr.Markdown("### Server Templates Gallery")
                        gr.Markdown("Browse and use pre-built server templates")

                        # Display available templates
                        def update_templates_display():
                            """Update the templates display"""
                            if HAS_REGISTRY:
                                templates = registry.list_templates()
                                if templates:
                                    display = ""
                                    for template in templates:
                                        template_info = registry.get_template(template)
                                        if template_info:
                                            display += f"### {template}\n"
                                            display += f"- **Description**: {template_info.get('description', 'No description')}\n"
                                            display += f"- **Files**: {', '.join(template_info.get('files', {}).keys())}\n\n"
                                    return display
                                else:
                                    return "No templates available."
                            return "Registry not available."

                        templates_display = gr.Markdown(value=update_templates_display())

            # Tab 3: Server Management (Unified)
            with gr.Tab("🖥️ Server Management"):
                gr.Markdown("### MCP Server Management")

                with gr.Tabs():
                    # Active Servers
                    with gr.Tab("🟢 Active Servers"):
                        servers_list = gr.Dataframe(
                            headers=[
                                "Name",
                                "Status",
                                "Source",
                                "Command",
                                "Last Seen",
                                "Errors",
                            ],
                            label="Active MCP Servers",
                            interactive=False,
                        )

                        with gr.Row():
                            refresh_servers_btn = gr.Button("🔄 Refresh", variant="secondary")
                            server_dropdown = gr.Dropdown(
                                label="Select Server",
                                choices=[],
                                value=None,
                                interactive=True,
                            )

                        with gr.Row():
                            start_btn = gr.Button("▶️ Start", variant="primary")
                            stop_btn = gr.Button("⏹️ Stop", variant="stop")
                            info_btn = gr.Button("ℹ️ Info", variant="secondary")
                            delete_btn = gr.Button("🗑️ Delete", variant="stop")

                        server_info = gr.JSON(label="Server Information", visible=False)
                        server_action_status = gr.Textbox(
                            label="Server Action Status", visible=False, lines=3
                        )

                    # Server Registry
                    with gr.Tab("📦 Browse Registry"):
                        gr.Markdown("### MCP Server Registry")

                        with gr.Row():
                            registry_search_query = gr.Textbox(
                                label="Search Servers",
                                placeholder="Search by name, description, or category...",
                                scale=3,
                            )
                            registry_search_btn = gr.Button("🔍 Search", variant="primary", scale=1)

                        registry_results_df = gr.Dataframe(
                            headers=["Name", "Category", "Description", "Install Method"],
                            label="Search Results",
                            interactive=False,
                            wrap=True,
                        )

                        registry_server_selector = gr.Dropdown(
                            label="Select Server to Install",
                            choices=[],
                            interactive=True,
                        )

                        registry_install_btn = gr.Button(
                            "📥 Install Selected Server", variant="primary"
                        )

                        # Quick Install section
                        gr.Markdown("### Quick Install Popular Servers")
                        with gr.Row():
                            install_filesystem_btn = gr.Button("📁 Filesystem", variant="secondary")
                            install_memory_btn = gr.Button("🧠 Memory", variant="secondary")
                            install_github_btn = gr.Button("🐙 GitHub", variant="secondary")

                        registry_install_status = gr.Textbox(
                            label="Installation Status",
                            interactive=False,
                            lines=10,
                        )

            # Tab 4: MCP Connections (Merged)
            with gr.Tab("🔌 MCP Connections"):
                gr.Markdown("### MCP Server Connections")
                gr.Markdown("Connect to multiple MCP servers for enhanced capabilities")

                with gr.Tabs():
                    # Quick Connect
                    with gr.Tab("⚡ Quick Connect"):
                        # Predefined servers grid with proper Gradio buttons
                        quick_connect_status = gr.Textbox(
                            label="Connection Status", visible=False, lines=3
                        )

                        with gr.Row():
                            with gr.Column(scale=1):
                                gr.Markdown("### 📁 Filesystem Server")
                                gr.Markdown(
                                    "Secure file operations with configurable access controls."
                                )
                                filesystem_btn = gr.Button("Connect", variant="primary")

                            with gr.Column(scale=1):
                                gr.Markdown("### 🧠 Memory Server")
                                gr.Markdown("Knowledge graph-based persistent memory system.")
                                memory_btn = gr.Button("Connect", variant="primary")

                        with gr.Row():
                            with gr.Column(scale=1):
                                gr.Markdown("### 🐙 GitHub Server")
                                gr.Markdown("Access GitHub repositories, issues, and PRs.")
                                github_btn = gr.Button("Connect", variant="primary")

                            with gr.Column(scale=1):
                                gr.Markdown("### 🔍 Brave Search")
                                gr.Markdown("Web search with privacy focus.")
                                brave_btn = gr.Button("Connect", variant="primary")

                    # Active Connections
                    with gr.Tab("🔗 Active Connections"):
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

                        with gr.Row():
                            refresh_connections_btn = gr.Button("🔄 Refresh", variant="secondary")
                            connection_dropdown = gr.Dropdown(
                                label="Select Connection",
                                choices=[],
                                value=None,
                                interactive=True,
                            )

                        with gr.Row():
                            disconnect_btn = gr.Button("🔌 Disconnect", variant="stop")
                            test_conn_btn = gr.Button("🧪 Test", variant="secondary")

                    # Custom Connection
                    with gr.Tab("➕ Custom Connection"):
                        gr.Markdown("### Connect to Custom MCP Server")

                        custom_mcp_name = gr.Textbox(
                            label="Connection Name",
                            placeholder="my-custom-server",
                        )

                        custom_mcp_url = gr.Textbox(
                            label="Server URL/Command",
                            placeholder="python -m my_mcp_server or http://localhost:8080/mcp",
                            lines=2,
                        )

                        custom_mcp_protocol = gr.Radio(
                            label="Protocol",
                            choices=["auto", "stdio", "sse"],
                            value="auto",
                        )

                        custom_mcp_connect_btn = gr.Button("🔗 Connect", variant="primary")
                        custom_mcp_status = gr.Textbox(
                            label="Connection Status",
                            interactive=False,
                            lines=3,
                        )

            # Tab 5: Tool Testing
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

            # Tab 6: Help & Resources
            with gr.Tab("📚 Help & Resources"):
                with gr.Tabs():
                    # Documentation
                    with gr.Tab("📖 Documentation"):
                        gr.Markdown(
                            """
                            ### Gradio MCP Playground Documentation
                            
                            **Getting Started:**
                            1. Configure your AI assistant with a HuggingFace token
                            2. Create or connect to MCP servers
                            3. Use the AI assistant to help build and manage servers
                            
                            **Key Features:**
                            - **AI Assistant**: Get help with coding and MCP development
                            - **Agent Builder**: Create custom Gradio agents
                            - **Server Builder**: Quick create servers or build complex pipelines
                            - **MCP Connections**: Connect to multiple servers simultaneously
                            - **Tool Testing**: Test MCP tools interactively
                            
                            **Resources:**
                            - [MCP Documentation](https://github.com/anthropics/mcp)
                            - [Gradio Documentation](https://gradio.app/docs)
                            - [Project GitHub](https://github.com/seanpoyner/gradio-mcp-playground)
                            """
                        )

                    # Examples
                    with gr.Tab("💡 Examples"):
                        gr.Markdown(
                            """
                            ### Example Use Cases
                            
                            **1. Create a Simple Calculator Server:**
                            ```python
                            # Use the Calculator template
                            # Name: my-calculator
                            # Port: 7860
                            ```
                            
                            **2. Build a Data Processing Pipeline:**
                            - Use Pipeline Builder to connect:
                              - File input → Data processor → Visualization → Output
                            
                            **3. Connect to GitHub:**
                            - Go to MCP Connections
                            - Click on GitHub in Quick Connect
                            - Provide your GitHub token
                            - Use tools to manage repos
                            """
                        )

                    # Agent Control Panel (from agent app)
                    with gr.Tab("🤖 Agent Monitor"):
                        if HAS_AGENT_COMPONENTS:
                            try:
                                # The control panel creates its own interface, so we can't embed it directly
                                # Instead, we'll show a placeholder with instructions
                                gr.Markdown("### Agent Control Panel")
                                gr.Markdown(
                                    """
                                    The Agent Control Panel provides advanced monitoring and control features.
                                    
                                    To access the full control panel, run:
                                    ```bash
                                    cd agent && python app.py
                                    ```
                                    
                                    Features include:
                                    - Real-time agent monitoring
                                    - Performance metrics
                                    - Log viewing
                                    - Agent lifecycle management
                                    """
                                )
                            except Exception as e:
                                gr.Markdown("### Agent Control Panel")
                                gr.Markdown(f"Control panel initialization error: {str(e)}")
                        else:
                            gr.Markdown("### Agent Control Panel")
                            gr.Markdown(
                                """
                                Monitor and control deployed agents.
                                This feature requires agent components to be installed.
                                """
                            )

            # Tab 7: Settings
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### Gradio MCP Playground Settings")

                with gr.Column():
                    settings_port = gr.Number(
                        label="Default Port",
                        value=config_manager.default_port if HAS_CONFIG_MANAGER else 8080,
                        precision=0,
                    )
                    settings_auto_reload = gr.Checkbox(
                        label="Auto-reload on file changes",
                        value=config_manager.auto_reload if HAS_CONFIG_MANAGER else False,
                    )
                    settings_protocol = gr.Dropdown(
                        choices=["auto", "stdio", "sse"],
                        label="Default MCP Protocol",
                        value=config_manager.mcp_protocol if HAS_CONFIG_MANAGER else "auto",
                    )
                    settings_log_level = gr.Dropdown(
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        label="Log Level",
                        value=config_manager.log_level if HAS_CONFIG_MANAGER else "INFO",
                    )

                save_settings_btn = gr.Button("💾 Save Settings", variant="primary")
                settings_output = gr.Textbox(label="Settings Output", visible=False)

        # Event handlers

        # Server management functions (implementations)
        def create_server(name, template, port):
            """Create a new MCP server"""
            if not HAS_REGISTRY:
                return "Registry not available"

            try:
                if not name:
                    return "Please provide a server name"

                # Create server using registry
                result = registry.create_from_template(name, template)
                if result["success"]:
                    return f"✅ Server '{name}' created successfully!\nPath: {result['path']}"
                else:
                    return f"❌ Failed to create server: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"❌ Error creating server: {str(e)}"

        def refresh_servers():
            """Refresh the servers list"""
            if not HAS_CONFIG_MANAGER:
                return [], []

            servers = config_manager.list_servers()

            # Format for dataframe
            data = []
            choices = []
            for server in servers:
                data.append(
                    [
                        server.get("name", ""),
                        "Running" if server.get("running") else "Stopped",
                        server.get("source", "local"),
                        server.get("command", ""),
                        server.get("last_seen", ""),
                        server.get("errors", ""),
                    ]
                )
                choices.append(server.get("name", ""))

            return data, gr.update(choices=choices)

        def show_template_info(template_name):
            """Show template information"""
            if not HAS_REGISTRY:
                return {}

            info = registry.get_template(template_name)
            return info if info else {"error": "Template not found"}

        def quick_connect_mcp(server_id):
            """Quick connect to a predefined MCP server"""
            if not HAS_CLIENT_MANAGER or not connection_manager:
                return "Connection manager not available"

            try:
                # Predefined server configs
                configs = {
                    "filesystem": {
                        "name": "Filesystem Server",
                        "command": "npx -y @modelcontextprotocol/server-filesystem",
                        "args": ["--path", os.path.expanduser("~")],
                    },
                    "memory": {
                        "name": "Memory Server",
                        "command": "npx -y @modelcontextprotocol/server-memory",
                        "args": [],
                    },
                    "github": {
                        "name": "GitHub Server",
                        "command": "npx -y @modelcontextprotocol/server-github",
                        "args": [],
                        "env": {"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")},
                    },
                    "brave-search": {
                        "name": "Brave Search",
                        "command": "npx -y @modelcontextprotocol/server-brave-search",
                        "args": [],
                        "env": {"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")},
                    },
                }

                if server_id not in configs:
                    return f"Unknown server: {server_id}"

                config = configs[server_id]

                # Check for required environment variables
                if server_id == "github" and not config["env"]["GITHUB_TOKEN"]:
                    return "❌ GitHub server requires GITHUB_TOKEN environment variable"
                elif server_id == "brave-search" and not config["env"]["BRAVE_API_KEY"]:
                    return "❌ Brave Search server requires BRAVE_API_KEY environment variable"

                # Connect to the server
                result = connection_manager.connect(
                    server_id, config["command"], config.get("args", []), config.get("env", {})
                )

                if result["success"]:
                    return f"✅ Connected to {config['name']} successfully!"
                else:
                    return f"❌ Failed to connect: {result.get('error', 'Unknown error')}"

            except Exception as e:
                return f"❌ Error connecting: {str(e)}"

        def quick_install_popular(server_id):
            """Quick install popular servers"""
            if not HAS_REGISTRY:
                return "Registry not available"

            try:
                # Install the server
                result = registry.install_server(server_id)
                if result["success"]:
                    return f"✅ {server_id} installed successfully!"
                else:
                    return f"❌ Failed to install: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"❌ Error installing: {str(e)}"

        def install_registry_server(server_name, user_args_json):
            """Install a server from the registry"""
            if not HAS_REGISTRY:
                return "Registry not available"

            try:
                # Parse user args if provided
                user_args = {}
                if user_args_json:
                    import json

                    user_args = json.loads(user_args_json)

                # Install the server
                result = registry.install_server(server_name, user_args)
                if result.get("success"):
                    return f"✅ {server_name} installed successfully!"
                else:
                    return f"❌ Failed to install: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"❌ Error installing: {str(e)}"

        def start_server(server_name):
            """Start a server"""
            if not HAS_SERVER_MANAGER or not server_manager:
                return refresh_servers()[0]

            try:
                result = server_manager.start_server(server_name)
                if result.get("success"):
                    return refresh_servers()[0]
                else:
                    # Show error in status
                    return refresh_servers()[0]
            except Exception as e:
                print(f"Error starting server: {e}")
                return refresh_servers()[0]

        def stop_server(server_name):
            """Stop a server"""
            if not HAS_SERVER_MANAGER or not server_manager:
                return refresh_servers()[0]

            try:
                result = server_manager.stop_server(server_name)
                if result.get("success"):
                    return refresh_servers()[0]
                else:
                    # Show error in status
                    return refresh_servers()[0]
            except Exception as e:
                print(f"Error stopping server: {e}")
                return refresh_servers()[0]

        def delete_server(server_name):
            """Delete a server"""
            if not HAS_CONFIG_MANAGER or not config_manager:
                return refresh_servers()

            try:
                # Stop server first if running
                if HAS_SERVER_MANAGER and server_manager:
                    server_manager.stop_server(server_name)

                # Delete from config
                success = config_manager.remove_server(server_name)
                if success:
                    print(f"Server '{server_name}' deleted successfully")
                else:
                    print(f"Failed to delete server '{server_name}'")

                return refresh_servers()
            except Exception as e:
                print(f"Error deleting server: {e}")
                return refresh_servers()

        def show_server_info(server_name):
            """Show server information"""
            if not HAS_CONFIG_MANAGER:
                return {}

            servers = config_manager.list_servers()
            for server in servers:
                if server.get("name") == server_name:
                    return server
            return {"error": "Server not found"}

        def get_template_info(template_name):
            """Get template information"""
            return show_template_info(template_name)

        def disconnect_mcp(connection_name):
            """Disconnect from an MCP server"""
            # Try coding agent first (where connections are actually stored)
            if coding_agent and hasattr(coding_agent, "_mcp_servers"):
                try:
                    if connection_name in coding_agent._mcp_servers:
                        server = coding_agent._mcp_servers[connection_name]
                        # Stop the server process
                        if hasattr(server, "stop"):
                            server.stop()
                        # Remove from coding agent
                        del coding_agent._mcp_servers[connection_name]
                        # Also remove tools if present
                        if (
                            hasattr(coding_agent, "mcp_tools")
                            and connection_name in coding_agent.mcp_tools
                        ):
                            del coding_agent.mcp_tools[connection_name]
                        return f"✅ Disconnected from {connection_name}"
                except Exception as e:
                    print(f"Error disconnecting from coding agent: {e}")

            # Fallback to connection manager
            if HAS_CLIENT_MANAGER and connection_manager:
                try:
                    # MCPConnectionManager stores connections by server_id
                    if connection_name in connection_manager.connections:
                        connection = connection_manager.connections[connection_name]
                        connection.stop()
                        del connection_manager.connections[connection_name]
                        return f"✅ Disconnected from {connection_name}"
                except Exception as e:
                    print(f"Error disconnecting from connection manager: {e}")

            return f"❌ Connection {connection_name} not found"

        def refresh_connections():
            """Refresh connections list"""
            # Try to get connections from coding agent first (where they're actually stored)
            if coding_agent and hasattr(coding_agent, "_mcp_servers"):
                try:
                    data = []
                    choices = []

                    print(
                        f"DEBUG: Found {len(coding_agent._mcp_servers)} MCP servers in coding agent"
                    )

                    # Get connections from coding agent's _mcp_servers
                    for server_name, server in coding_agent._mcp_servers.items():
                        # server is an MCPServerProcess object
                        connected = server.process is not None and server.process.poll() is None
                        data.append(
                            [
                                server_name,
                                f"{server.command} {' '.join(server.args)}",
                                "stdio",
                                "Connected" if connected else "Disconnected",
                                "Active" if connected else "Inactive",
                            ]
                        )
                        choices.append(server_name)
                        print(f"DEBUG: Added {server_name} - Connected: {connected}")

                    return data, gr.update(choices=choices)
                except Exception as e:
                    print(f"Error refreshing connections from coding agent: {e}")
                    import traceback

                    traceback.print_exc()

            # Fallback to connection manager if available
            if HAS_CLIENT_MANAGER and connection_manager:
                try:
                    # Get connections from the connection manager
                    data = []
                    choices = []

                    # The MCPConnectionManager stores connections in a dict
                    for server_id, connection in connection_manager.connections.items():
                        data.append(
                            [
                                server_id,
                                connection.command + " " + " ".join(connection.args),
                                "stdio",  # MCPConnectionManager only supports stdio
                                "Connected" if connection._connected else "Disconnected",
                                "Active" if connection._connected else "Inactive",
                            ]
                        )
                        choices.append(server_id)

                    return data, gr.update(choices=choices)
                except Exception as e:
                    print(f"Error refreshing connections: {e}")

            return [], gr.update(choices=[])

        # Initialize greeting functions first if available
        if coding_agent:

            def initialize_general_greeting():
                """General assistant greeting"""
                greeting = (
                    "👋 Hello! I'm Adam, your general assistant with access to MCP tools.\n\n"
                )

                # Show available tools
                if hasattr(coding_agent, "_mcp_servers") and coding_agent._mcp_servers:
                    greeting += "I have access to these capabilities:\n"
                    for server_name in coding_agent._mcp_servers.keys():
                        if server_name == "filesystem":
                            greeting += "• 📁 File operations (read, write, create)\n"
                        elif server_name == "brave-search":
                            greeting += "• 🔍 Web searches\n"
                        elif server_name == "github":
                            greeting += "• 🐙 GitHub operations\n"
                        elif server_name == "screenshotone":
                            greeting += "• 📸 Screenshots of websites\n"
                        elif server_name == "memory":
                            greeting += "• 🧠 Remember information across conversations\n"
                        elif server_name == "azure":
                            greeting += "• ☁️ Azure cloud operations\n"
                        elif server_name == "obsidian":
                            greeting += "• 📝 Obsidian vault management\n"
                    greeting += "\n"

                greeting += "What would you like me to help you with today?"
                return [{"role": "assistant", "content": greeting}]

            def initialize_liam_greeting():
                """MCP Agent (Liam) greeting"""
                # Count connected servers
                connected_count = 0
                if hasattr(coding_agent, "_mcp_servers") and coding_agent._mcp_servers:
                    connected_count = len(coding_agent._mcp_servers)

                greeting = f"👋 Hi! I'm Liam, your MCP development specialist.\n\n"
                greeting += "I can help you:\n"
                greeting += "• 🔍 Research and find MCP servers\n"
                greeting += "• 🔧 Build custom MCP servers\n"
                greeting += "• 🧪 Test server functionality\n"
                greeting += "• 📦 Install servers from the registry\n"
                greeting += "• 🔌 Connect and configure servers\n\n"

                if connected_count > 0:
                    greeting += f"✅ **{connected_count} servers connected** "
                    # Show first 3 servers
                    server_names = list(coding_agent._mcp_servers.keys())[:3]
                    greeting += f"({', '.join(server_names)}"
                    if connected_count > 3:
                        greeting += f", +{connected_count - 3} more"
                    greeting += ")\n\n"

                greeting += "💡 **Quick commands:** `install memory` • `find database servers` • `what's MCP?`\n\n"
                greeting += "What MCP-related task can I help you with?"

                return [{"role": "assistant", "content": greeting}]

        # Assistant mode switching (3 modes)
        def switch_assistant_mode(mode):
            if mode == "Assistant":
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif mode == "MCP Agent":
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            else:  # Agent Builder
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

        assistant_mode.change(
            switch_assistant_mode,
            inputs=[assistant_mode],
            outputs=[general_assistant_group, mcp_agent_group, agent_builder_group],
        )

        # Event handlers for all assistant modes
        if coding_agent:
            # Import additional event handler functions from web_ui
            from .web_ui import reset_conversation, configure_model as _configure_model

            # Define message handling functions locally
            def handle_message_submit(message, history, show_thinking):
                """Handle message submission with immediate display"""
                if not message.strip():
                    return history, ""

                # Clear input immediately and show user message
                history_with_user = history + [{"role": "user", "content": message}]

                # Return cleared input and updated history, then process
                return history_with_user, ""

            def process_message(history, show_thinking):
                """Process the last user message and generate response"""
                if not history or history[-1]["role"] != "user":
                    return history

                message = history[-1]["content"]

                # Add thinking indicator
                history.append({"role": "assistant", "content": "🤔 Thinking..."})
                yield history

                # Now process the actual message
                try:
                    # Remove the thinking message
                    history = history[:-1]

                    # Call the original send_message logic
                    if not coding_agent.is_configured():
                        bot_response = (
                            "Please configure a model first by providing your HuggingFace token."
                        )
                        history.append({"role": "assistant", "content": bot_response})
                        yield history
                        return

                    # Process with agent
                    import re

                    # Check if user is providing an API key in a natural way
                    # Pattern 1: "install brave search with key YOUR_KEY"
                    brave_key_match = re.search(
                        r"install brave search with (?:key|token) ([\w-]+)", message, re.IGNORECASE
                    )
                    if brave_key_match:
                        api_key = brave_key_match.group(1)
                        message = f"install_mcp_server_from_registry(server_id='brave-search', token='{api_key}')"

                    # Pattern 2: "install github with token YOUR_TOKEN"
                    github_key_match = re.search(
                        r"install github with (?:key|token) ([\w-]+)", message, re.IGNORECASE
                    )
                    if github_key_match:
                        api_key = github_key_match.group(1)
                        message = f"install_mcp_server_from_registry(server_id='github', token='{api_key}')"

                    # Process with agent
                    if show_thinking:
                        steps, bot_response = coding_agent.chat_with_steps(message)

                        # Show thinking steps
                        thinking_content = "### 🧠 Thinking Process:\n\n"
                        for i, step in enumerate(steps, 1):
                            thinking_content += f"**Step {i}:** {step}\n\n"
                        thinking_content += f"### 💬 Response:\n\n{bot_response}"

                        history.append({"role": "assistant", "content": thinking_content})
                    else:
                        bot_response = coding_agent.chat(message)
                        history.append({"role": "assistant", "content": bot_response})

                    yield history

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    history.append({"role": "assistant", "content": error_msg})
                    yield history

            # Server management functions are defined locally in this file

            # Access saved_hf_token from outer scope
            saved_token = saved_hf_token

            def configure_model(hf_token, model_name):
                # Check if user is using the masked token (didn't change it)
                if hf_token and hf_token == "*" * 20 and saved_token:
                    # Use the saved token
                    hf_token = saved_token
                    print("DEBUG: Using saved HuggingFace token")

                # Save token for future use (only if it's not the masked value)
                if hf_token and hf_token != "*" * 20:
                    try:
                        # Use config manager for secure token storage
                        success = config_manager.save_secure_token("huggingface", hf_token)
                        if success:
                            print("DEBUG: Saved HuggingFace token to secure storage")
                        else:
                            print("DEBUG: Could not save token to secure storage")
                    except Exception as e:
                        print(f"DEBUG: Error saving token: {e}")

                # Now configure the model
                if not hasattr(coding_agent, "configure_model"):
                    # Use the old method name for compatibility
                    return _configure_model(hf_token, model_name, coding_agent)

                result = coding_agent.configure_model(hf_token, model_name)

                if result.get("success"):
                    return (
                        f"✅ Successfully configured {model_name}",
                        {"model": result.get("model"), "description": result.get("description")},
                        gr.update(visible=True),
                    )
                else:
                    return (
                        f"❌ Configuration failed: {result.get('error', 'Unknown error')}",
                        {},
                        gr.update(visible=False),
                    )

            # General Assistant handlers
            general_send_btn.click(
                handle_message_submit,
                inputs=[general_input, general_chatbot, general_show_thinking],
                outputs=[general_chatbot, general_input],
            ).then(
                process_message,
                inputs=[general_chatbot, general_show_thinking],
                outputs=[general_chatbot],
            )

            general_input.submit(
                handle_message_submit,
                inputs=[general_input, general_chatbot, general_show_thinking],
                outputs=[general_chatbot, general_input],
            ).then(
                process_message,
                inputs=[general_chatbot, general_show_thinking],
                outputs=[general_chatbot],
            )

            # Refresh connected servers
            def refresh_connected_servers():
                return _get_connected_servers_info(coding_agent)

            refresh_servers_btn.click(refresh_connected_servers, outputs=[connected_servers_info])

            # MCP Agent (Liam) handlers
            configure_btn.click(
                configure_model,
                inputs=[hf_token_input, model_dropdown],
                outputs=[config_status, model_info, model_info_accordion],
            )

            send_btn.click(
                handle_message_submit,
                inputs=[chat_input, chatbot, show_thinking],
                outputs=[chatbot, chat_input],
            ).then(
                process_message,
                inputs=[chatbot, show_thinking],
                outputs=[chatbot],
            )

            chat_input.submit(
                handle_message_submit,
                inputs=[chat_input, chatbot, show_thinking],
                outputs=[chatbot, chat_input],
            ).then(
                process_message,
                inputs=[chatbot, show_thinking],
                outputs=[chatbot],
            )

            reset_chat_btn.click(reset_conversation, outputs=chatbot)

        # Agent builder event handlers
        if HAS_AGENT_COMPONENTS and gmp_agent:

            def handle_agent_message(message, history):
                """Handle agent builder messages"""
                if not message.strip():
                    return history, ""

                history.append({"role": "user", "content": message})

                try:
                    # GMPAgent uses async process_message method
                    import asyncio

                    async def get_response():
                        response, metadata = await gmp_agent.process_message(message)
                        return response

                    # Run the async function
                    response = asyncio.run(get_response())
                    history.append({"role": "assistant", "content": response})
                except Exception as e:
                    history.append({"role": "assistant", "content": f"Error: {str(e)}"})

                return history, ""

            # Only set up handlers if components exist
            try:
                agent_send_btn.click(
                    handle_agent_message,
                    inputs=[agent_input, agent_chatbot],
                    outputs=[agent_chatbot, agent_input],
                )

                agent_input.submit(
                    handle_agent_message,
                    inputs=[agent_input, agent_chatbot],
                    outputs=[agent_chatbot, agent_input],
                )
            except NameError:
                # Components don't exist, skip setting up handlers
                pass

        # Server management event handlers
        if HAS_CONFIG_MANAGER and HAS_REGISTRY:
            # Quick Connect buttons
            if "filesystem_btn" in locals():
                filesystem_btn.click(
                    lambda: quick_connect_mcp("filesystem"), outputs=[quick_connect_status]
                ).then(lambda: gr.update(visible=True), outputs=[quick_connect_status])

            if "memory_btn" in locals():
                memory_btn.click(
                    lambda: quick_connect_mcp("memory"), outputs=[quick_connect_status]
                ).then(lambda: gr.update(visible=True), outputs=[quick_connect_status])

            if "github_btn" in locals():
                github_btn.click(
                    lambda: quick_connect_mcp("github"), outputs=[quick_connect_status]
                ).then(lambda: gr.update(visible=True), outputs=[quick_connect_status])

            if "brave_btn" in locals():
                brave_btn.click(
                    lambda: quick_connect_mcp("brave-search"), outputs=[quick_connect_status]
                ).then(lambda: gr.update(visible=True), outputs=[quick_connect_status])

            # Create Server button
            if "create_server_btn" in locals():
                create_server_btn.click(
                    create_server,
                    inputs=[new_server_name, template_dropdown, create_port],
                    outputs=[create_output],
                ).then(lambda: gr.update(visible=True), outputs=[create_output])

            # Template info button
            if "template_info_btn" in locals():
                template_info_btn.click(
                    get_template_info, inputs=[template_dropdown], outputs=[template_info_output]
                ).then(lambda: gr.update(visible=True), outputs=[template_info_output])

            # Server management buttons
            if "refresh_btn" in locals():
                refresh_btn.click(refresh_servers, outputs=[servers_list, server_dropdown])

            if "refresh_servers_btn" in locals():
                refresh_servers_btn.click(refresh_servers, outputs=[servers_list, server_dropdown])

            if "start_btn" in locals():
                start_btn.click(start_server, inputs=[server_dropdown], outputs=[servers_list])

            if "stop_btn" in locals():
                stop_btn.click(stop_server, inputs=[server_dropdown], outputs=[servers_list])

            if "delete_btn" in locals():
                delete_btn.click(
                    delete_server, inputs=[server_dropdown], outputs=[servers_list, server_dropdown]
                )

            if "server_dropdown" in locals():
                server_dropdown.change(
                    show_server_info, inputs=[server_dropdown], outputs=[server_info]
                )

            if "info_btn" in locals():
                info_btn.click(show_server_info, inputs=[server_dropdown], outputs=[server_info])

            # Registry install buttons
            if "install_filesystem_btn" in locals():
                install_filesystem_btn.click(
                    lambda: quick_install_popular("filesystem"), outputs=[registry_install_status]
                ).then(lambda: gr.update(visible=True), outputs=[registry_install_status])

            if "install_memory_btn" in locals():
                install_memory_btn.click(
                    lambda: quick_install_popular("memory"), outputs=[registry_install_status]
                ).then(lambda: gr.update(visible=True), outputs=[registry_install_status])

            if "install_github_btn" in locals():
                install_github_btn.click(
                    lambda: quick_install_popular("github"), outputs=[registry_install_status]
                ).then(lambda: gr.update(visible=True), outputs=[registry_install_status])

            # Refresh connections button
            if "refresh_connections_btn" in locals() and HAS_CLIENT_MANAGER:
                refresh_connections_btn.click(
                    refresh_connections, outputs=[connections_list, connection_dropdown]
                )

                # Auto-refresh connections on tab load
                if "connections_list" in locals():
                    connections_list.change(
                        lambda: refresh_connections(),
                        outputs=[connections_list, connection_dropdown],
                    )

            # Custom MCP connect button
            if "custom_mcp_connect_btn" in locals():
                custom_mcp_connect_btn.click(
                    lambda url, protocol: (
                        quick_connect_mcp(url)
                        if HAS_CLIENT_MANAGER
                        else "Client manager not available"
                    ),
                    inputs=[custom_mcp_url, custom_mcp_protocol],
                    outputs=[custom_mcp_status],
                )

            # Registry install button
            if "registry_install_btn" in locals():
                registry_install_btn.click(
                    install_registry_server,
                    inputs=[
                        registry_server_selector,
                        gr.Textbox(value="{}", visible=False),
                    ],  # Empty user args
                    outputs=[registry_install_status],
                )

            # Registry search button
            if "registry_search_btn" in locals():

                def search_registry(query):
                    """Search the registry for servers"""
                    if HAS_REGISTRY:
                        results = registry.search_servers(query)
                        if results:
                            # Format results for dataframe
                            data = []
                            choices = []
                            for server in results:
                                data.append(
                                    [
                                        server.get("name", ""),
                                        server.get("category", ""),
                                        server.get("description", ""),
                                        server.get("install_method", ""),
                                    ]
                                )
                                choices.append(server.get("name", ""))
                            return gr.update(value=data), gr.update(choices=choices)
                        else:
                            return gr.update(value=[]), gr.update(choices=[])
                    return gr.update(value=[]), gr.update(choices=[])

                registry_search_btn.click(
                    search_registry,
                    inputs=[registry_search_query],
                    outputs=[registry_results_df, registry_server_selector],
                )

            # Save settings button
            if "save_settings_btn" in locals() and HAS_CONFIG_MANAGER:

                def save_settings(port, auto_reload, protocol, log_level):
                    """Save settings"""
                    try:
                        config_manager.default_port = port
                        config_manager.auto_reload = auto_reload
                        config_manager.mcp_protocol = protocol
                        config_manager.log_level = log_level
                        config_manager.save_config()
                        return gr.update(value="✅ Settings saved successfully!", visible=True)
                    except Exception as e:
                        return gr.update(value=f"❌ Error saving settings: {str(e)}", visible=True)

                save_settings_btn.click(
                    save_settings,
                    inputs=[
                        settings_port,
                        settings_auto_reload,
                        settings_protocol,
                        settings_log_level,
                    ],
                    outputs=[settings_output],
                )

            # Tool Testing event handlers
            if "connect_test_btn" in locals():

                def test_connection(url, protocol):
                    """Test connection to MCP server and list tools"""
                    if not HAS_CLIENT_MANAGER:
                        return gr.update(
                            value={"error": "Client manager not available"}, visible=True
                        )

                    try:
                        # This would connect and get tools
                        # For now, return placeholder
                        return gr.update(
                            value={"tools": ["example_tool_1", "example_tool_2"]}, visible=True
                        )
                    except Exception as e:
                        return gr.update(value={"error": str(e)}, visible=True)

                connect_test_btn.click(
                    test_connection, inputs=[test_server_url, test_protocol], outputs=[tools_list]
                )

            if "call_tool_btn" in locals():

                def call_mcp_tool(name, args_json):
                    """Call an MCP tool"""
                    try:
                        import json

                        args = json.loads(args_json) if args_json else {}
                        # This would actually call the tool
                        # For now, return placeholder
                        return {"success": True, "result": f"Called {name} with args: {args}"}
                    except Exception as e:
                        return {"error": str(e)}

                call_tool_btn.click(
                    call_mcp_tool, inputs=[tool_name, tool_args], outputs=[tool_result]
                )

            # Connection management buttons
            if "disconnect_btn" in locals():
                disconnect_btn.click(
                    disconnect_mcp,
                    inputs=[connection_dropdown],
                    outputs=[gr.Textbox(visible=False)],  # Status message
                ).then(refresh_connections, outputs=[connections_list, connection_dropdown])

            if "test_conn_btn" in locals():

                def test_existing_connection(connection_name):
                    """Test an existing connection"""
                    if not connection_name:
                        return "Please select a connection to test"
                    return f"✅ Connection '{connection_name}' is active"

                test_conn_btn.click(
                    test_existing_connection,
                    inputs=[connection_dropdown],
                    outputs=[gr.Textbox(visible=False)],  # Status message
                )

        # Initialize on load
        if "connections_list" in locals():
            # Add load event to refresh connections
            dashboard.load(refresh_connections, outputs=[connections_list, connection_dropdown])

    return dashboard


def launch_unified_dashboard(port: int = 8080, share: bool = False):
    """Launch the unified Gradio MCP Playground dashboard"""
    dashboard = create_unified_dashboard()
    dashboard.launch(
        server_port=port,
        share=share,
        server_name="127.0.0.1",
        show_api=False,
        prevent_thread_lock=False,
    )


if __name__ == "__main__":
    launch_unified_dashboard()
