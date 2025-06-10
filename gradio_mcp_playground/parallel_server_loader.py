"""Parallel Server Loader

Loads multiple MCP servers in parallel for faster startup.
"""

import concurrent.futures
import logging
from typing import Dict, List, Any, Optional, Tuple
from .mcp_working_client import MCPServerProcess, create_mcp_tools_for_server
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


def load_server(server_info: Tuple[str, Dict[str, Any]]) -> Tuple[str, Optional[List[Any]], Optional[Any]]:
    """Load a single server - used for parallel execution"""
    server_name, config = server_info
    
    try:
        command = config.get("command", "")
        args = config.get("args", [])
        env = config.get("env", {})
        
        # Create and start server
        server = MCPServerProcess(server_name, command, args, env)
        
        if server.start() and server.initialize():
            # Create tools
            server_tools = create_mcp_tools_for_server(server)
            
            if server_tools:
                return (server_name, server_tools, server)
            else:
                server.stop()
                return (server_name, None, None)
        else:
            return (server_name, None, None)
            
    except Exception as e:
        logger.error(f"Error loading {server_name}: {e}")
        return (server_name, None, None)


def load_servers_parallel(servers: Dict[str, Dict[str, Any]], max_workers: int = 5) -> Dict[str, Any]:
    """Load multiple servers in parallel"""
    results = {
        'tools': {},
        'servers': {},
        'loaded_count': 0,
        'failed': []
    }
    
    # Prepare server list
    server_list = [(name, config) for name, config in servers.items()]
    
    print(f"\n🔌 Loading {len(server_list)} MCP servers in parallel...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_server = {
            executor.submit(load_server, server_info): server_info[0] 
            for server_info in server_list
        }
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_server):
            server_name = future_to_server[future]
            
            try:
                name, tools, server = future.result()
                
                if tools and server:
                    results['tools'][name] = tools
                    results['servers'][name] = server
                    results['loaded_count'] += len(tools)
                    print(f"   ✅ Loaded {len(tools)} tools from {name}")
                else:
                    results['failed'].append(name)
                    print(f"   ❌ Failed to load {name}")
                    
            except Exception as e:
                results['failed'].append(server_name)
                print(f"   ❌ Error loading {server_name}: {e}")
    
    return results