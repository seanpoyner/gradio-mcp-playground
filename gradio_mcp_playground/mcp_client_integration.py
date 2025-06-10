"""MCP Client Integration for Coding Agent

This module provides integration between the coding agent and external MCP servers,
allowing the agent to communicate with servers like Obsidian, GitHub, etc.
"""

import asyncio
from contextlib import AsyncExitStack
from typing import Any, Dict, List

# Import MCP client components
try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.types import CallToolResult, Tool

    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("Warning: MCP package not installed. MCP client features will be limited.")


class MCPServerConnection:
    """Manages a connection to a single MCP server"""

    def __init__(self, server_id: str, command: str, args: List[str] = None):
        self.server_id = server_id
        self.command = command
        self.args = args or []
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self._connected = False
        self.tools = {}
        self.exit_stack = None

    async def connect(self) -> bool:
        """Connect to the MCP server"""
        if not HAS_MCP:
            return False

        try:
            # Create exit stack to manage the connection
            self.exit_stack = AsyncExitStack()

            # Create server parameters
            server_params = StdioServerParameters(command=self.command, args=self.args)

            # Create stdio connection and keep it alive
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.read_stream, self.write_stream = stdio_transport

            # Initialize session
            self.session = ClientSession(self.read_stream, self.write_stream)
            await self.session.initialize()

            # Get available tools
            tools_result = await self.session.list_tools()
            for tool in tools_result.tools:
                self.tools[tool.name] = tool

            self._connected = True
            return True

        except Exception as e:
            print(f"Failed to connect to {self.server_id}: {str(e)}")
            if self.exit_stack:
                await self.exit_stack.aclose()
                self.exit_stack = None
            return False

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the server"""
        if not self._connected or not self.session:
            raise RuntimeError(f"Not connected to {self.server_id}")

        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in {self.server_id}")

        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return f"Error calling {tool_name}: {str(e)}"

    async def disconnect(self):
        """Disconnect from the server"""
        self._connected = False
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = None
        self.session = None
        self.read_stream = None
        self.write_stream = None

    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected


class MCPClientManager:
    """Manages multiple MCP server connections for the coding agent"""

    def __init__(self):
        self.connections: Dict[str, MCPServerConnection] = {}
        self._running_servers: Dict[str, dict] = {}

    def get_running_servers(self) -> Dict[str, dict]:
        """Get info about running MCP servers from the management tool"""
        try:
            from .mcp_management_tool import get_mcp_manager

            manager = get_mcp_manager()
            if hasattr(manager, "_running_mcp_servers"):
                return manager._running_mcp_servers
        except:
            pass
        return {}

    async def connect_to_server(
        self, server_id: str, command: str = None, args: List[str] = None
    ) -> bool:
        """Connect to an MCP server"""
        # Check if we already have a connection
        if server_id in self.connections and self.connections[server_id].is_connected():
            return True

        # If no command provided, try to get it from running servers
        if not command:
            running_servers = self.get_running_servers()
            if server_id in running_servers:
                server_info = running_servers[server_id]
                command_str = server_info.get("command", "")
                parts = command_str.split()
                if parts:
                    command = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
            else:
                # Try to construct command based on server type
                if server_id == "obsidian":
                    command = "npx"
                    args = ["-y", "obsidian-mcp"] + (args or [])
                elif server_id == "filesystem":
                    command = "npx"
                    args = ["-y", "@modelcontextprotocol/server-filesystem"] + (args or [])
                elif server_id == "github":
                    command = "npx"
                    args = ["-y", "@modelcontextprotocol/server-github"]
                elif server_id == "brave-search":
                    command = "npx"
                    args = ["-y", "@modelcontextprotocol/server-brave-search"]
                else:
                    return False

        # Create connection
        connection = MCPServerConnection(server_id, command, args)

        # Connect
        if await connection.connect():
            self.connections[server_id] = connection
            return True

        return False

    async def call_server_tool(
        self, server_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on a specific server"""
        if server_id not in self.connections:
            # Try to connect first
            if not await self.connect_to_server(server_id):
                return f"Failed to connect to {server_id} server"

        connection = self.connections[server_id]
        return await connection.call_tool(tool_name, arguments)

    async def get_server_tools(self, server_id: str) -> Dict[str, Any]:
        """Get available tools from a server"""
        if server_id not in self.connections:
            if not await self.connect_to_server(server_id):
                return {}

        connection = self.connections[server_id]
        return connection.tools

    async def disconnect_from_server(self, server_id: str):
        """Disconnect from a server"""
        if server_id in self.connections:
            await self.connections[server_id].disconnect()
            del self.connections[server_id]

    async def disconnect_all(self):
        """Disconnect from all servers"""
        for server_id in list(self.connections.keys()):
            await self.disconnect_from_server(server_id)


# Singleton instance
_mcp_client_manager = None


def get_mcp_client_manager() -> MCPClientManager:
    """Get the global MCP client manager instance"""
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager


def create_mcp_tool_wrapper(server_id: str, tool_name: str, tool_description: str = None):
    """Create a synchronous wrapper for an MCP tool that can be used by LlamaIndex"""

    def tool_wrapper(**kwargs) -> str:
        """Wrapper function that handles async MCP tool calls"""
        try:
            # Get the client manager
            manager = get_mcp_client_manager()

            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, create a task
                future = asyncio.create_task(manager.call_server_tool(server_id, tool_name, kwargs))
                # Use nest_asyncio if available to handle nested loops
                try:
                    import nest_asyncio

                    nest_asyncio.apply()
                    result = loop.run_until_complete(future)
                except ImportError:
                    # Fall back to sync_to_async approach
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(
                            asyncio.run, manager.call_server_tool(server_id, tool_name, kwargs)
                        ).result()
            except RuntimeError:
                # No event loop running, we can create one
                result = asyncio.run(manager.call_server_tool(server_id, tool_name, kwargs))

            # Format the result
            if isinstance(result, CallToolResult):
                # Extract the content from the MCP result
                if hasattr(result, "content"):
                    if isinstance(result.content, list):
                        # Handle multiple content items
                        output = []
                        for item in result.content:
                            if hasattr(item, "text"):
                                output.append(item.text)
                            elif hasattr(item, "type") and item.type == "text":
                                output.append(str(item))
                            else:
                                output.append(str(item))
                        return "\n".join(output)
                    else:
                        return str(result.content)
                else:
                    return str(result)
            else:
                return str(result)

        except Exception as e:
            return f"Error calling {tool_name} on {server_id}: {str(e)}"

    # Set function metadata
    tool_wrapper.__name__ = f"{server_id}_{tool_name}"
    tool_wrapper.__doc__ = tool_description or f"Call {tool_name} tool from {server_id} MCP server"

    return tool_wrapper
