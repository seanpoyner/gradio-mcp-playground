"""MCP Process Wrapper

This module provides a process wrapper that pre-consumes startup messages
before handing off to the MCP client.
"""

import asyncio
import logging
import queue
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import mcp.types as types
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    HAS_MCP = True
except ImportError:
    HAS_MCP = False


class PreFilteredProcess:
    """A process wrapper that pre-filters startup messages"""

    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.args = args
        self.env = env
        self.process = None
        self.startup_consumed = False
        self.first_json_line = None
        self._stdout_queue = queue.Queue()
        self._stdin_queue = queue.Queue()

    def start(self) -> bool:
        """Start the process and consume startup messages"""
        try:
            # Prepare environment - use current env as base
            import os

            process_env = os.environ.copy()
            if self.env:
                process_env.update(self.env)

            # Log the command for debugging
            cmd = [self.command] + self.args
            logger.debug(f"Starting process: {' '.join(cmd)}")

            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr for debugging
                env=process_env,
                bufsize=0,  # Unbuffered
            )

            # Start reader threads
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()

            self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
            self._stderr_thread.start()

            # Wait for first JSON line
            timeout = time.time() + 5.0  # 5 second timeout
            while time.time() < timeout:
                try:
                    line = self._stdout_queue.get(timeout=0.1)
                    if line and line.strip().startswith(b"{") and b'"jsonrpc"' in line:
                        # This is our first JSON line - save it
                        self.first_json_line = line
                        self.startup_consumed = True
                        logger.info("Found first JSONRPC line, startup messages consumed")
                        return True
                except queue.Empty:
                    pass

                # Check if process is still running
                if self.process.poll() is not None:
                    # Read any remaining stderr
                    stderr_output = self.process.stderr.read().decode("utf-8", errors="replace")
                    logger.error(
                        f"Process exited during startup. Exit code: {self.process.returncode}"
                    )
                    if stderr_output:
                        logger.error(f"Stderr: {stderr_output}")
                    return False

            logger.error("Timeout waiting for JSONRPC")
            return False

        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            return False

    def _read_output(self):
        """Read output from process in a separate thread"""
        while True:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break

                # Log all lines during startup for debugging
                line_str = line.decode("utf-8", errors="replace").strip()
                if not self.startup_consumed:
                    logger.debug(f"Stdout: {line_str}")
                    if not (line_str.startswith("{") and '"jsonrpc"' in line_str):
                        logger.debug(f"Non-JSON stdout: {line_str}")

                self._stdout_queue.put(line)
            except Exception as e:
                logger.error(f"Error reading output: {e}")
                break

    def _read_stderr(self):
        """Read stderr from process in a separate thread"""
        while True:
            try:
                line = self.process.stderr.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").strip()
                if line_str:
                    logger.debug(f"Stderr: {line_str}")
            except Exception as e:
                logger.error(f"Error reading stderr: {e}")
                break

    def create_filtered_streams(self):
        """Create filtered streams for MCP client"""
        return FilteredReader(self), FilteredWriter(self)


class FilteredReader:
    """A reader that returns pre-consumed JSON and then reads from queue"""

    def __init__(self, process: PreFilteredProcess):
        self.process = process
        self.first_line_returned = False

    async def receive(self):
        """Receive data (for anyio compatibility)"""
        # First return the saved JSON line
        if not self.first_line_returned and self.process.first_json_line:
            self.first_line_returned = True
            # Parse the JSON line
            import json

            line_str = self.process.first_json_line.decode("utf-8", errors="replace").strip()
            return json.loads(line_str)

        # Then read from queue
        while True:
            try:
                line = self.process._stdout_queue.get(timeout=0.1)
                if line:
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if line_str.startswith("{"):
                        try:
                            return json.loads(line_str)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON: {line_str}")
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error receiving: {e}")
                raise


class FilteredWriter:
    """A writer that sends to process stdin"""

    def __init__(self, process: PreFilteredProcess):
        self.process = process

    async def send(self, data):
        """Send data (for anyio compatibility)"""
        try:
            import json

            json_str = json.dumps(data)
            self.process.process.stdin.write(json_str.encode("utf-8") + b"\n")
            self.process.process.stdin.flush()
        except Exception as e:
            logger.error(f"Error sending: {e}")
            raise


async def connect_with_prefilter(
    server_id: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None
) -> Tuple[Optional[ClientSession], Dict[str, Any]]:
    """Connect to MCP server using pre-filtering approach"""

    if not HAS_MCP:
        logger.error("MCP not installed")
        return None, {}

    # Create and start filtered process
    process = PreFilteredProcess(command, args, env)
    if not process.start():
        logger.error(f"Failed to start {server_id}")
        return None, {}

    try:
        # Create filtered streams
        read_stream, write_stream = process.create_filtered_streams()

        # Create session
        session = ClientSession(read_stream, write_stream)

        # Initialize
        await session.initialize()
        logger.info(f"Session initialized for {server_id}")

        # Get tools
        tools_result = await session.list_tools()
        tools = {}
        for tool in tools_result.tools:
            tools[tool.name] = tool

        logger.info(f"✅ Connected to {server_id} with {len(tools)} tools")

        # Store process reference for cleanup
        session._process = process.process

        return session, tools

    except Exception as e:
        logger.error(f"Failed to connect to {server_id}: {e}")
        import traceback

        traceback.print_exc()
        if process.process:
            process.process.terminate()
        return None, {}
