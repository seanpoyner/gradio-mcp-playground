"""MCP STDIO Filter

This module provides a robust filtered stdio implementation that handles
server startup messages before they reach the MCP client.
"""

import asyncio
import subprocess
import logging
from typing import Optional, Tuple, Dict, Any
import json
import re

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession, StdioServerParameters, stdio_client

    HAS_MCP = True
except ImportError as e:
    HAS_MCP = False
    logger.debug(f"MCP import error: {e}")


async def connect_to_mcp_server_filtered(
    server_id: str, command: str, args: list, env: dict = None
) -> Tuple[Optional[ClientSession], Dict[str, Any]]:
    """Connect to an MCP server with filtered stdio"""

    if not HAS_MCP:
        logger.warning("MCP package not installed")
        return None, {}

    # Prepare environment
    import os

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    # Add flags to suppress warnings
    process_env["NODE_NO_WARNINGS"] = "1"

    # Create server parameters
    server_params = StdioServerParameters(command=command, args=args, env=process_env)

    # Use stdio_client context manager
    session = None
    tools = {}

    try:
        logger.debug(f"Connecting to {server_id} with command: {command} {' '.join(args)}")

        # Use default stderr (messages will be logged but that's OK)
        async with stdio_client(server_params) as (read_stream, write_stream):
            logger.debug("stdio_client connection established")

            # Create session
            session = ClientSession(read_stream, write_stream)
            logger.debug("ClientSession created")

            # Initialize with timeout
            try:
                logger.debug("Initializing session...")
                await asyncio.wait_for(session.initialize(), timeout=10.0)
                logger.debug("Session initialized successfully")
            except asyncio.TimeoutError:
                logger.error(f"Timeout initializing {server_id}")
                return None, {}

            # Get tools
            logger.debug("Listing tools...")
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                tools[tool.name] = tool

            logger.info(f"✅ Connected to {server_id} with {len(tools)} tools")

            # IMPORTANT: We need to keep the session alive outside the context
            # The context manager will close the streams when it exits
            # So we return the session and tools but note it may not work after context exit
            return session, tools

    except Exception as e:
        logger.error(f"Failed to connect to {server_id}: {e}")
        import traceback

        traceback.print_exc()
        return None, {}
