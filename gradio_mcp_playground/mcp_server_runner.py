"""MCP Server Runner

This module manages running MCP servers and provides a clean interface for connecting to them.
It handles the async/sync boundary properly to work in Gradio environments.
"""

import asyncio
import subprocess
import sys
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.types import Tool
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("Warning: MCP package not installed")

try:
    from llama_index.core.tools import FunctionTool
    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


class MCPServerRunner:
    """Manages MCP server processes and connections"""
    
    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.connections: Dict[str, Any] = {}
        
    def start_server(self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """Start an MCP server process"""
        try:
            # Prepare environment
            import os
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start the server
            process = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env
            )
            
            # Store server info
            self.servers[server_id] = {
                'process': process,
                'command': command,
                'args': args,
                'env': env or {}
            }
            
            print(f"Started {server_id} server (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"Failed to start {server_id}: {e}")
            return False
    
    def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server"""
        if server_id not in self.servers:
            return False
            
        try:
            process = self.servers[server_id]['process']
            process.terminate()
            process.wait(timeout=5)
            del self.servers[server_id]
            
            # Also remove connection if exists
            if server_id in self.connections:
                del self.connections[server_id]
                
            print(f"Stopped {server_id} server")
            return True
            
        except Exception as e:
            print(f"Error stopping {server_id}: {e}")
            return False
    
    async def connect_to_server(self, server_id: str) -> Optional[ClientSession]:
        """Connect to a running MCP server"""
        if not HAS_MCP:
            return None
            
        if server_id not in self.servers:
            print(f"Server {server_id} not running")
            return None
            
        try:
            server_info = self.servers[server_id]
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=server_info['command'],
                args=server_info['args']
            )
            
            # Connect to the server
            async with stdio_client(server_params) as (read_stream, write_stream):
                session = ClientSession(read_stream, write_stream)
                await session.initialize()
                
                # Store the session
                self.connections[server_id] = {
                    'session': session,
                    'read_stream': read_stream,
                    'write_stream': write_stream
                }
                
                return session
                
        except Exception as e:
            print(f"Failed to connect to {server_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_server_tools(self, server_id: str) -> Dict[str, Any]:
        """Get tools from a server"""
        session = await self.connect_to_server(server_id)
        if not session:
            return {}
            
        try:
            tools_result = await session.list_tools()
            tools = {}
            for tool in tools_result.tools:
                tools[tool.name] = tool
            return tools
            
        except Exception as e:
            print(f"Failed to get tools from {server_id}: {e}")
            return {}
    
    async def call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a server"""
        session = await self.connect_to_server(server_id)
        if not session:
            return f"Failed to connect to {server_id}"
            
        try:
            result = await session.call_tool(tool_name, arguments)
            return result
            
        except Exception as e:
            return f"Error calling {tool_name}: {str(e)}"


# Global instance
_runner = MCPServerRunner()


def get_mcp_runner() -> MCPServerRunner:
    """Get the global MCP runner instance"""
    return _runner


def start_and_connect_server(server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[bool, List[Any]]:
    """Start a server and get its tools synchronously"""
    runner = get_mcp_runner()
    
    # Start the server
    if not runner.start_server(server_id, command, args, env):
        return False, []
    
    # Connect and get tools
    async def _get_tools():
        tools_dict = await runner.get_server_tools(server_id)
        
        if not HAS_LLAMAINDEX:
            return list(tools_dict.values())
            
        # Create LlamaIndex tools
        llamaindex_tools = []
        for tool_name, tool_info in tools_dict.items():
            # Create wrapper
            def make_tool_wrapper(sid, tname):
                def wrapper(**kwargs):
                    # Run async call in sync context
                    async def _call():
                        return await runner.call_tool(sid, tname, kwargs)
                    
                    try:
                        # Get or create event loop
                        try:
                            loop = asyncio.get_running_loop()
                            # We're in async context, use nest_asyncio
                            task = asyncio.create_task(_call())
                            return asyncio.run_until_complete(task)
                        except RuntimeError:
                            # No running loop
                            return asyncio.run(_call())
                    except Exception as e:
                        return f"Error: {str(e)}"
                
                wrapper.__name__ = f"{sid}_{tname}"
                wrapper.__doc__ = tool_info.description if hasattr(tool_info, 'description') else f"Call {tname}"
                return wrapper
            
            tool_fn = make_tool_wrapper(server_id, tool_name)
            llamaindex_tool = FunctionTool.from_defaults(
                fn=tool_fn,
                name=f"{server_id}_{tool_name}"
            )
            llamaindex_tools.append(llamaindex_tool)
        
        return llamaindex_tools
    
    # Run async function
    try:
        # Create new event loop for this operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tools = loop.run_until_complete(_get_tools())
            return True, tools
        finally:
            loop.close()
    except Exception as e:
        print(f"Error getting tools: {e}")
        import traceback
        traceback.print_exc()
        return True, []  # Server started but couldn't get tools


def load_all_configured_servers() -> List[Any]:
    """Load all configured MCP servers and return their tools"""
    from .mcp_server_config import MCPServerConfig
    
    config = MCPServerConfig()
    servers = config.list_servers()
    
    all_tools = []
    
    for server_name, server_config in servers.items():
        print(f"Loading {server_name}...")
        
        command = server_config.get('command', '')
        args = server_config.get('args', [])
        env = server_config.get('env', {})
        
        success, tools = start_and_connect_server(server_name, command, args, env)
        
        if success:
            print(f"✅ Started {server_name} with {len(tools)} tools")
            all_tools.extend(tools)
        else:
            print(f"❌ Failed to start {server_name}")
    
    return all_tools