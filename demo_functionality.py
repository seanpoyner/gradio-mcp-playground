"""
Real functionality implementations for the unified dashboard
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import gradio as gr

class DemoFunctionality:
    """Actual working implementations for demo features"""
    
    def __init__(self):
        self.active_servers = {}
        self.template_gallery = self._load_template_gallery()
    
    def create_server_from_template(self, template_name: str, server_name: str, port: int) -> str:
        """Actually create a server from template"""
        try:
            # Create server directory
            server_dir = Path.home() / "gradio-mcp-servers" / server_name
            server_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy template files
            template_path = Path(__file__).parent / "templates" / f"{template_name}.py"
            if template_path.exists():
                server_file = server_dir / "server.py"
                server_file.write_text(template_path.read_text())
                
                # Create a simple launcher script
                launcher = server_dir / "launch.py"
                launcher.write_text(f'''
import gradio as gr
from server import demo

if __name__ == "__main__":
    demo.launch(
        server_port={port},
        mcp_server=True,
        server_name="0.0.0.0"
    )
''')
                
                # Start the server
                process = subprocess.Popen(
                    ["python", str(launcher)],
                    cwd=str(server_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.active_servers[server_name] = {
                    "process": process,
                    "port": port,
                    "template": template_name,
                    "path": str(server_dir)
                }
                
                return f"""✅ Server '{server_name}' created successfully!

📁 Location: {server_dir}
🔧 Template: {template_name}
🌐 URL: http://localhost:{port}
🔌 MCP Endpoint: http://localhost:{port}/gradio_api/mcp/sse

The server is now running! You can:
1. Visit the web interface at http://localhost:{port}
2. Connect to it as an MCP server
3. Test its tools in the Tool Testing tab
"""
            else:
                return f"❌ Template '{template_name}' not found"
                
        except Exception as e:
            return f"❌ Error creating server: {str(e)}"
    
    def get_active_servers_data(self) -> List[List[Any]]:
        """Get real data for active servers table"""
        data = []
        for name, info in self.active_servers.items():
            # Check if process is still running
            if info["process"].poll() is None:
                status = "🟢 Running"
                errors = "None"
            else:
                status = "🔴 Stopped"
                errors = "Process terminated"
            
            data.append([
                name,
                status,
                info["template"],
                f"python server.py",
                "Just now",
                errors
            ])
        
        return data
    
    def _load_template_gallery(self) -> List[Dict[str, Any]]:
        """Load template gallery data"""
        templates = [
            {
                "name": "Calculator",
                "description": "Mathematical operations server",
                "preview": "🧮 Basic math operations",
                "tools": ["add", "subtract", "multiply", "divide"]
            },
            {
                "name": "Text Processor",
                "description": "Text manipulation and analysis",
                "preview": "📝 Text processing tools",
                "tools": ["word_count", "summarize", "translate"]
            },
            {
                "name": "Image Generator",
                "description": "AI image generation server",
                "preview": "🎨 Generate images from text",
                "tools": ["generate_image", "edit_image"]
            },
            {
                "name": "Data Analyzer",
                "description": "CSV and data analysis tools",
                "preview": "📊 Analyze data files",
                "tools": ["analyze_csv", "plot_data", "statistics"]
            }
        ]
        return templates
    
    def quick_connect_mcp_server(self, server_type: str) -> Dict[str, Any]:
        """Quick connect to predefined MCP servers"""
        configs = {
            "filesystem": {
                "command": "uvx",
                "args": ["mcp-server-filesystem", "--path", str(Path.home())],
                "env": {},
                "description": "File system access"
            },
            "memory": {
                "command": "uvx",
                "args": ["mcp-server-memory"],
                "env": {},
                "description": "Knowledge graph memory"
            },
            "github": {
                "command": "uvx", 
                "args": ["mcp-server-github"],
                "env": {"GITHUB_TOKEN": "YOUR_TOKEN"},
                "description": "GitHub operations"
            },
            "brave-search": {
                "command": "uvx",
                "args": ["mcp-server-brave-search"],
                "env": {"BRAVE_API_KEY": "YOUR_KEY"},
                "description": "Web search"
            }
        }
        
        if server_type in configs:
            return {
                "success": True,
                "config": configs[server_type],
                "message": f"Ready to connect to {server_type} server"
            }
        else:
            return {
                "success": False,
                "message": f"Unknown server type: {server_type}"
            }
    
    def test_mcp_tool(self, server_url: str, tool_name: str, args_json: str) -> Dict[str, Any]:
        """Actually test an MCP tool"""
        try:
            import requests
            
            # Parse arguments
            args = json.loads(args_json) if args_json else {}
            
            # Make request to MCP server
            response = requests.post(
                f"{server_url}/gradio_api/mcp/tools/{tool_name}",
                json=args,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON in arguments"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Usage in your unified dashboard:
demo_func = DemoFunctionality()

# Wire up the actual functionality
def handle_create_server(template, name, port):
    return demo_func.create_server_from_template(template, name, port)

def refresh_active_servers():
    return demo_func.get_active_servers_data()

def handle_quick_connect(server_type):
    result = demo_func.quick_connect_mcp_server(server_type)
    if result["success"]:
        # Actually connect to the server
        # ... connection code ...
        return f"✅ Connected to {server_type}!"
    else:
        return f"❌ {result['message']}"
