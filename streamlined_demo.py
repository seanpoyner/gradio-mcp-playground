#!/usr/bin/env python3
"""
Gradio MCP Playground - Streamlined Demo App
Focused on showcasing the most impressive working features
"""

import gradio as gr
import json
from pathlib import Path
from typing import Dict, List, Any
import os

# Import core components
try:
    from gradio_mcp_playground.web_ui import handle_message_submit, process_message as web_ui_process_message
    from gradio_mcp_playground.coding_agent import CodingAgent
    from gradio_mcp_playground.config_manager import ConfigManager
    from gradio_mcp_playground.registry import ServerRegistry
    from gradio_mcp_playground.mcp_connection_manager import MCPConnectionManager
    HAS_CORE = True
except ImportError:
    HAS_CORE = False
    print("Core components not available - running in demo mode")


def create_streamlined_demo():
    """Create a streamlined demo focused on working features"""
    
    # Initialize components
    config_manager = ConfigManager() if HAS_CORE else None
    registry = ServerRegistry() if HAS_CORE else None
    connection_manager = MCPConnectionManager() if HAS_CORE else None
    
    # Initialize coding agent
    coding_agent = None
    if HAS_CORE:
        try:
            coding_agent = CodingAgent()
        except Exception as e:
            print(f"Could not initialize coding agent: {e}")
    
    with gr.Blocks(
        title="Gradio MCP Playground - AI Agent Platform",
        theme=gr.themes.Soft(),
        css="""
        /* Improved message width */
        .prose { max-width: 100% !important; }
        .message-wrap { max-width: 100% !important; }
        
        /* Hero section */
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        /* Feature cards */
        .feature-card {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            transition: transform 0.2s;
        }
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        /* Status indicators */
        .status-good { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-error { color: #ef4444; }
        """
    ) as demo:
        gr.HTML("""
        <div class="hero-section">
            <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">🚀 Gradio MCP Playground</h1>
            <p style="font-size: 1.2rem; opacity: 0.9;">
                Transform any Python function into an AI-powered tool in seconds
            </p>
        </div>
        """)
        
        with gr.Tabs():
            # Tab 1: Live Demo - AI Assistant with MCP Tools
            with gr.Tab("🤖 AI Assistant Demo"):
                gr.Markdown("""
                ### Experience AI + MCP Tools in Action
                
                This assistant has access to multiple MCP servers, giving it superpowers:
                - 📁 **File Operations** - Read, write, and manage files
                - 🔍 **Web Search** - Search the internet for information
                - 📸 **Screenshots** - Capture screenshots of websites
                - 🧠 **Memory** - Remember information across conversations
                - And many more!
                """)
                
                if coding_agent:
                    # Show connected servers
                    def get_connected_servers():
                        if hasattr(coding_agent, '_mcp_servers') and coding_agent._mcp_servers:
                            servers = list(coding_agent._mcp_servers.keys())
                            return f"**🔌 Connected Servers:** {', '.join(servers)}"
                        return "**⚠️ No servers connected** - Connect servers in the next tab"
                    
                    connected_info = gr.Markdown(value=get_connected_servers())
                    
                    # Chat interface
                    chatbot = gr.Chatbot(
                        label="Chat with AI + MCP Tools",
                        height=500,
                        show_copy_button=True,
                        type="messages",
                        bubble_full_width=True,
                        value=[{
                            "role": "assistant",
                            "content": """👋 Hi! I'm your AI assistant with MCP superpowers!

Try asking me to:
- "Take a screenshot of python.org"
- "Search for the latest AI news"
- "Create a Python script that calculates fibonacci numbers"
- "What files are in my Documents folder?"

I can use my connected MCP tools to actually perform these tasks!"""
                        }]
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            label="Message",
                            placeholder="Ask me to do something with MCP tools...",
                            scale=4
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)
                    
                    show_thinking = gr.Checkbox(
                        label="🧠 Show Thinking Process",
                        value=True,
                        info="See how I use tools to complete tasks"
                    )
                    
                    # Event handlers
                    def process_message_wrapper(history, show_thinking):
                        return web_ui_process_message(history, show_thinking, coding_agent)
                    
                    send_btn.click(
                        handle_message_submit,
                        inputs=[msg_input, chatbot, show_thinking],
                        outputs=[chatbot, msg_input]
                    ).then(
                        process_message_wrapper,
                        inputs=[chatbot, show_thinking],
                        outputs=[chatbot]
                    )
                    
                    msg_input.submit(
                        handle_message_submit,
                        inputs=[msg_input, chatbot, show_thinking],
                        outputs=[chatbot, msg_input]
                    ).then(
                        process_message_wrapper,
                        inputs=[chatbot, show_thinking],
                        outputs=[chatbot]
                    )
                else:
                    gr.Markdown("### Configure AI Model")
                    gr.Markdown("Please configure your HuggingFace token in the Settings tab first.")
            
            # Tab 2: Create MCP Server
            with gr.Tab("🔧 Create MCP Server"):
                gr.Markdown("""
                ### Turn Any Gradio App into an MCP Server
                
                It's as simple as adding `mcp_server=True` to your launch!
                """)
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 1️⃣ Write Your Function")
                        code_input = gr.Code(
                            value='''import gradio as gr

def calculate_fibonacci(n: int) -> str:
    """Calculate the nth Fibonacci number.
    
    Args:
                n: The position in the Fibonacci sequence
    
    Returns:
                The nth Fibonacci number
    """
    if n <= 0:
        return "Please enter a positive number"
    elif n == 1:
        return "1"
    elif n == 2:
        return "1"
    else:
        a, b = 1, 1
        for _ in range(2, n):
            a, b = b, a + b
        return str(b)

# Create Gradio interface
demo = gr.Interface(
    fn=calculate_fibonacci,
    inputs=gr.Number(label="Position", value=10),
    outputs=gr.Text(label="Fibonacci Number"),
    title="Fibonacci Calculator",
    description="Calculate Fibonacci numbers - now as an MCP tool!"
)''',
                            language="python",
                            label="Your Code"
                        )
                    
                    with gr.Column():
                        gr.Markdown("#### 2️⃣ Launch as MCP Server")
                        gr.Code(
                            value='''# Just add mcp_server=True!
demo.launch(mcp_server=True)

# That's it! Your function is now:
# ✅ A web interface at http://localhost:7860
# ✅ An MCP server that LLMs can use
# ✅ Automatically documented with tool schemas''',
                            language="python",
                            label="Make it MCP"
                        )
                
                gr.Markdown("""
                ### 🎯 Try It Now!
                
                1. Copy the code above
                2. Save as `fibonacci_server.py`
                3. Run: `python fibonacci_server.py`
                4. Your MCP server is live!
                
                **MCP Endpoint**: `http://localhost:7860/gradio_api/mcp/sse`
                """)
                
                with gr.Row():
                    gr.Button("📋 Copy Full Example", variant="secondary")
                    gr.Button("📚 View More Templates", variant="secondary")
            
            # Tab 3: Connect & Test
            with gr.Tab("🔌 Connect & Test"):
                gr.Markdown("### Connect to MCP Servers")
                
                with gr.Row():
                    # Quick connect cards
                    with gr.Column(scale=1):
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>📁 Filesystem</h4>
                            <p>Read/write files securely</p>
                            <button class="gr-button gr-button-primary" onclick="alert('Connecting to Filesystem...')">Connect</button>
                        </div>
                        """)
                    
                    with gr.Column(scale=1):
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>🔍 Brave Search</h4>
                            <p>Search the web</p>
                            <button class="gr-button gr-button-primary" onclick="alert('Connecting to Brave Search...')">Connect</button>
                        </div>
                        """)
                    
                    with gr.Column(scale=1):
                        gr.HTML("""
                        <div class="feature-card">
                            <h4>🧠 Memory</h4>
                            <p>Persistent knowledge graph</p>
                            <button class="gr-button gr-button-primary" onclick="alert('Connecting to Memory...')">Connect</button>
                        </div>
                        """)
                
                gr.Markdown("### Test MCP Tools")
                
                with gr.Row():
                    test_server_url = gr.Textbox(
                        label="Server URL",
                        value="http://localhost:7860",
                        scale=2
                    )
                    test_btn = gr.Button("🔍 Discover Tools", variant="primary", scale=1)
                
                tools_output = gr.JSON(label="Available Tools", visible=True)
                
                # Mock data for demo
                test_btn.click(
                    lambda url: {
                        "tools": [
                            {
                                "name": "calculate_fibonacci",
                                "description": "Calculate the nth Fibonacci number",
                                "parameters": {
                                    "n": {"type": "integer", "description": "Position in sequence"}
                                }
                            }
                        ]
                    },
                    inputs=[test_server_url],
                    outputs=[tools_output]
                )
            
            # Tab 4: Gallery & Examples
            with gr.Tab("🎨 Gallery & Examples"):
                gr.Markdown("### MCP Server Gallery")
                
                examples = [
                    {
                        "title": "🧮 Calculator Server",
                        "description": "Basic math operations as MCP tools",
                        "tools": ["add", "subtract", "multiply", "divide"],
                        "code": "examples/calculator.py"
                    },
                    {
                        "title": "📊 Data Analyzer",
                        "description": "Analyze CSV files with MCP",
                        "tools": ["analyze_csv", "plot_data", "get_statistics"],
                        "code": "examples/data_analyzer.py"
                    },
                    {
                        "title": "🎨 Image Generator",
                        "description": "AI image generation via MCP",
                        "tools": ["generate_image", "edit_image", "upscale"],
                        "code": "examples/image_gen.py"
                    },
                    {
                        "title": "🌐 API Wrapper",
                        "description": "Wrap any API as MCP tools",
                        "tools": ["get_weather", "get_news", "translate"],
                        "code": "examples/api_wrapper.py"
                    }
                ]
                
                with gr.Row():
                    for example in examples[:2]:
                        with gr.Column():
                            gr.Markdown(f"""
                            ### {example['title']}
                            {example['description']}
                            
                            **Tools:** {', '.join(example['tools'])}
                            """)
                            gr.Button(f"View Code", variant="secondary")
                
                with gr.Row():
                    for example in examples[2:]:
                        with gr.Column():
                            gr.Markdown(f"""
                            ### {example['title']}
                            {example['description']}
                            
                            **Tools:** {', '.join(example['tools'])}
                            """)
                            gr.Button(f"View Code", variant="secondary")
        
        # Footer
        gr.Markdown("""
        ---
        ### 🏆 Why Gradio MCP Playground?
        
        - **🚀 Instant MCP Servers** - Add one line to any Gradio app
        - **🤖 AI-Powered** - Built-in assistant that can use all your tools
        - **🔧 No Configuration** - Automatic tool discovery and documentation
        - **🌐 Universal** - Works with Claude, Cursor, and any MCP client
        
        **[GitHub](https://github.com/yourusername/gradio-mcp-playground)** | 
        **[Documentation](https://docs.gradio-mcp.io)** | 
        **[Join Discord](https://discord.gg/gradio-mcp)**
        """)
    
    return demo


if __name__ == "__main__":
    # Create and launch the streamlined demo
    demo = create_streamlined_demo()
    demo.launch(
        server_port=8081,
        server_name="0.0.0.0",
        share=False,
        show_api=False
    )
