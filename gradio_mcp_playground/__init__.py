"""Gradio MCP Playground

A comprehensive toolkit for building and managing Gradio apps as MCP servers.
"""

import warnings
# Suppress Pydantic model_name warning
warnings.filterwarnings("ignore", message="Field \"model_name\" has conflict with protected namespace \"model_\"", category=UserWarning)

# Always available imports
from .config_manager import ConfigManager
from .registry import ServerRegistry

__version__ = "0.1.0"

# Core modules always available
__all__ = [
    "ServerRegistry",
    "ConfigManager",
]

# Optional imports that depend on external packages
try:
    from .server_manager import GradioMCPServer, MCPServer

    __all__.extend(["MCPServer", "GradioMCPServer"])
except ImportError:
    # MCP package not available
    pass

try:
    from .client_manager import GradioMCPClient, MCPClient

    __all__.extend(["MCPClient", "GradioMCPClient"])
except ImportError:
    # MCP or other client dependencies not available
    pass
