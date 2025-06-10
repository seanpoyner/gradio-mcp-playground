"""MCP Server Management Tool for Coding Agent

Provides the coding agent with direct access to gmp CLI commands for server management.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from llama_index.core.tools import FunctionTool

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False

try:
    import gradio as gr  # noqa: F401

    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False


class MCPServerManager:
    """Manages MCP servers through gmp CLI commands"""

    def __init__(self):
        from .prompt_manager import get_prompt_manager

        self.prompt_manager = get_prompt_manager()

    def _get_server_specific_guidance(self, server_id: str, kwargs: dict) -> str:
        """Get server-specific guidance for users"""

        # Special handling for WSL path issues
        if server_id == "obsidian":
            vault_path = kwargs.get("vault_path1", "")
            if vault_path and vault_path.startswith("/mnt/"):
                return "\n" + self.prompt_manager.get_server_guidance(
                    server_id, "wsl_path_issue", vault_path=vault_path
                )

        # Get standard success guidance
        guidance = self.prompt_manager.get_server_guidance(server_id, "success", **kwargs)
        return "\n" + guidance if guidance else ""

    def _get_gmp_path(self) -> str:
        """Get the path to the gmp command"""
        # Try direct execution first (most common case)
        try:
            result = subprocess.run(
                ["gmp", "--version"], capture_output=True, text=True, shell=True
            )
            if result.returncode == 0:
                return "gmp"
        except Exception:
            pass

        # Try which/where command depending on OS
        try:
            which_cmd = "where" if sys.platform == "win32" else "which"
            result = subprocess.run([which_cmd, "gmp"], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]  # Take first result on Windows
        except Exception:
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
        except Exception:
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
                # Check if it's just warnings (common Pydantic warnings)
                stderr_lower = (result.stderr or "").lower()
                stdout_content = result.stdout or ""

                # Handle Pydantic warnings more comprehensively
                if "warning" in stderr_lower and "pydantic" in stderr_lower:
                    # Check if the only error content is Pydantic warnings and "Aborted!"
                    stderr_lines = result.stderr.split("\n") if result.stderr else []
                    non_warning_errors = []
                    for line in stderr_lines:
                        line_lower = line.lower().strip()
                        if (
                            line_lower
                            and not line_lower.startswith(
                                "c:\\programdata\\anaconda3\\lib\\site-packages\\pydantic"
                            )
                            and "userwarning:" not in line_lower
                            and "warnings.warn(" not in line_lower
                            and 'field "model_name" has conflict' not in line_lower
                            and "you may be able to resolve this warning" not in line_lower
                            and line_lower != "aborted!"
                        ):
                            non_warning_errors.append(line)

                    # If only Pydantic warnings and possibly "Aborted!", treat as success for server operations
                    if not non_warning_errors and any(
                        cmd in args for cmd in ["create", "server", "start", "stop"]
                    ):
                        return True, "Command completed successfully (Pydantic warnings ignored)"

                    # If command has stdout content and no real errors
                    if stdout_content.strip() and not any(
                        error_word in stdout_content.lower()
                        for error_word in ["error:", "failed", "traceback"]
                    ):
                        return True, stdout_content

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
            # Add a note about external servers
            output_with_note = (
                output
                + "\n\n💡 Note: Servers marked with source 'Claude Desktop' are managed externally and cannot be modified here."
            )
            return f"📋 Available MCP Servers:\n{output_with_note}"
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
        """Start an MCP server using the proper server management system"""
        try:
            # Get server configuration
            from .config_manager import ConfigManager
            from .server_manager import GradioMCPServer

            config_manager = ConfigManager()
            server_config = config_manager.get_server(name)

            if not server_config:
                # List available servers to help user
                servers = config_manager.list_servers()
                local_servers = [s for s in servers if s.get("source") == "local"]
                if local_servers:
                    available_list = []
                    for server in local_servers:
                        port_info = (
                            f"port {server.get('port', 'N/A')}"
                            if server.get("port")
                            else "no port configured"
                        )
                        available_list.append(f"- {server.get('name')} ({port_info})")
                    available = "\n".join(available_list)
                    return f"❌ Server '{name}' not found in configuration.\n\nAvailable local servers:\n{available}\n\n💡 Suggestion: Use start_mcp_server() with one of the available server names, or use create_mcp_server() to create a new server."
                else:
                    return f"❌ Server '{name}' not found in configuration.\n\nNo local servers available. Use create_mcp_server() to create a new server first.\n\nExample: create_mcp_server(name='basic_server', template='basic', port=7862)"

            # Check if server is managed locally
            if server_config.get("source") != "local":
                return f"❌ Cannot start '{name}': This server is managed by {server_config.get('source', 'external system')} and cannot be started from here.\n\n💡 Tip: Only locally created servers can be started using this command."

            server_directory = server_config.get("directory")
            if not server_directory:
                return "❌ No directory specified in server configuration"

            # Convert relative path to absolute path
            server_path = Path(server_directory)
            if not server_path.is_absolute():
                server_path = Path.cwd() / server_directory

            if not server_path.exists():
                return f"❌ Server directory not found: {server_path}"

            # Determine port - avoid dashboard ports
            if not port:
                configured_port = server_config.get("port", 7862)
                # Check if configured port conflicts with dashboard or other common ports
                dashboard_ports = [7860, 7861, 8080, 8081]
                if configured_port in dashboard_ports:
                    # Find a safe port
                    safe_port = 7862
                    while safe_port in dashboard_ports:
                        safe_port += 1
                    port = safe_port
                    return f"⚠️ Server '{name}' is configured to use port {configured_port}, which may conflict with the dashboard.\n\nSuggested fix: Update the server configuration to use port {safe_port}\n\nRun: create_mcp_server(name='{name}', template='basic', port={safe_port}) to create a new server with a safe port."
                else:
                    port = configured_port

            # Check if app.py exists
            app_path = server_path / "app.py"
            if not app_path.exists():
                return f"❌ Server app.py not found: {app_path}"

            # Use the proper server manager to start the server
            server_manager = GradioMCPServer(app_path)
            process = server_manager.start(port=port)

            # Give it a moment to start
            import time

            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                return f"🚀 Server '{name}' started successfully on port {port}!\n\nProcess ID: {process.pid}\nURL: http://localhost:{port}\n\n✅ Server is running in the background and properly tracked."
            else:
                # Process exited, get error info
                stdout, stderr = process.communicate()
                error_msg = stderr.decode("utf-8", errors="replace") if stderr else "Unknown error"
                return f"❌ Server '{name}' failed to start:\n{error_msg}"

        except Exception as e:
            return f"❌ Failed to start server '{name}': {str(e)}"

    def stop_server(self, name: str) -> str:
        """Stop an MCP server using the proper server management system"""
        try:
            from .config_manager import ConfigManager
            from .server_manager import GradioMCPServer

            config_manager = ConfigManager()
            server_config = config_manager.get_server(name)

            if not server_config:
                return f"❌ Server '{name}' not found in configuration."

            # Check if server is managed locally
            if server_config.get("source") != "local":
                return f"❌ Cannot stop '{name}': This server is managed by {server_config.get('source', 'external system')} and cannot be stopped from here.\n\n💡 Tip: Only locally created servers can be stopped using this command."

            # Safety check: Don't stop servers that might be the dashboard
            server_port = server_config.get("port", 7860)
            dashboard_ports = [7861, 8080, 8081]  # Common dashboard ports

            # Check if this server might be the current dashboard
            if server_port in dashboard_ports:
                return f"🛡️ Safety Protection: Cannot stop server '{name}' on port {server_port} as it may be the dashboard server.\n\nTo stop the dashboard, use Ctrl+C in the terminal where you started 'gmp dashboard'."

            # Additional safety: Check if server is actually the dashboard by looking at its directory
            server_directory = server_config.get("directory", "")
            if "dashboard" in server_directory.lower() or "web_ui" in server_directory.lower():
                return f"🛡️ Safety Protection: Cannot stop server '{name}' as it appears to be a dashboard server.\n\nTo stop the dashboard, use Ctrl+C in the terminal where you started 'gmp dashboard'."

            if not server_directory:
                return "❌ No directory specified in server configuration"

            # Convert relative path to absolute path
            server_path = Path(server_directory)
            if not server_path.is_absolute():
                server_path = Path.cwd() / server_directory

            if not server_path.exists():
                return f"❌ Server directory not found: {server_path}"

            # Check if app.py exists
            app_path = server_path / "app.py"
            if not app_path.exists():
                return f"❌ Server app.py not found: {app_path}"

            # Use the proper server manager to stop the server
            server_manager = GradioMCPServer(app_path)
            server_manager.stop()

            return f"⏹️ Server '{name}' stopped successfully and process tracking updated."

        except Exception as e:
            return f"❌ Failed to stop server '{name}': {str(e)}"

    def delete_server(self, name: str) -> str:
        """Delete an MCP server"""
        # Check if server is managed locally
        from .config_manager import ConfigManager

        config_manager = ConfigManager()
        server_config = config_manager.get_server(name)

        if server_config and server_config.get("source") != "local":
            return f"❌ Cannot delete '{name}': This server is managed by {server_config.get('source', 'external system')} and cannot be deleted from here.\n\n💡 Tip: Only locally created servers can be deleted using this command."

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

    def start_pure_mcp_server(self) -> str:
        """Start a pure MCP server for tool communication (not web interface)"""
        success, output = self._execute_gmp_command(
            ["mcp"], "Start pure MCP server for tool communication"
        )

        if success:
            return f"🔗 Pure MCP server started successfully:\n{output}\n\n💡 This server uses stdio protocol for tool communication, not HTTP.\nConnect to it using the stdio protocol."
        else:
            return f"❌ Failed to start pure MCP server: {output}"

    def install_mcp_server_from_registry(self, server_id: str, **kwargs) -> str:
        """Install an MCP server from the registry

        Args:
            server_id: ID of the server in the registry (e.g., 'filesystem', 'memory', 'github')
            **kwargs: Additional arguments like 'path' for filesystem server, or environment variables

        Returns:
            str: Installation result and connection instructions
        """
        try:
            import os
            import platform
            import sys

            from .registry import ServerRegistry
            from .secure_storage import SecureTokenStorage
            from .path_translator import PathTranslator

            registry = ServerRegistry()
            storage = SecureTokenStorage()
            path_translator = PathTranslator()

            # Get server info from registry
            server_info = registry.get_server_info(server_id)
            if not server_info:
                return f"❌ Server '{server_id}' not found in registry"

            # Check for stored API keys first
            stored_keys = storage.retrieve_server_keys(server_id)

            # Special handling for environment variables passed as arguments
            # For brave-search, convert 'token' to 'BRAVE_API_KEY'
            if server_id == "brave-search":
                if "token" in kwargs:
                    kwargs["BRAVE_API_KEY"] = kwargs.pop("token")
                    # Store the key securely
                    storage.store_key("brave-search", "BRAVE_API_KEY", kwargs["BRAVE_API_KEY"])
                elif "BRAVE_API_KEY" in stored_keys:
                    # Use stored key
                    kwargs["BRAVE_API_KEY"] = stored_keys["BRAVE_API_KEY"]

            elif server_id == "github":
                if "token" in kwargs:
                    kwargs["GITHUB_TOKEN"] = kwargs.pop("token")
                    # Store the key securely
                    storage.store_key("github", "GITHUB_TOKEN", kwargs["GITHUB_TOKEN"])
                elif "GITHUB_TOKEN" in stored_keys:
                    # Use stored key
                    kwargs["GITHUB_TOKEN"] = stored_keys["GITHUB_TOKEN"]

            # Process and translate paths in kwargs
            for key, value in list(kwargs.items()):
                if key in ["path", "vault_path1", "vault_path2"] and isinstance(value, str):
                    # Replace generic paths with actual environment paths
                    if value == "/home/user" or value == "/home/user/":
                        value = os.path.expanduser("~")
                    elif value == "/home/user/workspace":
                        value = os.path.join(os.path.expanduser("~"), "workspace")
                    elif value.startswith("/home/user/"):
                        # Replace /home/user/ with actual home directory
                        relative_path = value[len("/home/user/"):]
                        value = os.path.join(os.path.expanduser("~"), relative_path)
                    
                    # Translate paths for cross-platform compatibility
                    kwargs[key] = path_translator.translate_path(value)

            # Auto-detect and set default arguments for specific servers
            if server_id == "filesystem" and "path" not in kwargs:
                # Auto-detect home directory based on OS
                home_path = os.path.expanduser("~")
                kwargs["path"] = path_translator.translate_path(home_path)
                auto_detected_path = True
            else:
                auto_detected_path = False

            # Create directory for memory server if needed
            if server_id == "memory":
                memory_dir = os.path.join(os.path.expanduser("~"), ".memory_server_bin")
                if not os.path.exists(memory_dir):
                    os.makedirs(memory_dir, exist_ok=True)
                    print(f"Created memory server directory: {memory_dir}")

            # Generate install command with user arguments (including auto-detected ones)
            install_config = registry.generate_install_command(server_id, kwargs)
            if not install_config:
                required_args = server_info.get("required_args", [])
                if required_args:
                    missing_args = [arg for arg in required_args if arg not in kwargs]
                    if missing_args:
                        # Special handling for servers that need API keys
                        if (
                            server_id == "brave-search"
                            and "token" not in kwargs
                            and "BRAVE_API_KEY" not in kwargs
                        ):
                            return f"❌ Missing required arguments: {missing_args}\n\nExample for {server_id}:\n{server_info['setup_help']}\n\n🔑 **API Key Required**\n\nTo use Brave Search, you need an API key:\n1. Get your free API key from https://brave.com/search/api/\n2. Install with: install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY')"
                        elif (
                            server_id == "github"
                            and "token" not in kwargs
                            and "GITHUB_TOKEN" not in kwargs
                        ):
                            return f"❌ Missing required arguments: {missing_args}\n\nExample for {server_id}:\n{server_info['setup_help']}\n\n🔑 **GitHub Token Required**\n\nTo use GitHub server, you need a personal access token:\n1. Create a token at https://github.com/settings/tokens\n2. Install with: install_mcp_server_from_registry(server_id='github', token='YOUR_TOKEN')"
                        else:
                            return f"❌ Missing required arguments: {missing_args}\n\nExample for {server_id}:\n{server_info['setup_help']}"
                return f"❌ Failed to generate install command for '{server_id}'"

            # Execute installation
            if install_config["install_method"] == "npm":
                # Use npx to install and run npm packages
                cmd = [install_config["command"]] + install_config["args"]
                cmd_str = " ".join(cmd)

                # Add auto-detected path info if applicable
                path_info = ""
                if server_id == "filesystem" and auto_detected_path:
                    path_info = f"\n**🏠 Auto-detected Home Directory:** {kwargs['path']}"

                # Automatically start the server as a subprocess
                try:
                    import subprocess
                    import time

                    # Set up environment variables if needed
                    env = os.environ.copy()
                    for k, v in install_config["env"].items():
                        env[k] = v

                    # Start the server process
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,  # Important for stdio servers
                        env=env,
                        shell=True if sys.platform == "win32" else False,
                    )

                    # Give it a moment to start
                    time.sleep(1)

                    # For stdio servers, check if they printed their startup message
                    if server_id in ["memory", "filesystem", "github", "obsidian", "time"]:
                        # These are stdio servers - check for startup output
                        import os
                        import select

                        # Non-blocking read of stdout
                        if sys.platform != "win32":
                            # Unix-like systems
                            ready, _, _ = select.select([process.stdout], [], [], 0.1)
                            if ready:
                                output = process.stdout.read(1024).decode("utf-8", errors="replace")
                                if (
                                    "running on stdio" in output.lower()
                                    or "server" in output.lower()
                                ):
                                    # Server started successfully
                                    process_is_running = True
                                else:
                                    process_is_running = process.poll() is None
                            else:
                                process_is_running = process.poll() is None
                        else:
                            # Windows - just check if process is alive
                            process_is_running = process.poll() is None
                    else:
                        process_is_running = process.poll() is None

                    # Check if process is running
                    if process_is_running:
                        # Process is running
                        # Store process info for later connection
                        if not hasattr(self, "_running_mcp_servers"):
                            self._running_mcp_servers = {}

                        self._running_mcp_servers[server_id] = {
                            "process": process,
                            "command": cmd_str,
                            "pid": process.pid,
                        }

                        # Save server configuration
                        from .mcp_server_config import MCPServerConfig

                        mcp_config = MCPServerConfig()

                        # For registry servers, we need to store the command and args
                        # Extract command and args from cmd list
                        if len(cmd) > 0:
                            server_command = cmd[0]
                            server_args = cmd[1:] if len(cmd) > 1 else []
                        else:
                            server_command = install_config["command"]
                            server_args = install_config["args"]

                        # Save the server configuration
                        mcp_config.add_server(
                            name=server_id,
                            command=server_command,
                            args=server_args,
                            env=install_config.get("env", {}),
                        )
                        print(f"Saved {server_id} configuration to MCP servers config")

                        # Add connection to coding agent if available
                        try:
                            # Set environment variable for the agent to use
                            if server_id == "brave-search" and "BRAVE_API_KEY" in env:
                                os.environ["BRAVE_API_KEY"] = env["BRAVE_API_KEY"]
                            elif server_id == "github" and "GITHUB_TOKEN" in env:
                                os.environ["GITHUB_TOKEN"] = env["GITHUB_TOKEN"]

                            # Get global coding agent instance if available
                            import gradio_mcp_playground.web_ui as web_ui

                            if hasattr(web_ui, "coding_agent") and web_ui.coding_agent:
                                # Use the subprocess-based MCP client for better compatibility
                                from .mcp_working_client import (
                                    MCPServerProcess,
                                    create_mcp_tools_for_server,
                                )

                                # Properly separate command and args
                                if len(cmd) > 0:
                                    actual_command = cmd[0]
                                    actual_args = cmd[1:] if len(cmd) > 1 else []
                                else:
                                    actual_command = install_config["command"]
                                    actual_args = install_config["args"]

                                # Create server process
                                server = MCPServerProcess(
                                    server_id, actual_command, actual_args, env
                                )

                                if server.start() and server.initialize():
                                    # Create tools
                                    server_tools = create_mcp_tools_for_server(server)

                                    if server_tools:
                                        # Add tools to agent
                                        web_ui.coding_agent.tools.extend(server_tools)

                                        # Store tools and server
                                        if not hasattr(web_ui.coding_agent, "mcp_tools"):
                                            web_ui.coding_agent.mcp_tools = {}
                                        web_ui.coding_agent.mcp_tools[server_id] = server_tools

                                        if not hasattr(web_ui.coding_agent, "_mcp_servers"):
                                            web_ui.coding_agent._mcp_servers = {}
                                        web_ui.coding_agent._mcp_servers[server_id] = server

                                        # Recreate agent with new tools
                                        if web_ui.coding_agent.is_configured():
                                            web_ui.coding_agent._recreate_agent_with_mcp_tools()

                                        print(
                                            f"✅ {len(server_tools)} tools registered for {server_id}"
                                        )

                                        # List the tool names
                                        tool_names = [
                                            tool.name
                                            for tool in server_tools
                                            if hasattr(tool, "name")
                                        ]
                                        print(f"   Available tools: {', '.join(tool_names)}")
                                    else:
                                        print(f"⚠️ No tools created for {server_id}")
                                        server.stop()
                                else:
                                    print(f"⚠️ Failed to initialize {server_id} server")
                        except Exception as e:
                            print(f"Could not add tools to coding agent: {e}")
                            import traceback

                            traceback.print_exc()

                        return f"""✅ MCP Server '{server_id}' started automatically!{path_info}

**🚀 Server Running:**
- Process ID: {process.pid}
- Command: `{cmd_str}`
- Status: Running in background for external MCP clients

**📝 Server Status:**
- Process running in background (PID: {process.pid})
- Tools are being connected to this chat interface
- **To stop the server:** Use stop_mcp_registry_server('{server_id}')

**🔌 For Claude Desktop users:**
Add this to your Claude Desktop config:
```json
{{
  "{server_id}": {{
    "command": "{cmd_str.replace('"', '\\"')}"
  }}
}}
```

**Description:** {server_info.get('description', server_info.get('example_usage', 'No description available'))}

{self._get_server_specific_guidance(server_id, kwargs)}
"""
                    else:
                        # Process exited, check why
                        stdout, stderr = process.communicate()
                        stdout_msg = stdout.decode("utf-8", errors="replace") if stdout else ""
                        stderr_msg = stderr.decode("utf-8", errors="replace") if stderr else ""

                        # Check if it's a stdio server's normal startup message
                        stdio_servers = [
                            "memory",
                            "filesystem",
                            "github",
                            "obsidian",
                            "time",
                            "brave-search",
                        ]
                        if (
                            server_id in stdio_servers
                            and (
                                "running on stdio" in stdout_msg.lower()
                                or "server" in stdout_msg.lower()
                            )
                            and not stderr_msg
                        ):
                            # This is actually a successful start - stdio server just printed and is waiting
                            # We need to restart it properly with stdin
                            process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,  # Important for stdio servers
                                env=env,
                                shell=True if sys.platform == "win32" else False,
                            )

                            # Store the process
                            if not hasattr(self, "_running_mcp_servers"):
                                self._running_mcp_servers = {}

                            self._running_mcp_servers[server_id] = {
                                "process": process,
                                "command": cmd_str,
                                "pid": process.pid,
                            }

                            # Save configuration (duplicate code but needed here)
                            from .mcp_server_config import MCPServerConfig

                            mcp_config = MCPServerConfig()

                            if len(cmd) > 0:
                                server_command = cmd[0]
                                server_args = cmd[1:] if len(cmd) > 1 else []
                            else:
                                server_command = install_config["command"]
                                server_args = install_config["args"]

                            mcp_config.add_server(
                                name=server_id,
                                command=server_command,
                                args=server_args,
                                env=install_config.get("env", {}),
                            )

                            return f"""✅ MCP Server '{server_id}' started successfully!

**🚀 Server Running:**
- Process ID: {process.pid}
- Command: `{cmd_str}`
- Status: Running (stdio protocol)

**📝 Note:** This is a stdio-based MCP server. It communicates via standard input/output.

{self._get_server_specific_guidance(server_id, kwargs)}
"""

                        # Otherwise it's a real error
                        error_msg = stderr_msg or stdout_msg or "Unknown error"
                        return f"""❌ Failed to start MCP Server '{server_id}'

**Error:** {error_msg}

**Command attempted:** `{cmd_str}`

**💡 Troubleshooting:**
1. Ensure npx is installed: `npm install -g npx`
2. Check if the package exists: `npm view {install_config['package']}`
3. Try running manually: `{cmd_str}`
"""

                except Exception as e:
                    return f"""❌ Error starting MCP Server '{server_id}': {str(e)}

**Command:** `{cmd_str}`

**💡 Try installing Node.js/npm if not already installed.**
"""

            elif install_config["install_method"] == "uvx":
                cmd = [install_config["command"]] + install_config["args"]
                cmd_str = " ".join(cmd)

                # Add auto-detected path info if applicable
                path_info = ""
                if server_id == "filesystem" and auto_detected_path:
                    path_info = f"\n**🏠 Auto-detected Home Directory:** {kwargs['path']}"

                return f"""✅ MCP Server '{server_id}' installation ready!{path_info}

**Installation Command:**
```
{cmd_str}
```

**Prerequisites:** Install uvx first with `pip install uvx`

**Connection Instructions:**
1. Run the command above (it will install and start the server)
2. Connect using stdio protocol with the same command

**Environment Variables Needed:**
{chr(10).join([f"- {k}: {v}" for k, v in install_config['env'].items()]) if install_config['env'] else "None"}

**Usage:** {server_info['example_usage']}
"""

            else:
                return f"❌ Install method '{install_config['install_method']}' not yet supported"

        except Exception as e:
            return f"❌ Error installing server '{server_id}': {str(e)}"

    def stop_mcp_registry_server(self, server_id: str) -> str:
        """Stop a running MCP registry server

        Args:
            server_id: ID of the server to stop

        Returns:
            str: Result of stopping the server
        """
        stopped_subprocess = False
        stopped_agent_server = False

        # Check subprocess tracking
        if hasattr(self, "_running_mcp_servers") and server_id in self._running_mcp_servers:
            try:
                server_info = self._running_mcp_servers[server_id]
                process = server_info["process"]

                # Terminate the process
                process.terminate()

                # Wait a bit for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    process.wait()

                # Remove from running servers
                del self._running_mcp_servers[server_id]
                stopped_subprocess = True

            except Exception as e:
                return f"❌ Error stopping server subprocess '{server_id}': {str(e)}"

        # Also check coding agent for MCP servers
        try:
            import gradio_mcp_playground.web_ui as web_ui

            if hasattr(web_ui, "coding_agent") and web_ui.coding_agent:
                if (
                    hasattr(web_ui.coding_agent, "_mcp_servers")
                    and server_id in web_ui.coding_agent._mcp_servers
                ):
                    server = web_ui.coding_agent._mcp_servers[server_id]
                    server.stop()

                    # Remove from agent tracking
                    del web_ui.coding_agent._mcp_servers[server_id]

                    # Remove tools
                    if (
                        hasattr(web_ui.coding_agent, "mcp_tools")
                        and server_id in web_ui.coding_agent.mcp_tools
                    ):
                        del web_ui.coding_agent.mcp_tools[server_id]

                    # Recreate agent without these tools
                    if web_ui.coding_agent.is_configured():
                        web_ui.coding_agent._recreate_agent_with_mcp_tools()

                    stopped_agent_server = True

        except Exception as e:
            if not stopped_subprocess:
                return f"❌ Error accessing coding agent: {str(e)}"

        if stopped_subprocess or stopped_agent_server:
            sources = []
            if stopped_subprocess:
                sources.append("subprocess manager")
            if stopped_agent_server:
                sources.append("coding agent")

            return f"""⏹️ MCP Server '{server_id}' stopped successfully!

**Stopped from:** {' and '.join(sources)}
**Server ID:** {server_id}
"""
        else:
            return f"❌ Server '{server_id}' is not running or was not started by this session"

    def create_and_start_server(
        self, name: str, template: str = "basic", port: Optional[int] = None
    ) -> str:
        """Create a new server and start it immediately with safe defaults"""
        try:
            # Use safe default port
            if not port:
                port = 7862

            # First create the server
            create_result = self.create_server(name, template, port)
            if "❌" in create_result:
                return create_result

            # Then start it
            start_result = self.start_server(name, port)

            return f"{create_result}\n\n{start_result}"

        except Exception as e:
            return f"❌ Failed to create and start server '{name}': {str(e)}"

    def connect_client(self, url: str, name: Optional[str] = None, protocol: str = "stdio") -> str:
        """Connect to an MCP server as a client

        Note: This connects to pure MCP servers, not Gradio web interfaces.
        For Gradio servers, use test_gradio_server() instead.
        """
        # Ensure protocol is valid (stdio or sse only)
        if protocol == "auto":
            protocol = "stdio"  # Default to stdio
        elif protocol not in ["stdio", "sse"]:
            protocol = "stdio"

        # Check if this looks like a Gradio HTTP server URL
        if url.startswith("http://") or url.startswith("https://"):
            return f"⚠️ Warning: '{url}' appears to be an HTTP URL.\n\nFor Gradio web servers:\n- Use test_gradio_server_http() to test HTTP connectivity\n- The web interface is accessible in your browser\n\nFor MCP tool communication:\n- Use start_pure_mcp_server() to start a pure MCP server\n- Then connect using stdio protocol"

        args = ["client", "connect", url, "--protocol", protocol]
        if name:
            args.extend(["--name", name])

        success, output = self._execute_gmp_command(
            args, f"Connect to MCP server at '{url}' using {protocol}"
        )

        if success:
            return f"🔗 Connected to server at '{url}' using {protocol} protocol:\n{output}"
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
        # Since 'gmp client test' doesn't exist, we'll provide guidance instead
        if url.startswith("http"):
            return self.test_gradio_server(url)
        else:
            return f"""ℹ️ MCP Server Connection Info for '{url}':

MCP servers using stdio protocol cannot be tested directly from this interface.
They are designed for external MCP clients like Claude Desktop.

**To use this server:**
1. Ensure the server is running (check with 'list_mcp_servers')
2. Configure your MCP client (e.g., Claude Desktop) with the server command
3. The client will handle the stdio communication

**Note:** This is not a limitation - it's how MCP servers are designed to work!"""

    def test_gradio_server(self, url: str) -> str:
        """Test HTTP connection to a Gradio server"""
        try:
            import requests

            # Test basic HTTP connectivity
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # Check if it's a Gradio server
                content = response.text.lower()
                if "gradio" in content:
                    return f"✅ Gradio server at '{url}' is accessible!\n\n🌐 Web interface: {url}\n📊 HTTP Status: {response.status_code}\n🎯 Server Type: Gradio Web Interface\n\n💡 Note: For MCP tool connections, use 'gmp mcp' to start a pure MCP server."
                else:
                    return f"✅ HTTP server at '{url}' is accessible (Status: {response.status_code})\n⚠️ However, this doesn't appear to be a Gradio server."
            else:
                return f"❌ HTTP server returned status {response.status_code} for '{url}'"

        except requests.exceptions.ConnectionError:
            return f"❌ Cannot connect to '{url}' - server may not be running or URL is incorrect"
        except requests.exceptions.Timeout:
            return f"❌ Connection to '{url}' timed out"
        except Exception as e:
            return f"❌ Error testing connection to '{url}': {str(e)}"

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

    import os
    
    manager = get_mcp_manager()
    
    # Import path translator for preprocessing paths
    from .path_translator import PathTranslator
    path_translator = PathTranslator()
    
    def preprocess_path(path: str) -> str:
        """Preprocess paths to replace generic placeholders with actual paths"""
        if not path:
            return path
            
        # Replace generic paths with actual environment paths
        if path == "/home/user" or path == "/home/user/":
            path = os.path.expanduser("~")
        elif path == "/home/user/workspace":
            path = os.path.join(os.path.expanduser("~"), "workspace")
        elif path.startswith("/home/user/"):
            # Replace /home/user/ with actual home directory
            relative_path = path[len("/home/user/"):]
            path = os.path.join(os.path.expanduser("~"), relative_path)
        
        # Translate paths for cross-platform compatibility
        return path_translator.translate_path(path)

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

        Note: Only locally created servers can be stopped. External servers
        (e.g., Claude Desktop servers) cannot be stopped through this command.

        Args:
            name: Name of the server to stop

        Returns:
            str: Result of stopping the server
        """
        return manager.stop_server(name)

    def delete_mcp_server(name: str) -> str:
        """Delete an MCP server and its files.

        Note: Only locally created servers can be deleted. External servers
        (e.g., Claude Desktop servers) cannot be deleted through this command.

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
    def connect_to_mcp_server(url: str, name: str = None, protocol: str = "stdio") -> str:
        """Connect to an MCP server as a client.

        Args:
            url: URL of the MCP server to connect to
            name: Optional name for the connection
            protocol: Communication protocol to use (stdio, sse)

        Returns:
            str: Result of connection attempt
        """
        return manager.connect_client(url, name, protocol)

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

    def test_gradio_server_http(url: str) -> str:
        """Test HTTP connection to a Gradio web server.

        Args:
            url: HTTP URL of the Gradio server (e.g., http://localhost:7860)

        Returns:
            str: Result of HTTP connection test
        """
        return manager.test_gradio_server(url)

    def get_mcp_help(command: str = None) -> str:
        """Get help for MCP server management commands.

        Args:
            command: Optional specific command to get help for

        Returns:
            str: Help information
        """
        return manager.get_help(command)

    def start_pure_mcp_server() -> str:
        """Start a pure MCP server for tool communication (not web interface).

        Returns:
            str: Result of starting the pure MCP server
        """
        return manager.start_pure_mcp_server()

    def install_mcp_server_from_registry(
        server_id: str,
        token: str = None,
        path: str = None,
        timezone: str = None,
        vault_path1: str = None,
        vault_path2: str = None,
    ) -> str:
        """Install an MCP server from the registry and automatically start it.

        Args:
            server_id: ID of the server to install (e.g., 'filesystem', 'memory', 'github', 'brave-search', 'obsidian')
            token: API token for servers that require authentication (brave-search, github)
            path: Path parameter for filesystem server (optional, defaults to home directory)
            timezone: Timezone for time server (e.g., 'UTC', 'America/New_York')
            vault_path1: Primary vault path for Obsidian server
            vault_path2: Secondary vault path for Obsidian server (optional)

        Returns:
            str: Server status and connection information
        """
        # Build kwargs from explicit parameters
        kwargs = {}
        if token is not None:
            kwargs["token"] = token
        if path is not None:
            kwargs["path"] = preprocess_path(path)
        if timezone is not None:
            kwargs["timezone"] = timezone
        if vault_path1 is not None:
            kwargs["vault_path1"] = preprocess_path(vault_path1)
        if vault_path2 is not None:
            kwargs["vault_path2"] = preprocess_path(vault_path2)

        return manager.install_mcp_server_from_registry(server_id, **kwargs)

    def stop_mcp_registry_server(server_id: str) -> str:
        """Stop a running MCP registry server that was started by install_mcp_server_from_registry.

        Args:
            server_id: ID of the server to stop (e.g., 'filesystem', 'memory', 'github')

        Returns:
            str: Result of stopping the server
        """
        return manager.stop_mcp_registry_server(server_id)

    def create_and_start_mcp_server(name: str, template: str = "basic", port: int = None) -> str:
        """Create a new MCP server and start it immediately with safe defaults.

        Args:
            name: Name for the new server
            template: Template to use (basic, calculator, multi-tool, image-generator)
            port: Optional port number (defaults to 7862 for safety)

        Returns:
            str: Result of creating and starting the server
        """
        return manager.create_and_start_server(name, template, port)

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
            FunctionTool.from_defaults(fn=test_gradio_server_http, name="test_gradio_server_http"),
            FunctionTool.from_defaults(fn=start_pure_mcp_server, name="start_pure_mcp_server"),
            FunctionTool.from_defaults(
                fn=create_and_start_mcp_server, name="create_and_start_mcp_server"
            ),
            FunctionTool.from_defaults(
                fn=install_mcp_server_from_registry, name="install_mcp_server_from_registry"
            ),
            FunctionTool.from_defaults(
                fn=stop_mcp_registry_server, name="stop_mcp_registry_server"
            ),
            # Help tools
            FunctionTool.from_defaults(fn=get_mcp_help, name="get_mcp_help"),
        ]
    )

    return tools
