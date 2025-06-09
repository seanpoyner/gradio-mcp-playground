#!/usr/bin/env python3
"""Test the MCP connection manager"""

import time
import logging
from gradio_mcp_playground.mcp_connection_manager import (
    MCPConnectionManager, 
    MCPConnection,
    load_mcp_servers_from_config
)
from gradio_mcp_playground.mcp_server_config import MCPServerConfig

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_single_connection():
    """Test a single MCP connection"""
    print("=== Testing Single MCP Connection ===\n")
    
    # Create connection
    connection = MCPConnection(
        "memory",
        "npx",
        ["-y", "@modelcontextprotocol/server-memory"]
    )
    
    # Start it
    print("Starting connection...")
    if connection.start():
        print(f"✅ Connected successfully")
        print(f"Tools available: {list(connection.tools.keys())}")
        
        # Test calling a tool
        if "store" in connection.tools:
            print("\nTesting store tool...")
            result = connection.call_tool("store", {
                "key": "test_connection",
                "value": {"message": "Connection manager works!"}
            })
            print(f"Result: {result}")
        
        # Get LlamaIndex tools
        llamaindex_tools = connection.get_llamaindex_tools()
        print(f"\nLlamaIndex tools created: {len(llamaindex_tools)}")
        for tool in llamaindex_tools:
            print(f"  - {tool.name}")
        
        # Stop connection
        connection.stop()
        print("\nConnection stopped")
    else:
        print("❌ Failed to connect")

def test_connection_manager():
    """Test the connection manager"""
    print("\n=== Testing Connection Manager ===\n")
    
    manager = MCPConnectionManager()
    
    # Add memory server
    print("Adding memory server...")
    if manager.add_server("memory", "npx", ["-y", "@modelcontextprotocol/server-memory"]):
        print("✅ Memory server added")
    
    # Get all tools
    tools = manager.get_all_tools()
    print(f"\nTotal tools available: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}")
    
    # Stop all
    manager.stop_all()
    print("\nAll connections stopped")

def test_config_loading():
    """Test loading from configuration"""
    print("\n=== Testing Config Loading ===\n")
    
    # Check config
    config = MCPServerConfig()
    servers = config.list_servers()
    print(f"Configured servers: {list(servers.keys())}")
    
    if servers:
        # Load all servers
        print("\nLoading servers from config...")
        tools = load_mcp_servers_from_config()
        
        print(f"\nLoaded {len(tools)} tools total")
        
        # Test a tool if available
        if tools:
            memory_store = next((t for t in tools if "store" in t.name), None)
            if memory_store:
                print(f"\nTesting {memory_store.name}...")
                result = memory_store.fn(
                    key="config_test",
                    value={"data": "Loaded from config!"}
                )
                print(f"Result: {result}")
        
        # Clean up
        from gradio_mcp_playground.mcp_connection_manager import get_connection_manager
        manager = get_connection_manager()
        manager.stop_all()
        print("\nCleanup complete")
    else:
        print("No servers configured")

def main():
    # Test single connection
    test_single_connection()
    
    # Test connection manager
    test_connection_manager()
    
    # Test config loading
    test_config_loading()
    
    print("\n=== All Tests Complete ===")

if __name__ == "__main__":
    main()