"""Gradio MCP Playground Web UI

Web-based dashboard for managing Gradio MCP servers.
"""

import warnings
import json
import os
from pathlib import Path

# Suppress Pydantic model_name warning
warnings.filterwarnings("ignore", message="Field \"model_name\" has conflict with protected namespace \"model_\"", category=UserWarning)

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


# Module-level functions for unified dashboard
def handle_message_submit(message, history, show_thinking):
    """Handle message submission with immediate display"""
    if not message.strip():
        return history, ""
    
    # Clear input immediately and show user message
    history_with_user = history + [{"role": "user", "content": message}]
    
    # Return cleared input and updated history, then process
    return history_with_user, ""


def process_message(history, show_thinking, coding_agent):
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
            # Try to configure with default model without requiring token
            try:
                # Use a free model that doesn't require API key
                coding_agent.configure("", "microsoft/Phi-3.5-mini-instruct")
            except:
                bot_response = (
                    "I'm having trouble initializing. Please try switching to MCP Agent mode to configure a model with your HuggingFace token."
                )
                history.append({"role": "assistant", "content": bot_response})
                yield history
                return
        
        # Your existing message processing logic here...
        # Check if user is providing an API key in a natural way
        import re
        
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
        
        # Pattern 3: "my brave api key is YOUR_KEY"
        brave_key_statement = re.search(
            r"(?:my )?brave (?:api )?key (?:is |= ?)([\w-]+)", message, re.IGNORECASE
        )
        if brave_key_statement:
            api_key = brave_key_statement.group(1)
            message = f"I have your Brave API key. Let me install the brave search server: install_mcp_server_from_registry(server_id='brave-search', token='{api_key}')"
        
        # Pattern 4: "use path /home/user/workspace" (for filesystem server)
        path_statement = re.search(
            r"(?:use |provide )?path (?:is |= ?)?([/\\][^\s]+)", message, re.IGNORECASE
        )
        if path_statement:
            path = path_statement.group(1)
            message = f"I'll use path '{path}' for the filesystem server: install_mcp_server_from_registry(server_id='filesystem', path='{path}')"
        
        # Pattern 5: "my obsidian vault is at /path/to/vault"
        vault_statement = re.search(
            r"(?:my )?obsidian vault (?:is )?(?:at |in )?([/\\][^\s]+)",
            message,
            re.IGNORECASE,
        )
        if vault_statement:
            vault_path = vault_statement.group(1)
            message = f"I'll use your Obsidian vault at '{vault_path}': install_mcp_server_from_registry(server_id='obsidian', vault_path1='{vault_path}')"
        
        # Pattern 6: "my github token is YOUR_TOKEN"
        github_token_statement = re.search(
            r"(?:my )?github (?:token|pat|personal access token) (?:is |= ?)([\w-]+)",
            message,
            re.IGNORECASE,
        )
        if github_token_statement:
            token = github_token_statement.group(1)
            message = f"I have your GitHub token. Let me install the GitHub server: install_mcp_server_from_registry(server_id='github', token='{token}')"
        
        # Process with agent
        if show_thinking:
            steps, bot_response = coding_agent.chat_with_steps(message)
            
            # Show thinking steps progressively
            thinking_content = "## 🧠 AI Thinking Process\n\n"
            for step in steps:
                thinking_content += f"{step}\n\n"
                history[-1] = {"role": "assistant", "content": thinking_content}
                yield history
            
            # Add final response
            full_response = thinking_content + "---\n\n## 💬 Final Response\n\n" + bot_response
            history[-1] = {"role": "assistant", "content": full_response}
        else:
            # Regular chat without steps
            full_response = coding_agent.chat(message)
            history.append({"role": "assistant", "content": full_response})
        
        # Check and enhance response with helpful prompts
        if "Missing required arguments:" in full_response and "Example for" in full_response:
            # Extract server ID and missing arguments
            server_match = re.search(r"Example for ([\w-]+):", full_response)
            args_match = re.search(r"Missing required arguments: \[([^\]]+)\]", full_response)
            
            if server_match and args_match:
                server_id = server_match.group(1)
                missing_args = [arg.strip().strip("'") for arg in args_match.group(1).split(",")]
                
                # Create a helpful prompt for the user
                api_key_prompt = "\n\n🔑 **API Key Required**\n\n"
                api_key_prompt += f"The {server_id} server requires the following:"
                
                for arg in missing_args:
                    if "token" in arg.lower() or "key" in arg.lower():
                        api_key_prompt += f"\n- **{arg}**: Please provide your API key"
                    else:
                        api_key_prompt += f"\n- **{arg}**: Please provide the required value"
                
                api_key_prompt += "\n\nPlease provide the required information in your next message."
                api_key_prompt += "\n\nExample: `install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"
                
                full_response += api_key_prompt
                history[-1]["content"] = full_response
        
        # Check if Brave Search API key is needed
        elif "BRAVE_API_KEY not set" in full_response:
            api_key_prompt = "\n\n🔑 **Brave Search API Key Required**\n\n"
            api_key_prompt += "To use Brave Search, you need to provide an API key.\n\n"
            api_key_prompt += "🌐 **Get your API key:**\n"
            api_key_prompt += "1. Visit https://brave.com/search/api/\n"
            api_key_prompt += "2. Sign up for a free account\n"
            api_key_prompt += "3. Copy your API key\n\n"
            api_key_prompt += "🔧 **To install with your key:**\n"
            api_key_prompt += "Please type: `install brave search with key YOUR_API_KEY_HERE`\n\n"
            api_key_prompt += "Or use the exact command:\n"
            api_key_prompt += "`install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"
            
            # Replace the error message with the helpful prompt
            if "Error: BRAVE_API_KEY not set" in full_response:
                full_response = full_response.split("Error: BRAVE_API_KEY not set")[0] + api_key_prompt
            else:
                full_response += api_key_prompt
            
            history[-1]["content"] = full_response
        
        yield history
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append({"role": "assistant", "content": error_msg})
        yield history


def reset_conversation():
    """Reset the conversation and provide a fresh greeting"""
    # Count connected servers
    initial_greeting = "👋 Hi! I'm Liam, your MCP coding assistant.\n\n"
    initial_greeting += "I can help you:\n"
    initial_greeting += "• 🔍 Research and find MCP servers\n"
    initial_greeting += "• 🔧 Build custom MCP servers\n"
    initial_greeting += "• 🧪 Test server functionality\n"
    initial_greeting += "• 📦 Install servers from the registry\n"
    initial_greeting += "• 🔌 Connect and configure servers\n\n"
    initial_greeting += "💡 **Quick commands:** `install memory` • `find database servers` • `what's MCP?`\n\n"
    initial_greeting += "What can I help you with today?"
    
    return [{"role": "assistant", "content": initial_greeting}]


def configure_model(hf_token, model_name, coding_agent):
    """Configure the AI model"""
    if not hf_token:
        return (
            "❌ Please provide a HuggingFace API token",
            {},
            gr.update(visible=False),
        )

    try:
        # Configure the agent
        coding_agent.configure(hf_token, model_name)

        # Get model info
        model_info = coding_agent.get_model_info()

        return (
            f"✅ Successfully configured {model_name}",
            model_info,
            gr.update(visible=True),
        )
    except Exception as e:
        return (
            f"❌ Configuration failed: {str(e)}",
            {},
            gr.update(visible=False),
        )


def create_dashboard():
    """Create the Gradio MCP Playground dashboard"""
    if not HAS_GRADIO:
        raise ImportError("Gradio is required for web dashboard functionality")

    config_manager = ConfigManager()
    registry = ServerRegistry()
    
    # Check if caching is disabled via environment variable
    use_cache = os.environ.get('GMP_DISABLE_CACHE', '').lower() not in ['1', 'true', 'yes']
    
    if use_cache:
        print("🚀 Cache enabled for faster startup")
    else:
        print("⚠️  Cache disabled (GMP_DISABLE_CACHE is set)")

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

    with gr.Blocks(
        title="Gradio MCP Playground",
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
    """,
    ) as dashboard:
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
                                    allow_custom_value=True,
                                    info="Select a server to manage",
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
                                    allow_custom_value=True,
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
                                test_server_btn = gr.Button(
                                    "🧪 Test Connection", variant="secondary"
                                )
                                connect_server_btn = gr.Button("🔗 Connect", variant="primary")

                        connection_output = gr.Textbox(label="Connection Output", visible=False)

            # Registry Tab - Enhanced MCP Server Registry
            with gr.Tab("📦 MCP Server Registry"):
                gr.Markdown("### 🚀 Discover & Install MCP Servers")
                gr.Markdown(
                    "Browse 80+ official and community MCP servers. Install with one click and connect to your coding agent."
                )

                with gr.Tabs():
                    # Search & Browse Tab
                    with gr.Tab("🔍 Search & Browse"):
                        with gr.Row():
                            with gr.Column(scale=2):
                                registry_search_query = gr.Textbox(
                                    label="Search Servers",
                                    placeholder="Search for filesystem, github, database, AI tools...",
                                    value="",
                                )
                            with gr.Column(scale=1):
                                registry_category_filter = gr.Dropdown(
                                    choices=["all"] + registry.list_categories("mcp_server"),
                                    label="Category",
                                    value="all",
                                )
                            with gr.Column(scale=1):
                                registry_server_type = gr.Dropdown(
                                    choices=["mcp_server", "template", "all"],
                                    label="Type",
                                    value="mcp_server",
                                )

                        with gr.Row():
                            registry_search_btn = gr.Button("🔍 Search", variant="primary", scale=1)
                            registry_show_all_btn = gr.Button(
                                "📋 Show All", variant="secondary", scale=1
                            )
                            registry_show_popular_btn = gr.Button(
                                "⭐ Popular", variant="secondary", scale=1
                            )

                        # Search Results
                        registry_results_df = gr.Dataframe(
                            headers=["Name", "Category", "Description", "Type", "Package"],
                            datatype=["str", "str", "str", "str", "str"],
                            interactive=False,
                            label="Available Servers",
                            wrap=True,
                            column_widths=[200, 100, 400, 100, 200],
                        )

                    # Server Details Tab
                    with gr.Tab("📋 Server Details"):
                        with gr.Row():
                            with gr.Column(scale=2):
                                registry_server_selector = gr.Dropdown(
                                    label="Select Server",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                    allow_custom_value=True,
                                )

                                # Server Information Display
                                registry_server_name = gr.Textbox(
                                    label="Server Name", interactive=False
                                )
                                registry_server_description = gr.Textbox(
                                    label="Description", lines=3, interactive=False
                                )
                                registry_server_category = gr.Textbox(
                                    label="Category", interactive=False
                                )
                                registry_server_package = gr.Textbox(
                                    label="Package", interactive=False
                                )
                                registry_server_install_method = gr.Textbox(
                                    label="Install Method", interactive=False
                                )
                                registry_server_homepage = gr.Textbox(
                                    label="Homepage", interactive=False
                                )

                                # Setup Requirements
                                gr.Markdown("#### Setup Requirements")
                                registry_server_setup_help = gr.Textbox(
                                    label="Setup Help", lines=3, interactive=False
                                )
                                registry_server_example_usage = gr.Textbox(
                                    label="Example Usage", lines=2, interactive=False
                                )

                            with gr.Column(scale=1):
                                gr.Markdown("#### Installation")

                                # Required Arguments
                                registry_required_args = gr.JSON(
                                    label="Required Arguments", value={}
                                )
                                registry_env_vars = gr.JSON(label="Environment Variables", value={})

                                # User Input for Arguments
                                gr.Markdown("#### Configuration")
                                registry_user_args = gr.JSON(
                                    label="Provide Required Arguments & Environment Variables",
                                    value={},
                                )

                                # Install Actions
                                with gr.Row():
                                    registry_install_btn = gr.Button(
                                        "📦 Install & Connect", variant="primary"
                                    )
                                    registry_copy_command_btn = gr.Button(
                                        "📋 Copy Command", variant="secondary"
                                    )

                                registry_install_status = gr.Textbox(
                                    label="Installation Status", interactive=False, lines=8
                                )

                    # Categories Tab
                    with gr.Tab("📂 Categories"):
                        gr.Markdown("### Browse by Category")

                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### 🏢 Official Servers")
                                official_servers_list = gr.Dataframe(
                                    headers=["Name", "Description"],
                                    datatype=["str", "str"],
                                    interactive=False,
                                    wrap=True,
                                )

                            with gr.Column():
                                gr.Markdown("#### 🌟 Community Servers")
                                community_servers_list = gr.Dataframe(
                                    headers=["Name", "Description"],
                                    datatype=["str", "str"],
                                    interactive=False,
                                    wrap=True,
                                )

                        refresh_categories_btn = gr.Button("🔄 Refresh Categories")

                    # Popular Servers Tab
                    with gr.Tab("⭐ Popular"):
                        gr.Markdown("### Most Popular MCP Servers")

                        popular_servers_grid = gr.HTML(
                            """
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin: 16px 0;">
                            <div class="mcp-connection-card">
                                <h4>📁 Filesystem Server</h4>
                                <p>Secure file operations with configurable access controls. Most essential MCP server.</p>
                                <button onclick="populateServer('filesystem')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Install</button>
                            </div>
                            <div class="mcp-connection-card">
                                <h4>🧠 Memory Server</h4>
                                <p>Knowledge graph-based persistent memory system for conversations.</p>
                                <button onclick="populateServer('memory')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Install</button>
                            </div>
                            <div class="mcp-connection-card">
                                <h4>🐙 GitHub Server</h4>
                                <p>Access GitHub repositories, issues, PRs, and code management.</p>
                                <button onclick="populateServer('github')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Install</button>
                            </div>
                            <div class="mcp-connection-card">
                                <h4>🔍 Brave Search</h4>
                                <p>Web search capabilities with privacy focus using Brave Search API.</p>
                                <button onclick="populateServer('brave-search')" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Install</button>
                            </div>
                        </div>
                        """
                        )

                # Quick Popular Servers Actions
                with gr.Row():
                    popular_filesystem_btn = gr.Button("📁 Install Filesystem", variant="primary")
                    popular_memory_btn = gr.Button("🧠 Install Memory", variant="primary")
                    popular_github_btn = gr.Button("🐙 Install GitHub", variant="primary")

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
                gr.Markdown(
                    "Connect to multiple MCP servers simultaneously for enhanced capabilities"
                )

                # Predefined MCP server configurations with auto-install
                predefined_servers = {
                    "memory": {
                        "name": "Memory Server",
                        "server_id": "memory",
                        "url": "npx -y @modelcontextprotocol/server-memory",
                        "protocol": "stdio",
                        "description": "Persistent memory storage for conversations and data",
                        "icon": "🧠",
                        "auto_install": True,
                    },
                    "sequential-thinking": {
                        "name": "Sequential Thinking",
                        "server_id": "sequential-thinking",
                        "url": "npx -y @modelcontextprotocol/server-sequential-thinking",
                        "protocol": "stdio",
                        "description": "Step-by-step reasoning and problem solving",
                        "icon": "🤔",
                        "auto_install": True,
                    },
                    "filesystem": {
                        "name": "File System",
                        "server_id": "filesystem",
                        "url": "npx -y @modelcontextprotocol/server-filesystem",
                        "protocol": "stdio",
                        "description": "File system access and manipulation",
                        "icon": "📁",
                        "auto_install": True,
                        "requires_path": True,
                    },
                    "brave-search": {
                        "name": "Brave Search",
                        "server_id": "brave-search",
                        "url": "npx -y @modelcontextprotocol/server-brave-search",
                        "protocol": "stdio",
                        "description": "Web search capabilities using Brave",
                        "icon": "🔍",
                        "auto_install": True,
                        "requires_env": ["BRAVE_API_KEY"],
                    },
                    "github": {
                        "name": "GitHub",
                        "server_id": "github",
                        "url": "npx -y @modelcontextprotocol/server-github",
                        "protocol": "stdio",
                        "description": "GitHub repository and issue management",
                        "icon": "🐙",
                        "auto_install": True,
                        "requires_env": ["GITHUB_TOKEN"],
                    },
                    "time": {
                        "name": "Time Server",
                        "server_id": "time",
                        "url": "uvx mcp-server-time",
                        "protocol": "stdio",
                        "description": "Time and date utilities",
                        "icon": "⏰",
                        "auto_install": True,
                        "requires_timezone": True,
                    },
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
                            for i, (server_id, server_info) in enumerate(
                                list(predefined_servers.items())[:3]
                            ):
                                with gr.Column():
                                    with gr.Group():
                                        gr.Markdown(
                                            f"### {server_info['icon']} {server_info['name']}"
                                        )
                                        gr.Markdown(server_info["description"])

                                        server_statuses[server_id] = gr.Textbox(
                                            label="Status",
                                            value="Not Connected",
                                            interactive=False,
                                            elem_id=f"status_{server_id}",
                                        )

                                        with gr.Row():
                                            server_buttons[server_id] = gr.Button(
                                                "Connect",
                                                variant="primary",
                                                elem_id=f"connect_{server_id}",
                                                scale=1,
                                            )

                                            server_install_buttons[server_id] = gr.Button(
                                                "Auto-Install & Connect",
                                                variant="secondary",
                                                elem_id=f"install_{server_id}",
                                                scale=1,
                                            )

                        # Create cards for remaining servers
                        with gr.Row():
                            for i, (server_id, server_info) in enumerate(
                                list(predefined_servers.items())[3:]
                            ):
                                with gr.Column():
                                    with gr.Group():
                                        gr.Markdown(
                                            f"### {server_info['icon']} {server_info['name']}"
                                        )
                                        gr.Markdown(server_info["description"])

                                        server_statuses[server_id] = gr.Textbox(
                                            label="Status",
                                            value="Not Connected",
                                            interactive=False,
                                            elem_id=f"status_{server_id}",
                                        )

                                        with gr.Row():
                                            server_buttons[server_id] = gr.Button(
                                                "Connect",
                                                variant="primary",
                                                elem_id=f"connect_{server_id}",
                                                scale=1,
                                            )

                                            server_install_buttons[server_id] = gr.Button(
                                                "Auto-Install & Connect",
                                                variant="secondary",
                                                elem_id=f"install_{server_id}",
                                                scale=1,
                                            )

                        # Bulk actions
                        with gr.Row():
                            connect_all_mcp_btn = gr.Button("🔗 Connect All", variant="primary")
                            disconnect_all_mcp_btn = gr.Button("🔌 Disconnect All", variant="stop")
                            refresh_mcp_status_btn = gr.Button("🔄 Refresh Status")

                        mcp_bulk_status = gr.Textbox(
                            label="Bulk Action Status", interactive=False, lines=3
                        )

                        # Installation progress display
                        gr.Markdown("### 📦 Installation Progress")
                        mcp_install_progress = gr.Textbox(
                            label="Installation Progress", interactive=False, lines=8, visible=False
                        )

                    # Active MCP Connections Tab
                    with gr.Tab("🔗 Active MCP Connections"):
                        gr.Markdown("### 📊 Active MCP Server Connections")

                        # MCP Connection list
                        mcp_connections_table = gr.Dataframe(
                            headers=["Server", "Type", "Status", "Tools", "URL"],
                            datatype=["str", "str", "str", "number", "str"],
                            interactive=False,
                            label="Active MCP Connections",
                        )

                        # MCP Connection details
                        with gr.Row():
                            with gr.Column(scale=2):
                                selected_mcp_connection = gr.Dropdown(
                                    label="Select MCP Connection",
                                    choices=[],
                                    value=None,
                                    interactive=True,
                                    allow_custom_value=True,
                                )

                                mcp_connection_details = gr.JSON(
                                    label="Connection Details", value={}
                                )

                                mcp_available_tools = gr.Dataframe(
                                    headers=["Tool Name", "Description", "Parameters"],
                                    datatype=["str", "str", "str"],
                                    interactive=False,
                                    label="Available Tools",
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
                                    interactive=True,
                                    allow_custom_value=True,
                                )

                                mcp_tool_args = gr.JSON(label="Tool Arguments", value={})

                                call_mcp_tool_btn = gr.Button("📞 Call Tool", variant="primary")

                                mcp_tool_result = gr.JSON(label="Tool Result", value={})

                    # Custom MCP Connection Tab
                    with gr.Tab("➕ Custom MCP Connection"):
                        gr.Markdown("### 🔧 Connect to Custom MCP Server")

                        with gr.Row():
                            with gr.Column():
                                custom_mcp_name = gr.Textbox(
                                    label="Connection Name",
                                    placeholder="my-custom-server",
                                    value="",
                                )

                                custom_mcp_url = gr.Textbox(
                                    label="Server URL/Command",
                                    placeholder="python -m my_mcp_server or http://localhost:8080/mcp",
                                    value="",
                                    lines=2,
                                )

                                custom_mcp_protocol = gr.Radio(
                                    label="Protocol",
                                    choices=["auto", "stdio", "sse", "gradio"],
                                    value="auto",
                                )

                                custom_mcp_description = gr.Textbox(
                                    label="Description (optional)",
                                    placeholder="What does this server do?",
                                    value="",
                                    lines=2,
                                )

                                custom_mcp_connect_btn = gr.Button("🔗 Connect", variant="primary")

                            with gr.Column():
                                gr.Markdown("### 📖 Connection Guide")
                                gr.Markdown(
                                    """
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
                                """
                                )

                        custom_mcp_status = gr.Textbox(
                            label="Connection Status", interactive=False, lines=3
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

        # Registry Functions
        def search_registry_servers(query, category, server_type):
            """Search for servers in the registry"""
            try:
                if not query.strip() and category == "all":
                    # Show popular servers by default
                    popular_ids = [
                        "filesystem",
                        "memory",
                        "github",
                        "brave-search",
                        "sequential-thinking",
                        "time",
                    ]
                    results = []
                    for server_id in popular_ids:
                        server = registry.get_mcp_server(server_id)
                        if server:
                            results.append(
                                [
                                    server["name"],
                                    server["category"],
                                    (
                                        server["description"][:100] + "..."
                                        if len(server["description"]) > 100
                                        else server["description"]
                                    ),
                                    server["type"],
                                    server.get("package", ""),
                                ]
                            )
                    return results

                # Search with query/filters
                if query.strip():
                    results = registry.search(
                        query, category if category != "all" else None, server_type
                    )
                else:
                    results = (
                        registry.get_by_category(category, server_type)
                        if category != "all"
                        else registry.get_all(server_type)
                    )

                data = []
                for server in results[:50]:  # Limit to 50 results
                    data.append(
                        [
                            server["name"],
                            server["category"],
                            (
                                server["description"][:100] + "..."
                                if len(server["description"]) > 100
                                else server["description"]
                            ),
                            server["type"],
                            server.get("package", ""),
                        ]
                    )

                return data
            except Exception as e:
                return [["Error", "error", f"Error searching registry: {str(e)}", "error", ""]]

        def show_all_servers(server_type):
            """Show all servers"""
            try:
                servers = registry.get_all(server_type)[:50]  # Limit to 50
                data = []
                for server in servers:
                    data.append(
                        [
                            server["name"],
                            server["category"],
                            (
                                server["description"][:100] + "..."
                                if len(server["description"]) > 100
                                else server["description"]
                            ),
                            server["type"],
                            server.get("package", ""),
                        ]
                    )
                return data
            except Exception as e:
                return [["Error", "error", f"Error loading servers: {str(e)}", "error", ""]]

        def show_popular_servers():
            """Show popular servers"""
            popular_ids = [
                "filesystem",
                "memory",
                "github",
                "brave-search",
                "sequential-thinking",
                "postgres",
                "docker",
                "obsidian",
            ]
            data = []
            for server_id in popular_ids:
                server = registry.get_mcp_server(server_id)
                if server:
                    data.append(
                        [
                            server["name"],
                            server["category"],
                            (
                                server["description"][:100] + "..."
                                if len(server["description"]) > 100
                                else server["description"]
                            ),
                            "mcp_server",
                            server.get("package", ""),
                        ]
                    )
            return data

        def load_server_details(server_id):
            """Load detailed information for a selected server"""
            if not server_id:
                return "", "", "", "", "", "", "", "", {}, {}, {}

            try:
                server = registry.get_server_info(server_id)
                if not server:
                    return "Server not found", "", "", "", "", "", "", "", {}, {}, {}

                return (
                    server["name"],
                    server["description"],
                    server["category"],
                    server.get("package", ""),
                    server.get("install_method", ""),
                    server.get("homepage", ""),
                    server.get("setup_help", ""),
                    server.get("example_usage", ""),
                    {arg: f"Required argument: {arg}" for arg in server.get("required_args", [])},
                    server.get("env_vars", {}),
                    {},  # Empty user args to start
                )
            except Exception as e:
                return f"Error: {str(e)}", "", "", "", "", "", "", "", {}, {}, {}

        def install_registry_server(server_id, user_args):
            """Install a server from the registry and connect to coding agent"""
            if not server_id:
                return "No server selected"

            try:
                server_info = registry.get_server_info(server_id)
                if not server_info:
                    return "❌ Server not found in registry"

                progress = f"📦 Installing {server_info['name']}...\n\n"

                # Generate install command with user arguments
                install_cmd = registry.generate_install_command(server_id, user_args)
                if not install_cmd:
                    return (
                        progress
                        + "❌ Failed to generate install command. Check required arguments."
                    )

                progress += f"📋 Install Method: {install_cmd['install_method']}\n"
                progress += f"📦 Package: {install_cmd['package']}\n"
                progress += (
                    f"🔧 Command: {install_cmd['command']} {' '.join(install_cmd['args'])}\n\n"
                )

                # Use existing installation function based on server type
                if server_id in predefined_servers:
                    # Use existing predefined server installation
                    result = install_and_connect_mcp(server_id)
                    if "✅" in result:
                        progress += result + "\n\n"

                        # Connect to coding agent if available
                        if coding_agent:
                            progress += "🤖 Connecting to coding agent...\n"
                            try:
                                # Create mock connection info for coding agent
                                connection_info = {
                                    "name": server_info["name"],
                                    "tools": [],  # Will be populated when real connection is made
                                }

                                coding_agent.add_mcp_connection(server_id, connection_info)
                                progress += "✅ Connected to coding agent!\n\n"
                            except Exception as e:
                                progress += f"⚠️ Coding agent connection failed: {str(e)}\n\n"

                        progress += f"🎉 {server_info['name']} setup completed successfully!\n"
                        progress += f"💡 {server_info.get('example_usage', 'You can now use this server in the AI Assistant.')}"

                        return progress
                    else:
                        return progress + result
                else:
                    # Handle registry-only servers with detailed installation instructions
                    progress += f"📖 Installation Instructions for {server_info['name']}:\n\n"

                    if install_cmd["install_method"] == "npm":
                        progress += "Run this command:\n"
                        progress += f"npm install -g {install_cmd['package']}\n\n"
                    elif install_cmd["install_method"] == "uvx":
                        progress += "Run this command:\n"
                        progress += f"uvx {install_cmd['package']}\n\n"
                    elif install_cmd["install_method"] == "git":
                        progress += "Run this command:\n"
                        progress += f"git clone {install_cmd['package']}\n\n"

                    if install_cmd.get("env"):
                        progress += "Environment variables needed:\n"
                        for key, value in install_cmd["env"].items():
                            progress += f"  {key}={value}\n"
                        progress += "\n"

                    progress += f"🔗 Setup Help: {server_info.get('setup_help', 'See homepage for details')}\n"
                    progress += f"🌐 Homepage: {server_info.get('homepage', 'N/A')}\n\n"
                    progress += "After installation, restart the dashboard and the server will be available in MCP Connections."

                    return progress

            except Exception as e:
                return f"❌ Installation error: {str(e)}"

        def get_registry_server_choices():
            """Get list of server choices for dropdown"""
            try:
                servers = registry.get_all("mcp_server")
                choices = [
                    (f"{server['name']} ({server['id']})", server["id"]) for server in servers
                ]
                return gr.update(choices=choices)
            except Exception:
                return gr.update(choices=[])

        def refresh_categories_data():
            """Refresh category data"""
            try:
                official_servers = registry.get_by_category("official", "mcp_server")
                community_servers = registry.get_by_category("community", "mcp_server")

                official_data = [
                    [
                        s["name"],
                        (
                            s["description"][:100] + "..."
                            if len(s["description"]) > 100
                            else s["description"]
                        ),
                    ]
                    for s in official_servers
                ]
                community_data = [
                    [
                        s["name"],
                        (
                            s["description"][:100] + "..."
                            if len(s["description"]) > 100
                            else s["description"]
                        ),
                    ]
                    for s in community_servers
                ]

                return official_data, community_data
            except Exception as e:
                return [["Error", str(e)]], [["Error", str(e)]]

        def quick_install_popular(server_id):
            """Quick install for popular servers"""
            try:
                return install_and_connect_mcp(server_id)
            except Exception as e:
                return f"❌ Installation error: {str(e)}"

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
                    return "Please enter a valid HuggingFace API token", gr.update(visible=False), gr.update(visible=False)

                # First test the token independently
                token_valid, token_msg = test_hf_token_only(hf_token)
                if not token_valid:
                    return f"❌ Token Error: {token_msg}", gr.update(visible=False), gr.update(visible=False)

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

                    return status_msg, gr.update(value=enhanced_details), gr.update(visible=True)
                else:
                    return f"❌ Error: {result['error']}", gr.update(visible=False), gr.update(visible=False)

        else:

            def configure_model(hf_token, model_name):
                """Test token when LlamaIndex not available"""
                if not hf_token.strip():
                    return "Please enter a valid HuggingFace API token", gr.update(visible=False), gr.update(visible=False)

                token_valid, token_msg = test_hf_token_only(hf_token)
                if token_valid:
                    return (
                        f"✅ Token is valid! {token_msg}\nInstall LlamaIndex to use the AI assistant.",
                        gr.update(visible=False),
                        gr.update(visible=False)
                    )
                else:
                    return f"❌ {token_msg}", gr.update(visible=False), gr.update(visible=False)

        if coding_agent:

            def send_message(message, history, show_thinking_steps):
                """Send message to AI assistant"""
                # Show user message immediately
                if not message.strip():
                    return history, ""
                
                history.append({"role": "user", "content": message})
                
                if not coding_agent.is_configured():
                    bot_response = (
                        "Please configure a model first by providing your HuggingFace token."
                    )
                    history.append({"role": "assistant", "content": bot_response})
                    return history, ""

                # Check if user is providing an API key in a natural way
                import re

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
                    message = (
                        f"install_mcp_server_from_registry(server_id='github', token='{api_key}')"
                    )

                # Pattern 3: "my brave api key is YOUR_KEY"
                brave_key_statement = re.search(
                    r"(?:my )?brave (?:api )?key (?:is |= ?)([\w-]+)", message, re.IGNORECASE
                )
                if brave_key_statement:
                    api_key = brave_key_statement.group(1)
                    message = f"I have your Brave API key. Let me install the brave search server: install_mcp_server_from_registry(server_id='brave-search', token='{api_key}')"

                # Pattern 4: "use path /home/user/workspace" (for filesystem server)
                path_statement = re.search(
                    r"(?:use |provide )?path (?:is |= ?)?([/\\][^\s]+)", message, re.IGNORECASE
                )
                if path_statement:
                    path = path_statement.group(1)
                    message = f"I'll use path '{path}' for the filesystem server: install_mcp_server_from_registry(server_id='filesystem', path='{path}')"

                # Pattern 5: "my obsidian vault is at /path/to/vault"
                vault_statement = re.search(
                    r"(?:my )?obsidian vault (?:is )?(?:at |in )?([/\\][^\s]+)",
                    message,
                    re.IGNORECASE,
                )
                if vault_statement:
                    vault_path = vault_statement.group(1)
                    message = f"I'll use your Obsidian vault at '{vault_path}': install_mcp_server_from_registry(server_id='obsidian', vault_path1='{vault_path}')"

                # Pattern 6: "my github token is YOUR_TOKEN"
                github_token_statement = re.search(
                    r"(?:my )?github (?:token|pat|personal access token) (?:is |= ?)([\w-]+)",
                    message,
                    re.IGNORECASE,
                )
                if github_token_statement:
                    token = github_token_statement.group(1)
                    message = f"I have your GitHub token. Let me install the GitHub server: install_mcp_server_from_registry(server_id='github', token='{token}')"

                if show_thinking_steps:
                    # Use the detailed method that shows thinking steps
                    steps, bot_response = coding_agent.chat_with_steps(message)

                    # Combine thinking steps with final response
                    if steps:
                        thinking_section = (
                            "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                        )
                        full_response = thinking_section + "## 💬 Final Response\n\n" + bot_response
                    else:
                        full_response = bot_response
                else:
                    # Use the regular chat method
                    full_response = coding_agent.chat(message)

                # Check if the response indicates missing API keys or if Brave search needs API key
                if (
                    "Missing required arguments:" in full_response
                    and "Example for" in full_response
                ):
                    # Extract server ID and missing arguments
                    import re

                    server_match = re.search(r"Example for ([\w-]+):", full_response)
                    args_match = re.search(
                        r"Missing required arguments: \[([^\]]+)\]", full_response
                    )

                    if server_match and args_match:
                        server_id = server_match.group(1)
                        missing_args = [
                            arg.strip().strip("'") for arg in args_match.group(1).split(",")
                        ]

                        # Create a helpful prompt for the user
                        api_key_prompt = "\n\n🔑 **API Key Required**\n\n"
                        api_key_prompt += f"The {server_id} server requires the following:"

                        for arg in missing_args:
                            if "token" in arg.lower() or "key" in arg.lower():
                                api_key_prompt += f"\n- **{arg}**: Please provide your API key"
                            else:
                                api_key_prompt += (
                                    f"\n- **{arg}**: Please provide the required value"
                                )

                        api_key_prompt += (
                            "\n\nPlease provide the required information in your next message."
                        )
                        api_key_prompt += "\n\nExample: `install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"

                        full_response += api_key_prompt

                # Check if Brave Search API key is needed
                elif "BRAVE_API_KEY not set" in full_response:
                    api_key_prompt = "\n\n🔑 **Brave Search API Key Required**\n\n"
                    api_key_prompt += "To use Brave Search, you need to provide an API key.\n\n"
                    api_key_prompt += "🌐 **Get your API key:**\n"
                    api_key_prompt += "1. Visit https://brave.com/search/api/\n"
                    api_key_prompt += "2. Sign up for a free account\n"
                    api_key_prompt += "3. Copy your API key\n\n"
                    api_key_prompt += "🔧 **To install with your key:**\n"
                    api_key_prompt += (
                        "Please type: `install brave search with key YOUR_API_KEY_HERE`\n\n"
                    )
                    api_key_prompt += "Or use the exact command:\n"
                    api_key_prompt += "`install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"

                    # Replace the error message with the helpful prompt
                    if "Error: BRAVE_API_KEY not set" in full_response:
                        full_response = (
                            full_response.split("Error: BRAVE_API_KEY not set")[0] + api_key_prompt
                        )
                    else:
                        full_response += api_key_prompt

                # Check if the response shows server requirements
                elif "Requirements for" in full_response and "Required Arguments:" in full_response:
                    # Add a helpful prompt for providing requirements
                    requirements_prompt = "\n\n📝 **Please provide the required information:**\n\n"

                    # Extract what's needed from the response
                    if "path" in full_response and "Directory path" in full_response:
                        requirements_prompt += (
                            "For **filesystem** server, please specify the directory path:\n"
                        )
                        requirements_prompt += "Example: `use path /home/user/workspace`\n\n"

                    if "vault_path1" in full_response:
                        requirements_prompt += (
                            "For **Obsidian** server, please specify your vault path:\n"
                        )
                        requirements_prompt += (
                            "Example: `my obsidian vault is at /path/to/vault`\n\n"
                        )

                    if "BRAVE_API_KEY" in full_response and "❌ Not yet provided" in full_response:
                        requirements_prompt += (
                            "For **Brave Search**, please provide your API key:\n"
                        )
                        requirements_prompt += "Example: `my brave api key is YOUR_KEY_HERE`\n\n"

                    if "GITHUB_TOKEN" in full_response and "❌ Not yet provided" in full_response:
                        requirements_prompt += (
                            "For **GitHub**, please provide your personal access token:\n"
                        )
                        requirements_prompt += "Example: `my github token is YOUR_TOKEN_HERE`\n\n"

                    full_response += requirements_prompt

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
                            thinking_section = (
                                "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            )
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
                            thinking_section = (
                                "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            )
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
                            thinking_section = (
                                "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            )
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
                            thinking_section = (
                                "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            )
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
                            thinking_section = (
                                "## 🧠 AI Thinking Process\n\n" + "\n\n".join(steps) + "\n\n---\n\n"
                            )
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
            """Install MCP server package and connect using registry"""
            import os
            import subprocess

            from .mcp_management_tool import get_mcp_manager

            server_info = predefined_servers.get(server_id)
            if not server_info:
                return "❌ Unknown server"

            progress = f"📦 Installing {server_info['name']}...\n"

            try:
                # Get the MCP manager
                manager = get_mcp_manager()

                # Prepare kwargs based on server requirements
                kwargs = {}

                # Handle filesystem path
                if server_id == "filesystem" and server_info.get("requires_path"):
                    # Auto-detect home directory
                    import platform

                    system = platform.system().lower()
                    if system == "windows":
                        home_path = os.environ.get("USERPROFILE", os.path.expanduser("~"))
                    else:
                        home_path = os.path.expanduser("~")
                    kwargs["path"] = home_path
                    progress += f"🏠 Using home directory: {home_path}\n"

                # Handle time server timezone
                elif server_id == "time" and server_info.get("requires_timezone"):
                    kwargs["timezone"] = "UTC"  # Default to UTC
                    progress += "🕐 Using timezone: UTC\n"

                # Check for required environment variables
                if server_info.get("requires_env"):
                    missing_env = []
                    for env_var in server_info["requires_env"]:
                        if not os.environ.get(env_var):
                            missing_env.append(env_var)

                    if missing_env:
                        progress += f"⚠️ Missing environment variables: {', '.join(missing_env)}\n"
                        if server_id == "brave-search":
                            progress += "\n📝 To use Brave Search:\n"
                            progress += "1. Get API key from https://brave.com/search/api/\n"
                            progress += (
                                "2. Set environment variable: BRAVE_API_KEY=your_key_here\n"
                            )
                        elif server_id == "github":
                            progress += "\n📝 To use GitHub:\n"
                            progress += "1. Create token at https://github.com/settings/tokens\n"
                            progress += (
                                "2. Set environment variable: GITHUB_TOKEN=your_token_here\n"
                            )
                        progress += "\n❌ Cannot install without required environment variables\n"
                        return progress

                # Use the registry's install_mcp_server_from_registry function
                progress += "🚀 Starting installation via registry...\n"
                result = manager.install_mcp_server_from_registry(server_id, **kwargs)
                progress += result + "\n"

                # Check if installation was successful
                if "✅" in result and "started automatically" in result:
                    progress += "\n🎉 Installation and startup successful!\n"

                    # Update connection status
                    if not hasattr(quick_connect_mcp, "connections"):
                        quick_connect_mcp.connections = {}

                    quick_connect_mcp.connections[server_id] = {
                        "name": server_info["name"],
                        "url": server_info["url"],
                        "protocol": server_info["protocol"],
                        "status": "running",
                        "auto_started": True,
                    }

                    return progress
                else:
                    return progress + "\n❌ Installation failed\n"

            except Exception as e:
                return progress + f"\n❌ Error during installation: {str(e)}\n"

            # Keep the old filesystem-specific implementation as fallback
            if server_id == "filesystem" and "✅" not in progress:
                progress = f"📦 Installing {server_info['name']}...\n"

                # Check if we have Node.js for filesystem server
                try:
                    node_result = subprocess.run(
                        ["node", "--version"], capture_output=True, text=True, timeout=10
                    )
                    if node_result.returncode != 0:
                        return (
                            progress
                            + "❌ Node.js not found. Please install Node.js first: https://nodejs.org/"
                        )

                    progress += f"✅ Node.js detected: {node_result.stdout.strip()}\n"

                    # Check if npm is available
                    npm_result = subprocess.run(
                        ["npm", "--version"], capture_output=True, text=True, timeout=10, shell=True
                    )
                    if npm_result.returncode != 0:
                        return (
                            progress
                            + "❌ npm not found. Node.js is installed but npm is missing.\n\nTry:\n1. Restart your terminal/PowerShell as Administrator\n2. Or reinstall Node.js from https://nodejs.org/\n3. Or check PATH: where npm"
                        )

                    progress += f"✅ npm detected: {npm_result.stdout.strip()}\n"

                    # Install the filesystem server
                    progress += "📦 Installing @modelcontextprotocol/server-filesystem...\n"

                    install_result = subprocess.run(
                        ["npm", "install", "-g", "@modelcontextprotocol/server-filesystem"],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        shell=True,  # Use shell on Windows to help find npm
                    )

                    if install_result.returncode != 0:
                        stderr_output = install_result.stderr or "No error details"
                        stdout_output = install_result.stdout or "No output"
                        return (
                            progress
                            + f"❌ Installation failed:\n\nSTDERR:\n{stderr_output}\n\nSTDOUT:\n{stdout_output}\n\nTry running this command manually in your terminal:\nnpm install -g @modelcontextprotocol/server-filesystem"
                        )

                    progress += "✅ Package installed successfully!\n\n"
                    progress += "🔌 Testing filesystem access...\n"

                    # Test basic filesystem access
                    import os

                    test_dir = os.getcwd()
                    files = os.listdir(test_dir)

                    progress += f"✅ Filesystem access working - found {len(files)} items in current directory\n\n"

                    # Store connection info
                    if not hasattr(quick_connect_mcp, "connections"):
                        quick_connect_mcp.connections = {}

                    quick_connect_mcp.connections[server_id] = {
                        "name": server_info["name"],
                        "url": server_info["url"],
                        "protocol": server_info["protocol"],
                        "status": "connected",
                        "tools": ["read_file", "write_file", "list_directory", "create_directory"],
                    }

                    # Connect to coding agent if available
                    if coding_agent:
                        progress += "🤖 Connecting to coding agent...\n"
                        try:
                            coding_agent.add_mcp_connection(
                                server_id,
                                {
                                    "name": server_info["name"],
                                    "tools": [
                                        "read_file",
                                        "write_file",
                                        "list_directory",
                                        "create_directory",
                                    ],
                                },
                            )
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
                        if not hasattr(quick_connect_mcp, "connections"):
                            quick_connect_mcp.connections = {}

                        quick_connect_mcp.connections[server_id] = {
                            "name": server_info["name"],
                            "url": server_info["url"],
                            "protocol": server_info["protocol"],
                            "status": "connected",
                            "tools": [
                                "read_file",
                                "write_file",
                                "list_directory",
                                "create_directory",
                            ],
                        }

                        # Connect to coding agent if available
                        if coding_agent:
                            progress += "🤖 Connecting to coding agent...\n"
                            try:
                                coding_agent.add_mcp_connection(
                                    server_id,
                                    {
                                        "name": server_info["name"],
                                        "tools": [
                                            "read_file",
                                            "write_file",
                                            "list_directory",
                                            "create_directory",
                                        ],
                                    },
                                )
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
                    "time": "pip install mcp-server-time",
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

                # Check if server is already running from auto-install
                if (
                    hasattr(quick_connect_mcp, "connections")
                    and server_id in quick_connect_mcp.connections
                ):
                    conn_info = quick_connect_mcp.connections[server_id]
                    if conn_info.get("auto_started") and conn_info.get("status") == "running":
                        return f"✅ {server_info['name']} is already running!\n\nThis server was auto-started and is ready for use by external MCP clients."

                # Try to connect using the actual MCP client
                try:
                    # Use the existing connection manager to make a real MCP connection
                    result = GradioMCPClient.test_connection(
                        server_info["url"], server_info["protocol"]
                    )

                    if result.get("success"):
                        # Store the connection info
                        if not hasattr(quick_connect_mcp, "connections"):
                            quick_connect_mcp.connections = {}

                        # Save the connection for reuse
                        connection_manager.save_connection(
                            server_id, server_info["url"], server_info["protocol"]
                        )

                        # Get available tools from the connection
                        tools = result.get("tools", [])
                        tool_names = (
                            [tool.get("name", "unknown") for tool in tools] if tools else []
                        )

                        quick_connect_mcp.connections[server_id] = {
                            "name": server_info["name"],
                            "url": server_info["url"],
                            "protocol": server_info["protocol"],
                            "status": "connected",
                            "tools": tool_names,
                            "client_info": result,
                        }

                        # Connect to coding agent if available
                        if coding_agent:
                            try:
                                coding_agent.add_mcp_connection(
                                    server_id,
                                    {
                                        "name": server_info["name"],
                                        "client": connection_manager.get_connection(server_id),
                                        "tools": tool_names,
                                    },
                                )
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
                    install_cmd = (
                        "npm install -g @modelcontextprotocol/server-filesystem"
                        if server_id == "filesystem"
                        else f"pip install mcp-server-{server_id}"
                    )
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
                    connection_manager.remove_connection(conn.get("name", ""))
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
                    status = "🟢 Connected" if conn.get("connected") else "🔴 Disconnected"
                    status_lines.append(f"{conn.get('name', 'Unknown')}: {status}")

                return "\n".join(status_lines) if status_lines else "No connections found"
            except Exception as e:
                return f"❌ Error refreshing status: {str(e)}"

        def get_mcp_connections_data():
            """Get MCP connections data for the table"""
            data = []

            # Check coding agent's MCP connections first (these are the actual loaded servers)
            if coding_agent and hasattr(coding_agent, '_mcp_servers') and coding_agent._mcp_servers:
                for server_id, server in coding_agent._mcp_servers.items():
                    # Get server info from predefined or create basic info
                    server_info = predefined_servers.get(server_id, {
                        'name': server_id,
                        'icon': '🔌',
                        'url': f"{server_id} server"
                    })
                    
                    # Get tool count
                    tool_count = 0
                    if hasattr(coding_agent, 'mcp_tools') and server_id in coding_agent.mcp_tools:
                        tool_count = len(coding_agent.mcp_tools[server_id])
                    
                    data.append(
                        [
                            f"{server_info.get('icon', '🔌')} {server_info.get('name', server_id)}",
                            "MCP Server",
                            f"🟢 Connected",
                            tool_count,
                            server_info.get('url', f"{server_id} server"),
                        ]
                    )

            # Also check if we have any connections stored in quick_connect_mcp
            elif hasattr(quick_connect_mcp, "connections"):
                for server_id, conn_info in quick_connect_mcp.connections.items():
                    server_info = predefined_servers.get(server_id, {})
                    status_icon = "🟢" if conn_info["status"] == "connected" else "🟡"
                    status_text = "Connected" if conn_info["status"] == "connected" else "Simulated"

                    data.append(
                        [
                            f"{server_info.get('icon', '🔌')} {conn_info['name']}",
                            "MCP Server",
                            f"{status_icon} {status_text}",
                            len(conn_info.get("tools", [])),
                            conn_info["url"],
                        ]
                    )

            return data

        def get_mcp_connection_choices():
            """Get list of MCP connection names for dropdown"""
            choices = []

            # Check coding agent's MCP connections first
            if coding_agent and hasattr(coding_agent, '_mcp_servers') and coding_agent._mcp_servers:
                for server_id in coding_agent._mcp_servers.keys():
                    choices.append(server_id)
            # Also check if we have any connections stored in quick_connect_mcp
            elif hasattr(quick_connect_mcp, "connections"):
                for server_id, conn_info in quick_connect_mcp.connections.items():
                    choices.append(server_id)

            return choices

        def load_mcp_connection_details(connection_name):
            """Load details for a selected MCP connection"""
            if not connection_name:
                return {}, [], []

            # Handle case where connection_name might be a list
            if isinstance(connection_name, list):
                connection_name = connection_name[0] if connection_name else None
                if not connection_name:
                    return {}, [], []

            try:
                # First check coding agent's connections
                if (
                    coding_agent and 
                    hasattr(coding_agent, '_mcp_servers') and 
                    connection_name in coding_agent._mcp_servers
                ):
                    # Get server info
                    server_info = predefined_servers.get(connection_name, {
                        'name': connection_name,
                        'url': f"{connection_name} server",
                        'protocol': 'stdio'
                    })
                    
                    details = {
                        "name": connection_name,
                        "url": server_info.get('url', f"{connection_name} server"),
                        "protocol": server_info.get('protocol', 'stdio'),
                        "status": "connected",
                        "connected": True,
                    }
                    
                    # Get tools data from coding agent
                    tools_data = []
                    tool_names = []
                    
                    if hasattr(coding_agent, 'mcp_tools') and connection_name in coding_agent.mcp_tools:
                        for tool in coding_agent.mcp_tools[connection_name]:
                            tool_name = tool.metadata.name if hasattr(tool, 'metadata') else str(tool)
                            # Remove server prefix from tool name for display
                            display_name = tool_name.replace(f"{connection_name}_", "")
                            # Get clean description
                            if hasattr(tool, 'metadata') and hasattr(tool.metadata, 'description'):
                                description = tool.metadata.description
                                # Remove function signature if present
                                if "(**kwargs)" in description:
                                    parts = description.split("(**kwargs)")
                                    if len(parts) > 1:
                                        description = parts[1].strip()
                                    else:
                                        description = parts[0].strip()
                            else:
                                description = f"Tool from {connection_name}"
                            
                            tools_data.append(
                                [
                                    display_name,
                                    description,
                                    "{}",  # Parameters would need more work to extract
                                ]
                            )
                            tool_names.append(display_name)
                    
                    return details, tools_data, tool_names
                    
                # Otherwise check quick_connect_mcp connections
                elif (
                    hasattr(quick_connect_mcp, "connections")
                    and connection_name in quick_connect_mcp.connections
                ):
                    conn_info = quick_connect_mcp.connections[connection_name]

                    details = {
                        "name": connection_name,
                        "url": conn_info["url"],
                        "protocol": conn_info["protocol"],
                        "status": conn_info["status"],
                        "connected": conn_info["status"] == "connected",
                    }

                    # Get tools data
                    tools_data = []
                    tool_names = []

                    for tool in conn_info.get("tools", []):
                        tools_data.append(
                            [
                                tool,
                                f"Tool for {conn_info['name']}",
                                "{}",  # Empty parameters for demo
                            ]
                        )
                        tool_names.append(tool)

                    return details, tools_data, tool_names

            except Exception as e:
                print(f"Error loading MCP connection details: {e}")
                return {"error": f"Error loading connection: {str(e)}"}, [], []

            return {"error": "Connection not found"}, [], []

        def test_mcp_connection(connection_name):
            """Test an MCP connection"""
            if not HAS_CLIENT_MANAGER or not connection_name:
                return {"error": "Invalid connection"}

            connections = connection_manager.list_connections()
            selected_conn = None

            for conn in connections:
                if conn.get("name") == connection_name:
                    selected_conn = conn
                    break

            if not selected_conn:
                return {"error": "Connection not found"}

            try:
                result = GradioMCPClient.test_connection(
                    selected_conn.get("url"), selected_conn.get("protocol")
                )
                return {"status": "connected" if result["success"] else "error", "result": result}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        def disconnect_mcp_connection(connection_name):
            """Disconnect a specific MCP connection"""
            if not connection_name:
                return get_mcp_connections_data()

            try:
                # Remove from our stored connections
                if (
                    hasattr(quick_connect_mcp, "connections")
                    and connection_name in quick_connect_mcp.connections
                ):
                    del quick_connect_mcp.connections[connection_name]
            except Exception:
                pass

            return get_mcp_connections_data()

        def call_mcp_tool(connection_name, tool_name, tool_args):
            """Call a tool on an MCP connection"""
            if not connection_name or not tool_name:
                return {"error": "Missing connection name or tool name"}

            # Check if we have this connection
            if (
                not hasattr(quick_connect_mcp, "connections")
                or connection_name not in quick_connect_mcp.connections
            ):
                return {"error": "Connection not found"}

            conn_info = quick_connect_mcp.connections[connection_name]

            try:
                # For filesystem connection, implement actual operations
                if connection_name == "filesystem":
                    import os

                    if tool_name == "list_directory":
                        path = tool_args.get("path", ".")
                        try:
                            files = os.listdir(path)
                            return {
                                "success": True,
                                "result": {
                                    "files": files,
                                    "path": os.path.abspath(path),
                                    "count": len(files),
                                },
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}

                    elif tool_name == "read_file":
                        path = tool_args.get("path", "")
                        if not path:
                            return {"success": False, "error": "Path is required"}

                        try:
                            with open(path, encoding="utf-8") as f:
                                content = f.read()
                            return {
                                "success": True,
                                "result": {
                                    "content": content,
                                    "path": os.path.abspath(path),
                                    "size": len(content),
                                },
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}

                    elif tool_name == "write_file":
                        path = tool_args.get("path", "")
                        content = tool_args.get("content", "")
                        if not path:
                            return {"success": False, "error": "Path is required"}

                        try:
                            with open(path, "w", encoding="utf-8") as f:
                                f.write(content)
                            return {
                                "success": True,
                                "result": {
                                    "message": "File written successfully",
                                    "path": os.path.abspath(path),
                                    "bytes_written": len(content.encode("utf-8")),
                                },
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}

                    elif tool_name == "create_directory":
                        path = tool_args.get("path", "")
                        if not path:
                            return {"success": False, "error": "Path is required"}

                        try:
                            os.makedirs(path, exist_ok=True)
                            return {
                                "success": True,
                                "result": {
                                    "message": "Directory created successfully",
                                    "path": os.path.abspath(path),
                                },
                            }
                        except Exception as e:
                            return {"success": False, "error": str(e)}

                    else:
                        return {"success": False, "error": f"Unknown tool: {tool_name}"}

                # For other connections, show installation instructions
                else:
                    return {
                        "success": False,
                        "error": f"MCP server '{connection_name}' not fully implemented.\n\nTo install real MCP servers, run:\npip install mcp-server-{connection_name}\n\nThen restart the dashboard.",
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

        # Helper function for MCP connection dropdown
        def load_mcp_connection_dropdown():
            """Load MCP connection choices for dropdown"""
            choices = get_mcp_connection_choices()
            return gr.update(choices=choices, value=choices[0] if choices else None)

        # Connect event handlers

        # AI Assistant event connections
        if coding_agent:
            configure_btn.click(
                configure_model,
                inputs=[hf_token_input, model_dropdown],
                outputs=[config_status, model_info, model_info_accordion],
            )

            # Chat functionality
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
                    
                    # Your existing message processing logic here...
                    # Check if user is providing an API key in a natural way
                    import re
                    
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
                    
                    # Pattern 3: "my brave api key is YOUR_KEY"
                    brave_key_statement = re.search(
                        r"(?:my )?brave (?:api )?key (?:is |= ?)([\w-]+)", message, re.IGNORECASE
                    )
                    if brave_key_statement:
                        api_key = brave_key_statement.group(1)
                        message = f"I have your Brave API key. Let me install the brave search server: install_mcp_server_from_registry(server_id='brave-search', token='{api_key}')"
                    
                    # Pattern 4: "use path /home/user/workspace" (for filesystem server)
                    path_statement = re.search(
                        r"(?:use |provide )?path (?:is |= ?)?([/\\][^\s]+)", message, re.IGNORECASE
                    )
                    if path_statement:
                        path = path_statement.group(1)
                        message = f"I'll use path '{path}' for the filesystem server: install_mcp_server_from_registry(server_id='filesystem', path='{path}')"
                    
                    # Pattern 5: "my obsidian vault is at /path/to/vault"
                    vault_statement = re.search(
                        r"(?:my )?obsidian vault (?:is )?(?:at |in )?([/\\][^\s]+)",
                        message,
                        re.IGNORECASE,
                    )
                    if vault_statement:
                        vault_path = vault_statement.group(1)
                        message = f"I'll use your Obsidian vault at '{vault_path}': install_mcp_server_from_registry(server_id='obsidian', vault_path1='{vault_path}')"
                    
                    # Pattern 6: "my github token is YOUR_TOKEN"
                    github_token_statement = re.search(
                        r"(?:my )?github (?:token|pat|personal access token) (?:is |= ?)([\w-]+)",
                        message,
                        re.IGNORECASE,
                    )
                    if github_token_statement:
                        token = github_token_statement.group(1)
                        message = f"I have your GitHub token. Let me install the GitHub server: install_mcp_server_from_registry(server_id='github', token='{token}')"
                    
                    # Process with agent
                    if show_thinking:
                        steps, bot_response = coding_agent.chat_with_steps(message)
                        
                        # Show thinking steps progressively
                        thinking_content = "## 🧠 AI Thinking Process\n\n"
                        for step in steps:
                            thinking_content += f"{step}\n\n"
                            history[-1] = {"role": "assistant", "content": thinking_content}
                            yield history
                        
                        # Add final response
                        full_response = thinking_content + "---\n\n## 💬 Final Response\n\n" + bot_response
                        history[-1] = {"role": "assistant", "content": full_response}
                    else:
                        # Regular chat without steps
                        full_response = coding_agent.chat(message)
                        history.append({"role": "assistant", "content": full_response})
                    
                    # Check and enhance response with helpful prompts
                    if "Missing required arguments:" in full_response and "Example for" in full_response:
                        # Extract server ID and missing arguments
                        server_match = re.search(r"Example for ([\w-]+):", full_response)
                        args_match = re.search(r"Missing required arguments: \[([^\]]+)\]", full_response)
                        
                        if server_match and args_match:
                            server_id = server_match.group(1)
                            missing_args = [arg.strip().strip("'") for arg in args_match.group(1).split(",")]
                            
                            # Create a helpful prompt for the user
                            api_key_prompt = "\n\n🔑 **API Key Required**\n\n"
                            api_key_prompt += f"The {server_id} server requires the following:"
                            
                            for arg in missing_args:
                                if "token" in arg.lower() or "key" in arg.lower():
                                    api_key_prompt += f"\n- **{arg}**: Please provide your API key"
                                else:
                                    api_key_prompt += f"\n- **{arg}**: Please provide the required value"
                            
                            api_key_prompt += "\n\nPlease provide the required information in your next message."
                            api_key_prompt += "\n\nExample: `install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"
                            
                            full_response += api_key_prompt
                            history[-1]["content"] = full_response
                    
                    # Check if Brave Search API key is needed
                    elif "BRAVE_API_KEY not set" in full_response:
                        api_key_prompt = "\n\n🔑 **Brave Search API Key Required**\n\n"
                        api_key_prompt += "To use Brave Search, you need to provide an API key.\n\n"
                        api_key_prompt += "🌐 **Get your API key:**\n"
                        api_key_prompt += "1. Visit https://brave.com/search/api/\n"
                        api_key_prompt += "2. Sign up for a free account\n"
                        api_key_prompt += "3. Copy your API key\n\n"
                        api_key_prompt += "🔧 **To install with your key:**\n"
                        api_key_prompt += "Please type: `install brave search with key YOUR_API_KEY_HERE`\n\n"
                        api_key_prompt += "Or use the exact command:\n"
                        api_key_prompt += "`install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"
                        
                        # Replace the error message with the helpful prompt
                        if "Error: BRAVE_API_KEY not set" in full_response:
                            full_response = full_response.split("Error: BRAVE_API_KEY not set")[0] + api_key_prompt
                        else:
                            full_response += api_key_prompt
                        
                        history[-1]["content"] = full_response
                    
                    yield history
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    history.append({"role": "assistant", "content": error_msg})
                    yield history
            
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

        # Registry Event Handlers

        # Search functionality
        registry_search_btn.click(
            search_registry_servers,
            inputs=[registry_search_query, registry_category_filter, registry_server_type],
            outputs=[registry_results_df],
        )

        registry_show_all_btn.click(
            show_all_servers, inputs=[registry_server_type], outputs=[registry_results_df]
        )

        registry_show_popular_btn.click(show_popular_servers, outputs=[registry_results_df])

        # Server details functionality
        registry_server_selector.change(
            load_server_details,
            inputs=[registry_server_selector],
            outputs=[
                registry_server_name,
                registry_server_description,
                registry_server_category,
                registry_server_package,
                registry_server_install_method,
                registry_server_homepage,
                registry_server_setup_help,
                registry_server_example_usage,
                registry_required_args,
                registry_env_vars,
                registry_user_args,
            ],
        )

        # Installation functionality
        registry_install_btn.click(
            install_registry_server,
            inputs=[registry_server_selector, registry_user_args],
            outputs=[registry_install_status],
        )

        # Categories functionality
        refresh_categories_btn.click(
            refresh_categories_data, outputs=[official_servers_list, community_servers_list]
        )

        # Popular servers quick install
        popular_filesystem_btn.click(
            lambda: quick_install_popular("filesystem"), outputs=[registry_install_status]
        )

        popular_memory_btn.click(
            lambda: quick_install_popular("memory"), outputs=[registry_install_status]
        )

        popular_github_btn.click(
            lambda: quick_install_popular("github"), outputs=[registry_install_status]
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
                    outputs=[server_statuses[server_id]],
                ).then(fn=get_mcp_connections_data, outputs=[mcp_connections_table]).then(
                    fn=load_mcp_connection_dropdown, outputs=[selected_mcp_connection]
                )

            # Auto-install buttons
            if server_id in server_install_buttons:

                def create_install_handler(sid):
                    def install_handler():
                        return install_and_connect_mcp(sid)

                    return install_handler

                # Update status display after installation
                def update_server_status_handler(sid):
                    def handler(install_output):
                        if "✅" in install_output and "started automatically" in install_output:
                            return "✅ Running (Auto-started)"
                        elif "❌" in install_output:
                            return "❌ Installation Failed"
                        else:
                            return "⏳ Installing..."

                    return handler

                server_install_buttons[server_id].click(
                    fn=lambda: gr.update(visible=True), outputs=[mcp_install_progress]
                ).then(fn=create_install_handler(server_id), outputs=[mcp_install_progress]).then(
                    fn=update_server_status_handler(server_id),
                    inputs=[mcp_install_progress],
                    outputs=[server_statuses[server_id]],
                ).then(
                    fn=get_mcp_connections_data, outputs=[mcp_connections_table]
                ).then(
                    fn=load_mcp_connection_dropdown, outputs=[selected_mcp_connection]
                )

        # Bulk MCP actions
        connect_all_mcp_btn.click(connect_all_mcp_servers, outputs=[mcp_bulk_status])

        disconnect_all_mcp_btn.click(disconnect_all_mcp_servers, outputs=[mcp_bulk_status])

        refresh_mcp_status_btn.click(refresh_mcp_status, outputs=[mcp_bulk_status])

        # Active MCP connections management
        def update_mcp_connection_ui(connection_name):
            """Update UI when MCP connection is selected"""
            details, tools_data, tool_names = load_mcp_connection_details(connection_name)
            # Return the tool dropdown update with choices
            return details, tools_data, gr.update(choices=tool_names, value=None)
        
        selected_mcp_connection.change(
            update_mcp_connection_ui,
            inputs=[selected_mcp_connection],
            outputs=[mcp_connection_details, mcp_available_tools, mcp_tool_name],
        )

        test_mcp_connection_btn.click(
            test_mcp_connection, inputs=[selected_mcp_connection], outputs=[mcp_connection_details]
        )

        def handle_mcp_disconnect(connection_name):
            """Handle MCP disconnection and update UI"""
            table_data = disconnect_mcp_connection(connection_name)
            choices = get_mcp_connection_choices()
            return table_data, gr.update(choices=choices, value=choices[0] if choices else None)
        
        disconnect_mcp_btn.click(
            handle_mcp_disconnect,
            inputs=[selected_mcp_connection],
            outputs=[mcp_connections_table, selected_mcp_connection],
        )

        # MCP tool calling
        call_mcp_tool_btn.click(
            call_mcp_tool,
            inputs=[selected_mcp_connection, mcp_tool_name, mcp_tool_args],
            outputs=[mcp_tool_result],
        )

        # Custom MCP connection
        custom_mcp_connect_btn.click(
            connect_custom_mcp,
            inputs=[custom_mcp_name, custom_mcp_url, custom_mcp_protocol, custom_mcp_description],
            outputs=[custom_mcp_status],
        )

        # Load initial data
        dashboard.load(refresh_servers, outputs=servers_list)
        dashboard.load(refresh_connections, outputs=connections_list)
        dashboard.load(update_server_dropdown, outputs=server_dropdown)
        dashboard.load(update_connection_dropdown, outputs=connection_dropdown)

        # Load initial MCP connections data
        dashboard.load(get_mcp_connections_data, outputs=mcp_connections_table)
        dashboard.load(load_mcp_connection_dropdown, outputs=selected_mcp_connection)

        # Load initial registry data
        dashboard.load(show_popular_servers, outputs=registry_results_df)
        dashboard.load(get_registry_server_choices, outputs=registry_server_selector)
        dashboard.load(
            refresh_categories_data, outputs=[official_servers_list, community_servers_list]
        )

        # Load saved token on startup
        if coding_agent and config_manager.has_secure_storage():
            dashboard.load(load_saved_token_on_startup, outputs=[hf_token_input, token_status])
        
        # Initialize Liam's greeting
        if coding_agent:
            def initialize_liam_greeting():
                """Generate Liam's initial greeting with available MCP servers"""
                # Count connected servers
                connected_count = 0
                if hasattr(coding_agent, '_mcp_servers') and coding_agent._mcp_servers:
                    connected_count = len(coding_agent._mcp_servers)
                
                greeting = f"👋 Hi! I'm Liam, your MCP assistant. I can help you install and manage MCP servers, write code, and build Gradio apps.\n\n"
                
                if connected_count > 0:
                    greeting += f"✅ **{connected_count} servers connected** "
                    # Show first 3 servers
                    server_names = list(coding_agent._mcp_servers.keys())[:3]
                    greeting += f"({', '.join(server_names)}"
                    if connected_count > 3:
                        greeting += f", +{connected_count - 3} more"
                    greeting += ")\n\n"
                
                greeting += "💡 **Quick commands:** `install memory` • `find database servers` • `what's MCP?`\n\n"
                greeting += "What would you like to do?"
                
                return [{"role": "assistant", "content": greeting}]
            
            dashboard.load(initialize_liam_greeting, outputs=[chatbot])

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
        favicon_path="🛝",
    )
