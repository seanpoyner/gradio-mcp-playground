"""MCP Connection Manager

Manages persistent connections to MCP servers and provides tools that work
with the active connections.
"""

import asyncio
import threading
from typing import Dict, List, Any, Optional
import logging
import nest_asyncio
from contextlib import AsyncExitStack

# Apply nest_asyncio to handle nested loops
nest_asyncio.apply()

logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession, StdioServerParameters, stdio_client
    import mcp.types as types
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    logger.warning("MCP package not installed")

try:
    from llama_index.core.tools import FunctionTool
    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


class MCPConnection:
    """Manages a single MCP server connection"""
    
    def __init__(self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.server_id = server_id
        self.command = command
        self.args = args
        self.env = env
        self.session = None
        self.tools = {}
        self._loop = None
        self._thread = None
        self._exit_stack = None
        self._connected = False
    
    def start(self):
        """Start the connection in a separate thread with its own event loop"""
        self._thread = threading.Thread(target=self._run_connection, daemon=True)
        self._thread.start()
        
        # Wait for connection to be established
        import time
        for _ in range(50):  # Wait up to 5 seconds
            if self._connected:
                return True
            time.sleep(0.1)
        return False
    
    def _run_connection(self):
        """Run the connection in a separate thread"""
        try:
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Run the connection
            self._loop.run_until_complete(self._maintain_connection())
        except Exception as e:
            logger.error(f"Error in connection thread for {self.server_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self._loop:
                self._loop.close()
    
    async def _maintain_connection(self):
        """Maintain the MCP connection"""
        try:
            # Create server parameters with stderr redirection
            import os
            env = self.env or {}
            # Suppress server status messages by redirecting stderr
            env['NODE_NO_WARNINGS'] = '1'
            
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=env
            )
            
            # Use exit stack to manage the connection
            self._exit_stack = AsyncExitStack()
            
            # Connect to server
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            
            # Create session
            self.session = ClientSession(read_stream, write_stream)
            
            # Initialize
            await self.session.initialize()
            
            # Get tools
            tools_result = await self.session.list_tools()
            for tool in tools_result.tools:
                self.tools[tool.name] = tool
            
            logger.info(f"Connected to {self.server_id} with {len(self.tools)} tools")
            self._connected = True
            
            # Keep the connection alive
            while self._connected:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error connecting to {self.server_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self._exit_stack:
                await self._exit_stack.aclose()
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on this connection"""
        if not self._connected or not self.session:
            return f"Not connected to {self.server_id}"
        
        # Run the async call in the connection's event loop
        future = asyncio.run_coroutine_threadsafe(
            self.session.call_tool(tool_name, arguments),
            self._loop
        )
        
        try:
            result = future.result(timeout=30)
            return result
        except Exception as e:
            return f"Error calling {tool_name}: {str(e)}"
    
    def stop(self):
        """Stop the connection"""
        self._connected = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_llamaindex_tools(self) -> List[Any]:
        """Get LlamaIndex tools for this connection"""
        if not HAS_LLAMAINDEX:
            return []
        
        tools = []
        
        for tool_name, tool_info in self.tools.items():
            # Create wrapper function
            def make_wrapper(tname):
                def wrapper(**kwargs):
                    """Wrapper function for MCP tool"""
                    result = self.call_tool(tname, kwargs)
                    
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
                
                wrapper.__name__ = f"{self.server_id}_{tname}"
                wrapper.__doc__ = tool_info.description if hasattr(tool_info, 'description') else f"Call {tname}"
                return wrapper
            
            # Create the wrapper
            tool_fn = make_wrapper(tool_name)
            
            # Create LlamaIndex tool
            llamaindex_tool = FunctionTool.from_defaults(
                fn=tool_fn,
                name=f"{self.server_id}_{tool_name}"
            )
            tools.append(llamaindex_tool)
        
        return tools


class MCPConnectionManager:
    """Manages multiple MCP server connections"""
    
    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
    
    def add_server(self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """Add and start a server connection"""
        if server_id in self.connections:
            logger.warning(f"Server {server_id} already connected")
            return True
        
        # Create connection
        connection = MCPConnection(server_id, command, args, env)
        
        # Start it
        if connection.start():
            self.connections[server_id] = connection
            return True
        else:
            logger.error(f"Failed to start {server_id}")
            return False
    
    def get_all_tools(self) -> List[Any]:
        """Get all LlamaIndex tools from all connections"""
        all_tools = []
        
        for connection in self.connections.values():
            tools = connection.get_llamaindex_tools()
            all_tools.extend(tools)
        
        return all_tools
    
    def stop_all(self):
        """Stop all connections"""
        for connection in self.connections.values():
            connection.stop()
        self.connections.clear()


# Global instance
_manager = MCPConnectionManager()


def get_connection_manager() -> MCPConnectionManager:
    """Get the global connection manager"""
    return _manager


def load_mcp_servers_from_config() -> List[Any]:
    """Load all configured MCP servers and return their tools"""
    from .mcp_server_config import MCPServerConfig
    
    if not HAS_MCP:
        logger.warning("MCP not installed, skipping server loading")
        return []
    
    config = MCPServerConfig()
    servers = config.list_servers()
    
    manager = get_connection_manager()
    
    # Stop any existing connections
    manager.stop_all()
    
    # Load each server
    for server_name, server_config in servers.items():
        logger.info(f"Loading {server_name}...")
        
        command = server_config.get('command', '')
        args = server_config.get('args', [])
        env = server_config.get('env', {})
        
        if manager.add_server(server_name, command, args, env):
            logger.info(f"✅ Connected to {server_name}")
        else:
            logger.error(f"❌ Failed to connect to {server_name}")
    
    # Return all tools
    return manager.get_all_tools()