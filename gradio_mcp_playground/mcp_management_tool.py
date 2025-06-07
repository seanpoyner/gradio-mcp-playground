"""MCP Server Management Tool for Coding Agent

Provides the coding agent with direct access to gmp CLI commands for server management.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    from llama_index.core.tools import FunctionTool

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False

try:
    import gradio as gr

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False


class MCPServerManager:
    """Manages MCP servers through gmp CLI commands"""

    def __init__(self):
        pass

    def _get_gmp_path(self) -> str:
        """Get the path to the gmp command"""
        # Try direct execution first (most common case)
        try:
            result = subprocess.run(
                ["gmp", "--version"], capture_output=True, text=True, shell=True
            )
            if result.returncode == 0:
                return "gmp"
        except:
            pass

        # Try which/where command depending on OS
        try:
            which_cmd = "where" if sys.platform == "win32" else "which"
            result = subprocess.run([which_cmd, "gmp"], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]  # Take first result on Windows
        except:
            pass

        # Try Python module execution
        try:
            result = subprocess.run(
                [sys.executable, "-m", "gradio_mcp_playground.cli", "--version"],
                capture_output=True,
                text=True,
                shell=True,
            )
            if result.returncode == 0:
                return f"{sys.executable} -m gradio_mcp_playground.cli"
        except:
            pass

        raise RuntimeError(
            "gmp command not found. Please ensure gradio-mcp-playground is installed."
        )

    def _request_approval(self, command: str, description: str) -> bool:
        """No approval required - execute commands directly"""
        return True

    def _execute_gmp_command(self, args: List[str], description: str) -> Tuple[bool, str]:
        """Execute a gmp command directly"""
        try:
            gmp_path = self._get_gmp_path()
            command_parts = gmp_path.split() + args
            command_str = " ".join(command_parts)

            # Execute directly without approval

            # Execute command with longer timeout for list operations and proper encoding
            timeout = 60 if "list" in args else 30

            # Set environment variables to handle encoding issues on Windows
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            # Disable Rich progress bars to avoid Unicode issues on Windows
            env["RICH_FORCE_TERMINAL"] = "0"
            env["NO_COLOR"] = "1"
            # Force non-interactive mode
            env["CI"] = "1"
            env["TERM"] = "dumb"

            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
                env=env,
                encoding="utf-8",
                errors="replace",
                stdin=subprocess.DEVNULL,  # Prevent any interactive input
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"Command failed: {result.stderr or result.stdout}"

        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    def list_servers(self) -> str:
        """List all available MCP servers"""
        success, output = self._execute_gmp_command(
            ["server", "list"], "List all MCP servers (running and available)"
        )

        if success:
            return f"📋 Available MCP Servers:\n{output}"
        else:
            return f"❌ Failed to list servers: {output}"

    def create_server(self, name: str, template: str = "basic", port: Optional[int] = None) -> str:
        """Create a new MCP server"""
        args = ["server", "create", name, "--template", template]
        if port:
            args.extend(["--port", str(port)])

        success, output = self._execute_gmp_command(
            args, f"Create new MCP server '{name}' using template '{template}'"
        )

        if success:
            return f"✅ Server '{name}' created successfully:\n{output}"
        else:
            return f"❌ Failed to create server '{name}': {output}"

    def start_server(self, name: str, port: Optional[int] = None) -> str:
        """Start an MCP server"""
        try:
            gmp_path = self._get_gmp_path()
            args = ["server", "start", name]
            if port:
                args.extend(["--port", str(port)])

            command_parts = gmp_path.split() + args

            # Set environment for non-interactive mode
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            env["RICH_FORCE_TERMINAL"] = "0"
            env["NO_COLOR"] = "1"
            env["CI"] = "1"
            env["TERM"] = "dumb"

            # Start process in background and return immediately
            process = subprocess.Popen(
                command_parts,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            port_info = f" on port {port}" if port else ""
            return f"🚀 Server '{name}' is starting{port_info}...\n\nProcess ID: {process.pid}\nUse 'gmp server list' to check status.\n\n⚠️ Note: The server is running in the background. Use the dashboard's Server Management tab to stop it."

        except Exception as e:
            return f"❌ Failed to start server '{name}': {str(e)}"

    def stop_server(self, name: str) -> str:
        """Stop an MCP server"""
        success, output = self._execute_gmp_command(
            ["server", "stop", name], f"Stop MCP server '{name}'"
        )

        if success:
            return f"⏹️ Server '{name}' stopped successfully:\n{output}"
        else:
            return f"❌ Failed to stop server '{name}': {output}"

    def delete_server(self, name: str) -> str:
        """Delete an MCP server"""
        success, output = self._execute_gmp_command(
            ["server", "delete", name], f"Delete MCP server '{name}' and its files"
        )

        if success:
            return f"🗑️ Server '{name}' deleted successfully:\n{output}"
        else:
            return f"❌ Failed to delete server '{name}': {output}"

    def server_info(self, name: str) -> str:
        """Get detailed information about a server"""
        success, output = self._execute_gmp_command(
            ["server", "info", name], f"Get information about MCP server '{name}'"
        )

        if success:
            return f"ℹ️ Server '{name}' information:\n{output}"
        else:
            return f"❌ Failed to get server info for '{name}': {output}"

    def list_templates(self) -> str:
        """List available server templates"""
        success, output = self._execute_gmp_command(
            ["server", "templates"], "List available MCP server templates"
        )

        if success:
            return f"📦 Available Templates:\n{output}"
        else:
            return f"❌ Failed to list templates: {output}"

    def connect_client(self, url: str, name: Optional[str] = None) -> str:
        """Connect to an MCP server as a client"""
        args = ["client", "connect", url]
        if name:
            args.extend(["--name", name])

        success, output = self._execute_gmp_command(args, f"Connect to MCP server at '{url}'")

        if success:
            return f"🔗 Connected to server at '{url}':\n{output}"
        else:
            return f"❌ Failed to connect to '{url}': {output}"

    def disconnect_client(self, name: str) -> str:
        """Disconnect from an MCP server"""
        success, output = self._execute_gmp_command(
            ["client", "disconnect", name], f"Disconnect from MCP server '{name}'"
        )

        if success:
            return f"🔌 Disconnected from '{name}':\n{output}"
        else:
            return f"❌ Failed to disconnect from '{name}': {output}"

    def list_connections(self) -> str:
        """List active client connections"""
        success, output = self._execute_gmp_command(
            ["client", "list"], "List active MCP client connections"
        )

        if success:
            return f"🔗 Active Connections:\n{output}"
        else:
            return f"❌ Failed to list connections: {output}"

    def test_connection(self, url: str) -> str:
        """Test connection to an MCP server"""
        success, output = self._execute_gmp_command(
            ["client", "test", url], f"Test connection to MCP server at '{url}'"
        )

        if success:
            return f"🧪 Connection test for '{url}':\n{output}"
        else:
            return f"❌ Connection test failed for '{url}': {output}"

    def get_help(self, command: Optional[str] = None) -> str:
        """Get help for gmp commands"""
        args = ["--help"]
        if command:
            args = [command, "--help"]

        success, output = self._execute_gmp_command(
            args, f"Get help for gmp {command or 'commands'}"
        )

        if success:
            return f"📖 GMP Help:\n{output}"
        else:
            return f"❌ Failed to get help: {output}"


# Global manager instance for GUI integration
_global_manager = None


def get_mcp_manager() -> MCPServerManager:
    """Get the global MCP manager instance"""
    global _global_manager
    if _global_manager is None:
        _global_manager = MCPServerManager()
    return _global_manager


def create_mcp_management_tools():
    """Create LlamaIndex tools for MCP server management"""
    if not HAS_LLAMAINDEX:
        return []

    manager = get_mcp_manager()

    tools = []

    # Server management tools
    def list_mcp_servers() -> str:
        """List all available MCP servers and their status.

        Returns:
            str: List of servers with their current status
        """
        return manager.list_servers()

    def create_mcp_server(name: str, template: str = "basic", port: int = None) -> str:
        """Create a new MCP server from a template.

        Args:
            name: Name for the new server
            template: Template to use (basic, calculator, multi-tool, image-generator)
            port: Optional port number for the server

        Returns:
            str: Result of server creation
        """
        return manager.create_server(name, template, port)

    def start_mcp_server(name: str, port: int = None) -> str:
        """Start an MCP server.

        Args:
            name: Name of the server to start
            port: Optional port number to use

        Returns:
            str: Result of starting the server
        """
        return manager.start_server(name, port)

    def stop_mcp_server(name: str) -> str:
        """Stop a running MCP server.

        Args:
            name: Name of the server to stop

        Returns:
            str: Result of stopping the server
        """
        return manager.stop_server(name)

    def delete_mcp_server(name: str) -> str:
        """Delete an MCP server and its files.

        Args:
            name: Name of the server to delete

        Returns:
            str: Result of deleting the server
        """
        return manager.delete_server(name)

    def get_mcp_server_info(name: str) -> str:
        """Get detailed information about an MCP server.

        Args:
            name: Name of the server to get info about

        Returns:
            str: Detailed server information
        """
        return manager.server_info(name)

    def list_mcp_templates() -> str:
        """List available MCP server templates.

        Returns:
            str: List of available templates with descriptions
        """
        return manager.list_templates()

    # Client connection tools
    def connect_to_mcp_server(url: str, name: str = None) -> str:
        """Connect to an MCP server as a client.

        Args:
            url: URL of the MCP server to connect to
            name: Optional name for the connection

        Returns:
            str: Result of connection attempt
        """
        return manager.connect_client(url, name)

    def disconnect_from_mcp_server(name: str) -> str:
        """Disconnect from an MCP server.

        Args:
            name: Name of the connection to disconnect

        Returns:
            str: Result of disconnection
        """
        return manager.disconnect_client(name)

    def list_mcp_connections() -> str:
        """List active MCP client connections.

        Returns:
            str: List of active connections
        """
        return manager.list_connections()

    def test_mcp_connection(url: str) -> str:
        """Test connection to an MCP server.

        Args:
            url: URL of the MCP server to test

        Returns:
            str: Result of connection test
        """
        return manager.test_connection(url)

    def get_mcp_help(command: str = None) -> str:
        """Get help for MCP server management commands.

        Args:
            command: Optional specific command to get help for

        Returns:
            str: Help information
        """
        return manager.get_help(command)

    # Create tools
    tools.extend(
        [
            # Server management tools
            FunctionTool.from_defaults(fn=list_mcp_servers, name="list_mcp_servers"),
            FunctionTool.from_defaults(fn=create_mcp_server, name="create_mcp_server"),
            FunctionTool.from_defaults(fn=start_mcp_server, name="start_mcp_server"),
            FunctionTool.from_defaults(fn=stop_mcp_server, name="stop_mcp_server"),
            FunctionTool.from_defaults(fn=delete_mcp_server, name="delete_mcp_server"),
            FunctionTool.from_defaults(fn=get_mcp_server_info, name="get_mcp_server_info"),
            FunctionTool.from_defaults(fn=list_mcp_templates, name="list_mcp_templates"),
            # Client connection tools
            FunctionTool.from_defaults(fn=connect_to_mcp_server, name="connect_to_mcp_server"),
            FunctionTool.from_defaults(
                fn=disconnect_from_mcp_server, name="disconnect_from_mcp_server"
            ),
            FunctionTool.from_defaults(fn=list_mcp_connections, name="list_mcp_connections"),
            FunctionTool.from_defaults(fn=test_mcp_connection, name="test_mcp_connection"),
            # Help tools
            FunctionTool.from_defaults(fn=get_mcp_help, name="get_mcp_help"),
        ]
    )

    return tools
