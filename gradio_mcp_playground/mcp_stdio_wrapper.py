"""MCP STDIO Wrapper

This module provides a wrapper around MCP servers that handle their startup messages.
"""

import asyncio
import logging
from typing import Optional, Tuple, Dict, Any, List
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    HAS_MCP = True
except ImportError as e:
    HAS_MCP = False
    logger.debug(f"MCP import error: {e}")


class MCPServerManager:
    """Manages MCP server connections with proper lifecycle management"""

    def __init__(self):
        self._sessions: Dict[str, ClientSession] = {}
        self._contexts: Dict[str, Any] = {}

    async def connect_server(
        self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Connect to an MCP server and store the session"""

        if not HAS_MCP:
            logger.warning("MCP package not installed")
            return False, {}

        # Prepare environment
        import os

        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Add flags to suppress warnings
        process_env["NODE_NO_WARNINGS"] = "1"

        # Create server parameters
        server_params = StdioServerParameters(command=command, args=args, env=process_env)

        try:
            logger.debug(f"Starting {server_id} with: {command} {' '.join(args)}")

            # Create the context
            ctx = stdio_client(server_params)
            read_stream, write_stream = await ctx.__aenter__()

            # Store context for cleanup
            self._contexts[server_id] = ctx

            # Create session
            session = ClientSession(read_stream, write_stream)

            # Initialize with timeout
            try:
                await asyncio.wait_for(session.initialize(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.error(f"Timeout initializing {server_id}")
                await self._cleanup_server(server_id)
                return False, {}

            # Get tools
            tools_result = await session.list_tools()
            tools = {}
            for tool in tools_result.tools:
                tools[tool.name] = tool

            # Store session
            self._sessions[server_id] = session

            logger.info(f"✅ Connected to {server_id} with {len(tools)} tools")
            return True, tools

        except Exception as e:
            logger.error(f"Failed to connect to {server_id}: {e}")
            import traceback

            traceback.print_exc()
            await self._cleanup_server(server_id)
            return False, {}

    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a connected server"""
        session = self._sessions.get(server_id)
        if not session:
            return f"Error: {server_id} not connected"

        try:
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            return f"Error calling {tool_name}: {str(e)}"

    async def _cleanup_server(self, server_id: str):
        """Clean up a server connection"""
        if server_id in self._contexts:
            try:
                await self._contexts[server_id].__aexit__(None, None, None)
            except:
                pass
            del self._contexts[server_id]

        if server_id in self._sessions:
            del self._sessions[server_id]

    async def cleanup_all(self):
        """Clean up all server connections"""
        for server_id in list(self._contexts.keys()):
            await self._cleanup_server(server_id)


# Global manager instance
_manager = MCPServerManager()


async def get_mcp_manager() -> MCPServerManager:
    """Get the global MCP server manager"""
    return _manager
