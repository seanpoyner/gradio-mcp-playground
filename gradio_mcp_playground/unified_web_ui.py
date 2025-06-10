"""
Unified Gradio MCP Playground Dashboard
Combines the main dashboard with agent builder functionality
"""

import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Tuple

import gradio as gr

# We'll define message handling functions locally instead of importing
# because the web_ui versions expect a different scope

# Server management functions are defined locally in this file
# No need to import from web_ui as they were causing import errors
HAS_SERVER_FUNCTIONS = True

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
    from ui.chat_interface import ChatInterface
    from ui.control_panel import ControlPanelUI
    from ui.pipeline_view import PipelineView

    HAS_AGENT_COMPONENTS = True
    HAS_CONTROL_PANEL = True
    HAS_PIPELINE_VIEW = True

    # Apply UI patches to fix event handler issues
    try:
        from agent_ui_fixes import apply_all_patches

        apply_all_patches()
    except ImportError:
        # Try loading from parent directory
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from agent_ui_fixes import apply_all_patches

            apply_all_patches()
        except Exception as patch_error:
            print(f"Could not apply UI patches: {patch_error}")

except ImportError as e:
    HAS_AGENT_COMPONENTS = False
    HAS_CONTROL_PANEL = False
    HAS_PIPELINE_VIEW = False
    print(f"Agent components not available - some features will be disabled: {e}")

    # Try to import individual components
    try:
        from ui.pipeline_view import PipelineView

        HAS_PIPELINE_VIEW = True
    except ImportError:
        pass

# Try to import just control panel if full agent components fail
if not HAS_CONTROL_PANEL:
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))
        from ui.control_panel import ControlPanelUI

        HAS_CONTROL_PANEL = True
    except ImportError:
        HAS_CONTROL_PANEL = False


def _get_connected_servers_info(coding_agent):
    """Get information about connected MCP servers"""
    if not coding_agent or not hasattr(coding_agent, "_mcp_servers"):
        return "**No MCP servers connected.** Connect servers in the MCP Connections tab."

    servers = coding_agent._mcp_servers
    if not servers:
        return "**No MCP servers connected.** Connect servers in the MCP Connections tab."

    info = f"**🔌 {len(servers)} MCP Servers Connected:**\n\n"
    for server_name, _server in servers.items():
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
            border: 1px solid var(--border-color-primary);
            border-radius: 8px;
            padding: 16px;
            margin: 8px;
            background: var(--background-fill-secondary);
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
        
        /* Agent viewer iframe styles */
        #agent-viewer-iframe iframe {
            width: 100%;
            height: 600px;
            border: 1px solid var(--border-color-primary);
            border-radius: 8px;
            background: var(--background-fill-primary);
        }
        
        #agent-viewer-iframe {
            min-height: 600px;
            background: var(--background-fill-secondary);
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Pipeline builder styles */
        .pipeline-node {
            transition: all 0.2s ease;
            user-select: none;
        }
        
        .pipeline-node:hover {
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        #pipeline-canvas {
            background: var(--background-fill-secondary);
            background-image: 
                linear-gradient(var(--border-color-primary) 1px, transparent 1px),
                linear-gradient(90deg, var(--border-color-primary) 1px, transparent 1px);
            background-size: 20px 20px;
        }
        
        #template-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 16px;
            padding: 16px;
        }
        
        /* Template gallery styles - Works in both light and dark modes */
        .templates-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 20px 0;
        }
        
        .template-card {
            background: #374151;
            border: 2px solid #4b5563;
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .template-card:hover {
            border-color: #60a5fa;
            box-shadow: 0 6px 20px rgba(96, 165, 250, 0.3);
            transform: translateY(-2px);
        }
        
        .template-icon {
            font-size: 48px;
            margin-bottom: 16px;
            text-align: center;
        }
        
        .template-name {
            font-size: 20px;
            font-weight: 600;
            margin: 0 0 8px 0;
            color: #f3f4f6;
        }
        
        .template-category {
            display: inline-block;
            background: #1f2937;
            color: #d1d5db;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 12px;
        }
        
        .template-description {
            color: #d1d5db;
            font-size: 14px;
            line-height: 1.5;
            margin: 0 0 16px 0;
        }
        
        .template-difficulty {
            position: absolute;
            top: 16px;
            right: 16px;
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .template-grid-empty {
            text-align: center;
            padding: 60px 20px;
            color: #9ca3af;
            font-size: 16px;
        }
        
        .template-details {
            background: #374151;
            border-radius: 8px;
            padding: 20px;
            min-height: 400px;
            color: #f3f4f6;
        }
        
        .template-details h3 {
            margin-top: 0;
            color: #f3f4f6;
        }
        
        .template-details h4 {
            color: #f3f4f6;
            margin-top: 24px;
            margin-bottom: 12px;
        }
        
        .template-details ul {
            margin: 0;
            padding-left: 20px;
            color: #d1d5db;
        }
        
        .template-details code {
            background: #1f2937;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
            color: #f3f4f6;
        }
        """,
    ) as dashboard:
        gr.Markdown(
            """
            # 🛝 Gradio MCP Playground
            """
        )

        with gr.Tabs():
            # Tab 1: AI Assistant (Enhanced with Agent Builder)
            with gr.Tab("🛝 AI Assistant"):
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
                            value=[],
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
                            # Get available templates and ensure default value is valid
                            available_templates = (
                                registry.list_templates() if HAS_REGISTRY else ["basic"]
                            )
                            # Ensure we have a fallback if no templates are available
                            if not available_templates:
                                available_templates = ["basic"]
                            default_template = (
                                available_templates[0] if available_templates else None
                            )

                            template_dropdown = gr.Dropdown(
                                choices=available_templates,
                                label="Server Template",
                                value=default_template,
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
                        if HAS_PIPELINE_VIEW and gmp_agent:
                            # Create pipeline view instance
                            try:
                                pipeline_view = PipelineView(gmp_agent)
                                pipeline_view.create_interface()
                            except Exception as e:
                                gr.Markdown("### Visual Pipeline Builder")
                                gr.Markdown(f"Error initializing pipeline builder: {str(e)}")
                                gr.Markdown(
                                    """
                                    To access the pipeline builder directly, run:
                                    ```bash
                                    cd agent && python app.py
                                    ```
                                    """
                                )
                        else:
                            gr.Markdown("### Visual Pipeline Builder")
                            gr.Markdown(
                                """
                                The pipeline builder allows you to create complex workflows visually.
                                This feature requires the agent components to be installed.
                                
                                To enable this feature:
                                1. Ensure the agent directory is properly set up
                                2. Install required dependencies: `pip install -r agent/requirements.txt`
                                3. Restart the application
                                """
                            )

                    # Templates Gallery
                    with gr.Tab("📚 Templates"):
                        gr.Markdown(
                            """
                            ## 🎨 Server Template Gallery
                            
                            Choose from our collection of pre-built MCP server templates to quickly get started.
                            Each template includes complete code, configuration, and documentation.
                            """
                        )

                        # Define helper functions first
                        def create_templates_grid(category="All", search_query=""):
                            """Create a professional grid display of templates"""
                            if not HAS_REGISTRY:
                                return (
                                    '<div class="template-grid-empty">Registry not available</div>'
                                )

                            templates = registry.list_templates()
                            if not templates:
                                return (
                                    '<div class="template-grid-empty">No templates available</div>'
                                )

                            # Template metadata with better organization
                            template_metadata = {
                                "basic": {
                                    "icon": "🎯",
                                    "category": "Starter",
                                    "description": "Simple MCP server with basic structure",
                                    "difficulty": "Beginner",
                                    "features": [
                                        "Single tool",
                                        "Minimal setup",
                                        "Great for learning",
                                    ],
                                    "use_cases": [
                                        "Learning MCP",
                                        "Simple utilities",
                                        "Quick prototypes",
                                    ],
                                },
                                "calculator": {
                                    "icon": "🔢",
                                    "category": "Tools",
                                    "description": "Mathematical operations server",
                                    "difficulty": "Beginner",
                                    "features": [
                                        "Basic math",
                                        "Scientific functions",
                                        "Unit conversion",
                                    ],
                                    "use_cases": [
                                        "Calculations",
                                        "Data processing",
                                        "Educational tools",
                                    ],
                                },
                                "basic-tool": {
                                    "icon": "🔧",
                                    "category": "Starter",
                                    "description": "Template for single-tool servers",
                                    "difficulty": "Beginner",
                                    "features": [
                                        "Tool scaffold",
                                        "Error handling",
                                        "Type validation",
                                    ],
                                    "use_cases": [
                                        "Custom tools",
                                        "API wrappers",
                                        "Simple automation",
                                    ],
                                },
                                "multi-tool": {
                                    "icon": "🛠️",
                                    "category": "Tools",
                                    "description": "Server with multiple tools",
                                    "difficulty": "Intermediate",
                                    "features": [
                                        "Multiple tools",
                                        "Shared state",
                                        "Complex operations",
                                    ],
                                    "use_cases": ["Tool suites", "Workflows", "Complex utilities"],
                                },
                                "image-generator": {
                                    "icon": "🎨",
                                    "category": "AI/ML",
                                    "description": "AI-powered image generation",
                                    "difficulty": "Advanced",
                                    "features": ["Stable Diffusion", "DALL-E", "Image editing"],
                                    "use_cases": [
                                        "Content creation",
                                        "Design tools",
                                        "Creative apps",
                                    ],
                                },
                            }

                            # Build grid HTML
                            grid_html = '<div class="templates-grid">'

                            for template_name in templates:
                                template_info = registry.get_template(template_name)
                                if not template_info:
                                    continue

                                # Get metadata
                                meta = template_metadata.get(
                                    template_name,
                                    {
                                        "icon": "📦",
                                        "category": "Other",
                                        "description": template_info.get(
                                            "description", "Custom MCP server template"
                                        ),
                                        "difficulty": "Intermediate",
                                        "features": [],
                                        "use_cases": [],
                                    },
                                )

                                # Apply filters
                                if category != "All" and meta["category"] != category:
                                    continue
                                if (
                                    search_query
                                    and search_query.lower() not in template_name.lower()
                                    and search_query.lower() not in meta["description"].lower()
                                ):
                                    continue

                                # Difficulty badge color
                                difficulty_colors = {
                                    "Beginner": "#28a745",
                                    "Intermediate": "#ffc107",
                                    "Advanced": "#dc3545",
                                }

                                grid_html += f"""
                                <div class="template-card" data-template="{template_name}">
                                    <div class="template-icon">{meta["icon"]}</div>
                                    <h3 class="template-name">{template_name}</h3>
                                    <div class="template-category">{meta["category"]}</div>
                                    <p class="template-description">{meta["description"]}</p>
                                    <div class="template-difficulty" style="background-color: {difficulty_colors.get(meta['difficulty'], '#6c757d')}">
                                        {meta["difficulty"]}
                                    </div>
                                </div>
                                """

                            grid_html += "</div>"
                            return grid_html

                        def show_template_details(template_name=None):
                            """Show detailed information about a template"""
                            if not template_name or not HAS_REGISTRY:
                                return (
                                    "### Select a template to view details",
                                    gr.update(visible=False),
                                    gr.update(visible=False),
                                )

                            template_info = registry.get_template(template_name)
                            if not template_info:
                                return (
                                    "### Template not found",
                                    gr.update(visible=False),
                                    gr.update(visible=False),
                                )

                            # Enhanced template metadata
                            template_metadata = {
                                "basic": {
                                    "icon": "🎯",
                                    "category": "Starter",
                                    "description": "Simple MCP server with basic structure. Perfect for learning the fundamentals of MCP.",
                                    "difficulty": "Beginner",
                                    "features": [
                                        "Single tool implementation",
                                        "Basic error handling",
                                        "Minimal dependencies",
                                        "Clear code structure",
                                    ],
                                    "use_cases": [
                                        "Learning MCP basics",
                                        "Building simple utilities",
                                        "Quick prototypes",
                                        "Testing MCP concepts",
                                    ],
                                    "requirements": ["Python 3.8+", "mcp package"],
                                    "setup_time": "< 5 minutes",
                                },
                                "calculator": {
                                    "icon": "🔢",
                                    "category": "Tools",
                                    "description": "Full-featured calculator server with mathematical operations and functions.",
                                    "difficulty": "Beginner",
                                    "features": [
                                        "Basic arithmetic operations",
                                        "Scientific functions (sin, cos, log, etc.)",
                                        "Memory functions",
                                        "Expression evaluation",
                                        "Unit conversions",
                                    ],
                                    "use_cases": [
                                        "Mathematical calculations",
                                        "Data processing pipelines",
                                        "Educational applications",
                                        "Scientific computing",
                                    ],
                                    "requirements": ["Python 3.8+", "math module", "mcp package"],
                                    "setup_time": "< 5 minutes",
                                },
                                "multi-tool": {
                                    "icon": "🛠️",
                                    "category": "Tools",
                                    "description": "Template for servers with multiple related tools working together.",
                                    "difficulty": "Intermediate",
                                    "features": [
                                        "Multiple tool implementations",
                                        "Shared state management",
                                        "Tool interdependencies",
                                        "Advanced error handling",
                                        "Configuration system",
                                    ],
                                    "use_cases": [
                                        "Complex tool suites",
                                        "Workflow automation",
                                        "Integrated services",
                                        "Professional utilities",
                                    ],
                                    "requirements": ["Python 3.8+", "mcp package", "pydantic"],
                                    "setup_time": "5-10 minutes",
                                },
                                "image-generator": {
                                    "icon": "🎨",
                                    "category": "AI/ML",
                                    "description": "AI-powered image generation server using state-of-the-art models.",
                                    "difficulty": "Advanced",
                                    "features": [
                                        "Multiple AI model support",
                                        "Stable Diffusion integration",
                                        "DALL-E API support",
                                        "Image editing capabilities",
                                        "Batch processing",
                                        "Style transfer",
                                    ],
                                    "use_cases": [
                                        "Content creation",
                                        "Design automation",
                                        "Creative applications",
                                        "Marketing tools",
                                        "Game asset generation",
                                    ],
                                    "requirements": [
                                        "Python 3.8+",
                                        "GPU recommended",
                                        "transformers or diffusers",
                                        "API keys for cloud services",
                                    ],
                                    "setup_time": "15-30 minutes",
                                },
                            }

                            # Get metadata
                            meta = template_metadata.get(
                                template_name,
                                {
                                    "icon": "📦",
                                    "category": "Other",
                                    "description": template_info.get(
                                        "description", "Custom MCP server template"
                                    ),
                                    "difficulty": "Intermediate",
                                    "features": ["Custom implementation"],
                                    "use_cases": ["Specific use cases"],
                                    "requirements": ["Python 3.8+", "mcp package"],
                                    "setup_time": "Varies",
                                },
                            )

                            # Build detailed view
                            details = f"""
### {meta['icon']} {template_name}

**Category:** {meta['category']} | **Difficulty:** {meta['difficulty']} | **Setup Time:** {meta['setup_time']}

#### 📝 Description
{meta['description']}

#### ✨ Key Features
"""
                            for feature in meta["features"]:
                                details += f"- {feature}\n"

                            details += "\n#### 🎯 Use Cases\n"
                            for use_case in meta["use_cases"]:
                                details += f"- {use_case}\n"

                            details += "\n#### 📋 Requirements\n"
                            for req in meta["requirements"]:
                                details += f"- {req}\n"

                            # Add file structure if available
                            if "files" in template_info:
                                details += "\n#### 📁 Template Structure\n```\n"
                                for filename in template_info["files"].keys():
                                    details += f"{filename}\n"
                                details += "```\n"

                            # Add quick start guide
                            details += f"""
#### 🚀 Quick Start

1. **Create from template:**
   ```bash
   gmp create {template_name} my-server
   ```

2. **Navigate to directory:**
   ```bash
   cd servers/my-server
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server:**
   ```bash
   python app.py
   ```
"""

                            # Show action buttons
                            actions = """
Ready to use this template? Click the button above or use the Quick Create tab to get started!
"""

                            return (
                                details,
                                gr.update(visible=True),
                                gr.update(value=actions, visible=True),
                            )

                        def filter_templates(category, search=None):
                            # Handle cases where search might not be provided
                            if search is None:
                                search = ""
                            return create_templates_grid(category, search)

                        def use_selected_template(template_name=None):
                            # Switch to Quick Create tab and pre-select the template
                            # This would require updating the Quick Create template dropdown
                            if template_name:
                                return gr.update(value=template_name)
                            return gr.update()

                        # Now create the UI components
                        # Template categories
                        with gr.Row():
                            template_category_filter = gr.Radio(
                                choices=["All", "Starter", "Tools", "AI/ML", "Data", "Integration"],
                                value="All",
                                label="Filter by Category",
                                interactive=True,
                            )
                            template_search = gr.Textbox(
                                placeholder="Search templates...", label="Search", scale=2
                            )

                        # Templates grid
                        with gr.Row():
                            templates_grid = gr.HTML(value=create_templates_grid())

                        # Selected template details
                        with gr.Row():
                            with gr.Column(scale=1):
                                # Get available templates and ensure safe initialization
                                available_templates = (
                                    registry.list_templates() if HAS_REGISTRY else []
                                )

                                selected_template_dropdown = gr.Dropdown(
                                    choices=available_templates,
                                    label="Select Template",
                                    value=None,
                                    interactive=True,
                                )

                                use_template_btn = gr.Button(
                                    "🚀 Use This Template",
                                    variant="primary",
                                    size="lg",
                                    visible=False,
                                )

                                template_actions = gr.Markdown(visible=False)

                            with gr.Column(scale=2):
                                template_details = gr.Markdown(
                                    value="### Select a template to view details",
                                    elem_classes=["template-details"],
                                )

                        # Setup event handlers after all components are created
                        template_category_filter.change(
                            filter_templates,
                            inputs=[template_category_filter, template_search],
                            outputs=[templates_grid],
                        )

                        template_search.change(
                            filter_templates,
                            inputs=[template_category_filter, template_search],
                            outputs=[templates_grid],
                        )

                        selected_template_dropdown.change(
                            show_template_details,
                            inputs=[selected_template_dropdown],
                            outputs=[template_details, use_template_btn, template_actions],
                        )

                        # Note: This references template_dropdown from Quick Create tab
                        # We'll handle this connection at the dashboard level instead
                        def switch_to_quick_create_with_template(template_name):
                            # Return template name to be handled by parent
                            return template_name

                        # This will be connected to template_dropdown after it's created
                        def use_template_handler(template_name):
                            if template_name:
                                return gr.update(value=template_name)
                            return gr.update()

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

            # Tab 4: Agent Control Panel (moved after Server Management)
            with gr.Tab("🤖 Agent Control Panel"):
                if HAS_CONTROL_PANEL:
                    try:
                        # Initialize control panel
                        control_panel = ControlPanelUI()

                        # Add iframe viewer for deployed agents
                        with gr.Row():
                            with gr.Column(scale=3):
                                # Create the control panel components
                                control_panel.create_components()

                            with gr.Column(scale=2):
                                gr.Markdown("### 🌐 Agent Viewer")
                                gr.Markdown("Open deployed agents directly in the dashboard")

                                # Agent viewer controls
                                with gr.Row():
                                    deployed_agent_dropdown = gr.Dropdown(
                                        label="Select Deployed Agent",
                                        choices=["No agents deployed yet"],
                                        value=None,
                                        interactive=True,
                                        allow_custom_value=False,
                                    )
                                    open_agent_btn = gr.Button("🔗 Open Agent", variant="primary")

                                # Iframe to display the agent
                                agent_iframe = gr.HTML(
                                    value='<div style="text-align: center; padding: 50px; color: #666;">Select a deployed agent to view it here</div>',
                                    label="Agent Interface",
                                    elem_id="agent-viewer-iframe",
                                )

                                # Refresh deployed agents list
                                def refresh_deployed_agents():
                                    """Get list of deployed agents with their ports"""
                                    if control_panel and control_panel.agent_runner:
                                        agents = control_panel.agent_runner.list_agents()
                                        choices = []
                                        for name, info in agents.items():
                                            if info.get("status") == "running" and info.get("port"):
                                                choices.append(f"{name} (port {info['port']})")
                                        if choices:
                                            return gr.update(choices=choices, value=None)
                                        else:
                                            return gr.update(
                                                choices=["No agents deployed yet"], value=None
                                            )
                                    return gr.update(choices=["No agents deployed yet"], value=None)

                                # Open agent in iframe
                                def open_agent_in_iframe(agent_selection):
                                    """Open selected agent in iframe"""
                                    if (
                                        not agent_selection
                                        or agent_selection == "No agents deployed yet"
                                    ):
                                        return '<div style="text-align: center; padding: 50px; color: #666;">Select a deployed agent to view it here</div>'

                                    # Extract port from selection
                                    import re

                                    port_match = re.search(r"\(port (\d+)\)", agent_selection)
                                    if port_match:
                                        port = port_match.group(1)
                                        # Create iframe HTML
                                        iframe_html = f"""
                                        <iframe 
                                            src="http://localhost:{port}" 
                                            width="100%" 
                                            height="600px" 
                                            style="border: 1px solid #ddd; border-radius: 8px;"
                                            title="{agent_selection}">
                                        </iframe>
                                        """
                                        return iframe_html
                                    return '<div style="text-align: center; padding: 50px; color: #f00;">Could not determine agent port</div>'

                                # Auto-refresh deployed agents dropdown
                                deployed_agents_timer = gr.Timer(10.0)
                                deployed_agents_timer.tick(
                                    fn=refresh_deployed_agents, outputs=[deployed_agent_dropdown]
                                )

                                # Open agent button handler
                                open_agent_btn.click(
                                    fn=open_agent_in_iframe,
                                    inputs=[deployed_agent_dropdown],
                                    outputs=[agent_iframe],
                                )

                    except Exception as e:
                        gr.Markdown("### Agent Control Panel Error")
                        gr.Markdown(f"Failed to initialize control panel: {str(e)}")
                        gr.Markdown("Please ensure all agent dependencies are installed.")
                else:
                    gr.Markdown("### Agent Control Panel Unavailable")
                    gr.Markdown(
                        """
                        The Agent Control Panel requires additional components to be installed.
                        
                        To enable this feature:
                        1. Ensure the agent directory is properly set up
                        2. Install required dependencies
                        3. Restart the application
                        """
                    )

            # Tab 5: MCP Connections (Merged)
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

            # Tab 6: Help & Resources
            with gr.Tab("📚 Help & Resources"):
                with gr.Tabs():
                    # User Guides
                    with gr.Tab("📖 User Guides"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                # Documentation selector
                                doc_category = gr.Radio(
                                    label="Documentation Category",
                                    choices=[
                                        "Getting Started",
                                        "Configuration",
                                        "Advanced Topics",
                                        "API Reference",
                                    ],
                                    value="Getting Started",
                                )

                                doc_list = gr.Dataframe(
                                    headers=["Document", "Description"],
                                    label="Available Documents",
                                    interactive=False,
                                    value=[
                                        [
                                            "Getting Started Guide",
                                            "Learn the basics of Gradio MCP Playground",
                                        ],
                                        ["User Guide", "Comprehensive guide to all features"],
                                    ],
                                )

                                doc_selector = gr.Dropdown(
                                    label="Select Document",
                                    choices=["getting-started.md", "user_guide.md"],
                                    value="getting-started.md",
                                    interactive=True,
                                )

                                load_doc_btn = gr.Button("📄 Load Document", variant="primary")

                            with gr.Column(scale=2):
                                # Document viewer
                                doc_viewer = gr.Markdown(
                                    value="# Welcome to Gradio MCP Playground\n\nSelect a document from the left to view its contents.",
                                    label="Document Viewer",
                                    elem_id="doc-viewer",
                                )

                    # Configuration Guide
                    with gr.Tab("⚙️ Configuration"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                config_topic = gr.Radio(
                                    label="Configuration Topics",
                                    choices=[
                                        "Basic Configuration",
                                        "API Keys & Security",
                                        "Model Configuration",
                                        "Server Configuration",
                                    ],
                                    value="Basic Configuration",
                                )

                                config_doc_selector = gr.Dropdown(
                                    label="Select Guide",
                                    choices=["configuration.md", "api_key_handling.md"],
                                    value="configuration.md",
                                    interactive=True,
                                )

                                load_config_doc_btn = gr.Button("📄 Load Guide")

                            with gr.Column(scale=2):
                                config_doc_viewer = gr.Markdown(
                                    value="# Configuration Guide\n\nSelect a configuration topic to learn more."
                                )

                    # Quick Start
                    with gr.Tab("🚀 Quick Start"):
                        gr.Markdown(
                            """
                            # 🚀 Quick Start Guide
                            
                            ## Welcome to Gradio MCP Playground!
                            
                            ### 🎯 Getting Started in 3 Steps:
                            
                            **1. Configure Your AI Assistant** 🤖
                            - Go to the **AI Assistant** tab
                            - Enter your HuggingFace API token (get one at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))
                            - Click "Configure Model" to activate the AI assistant
                            
                            **2. Create or Connect MCP Servers** 🔧
                            - **Quick Create**: Use the Server Builder tab to create servers from templates
                            - **Connect Existing**: Use MCP Connections tab to connect to running servers
                            - **Visual Pipeline**: Build complex workflows with the Pipeline Builder
                            
                            **3. Deploy and Manage Agents** 🌐
                            - Use the **Agent Control Panel** to deploy Gradio agents
                            - View deployed agents directly in the embedded viewer
                            - Monitor agent health and performance in real-time
                            
                            ### 📚 Key Features:
                            
                            **AI Assistants** 🤖
                            - **Adam**: General assistant with MCP tool access
                            - **Liam**: MCP development specialist
                            - **Arthur**: Agent creation specialist
                            
                            **Server Management** 🖥️
                            - Create servers from templates
                            - Manage server lifecycle
                            - Browse and install from registry
                            
                            **Agent Deployment** 🚀
                            - Deploy custom Gradio agents
                            - Real-time monitoring
                            - Embedded agent viewer
                            
                            **MCP Connections** 🔌
                            - Connect to multiple MCP servers
                            - Quick connect to popular servers
                            - Custom server connections
                            
                            ### 💡 Pro Tips:
                            
                            1. **Use the AI Assistant**: Ask questions like "How do I create a calculator server?" or "Help me build a data processing pipeline"
                            
                            2. **Explore Templates**: Check out the Server Builder templates for quick starts
                            
                            3. **Monitor Performance**: Keep an eye on the Agent Control Panel for agent health
                            
                            4. **Read the Docs**: Use the documentation tabs for detailed guides
                            
                            ### 🔗 Useful Resources:
                            - [MCP Protocol Documentation](https://github.com/anthropics/mcp)
                            - [Gradio Documentation](https://gradio.app/docs)
                            - [Project Repository](https://github.com/seanpoyner/gradio-mcp-playground)
                            
                            ### ❓ Need Help?
                            - Check the other documentation tabs for detailed guides
                            - Use the AI Assistant for interactive help
                            - Report issues on [GitHub](https://github.com/seanpoyner/gradio-mcp-playground/issues)
                            """
                        )

                    # Tutorials & Examples
                    with gr.Tab("💡 Tutorials"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                tutorial_category = gr.Radio(
                                    label="Tutorial Category",
                                    choices=[
                                        "Quick Start",
                                        "Server Creation",
                                        "MCP Connections",
                                        "Agent Development",
                                        "Advanced Topics",
                                    ],
                                    value="Quick Start",
                                )

                                # Tutorial list that updates based on category
                                tutorial_list = gr.Dataframe(
                                    headers=["Tutorial", "Description"],
                                    interactive=True,
                                    value=[
                                        [
                                            "Getting Started",
                                            "Learn the basics of Gradio MCP Playground",
                                        ],
                                        [
                                            "Your First Server",
                                            "Create and run your first MCP server",
                                        ],
                                        [
                                            "Using AI Assistant",
                                            "How to use the AI assistant effectively",
                                        ],
                                    ],
                                )

                                # Hidden dropdown for tutorial selection
                                tutorial_dropdown = gr.Dropdown(
                                    visible=False,
                                    choices=["getting-started.md"],
                                    value="getting-started.md",
                                )

                            with gr.Column(scale=2):
                                tutorial_content = gr.Markdown(
                                    value="# Getting Started\n\nSelect a tutorial from the list to begin."
                                )

                    # API Reference
                    with gr.Tab("🔧 API Reference"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                api_category = gr.Dropdown(
                                    label="API Category",
                                    choices=[
                                        "MCP Protocol",
                                        "Server API",
                                        "Client API",
                                        "Tool Development",
                                        "Agent API",
                                    ],
                                    value="MCP Protocol",
                                )

                                api_method_list = gr.Markdown(
                                    """
                                    ### MCP Protocol Methods:
                                    
                                    **Core Methods:**
                                    - `initialize()`
                                    - `list_tools()`
                                    - `call_tool()`
                                    - `list_resources()`
                                    
                                    **Server Methods:**
                                    - `create_server()`
                                    - `start_server()`
                                    - `stop_server()`
                                    """
                                )

                            with gr.Column(scale=2):
                                gr.Markdown(
                                    """
                                    # 🔧 API Reference
                                    
                                    ## MCP Protocol Overview
                                    
                                    The Model Context Protocol (MCP) provides a standard interface for AI models to interact with external tools and resources.
                                    
                                    ### Core Concepts
                                    
                                    **1. Tools** - Functions that can be called by the AI
                                    ```python
                                    @server.tool()
                                    async def my_tool(param: str) -> str:
                                        return f"Processed: {param}"
                                    ```
                                    
                                    **2. Resources** - Data that can be accessed by the AI
                                    ```python
                                    @server.resource()
                                    async def get_data() -> Dict[str, Any]:
                                        return {"data": "value"}
                                    ```
                                    
                                    **3. Servers** - Host tools and resources
                                    ```python
                                    server = Server("my-server")
                                    await server.run()
                                    ```
                                    
                                    ### Creating MCP Servers
                                    
                                    **Basic Server Structure:**
                                    ```python
                                    from mcp.server import Server, tool
                                    from mcp.server.stdio import stdio_server
                                    
                                    # Create server instance
                                    server = Server("my-server")
                                    
                                    # Define tools
                                    @server.tool()
                                    async def hello(name: str) -> str:
                                        return f"Hello, {name}!"
                                    
                                    # Run server
                                    async def main():
                                        async with stdio_server() as (read, write):
                                            await server.run(read, write)
                                    ```
                                    
                                    ### Client API
                                    
                                    **Connecting to Servers:**
                                    ```python
                                    from gradio_mcp_playground import GradioMCPClient
                                    
                                    client = GradioMCPClient()
                                    await client.connect_to_server("my-server")
                                    
                                    # List available tools
                                    tools = await client.list_tools()
                                    
                                    # Call a tool
                                    result = await client.call_tool("hello", {"name": "World"})
                                    ```
                                    
                                    ### Agent Development API
                                    
                                    **Creating Custom Agents:**
                                    ```python
                                    class MyAgent:
                                        def __init__(self):
                                            self.name = "My Agent"
                                        
                                        async def process_request(self, request: str) -> str:
                                            # Agent logic here
                                            return "Response"
                                    ```
                                    
                                    ### Best Practices
                                    
                                    1. **Error Handling**: Always handle errors gracefully
                                    2. **Type Hints**: Use type hints for tool parameters
                                    3. **Async/Await**: Use async functions for I/O operations
                                    4. **Documentation**: Document your tools clearly
                                    5. **Testing**: Write tests for your servers
                                    """
                                )

                    # Troubleshooting
                    with gr.Tab("🛠️ Troubleshooting"):
                        gr.Markdown(
                            """
                            # 🛠️ Troubleshooting Guide
                            
                            ## Common Issues and Solutions
                            
                            ### 🔴 AI Assistant Not Working
                            
                            **Problem:** Assistant says "Please configure a model first"
                            
                            **Solution:**
                            1. Get a HuggingFace token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
                            2. Enter the token in the AI Assistant tab
                            3. Select a model from the dropdown
                            4. Click "Configure Model"
                            
                            ### 🔴 Server Won't Start
                            
                            **Problem:** Error when creating or starting a server
                            
                            **Common Causes:**
                            - Port already in use
                            - Missing dependencies
                            - Syntax errors in code
                            
                            **Solutions:**
                            1. **Port conflict**: Change the port number or stop the conflicting process
                            2. **Dependencies**: Run `pip install -r requirements.txt` in the server directory
                            3. **Syntax**: Check the server logs for error details
                            
                            ### 🔴 MCP Connection Failed
                            
                            **Problem:** Can't connect to MCP servers
                            
                            **Solutions:**
                            1. **Check server is running**: Ensure the MCP server process is active
                            2. **Verify credentials**: Some servers need API keys (GitHub, Brave Search)
                            3. **Network issues**: Check firewall settings
                            4. **Path issues**: Use absolute paths for stdio servers
                            
                            ### 🔴 Agent Deployment Fails
                            
                            **Problem:** Agent won't deploy from Control Panel
                            
                            **Solutions:**
                            1. **Check code syntax**: Use the Validate button first
                            2. **Port conflicts**: Agents auto-assign ports (7860-7869)
                            3. **Dependencies**: Ensure required packages are installed
                            4. **Logs**: Check the Agent Health Monitor for errors
                            
                            ### 🔴 Pipeline Builder Issues
                            
                            **Problem:** Pipeline won't execute or connect servers
                            
                            **Solutions:**
                            1. **Check connections**: Ensure all servers are properly connected
                            2. **Circular dependencies**: Avoid creating loops in the pipeline
                            3. **Server compatibility**: Verify data formats match between servers
                            
                            ### 🟡 Performance Issues
                            
                            **Slow Response Times:**
                            - Reduce the number of active agents
                            - Check CPU/Memory usage in Control Panel
                            - Consider using lighter models for AI assistant
                            
                            ### 🟡 Security Warnings
                            
                            **API Key Storage:**
                            - Use secure storage for sensitive keys
                            - Never commit API keys to version control
                            - Set environment variables for production
                            
                            ## 📋 Diagnostic Commands
                            
                            **Check Python Version:**
                            ```bash
                            python --version  # Should be 3.8+
                            ```
                            
                            **Check Dependencies:**
                            ```bash
                            pip list | grep gradio
                            pip list | grep mcp
                            ```
                            
                            **Test MCP Server:**
                            ```bash
                            # Test a simple echo server
                            echo '{"method": "list_tools"}' | python -m your_server
                            ```
                            
                            **View Logs:**
                            - Server logs: Check terminal where server is running
                            - Agent logs: Use Agent Health Monitor
                            - System logs: Check `~/.gmp/logs/`
                            
                            ## 🆘 Getting Help
                            
                            1. **Check Documentation**: Review guides in other tabs
                            2. **AI Assistant**: Ask Liam for MCP-specific help
                            3. **GitHub Issues**: [Report bugs](https://github.com/seanpoyner/gradio-mcp-playground/issues)
                            4. **Community**: Join discussions on GitHub
                            
                            ## 🔍 Debug Mode
                            
                            Enable debug logging:
                            ```python
                            import logging
                            logging.basicConfig(level=logging.DEBUG)
                            ```
                            
                            This will show detailed information about:
                            - MCP protocol messages
                            - Server connections
                            - Tool executions
                            - Error traces
                            """
                        )

            # Tab 7: Settings
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### Gradio MCP Playground Settings")

                with gr.Tabs():
                    # Basic Settings
                    with gr.Tab("🔧 Basic Settings"):
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

                    # Pipeline Configuration
                    with gr.Tab("🔗 Pipeline Settings"):
                        with gr.Column():
                            pipeline_step_timeout = gr.Number(
                                label="Step Timeout (seconds)",
                                value=30,
                                minimum=5,
                                maximum=300,
                                precision=0,
                                info="Maximum time to wait for each pipeline step",
                            )

                            pipeline_error_handling = gr.Dropdown(
                                choices=["stop", "continue", "retry", "skip"],
                                label="Error Handling Method",
                                value="stop",
                                info="How to handle errors in pipeline execution",
                            )

                            pipeline_retry_attempts = gr.Number(
                                label="Retry Attempts",
                                value=3,
                                minimum=0,
                                maximum=10,
                                precision=0,
                                info="Number of retry attempts for failed steps",
                            )

                            pipeline_data_flow = gr.Radio(
                                choices=["sequential", "parallel", "adaptive"],
                                label="Data Flow Mode",
                                value="sequential",
                                info="How data flows between pipeline servers",
                            )

                            pipeline_max_concurrent = gr.Number(
                                label="Max Concurrent Servers",
                                value=5,
                                minimum=1,
                                maximum=20,
                                precision=0,
                                info="Maximum number of servers to run concurrently",
                            )

                    # Server Configuration
                    with gr.Tab("🖥️ Server Settings"):
                        with gr.Column():
                            server_startup_timeout = gr.Number(
                                label="Server Startup Timeout (seconds)",
                                value=30,
                                minimum=5,
                                maximum=120,
                                precision=0,
                                info="Time to wait for servers to start",
                            )

                            server_health_check_interval = gr.Number(
                                label="Health Check Interval (seconds)",
                                value=10,
                                minimum=5,
                                maximum=60,
                                precision=0,
                                info="How often to check server health",
                            )

                            server_auto_restart = gr.Checkbox(
                                label="Auto-restart Failed Servers",
                                value=True,
                                info="Automatically restart servers that crash",
                            )

                            server_memory_limit = gr.Number(
                                label="Memory Limit per Server (MB)",
                                value=512,
                                minimum=128,
                                maximum=4096,
                                precision=0,
                                info="Maximum memory usage per server",
                            )

                save_settings_btn = gr.Button("💾 Save Settings", variant="primary")
                settings_output = gr.Textbox(label="Settings Output", visible=False)

        # Documentation loading functions
        def load_documentation(doc_file: str) -> str:
            """Load documentation from /docs directory"""
            try:
                docs_dir = Path(__file__).parent.parent / "docs"
                doc_path = docs_dir / doc_file

                if not doc_path.exists():
                    return f"# Document Not Found\n\nThe document '{doc_file}' was not found in the documentation directory."

                with open(doc_path, encoding="utf-8") as f:
                    content = f.read()

                # Add a header if the file doesn't start with one
                if not content.strip().startswith("#"):
                    title = doc_file.replace(".md", "").replace("_", " ").title()
                    content = f"# {title}\n\n{content}"

                return content
            except Exception as e:
                return f"# Error Loading Documentation\n\nAn error occurred while loading '{doc_file}':\n\n```\n{str(e)}\n```"

        def update_doc_list(category: str) -> Tuple[gr.Dataframe, gr.Dropdown, gr.Dropdown]:
            """Update document list based on category"""
            doc_mapping = {
                "Getting Started": [
                    ["Getting Started Guide", "Learn the basics of Gradio MCP Playground"],
                    ["User Guide", "Comprehensive guide to all features"],
                ],
                "Configuration": [
                    ["Configuration Guide", "Complete configuration reference"],
                    ["API Key Handling", "Secure storage and management of API keys"],
                    ["Requirements-based Installation", "Installing specific feature sets"],
                ],
                "Advanced Topics": [
                    ["MCP Server Types", "Understanding different server implementations"],
                    ["Performance Optimization", "Tips for optimizing your servers"],
                    ["Obsidian WSL Guide", "Using Obsidian vault with WSL"],
                ],
                "API Reference": [
                    ["GitHub Tools Reference", "Complete GitHub MCP server reference"],
                    ["MCP Protocol", "Model Context Protocol specification"],
                ],
            }

            file_mapping = {
                "Getting Started Guide": "getting-started.md",
                "User Guide": "user_guide.md",
                "Configuration Guide": "configuration.md",
                "API Key Handling": "api_key_handling.md",
                "Requirements-based Installation": "requirements_based_installation.md",
                "MCP Server Types": "mcp_server_types.md",
                "Performance Optimization": "performance_optimization.md",
                "Obsidian WSL Guide": "obsidian_wsl_guide.md",
                "GitHub Tools Reference": "github_tools_reference.md",
            }

            docs = doc_mapping.get(category, [])
            doc_choices = [file_mapping.get(doc[0], "") for doc in docs if doc[0] in file_mapping]
            default_doc = doc_choices[0] if doc_choices else "getting-started.md"

            # Return proper Gradio updates
            return (
                gr.update(value=docs),  # Update dataframe with new docs
                gr.update(choices=doc_choices, value=default_doc),  # Update dropdown choices
                gr.update(choices=doc_choices, value=default_doc),  # Update both dropdowns
            )

        def update_config_doc_list(topic: str) -> Tuple[gr.Dropdown, str]:
            """Update configuration document based on topic"""
            topic_mapping = {
                "Basic Configuration": ["configuration.md"],
                "API Keys & Security": ["api_key_handling.md"],
                "Model Configuration": ["configuration.md"],
                "Server Configuration": ["mcp_server_types.md"],
            }

            choices = topic_mapping.get(topic, ["configuration.md"])
            doc_file = choices[0]
            content = load_documentation(doc_file)

            return gr.update(choices=choices, value=doc_file), content

        def update_tutorial_list(category: str) -> Tuple[gr.Dataframe, gr.Dropdown, str]:
            """Update tutorial list based on category"""
            tutorial_mapping = {
                "Quick Start": [
                    ["Getting Started", "Learn the basics of Gradio MCP Playground"],
                    ["Your First Server", "Create and run your first MCP server"],
                    ["Using AI Assistant", "How to use the AI assistant effectively"],
                ],
                "Server Creation": [
                    ["Calculator Server", "Build a calculator with MCP tools"],
                    ["Text Processor", "Create text processing tools"],
                    ["Image Tools", "Build image manipulation servers"],
                    ["Data Analyzer", "Create data analysis servers"],
                ],
                "MCP Connections": [
                    ["Connecting to Servers", "How to connect to MCP servers"],
                    ["GitHub Integration", "Connect and use GitHub MCP server"],
                    ["Filesystem Access", "Use the filesystem MCP server"],
                    ["Managing Connections", "Manage multiple MCP connections"],
                ],
                "Agent Development": [
                    ["Agent Builder Basics", "Create agents with Agent Builder"],
                    ["Custom System Prompts", "Write effective system prompts"],
                    ["Agent Templates", "Use and customize agent templates"],
                    ["Deploying Agents", "Deploy agents to production"],
                ],
                "Advanced Topics": [
                    ["Pipeline Building", "Create complex server pipelines"],
                    ["Custom MCP Tools", "Build your own MCP tools"],
                    ["Performance Tips", "Optimize server performance"],
                    ["Security Best Practices", "Secure your MCP servers"],
                ],
            }

            # Map tutorial names to documentation files
            file_mapping = {
                "Getting Started": "getting-started.md",
                "Your First Server": "getting-started.md",
                "Using AI Assistant": "user_guide.md",
                "Calculator Server": "getting-started.md",
                "Agent Builder Basics": "user_guide.md",
                "Pipeline Building": "user_guide.md",
                "Performance Tips": "performance_optimization.md",
                "Connecting to Servers": "mcp_server_types.md",
            }

            tutorials = tutorial_mapping.get(category, tutorial_mapping["Quick Start"])

            # Get the first tutorial's file
            first_tutorial = tutorials[0][0] if tutorials else "Getting Started"
            doc_file = file_mapping.get(first_tutorial, "getting-started.md")

            # Create dropdown choices
            choices = []
            for tutorial in tutorials:
                mapped_file = file_mapping.get(tutorial[0], "getting-started.md")
                if mapped_file not in choices:
                    choices.append(mapped_file)

            content = load_documentation(doc_file)

            return (
                gr.update(value=tutorials),  # Update dataframe
                gr.update(choices=choices, value=doc_file),  # Update dropdown
                content,  # Return content as string
            )

        def handle_tutorial_selection(evt: gr.SelectData, tutorial_list_data) -> Tuple[str, str]:
            """Handle clicking on a tutorial in the dataframe"""
            if evt and hasattr(evt, "index"):
                row_idx = evt.index[0]
                if row_idx < len(tutorial_list_data):
                    tutorial_name = tutorial_list_data[row_idx][0]

                    # Map tutorial name to file
                    file_mapping = {
                        "Getting Started": "getting-started.md",
                        "Your First Server": "getting-started.md",
                        "Using AI Assistant": "user_guide.md",
                        "Calculator Server": "getting-started.md",
                        "Agent Builder Basics": "user_guide.md",
                        "Pipeline Building": "user_guide.md",
                        "Performance Tips": "performance_optimization.md",
                        "Connecting to Servers": "mcp_server_types.md",
                    }

                    doc_file = file_mapping.get(tutorial_name, "getting-started.md")
                    content = load_documentation(doc_file)
                    return doc_file, content

            return gr.update(), gr.update()

        # Event handlers

        # Server management functions (implementations)
        def create_server(name, template, port):
            """Create a new MCP server"""
            if not HAS_REGISTRY:
                return "Registry not available"

            try:
                if not name:
                    return "Please provide a server name"

                # Define the directory for the new server
                from pathlib import Path

                # Use config_manager's directory to ensure consistency
                if HAS_CONFIG_MANAGER:
                    servers_dir = config_manager.config_dir / "servers"
                else:
                    servers_dir = Path.home() / ".gradio-mcp" / "servers"
                servers_dir.mkdir(parents=True, exist_ok=True)
                server_directory = servers_dir / name

                # Create server using registry with correct argument order
                result = registry.create_from_template(template, name, server_directory, port=port)
                # The method returns a config dict if successful, not a success flag
                if result and "path" in result:
                    # Register the server in servers.json so it appears in the management tab
                    if HAS_CONFIG_MANAGER:
                        try:
                            server_config = {
                                "name": name,
                                "path": result["path"],
                                "directory": result["directory"],
                                "template": template,
                                "port": port,
                                "created": result.get("created"),
                            }
                            config_manager.add_server(server_config)
                        except Exception as reg_error:
                            # Server was created but registration failed - warn the user
                            return f"⚠️ Server '{name}' created but registration failed: {str(reg_error)}\nPath: {result['path']}\nDirectory: {result['directory']}\n\nYou can manually register it using: gmp server add {name} {result['path']}"

                    return f"✅ Server '{name}' created and registered successfully!\nPath: {result['path']}\nDirectory: {result['directory']}"
                else:
                    return "❌ Failed to create server: No server configuration returned"
            except Exception as e:
                return f"❌ Error creating server: {str(e)}"

        def refresh_servers():
            """Refresh the servers list"""
            if not HAS_CONFIG_MANAGER:
                return [], gr.update(choices=[], value=None)

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

            return data, gr.update(choices=choices, value=None)

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

                # Get server info from registry
                server_info = registry.get_mcp_server(server_name)
                if not server_info:
                    return f"❌ Server '{server_name}' not found in registry"

                # Generate install command
                install_info = registry.generate_install_command(server_name, user_args)
                if not install_info:
                    return f"❌ Failed to generate install command for {server_name}"

                # For now, just return the install info
                # In a full implementation, this would execute the install command
                return f"""✅ Installation info for {server_name}:
                
**Command**: {install_info.get('command', 'N/A')}
**Args**: {' '.join(install_info.get('args', []))}
**Required Args**: {', '.join(server_info.get('required_args', []))}
**Environment Variables**: {', '.join(server_info.get('env_vars', {}).keys())}

To complete installation, run the command above or use the MCP Connections tab to connect."""
            except Exception as e:
                return f"❌ Error installing: {str(e)}"

        def start_server(server_name):
            """Start a server"""
            if not server_name:
                return refresh_servers()[0]

            if not HAS_SERVER_MANAGER or not server_manager:
                return refresh_servers()[0]

            try:
                result = server_manager.start_server(server_name)
                if result.get("success"):
                    print(f"Server '{server_name}' started successfully")
                else:
                    print(
                        f"Failed to start server '{server_name}': {result.get('error', 'Unknown error')}"
                    )
                return refresh_servers()[0]
            except Exception as e:
                print(f"Error starting server: {e}")
                return refresh_servers()[0]

        def stop_server(server_name):
            """Stop a server"""
            if not server_name:
                return refresh_servers()[0]

            if not HAS_SERVER_MANAGER or not server_manager:
                return refresh_servers()[0]

            try:
                result = server_manager.stop_server(server_name)
                if result.get("success"):
                    print(f"Server '{server_name}' stopped successfully")
                else:
                    print(
                        f"Failed to stop server '{server_name}': {result.get('error', 'Unknown error')}"
                    )
                return refresh_servers()[0]
            except Exception as e:
                print(f"Error stopping server: {e}")
                return refresh_servers()[0]

        def delete_server(server_name):
            """Delete a server"""
            if not server_name:
                return refresh_servers()

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

                greeting = "👋 Hi! I'm Liam, your MCP development specialist.\n\n"
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
                # Show general assistant, hide others
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
            elif mode == "MCP Agent":
                # Show MCP agent (Liam), hide others
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
            else:  # Agent Builder
                # Show agent builder (Arthur), hide others
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

        assistant_mode.change(
            switch_assistant_mode,
            inputs=[assistant_mode],
            outputs=[general_assistant_group, mcp_agent_group, agent_builder_group],
        )

        # Event handlers for all assistant modes
        if coding_agent:
            # Import additional event handler functions from web_ui
            from .web_ui import configure_model as _configure_model
            from .web_ui import reset_conversation

            # Define message handling functions locally
            def handle_message_submit(message, history, show_thinking):
                """Handle message submission with immediate display"""
                if not message or not message.strip():
                    return history or [], ""

                # Clear input immediately and show user message
                history_with_user = (history or []) + [{"role": "user", "content": message}]

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
                        # If query is empty, show all servers
                        if not query or query.strip() == "":
                            results = registry.get_all(server_type="mcp_server")
                        else:
                            results = registry.search(query, server_type="mcp_server")

                        if results:
                            # Format results for dataframe
                            data = []
                            choices = []
                            for server in results:
                                # Handle both direct server data and search results
                                server_data = server if isinstance(server, dict) else server
                                data.append(
                                    [
                                        server_data.get("name", server_data.get("id", "")),
                                        server_data.get("category", ""),
                                        server_data.get("description", ""),
                                        server_data.get("install_method", ""),
                                    ]
                                )
                                choices.append(server_data.get("id", server_data.get("name", "")))
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

                def save_settings(
                    port,
                    auto_reload,
                    protocol,
                    log_level,
                    step_timeout,
                    error_handling,
                    retry_attempts,
                    data_flow,
                    max_concurrent,
                    startup_timeout,
                    health_check_interval,
                    auto_restart,
                    memory_limit,
                ):
                    """Save settings"""
                    try:
                        # Basic settings
                        config_manager.default_port = port
                        config_manager.auto_reload = auto_reload
                        config_manager.mcp_protocol = protocol
                        config_manager.log_level = log_level

                        # Pipeline settings
                        config_manager.pipeline_step_timeout = step_timeout
                        config_manager.pipeline_error_handling = error_handling
                        config_manager.pipeline_retry_attempts = retry_attempts
                        config_manager.pipeline_data_flow = data_flow
                        config_manager.pipeline_max_concurrent = max_concurrent

                        # Server settings
                        config_manager.server_startup_timeout = startup_timeout
                        config_manager.server_health_check_interval = health_check_interval
                        config_manager.server_auto_restart = auto_restart
                        config_manager.server_memory_limit = memory_limit

                        config_manager.save_config()
                        return gr.update(value="✅ All settings saved successfully!", visible=True)
                    except Exception as e:
                        return gr.update(value=f"❌ Error saving settings: {str(e)}", visible=True)

                save_settings_btn.click(
                    save_settings,
                    inputs=[
                        settings_port,
                        settings_auto_reload,
                        settings_protocol,
                        settings_log_level,
                        pipeline_step_timeout,
                        pipeline_error_handling,
                        pipeline_retry_attempts,
                        pipeline_data_flow,
                        pipeline_max_concurrent,
                        server_startup_timeout,
                        server_health_check_interval,
                        server_auto_restart,
                        server_memory_limit,
                    ],
                    outputs=[settings_output],
                )

            # Documentation event handlers
            if "doc_category" in locals():
                # Update document list when category changes
                doc_category.change(
                    update_doc_list,
                    inputs=[doc_category],
                    outputs=[doc_list, doc_selector, doc_selector],
                )

                # Load document when button is clicked
                load_doc_btn.click(load_documentation, inputs=[doc_selector], outputs=[doc_viewer])

                # Also load document when selection changes
                doc_selector.change(load_documentation, inputs=[doc_selector], outputs=[doc_viewer])

            if "config_topic" in locals():
                # Update config document when topic changes
                config_topic.change(
                    update_config_doc_list,
                    inputs=[config_topic],
                    outputs=[config_doc_selector, config_doc_viewer],
                )

                # Load config document when button is clicked
                load_config_doc_btn.click(
                    load_documentation, inputs=[config_doc_selector], outputs=[config_doc_viewer]
                )

            if "tutorial_category" in locals():
                # Update tutorial list when category changes
                tutorial_category.change(
                    update_tutorial_list,
                    inputs=[tutorial_category],
                    outputs=[tutorial_list, tutorial_dropdown, tutorial_content],
                )

                # Handle clicking on a tutorial in the list
                tutorial_list.select(
                    handle_tutorial_selection,
                    inputs=[tutorial_list],
                    outputs=[tutorial_dropdown, tutorial_content],
                )

                # Also update content when dropdown changes
                tutorial_dropdown.change(
                    load_documentation, inputs=[tutorial_dropdown], outputs=[tutorial_content]
                )

            # Connection management buttons
            if "disconnect_btn" in locals():
                disconnect_btn.click(
                    disconnect_mcp,
                    inputs=[connection_dropdown],
                    outputs=[gr.Textbox(visible=False)],  # Status message
                ).then(refresh_connections, outputs=[connections_list, connection_dropdown])

            # Connect Template Browser button to Quick Create template dropdown
            if "use_template_btn" in locals() and "template_dropdown" in locals():
                use_template_btn.click(
                    use_template_handler,
                    inputs=[selected_template_dropdown],
                    outputs=[template_dropdown],
                )

        # Initialize on load
        if "connections_list" in locals():
            # Add load event to refresh connections
            dashboard.load(refresh_connections, outputs=[connections_list, connection_dropdown])

        # Also initialize servers list on load
        if "servers_list" in locals() and HAS_CONFIG_MANAGER:
            # Add another load event to refresh servers
            dashboard.load(refresh_servers, outputs=[servers_list, server_dropdown])

        # Initialize registry with all servers on load
        if "registry_results_df" in locals() and HAS_REGISTRY:
            # Show all servers when the page loads
            dashboard.load(
                lambda: search_registry(""),  # Empty query to show all
                outputs=[registry_results_df, registry_server_selector],
            )

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
        favicon_path=None,
    )


if __name__ == "__main__":
    launch_unified_dashboard()
