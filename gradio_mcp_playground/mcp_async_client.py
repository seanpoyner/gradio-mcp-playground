"""Async MCP Client Implementation

This module provides an async MCP client that properly handles server connections
and the MCP library's async context requirements.
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


class AsyncMCPClient:
    """Async MCP client that manages persistent connections"""

    def __init__(self):
        self.connections = {}  # server_id -> connection info
        self._running = False
        self._tasks = []

    async def start(self):
        """Start the async client"""
        self._running = True
        logger.info("AsyncMCPClient started")

    async def stop(self):
        """Stop the async client and close all connections"""
        self._running = False

        # Close all connections
        for server_id in list(self.connections.keys()):
            await self.disconnect_server(server_id)

        # Cancel any running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        logger.info("AsyncMCPClient stopped")

    async def connect_server(
        self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, List[str]]:
        """Connect to an MCP server

        Returns:
            Tuple of (success, list of tool names)
        """
        if not HAS_MCP:
            return False, []

        if server_id in self.connections:
            logger.warning(f"Server {server_id} already connected")
            return False, []

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        process_env["NODE_NO_WARNINGS"] = "1"

        # Create connection task
        task = asyncio.create_task(self._maintain_connection(server_id, command, args, process_env))
        self._tasks.append(task)

        # Wait for connection to be established
        await asyncio.sleep(2.0)

        # Check if connection was successful
        if server_id in self.connections and self.connections[server_id].get("tools"):
            tool_names = list(self.connections[server_id]["tools"].keys())
            return True, tool_names
        else:
            return False, []

    async def _maintain_connection(
        self, server_id: str, command: str, args: List[str], env: Dict[str, str]
    ):
        """Maintain a connection to an MCP server"""
        server_params = StdioServerParameters(command=command, args=args, env=env)

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                # Filter startup messages
                startup_complete = False
                while not startup_complete:
                    try:
                        # Try to read with a short timeout
                        read_task = asyncio.create_task(read_stream.receive())
                        await asyncio.wait_for(read_task, timeout=0.5)
                        msg = read_task.result()

                        # Check if this is JSON-RPC
                        if isinstance(msg, dict) or (
                            isinstance(msg, str) and msg.strip().startswith("{")
                        ):
                            # Put it back for the session
                            startup_complete = True
                            # Can't put back, so we'll handle differently
                        else:
                            # Log startup message
                            logger.debug(f"Startup message from {server_id}: {msg}")
                    except asyncio.TimeoutError:
                        # No more startup messages
                        startup_complete = True

                # Create session
                session = ClientSession(read_stream, write_stream)

                # Initialize
                await session.initialize()
                logger.info(f"✅ Session initialized for {server_id}")

                # Get tools
                tools_result = await session.list_tools()
                tools = {}
                for tool in tools_result.tools:
                    tools[tool.name] = tool

                # Store connection info
                self.connections[server_id] = {
                    "session": session,
                    "tools": tools,
                    "read_stream": read_stream,
                    "write_stream": write_stream,
                }

                logger.info(f"✅ Connected to {server_id} with {len(tools)} tools")

                # Keep connection alive
                while self._running and server_id in self.connections:
                    await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Error maintaining connection to {server_id}: {e}")
            import traceback

            traceback.print_exc()
        finally:
            # Clean up connection
            if server_id in self.connections:
                del self.connections[server_id]

    async def call_tool(
        self, server_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on a connected server"""
        if server_id not in self.connections:
            return {"error": f"Server {server_id} not connected"}

        session = self.connections[server_id]["session"]

        try:
            result = await session.call_tool(tool_name, arguments)

            # Extract content
            if hasattr(result, "content"):
                content = result.content
                if isinstance(content, list):
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

    async def disconnect_server(self, server_id: str):
        """Disconnect from a server"""
        if server_id in self.connections:
            # Connection will be closed when the maintain task ends
            del self.connections[server_id]
            logger.info(f"Disconnected from {server_id}")


async def test_async_client():
    """Test the async MCP client"""
    client = AsyncMCPClient()
    await client.start()

    try:
        # Connect to filesystem server
        success, tools = await client.connect_server(
            "filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"], {}
        )

        if success:
            print(f"✅ Connected with tools: {tools}")

            # Test a tool
            result = await client.call_tool("filesystem", "list_directory", {"path": "/tmp"})
            print(f"Tool result: {result}")
        else:
            print("❌ Connection failed")

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(test_async_client())
