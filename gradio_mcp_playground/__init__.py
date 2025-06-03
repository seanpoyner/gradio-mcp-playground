"""Gradio MCP Playground

A comprehensive toolkit for building and managing Gradio apps as MCP servers.
"""

# Always available imports
from .registry import ServerRegistry
from .config_manager import ConfigManager

__version__ = "0.1.0"

# Core modules always available
__all__ = [
    "ServerRegistry",
    "ConfigManager",
]

# Optional imports that depend on external packages
try:
    from .server_manager import MCPServer, GradioMCPServer
    __all__.extend(["MCPServer", "GradioMCPServer"])
except ImportError:
    # MCP package not available
    pass

try:
    from .client_manager import MCPClient, GradioMCPClient
    __all__.extend(["MCPClient", "GradioMCPClient"])
except ImportError:
    # MCP or other client dependencies not available
    pass
