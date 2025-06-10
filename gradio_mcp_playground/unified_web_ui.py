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

# Suppress Pydantic warning
warnings.filterwarnings("ignore", message="Field \"model_name\" has conflict with protected namespace \"model_\"", category=UserWarning)

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
    if not coding_agent or not hasattr(coding_agent, '_mcp_servers'):
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

    # Initialize connection manager if available
    if HAS_CLIENT_MANAGER:
        connection_manager = MCPConnectionManager()
    else:
        connection_manager = None

    # Initialize coding agent if available
    coding_agent = None
    coding_agent_error = None
    if HAS_CODING_AGENT:
        try:
            coding_agent = CodingAgent()
            # Try to configure with stored HF token if available
            if hasattr(config_manager, 'hf_token') and config_manager.hf_token:
                try:
                    # Get available models
                    models = coding_agent.get_available_models()
                    if models:
                        # Use first available model
                        model_name = list(models.keys())[0]
                        coding_agent.configure(config_manager.hf_token, model_name)
                        print(f"Configured coding agent with {model_name}")
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
                # Mode selector with three modes
                with gr.Row(elem_classes=["agent-mode-selector"]):
                    assistant_mode = gr.Radio(
                        choices=["Assistant", "MCP Agent", "Agent Builder"],
                        value="Assistant",
                        label="Assistant Mode",
                        info="Choose your assistant type: General Assistant with MCP tools | MCP-focused development | Custom agent creation"
                    )

                # General Assistant Mode (conversational with MCP agency)
                with gr.Group(visible=True) as general_assistant_group:
                    if coding_agent:
                        gr.Markdown("### Claude - General Assistant with MCP Tools")
                        gr.Markdown(
                            "I'm Claude, your general-purpose assistant with access to all connected MCP tools. I can help with any task using the available servers."
                        )

                        # Show connected MCP servers
                        with gr.Row():
                            connected_servers_info = gr.Markdown(
                                value=_get_connected_servers_info(coding_agent)
                            )
                            refresh_servers_btn = gr.Button("🔄 Refresh", size="sm", variant="secondary")

                        # General chat interface
                        general_chatbot = gr.Chatbot(
                            label="Chat with Claude",
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
                                # Get available models and set a valid default
                                available_models = list(coding_agent.get_available_models().keys()) if coding_agent else []
                                default_model = available_models[0] if available_models else None
                                
                                model_dropdown = gr.Dropdown(
                                    label="Select Model",
                                    choices=available_models,
                                    value=default_model,
                                    info="Choose a model for the AI assistant",
                                )

                        with gr.Row():
                            configure_btn = gr.Button("🔧 Configure Model", variant="primary")
                            reset_chat_btn = gr.Button("🔄 Reset Chat", variant="secondary")

                        config_status = gr.Textbox(
                            label="Configuration Status",
                            value="Not configured - please enter your HuggingFace token and configure a model",
                            interactive=False,
                        )

                        # Model info display in collapsible section
                        with gr.Accordion("📊 Selected Model Information", open=False, visible=False) as model_info_accordion:
                            model_info = gr.JSON(label="", visible=True)

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
                        gr.Markdown("### Architect - Agent Builder")
                        gr.Markdown(
                            "I'm Architect, your agent creation specialist. I can help you create custom Gradio agents using system prompts from top AI assistants."
                        )
                        
                        # Agent builder chat interface
                        agent_chatbot = gr.Chatbot(
                            label="Agent Builder Assistant",
                            height=500,
                            show_copy_button=True,
                            type="messages",
                            bubble_full_width=True,
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
                            try:
                                pipeline_view = PipelineView(gmp_agent)
                                pipeline_view.create_interface()
                            except Exception as e:
                                gr.Markdown("### Visual Pipeline Builder")
                                gr.Markdown(f"Pipeline builder initialization error: {str(e)}")
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
                        
                        templates_gallery = gr.Gallery(
                            label="Available Templates",
                            show_label=False,
                            columns=3,
                            height="auto"
                        )

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
                        
                        registry_install_btn = gr.Button("📥 Install Selected Server", variant="primary")
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
                        # Predefined servers grid
                        gr.HTML(
                            """
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin: 16px 0;">
                                <div class="mcp-connection-card">
                                    <h4>📁 Filesystem Server</h4>
                                    <p>Secure file operations with configurable access controls.</p>
                                    <button onclick="quickConnect('filesystem')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Connect</button>
                                </div>
                                <div class="mcp-connection-card">
                                    <h4>🧠 Memory Server</h4>
                                    <p>Knowledge graph-based persistent memory system.</p>
                                    <button onclick="quickConnect('memory')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Connect</button>
                                </div>
                                <div class="mcp-connection-card">
                                    <h4>🐙 GitHub Server</h4>
                                    <p>Access GitHub repositories, issues, and PRs.</p>
                                    <button onclick="quickConnect('github')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Connect</button>
                                </div>
                                <div class="mcp-connection-card">
                                    <h4>🔍 Brave Search</h4>
                                    <p>Web search with privacy focus.</p>
                                    <button onclick="quickConnect('brave-search')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Connect</button>
                                </div>
                            </div>
                            """
                        )
                    
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
                                control_panel = ControlPanelUI()
                                control_panel.create_interface()
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
                        precision=0
                    )
                    settings_auto_reload = gr.Checkbox(
                        label="Auto-reload on file changes", 
                        value=config_manager.auto_reload if HAS_CONFIG_MANAGER else False
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
            outputs=[general_assistant_group, mcp_agent_group, agent_builder_group]
        )
        
        # Event handlers for all assistant modes
        if coding_agent:
            # Import event handler functions from web_ui
            from .web_ui import (
                handle_message_submit,
                process_message as _process_message,
                reset_conversation,
                configure_model as _configure_model
            )
            
            # Create wrapper functions that include the coding_agent parameter
            def process_message(history, show_thinking):
                return _process_message(history, show_thinking, coding_agent)
            
            def configure_model(hf_token, model_name):
                return _configure_model(hf_token, model_name, coding_agent)
            
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
            
            refresh_servers_btn.click(
                refresh_connected_servers,
                outputs=[connected_servers_info]
            )
            
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
                    response = gmp_agent.chat(message)
                    history.append({"role": "assistant", "content": response})
                except Exception as e:
                    history.append({"role": "assistant", "content": f"Error: {str(e)}"})
                
                return history, ""
            
            agent_send_btn.click(
                handle_agent_message,
                inputs=[agent_input, agent_chatbot],
                outputs=[agent_chatbot, agent_input]
            )
            
            agent_input.submit(
                handle_agent_message,
                inputs=[agent_input, agent_chatbot],
                outputs=[agent_chatbot, agent_input]
            )
        
        # Initialize greetings for different modes
        if coding_agent:
            def initialize_general_greeting():
                """General assistant greeting"""
                greeting = "👋 Hello! I'm Claude, your general assistant with access to MCP tools.\n\n"
                
                # Show available tools
                if hasattr(coding_agent, '_mcp_servers') and coding_agent._mcp_servers:
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
                if hasattr(coding_agent, '_mcp_servers') and coding_agent._mcp_servers:
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
            
            # Load appropriate greeting based on default mode
            dashboard.load(initialize_general_greeting, outputs=[general_chatbot])
            dashboard.load(initialize_liam_greeting, outputs=[chatbot])

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