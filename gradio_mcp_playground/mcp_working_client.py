"""Working MCP Client Implementation

This module provides a working MCP client that handles server startup correctly.
"""

import json
import logging
import subprocess
import time
from queue import Queue
from threading import Thread
from typing import Any, Dict, List, Optional

from .path_translator import translate_server_config

logger = logging.getLogger(__name__)

try:
    from llama_index.core.tools import FunctionTool

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False


class MCPServerProcess:
    """Manages an MCP server process with proper startup handling"""

    def __init__(
        self, server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ):
        self.server_id = server_id

        # Translate paths in the server configuration
        config = translate_server_config({"command": command, "args": args, "env": env or {}})

        self.command = config.get("command", command)
        self.args = config.get("args", args)
        self.env = config.get("env", env or {})

        self.process = None
        self.tools = {}
        self._request_id = 0
        self._pending_requests = {}
        self._stdout_queue = Queue()
        self._reader_thread = None
        self._stderr_thread = None

    def start(self) -> bool:
        """Start the server process"""
        try:
            # Prepare environment
            import os
            import platform
            import shutil

            process_env = os.environ.copy()
            process_env.update(self.env)
            process_env["NODE_NO_WARNINGS"] = "1"

            # Handle command resolution
            command = self.command
            args = self.args

            # For npx, try to find it in PATH first
            if command == "npx":
                npx_path = shutil.which("npx") or shutil.which("npx.cmd")
                if npx_path:
                    command = npx_path
                else:
                    # On Windows, try common locations
                    if platform.system() == "Windows" or os.path.exists("/mnt/c"):
                        npx_locations = [
                            "C:\\Program Files\\nodejs\\npx.cmd",
                            "C:\\Program Files (x86)\\nodejs\\npx.cmd",
                            os.path.expanduser("~\\AppData\\Roaming\\npm\\npx.cmd"),
                            "/mnt/c/Program Files/nodejs/npx.cmd",
                            "/mnt/c/Program Files (x86)/nodejs/npx.cmd",
                        ]

                        for loc in npx_locations:
                            if os.path.exists(loc):
                                command = loc
                                break
                        else:
                            logger.error(
                                f"npx not found for {self.server_id}. Please install Node.js."
                            )
                            return False

            logger.info(f"Starting {self.server_id} with command: {command} {' '.join(args)}")

            # Start process
            try:
                self.process = subprocess.Popen(
                    [command] + args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,  # Capture stderr for debugging
                    env=process_env,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=0,
                )
            except FileNotFoundError:
                logger.error(f"Command not found: {command}")
                return False

            # Start reader thread
            self._reader_thread = Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()

            # Also start stderr reader for debugging
            self._stderr_thread = Thread(target=self._read_stderr, daemon=True)
            self._stderr_thread.start()

            # Wait for process to be ready
            time.sleep(2.0)  # Give more time for Node.js to start

            # Check if still running
            if self.process.poll() is not None:
                logger.error(f"Server {self.server_id} exited immediately")
                # Try to get stderr output for debugging
                try:
                    _, stderr = self.process.communicate(timeout=0.1)
                    if stderr:
                        logger.error(f"Server {self.server_id} stderr: {stderr}")
                except Exception:
                    pass
                return False

            logger.info(f"Started {self.server_id} server")
            return True

        except Exception as e:
            logger.error(f"Failed to start {self.server_id}: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _read_output(self):
        """Read JSON-RPC output from server"""
        while True:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if line and line.startswith("{"):
                    try:
                        msg = json.loads(line)
                        # Handle response
                        if "id" in msg and msg["id"] in self._pending_requests:
                            self._pending_requests[msg["id"]].put(msg)
                    except json.JSONDecodeError:
                        logger.debug(f"Invalid JSON: {line}")

            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break

    def _read_stderr(self):
        """Read stderr output for debugging"""
        while True:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break

                line = line.strip()
                if line:
                    # Log stderr but don't treat as errors unless they're actual errors
                    if "error" in line.lower() or "exception" in line.lower():
                        logger.error(f"{self.server_id} stderr: {line}")
                    else:
                        logger.debug(f"{self.server_id} stderr: {line}")
            except Exception as e:
                logger.debug(f"Error reading stderr: {e}")
                break

    def _send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send a JSON-RPC request and wait for response"""
        if not self.process or self.process.poll() is not None:
            raise Exception(f"Server {self.server_id} not running")

        # Create request
        self._request_id += 1
        request_id = self._request_id
        request = {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}

        # Create response queue
        response_queue = Queue()
        self._pending_requests[request_id] = response_queue

        try:
            # Send request
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str)
            self.process.stdin.flush()

            # Wait for response
            response = response_queue.get(timeout=5.0)

            if "error" in response:
                raise Exception(f"Server error: {response['error']}")

            return response.get("result", {})

        finally:
            # Clean up
            if request_id in self._pending_requests:
                del self._pending_requests[request_id]

    def initialize(self) -> bool:
        """Initialize the server connection"""
        try:
            result = self._send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "gradio-mcp", "version": "1.0"},
                },
            )

            logger.info(f"Initialized {self.server_id}: {result.get('serverInfo', {})}")

            # Get tools
            tools_result = self._send_request("tools/list", {})
            self.tools = {}

            for tool in tools_result.get("tools", []):
                self.tools[tool["name"]] = tool

            logger.info(f"Found {len(self.tools)} tools in {self.server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize {self.server_id}: {e}")
            return False

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on this server"""
        try:
            result = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
            return result
        except Exception as e:
            return {"error": str(e)}

    def stop(self):
        """Stop the server process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.process = None


def create_mcp_tools_for_server(server: MCPServerProcess) -> List[Any]:
    """Create LlamaIndex tools for an MCP server"""
    if not HAS_LLAMAINDEX:
        return []

    tools = []

    # Maximum output size to prevent token limit issues
    MAX_OUTPUT_LENGTH = 15000  # Conservative limit to stay well under 32k tokens
    TRUNCATION_MESSAGE = "\n\n... (output truncated to prevent token limit overflow)"

    for tool_name, tool_info in server.tools.items():
        # Create wrapper function
        def make_wrapper(srv, name, info):
            def wrapper(**kwargs):
                """MCP tool wrapper"""
                # Special handling for puppeteer_screenshot to ensure path is correct
                if name == "puppeteer_screenshot" and "name" in kwargs:
                    # Ensure the screenshot name/path uses Windows paths in WSL
                    from .environment_config import get_environment_info
                    env_info = get_environment_info()
                    
                    screenshot_name = kwargs["name"]
                    # If no path is specified, save to home directory
                    if not any(sep in screenshot_name for sep in ['/', '\\']):
                        if 'wsl' in env_info and 'windows_user_home' in env_info['wsl']:
                            # Use Windows home directory for screenshots
                            windows_home = env_info['wsl']['windows_user_home']
                            screenshot_name = f"{windows_home}\\{screenshot_name}"
                            kwargs["name"] = screenshot_name
                            logger.info(f"Puppeteer screenshot will be saved to: {screenshot_name}")
                
                # Translate paths in arguments if needed
                translated_kwargs = {}
                for key, value in kwargs.items():
                    # Check if this argument might be a path
                    if isinstance(value, str) and (
                        # Common path-related parameter names
                        "path" in key.lower()
                        or "file" in key.lower()
                        or "dir" in key.lower()
                        or "folder" in key.lower()
                        or "location" in key.lower()
                        # Check if value looks like a path
                        or value.startswith("C:\\")
                        or value.startswith("c:\\")
                        or value.startswith("/mnt/")
                        or value.startswith("/home/")
                        or value.startswith("/")  # Any absolute path
                        or "\\" in value
                    ):
                        # Handle generic paths that models might use
                        generic_paths = ["/home/user/", "~/", "/tmp/"]
                        for generic_path in generic_paths:
                            if value.startswith(generic_path):
                                # Replace generic paths with actual Windows home
                                from .environment_config import get_environment_info
                                env_info = get_environment_info()
                                if 'wsl' in env_info and 'windows_user_home' in env_info['wsl']:
                                    # Use Windows home directory
                                    windows_home = env_info['wsl']['windows_user_home']
                                    if generic_path == "/tmp/":
                                        # Use Windows temp directory
                                        value = value.replace(generic_path, windows_home + "\\temp\\")
                                    elif generic_path == "~/":
                                        # Replace ~/ with Windows home, preserving the rest of the path
                                        value = value.replace("~/", windows_home + "\\").replace("/", "\\")
                                    else:
                                        value = value.replace(generic_path.rstrip("/"), windows_home).replace("/", "\\")
                                    logger.info(f"Replaced generic path for {srv.server_id}.{name}: {generic_path} -> {windows_home}")
                                elif env_info['os']['is_windows']:
                                    # Native Windows
                                    windows_home = env_info['paths']['home']
                                    if generic_path == "/tmp/":
                                        value = value.replace(generic_path, windows_home + "\\temp\\")
                                    elif generic_path == "~/":
                                        # Replace ~/ with Windows home, preserving the rest of the path
                                        value = value.replace("~/", windows_home + "\\").replace("/", "\\")
                                    else:
                                        value = value.replace(generic_path.rstrip("/"), windows_home).replace("/", "\\")
                                break

                        # Translate the path
                        from .path_translator import translate_path
                        translated_value = translate_path(value)
                        if translated_value != value:
                            logger.info(f"Translated path for {srv.server_id}.{name}: {value} -> {translated_value}")
                        translated_kwargs[key] = translated_value
                    else:
                        translated_kwargs[key] = value

                result = srv.call_tool(name, translated_kwargs)

                # Extract content from result
                output = ""
                is_screenshot = name == "puppeteer_screenshot" or "screenshot" in name.lower()
                
                if isinstance(result, dict):
                    if "content" in result:
                        if isinstance(result["content"], list):
                            # Multiple content items
                            outputs = []
                            for item in result["content"]:
                                if isinstance(item, dict):
                                    # Check if this item contains image data
                                    if "data" in item and isinstance(item.get("data"), str) and len(item["data"]) > 1000:
                                        # This is likely base64 image data
                                        mime_type = item.get("mimeType", "image/png")
                                        data_len = len(item["data"])
                                        logger.info(f"Replacing image data for {srv.server_id}.{name}: {data_len} chars of type {mime_type}")
                                        # Replace the actual data with a placeholder
                                        item_copy = item.copy()
                                        item_copy["data"] = f"[Image data - {data_len} chars, type: {mime_type}]"
                                        outputs.append(str(item_copy))
                                        if is_screenshot:
                                            outputs.append("[Screenshot captured successfully]")
                                    elif "text" in item:
                                        outputs.append(item["text"])
                                    else:
                                        outputs.append(str(item))
                                else:
                                    outputs.append(str(item))
                            output = "\n".join(outputs)
                        else:
                            output = str(result["content"])
                    elif "error" in result:
                        output = f"Error: {result['error']}"
                    else:
                        output = str(result)
                else:
                    output = str(result)

                # Additional image data processing for string representations
                if "data': '" in output and len(output) > 5000:
                    # Likely contains base64 image data in string format
                    # Replace with a placeholder
                    import re
                    image_pattern = r"'data': '([A-Za-z0-9+/=]{1000,})'"
                    
                    def replace_image_data(match):
                        data_len = len(match.group(1))
                        return f"'data': '[Image data - {data_len} chars]'"
                    
                    output = re.sub(image_pattern, replace_image_data, output)
                    
                # Also handle data": " format (with double quotes)
                if 'data": "' in output and len(output) > 5000:
                    import re
                    image_pattern = r'"data": "([A-Za-z0-9+/=]{1000,})"'
                    
                    def replace_image_data(match):
                        data_len = len(match.group(1))
                        return f'"data": "[Image data - {data_len} chars]"'
                    
                    output = re.sub(image_pattern, replace_image_data, output)
                
                # Truncate if output is still too large
                if len(output) > MAX_OUTPUT_LENGTH:
                    logger.warning(
                        f"Truncating output from {srv.server_id}.{name}: {len(output)} chars -> {MAX_OUTPUT_LENGTH} chars"
                    )
                    output = output[:MAX_OUTPUT_LENGTH] + TRUNCATION_MESSAGE

                return output

            wrapper.__name__ = f"{srv.server_id}_{name}"
            wrapper.__doc__ = info.get("description", f"Call {name} from {srv.server_id}")
            return wrapper

        # Create tool
        tool_fn = make_wrapper(server, tool_name, tool_info)
        tool = FunctionTool.from_defaults(fn=tool_fn, name=f"{server.server_id}_{tool_name}")
        tools.append(tool)

    return tools


async def load_mcp_tools_working() -> List[Any]:
    """Load MCP tools using the working approach"""
    tools = []

    try:
        from .mcp_server_config import MCPServerConfig

        config = MCPServerConfig()
        servers = config.list_servers()

        if not servers:
            logger.info("No MCP servers configured")
            return []

        logger.info(f"Loading {len(servers)} MCP servers...")

        for server_name, server_config in servers.items():
            logger.info(f"Starting {server_name}...")

            command = server_config.get("command", "")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            # Create and start server
            server = MCPServerProcess(server_name, command, args, env)

            if server.start():
                if server.initialize():
                    # Create tools
                    server_tools = create_mcp_tools_for_server(server)
                    tools.extend(server_tools)
                    logger.info(f"✅ Loaded {len(server_tools)} tools from {server_name}")

                    # Keep server running (in production, store these for cleanup)
                else:
                    logger.error(f"Failed to initialize {server_name}")
                    server.stop()
            else:
                logger.error(f"Failed to start {server_name}")

    except Exception as e:
        logger.error(f"Error loading MCP tools: {e}")
        import traceback

        traceback.print_exc()

    return tools
