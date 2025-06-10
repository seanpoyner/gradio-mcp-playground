"""MCP Process Manager

This module manages MCP server processes separately from the MCP client connections.
It ensures servers are started cleanly before attempting to connect.
"""

import asyncio
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import mcp.types as types
    from mcp import ClientSession, StdioServerParameters, stdio_client

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

try:
    from llama_index.core.tools import FunctionTool

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


class MCPServerProcess:
    """Manages a single MCP server process"""

    def __init__(
        self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ):
        self.server_id = server_id
        self.command = command
        self.args = args
        self.env = env
        self.process = None
        self.tools = {}

    def start(self) -> bool:
        """Start the server process"""
        try:
            # Prepare environment
            process_env = os.environ.copy()
            if self.env:
                process_env.update(self.env)

            # Start with stderr redirected to devnull to suppress status messages
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Suppress status messages
                env=process_env,
            )

            # Give server time to start
            time.sleep(2)

            # Check if still running
            if self.process.poll() is None:
                logger.info(f"Started {self.server_id} server (PID: {self.process.pid})")
                return True
            else:
                logger.error(f"Server {self.server_id} exited immediately")
                return False

        except Exception as e:
            logger.error(f"Failed to start {self.server_id}: {e}")
            return False

    def stop(self):
        """Stop the server process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None

    async def get_tools(self) -> Dict[str, Any]:
        """Connect to the running server and get its tools"""
        if not self.process or self.process.poll() is not None:
            logger.error(f"Server {self.server_id} not running")
            return {}

        try:
            # Create a new connection to the existing process
            # We'll use the process's stdin/stdout directly
            session = ClientSession(self.process.stdout, self.process.stdin)
            await session.initialize()

            # Get tools
            tools_result = await session.list_tools()

            tools = {}
            for tool in tools_result.tools:
                tools[tool.name] = tool

            # Store session for later use
            self._session = session
            self.tools = tools

            return tools

        except Exception as e:
            logger.error(f"Failed to get tools from {self.server_id}: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def create_llamaindex_tools(self) -> List[Any]:
        """Create LlamaIndex tools for this server"""
        if not HAS_LLAMAINDEX or not self.tools:
            return []

        tools = []

        for tool_name, tool_info in self.tools.items():
            # Create wrapper that calls the tool via subprocess
            def make_wrapper(sid, tname, proc):
                def wrapper(**kwargs):
                    """Call MCP tool via subprocess communication"""
                    # This is a simplified version - in production you'd want proper JSONRPC
                    try:
                        # For now, return a placeholder
                        return f"Called {tname} on {sid} with args: {kwargs}"
                    except Exception as e:
                        return f"Error calling {tname}: {str(e)}"

                wrapper.__name__ = f"{sid}_{tname}"
                wrapper.__doc__ = (
                    tool_info.description if hasattr(tool_info, "description") else f"Call {tname}"
                )
                return wrapper

            tool_fn = make_wrapper(self.server_id, tool_name, self.process)

            llamaindex_tool = FunctionTool.from_defaults(
                fn=tool_fn, name=f"{self.server_id}_{tool_name}"
            )
            tools.append(llamaindex_tool)

        return tools


def load_servers_simple() -> List[Any]:
    """Simple server loading that avoids the async complexity"""
    from .mcp_server_config import MCPServerConfig

    if not HAS_MCP:
        logger.warning("MCP not installed")
        return []

    config = MCPServerConfig()
    servers = config.list_servers()

    all_tools = []

    for server_name, server_config in servers.items():
        logger.info(f"Starting {server_name}...")

        command = server_config.get("command", "")
        args = server_config.get("args", [])
        env = server_config.get("env", {})

        # Create and start server
        server = MCPServerProcess(server_name, command, args, env)

        if server.start():
            # Get tools asynchronously
            try:
                loop = asyncio.new_event_loop()
                tools_dict = loop.run_until_complete(server.get_tools())
                loop.close()

                if tools_dict:
                    logger.info(f"✅ Got {len(tools_dict)} tools from {server_name}")

                    # Create LlamaIndex tools
                    llamaindex_tools = server.create_llamaindex_tools()
                    all_tools.extend(llamaindex_tools)
                else:
                    logger.warning(f"No tools from {server_name}")

            except Exception as e:
                logger.error(f"Error getting tools from {server_name}: {e}")

            # Stop the server after getting tools
            # In a real implementation, you'd keep it running
            server.stop()
        else:
            logger.error(f"Failed to start {server_name}")

    return all_tools
