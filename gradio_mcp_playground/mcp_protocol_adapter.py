"""MCP Protocol Adapter

This module provides protocol version adaptation between client and servers.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class ProtocolAdapter:
    """Adapts protocol versions between MCP client and servers"""

    def __init__(
        self, read_stream, write_stream, client_version="2025-03-26", server_version="2024-11-05"
    ):
        self.read_stream = read_stream
        self.write_stream = write_stream
        self.client_version = client_version
        self.server_version = server_version
        self._initialized = False

    async def receive(self):
        """Receive and adapt messages from server"""
        message = await self.read_stream.receive()

        # Adapt protocol version in responses
        if isinstance(message, dict):
            # Check if this is an initialize response
            if "result" in message and isinstance(message["result"], dict):
                if "protocolVersion" in message["result"]:
                    logger.debug(
                        f"Adapting protocol version from {message['result']['protocolVersion']} to {self.client_version}"
                    )
                    message["result"]["protocolVersion"] = self.client_version
                    self._initialized = True

        return message

    async def send(self, message):
        """Send and adapt messages to server"""
        # Adapt protocol version in requests
        if isinstance(message, dict):
            # Check if this is an initialize request
            if message.get("method") == "initialize" and "params" in message:
                if "protocolVersion" in message["params"]:
                    logger.debug(
                        f"Adapting protocol version from {message['params']['protocolVersion']} to {self.server_version}"
                    )
                    message["params"]["protocolVersion"] = self.server_version

        await self.write_stream.send(message)


async def create_adapted_session(server_id: str, command: str, args: list, env: dict = None):
    """Create an MCP session with protocol adaptation"""

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        logger.error("MCP not installed")
        return None, {}

    # Prepare environment
    import os

    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    process_env["NODE_NO_WARNINGS"] = "1"

    # Create server parameters
    server_params = StdioServerParameters(command=command, args=args, env=process_env)

    try:
        # Connect to server
        async with stdio_client(server_params) as (read_stream, write_stream):
            # Wrap streams with protocol adapter
            adapted_read = ProtocolAdapter(read_stream, write_stream)
            adapted_write = adapted_read  # Same adapter handles both

            # Create session with adapted streams
            session = ClientSession(adapted_read, adapted_write)

            # Initialize
            await asyncio.wait_for(session.initialize(), timeout=10.0)
            logger.info(f"Session initialized for {server_id}")

            # Get tools
            tools_result = await session.list_tools()
            tools = {}
            for tool in tools_result.tools:
                tools[tool.name] = tool

            logger.info(f"✅ Connected to {server_id} with {len(tools)} tools")
            return session, tools

    except Exception as e:
        logger.error(f"Failed to connect to {server_id}: {e}")
        import traceback

        traceback.print_exc()
        return None, {}
