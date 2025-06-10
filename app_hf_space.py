# app.py - Gradio MCP Playground Demo for HF Spaces
import gradio as gr
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid
import asyncio
import time

# Demo mode flag
DEMO_MODE = True
HF_SPACE_ID = os.getenv("SPACE_ID", "demo")

class GradioMCPPlayground:
    """Streamlined demo showcasing core MCP agent capabilities"""
    
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.sessions = {}  # Session-based storage
        self.setup_demo_data()
        
    def setup_demo_data(self):
        """Initialize impressive demo content"""
        self.demo_agents = [
            {
                "id": "weather-assistant",
                "name": "Weather Assistant",
                "description": "Real-time weather information using MCP tools",
                "template": "weather",
                "status": "active",
                "tools": ["get_weather", "get_forecast"],
                "created": "2025-01-08"
            },
            {
                "id": "code-helper",
                "name": "Code Helper",
                "description": "AI pair programmer with file system access",
                "template": "filesystem",
                "status": "active",
                "tools": ["read_file", "write_file", "list_directory"],
                "created": "2025-01-09"
            },
            {
                "id": "research-agent",
                "name": "Research Agent",
                "description": "Web search and summarization",
                "template": "search",
                "status": "beta",
                "tools": ["web_search", "summarize"],
                "created": "2025-01-10"
            }
        ]
        
        self.mcp_servers = {
            "filesystem": {
                "name": "File System MCP",
                "status": "connected",
                "endpoint": "mcp://localhost:3000",
                "tools": ["read_file", "write_file", "list_directory", "create_directory", "delete_file"]
            },
            "brave-search": {
                "name": "Brave Search MCP",
                "status": "available",
                "endpoint": "mcp://localhost:3001",
                "tools": ["web_search", "image_search"]
            },
            "weather": {
                "name": "Weather API MCP",
                "status": "connected",
                "endpoint": "mcp://localhost:3002", 
                "tools": ["get_weather", "get_forecast"]
            }
        }
        
        self.chat_history = []
        
    def get_session_data(self, session_id: str) -> Dict:
        """Get or create session data"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "agents": list(self.demo_agents),
                "chat_history": [],
                "created_agents": []
            }
        return self.sessions[session_id]
    
    def create_interface(self) -> gr.Blocks:
        """Create the main Gradio interface"""
        with gr.Blocks(
            title="🛝 Gradio MCP Playground",
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="green",
            ),
            css="""
            .gradio-container {max-width: 1200px !important}
            .success-message {
                background-color: #d4edda !important;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 12px;
                border-radius: 4px;
                margin: 10px 0;
            }
            .info-box {
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 12px;
                border-radius: 4px;
                margin: 10px 0;
            }
            .tool-response {
                background-color: #f8f9fa;
                border-left: 4px solid #007bff;
                padding: 10px;
                margin: 10px 0;
                font-family: monospace;
            }
            .template-card {
                background: #374151;
                border: 2px solid #4b5563;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .template-card:hover {
                border-color: #60a5fa;
                transform: translateY(-2px);
            }
            .template-name {
                color: #f3f4f6;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .template-description {
                color: #d1d5db;
                font-size: 0.9em;
            }
            .template-tools {
                color: #9ca3af;
                font-size: 0.8em;
                margin-top: 8px;
            }
            """
        ) as demo:
            # State management
            session_id = gr.State(value=str(uuid.uuid4()))
            
            # Header
            with gr.Row():
                gr.Markdown("""
                # 🛝 Gradio MCP Playground
                ### Build AI Agents in Seconds - No Code Required!
                
                <div class="info-box">
                <b>🏆 Hugging Face MCP Hackathon Submission</b><br>
                Transform any Python function into an AI agent with visual tools and instant testing.
                <a href="https://github.com/seanpoyner/gradio-mcp-playground" target="_blank">GitHub</a> | 
                <a href="https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground" target="_blank">Documentation</a>
                </div>
                """)
            
            # Main tabs
            with gr.Tabs() as main_tabs:
                # Tab 1: AI Assistant Hub (Main Feature)
                with gr.Tab("🛝 AI Assistant", id="assistant"):
                    self.create_assistant_tab(session_id)
                
                # Tab 2: Visual Agent Builder
                with gr.Tab("🏗️ Server Builder", id="builder"):
                    self.create_builder_tab(session_id)
                
                # Tab 3: MCP Connections
                with gr.Tab("🔌 MCP Connections", id="tools"):
                    self.create_tools_tab(session_id)
                
                # Tab 4: My Agents
                with gr.Tab("📦 Server Management", id="agents"):
                    self.create_agents_tab(session_id)
                    
                # Tab 5: Help
                with gr.Tab("📚 Help & Resources", id="help"):
                    self.create_help_tab()
            
            # Footer
            gr.Markdown("""
            ---
            <center>
            Made with ❤️ using Gradio | 
            <a href="https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground/discussions" target="_blank">Feedback</a> |
            <a href="https://github.com/seanpoyner/gradio-mcp-playground" target="_blank">GitHub</a>
            </center>
            """)
            
        return demo
    
    def create_assistant_tab(self, session_id):
        """Multi-mode AI assistant interface"""
        with gr.Row():
            with gr.Column(scale=1):
                assistant_mode = gr.Radio(
                    choices=[
                        "Adam (General)",
                        "Liam (MCP Agent)",
                        "Arthur (Agent Builder)"
                    ],
                    value="Adam (General)",
                    label="Choose AI Assistant",
                    info="Each assistant specializes in different tasks"
                )
                
                gr.Markdown("""
                ### 🛠️ Available MCP Tools
                
                **Connected:**
                - 📁 **FileSystem**: Read/write files
                - 🌤️ **Weather**: Real-time weather
                - 🔍 **Search**: Web search
                
                **Available:**
                - 🖼️ Images
                - 📊 Data Analysis
                - 🗄️ Database
                """)
                
                clear_btn = gr.Button("Clear Chat", variant="secondary")
                
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    value=[
                        (None, "👋 Hi! I'm Adam, your AI assistant with MCP superpowers. I can help you build agents, test MCP tools, or answer questions. Try asking me to check the weather or create a calculator agent!")
                    ],
                    height=400,
                    avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=adam")
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Message",
                        placeholder="Try: 'What's the weather in Paris?' or 'Help me build a calculator agent'",
                        scale=4,
                        lines=1
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                # Tool execution display
                with gr.Accordion("🔧 Tool Execution Log", open=False) as tool_log:
                    tool_display = gr.Markdown("*No tools executed yet*")
                
                # Example prompts
                gr.Examples(
                    examples=[
                        "What's the weather in San Francisco?",
                        "Help me create a calculator agent",
                        "Show me available MCP tools",
                        "How do I connect a new MCP server?",
                        "Build an agent that can search the web"
                    ],
                    inputs=msg_input,
                    label="Quick Start Examples"
                )
        
        # Chat functionality
        def respond(message: str, history: List, mode: str) -> Tuple[List, str, str]:
            """Process chat messages and simulate MCP tool execution"""
            if not message.strip():
                return history, "", tool_display.value
            
            # Simulate different assistant personalities
            assistant_name = mode.split(" ")[0]
            
            # Simulate MCP tool execution for certain queries
            tool_executed = None
            
            if "weather" in message.lower():
                # Simulate weather tool execution
                location = "San Francisco"  # Extract from message in real impl
                if "paris" in message.lower():
                    location = "Paris"
                tool_executed = f"""
### 🔧 Tool Execution

**Tool:** `weather.get_current`  
**Parameters:** `{{"location": "{location}"}}`  
**Response:**
```json
{{
  "temperature": 72,
  "condition": "Sunny",
  "humidity": 65,
  "wind_speed": 12
}}
```
**Status:** ✅ Success
                """
                response = f"I've checked the weather using the MCP weather tool. In {location}, it's currently 72°F and sunny with 65% humidity and winds at 12 mph. Perfect weather for a walk! ☀️"
                
            elif "create" in message.lower() and ("agent" in message.lower() or "calculator" in message.lower()):
                response = """I'll help you create a calculator agent! Here's what I'll do:

1. **Choose a template**: I'll use the calculator template that includes basic math operations
2. **Configure the agent**: Set up addition, subtraction, multiplication, and division tools  
3. **Generate MCP server code**: Create a Python-based MCP server
4. **Test the tools**: Verify each operation works correctly

Would you like me to walk you through the visual builder, or should I generate the code directly for you?"""
            
            elif "mcp tools" in message.lower() or "available tools" in message.lower():
                response = """Here are the currently available MCP tools:

📁 **FileSystem MCP** (Connected)
- `read_file`: Read file contents
- `write_file`: Write to files
- `list_directory`: List folder contents

🌤️ **Weather MCP** (Connected)
- `get_current`: Current weather
- `get_forecast`: 5-day forecast

🔍 **Search MCP** (Available)
- `web_search`: Search the web
- `image_search`: Find images

Would you like to test any of these tools or learn how to create your own?"""
            
            else:
                # General responses based on assistant mode
                if assistant_name == "Adam":
                    response = f"Great question! As a general assistant with MCP capabilities, I can help you with {message}. Would you like me to use any specific tools or create an agent for this task?"
                elif assistant_name == "Liam":
                    response = f"As an MCP development specialist, I'll help you with {message}. I can show you how to implement this as an MCP tool or integrate it into an existing server. Which approach would you prefer?"
                else:  # Arthur
                    response = f"Let's architect a solution for {message}. I can help you design the agent structure, choose the right MCP tools, and create a scalable implementation. What's your main goal with this agent?"
            
            # Add to history
            history.append((message, response))
            
            # Update tool display
            tool_display_text = tool_executed if tool_executed else "*No tools executed*"
            
            return history, "", tool_display_text
        
        # Wire up events
        msg_input.submit(respond, [msg_input, chatbot, assistant_mode], [chatbot, msg_input, tool_display])
        send_btn.click(respond, [msg_input, chatbot, assistant_mode], [chatbot, msg_input, tool_display])
        clear_btn.click(lambda: ([(None, "Chat cleared! How can I help you?")], ""), outputs=[chatbot, msg_input])

    def create_builder_tab(self, session_id):
        """Visual agent builder interface"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🏗️ Create Your Server")
                
                agent_name = gr.Textbox(
                    label="Server Name",
                    placeholder="my-awesome-server",
                    info="Lowercase letters, numbers, and hyphens only"
                )
                
                agent_desc = gr.Textbox(
                    label="Description", 
                    placeholder="What does your server do?",
                    lines=2
                )
                
                template = gr.Dropdown(
                    choices=[
                        ("🧮 Calculator - Math operations", "calculator"),
                        ("🌤️ Weather - Weather information", "weather"),
                        ("🔍 Search - Web search", "search"),
                        ("📁 FileSystem - File operations", "filesystem"),
                        ("⚡ Custom - Start from scratch", "custom")
                    ],
                    label="Template",
                    value="calculator",
                    info="Choose a starting template"
                )
                
                with gr.Row():
                    create_btn = gr.Button("Create Server", variant="primary")
                    test_btn = gr.Button("Test Server", variant="secondary")
                
                creation_status = gr.HTML()
                
                # Templates gallery
                gr.Markdown("### 📚 Template Gallery")
                templates_html = gr.HTML(self.render_templates_gallery())
                
            with gr.Column():
                gr.Markdown("### 📝 Generated Code")
                
                code_editor = gr.Code(
                    label="MCP Server Implementation",
                    language="python",
                    value=self.get_template_code("calculator"),
                    lines=20
                )
                
                with gr.Accordion("🧪 Test Console", open=False):
                    test_input = gr.Textbox(
                        label="Test Input",
                        placeholder='{"operation": "add", "a": 5, "b": 3}'
                    )
                    test_output = gr.JSON(label="Test Output")
        
        # Template change handler
        def update_template(template_choice):
            return self.get_template_code(template_choice)
        
        template.change(update_template, template, code_editor)
        
        # Create agent handler
        def create_agent(name, desc, template_choice, session_data):
            if not name:
                return '<div class="error">Please enter a server name</div>'
            
            # Add to session agents
            new_agent = {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": desc,
                "template": template_choice,
                "status": "created",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # In demo mode, just show success
            return f'''
            <div class="success-message">
            ✅ <b>Server "{name}" created successfully!</b><br>
            Template: {template_choice}<br>
            Status: Ready to deploy<br>
            <small>Note: In production, this would be saved to your account.</small>
            </div>
            '''
        
        create_btn.click(
            create_agent,
            [agent_name, agent_desc, template, session_id],
            creation_status
        )
        
        # Test handler
        def test_agent(test_input_str):
            try:
                # Simulate test execution
                import json
                input_data = json.loads(test_input_str)
                
                # Mock response based on template
                if "operation" in input_data:
                    result = {"result": 8, "operation": "add", "status": "success"}
                else:
                    result = {"status": "success", "message": "Test completed"}
                    
                return result
            except Exception as e:
                return {"error": str(e), "status": "failed"}
        
        test_btn.click(test_agent, test_input, test_output)

    def create_tools_tab(self, session_id):
        """MCP tools and connections interface"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🔌 Quick Connect")
                
                # Quick connect buttons
                with gr.Row():
                    fs_btn = gr.Button("📁 Filesystem", variant="secondary")
                    weather_btn = gr.Button("🌤️ Weather", variant="secondary")
                    search_btn = gr.Button("🔍 Search", variant="secondary")
                
                gr.Markdown("### 🔌 Connected MCP Servers")
                
                # Server status cards
                server_html = self.render_server_cards()
                server_display = gr.HTML(server_html)
                
                # Add new server
                with gr.Accordion("➕ Add MCP Server", open=False):
                    server_url = gr.Textbox(
                        label="Server URL",
                        placeholder="mcp://localhost:3000"
                    )
                    server_name = gr.Textbox(
                        label="Server Name",
                        placeholder="My Custom Server"
                    )
                    connect_btn = gr.Button("Connect", variant="primary")
                    
                refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
                
            with gr.Column():
                gr.Markdown("### 🧪 Test MCP Tools")
                
                # Tool selector
                tool_category = gr.Dropdown(
                    choices=list(self.mcp_servers.keys()),
                    label="Select Server",
                    value="filesystem"
                )
                
                tool_name = gr.Dropdown(
                    choices=self.mcp_servers["filesystem"]["tools"],
                    label="Select Tool"
                )
                
                # Tool parameters
                tool_params = gr.JSON(
                    value={"path": "/tmp/test.txt"},
                    label="Tool Parameters",
                    lines=5
                )
                
                execute_btn = gr.Button("▶️ Execute Tool", variant="primary")
                
                # Results
                execution_result = gr.JSON(
                    label="Execution Result",
                    value={"status": "ready"}
                )
                
                # Activity log
                gr.Markdown("### 📊 Activity Log")
                activity_log = gr.Textbox(
                    value=self.get_activity_log(),
                    label="Recent Activity",
                    lines=8,
                    max_lines=10,
                    interactive=False
                )
        
        # Update tool list when server changes
        def update_tools(server):
            return gr.update(choices=self.mcp_servers.get(server, {}).get("tools", []))
        
        tool_category.change(update_tools, tool_category, tool_name)
        
        # Execute tool
        def execute_tool(server, tool, params):
            # Simulate tool execution
            result = {
                "server": server,
                "tool": tool,
                "params": params,
                "response": {
                    "status": "success",
                    "data": f"Executed {tool} successfully",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Update activity log
            new_log = f"[{datetime.now().strftime('%H:%M:%S')}] Executed {server}.{tool}\n"
            
            return result, activity_log.value + new_log
        
        execute_btn.click(
            execute_tool,
            [tool_category, tool_name, tool_params],
            [execution_result, activity_log]
        )

    def create_agents_tab(self, session_id):
        """Display user's agents"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📦 Your Servers")
                
                # Search and filter
                with gr.Row():
                    search_box = gr.Textbox(
                        label="Search",
                        placeholder="Search servers...",
                        scale=3
                    )
                    filter_status = gr.Dropdown(
                        choices=["All", "Active", "Inactive", "Beta"],
                        value="All",
                        label="Status",
                        scale=1
                    )
                
                # Agent gallery
                agent_gallery = gr.HTML(self.render_agent_gallery())
                
                # Refresh button
                refresh_agents_btn = gr.Button("🔄 Refresh", variant="secondary")
                
            with gr.Column():
                gr.Markdown("### 📊 Server Details")
                
                selected_agent = gr.JSON(
                    label="Selected Server",
                    value=self.demo_agents[0] if self.demo_agents else {}
                )
                
                with gr.Row():
                    deploy_btn = gr.Button("🚀 Deploy", variant="primary")
                    edit_btn = gr.Button("✏️ Edit", variant="secondary")
                    delete_btn = gr.Button("🗑️ Delete", variant="stop")
                
                deployment_status = gr.HTML()
        
        # Deploy handler
        def deploy_agent(agent_data):
            return f'''
            <div class="success-message">
            🚀 <b>Deployment Initiated!</b><br>
            Server: {agent_data.get('name', 'Unknown')}<br>
            Target: Hugging Face Spaces<br>
            Status: In Progress...<br>
            <small>Note: In production, this would deploy to your HF Space.</small>
            </div>
            '''
        
        deploy_btn.click(deploy_agent, selected_agent, deployment_status)
    
    def create_help_tab(self):
        """Help and resources tab"""
        gr.Markdown("""
        ## 📚 Help & Resources
        
        ### 🚀 Quick Start Guide
        
        1. **Choose an AI Assistant** - Start with Adam for general help, Liam for MCP development, or Arthur for architecture
        2. **Build Your First Agent** - Use the Server Builder tab to create an agent from templates
        3. **Connect MCP Servers** - Use the MCP Connections tab to connect to available servers
        4. **Test and Deploy** - Test your agents and deploy them to production
        
        ### 🔧 Available Templates
        
        - **Calculator** - Basic math operations (add, subtract, multiply, divide)
        - **Weather** - Get weather information for any location
        - **Search** - Web search capabilities
        - **FileSystem** - Read and write files (with safety checks)
        - **Custom** - Start from scratch with your own implementation
        
        ### 📖 Documentation
        
        - [Getting Started Guide](https://github.com/seanpoyner/gradio-mcp-playground/wiki/Getting-Started)
        - [MCP Protocol Specification](https://github.com/anthropics/mcp)
        - [Gradio Documentation](https://gradio.app/docs)
        
        ### 💡 Tips
        
        - Use the chat to ask for help building specific agents
        - Templates are fully customizable - modify the generated code as needed
        - Test your tools before deploying to ensure they work correctly
        - Join our Discord for community support and sharing
        
        ### 🐛 Known Limitations (Demo Mode)
        
        - MCP servers are simulated in this demo
        - File operations are limited to safe paths
        - API integrations require your own keys
        - Deployments are simulated (not real)
        
        ### 📞 Support
        
        - [GitHub Issues](https://github.com/seanpoyner/gradio-mcp-playground/issues)
        - [Discussions](https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground/discussions)
        - [Discord Community](#)
        """)

    def get_template_code(self, template: str) -> str:
        """Return template code for different agent types"""
        templates = {
            "calculator": '''"""
Calculator MCP Server
A simple calculator that performs basic math operations
"""
import json
from typing import Dict, Any
from mcp.server import Server, Tool

class CalculatorServer(Server):
    def __init__(self):
        super().__init__("calculator")
        self.register_tools()
    
    def register_tools(self):
        self.add_tool(Tool(
            name="calculate",
            description="Perform a calculation",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            handler=self.calculate
        ))
    
    async def calculate(self, operation: str, a: float, b: float) -> Dict[str, Any]:
        """Execute calculation based on operation"""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else None
        }
        
        if operation in operations:
            result = operations[operation](a, b)
            if result is not None:
                return {"result": result, "status": "success"}
            else:
                return {"error": "Division by zero", "status": "error"}
        
        return {"error": "Unknown operation", "status": "error"}

if __name__ == "__main__":
    server = CalculatorServer()
    server.run()
''',
            "weather": '''"""
Weather MCP Server
Provides weather information for any location
"""
import aiohttp
from mcp.server import Server, Tool

class WeatherServer(Server):
    def __init__(self):
        super().__init__("weather")
        self.api_key = "YOUR_API_KEY"  # Set via environment variable
        self.register_tools()
    
    def register_tools(self):
        self.add_tool(Tool(
            name="get_current_weather",
            description="Get current weather for a location",
            input_schema={
                "type": "object", 
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            },
            handler=self.get_weather
        ))
    
    async def get_weather(self, location: str) -> dict:
        """Fetch current weather data"""
        # Demo response
        return {
            "location": location,
            "temperature": 72,
            "condition": "Sunny",
            "humidity": 65,
            "wind_speed": 12,
            "unit": "fahrenheit"
        }

if __name__ == "__main__":
    server = WeatherServer()
    server.run()
''',
            "filesystem": '''"""
FileSystem MCP Server
Safe file operations within allowed directories
"""
import os
import json
from pathlib import Path
from mcp.server import Server, Tool

class FileSystemServer(Server):
    def __init__(self):
        super().__init__("filesystem")
        self.allowed_paths = ["/tmp", "/workspace"]
        self.register_tools()
    
    def register_tools(self):
        tools = [
            Tool(
                name="read_file",
                description="Read file contents",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"}
                    },
                    "required": ["path"]
                },
                handler=self.read_file
            ),
            Tool(
                name="write_file",
                description="Write content to file",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                },
                handler=self.write_file
            )
        ]
        
        for tool in tools:
            self.add_tool(tool)
    
    async def read_file(self, path: str) -> dict:
        """Read file with safety checks"""
        try:
            file_path = Path(path).resolve()
            
            # Safety check
            if not any(str(file_path).startswith(allowed) 
                      for allowed in self.allowed_paths):
                return {"error": "Path not allowed", "status": "error"}
            
            if file_path.exists() and file_path.is_file():
                content = file_path.read_text()
                return {"content": content, "status": "success"}
            
            return {"error": "File not found", "status": "error"}
            
        except Exception as e:
            return {"error": str(e), "status": "error"}

if __name__ == "__main__":
    server = FileSystemServer()
    server.run()
''',
            "custom": '''"""
Custom MCP Server Template
Build your own MCP server with custom tools
"""
from mcp.server import Server, Tool

class CustomServer(Server):
    def __init__(self):
        super().__init__("custom-server")
        self.register_tools()
    
    def register_tools(self):
        # Add your custom tools here
        self.add_tool(Tool(
            name="example_tool",
            description="An example tool",
            input_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            },
            handler=self.example_handler
        ))
    
    async def example_handler(self, input: str) -> dict:
        """Your tool implementation"""
        return {
            "result": f"Processed: {input}",
            "status": "success"
        }

if __name__ == "__main__":
    server = CustomServer()
    server.run()
'''
        }
        return templates.get(template, templates["custom"])
    
    def render_templates_gallery(self) -> str:
        """Render template gallery as HTML"""
        templates = [
            {"name": "Calculator", "desc": "Math operations", "tools": 4, "icon": "🧮"},
            {"name": "Weather", "desc": "Weather data", "tools": 2, "icon": "🌤️"},
            {"name": "Search", "desc": "Web search", "tools": 2, "icon": "🔍"},
            {"name": "FileSystem", "desc": "File operations", "tools": 5, "icon": "📁"},
        ]
        
        html = '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">'
        for tmpl in templates:
            html += f'''
            <div class="template-card">
                <div class="template-name">{tmpl["icon"]} {tmpl["name"]}</div>
                <div class="template-description">{tmpl["desc"]}</div>
                <div class="template-tools">{tmpl["tools"]} tools included</div>
            </div>
            '''
        html += '</div>'
        return html
    
    def render_server_cards(self) -> str:
        """Render MCP server status cards"""
        html = '<div style="display: grid; gap: 15px;">'
        
        for server_id, server_info in self.mcp_servers.items():
            status_color = "#28a745" if server_info["status"] == "connected" else "#ffc107"
            status_icon = "🟢" if server_info["status"] == "connected" else "🟡"
            
            html += f'''
            <div style="border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; background: #f8f9fa;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">{server_info["name"]}</h4>
                    <span style="color: {status_color};">{status_icon} {server_info["status"].title()}</span>
                </div>
                <p style="color: #6c757d; font-size: 14px; margin: 5px 0;">
                    {server_info["endpoint"]}
                </p>
                <div style="margin-top: 10px;">
                    <span style="background: #e9ecef; padding: 2px 8px; border-radius: 3px; font-size: 12px;">
                        {len(server_info["tools"])} tools
                    </span>
                </div>
            </div>
            '''
        
        html += '</div>'
        return html

    def render_agent_gallery(self) -> str:
        """Render agent gallery cards"""
        html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">'
        
        for agent in self.demo_agents:
            status_color = {
                "active": "#28a745",
                "inactive": "#dc3545", 
                "beta": "#ffc107"
            }.get(agent["status"], "#6c757d")
            
            html += f'''
            <div style="border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; cursor: pointer; transition: transform 0.2s; hover: transform: scale(1.02);">
                <h4 style="margin: 0 0 10px 0;">{agent["name"]}</h4>
                <p style="color: #6c757d; font-size: 14px; margin-bottom: 15px;">
                    {agent["description"]}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: {status_color}; font-size: 12px;">
                        ● {agent["status"].upper()}
                    </span>
                    <span style="font-size: 12px; color: #6c757d;">
                        {len(agent["tools"])} tools
                    </span>
                </div>
                <div style="margin-top: 10px;">
                    <small style="color: #6c757d;">Created: {agent["created"]}</small>
                </div>
                <button style="width: 100%; margin-top: 15px; padding: 8px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    View Details
                </button>
            </div>
            '''
        
        html += '</div>'
        return html

    def get_activity_log(self) -> str:
        """Generate activity log entries"""
        return """[10:00:00] System initialized
[10:00:01] Connected to filesystem MCP server
[10:00:02] Connected to weather MCP server  
[10:00:03] Tool discovery completed: 10 tools available
[10:00:05] Agent registry loaded: 3 agents
[10:00:10] Ready for connections
[10:01:23] Executed: filesystem.read_file
[10:02:45] Executed: weather.get_current
"""

# Initialize and launch
if __name__ == "__main__":
    print("🚀 Starting Gradio MCP Playground...")
    
    # Create app instance
    app = GradioMCPPlayground()
    
    # Create interface
    demo = app.create_interface()
    
    # Configure for HF Spaces
    demo.queue(max_size=20)
    
    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path="🛝"
    )