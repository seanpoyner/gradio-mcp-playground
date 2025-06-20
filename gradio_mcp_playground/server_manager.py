"""Gradio MCP Server Manager

Manages creation and configuration of Gradio apps as MCP servers.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Optional imports
try:
    import gradio as gr

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

try:
    from mcp.server import FastMCP

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

try:
    from pydantic import BaseModel

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

    # Create a simple fallback
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class MCPTool(BaseModel):
    """Represents an MCP tool"""

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


class MCPServer:
    """Base MCP Server implementation"""

    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        if not HAS_MCP:
            raise ImportError("MCP package is required for server functionality")
        self.name = name
        self.version = version
        self.description = description
        self.tools: List[MCPTool] = []
        self._server = FastMCP(name=name, instructions=description)

    def tool(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a function as an MCP tool"""

        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or "No description"

            # Extract input schema from function signature
            import inspect

            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                param_type = "string"  # Default type
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"

                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}",
                }

                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            input_schema = {"type": "object", "properties": properties, "required": required}

            # Register tool
            tool = MCPTool(
                name=tool_name,
                description=tool_description,
                input_schema=input_schema,
                handler=func,
            )
            self.tools.append(tool)

            # Register with underlying FastMCP server using its tool decorator
            @self._server.tool(tool_name)
            async def tool_handler(**kwargs):
                return await func(**kwargs)

            return func

        return decorator

    async def run_stdio(self):
        """Run the MCP server using stdio transport"""
        await self._server.run_stdio_async()

    def to_gradio_functions(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to Gradio function definitions"""
        if not HAS_GRADIO:
            raise ImportError("Gradio is required for function conversion")

        functions = []

        for tool in self.tools:
            # Create Gradio-compatible function
            def create_gradio_fn(tool_handler):
                def gradio_fn(**kwargs):
                    # Run async function in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(tool_handler(**kwargs))
                    finally:
                        loop.close()

                return gradio_fn

            functions.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "fn": create_gradio_fn(tool.handler),
                    "inputs": self._schema_to_gradio_inputs(tool.input_schema),
                    "outputs": "text",  # Default output type
                }
            )

        return functions

    def _schema_to_gradio_inputs(self, schema: Dict[str, Any]) -> List[Any]:
        """Convert JSON schema to Gradio input components"""
        if not HAS_GRADIO:
            return []

        inputs = []
        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "string")
            label = prop_schema.get("description", prop_name)

            if prop_type == "string":
                inputs.append(gr.Textbox(label=label))
            elif prop_type == "integer":
                inputs.append(gr.Number(label=label, precision=0))
            elif prop_type == "number":
                inputs.append(gr.Number(label=label))
            elif prop_type == "boolean":
                inputs.append(gr.Checkbox(label=label))
            else:
                # Default to textbox
                inputs.append(gr.Textbox(label=label))

        return inputs


class GradioMCPServer:
    """Enhanced Gradio server with MCP capabilities"""

    def __init__(self, app_path: Optional[Path] = None):
        self.app_path = app_path or Path("app.py")
        self.config = self._load_config()
        self.process: Optional[subprocess.Popen] = None

    def _load_config(self) -> Dict[str, Any]:
        """Load server configuration"""
        config_path = self.app_path.parent / "mcp_config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}

    def create_from_function(self, fn: Callable, **kwargs):
        """Create a Gradio Interface from a function with MCP support"""
        # Extract function metadata
        import inspect

        # Get function signature
        sig = inspect.signature(fn)
        doc = inspect.getdoc(fn) or "No description"

        # Parse docstring for better descriptions
        lines = doc.split("\n")
        description = lines[0] if lines else "No description"

        # Create inputs based on function signature
        inputs = []
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == str:
                    inputs.append(gr.Textbox(label=param_name))
                elif param.annotation == int:
                    inputs.append(gr.Number(label=param_name, precision=0))
                elif param.annotation == float:
                    inputs.append(gr.Number(label=param_name))
                elif param.annotation == bool:
                    inputs.append(gr.Checkbox(label=param_name))
                else:
                    inputs.append(gr.Textbox(label=param_name))
            else:
                inputs.append(gr.Textbox(label=param_name))

        # Create interface
        interface = gr.Interface(
            fn=fn,
            inputs=inputs,
            outputs="text",
            title=kwargs.get("title", fn.__name__),
            description=description,
            **kwargs,
        )

        return interface

    def create_multi_tool_interface(self, tools: List[Dict[str, Any]]):
        """Create a tabbed interface for multiple tools"""
        interfaces = []
        tab_names = []

        for tool in tools:
            interface = gr.Interface(
                fn=tool["fn"],
                inputs=tool.get("inputs", "text"),
                outputs=tool.get("outputs", "text"),
                title=tool["name"],
                description=tool["description"],
            )
            interfaces.append(interface)
            tab_names.append(tool["name"])

        return gr.TabbedInterface(interfaces, tab_names)

    def start(self, port: int = 7860, reload: bool = False, public: bool = False):
        """Start the Gradio MCP server"""
        cmd = [sys.executable, str(self.app_path)]
        env = os.environ.copy()

        # Set Gradio environment variables
        env["GRADIO_SERVER_PORT"] = str(port)
        env["GRADIO_MCP_SERVER"] = "true"

        if reload:
            env["GRADIO_WATCH_DIRS"] = str(self.app_path.parent)
            env["GRADIO_WATCH_RELOAD"] = "true"

        if public:
            env["GRADIO_SHARE"] = "true"

        # Start process in background with suppressed output
        self.process = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(self.app_path.parent),
            stdout=subprocess.DEVNULL,  # Suppress stdout
            stderr=subprocess.DEVNULL,  # Suppress stderr
            stdin=subprocess.DEVNULL,  # No input
            creationflags=(
                subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            ),  # Hide window on Windows
        )

        # Save process info
        self._save_process_info(port)

        return self.process

    def stop(self):
        """Stop the Gradio MCP server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            self._remove_process_info()

    def _save_process_info(self, port: int):
        """Save process information for management"""
        info = {
            "pid": self.process.pid,
            "port": port,
            "started": datetime.now().isoformat(),
            "app_path": str(self.app_path),
        }

        info_path = self.app_path.parent / ".mcp_server.json"
        with open(info_path, "w") as f:
            json.dump(info, f)

    def _remove_process_info(self):
        """Remove process information file"""
        info_path = self.app_path.parent / ".mcp_server.json"
        if info_path.exists():
            info_path.unlink()

    @staticmethod
    def find_running_servers() -> List[Dict[str, Any]]:
        """Find all running Gradio MCP servers"""
        servers = []

        # Look for .mcp_server.json files
        for info_file in Path(".").rglob(".mcp_server.json"):
            try:
                with open(info_file) as f:
                    info = json.load(f)

                # Check if process is still running
                try:
                    os.kill(info["pid"], 0)
                    info["running"] = True
                except OSError:
                    info["running"] = False

                servers.append(info)
            except Exception:
                continue

        return servers

    @staticmethod
    def find_claude_desktop_servers() -> List[Dict[str, Any]]:
        """Find MCP servers managed by Claude Desktop"""
        servers = []

        # Path to Claude Desktop configuration and logs
        # Handle both Windows and WSL paths
        if os.name == "nt":
            # Native Windows
            claude_config_path = Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json"
            claude_logs_path = Path.home() / "AppData/Roaming/Claude/logs"
        else:
            # WSL or Linux - look for Windows user directory
            # Try multiple possible usernames
            possible_users = [
                os.environ.get("USER", ""),
                os.environ.get("USERNAME", ""),
                "seanp",  # fallback
            ]

            claude_config_path = None
            claude_logs_path = None

            for user in possible_users:
                if user:
                    config_path = Path(
                        f"/mnt/c/Users/{user}/AppData/Roaming/Claude/claude_desktop_config.json"
                    )
                    logs_path = Path(f"/mnt/c/Users/{user}/AppData/Roaming/Claude/logs")

                    if config_path.exists():
                        claude_config_path = config_path
                        claude_logs_path = logs_path
                        break

            # If still not found, return empty list
            if not claude_config_path:
                return servers

        if not claude_config_path.exists() or not claude_logs_path.exists():
            return servers

        try:
            # Read Claude Desktop configuration
            with open(claude_config_path) as f:
                config = json.load(f)

            mcp_servers = config.get("mcpServers", {})

            for server_name, server_config in mcp_servers.items():
                server_info = {
                    "name": server_name,
                    "command": server_config.get("command", ""),
                    "args": server_config.get("args", []),
                    "env": server_config.get("env", {}),
                    "source": "claude_desktop",
                    "running": False,
                    "last_seen": None,
                    "errors": [],
                    "status_message": "Unknown",
                }

                # Check server log file for status
                log_file = claude_logs_path / f"mcp-server-{server_name}.log"
                if log_file.exists():
                    status = GradioMCPServer._parse_claude_server_log(log_file)
                    server_info.update(status)

                servers.append(server_info)

        except Exception as e:
            print(f"Error reading Claude Desktop configuration: {e}")

        return servers

    @staticmethod
    def _parse_claude_server_log(log_file: Path) -> Dict[str, Any]:
        """Parse Claude Desktop server log to determine status"""
        status = {"running": False, "last_seen": None, "errors": [], "status_message": "Stopped"}

        try:
            # Read the last 200 lines of the log file for recent status
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
                recent_lines = lines[-200:] if len(lines) > 200 else lines

            # Track timestamped events to determine current state
            last_server_started = None
            last_transport_closed = None
            last_message_activity = None
            last_activity = None
            errors = []

            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue

                # Parse timestamp and message
                if line.startswith("202"):  # Handles 2024, 2025, etc.
                    parts = line.split(" ", 3)
                    if len(parts) >= 4:
                        timestamp_str = parts[0]
                        level = parts[2] if parts[2].startswith("[") else None
                        message = parts[3] if len(parts) > 3 else ""

                        # Parse timestamp
                        try:
                            from datetime import datetime

                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            last_activity = timestamp
                        except:
                            timestamp = None

                        # Track important events with timestamps
                        if timestamp:
                            if "Server started and connected successfully" in message:
                                last_server_started = timestamp
                            elif (
                                "Client transport closed" in message
                                or "Server transport closed" in message
                            ):
                                last_transport_closed = timestamp
                            elif (
                                "Message from server:" in message or "Message to server:" in message
                            ):
                                # Any message activity indicates the server is running
                                last_message_activity = timestamp
                            elif (
                                "Server disconnected" in message or "error" in level.lower()
                                if level
                                else False
                            ):
                                errors.append(message)

            # Determine current status based on the most recent events
            if last_message_activity and last_activity:
                # If we've seen message activity in the last 5 minutes, server is running
                from datetime import datetime, timedelta, timezone

                now = datetime.now(timezone.utc)
                if (now - last_message_activity) < timedelta(minutes=5):
                    status["running"] = True
                    status["status_message"] = "Running"
                else:
                    status["running"] = False
                    status["status_message"] = "Inactive"
            elif last_server_started and last_transport_closed:
                # Compare timestamps to see which event was more recent
                if last_server_started > last_transport_closed:
                    status["running"] = True
                    status["status_message"] = "Running"
                else:
                    status["running"] = False
                    status["status_message"] = "Disconnected"
            elif last_server_started:
                status["running"] = True
                status["status_message"] = "Running"
            elif errors:
                status["running"] = False
                status["status_message"] = "Error"
            else:
                status["running"] = False
                status["status_message"] = "Stopped"

            status["last_seen"] = last_activity.isoformat() if last_activity else None
            status["errors"] = errors[-5:]  # Keep last 5 errors

        except Exception as e:
            status["errors"] = [f"Failed to parse log: {str(e)}"]
            status["status_message"] = "Log Parse Error"

        return status

    @staticmethod
    def create_template_server(template: str, name: str, directory: Path) -> Dict[str, Any]:
        """Create a new server from a template"""
        from .registry import ServerRegistry

        registry = ServerRegistry()
        template_data = registry.get_template(template)

        if not template_data:
            raise ValueError(f"Template '{template}' not found")

        # Create directory
        directory.mkdir(parents=True, exist_ok=True)

        # Copy template files
        for file_name, content in template_data["files"].items():
            file_path = directory / file_name

            # Replace placeholders
            content = content.replace("{{name}}", name)
            content = content.replace("{{description}}", template_data.get("description", ""))

            with open(file_path, "w") as f:
                f.write(content)

        # Create config file
        config = {
            "name": name,
            "template": template,
            "created": datetime.now().isoformat(),
            "version": "1.0.0",
            "tools": template_data.get("tools", []),
        }

        config_path = directory / "mcp_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return config

    @staticmethod
    def validate_server(directory: Path) -> Dict[str, Any]:
        """Validate a Gradio MCP server"""
        results = {"valid": True, "errors": [], "warnings": []}

        # Check for required files
        app_path = directory / "app.py"
        if not app_path.exists():
            results["valid"] = False
            results["errors"].append("Missing app.py file")

        # Check for config
        config_path = directory / "mcp_config.json"
        if not config_path.exists():
            results["warnings"].append("Missing mcp_config.json file")
        else:
            try:
                with open(config_path) as f:
                    config = json.load(f)

                # Validate config structure
                if "name" not in config:
                    results["errors"].append("Config missing 'name' field")
                    results["valid"] = False
            except json.JSONDecodeError:
                results["errors"].append("Invalid JSON in mcp_config.json")
                results["valid"] = False

        # Check for MCP server flag in app.py
        if app_path.exists():
            with open(app_path) as f:
                content = f.read()

            if "mcp_server=True" not in content:
                results["warnings"].append("app.py doesn't seem to enable MCP server")

        return results

    @staticmethod
    def delete_server(directory: Path, force: bool = False) -> Dict[str, Any]:
        """Delete a Gradio MCP server"""
        result = {"success": False, "message": "", "files_removed": [], "process_stopped": False}

        if not directory.exists():
            result["message"] = f"Server directory {directory} does not exist"
            return result

        # Check if server is running and stop it
        info_file = directory / ".mcp_server.json"
        if info_file.exists():
            try:
                with open(info_file) as f:
                    server_info = json.load(f)

                # Try to stop the process
                try:
                    pid = server_info.get("pid")
                    if pid:
                        os.kill(pid, 15)  # SIGTERM
                        result["process_stopped"] = True
                except (OSError, ProcessLookupError):
                    # Process already stopped or doesn't exist
                    pass
            except (OSError, json.JSONDecodeError):
                pass

        # Get list of files to remove
        files_to_remove = list(directory.rglob("*"))

        # Safety check - don't delete if directory contains non-server files
        if not force:
            server_files = {
                ".mcp_server.json",
                "mcp_config.json",
                "app.py",
                "requirements.txt",
                "README.md",
            }
            found_files = {f.name for f in directory.iterdir() if f.is_file()}

            # Check for unexpected files
            unexpected_files = found_files - server_files
            if unexpected_files:
                result["message"] = (
                    f"Directory contains unexpected files: {unexpected_files}. Use --force to delete anyway."
                )
                return result

        # Remove all files and directories
        try:
            import shutil

            # Remove individual files first (for logging)
            for file_path in files_to_remove:
                if file_path.is_file():
                    result["files_removed"].append(str(file_path))

            # Remove the entire directory
            shutil.rmtree(directory)

            result["success"] = True
            result["message"] = f"Server directory {directory} deleted successfully"

        except Exception as e:
            result["message"] = f"Error deleting server directory: {e}"

        return result


def create_simple_mcp_server(fn: Callable, name: str = "gradio-mcp-server"):
    """Create a simple Gradio MCP server from a function"""
    # Extract function metadata
    import inspect

    doc = inspect.getdoc(fn) or "No description"

    # Create and configure interface
    interface = gr.Interface(
        fn=fn,
        inputs="text",  # Default to text input
        outputs="text",  # Default to text output
        title=name,
        description=doc,
    )

    return interface


def launch_mcp_server(interface, port: int = 7860, mcp_server: bool = True, **kwargs) -> None:
    """Launch a Gradio interface as an MCP server"""
    interface.launch(server_port=port, mcp_server=mcp_server, **kwargs)
