"""MCP Connections Panel

UI component for managing multiple MCP client connections to external servers
like memory, sequential-thinking, file system, etc.
"""

import gradio as gr
import asyncio
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging

# Import the connection manager from parent project
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from gradio_mcp_playground.client_manager import MCPConnectionManager, GradioMCPClient
except ImportError:
    MCPConnectionManager = None
    GradioMCPClient = None

logger = logging.getLogger(__name__)


class MCPConnectionsPanel:
    """Panel for managing multiple MCP server connections"""
    
    def __init__(self, agent=None):
        self.agent = agent
        self.connection_manager = MCPConnectionManager() if MCPConnectionManager else None
        self.active_connections = {}
        
        # Predefined MCP server configurations
        self.predefined_servers = {
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
                "url": "python -m mcp_server_filesystem /",
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
        
    def create_interface(self) -> None:
        """Create the MCP connections panel interface"""
        
        with gr.Column():
            gr.Markdown("## 🔌 MCP Server Connections")
            gr.Markdown("Connect to multiple MCP servers for enhanced capabilities")
            
            with gr.Tabs():
                # Quick Connect Tab
                with gr.Tab("⚡ Quick Connect"):
                    self._create_quick_connect_interface()
                
                # Active Connections Tab
                with gr.Tab("🔗 Active Connections"):
                    self._create_active_connections_interface()
                
                # Custom Connection Tab
                with gr.Tab("➕ Custom Connection"):
                    self._create_custom_connection_interface()
                
                # Connection Logs Tab
                with gr.Tab("📋 Connection Logs"):
                    self._create_logs_interface()
    
    def _create_quick_connect_interface(self) -> None:
        """Create quick connect interface for predefined servers"""
        
        gr.Markdown("### 🚀 Quick Connect to Common MCP Servers")
        
        # Create cards for each predefined server
        with gr.Row():
            for server_id, server_info in list(self.predefined_servers.items())[:3]:
                with gr.Column():
                    with gr.Group():
                        gr.Markdown(f"### {server_info['icon']} {server_info['name']}")
                        gr.Markdown(server_info['description'])
                        
                        # Connection status
                        status_box = gr.Textbox(
                            label="Status",
                            value="Not Connected",
                            interactive=False,
                            elem_id=f"status_{server_id}"
                        )
                        
                        # Connect button
                        connect_btn = gr.Button(
                            f"Connect to {server_info['name']}",
                            variant="primary",
                            elem_id=f"connect_{server_id}"
                        )
                        
                        # Set up click handler
                        connect_btn.click(
                            fn=lambda sid=server_id: self._quick_connect(sid),
                            outputs=[status_box]
                        )
        
        with gr.Row():
            for server_id, server_info in list(self.predefined_servers.items())[3:]:
                with gr.Column():
                    with gr.Group():
                        gr.Markdown(f"### {server_info['icon']} {server_info['name']}")
                        gr.Markdown(server_info['description'])
                        
                        # Connection status
                        status_box = gr.Textbox(
                            label="Status",
                            value="Not Connected",
                            interactive=False,
                            elem_id=f"status_{server_id}"
                        )
                        
                        # Connect button
                        connect_btn = gr.Button(
                            f"Connect to {server_info['name']}",
                            variant="primary",
                            elem_id=f"connect_{server_id}"
                        )
                        
                        # Set up click handler
                        connect_btn.click(
                            fn=lambda sid=server_id: self._quick_connect(sid),
                            outputs=[status_box]
                        )
        
        # Bulk actions
        with gr.Row():
            self.connect_all_btn = gr.Button("🔗 Connect All", variant="primary")
            self.disconnect_all_btn = gr.Button("🔌 Disconnect All", variant="stop")
            self.refresh_status_btn = gr.Button("🔄 Refresh Status")
        
        self.bulk_status = gr.Textbox(
            label="Bulk Action Status",
            interactive=False,
            lines=3
        )
        
        # Set up bulk action handlers
        self._setup_quick_connect_handlers()
    
    def _create_active_connections_interface(self) -> None:
        """Create interface for managing active connections"""
        
        gr.Markdown("### 📊 Active MCP Server Connections")
        
        # Connection list
        self.connections_table = gr.Dataframe(
            headers=["Server", "Type", "Status", "Tools", "URL"],
            datatype=["str", "str", "str", "number", "str"],
            interactive=False,
            value=self._get_connections_data()
        )
        
        # Selected connection details
        with gr.Row():
            with gr.Column(scale=2):
                self.selected_connection = gr.Dropdown(
                    label="Select Connection",
                    choices=self._get_connection_choices(),
                    interactive=True
                )
                
                # Connection details
                self.connection_details = gr.JSON(
                    label="Connection Details",
                    value={}
                )
                
                # Available tools
                self.available_tools = gr.Dataframe(
                    headers=["Tool Name", "Description", "Parameters"],
                    datatype=["str", "str", "str"],
                    interactive=False,
                    label="Available Tools"
                )
            
            with gr.Column(scale=1):
                # Connection actions
                gr.Markdown("### Actions")
                
                self.test_connection_btn = gr.Button("🧪 Test Connection")
                self.disconnect_btn = gr.Button("🔌 Disconnect", variant="stop")
                self.reconnect_btn = gr.Button("🔄 Reconnect")
                
                # Tool testing
                gr.Markdown("### Tool Testing")
                
                self.tool_name = gr.Dropdown(
                    label="Select Tool",
                    choices=[],
                    interactive=True
                )
                
                self.tool_args = gr.JSON(
                    label="Tool Arguments",
                    value={},
                    interactive=True
                )
                
                self.call_tool_btn = gr.Button("📞 Call Tool", variant="primary")
                
                self.tool_result = gr.JSON(
                    label="Tool Result",
                    value={}
                )
        
        # Set up active connections handlers
        self._setup_active_connections_handlers()
    
    def _create_custom_connection_interface(self) -> None:
        """Create interface for custom MCP server connections"""
        
        gr.Markdown("### 🔧 Connect to Custom MCP Server")
        
        with gr.Row():
            with gr.Column():
                self.custom_name = gr.Textbox(
                    label="Connection Name",
                    placeholder="my-custom-server",
                    value=""
                )
                
                self.custom_url = gr.Textbox(
                    label="Server URL/Command",
                    placeholder="python -m my_mcp_server or http://localhost:8080/mcp",
                    value="",
                    lines=2
                )
                
                self.custom_protocol = gr.Radio(
                    label="Protocol",
                    choices=["auto", "stdio", "sse", "gradio"],
                    value="auto"
                )
                
                self.custom_description = gr.Textbox(
                    label="Description (optional)",
                    placeholder="What does this server do?",
                    value="",
                    lines=2
                )
                
                self.custom_connect_btn = gr.Button("🔗 Connect", variant="primary")
            
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
        
        self.custom_status = gr.Textbox(
            label="Connection Status",
            interactive=False,
            lines=3
        )
        
        # Recent custom connections
        gr.Markdown("### 📌 Recent Custom Connections")
        
        self.recent_connections = gr.Dataframe(
            headers=["Name", "URL", "Protocol", "Last Used"],
            datatype=["str", "str", "str", "str"],
            interactive=True,
            value=self._get_recent_connections()
        )
        
        # Set up custom connection handlers
        self._setup_custom_connection_handlers()
    
    def _create_logs_interface(self) -> None:
        """Create interface for connection logs"""
        
        gr.Markdown("### 📋 Connection Logs")
        
        with gr.Row():
            self.log_level = gr.Radio(
                label="Log Level",
                choices=["All", "Error", "Warning", "Info", "Debug"],
                value="All",
                interactive=True
            )
            
            self.clear_logs_btn = gr.Button("🧹 Clear Logs")
            self.export_logs_btn = gr.Button("📤 Export Logs")
        
        self.connection_logs = gr.Textbox(
            label="Connection Logs",
            lines=15,
            max_lines=30,
            interactive=False,
            value="Connection logs will appear here...",
            show_copy_button=True
        )
        
        # Auto-refresh logs
        self.log_timer = gr.Timer(2.0)
        self.log_timer.tick(
            fn=self._update_logs,
            outputs=[self.connection_logs]
        )
    
    def _setup_quick_connect_handlers(self) -> None:
        """Set up event handlers for quick connect interface"""
        
        self.connect_all_btn.click(
            fn=self._connect_all_predefined,
            outputs=[self.bulk_status]
        )
        
        self.disconnect_all_btn.click(
            fn=self._disconnect_all,
            outputs=[self.bulk_status]
        )
        
        self.refresh_status_btn.click(
            fn=self._refresh_all_status,
            outputs=[self.bulk_status]
        )
    
    def _setup_active_connections_handlers(self) -> None:
        """Set up event handlers for active connections interface"""
        
        # Connection selection
        self.selected_connection.change(
            fn=self._load_connection_details,
            inputs=[self.selected_connection],
            outputs=[self.connection_details, self.available_tools, self.tool_name]
        )
        
        # Connection actions
        self.test_connection_btn.click(
            fn=self._test_connection,
            inputs=[self.selected_connection],
            outputs=[self.connection_details]
        )
        
        self.disconnect_btn.click(
            fn=self._disconnect_connection,
            inputs=[self.selected_connection],
            outputs=[self.connections_table, self.selected_connection]
        )
        
        self.reconnect_btn.click(
            fn=self._reconnect_connection,
            inputs=[self.selected_connection],
            outputs=[self.connection_details]
        )
        
        # Tool testing
        self.call_tool_btn.click(
            fn=self._call_tool,
            inputs=[self.selected_connection, self.tool_name, self.tool_args],
            outputs=[self.tool_result]
        )
    
    def _setup_custom_connection_handlers(self) -> None:
        """Set up event handlers for custom connection interface"""
        
        self.custom_connect_btn.click(
            fn=self._connect_custom,
            inputs=[self.custom_name, self.custom_url, self.custom_protocol, self.custom_description],
            outputs=[self.custom_status, self.recent_connections]
        )
    
    def _quick_connect(self, server_id: str) -> str:
        """Quick connect to a predefined server"""
        
        if not self.connection_manager:
            return "❌ Connection manager not available"
        
        server_info = self.predefined_servers.get(server_id)
        if not server_info:
            return "❌ Unknown server"
        
        try:
            # Check if already connected
            existing = self.connection_manager.get_connection(server_id)
            if existing and existing.mcp_client and existing.mcp_client.is_connected:
                return f"✅ Already connected to {server_info['name']}"
            
            # Connect to server
            self.connection_manager.add_connection(
                name=server_id,
                server_url=server_info['url'],
                protocol=server_info['protocol'],
                auto_connect=True
            )
            
            # Get connection info
            client = self.connection_manager.get_connection(server_id)
            if client:
                tools = client.list_tools()
                return f"✅ Connected to {server_info['name']} ({len(tools)} tools available)"
            else:
                return f"❌ Failed to establish connection to {server_info['name']}"
            
        except Exception as e:
            logger.error(f"Error connecting to {server_id}: {e}")
            return f"❌ Error: {str(e)}"
    
    def _connect_all_predefined(self) -> str:
        """Connect to all predefined servers"""
        
        if not self.connection_manager:
            return "❌ Connection manager not available"
        
        results = []
        success_count = 0
        
        for server_id, server_info in self.predefined_servers.items():
            result = self._quick_connect(server_id)
            if "✅" in result:
                success_count += 1
            results.append(f"{server_info['icon']} {server_info['name']}: {result}")
        
        summary = f"Connected to {success_count}/{len(self.predefined_servers)} servers\n\n"
        return summary + "\n".join(results)
    
    def _disconnect_all(self) -> str:
        """Disconnect all connections"""
        
        if not self.connection_manager:
            return "❌ Connection manager not available"
        
        try:
            count = len(self.connection_manager.connections)
            self.connection_manager.disconnect_all()
            return f"✅ Disconnected {count} servers"
        except Exception as e:
            return f"❌ Error disconnecting: {str(e)}"
    
    def _refresh_all_status(self) -> str:
        """Refresh status of all connections"""
        
        if not self.connection_manager:
            return "❌ Connection manager not available"
        
        try:
            connections = self.connection_manager.list_connections()
            status_lines = []
            
            for conn in connections:
                status = "🟢 Connected" if conn['connected'] else "🔴 Disconnected"
                status_lines.append(f"{conn['name']}: {status}")
            
            return "\n".join(status_lines) if status_lines else "No connections found"
        except Exception as e:
            return f"❌ Error refreshing status: {str(e)}"
    
    def _get_connections_data(self) -> List[List[Any]]:
        """Get connections data for the table"""
        
        if not self.connection_manager:
            return []
        
        data = []
        for name, client in self.connection_manager.connections.items():
            if client.mcp_client and client.mcp_client.is_connected:
                tools = client.list_tools()
                server_info = self.predefined_servers.get(name, {})
                
                data.append([
                    f"{server_info.get('icon', '🔌')} {server_info.get('name', name)}",
                    client.server_info.get('type', 'mcp'),
                    "🟢 Connected",
                    len(tools),
                    server_info.get('url', 'custom')
                ])
        
        return data
    
    def _get_connection_choices(self) -> List[str]:
        """Get list of connection names for dropdown"""
        
        if not self.connection_manager:
            return []
        
        return list(self.connection_manager.connections.keys())
    
    def _load_connection_details(self, connection_name: str) -> Tuple[Dict, List[List[str]], List[str]]:
        """Load details for a selected connection"""
        
        if not self.connection_manager or not connection_name:
            return {}, [], []
        
        client = self.connection_manager.get_connection(connection_name)
        if not client:
            return {"error": "Connection not found"}, [], []
        
        # Get connection details
        details = {
            "name": connection_name,
            "type": client.server_info.get('type', 'unknown'),
            "connected": client.mcp_client.is_connected if client.mcp_client else False
        }
        
        # Get tools
        tools_data = []
        tool_names = []
        
        if client.mcp_client and client.mcp_client.is_connected:
            tools = client.list_tools()
            for tool in tools:
                tools_data.append([
                    tool.get('name', 'unknown'),
                    tool.get('description', 'No description'),
                    json.dumps(tool.get('parameters', {}), indent=2)
                ])
                tool_names.append(tool.get('name', 'unknown'))
        
        return details, tools_data, tool_names
    
    def _test_connection(self, connection_name: str) -> Dict[str, Any]:
        """Test a connection"""
        
        if not self.connection_manager or not connection_name:
            return {"error": "Invalid connection"}
        
        client = self.connection_manager.get_connection(connection_name)
        if not client:
            return {"error": "Connection not found"}
        
        try:
            tools = client.list_tools()
            return {
                "status": "connected",
                "tools_count": len(tools),
                "server_type": client.server_info.get('type', 'unknown')
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _disconnect_connection(self, connection_name: str) -> Tuple[List[List[Any]], List[str]]:
        """Disconnect a specific connection"""
        
        if not self.connection_manager or not connection_name:
            return self._get_connections_data(), self._get_connection_choices()
        
        try:
            self.connection_manager.remove_connection(connection_name)
        except Exception as e:
            logger.error(f"Error disconnecting {connection_name}: {e}")
        
        return self._get_connections_data(), self._get_connection_choices()
    
    def _reconnect_connection(self, connection_name: str) -> Dict[str, Any]:
        """Reconnect to a server"""
        
        if not self.connection_manager or not connection_name:
            return {"error": "Invalid connection"}
        
        try:
            # Get saved connection info
            saved_info = self.connection_manager.saved_connections.get(connection_name)
            if not saved_info:
                return {"error": "Connection info not found"}
            
            # Disconnect if connected
            if connection_name in self.connection_manager.connections:
                self.connection_manager.connections[connection_name].disconnect()
            
            # Reconnect
            client = self.connection_manager.connections[connection_name]
            client.connect(saved_info['url'], saved_info['protocol'])
            
            return {"status": "reconnected", "message": f"Successfully reconnected to {connection_name}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _call_tool(self, connection_name: str, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a connection"""
        
        if not self.connection_manager or not connection_name or not tool_name:
            return {"error": "Invalid parameters"}
        
        client = self.connection_manager.get_connection(connection_name)
        if not client:
            return {"error": "Connection not found"}
        
        try:
            result = client.call_tool(tool_name, tool_args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _connect_custom(self, name: str, url: str, protocol: str, description: str) -> Tuple[str, List[List[str]]]:
        """Connect to a custom MCP server"""
        
        if not self.connection_manager:
            return "❌ Connection manager not available", self._get_recent_connections()
        
        if not name or not url:
            return "❌ Please provide both name and URL", self._get_recent_connections()
        
        try:
            # Add connection
            self.connection_manager.add_connection(
                name=name,
                server_url=url,
                protocol=protocol,
                auto_connect=True
            )
            
            # Save to recent connections
            self._save_recent_connection(name, url, protocol)
            
            # Get connection info
            client = self.connection_manager.get_connection(name)
            if client and client.mcp_client and client.mcp_client.is_connected:
                tools = client.list_tools()
                return f"✅ Connected to {name} ({len(tools)} tools available)", self._get_recent_connections()
            else:
                return f"❌ Failed to connect to {name}", self._get_recent_connections()
            
        except Exception as e:
            return f"❌ Error: {str(e)}", self._get_recent_connections()
    
    def _get_recent_connections(self) -> List[List[str]]:
        """Get recent custom connections"""
        
        # This would load from a persistent storage
        # For now, return empty list
        return []
    
    def _save_recent_connection(self, name: str, url: str, protocol: str) -> None:
        """Save a recent connection"""
        
        # This would save to persistent storage
        pass
    
    def _update_logs(self) -> str:
        """Update connection logs"""
        
        # This would show real connection logs
        # For now, return placeholder
        return "Connection logs will appear here..."
    
    def get_active_connections(self) -> Dict[str, Any]:
        """Get all active connections for use by the agent"""
        
        if not self.connection_manager:
            return {}
        
        active = {}
        for name, client in self.connection_manager.connections.items():
            if client.mcp_client and client.mcp_client.is_connected:
                active[name] = {
                    "client": client,
                    "tools": client.list_tools(),
                    "info": self.predefined_servers.get(name, {"name": name})
                }
        
        return active