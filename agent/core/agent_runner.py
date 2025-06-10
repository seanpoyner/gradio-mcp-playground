"""Agent Runner - Core execution system for persistent agent processes

This module provides the core functionality for running agents as persistent
background processes instead of just returning chat responses.
"""

import os
import sys
import subprocess
import tempfile
import threading
import time
import signal
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class AgentProcess:
    """Represents a running agent process with metadata"""
    
    def __init__(self, name: str, process: subprocess.Popen, code_file: Path, port: int = None):
        self.name = name
        self.process = process
        self.code_file = code_file
        self.port = port
        self.start_time = datetime.now()
        self.status = "starting"
        self.error_count = 0
        self.last_error = None
    
    @property
    def pid(self) -> int:
        """Get process ID"""
        return self.process.pid if self.process else None
    
    @property
    def uptime(self) -> timedelta:
        """Get process uptime"""
        return datetime.now() - self.start_time
    
    @property
    def is_running(self) -> bool:
        """Check if process is still running"""
        if not self.process:
            return False
        
        try:
            # Check if process is still alive
            return self.process.poll() is None
        except:
            return False
    
    def get_memory_usage(self) -> Optional[float]:
        """Get memory usage in MB"""
        try:
            if self.is_running:
                proc = psutil.Process(self.pid)
                return proc.memory_info().rss / 1024 / 1024  # Convert to MB
        except:
            pass
        return None
    
    def get_cpu_percent(self) -> Optional[float]:
        """Get CPU usage percentage"""
        try:
            if self.is_running:
                proc = psutil.Process(self.pid)
                return proc.cpu_percent()
        except:
            pass
        return None


class AgentRunner:
    """Manages agent processes - starting, stopping, and monitoring"""
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path.cwd() / "agent_workspace"
        self.workspace_dir.mkdir(exist_ok=True)
        
        # Registry of running processes
        self.running_agents: Dict[str, AgentProcess] = {}
        
        # Port management for web interfaces
        self._port_counter = 7860
        self._used_ports = set()
        
        # Cleanup on exit
        import atexit
        atexit.register(self.cleanup_all)
    
    def _get_next_port(self) -> int:
        """Get next available port for agent web interface"""
        while self._port_counter in self._used_ports:
            self._port_counter += 1
        
        port = self._port_counter
        self._used_ports.add(port)
        self._port_counter += 1
        return port
    
    def _release_port(self, port: int) -> None:
        """Release a port back to the pool"""
        self._used_ports.discard(port)
    
    def _create_agent_file(self, name: str, code: str) -> Path:
        """Create a Python file for the agent code in agents directory"""
        # Save directly to agents directory (no subdirectories)
        agent_file = self.workspace_dir / f"{name}.py"
        
        # Use the original code directly without wrapping
        # This allows the agent to run as originally designed
        agent_file.write_text(code)
        agent_file.chmod(0o755)  # Make executable
        return agent_file
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces"""
        indent = " " * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def start_agent(self, name: str, code: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Start an agent as a persistent background process
        
        Args:
            name: Unique name for the agent
            code: Python code to execute as the agent
            
        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            # Check if agent is already running
            if name in self.running_agents:
                if self.running_agents[name].is_running:
                    return False, f"Agent '{name}' is already running", {
                        "status": "already_running",
                        "pid": self.running_agents[name].pid
                    }
                else:
                    # Clean up dead process
                    self._cleanup_agent(name)
            
            # Validate agent name
            if not name or not name.replace('_', '').replace('-', '').isalnum():
                return False, "Agent name must contain only letters, numbers, hyphens, and underscores", {
                    "status": "invalid_name"
                }
            
            # Create agent file
            agent_file = self._create_agent_file(name, code)
            
            # Get port for web interface (if the code uses Gradio)
            port = self._get_next_port()
            
            # Set up environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(__file__).parent.parent.parent)
            env['AGENT_NAME'] = name
            env['AGENT_PORT'] = str(port)
            
            # Start the process
            process = subprocess.Popen(
                [sys.executable, str(agent_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self.workspace_dir,  # Use agents directory as working directory
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Create agent process object
            agent_process = AgentProcess(name, process, agent_file, port)
            self.running_agents[name] = agent_process
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if it started successfully
            if not agent_process.is_running:
                # Process died immediately, get error info
                stdout, stderr = process.communicate(timeout=1)
                error_msg = stderr.decode() if stderr else "Process died immediately"
                self._cleanup_agent(name)
                return False, f"Agent failed to start: {error_msg}", {
                    "status": "startup_failed",
                    "error": error_msg
                }
            
            agent_process.status = "running"
            logger.info(f"Started agent '{name}' with PID {process.pid}")
            
            return True, f"Agent '{name}' started successfully", {
                "status": "running",
                "pid": process.pid,
                "port": port,
                "start_time": agent_process.start_time.isoformat(),
                "agent_file": str(agent_file)
            }
            
        except Exception as e:
            logger.error(f"Error starting agent '{name}': {e}")
            return False, f"Failed to start agent: {str(e)}", {
                "status": "error",
                "error": str(e)
            }
    
    def stop_agent(self, name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Stop a running agent process
        
        Args:
            name: Name of the agent to stop
            
        Returns:
            Tuple of (success, message, metadata)
        """
        try:
            if name not in self.running_agents:
                return False, f"Agent '{name}' is not running", {
                    "status": "not_found"
                }
            
            agent_process = self.running_agents[name]
            
            if not agent_process.is_running:
                # Process already dead, just clean up
                self._cleanup_agent(name)
                return True, f"Agent '{name}' was already stopped", {
                    "status": "already_stopped"
                }
            
            # Try graceful shutdown first
            pid = agent_process.pid
            logger.info(f"Stopping agent '{name}' (PID: {pid})")
            
            try:
                if os.name != 'nt':
                    # Unix-like systems
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                else:
                    # Windows
                    agent_process.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    agent_process.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning(f"Agent '{name}' didn't stop gracefully, force killing")
                    if os.name != 'nt':
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    else:
                        agent_process.process.kill()
                    agent_process.process.wait(timeout=2)
                
            except ProcessLookupError:
                # Process already died
                pass
            
            # Clean up resources
            uptime = agent_process.uptime
            self._cleanup_agent(name)
            
            return True, f"Agent '{name}' stopped successfully", {
                "status": "stopped",
                "uptime_seconds": uptime.total_seconds(),
                "pid": pid
            }
            
        except Exception as e:
            logger.error(f"Error stopping agent '{name}': {e}")
            return False, f"Failed to stop agent: {str(e)}", {
                "status": "error",
                "error": str(e)
            }
    
    def get_status(self, name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Get status information for an agent
        
        Args:
            name: Name of the agent to check
            
        Returns:
            Tuple of (found, status_message, detailed_info)
        """
        try:
            if name not in self.running_agents:
                return False, f"Agent '{name}' not found", {
                    "status": "not_found",
                    "name": name
                }
            
            agent_process = self.running_agents[name]
            
            if not agent_process.is_running:
                # Process died, get exit info
                exit_code = agent_process.process.returncode
                uptime = agent_process.uptime
                
                status_info = {
                    "status": "stopped",
                    "name": name,
                    "exit_code": exit_code,
                    "uptime_seconds": uptime.total_seconds(),
                    "start_time": agent_process.start_time.isoformat(),
                    "stop_time": datetime.now().isoformat()
                }
                
                return True, f"Agent '{name}' is stopped (exit code: {exit_code})", status_info
            
            # Process is running, get detailed info
            uptime = agent_process.uptime
            memory_mb = agent_process.get_memory_usage()
            cpu_percent = agent_process.get_cpu_percent()
            
            status_info = {
                "status": "running",
                "name": name,
                "pid": agent_process.pid,
                "port": agent_process.port,
                "uptime_seconds": uptime.total_seconds(),
                "uptime_human": str(uptime).split('.')[0],  # Remove microseconds
                "start_time": agent_process.start_time.isoformat(),
                "memory_mb": memory_mb,
                "cpu_percent": cpu_percent,
                "error_count": agent_process.error_count,
                "agent_file": str(agent_process.code_file)
            }
            
            return True, f"Agent '{name}' is running (PID: {agent_process.pid})", status_info
            
        except Exception as e:
            logger.error(f"Error getting status for agent '{name}': {e}")
            return False, f"Error checking agent status: {str(e)}", {
                "status": "error",
                "error": str(e)
            }
    
    def _cleanup_agent(self, name: str) -> None:
        """Clean up resources for an agent"""
        if name in self.running_agents:
            agent_process = self.running_agents[name]
            
            # Release the port
            if agent_process.port:
                self._release_port(agent_process.port)
            
            # Remove from registry
            del self.running_agents[name]
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        agents_status = {}
        
        for name in list(self.running_agents.keys()):
            found, message, info = self.get_status(name)
            agents_status[name] = info
            
        return agents_status
    
    def cleanup_all(self) -> None:
        """Stop all running agents and clean up resources"""
        logger.info("Cleaning up all running agents...")
        
        for name in list(self.running_agents.keys()):
            try:
                self.stop_agent(name)
            except Exception as e:
                logger.error(f"Error stopping agent '{name}' during cleanup: {e}")


# Global instance for the module
_agent_runner = None

def get_agent_runner() -> AgentRunner:
    """Get the global agent runner instance"""
    global _agent_runner
    if _agent_runner is None:
        # Use agents directory instead of agent_workspace
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        agents_dir = project_root / "agent/agents"
        
        # Ensure agents directory exists
        agents_dir.mkdir(exist_ok=True)
        
        _agent_runner = AgentRunner(workspace_dir=agents_dir)
    return _agent_runner

# Convenience functions using the global instance
def start_agent(name: str, code: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Start an agent process"""
    return get_agent_runner().start_agent(name, code)

def stop_agent(name: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Stop an agent process"""
    return get_agent_runner().stop_agent(name)

def get_status(name: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Get agent status"""
    return get_agent_runner().get_status(name)

def list_agents() -> Dict[str, Dict[str, Any]]:
    """List all agents"""
    return get_agent_runner().list_agents()