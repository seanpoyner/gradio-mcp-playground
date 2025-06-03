"""Gradio MCP Configuration Manager

Manages configuration for Gradio MCP Playground.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class ConfigManager:
    """Manages Gradio MCP Playground configuration"""

    def __init__(self):
        self.config_dir = Path.home() / ".gradio-mcp"
        self.config_path = self.config_dir / "config.json"
        self.servers_path = self.config_dir / "servers.json"
        self.connections_path = self.config_dir / "connections.json"
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> None:
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                self.config = json.load(f)
        else:
            self.config = self._get_default_config()
            self.save_config(self.config)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "default_port": 7860,
            "auto_reload": True,
            "mcp_protocol": "auto",
            "log_level": "INFO",
            "theme": "default",
            "check_updates": True,
        }

    def config_exists(self) -> bool:
        """Check if configuration exists"""
        return self.config_path.exists()

    def load_config(self) -> Dict[str, Any]:
        """Load and return configuration"""
        return self.config.copy()

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        self.config = config
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.config[key] = value
        self.save_config(self.config)

    # Server management

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered servers"""
        if not self.servers_path.exists():
            return []

        with open(self.servers_path) as f:
            servers_data = json.load(f)

        # Add runtime status
        from .server_manager import GradioMCPServer

        running_servers = GradioMCPServer.find_running_servers()
        running_map = {s["app_path"]: s for s in running_servers}

        servers = []
        for server in servers_data.get("servers", []):
            server_info = server.copy()

            # Check if running
            if server_info.get("path") in running_map:
                server_info["running"] = running_map[server_info["path"]]["running"]
                server_info["pid"] = running_map[server_info["path"]].get("pid")
                server_info["port"] = running_map[server_info["path"]].get("port")
            else:
                server_info["running"] = False

            servers.append(server_info)

        return servers

    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific server by name"""
        servers = self.list_servers()
        for server in servers:
            if server.get("name") == name:
                return server
        return None

    def add_server(self, server_config: Dict[str, Any]) -> None:
        """Add a new server to the registry"""
        if self.servers_path.exists():
            with open(self.servers_path) as f:
                data = json.load(f)
        else:
            data = {"servers": []}

        # Check for duplicate names
        for existing in data["servers"]:
            if existing.get("name") == server_config.get("name"):
                raise ValueError(f"Server '{server_config['name']}' already exists")

        # Add timestamp
        server_config["registered"] = datetime.now().isoformat()

        data["servers"].append(server_config)

        with open(self.servers_path, "w") as f:
            json.dump(data, f, indent=2)

    def remove_server(self, name: str) -> bool:
        """Remove a server from the registry"""
        if not self.servers_path.exists():
            return False

        with open(self.servers_path) as f:
            data = json.load(f)

        original_count = len(data["servers"])
        data["servers"] = [s for s in data["servers"] if s.get("name") != name]

        if len(data["servers"]) < original_count:
            with open(self.servers_path, "w") as f:
                json.dump(data, f, indent=2)
            return True

        return False

    def update_server(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update server configuration"""
        if not self.servers_path.exists():
            return False

        with open(self.servers_path) as f:
            data = json.load(f)

        for server in data["servers"]:
            if server.get("name") == name:
                server.update(updates)
                server["updated"] = datetime.now().isoformat()

                with open(self.servers_path, "w") as f:
                    json.dump(data, f, indent=2)

                return True

        return False

    # Connection management

    def list_connections(self) -> List[Dict[str, Any]]:
        """List all saved connections"""
        if not self.connections_path.exists():
            return []

        with open(self.connections_path) as f:
            data = json.load(f)

        return data.get("connections", [])

    def save_connection(self, name: str, url: str, protocol: str = "auto") -> None:
        """Save a connection"""
        if self.connections_path.exists():
            with open(self.connections_path) as f:
                data = json.load(f)
        else:
            data = {"connections": []}

        # Check for duplicate names
        for conn in data["connections"]:
            if conn.get("name") == name:
                # Update existing
                conn["url"] = url
                conn["protocol"] = protocol
                conn["updated"] = datetime.now().isoformat()

                with open(self.connections_path, "w") as f:
                    json.dump(data, f, indent=2)
                return

        # Add new connection
        connection = {
            "name": name,
            "url": url,
            "protocol": protocol,
            "created": datetime.now().isoformat(),
        }

        data["connections"].append(connection)

        with open(self.connections_path, "w") as f:
            json.dump(data, f, indent=2)

    def remove_connection(self, name: str) -> bool:
        """Remove a saved connection"""
        if not self.connections_path.exists():
            return False

        with open(self.connections_path) as f:
            data = json.load(f)

        original_count = len(data["connections"])
        data["connections"] = [c for c in data["connections"] if c.get("name") != name]

        if len(data["connections"]) < original_count:
            with open(self.connections_path, "w") as f:
                json.dump(data, f, indent=2)
            return True

        return False

    # Environment setup

    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variables for Gradio MCP"""
        env = {}

        # Add HF token if configured
        if "hf_token" in self.config:
            env["HF_TOKEN"] = self.config["hf_token"]

        # Add other relevant env vars
        env["GRADIO_ANALYTICS_ENABLED"] = "false"
        env["GRADIO_SERVER_NAME"] = "0.0.0.0"

        return env

    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration"""
        result = {"valid": True, "errors": [], "warnings": []}

        # Check required fields
        required = ["default_port", "mcp_protocol", "log_level"]
        for field in required:
            if field not in self.config:
                result["errors"].append(f"Missing required field: {field}")
                result["valid"] = False

        # Validate port
        port = self.config.get("default_port")
        if port:
            if not isinstance(port, int) or port < 1 or port > 65535:
                result["errors"].append("Invalid port number")
                result["valid"] = False

        # Validate MCP protocol
        protocol = self.config.get("mcp_protocol")
        if protocol and protocol not in ["stdio", "sse", "auto"]:
            result["errors"].append(f"Invalid MCP protocol: {protocol}")
            result["valid"] = False

        # Check for HF token if deployment is planned
        if "hf_token" not in self.config:
            result["warnings"].append("Hugging Face token not configured (needed for deployment)")

        return result

    # Quick access methods

    @property
    def default_port(self) -> int:
        """Get default port"""
        return self.config.get("default_port", 7860)

    @property
    def auto_reload(self) -> bool:
        """Get auto-reload setting"""
        return self.config.get("auto_reload", True)

    @property
    def mcp_protocol(self) -> str:
        """Get preferred MCP protocol"""
        return self.config.get("mcp_protocol", "auto")

    @property
    def log_level(self) -> str:
        """Get log level"""
        return self.config.get("log_level", "INFO")

    @property
    def hf_token(self) -> Optional[str]:
        """Get Hugging Face token"""
        return self.config.get("hf_token")
