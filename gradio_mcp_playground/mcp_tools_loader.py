"""MCP Tools Loader

Loads MCP servers from configuration and creates LlamaIndex tools.
"""

import asyncio
import logging
from typing import List, Any, Dict, Optional, Tuple
import threading
import time

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession, StdioServerParameters, stdio_client

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

try:
    from llama_index.core.tools import FunctionTool

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


async def load_mcp_tools() -> List[Any]:
    """Load all MCP servers and create LlamaIndex tools"""
    if not HAS_LLAMAINDEX:
        logger.warning("LlamaIndex not installed")
        return []

    if not HAS_MCP:
        logger.warning("MCP not installed")
        return []

    tools = []

    try:
        from .mcp_server_config import MCPServerConfig
        from .mcp_stdio_wrapper import get_mcp_manager

        config = MCPServerConfig()
        servers = config.list_servers()

        if not servers:
            logger.info("No MCP servers configured")
            return []

        logger.info(f"Loading {len(servers)} MCP servers...")

        # Get the manager
        manager = await get_mcp_manager()

        # Connect to each server
        for server_name, server_config in servers.items():
            logger.info(f"Connecting to {server_name}...")

            command = server_config.get("command", "")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            connected, server_tools = await manager.connect_server(server_name, command, args, env)

            if connected and server_tools:
                # Create LlamaIndex tools for each MCP tool
                for tool_name, tool_info in server_tools.items():
                    # Create a wrapper function for the tool
                    def create_tool_wrapper(mgr, s_name, t_name):
                        def wrapper(**kwargs):
                            """Wrapper for MCP tool"""
                            # Run async call in new event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                result = loop.run_until_complete(
                                    mgr.call_tool(s_name, t_name, kwargs)
                                )

                                # Extract content from result
                                if hasattr(result, "content"):
                                    if isinstance(result.content, list):
                                        # Multiple content items
                                        outputs = []
                                        for item in result.content:
                                            if hasattr(item, "text"):
                                                outputs.append(item.text)
                                            else:
                                                outputs.append(str(item))
                                        return "\n".join(outputs)
                                    else:
                                        return str(result.content)
                                return str(result)
                            except Exception as e:
                                return f"Error calling {t_name}: {str(e)}"
                            finally:
                                loop.close()

                        wrapper.__name__ = f"{s_name}_{t_name}"
                        wrapper.__doc__ = (
                            tool_info.description
                            if hasattr(tool_info, "description")
                            else f"Call {t_name} from {s_name}"
                        )
                        return wrapper

                    # Create the tool
                    tool_fn = create_tool_wrapper(manager, server_name, tool_name)
                    llamaindex_tool = FunctionTool.from_defaults(
                        fn=tool_fn, name=f"{server_name}_{tool_name}"
                    )
                    tools.append(llamaindex_tool)

                logger.info(f"✅ Loaded {len(server_tools)} tools from {server_name}")
            else:
                logger.warning(f"❌ Could not connect to {server_name}")

        logger.info(f"Total tools loaded: {len(tools)}")

    except Exception as e:
        logger.error(f"Error loading MCP tools: {e}")
        import traceback

        traceback.print_exc()

    return tools


def load_mcp_tools_sync() -> List[Any]:
    """Synchronous wrapper to load all MCP tools"""
    # Run in a dedicated thread to avoid event loop conflicts
    result = []
    error = None

    def run_async():
        nonlocal result, error
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(load_mcp_tools())
            finally:
                loop.close()
        except Exception as e:
            error = e

    # Run in thread
    thread = threading.Thread(target=run_async)
    thread.start()
    thread.join(timeout=30)  # 30 second timeout

    if thread.is_alive():
        logger.error("Timeout loading MCP tools")
        return []

    if error:
        logger.error(f"Error loading MCP tools: {error}")
        return []

    return result


async def cleanup_connections():
    """Clean up all active MCP connections"""
    try:
        from .mcp_stdio_wrapper import get_mcp_manager

        manager = await get_mcp_manager()
        await manager.cleanup_all()
    except:
        pass
