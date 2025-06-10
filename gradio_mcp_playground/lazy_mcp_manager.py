"""Lazy MCP Manager

Provides lazy loading of MCP servers - tools are registered from cache
but servers are only started when tools are actually used.
"""

import logging
from typing import Dict, List, Any, Optional
from .mcp_working_client import MCPServerProcess, create_mcp_tools_for_server
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

try:
    from llama_index.core.tools import FunctionTool
    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


class LazyMCPManager:
    """Manages MCP servers with lazy loading from cache"""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self._server_configs = {}  # Store server configurations
        self._active_servers = {}  # Store running server processes
        self._lazy_tools = {}  # Store tool definitions without starting servers
        
    def register_server(self, server_name: str, command: str, args: List[str], 
                       env: Optional[Dict[str, str]] = None) -> List[Any]:
        """Register a server and return tools (from cache if available)"""
        server_config = {
            "command": command,
            "args": args,
            "env": env or {}
        }
        
        # Store config for lazy loading
        self._server_configs[server_name] = server_config
        
        # Check cache first
        cache_key_config = {
            "command": command,
            "args": args,
        }
        
        cached_data = self.cache_manager.get_server_cache(server_name, cache_key_config)
        if cached_data and 'tools' in cached_data:
            # Create lazy-loading tools from cache
            return self._create_lazy_tools(server_name, cached_data['tools'])
        
        # No cache, need to start server to get tools
        return self._start_server_and_get_tools(server_name)
    
    def _create_lazy_tools(self, server_name: str, tools_data: Dict[str, Any]) -> List[Any]:
        """Create lazy-loading tools that start server on first use"""
        if not HAS_LLAMAINDEX:
            return []
            
        tools = []
        for tool_name, tool_info in tools_data.items():
            # Create a lazy tool function
            def create_lazy_tool(t_name, s_name):
                def lazy_tool_func(**kwargs):
                    # Ensure server is running
                    server = self._ensure_server_running(s_name)
                    if not server:
                        return {"error": f"Failed to start server {s_name}"}
                    
                    # Call the actual tool
                    return server.call_tool(t_name, kwargs)
                
                return lazy_tool_func
            
            tool = FunctionTool.from_defaults(
                fn=create_lazy_tool(tool_name, server_name),
                name=f"{server_name}__{tool_name}",
                description=tool_info.get("description", f"Tool {tool_name} from {server_name}")
            )
            tools.append(tool)
            
        # Store tools for this server
        self._lazy_tools[server_name] = tools
        return tools
    
    def _ensure_server_running(self, server_name: str) -> Optional[MCPServerProcess]:
        """Ensure a server is running, starting it if necessary"""
        # Check if already running
        if server_name in self._active_servers:
            return self._active_servers[server_name]
        
        # Start the server
        config = self._server_configs.get(server_name)
        if not config:
            logger.error(f"No configuration found for server {server_name}")
            return None
            
        logger.info(f"Starting server {server_name} on demand...")
        server = MCPServerProcess(
            server_name, 
            config['command'], 
            config['args'], 
            config.get('env')
        )
        
        if server.start() and server.initialize():
            self._active_servers[server_name] = server
            logger.info(f"✅ Started {server_name} successfully")
            return server
        else:
            logger.error(f"Failed to start {server_name}")
            return None
    
    def _start_server_and_get_tools(self, server_name: str) -> List[Any]:
        """Start a server immediately and get its tools"""
        config = self._server_configs.get(server_name)
        if not config:
            return []
            
        server = MCPServerProcess(
            server_name,
            config['command'],
            config['args'],
            config.get('env')
        )
        
        if server.start() and server.initialize():
            self._active_servers[server_name] = server
            tools = create_mcp_tools_for_server(server)
            self._lazy_tools[server_name] = tools
            return tools
        
        return []
    
    def stop_all(self):
        """Stop all active servers"""
        for server_name, server in self._active_servers.items():
            try:
                server.stop()
                logger.info(f"Stopped server {server_name}")
            except Exception as e:
                logger.error(f"Error stopping server {server_name}: {e}")
        
        self._active_servers.clear()
    
    def get_active_servers(self) -> List[str]:
        """Get list of currently running servers"""
        return list(self._active_servers.keys())
    
    def get_registered_servers(self) -> List[str]:
        """Get list of all registered servers (running or not)"""
        return list(self._server_configs.keys())