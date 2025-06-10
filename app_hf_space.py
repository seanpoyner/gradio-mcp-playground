# app.py - Gradio MCP Playground for HF Spaces
import gradio as gr
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import uuid
import asyncio
import time
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

# Configuration
HF_SPACE_MODE = True
HF_SPACE_ID = os.getenv("SPACE_ID", "Agents-MCP-Hackathon/gradio-mcp-playground")

class MCPPlaygroundApp:
    """Gradio MCP Playground - Functional demo for HF Spaces"""
    
    def __init__(self):
        self.sessions = {}
        self.templates = self.load_templates()
        self.active_servers = {}
        
    def load_templates(self) -> List[Dict]:
        """Load available MCP server templates"""
        return [
            {
                "name": "Calculator",
                "id": "calculator",
                "description": "Basic arithmetic operations server",
                "code": '''import json
import sys

class CalculatorServer:
    def handle_add(self, a, b):
        return {"result": a + b}
    
    def handle_subtract(self, a, b):
        return {"result": a - b}
    
    def handle_multiply(self, a, b):
        return {"result": a * b}
    
    def handle_divide(self, a, b):
        if b == 0:
            return {"error": "Division by zero"}
        return {"result": a / b}

# Simple stdin/stdout handler
server = CalculatorServer()
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        request = json.loads(line)
        
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "add":
            result = server.handle_add(params.get("a", 0), params.get("b", 0))
        elif method == "subtract":
            result = server.handle_subtract(params.get("a", 0), params.get("b", 0))
        elif method == "multiply":
            result = server.handle_multiply(params.get("a", 0), params.get("b", 0))
        elif method == "divide":
            result = server.handle_divide(params.get("a", 0), params.get("b", 1))
        else:
            result = {"error": f"Unknown method: {method}"}
        
        response = {"id": request.get("id"), "result": result}
        print(json.dumps(response))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.stdout.flush()
'''
            },
            {
                "name": "Text Processor",
                "id": "text_processor",
                "description": "Text manipulation and analysis",
                "code": '''import json
import sys

class TextProcessor:
    def count_words(self, text):
        return {"count": len(text.split())}
    
    def reverse_text(self, text):
        return {"reversed": text[::-1]}
    
    def to_uppercase(self, text):
        return {"uppercase": text.upper()}
    
    def to_lowercase(self, text):
        return {"lowercase": text.lower()}

# Simple stdin/stdout handler
processor = TextProcessor()
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        request = json.loads(line)
        
        method = request.get("method", "")
        params = request.get("params", {})
        text = params.get("text", "")
        
        if method == "count_words":
            result = processor.count_words(text)
        elif method == "reverse":
            result = processor.reverse_text(text)
        elif method == "uppercase":
            result = processor.to_uppercase(text)
        elif method == "lowercase":
            result = processor.to_lowercase(text)
        else:
            result = {"error": f"Unknown method: {method}"}
        
        response = {"id": request.get("id"), "result": result}
        print(json.dumps(response))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.stdout.flush()
'''
            },
            {
                "name": "Echo Server",
                "id": "echo",
                "description": "Simple echo server for testing",
                "code": '''import json
import sys
import datetime

# Simple echo server
while True:
    try:
        line = sys.stdin.readline()
        if not line:
            break
        request = json.loads(line)
        
        response = {
            "id": request.get("id"),
            "result": {
                "echo": request,
                "timestamp": datetime.datetime.now().isoformat(),
                "server": "echo-server-v1"
            }
        }
        print(json.dumps(response))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.stdout.flush()
'''
            }
        ]
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        with gr.Blocks(
            title="🛝 Gradio MCP Playground",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="gray",
                font=["Inter", "system-ui", "sans-serif"]
            ),
            css=self.get_custom_css()
        ) as demo:
            # Header with GitHub banner
            gr.HTML("""
            <div class="github-banner">
                <a href="https://github.com/seanpoyner/gradio-mcp-playground" target="_blank">
                    📦 For full functionality, install from GitHub - Free & Open Source!
                </a>
            </div>
            """)
            
            gr.Markdown("""
            # 🛝 Gradio MCP Playground
            
            **Open-source access to MCP tools without expensive LLM subscriptions**
            
            Build, test, and deploy Model Context Protocol (MCP) servers directly in your browser.
            This demo showcases the core features - install locally for full functionality.
            """)
            
            # Session state
            session_id = gr.State(value=lambda: str(uuid.uuid4()))
            
            with gr.Tabs() as main_tabs:
                # Tab 1: AI Assistant
                with gr.Tab("🛝 AI Assistant"):
                    gr.Markdown("### Choose Your AI Assistant")
                    
                    assistant_mode = gr.Radio(
                        choices=["General Assistant", "MCP Development", "Agent Builder"],
                        value="General Assistant",
                        label="Select Mode"
                    )
                    
                    # General Assistant Mode
                    with gr.Group(visible=True) as general_assistant_group:
                        gr.Markdown("### Adam - General Assistant [DEMO]")
                        gr.Markdown(
                            "In the full version, Adam has access to all connected MCP tools and can help with any task. "
                            "This demo shows a simulated conversation."
                        )
                        
                        # Demo chat interface
                        demo_chatbot = gr.Chatbot(
                            label="Chat with Adam [DEMO]",
                            height=500,
                            value=[
                                [None, "👋 Hello! I'm Adam, your general-purpose assistant. In the full version, I have access to MCP tools like screenshot capture, web search, file operations, and more!"],
                                ["Can you take a screenshot of a website?", None],
                                [None, "In the full version, I would use the MCP screenshot tool to capture any website. This demo version doesn't have live MCP connections, but you can see how it would work in the full GitHub version!"]
                            ]
                        )
                        
                        with gr.Row():
                            demo_input = gr.Textbox(
                                label="Message [DEMO]",
                                placeholder="This is a demo - messages won't be processed. Get the full version on GitHub!",
                                scale=4
                            )
                            demo_send_btn = gr.Button("Send [DEMO]", variant="primary", scale=1)
                    
                    # MCP Agent Mode
                    with gr.Group(visible=False) as mcp_agent_group:
                        gr.Markdown("### Liam - MCP Development Specialist [DEMO]")
                        gr.Markdown(
                            "In the full version, Liam helps with MCP server development, best practices, and troubleshooting."
                        )
                        
                        mcp_demo_chatbot = gr.Chatbot(
                            label="Chat with Liam [DEMO]",
                            height=500,
                            value=[
                                [None, "🏗️ Hello! I'm Liam, specialized in MCP pipeline creation. Let me show you what I can do in the full version!"],
                                ["I need a pipeline for web scraping and analysis.", None],
                                [None, "Great choice! Here's what I would build for you:\n\n1. **Web Scraper MCP** → Extract data from websites\n2. **Data Processor MCP** → Clean and structure the data\n3. **Analysis MCP** → Generate insights and reports\n\nEach component would be a separate MCP server that communicates through the pipeline. Install the full version to build this!"]
                            ]
                        )
                    
                    # Agent Builder Mode
                    with gr.Group(visible=False) as agent_builder_group:
                        gr.Markdown("### Arthur - Agent Builder [DEMO]")
                        gr.Markdown(
                            "In the full version, Arthur helps create custom Gradio agents using system prompts from top AI assistants."
                        )
                        
                        agent_demo_chatbot = gr.Chatbot(
                            label="Agent Builder Assistant [DEMO]",
                            height=500,
                            value=[
                                [None, "🧙‍♂️ Greetings! I'm Arthur, your advanced MCP developer. In the full version, I can create sophisticated autonomous agents!"],
                                ["Can you build a Twitter monitoring agent?", None],
                                [None, "Absolutely! Here's the architecture I'd create:\n\n```python\n# Twitter Monitor Agent\nclass TwitterAgent:\n    tools = [\n        'twitter_stream',\n        'sentiment_analysis',\n        'alert_system',\n        'data_storage'\n    ]\n```\n\nThis agent would:\n✓ Monitor keywords in real-time\n✓ Analyze sentiment and trends\n✓ Send alerts on important events\n✓ Store data for analysis\n\nGet the full version to build this!"]
                            ]
                        )
                    
                    # Add event handler for assistant mode switching
                    def switch_assistant_mode(mode):
                        return (
                            gr.update(visible=mode == "General Assistant"),
                            gr.update(visible=mode == "MCP Development"),
                            gr.update(visible=mode == "Agent Builder")
                        )
                    
                    assistant_mode.change(
                        switch_assistant_mode,
                        inputs=[assistant_mode],
                        outputs=[general_assistant_group, mcp_agent_group, agent_builder_group]
                    )
                
                # Tab 2: Server Builder
                with gr.Tab("🔧 Server Builder"):
                    gr.Markdown("### Build MCP Servers")
                    
                    with gr.Tabs():
                        # Quick Create Tab
                        with gr.Tab("Quick Create"):
                            gr.Markdown("#### Create from Templates")
                            
                            with gr.Row():
                                template_select = gr.Dropdown(
                                    choices=[t["name"] for t in self.templates],
                                    label="Select Template",
                                    value="Calculator"
                                )
                                create_btn = gr.Button("Create Server", variant="primary")
                            
                            template_code = gr.Code(
                                value=self.templates[0]["code"],
                                language="python",
                                label="Template Code"
                            )
                            
                            creation_result = gr.JSON(label="Creation Result")
                        
                        # Pipeline Builder Tab
                        with gr.Tab("Pipeline Builder [DEMO]"):
                            gr.Markdown("""
                            #### Visual Pipeline Builder
                            
                            In the full version, you can:
                            - Drag and drop MCP servers to create pipelines
                            - Connect servers with data flow arrows
                            - Configure server parameters visually
                            - Test pipelines in real-time
                            - Export pipeline configurations
                            
                            **[Install from GitHub for this feature]**
                            """)
                            
                            # Demo pipeline visualization
                            gr.HTML("""
                            <div style="border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 8px;">
                                <p style="color: #666;">🔗 Web Scraper → 📊 Data Processor → 📈 Analyzer → 📧 Report Generator</p>
                                <p style="color: #999; font-size: 14px;">Visual pipeline builder available in full version</p>
                            </div>
                            """)
                        
                        # Templates Gallery Tab
                        with gr.Tab("Templates Gallery"):
                            gr.Markdown("#### Available Templates")
                            
                            for template in self.templates:
                                with gr.Box():
                                    gr.Markdown(f"**{template['name']}**")
                                    gr.Markdown(f"*{template['description']}*")
                                    gr.Code(
                                        value=template['code'][:200] + "...",
                                        language="python",
                                        label="Preview"
                                    )
                
                # Tab 3: Server Management
                with gr.Tab("🖥️ Server Management"):
                    with gr.Tabs():
                        with gr.Tab("Active Servers"):
                            gr.Markdown("### Running MCP Servers")
                            
                            server_list = gr.JSON(
                                value={"servers": [], "message": "No active servers"},
                                label="Server Status"
                            )
                            
                            with gr.Row():
                                refresh_servers_btn = gr.Button("🔄 Refresh", scale=1)
                                stop_all_btn = gr.Button("⏹️ Stop All [DEMO]", scale=1)
                        
                        with gr.Tab("Browse Registry [DEMO]"):
                            gr.Markdown("""
                            ### MCP Server Registry
                            
                            In the full version, browse and install community servers:
                            - 🔍 Search thousands of MCP servers
                            - ⭐ Filter by ratings and popularity
                            - 📦 One-click installation
                            - 🔒 Security verification
                            """)
                
                # Tab 4: Agent Control Panel
                with gr.Tab("🤖 Agent Control Panel [DEMO]"):
                    gr.Markdown("""
                    ### Agent Management Dashboard
                    
                    The full version includes:
                    - **Agent Creation Wizard** - Step-by-step agent building
                    - **Agent Templates** - Pre-built agent architectures
                    - **Performance Monitoring** - Real-time agent metrics
                    - **Agent Marketplace** - Share and discover agents
                    
                    **[Get the full version on GitHub]**
                    """)
                
                # Tab 5: MCP Connections
                with gr.Tab("🔌 MCP Connections"):
                    with gr.Tabs():
                        with gr.Tab("Quick Connect"):
                            gr.Markdown("### Connect to Popular MCP Servers")
                            
                            with gr.Row():
                                with gr.Column():
                                    server_type = gr.Dropdown(
                                        choices=["Filesystem", "Memory", "GitHub", "Brave Search"],
                                        label="Server Type",
                                        value="Filesystem"
                                    )
                                    
                                    connect_params = gr.JSON(
                                        value={"path": "/home/user"},
                                        label="Connection Parameters"
                                    )
                                    
                                    connect_btn = gr.Button("🔗 Connect [DEMO]", variant="primary")
                                
                                with gr.Column():
                                    connection_status = gr.JSON(
                                        value={"status": "Not connected"},
                                        label="Connection Status"
                                    )
                        
                        with gr.Tab("Active Connections [DEMO]"):
                            gr.Markdown("### Currently Connected Servers")
                            gr.JSON(
                                value={"connections": [], "message": "No active connections in demo"},
                                label="Active Connections"
                            )
                        
                        with gr.Tab("Custom Connection [DEMO]"):
                            gr.Markdown("""
                            ### Connect to Custom MCP Server
                            
                            In the full version:
                            - Connect via stdio or SSE
                            - Custom authentication
                            - Advanced configuration
                            """)
                
                # Tab 6: Help & Resources
                with gr.Tab("📚 Help & Resources"):
                    with gr.Tabs():
                        with gr.Tab("Getting Started"):
                            gr.Markdown("""
                            ### Welcome to Gradio MCP Playground!
                            
                            This demo showcases what's possible with the full version.
                            
                            **To get started with full features:**
                            
                            1. **Install from GitHub:**
                            ```bash
                            git clone https://github.com/seanpoyner/gradio-mcp-playground
                            cd gradio-mcp-playground
                            pip install -e ".[all]"
                            ```
                            
                            2. **Launch the dashboard:**
                            ```bash
                            gmp dashboard
                            ```
                            
                            3. **Create your first server:**
                            ```bash
                            gmp create calculator my-calc-server
                            ```
                            """)
                        
                        with gr.Tab("Features Overview"):
                            gr.Markdown("""
                            ### What You Can Do
                            
                            **In This Demo:**
                            - ✅ Explore the interface
                            - ✅ View server templates
                            - ✅ Test calculator functionality
                            - ✅ See AI assistant examples
                            
                            **In Full Version:**
                            - ✅ Create real MCP servers
                            - ✅ Connect to any MCP server
                            - ✅ Build complex pipelines
                            - ✅ Deploy to production
                            - ✅ Use AI assistants with real tools
                            - ✅ Access CLI tools
                            - ✅ Much more!
                            """)
                        
                        with gr.Tab("About"):
                            gr.Markdown(f"""
                            ### About Gradio MCP Playground
                            
                            **Our Mission:** Democratize access to MCP technology by providing free, open-source tools
                            that don't require expensive LLM subscriptions.
                            
                            **Created by:**
                            - Sean Poyner - Project Lead
                            - Ranadeep Laskar ([@flickinshots](https://github.com/flickinshots)) - Project Member & Collaborator
                            
                            **Version:** 1.0.0
                            **License:** MIT
                            **Space ID:** {HF_SPACE_ID}
                            
                            **Links:**
                            - [GitHub Repository](https://github.com/seanpoyner/gradio-mcp-playground)
                            - [Documentation](https://github.com/seanpoyner/gradio-mcp-playground)
                            - [Report Issues](https://github.com/seanpoyner/gradio-mcp-playground/issues)
                            """)
            
            # Event handlers for templates
            template_select.change(
                self.update_template_view,
                inputs=[template_select],
                outputs=[template_code]
            )
            
            create_btn.click(
                self.create_server,
                inputs=[template_select, session_id],
                outputs=[creation_result]
            )
            
            refresh_servers_btn.click(
                self.refresh_status,
                inputs=[session_id],
                outputs=[server_list]
            )
            
            # Demo button handlers
            demo_send_btn.click(
                lambda: gr.Info("This is a demo - install the full version from GitHub for real chat functionality!"),
                inputs=[],
                outputs=[]
            )
            
            connect_btn.click(
                lambda: {"status": "Demo mode - install full version to connect to real MCP servers"},
                inputs=[],
                outputs=[connection_status]
            )
            
            stop_all_btn.click(
                lambda: gr.Info("This is a demo feature - install full version from GitHub!"),
                inputs=[],
                outputs=[]
            )
            
        return demo
    
    def get_custom_css(self) -> str:
        """Custom CSS for the interface"""
        return """
        .gradio-container {
            max-width: 1200px !important;
        }
        
        /* GitHub Banner */
        .github-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 12px;
            text-align: center;
            margin-bottom: 20px;
            border-radius: 8px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        .github-banner a {
            color: white !important;
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
        }
        
        .github-banner:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        @keyframes pulse {
            0% { opacity: 0.9; }
            50% { opacity: 1; }
            100% { opacity: 0.9; }
        }
        
        /* Dark mode friendly styles */
        .template-card {
            background: #374151;
            border: 2px solid #4b5563;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            transition: all 0.3s ease;
        }
        
        .template-card:hover {
            border-color: #60a5fa;
            transform: translateY(-2px);
        }
        
        /* Demo labels */
        button:has-text("[DEMO]") {
            opacity: 0.8;
        }
        
        /* Make JSON components more readable */
        .block.json-block {
            font-family: 'Monaco', 'Consolas', monospace;
        }
        """
    
    def update_template_view(self, template_name: str) -> str:
        """Update template code view"""
        template = next((t for t in self.templates if t["name"] == template_name), None)
        return template["code"] if template else ""
    
    def create_server(self, template_name: str, session_id: str) -> Dict:
        """Create a demo server"""
        # Initialize session
        if session_id not in self.sessions:
            self.sessions[session_id] = {"servers": []}
        
        # Add server to session
        server_info = {
            "name": f"{template_name.lower()}-{int(time.time())}",
            "template": template_name,
            "status": "active",
            "created": datetime.now().isoformat()
        }
        
        self.sessions[session_id]["servers"].append(server_info)
        
        return {
            "success": True,
            "message": f"Server created from {template_name} template",
            "server": server_info,
            "note": "This is a demo - install full version for real server creation"
        }
    
    def refresh_status(self, session_id: str) -> Dict:
        """Refresh server status"""
        session = self.sessions.get(session_id, {})
        servers = session.get("servers", [])
        
        return {
            "servers": servers,
            "count": len(servers),
            "message": f"{len(servers)} active server(s)" if servers else "No active servers",
            "timestamp": datetime.now().isoformat()
        }

# Create and launch the app
print("🚀 Starting Gradio MCP Playground...")
app = MCPPlaygroundApp()
demo = app.create_interface()

# Launch with API disabled to avoid schema errors
if __name__ == "__main__":
    demo.queue(api_open=False).launch(
        server_name="0.0.0.0",
        server_port=7860,
        favicon_path="🛝",
        show_api=False
    )