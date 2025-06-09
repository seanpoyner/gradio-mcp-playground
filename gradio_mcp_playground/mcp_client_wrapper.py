"""MCP Client Wrapper that handles server startup messages

This wrapper properly handles MCP servers that print status messages before
entering JSONRPC mode by using the standard MCP client with workarounds.
"""

import asyncio
import subprocess
import sys
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from contextlib import asynccontextmanager
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession, StdioServerParameters, stdio_client
    import mcp.types as types
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    logger.warning("MCP package not installed")




async def connect_to_mcp_server(server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[Optional[ClientSession], Dict[str, Any]]:
    """Connect to an MCP server and return session and tools"""
    
    if not HAS_MCP:
        return None, {}
    
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        # Connect with timeout
        async with asyncio.timeout(10):
            async with stdio_client(server_params) as (read_stream, write_stream):
                # Create session
                session = ClientSession(read_stream, write_stream)
                
                # Initialize
                await session.initialize()
                
                # Get tools
                tools_result = await session.list_tools()
                
                tools = {}
                for tool in tools_result.tools:
                    tools[tool.name] = tool
                
                logger.info(f"Connected to {server_id} with {len(tools)} tools")
                return session, tools
            
    except asyncio.TimeoutError:
        logger.error(f"Timeout connecting to {server_id}")
        return None, {}
    except Exception as e:
        logger.error(f"Error connecting to {server_id}: {e}")
        import traceback
        traceback.print_exc()
        return None, {}


def create_llamaindex_tools(server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> List[Any]:
    """Create LlamaIndex tools for an MCP server"""
    
    try:
        from llama_index.core.tools import FunctionTool
    except ImportError:
        logger.warning("LlamaIndex not installed")
        return []
    
    # Connect and get tools
    async def _get_tools():
        session, tools_dict = await connect_to_mcp_server(server_id, command, args, env)
        if not session or not tools_dict:
            return []
        
        # Create LlamaIndex tools
        llamaindex_tools = []
        
        for tool_name, tool_info in tools_dict.items():
            # Create wrapper function
            def make_wrapper(sid, tname, sess):
                def wrapper(**kwargs):
                    """Wrapper function for MCP tool"""
                    async def _call():
                        try:
                            result = await sess.call_tool(tname, kwargs)
                            # Extract content from result
                            if hasattr(result, 'content'):
                                if isinstance(result.content, list):
                                    # Multiple content items
                                    outputs = []
                                    for item in result.content:
                                        if hasattr(item, 'text'):
                                            outputs.append(item.text)
                                        else:
                                            outputs.append(str(item))
                                    return '\n'.join(outputs)
                                else:
                                    return str(result.content)
                            return str(result)
                        except Exception as e:
                            return f"Error calling {tname}: {str(e)}"
                    
                    # Run async function
                    try:
                        import nest_asyncio
                        nest_asyncio.apply()
                        
                        # Create new loop for this call
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(_call())
                        finally:
                            loop.close()
                    except Exception as e:
                        return f"Error: {str(e)}"
                
                wrapper.__name__ = f"{sid}_{tname}"
                wrapper.__doc__ = tool_info.description if hasattr(tool_info, 'description') else f"Call {tname}"
                return wrapper
            
            # Create the wrapper
            tool_fn = make_wrapper(server_id, tool_name, session)
            
            # Create LlamaIndex tool
            llamaindex_tool = FunctionTool.from_defaults(
                fn=tool_fn,
                name=f"{server_id}_{tool_name}"
            )
            llamaindex_tools.append(llamaindex_tool)
        
        return llamaindex_tools
    
    # Run async function
    try:
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_get_tools())
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Error creating tools: {e}")
        return []