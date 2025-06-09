"""MCP Server Configuration Management

This module manages MCP server configurations in a format compatible with Claude Desktop.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class MCPServerConfig:
    """Manages MCP server configurations like Claude Desktop"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # Use the same directory as our other configs
            # Check if we're on WSL with Windows home
            if Path("/mnt/c/Users/seanp/.gradio-mcp").exists():
                self.config_dir = Path("/mnt/c/Users/seanp/.gradio-mcp")
            else:
                self.config_dir = Path.home() / ".gradio-mcp"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "mcp_servers.json"
        
        # Load or initialize config
        self._load_config()
    
    def _load_config(self):
        """Load the MCP server configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Initialize with empty config
            self.config = {
                "mcpServers": {}
            }
            self._save_config()
    
    def _save_config(self):
        """Save the MCP server configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def add_server(self, name: str, command: str, args: Optional[List[str]] = None, 
                   env: Optional[Dict[str, str]] = None) -> bool:
        """Add or update an MCP server configuration
        
        Args:
            name: Server name/ID
            command: Command to run the server
            args: Command arguments
            env: Environment variables
            
        Returns:
            True if added/updated successfully
        """
        server_config = {
            "command": command
        }
        
        if args:
            server_config["args"] = args
        
        if env:
            server_config["env"] = env
        
        self.config["mcpServers"][name] = server_config
        self._save_config()
        return True
    
    def remove_server(self, name: str) -> bool:
        """Remove an MCP server configuration"""
        if name in self.config["mcpServers"]:
            del self.config["mcpServers"][name]
            self._save_config()
            return True
        return False
    
    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific server configuration"""
        return self.config["mcpServers"].get(name)
    
    def list_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all server configurations"""
        return self.config["mcpServers"].copy()
    
    def get_server_command(self, name: str) -> Optional[tuple[str, List[str]]]:
        """Get the command and args for a server
        
        Returns:
            Tuple of (command, args) or None if not found
        """
        server = self.get_server(name)
        if not server:
            return None
        
        command = server.get("command", "")
        args = server.get("args", [])
        
        return command, args
    
    def export_claude_desktop_format(self) -> str:
        """Export configuration in Claude Desktop format"""
        # Claude Desktop format is slightly different
        claude_config = {}
        
        for name, server in self.config["mcpServers"].items():
            claude_server = {
                "command": server["command"]
            }
            
            if "args" in server:
                claude_server["args"] = server["args"]
            
            if "env" in server:
                claude_server["env"] = server["env"]
            
            claude_config[name] = claude_server
        
        return json.dumps(claude_config, indent=2)
    
    def import_from_claude_desktop(self, claude_config: Dict[str, Any]):
        """Import configuration from Claude Desktop format"""
        for name, server in claude_config.items():
            self.add_server(
                name=name,
                command=server.get("command", ""),
                args=server.get("args"),
                env=server.get("env")
            )
    
    def create_server_from_registry(self, server_id: str, command: str, 
                                   args: List[str], env: Optional[Dict[str, str]] = None):
        """Create a server configuration from registry installation"""
        # Store the server configuration
        self.add_server(
            name=server_id,
            command=command,
            args=args,
            env=env
        )
        
        return {
            "name": server_id,
            "command": command,
            "args": args,
            "env": env or {}
        }