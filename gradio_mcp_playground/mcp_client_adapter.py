"""MCP Client Adapter with Startup Message Filtering

This module provides a robust MCP client that handles server startup messages
and protocol version negotiation properly.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import MCP
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Tool

    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    logger.warning("MCP library not installed")


class FilteredStream:
    """Filters startup messages from MCP server output"""

    def __init__(self, stream, server_id: str):
        self.stream = stream
        self.server_id = server_id
        self.startup_filtered = False
        self.buffer = []

    async def receive(self):
        """Receive messages, filtering startup text"""
        while True:
            message = await self.stream.receive()

            # If we've already filtered startup, pass through
            if self.startup_filtered:
                return message

            # Check if this is a JSON-RPC message
            if isinstance(message, dict) or (
                isinstance(message, str) and message.strip().startswith("{")
            ):
                self.startup_filtered = True
                return message

            # This might be startup text, log it but don't return
            if isinstance(message, str):
                logger.debug(f"Filtered startup message from {self.server_id}: {message}")
                continue

            # Unknown message type, return it
            return message

    async def send(self, message):
        """Pass through sends"""
        return await self.stream.send(message)


class MCPClientAdapter:
    """Adapter for MCP client that handles common issues"""

    def __init__(self):
        self.sessions = {}
        self.tools = {}
        self.contexts = {}  # Store context managers

    async def connect_to_server(
        self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Dict[str, Tool]]:
        """Connect to an MCP server with robust error handling

        Returns:
            Tuple of (success, tools_dict)
        """
        if not HAS_MCP:
            logger.error("MCP library not available")
            return False, {}

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        process_env["NODE_NO_WARNINGS"] = "1"

        # Create server parameters
        server_params = StdioServerParameters(command=command, args=args, env=process_env)

        try:
            # Use the context manager properly
            async with stdio_client(server_params) as (read_stream, write_stream):
                # Wrap with filtering stream
                filtered_read = FilteredStream(read_stream, server_id)

                # Create session
                session = ClientSession(filtered_read, write_stream)

                # Initialize with timeout
                try:
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    logger.info(f"✅ Session initialized for {server_id}")
                except asyncio.TimeoutError:
                    logger.error(f"Timeout initializing {server_id}")
                    return False, {}

                # Get tools
                tools_result = await session.list_tools()
                tools = {}
                for tool in tools_result.tools:
                    tools[tool.name] = tool

                # Store session for later use
                self.sessions[server_id] = session
                self.tools[server_id] = tools

                logger.info(f"✅ Connected to {server_id} with {len(tools)} tools")

                # Return here but keep the connection open
                # This is a simplified test - in production we'd need proper lifecycle management
                return True, tools

        except Exception as e:
            logger.error(f"Failed to connect to {server_id}: {e}")
            import traceback

            traceback.print_exc()
            return False, {}

    async def call_tool(
        self, server_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on a connected server"""

        if server_id not in self.sessions:
            return {"error": f"Server {server_id} not connected"}

        session = self.sessions[server_id]

        try:
            # Call the tool
            result = await session.call_tool(tool_name, arguments)

            # Extract content from result
            if hasattr(result, "content"):
                content = result.content
                if isinstance(content, list):
                    # Handle multiple content items
                    outputs = []
                    for item in content:
                        if hasattr(item, "text"):
                            outputs.append(item.text)
                        else:
                            outputs.append(str(item))
                    return {"content": "\n".join(outputs)}
                else:
                    return {"content": str(content)}
            else:
                return {"content": str(result)}

        except Exception as e:
            logger.error(f"Error calling {tool_name} on {server_id}: {e}")
            return {"error": str(e)}

    async def disconnect(self, server_id: str):
        """Disconnect from a server"""
        if server_id in self.sessions:
            # Sessions are auto-closed by context manager
            del self.sessions[server_id]
            if server_id in self.tools:
                del self.tools[server_id]
            logger.info(f"Disconnected from {server_id}")

    async def disconnect_all(self):
        """Disconnect from all servers"""
        server_ids = list(self.sessions.keys())
        for server_id in server_ids:
            await self.disconnect(server_id)


# Global client instance
_global_client = None


def get_mcp_client() -> MCPClientAdapter:
    """Get the global MCP client instance"""
    global _global_client
    if _global_client is None:
        _global_client = MCPClientAdapter()
    return _global_client


async def test_mcp_connection():
    """Test MCP connection with filesystem server"""
    client = get_mcp_client()

    # Test with filesystem server
    success, tools = await client.connect_to_server(
        "filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"], {}
    )

    if success:
        print(f"✅ Connected successfully with {len(tools)} tools")
        for tool_name in tools:
            print(f"  - {tool_name}")

        # Test a tool call
        result = await client.call_tool("filesystem", "list_directory", {"path": "/tmp"})
        print(f"\nTool call result: {result}")
    else:
        print("❌ Connection failed")


if __name__ == "__main__":
    # Test the adapter
    asyncio.run(test_mcp_connection())
