#!/usr/bin/env python3
"""GMP Agent - Intelligent MCP Server Builder

Main application entry point for the GMP Agent, a conversational AI interface
for building and managing MCP servers using the Gradio MCP Playground toolkit.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import gradio as gr
from rich.console import Console
from rich.logging import RichHandler

# Import core components
try:
    from core.agent import GMPAgent
    from ui.chat_interface import ChatInterface
    from ui.pipeline_view import PipelineView
    from ui.server_manager import ServerManager
    from ui.control_panel import ControlPanelUI
    from ui.mcp_connections_panel import MCPConnectionsPanel
except ImportError as e:
    console.print(f"[red]Import error: {e}[/red]")
    console.print("[yellow]Make sure you're running from the agent directory or have proper Python path setup[/yellow]")
    sys.exit(1)

console = Console()

def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

def load_config(config_path: Optional[Path] = None) -> dict:
    """Load application configuration"""
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "default.json"
    
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[yellow]Config file not found: {config_path}[/yellow]")
        return {}
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in config file: {e}[/red]")
        return {}

def create_agent_interface() -> gr.Interface:
    """Create the main agent interface"""
    
    # Initialize core components
    agent = GMPAgent()
    chat_interface = ChatInterface(agent)
    pipeline_view = PipelineView(agent)
    server_manager = ServerManager(agent)
    control_panel = ControlPanelUI()
    mcp_connections = MCPConnectionsPanel(agent)
    
    # Connect components
    chat_interface.set_mcp_connections_panel(mcp_connections)
    
    # Custom CSS for better styling
    css = """
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
    }
    
    .pipeline-container {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    
    .server-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #007bff;
    }
    
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-running {
        background-color: #28a745;
    }
    
    .status-stopped {
        background-color: #dc3545;
    }
    
    .status-building {
        background-color: #ffc107;
    }
    
    .mcp-connection-card {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #3b82f6;
        transition: all 0.2s ease;
    }
    
    .mcp-connection-card:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    .connection-status-active {
        color: #10b981;
        font-weight: bold;
    }
    
    .connection-status-inactive {
        color: #ef4444;
        font-weight: bold;
    }
    """
    
    with gr.Blocks(
        title="GMP Agent - Intelligent MCP Server Builder",
        css=css,
        theme=gr.themes.Soft()
    ) as interface:
          # Header
        gr.Markdown("""
        # 🤖 GMP Agent - Intelligent MCP Server Builder
        
        Welcome! I'm your intelligent assistant for building and managing MCP servers. 
        Tell me what you want to create in plain language, and I'll help you build it using the Gradio MCP Playground toolkit.
        
        ## ✨ NEW: AI-Powered Responses
        Configure HuggingFace models in the chat interface for enhanced, context-aware responses!
        
        **Examples:**
        - "Create a calculator server with basic math operations"
        - "Build an image processing pipeline that can resize and filter images"  
        - "I need a data analysis tool that works with CSV files"
        - "Help me understand how MCP servers work"
        """)
        with gr.Tabs() as tabs:
            
            # Chat Tab - Main conversation interface
            with gr.Tab("💬 Chat", id="chat"):
                chat_interface.create_interface()
            
            # Pipeline Tab - Visual pipeline builder
            with gr.Tab("🔧 Pipeline Builder", id="pipeline"):
                pipeline_view.create_interface()
            
            # Servers Tab - Server management
            with gr.Tab("🖥️ Server Manager", id="servers"):
                server_manager.create_interface()
            
            # Control Panel Tab - Agent control and monitoring
            with gr.Tab("🤖 Agent Control Panel", id="control"):
                # Embed the control panel components directly
                control_panel.create_components()
            
            # MCP Connections Tab - Connect to external MCP servers
            with gr.Tab("🔌 MCP Connections", id="mcp_connections"):
                mcp_connections.create_interface()
            
            # Help Tab - Documentation and examples
            with gr.Tab("📚 Help & Examples", id="help"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("""
                        ## 🚀 Quick Start
                        
                        1. **Start a Conversation**: Go to the Chat tab and describe what you want to build
                        2. **Review Suggestions**: I'll suggest relevant servers and configurations
                        3. **Build Your Server**: Approve the approach and I'll create your MCP server
                        4. **Test & Deploy**: Use the built-in tools to test and deploy your server
                        
                        ## 💡 Example Prompts
                        
                        ### Simple Tools
                        - "Create a basic calculator"
                        - "Build a text processor that converts to uppercase"
                        - "Make a simple file converter"
                        
                        ### Data Processing
                        - "I need to analyze CSV data and create charts"
                        - "Build a data cleaning pipeline"
                        - "Create a statistics calculator for datasets"
                        
                        ### AI-Powered Tools
                        - "Build a text summarization server"
                        - "Create an image classification tool"
                        - "Make a sentiment analysis API"
                        
                        ### Complex Pipelines
                        - "Build a content creation workflow: research → write → generate images"
                        - "Create an e-commerce data pipeline: scrape → analyze → report"
                        - "Make a social media management tool: schedule → post → analyze"
                        """)
                    
                    with gr.Column():
                        gr.Markdown("""
                        ## 🛠️ Available Server Types
                        
                        I can help you build various types of MCP servers:
                        
                        ### Basic Tools
                        - Calculator servers
                        - Text processing tools
                        - File manipulation utilities
                        - Data converters
                        
                        ### Advanced Tools
                        - Image processing pipelines
                        - Data analysis platforms
                        - API integration servers
                        - Multi-tool interfaces
                          ### AI-Powered Servers
                        - LLM-based tools
                        - Image generation servers
                        - ML model inference
                        - Natural language processing
                        
                        ## 🤖 AI Model Integration
                        
                        The GMP Agent now supports Hugging Face models for enhanced responses:
                        
                        ### Setup Instructions:
                        1. **Get HF Token**: Get your token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
                        2. **Save Token**: Use the "AI Model Configuration" panel in the Chat tab
                        3. **Select Model**: Choose from Qwen, Mixtral, or Zephyr models
                        4. **Load Model**: Click "Load Model" (may take a few minutes)
                        
                        ### Available Models:
                        - **Qwen/Qwen2.5-Coder-32B-Instruct**: Best for code generation
                        - **mistralai/Mixtral-8x7B-Instruct-v0.1**: Balanced performance
                        - **HuggingfaceH4/zephyr-7b-beta**: Fastest, good for chat
                        
                        ### Security:
                        - Tokens are encrypted with AES-256 encryption
                        - Stored locally with machine-specific keys
                        - Persist across app restarts
                        - Can be deleted anytime
                        
                        ## 🔗 Integration Capabilities
                        
                        - **Web APIs**: Connect to external services
                        - **Databases**: Read/write data from various sources
                        - **File Systems**: Process local and remote files
                        - **Cloud Services**: Integrate with AWS, GCP, Azure
                        - **AI Models**: Use Hugging Face, OpenAI, and local models
                        
                        ## 🎯 Best Practices
                        
                        - Be specific about your requirements
                        - Mention any constraints or preferences
                        - Ask for examples or clarifications
                        - Test servers before deployment
                        - Use version control for your servers
                        """)
        
        # Footer
        gr.Markdown("""
        ---
        🔧 **Built with Gradio MCP Playground** | 
        📖 [Documentation](docs/user_guide.md) | 
        🐛 [Report Issues](https://github.com/gradio-mcp-playground/issues) |
        💡 [Examples](examples/)
        """)
    
    return interface

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="GMP Agent - Intelligent MCP Server Builder")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--share", action="store_true", help="Create public URL")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.dev:
        config["development"] = True
        config["auto_reload"] = True
        args.log_level = "DEBUG"
    
    console.print("🚀 [bold blue]Starting GMP Agent...[/bold blue]")
    console.print(f"📍 Running on: http://{args.host}:{args.port}")
    
    if args.share:
        console.print("🌐 Creating public URL...")
    
    try:
        # Create and launch the interface
        interface = create_agent_interface()
        
        interface.launch(
            server_name=args.host,
            server_port=args.port,
            share=args.share,
            show_api=args.dev,
            debug=args.dev
        )
        
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]GMP Agent stopped by user[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Error starting GMP Agent: {e}[/red]")
        if args.dev:
            raise
        sys.exit(1)

if __name__ == "__main__":
    main()