"""Gradio MCP Playground

A comprehensive toolkit for building and managing Gradio apps as MCP servers.
"""

from .server_manager import MCPServer, GradioMCPServer
from .client_manager import MCPClient, GradioMCPClient
from .registry import ServerRegistry
from .config_manager import ConfigManager

__version__ = "0.1.0"
__all__ = [
    "MCPServer",
    "GradioMCPServer",
    "MCPClient",
    "GradioMCPClient",
    "ServerRegistry",
    "ConfigManager",
]
