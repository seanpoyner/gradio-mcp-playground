"""Gradio MCP Client Manager

Manages MCP client connections to Gradio servers.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import aiohttp
from gradio_client import Client as GradioClient


class MCPClient:
    """Base MCP client implementation"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self._connected = False
        
    async def connect_stdio(self, command: str, args: List[str] = None) -> None:
        """Connect to an MCP server via stdio"""
        self.exit_stack = AsyncExitStack()
        
        server_params = StdioServerParameters(
            command=command,
            args=args or []
        )
        
        # Connect to server
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        # Initialize client session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio_transport[0], stdio_transport[1])
        )
        
        # Initialize
        await self.session.initialize()
        self._connected = True
        
    async def connect_sse(self, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """Connect to an MCP server via SSE"""
        self.exit_stack = AsyncExitStack()
        
        # Create SSE transport
        sse_transport = await self.exit_stack.enter_async_context(
            sse_client(url, headers)
        )
        
        # Initialize client session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(sse_transport[0], sse_transport[1])
        )
        
        # Initialize
        await self.session.initialize()
        self._connected = True
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the connected server"""
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to a server")
        
        result = await self.session.list_tools()
        return [tool.model_dump() for tool in result.tools]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the connected server"""
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to a server")
        
        result = await self.session.call_tool(name, arguments)
        return result
    
    async def disconnect(self) -> None:
        """Disconnect from the server"""
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = None
        
        self.session = None
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected


class GradioMCPClient:
    """Enhanced MCP client for Gradio servers"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.gradio_client: Optional[GradioClient] = None
        self.server_info: Dict[str, Any] = {}
        
    def connect(self, server_url: str, protocol: str = "auto") -> None:
        """Connect to a Gradio MCP server"""
        # Determine protocol
        if protocol == "auto":
            protocol = self._detect_protocol(server_url)
        
        # Connect via appropriate protocol
        if protocol == "stdio":
            # Parse stdio connection string
            parts = server_url.split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Run async connection
            asyncio.run(self.mcp_client.connect_stdio(command, args))
            
        elif protocol == "sse":
            # Connect via SSE
            asyncio.run(self.mcp_client.connect_sse(server_url))
            
        else:
            # Try Gradio client connection
            self.gradio_client = GradioClient(server_url)
        
        # Get server info
        self._fetch_server_info()
    
    def _detect_protocol(self, server_url: str) -> str:
        """Detect the appropriate protocol for a server URL"""
        if server_url.startswith("http"):
            # Check if it's an MCP SSE endpoint
            if "/sse" in server_url or "/mcp" in server_url:
                return "sse"
            else:
                return "gradio"
        else:
            # Assume stdio for non-URL connections
            return "stdio"
    
    def _fetch_server_info(self) -> None:
        """Fetch information about the connected server"""
        if self.mcp_client.is_connected:
            # Get MCP server info
            tools = asyncio.run(self.mcp_client.list_tools())
            self.server_info = {
                "type": "mcp",
                "tools": tools
            }
        elif self.gradio_client:
            # Get Gradio server info
            self.server_info = {
                "type": "gradio",
                "api_info": self.gradio_client.view_api()
            }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools/functions"""
        if self.server_info.get("type") == "mcp":
            return self.server_info.get("tools", [])
        elif self.server_info.get("type") == "gradio":
            # Convert Gradio API info to tool format
            api_info = self.server_info.get("api_info", {})
            tools = []
            
            for endpoint in api_info.get("named_endpoints", {}).values():
                tools.append({
                    "name": endpoint.get("api_name", "unknown"),
                    "description": endpoint.get("description", "No description"),
                    "parameters": endpoint.get("parameters", [])
                })
            
            return tools
        
        return []
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool/function on the server"""
        if self.server_info.get("type") == "mcp":
            return asyncio.run(self.mcp_client.call_tool(name, arguments))
        elif self.server_info.get("type") == "gradio" and self.gradio_client:
            # Call Gradio endpoint
            result = self.gradio_client.predict(
                api_name=f"/{name}",
                **arguments
            )
            return result
        
        raise RuntimeError("No connection available")
    
    def disconnect(self) -> None:
        """Disconnect from the server"""
        if self.mcp_client.is_connected:
            asyncio.run(self.mcp_client.disconnect())
        
        self.gradio_client = None
        self.server_info = {}
    
    @staticmethod
    def test_connection(server_url: str, protocol: str = "auto") -> Dict[str, Any]:
        """Test connection to a server"""
        client = GradioMCPClient()
        
        try:
            client.connect(server_url, protocol)
            tools = client.list_tools()
            
            result = {
                "success": True,
                "server_type": client.server_info.get("type"),
                "tools_count": len(tools),
                "tools": tools
            }
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        
        finally:
            client.disconnect()
        
        return result


class MCPConnectionManager:
    """Manages multiple MCP client connections"""
    
    def __init__(self):
        self.connections: Dict[str, GradioMCPClient] = {}
        self.config_path = Path.home() / ".gradio-mcp" / "connections.json"
        self._load_saved_connections()
    
    def _load_saved_connections(self) -> None:
        """Load saved connections from config file"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                saved = json.load(f)
            
            # Don't auto-connect, just load the configuration
            self.saved_connections = saved.get("connections", {})
        else:
            self.saved_connections = {}
    
    def add_connection(
        self,
        name: str,
        server_url: str,
        protocol: str = "auto",
        auto_connect: bool = True
    ) -> None:
        """Add a new connection"""
        if name in self.connections:
            raise ValueError(f"Connection '{name}' already exists")
        
        client = GradioMCPClient()
        
        if auto_connect:
            client.connect(server_url, protocol)
        
        self.connections[name] = client
        
        # Save connection info
        self.saved_connections[name] = {
            "url": server_url,
            "protocol": protocol
        }
        self._save_connections()
    
    def remove_connection(self, name: str) -> None:
        """Remove a connection"""
        if name in self.connections:
            self.connections[name].disconnect()
            del self.connections[name]
        
        if name in self.saved_connections:
            del self.saved_connections[name]
            self._save_connections()
    
    def get_connection(self, name: str) -> Optional[GradioMCPClient]:
        """Get a connection by name"""
        return self.connections.get(name)
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """List all connections"""
        connections = []
        
        for name, config in self.saved_connections.items():
            connection_info = {
                "name": name,
                "url": config["url"],
                "protocol": config["protocol"],
                "connected": name in self.connections and self.connections[name].mcp_client.is_connected
            }
            connections.append(connection_info)
        
        return connections
    
    def _save_connections(self) -> None:
        """Save connections to config file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, "w") as f:
            json.dump(
                {"connections": self.saved_connections},
                f,
                indent=2
            )
    
    def connect_all(self) -> Dict[str, bool]:
        """Connect to all saved connections"""
        results = {}
        
        for name, config in self.saved_connections.items():
            if name not in self.connections:
                try:
                    self.add_connection(
                        name,
                        config["url"],
                        config["protocol"],
                        auto_connect=True
                    )
                    results[name] = True
                except Exception:
                    results[name] = False
        
        return results
    
    def disconnect_all(self) -> None:
        """Disconnect all connections"""
        for client in self.connections.values():
            client.disconnect()
        
        self.connections.clear()
