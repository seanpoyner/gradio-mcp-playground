"""MCP Server for Gradio MCP Playground

Exposes server management functionality as MCP tools.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import mcp.server.stdio
    from mcp.server import Server
    from mcp.types import CallToolResult, TextContent, Tool

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

from .config_manager import ConfigManager
from .registry import ServerRegistry
from .server_manager import GradioMCPServer


class GradioMCPManagementServer:
    """MCP Server for managing Gradio MCP servers"""

    def __init__(self):
        if not HAS_MCP:
            raise ImportError("MCP package is required for server functionality")

        self.config_manager = ConfigManager()
        self.registry = ServerRegistry()
        self.server = Server("gradio-mcp-playground")

        # Register all tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="list_servers",
                    description="List all MCP servers (both Claude Desktop and local)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "description": "Include detailed server information",
                                "default": False,
                            }
                        },
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_server_info",
                    description="Get detailed information about a specific server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the server to get info for",
                            }
                        },
                        "required": ["server_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="get_server_logs",
                    description="Get logs for a specific server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the server to get logs for",
                            },
                            "lines": {
                                "type": "integer",
                                "description": "Number of log lines to retrieve",
                                "default": 50,
                            },
                        },
                        "required": ["server_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="start_local_server",
                    description="Start a local Gradio MCP server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the local server to start",
                            },
                            "port": {
                                "type": "integer",
                                "description": "Port to start the server on",
                                "default": 7860,
                            },
                        },
                        "required": ["server_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="stop_local_server",
                    description="Stop a local Gradio MCP server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the local server to stop",
                            }
                        },
                        "required": ["server_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="create_server",
                    description="Create a new Gradio MCP server from a template",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name for the new server",
                            },
                            "template": {
                                "type": "string",
                                "description": "Template to use for the server",
                                "default": "basic",
                            },
                            "port": {
                                "type": "integer",
                                "description": "Port for the new server",
                                "default": 7860,
                            },
                        },
                        "required": ["server_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="delete_local_server",
                    description="Delete a local Gradio MCP server",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "server_name": {
                                "type": "string",
                                "description": "Name of the local server to delete",
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force deletion without confirmation",
                                "default": False,
                            },
                        },
                        "required": ["server_name"],
                        "additionalProperties": False,
                    },
                ),
                Tool(
                    name="list_templates",
                    description="List available server templates",
                    inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
                ),
                Tool(
                    name="search_registry",
                    description="Search the server registry for templates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "category": {
                                "type": "string",
                                "description": "Category to filter by",
                                "default": "all",
                            },
                        },
                        "additionalProperties": False,
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "list_servers":
                    return await self._list_servers(arguments.get("include_details", False))
                elif name == "get_server_info":
                    return await self._get_server_info(arguments["server_name"])
                elif name == "get_server_logs":
                    return await self._get_server_logs(
                        arguments["server_name"], arguments.get("lines", 50)
                    )
                elif name == "start_local_server":
                    return await self._start_local_server(
                        arguments["server_name"], arguments.get("port", 7860)
                    )
                elif name == "stop_local_server":
                    return await self._stop_local_server(arguments["server_name"])
                elif name == "create_server":
                    return await self._create_server(
                        arguments["server_name"],
                        arguments.get("template", "basic"),
                        arguments.get("port", 7860),
                    )
                elif name == "delete_local_server":
                    return await self._delete_local_server(
                        arguments["server_name"], arguments.get("force", False)
                    )
                elif name == "list_templates":
                    return await self._list_templates()
                elif name == "search_registry":
                    return await self._search_registry(
                        arguments.get("query", ""), arguments.get("category", "all")
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
                )

    async def _list_servers(self, include_details: bool) -> CallToolResult:
        """List all servers"""
        servers = self.config_manager.list_servers()

        if include_details:
            result = {
                "total_servers": len(servers),
                "claude_desktop_servers": len(
                    [s for s in servers if s.get("source") == "claude_desktop"]
                ),
                "local_servers": len([s for s in servers if s.get("source") == "local"]),
                "running_servers": len([s for s in servers if s.get("running")]),
                "servers": servers,
            }
        else:
            result = []
            for server in servers:
                status = "🟢 Running" if server.get("running") else "⚫ Stopped"
                if server.get("errors"):
                    status = "🔴 Error"

                result.append(
                    {
                        "name": server.get("name"),
                        "source": server.get("source", "local"),
                        "status": status,
                        "running": server.get("running", False),
                        "errors": len(server.get("errors", [])),
                    }
                )

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])

    async def _get_server_info(self, server_name: str) -> CallToolResult:
        """Get detailed server information"""
        servers = self.config_manager.list_servers()
        server = None

        for s in servers:
            if s.get("name") == server_name:
                server = s
                break

        if not server:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Server '{server_name}' not found")]
            )

        return CallToolResult(content=[TextContent(type="text", text=json.dumps(server, indent=2))])

    async def _get_server_logs(self, server_name: str, lines: int) -> CallToolResult:
        """Get server logs"""
        servers = self.config_manager.list_servers()
        server = None

        for s in servers:
            if s.get("name") == server_name:
                server = s
                break

        if not server:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Server '{server_name}' not found")]
            )

        logs_content = ""

        if server.get("source") == "claude_desktop":
            # Read Claude Desktop logs
            import os

            if os.name == "nt":
                claude_logs_path = Path.home() / "AppData/Roaming/Claude/logs"
            else:
                # WSL or Linux - try multiple possible usernames
                possible_users = [
                    os.environ.get("USER", ""),
                    os.environ.get("USERNAME", ""),
                    "seanp",  # fallback
                ]

                claude_logs_path = None
                for user in possible_users:
                    if user:
                        logs_path = Path(f"/mnt/c/Users/{user}/AppData/Roaming/Claude/logs")
                        if logs_path.exists():
                            claude_logs_path = logs_path
                            break

                if not claude_logs_path:
                    return CallToolResult(
                        content=[
                            TextContent(type="text", text="Claude Desktop logs directory not found")
                        ]
                    )

            log_file = claude_logs_path / f"mcp-server-{server_name}.log"

            if log_file.exists():
                try:
                    with open(log_file, encoding="utf-8") as f:
                        log_lines = f.readlines()
                        # Show last N lines
                        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                        logs_content = "".join(recent_lines)
                except Exception as e:
                    logs_content = f"Error reading log file: {str(e)}"
            else:
                logs_content = "No log file found for this server"
        else:
            # For local servers, check if there's a log file
            server_path = server.get("path")
            if server_path:
                log_file = Path(server_path).parent / "server.log"
                if log_file.exists():
                    try:
                        with open(log_file, encoding="utf-8") as f:
                            log_lines = f.readlines()
                            recent_lines = (
                                log_lines[-lines:] if len(log_lines) > lines else log_lines
                            )
                            logs_content = "".join(recent_lines)
                    except Exception as e:
                        logs_content = f"Error reading log file: {str(e)}"
                else:
                    logs_content = "No log file found for this local server"
            else:
                logs_content = "Server path not configured"

        return CallToolResult(content=[TextContent(type="text", text=logs_content)])

    async def _start_local_server(self, server_name: str, port: int) -> CallToolResult:
        """Start a local server"""
        server = self.config_manager.get_server(server_name)

        if not server:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Server '{server_name}' not found")]
            )

        if server.get("source") == "claude_desktop":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Cannot start Claude Desktop managed server '{server_name}'",
                    )
                ]
            )

        try:
            server_mgr = GradioMCPServer(Path(server["path"]))
            process = server_mgr.start(port=port)

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Successfully started server '{server_name}' on port {port} (PID: {process.pid})",
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Failed to start server '{server_name}': {str(e)}"
                    )
                ]
            )

    async def _stop_local_server(self, server_name: str) -> CallToolResult:
        """Stop a local server"""
        server = self.config_manager.get_server(server_name)

        if not server:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Server '{server_name}' not found")]
            )

        if server.get("source") == "claude_desktop":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Cannot stop Claude Desktop managed server '{server_name}'",
                    )
                ]
            )

        try:
            server_mgr = GradioMCPServer(Path(server["path"]))
            server_mgr.stop()

            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Successfully stopped server '{server_name}'")
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Failed to stop server '{server_name}': {str(e)}"
                    )
                ]
            )

    async def _create_server(self, server_name: str, template: str, port: int) -> CallToolResult:
        """Create a new server"""
        try:
            # Create server directory
            server_dir = Path.cwd() / server_name

            # Create from template
            server_config = self.registry.create_from_template(
                template, server_name, server_dir, port=port
            )

            # Register server
            self.config_manager.add_server(server_config)

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Successfully created server '{server_name}' from template '{template}' at {server_dir}",
                    )
                ]
            )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Failed to create server '{server_name}': {str(e)}"
                    )
                ]
            )

    async def _delete_local_server(self, server_name: str, force: bool) -> CallToolResult:
        """Delete a local server"""
        server = self.config_manager.get_server(server_name)

        if not server:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Server '{server_name}' not found")]
            )

        if server.get("source") == "claude_desktop":
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Cannot delete Claude Desktop managed server '{server_name}'",
                    )
                ]
            )

        try:
            # Remove from registry
            success = self.config_manager.remove_server(server_name)

            if success:
                # Also delete files if directory exists
                server_directory = server.get("directory")
                if server_directory and Path(server_directory).exists():
                    try:
                        result = GradioMCPServer.delete_server(Path(server_directory), force=force)
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Successfully deleted server '{server_name}': {result['message']}",
                                )
                            ]
                        )
                    except Exception as e:
                        return CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text=f"Server removed from registry but failed to delete files: {str(e)}",
                                )
                            ]
                        )
                else:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Successfully removed server '{server_name}' from registry",
                            )
                        ]
                    )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Failed to remove server '{server_name}' from registry",
                        )
                    ]
                )
        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"Failed to delete server '{server_name}': {str(e)}"
                    )
                ]
            )

    async def _list_templates(self) -> CallToolResult:
        """List available templates"""
        templates = self.registry.list_templates()
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(templates, indent=2))]
        )

    async def _search_registry(self, query: str, category: str) -> CallToolResult:
        """Search the registry"""
        if category == "all":
            category = None

        if query:
            results = self.registry.search(query, category)
        elif category:
            results = self.registry.get_by_category(category)
        else:
            results = self.registry.get_all()

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(results, indent=2))]
        )

    async def run(self):
        """Run the MCP server"""
        # Use the correct MCP stdio server interface
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, {})


async def main():
    """Main entry point for the MCP server"""
    if not HAS_MCP:
        print("Error: MCP package is required. Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    try:
        server = GradioMCPManagementServer()
        await server.run()
    except Exception as e:
        print(f"Error in MCP server: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
