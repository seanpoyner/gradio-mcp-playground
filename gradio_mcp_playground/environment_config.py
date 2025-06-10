"""
Environment configuration module for storing and retrieving system-specific details.

This module provides functionality to capture and manage environment information
that can be injected into agent prompts, including OS type, home directory,
and other system-specific details.
"""

import os
import platform
import sys
import socket
import getpass
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class EnvironmentConfig:
    """Manages environment configuration and system information."""
    
    def __init__(self):
        """Initialize the environment configuration."""
        self._config_cache: Optional[Dict[str, Any]] = None
        self._config_file = Path.home() / ".gradio_mcp" / "environment_config.json"
        
    def get_environment_info(self, refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive environment information.
        
        Args:
            refresh: If True, force refresh the configuration cache
            
        Returns:
            Dictionary containing environment information
        """
        if self._config_cache is not None and not refresh:
            return self._config_cache
            
        env_info = {
            # OS Information
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "platform": platform.platform(),
                "is_windows": platform.system() == "Windows",
                "is_linux": platform.system() == "Linux",
                "is_mac": platform.system() == "Darwin",
            },
            
            # Python Information
            "python": {
                "version": sys.version,
                "version_info": {
                    "major": sys.version_info.major,
                    "minor": sys.version_info.minor,
                    "micro": sys.version_info.micro,
                },
                "implementation": platform.python_implementation(),
                "executable": sys.executable,
            },
            
            # User and System Paths
            "paths": {
                "home": str(Path.home()),
                "current_dir": os.getcwd(),
                "temp_dir": self._get_temp_dir(),
                "user_data_dir": str(Path.home() / ".gradio_mcp"),
                "config_dir": str(Path.home() / ".gradio_mcp" / "config"),
            },
            
            # User Information
            "user": {
                "username": getpass.getuser(),
                "hostname": socket.gethostname(),
            },
            
            # Environment Variables (selected safe ones)
            "env_vars": self._get_safe_env_vars(),
            
            # System Capabilities
            "capabilities": {
                "has_git": self._check_command_exists("git"),
                "has_docker": self._check_command_exists("docker"),
                "has_node": self._check_command_exists("node"),
                "has_npm": self._check_command_exists("npm"),
                "has_python3": self._check_command_exists("python3"),
                "has_pip": self._check_command_exists("pip"),
            },
            
            # Timestamp
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add Windows-specific information
        if platform.system() == "Windows":
            env_info["windows"] = self._get_windows_info()
            
        # Add WSL-specific information if running in WSL
        if self._is_wsl():
            env_info["wsl"] = self._get_wsl_info()
            
        self._config_cache = env_info
        return env_info
        
    def get_agent_prompt_context(self) -> str:
        """
        Get a formatted string of environment information suitable for agent prompts.
        
        Returns:
            Formatted string with key environment details
        """
        env_info = self.get_environment_info()
        
        context_parts = [
            "Environment Information:",
        ]
        
        # If in WSL, emphasize Windows environment
        if 'wsl' in env_info:
            context_parts.extend([
                f"- OS: Windows (via WSL - {env_info['wsl'].get('distro', 'Unknown')})",
                f"- Platform: {env_info['os']['platform']}",
                f"- Python: {env_info['python']['version_info']['major']}.{env_info['python']['version_info']['minor']}.{env_info['python']['version_info']['micro']}",
            ])
            
            # Use Windows paths if available
            if 'windows_user_home' in env_info['wsl']:
                context_parts.append(f"- Windows Home Directory: {env_info['wsl']['windows_user_home']}")
            context_parts.append(f"- WSL Home Directory: {env_info['paths']['home']}")
            
            # Convert current directory to Windows path if in /mnt/c
            current_dir = env_info['paths']['current_dir']
            if current_dir.startswith('/mnt/c'):
                windows_path = current_dir.replace('/mnt/c', 'C:').replace('/', '\\')
                context_parts.append(f"- Current Directory: {windows_path} (WSL: {current_dir})")
            else:
                context_parts.append(f"- Current Directory: {current_dir}")
                
        else:
            # Regular non-WSL environment
            context_parts.extend([
                f"- OS: {env_info['os']['system']} {env_info['os']['release']}",
                f"- Platform: {env_info['os']['platform']}",
                f"- Python: {env_info['python']['version_info']['major']}.{env_info['python']['version_info']['minor']}.{env_info['python']['version_info']['micro']}",
                f"- Home Directory: {env_info['paths']['home']}",
                f"- Current Directory: {env_info['paths']['current_dir']}",
            ])
            
        context_parts.append(f"- Username: {env_info['user']['username']}@{env_info['user']['hostname']}")
        
        # Add capabilities
        capabilities = []
        for tool, available in env_info['capabilities'].items():
            if available:
                capabilities.append(tool.replace('has_', ''))
        if capabilities:
            context_parts.append(f"- Available Tools: {', '.join(capabilities)}")
            
        # Add important note for Windows/WSL users
        if 'wsl' in env_info:
            context_parts.extend([
                "",
                "IMPORTANT: This is a Windows environment accessed through WSL.",
                "When providing file paths, use Windows-style paths (C:\\Users\\...) for MCP servers running on Windows.",
                "Use WSL paths (/mnt/c/...) only for operations within the WSL environment."
            ])
            
        return "\n".join(context_parts)
        
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save environment configuration to disk.
        
        Args:
            config: Configuration to save (uses current if not provided)
        """
        if config is None:
            config = self.get_environment_info()
            
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self._config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
            
    def load_config(self) -> Optional[Dict[str, Any]]:
        """
        Load environment configuration from disk.
        
        Returns:
            Loaded configuration or None if not found
        """
        if not self._config_file.exists():
            return None
            
        try:
            with open(self._config_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
            
    def _get_temp_dir(self) -> str:
        """Get the system's temporary directory."""
        import tempfile
        return tempfile.gettempdir()
        
    def _get_safe_env_vars(self) -> Dict[str, str]:
        """Get a selection of safe environment variables."""
        safe_vars = [
            "PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
            "LANG", "LC_ALL", "TZ", "SHELL", "TERM", "EDITOR",
            "HOME", "USER", "USERNAME", "COMPUTERNAME", "HOSTNAME"
        ]
        
        env_vars = {}
        for var in safe_vars:
            value = os.environ.get(var)
            if value:
                env_vars[var] = value
                
        return env_vars
        
    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        import shutil
        return shutil.which(command) is not None
        
    def _is_wsl(self) -> bool:
        """Check if running in Windows Subsystem for Linux."""
        if platform.system() != "Linux":
            return False
            
        # Check for WSL-specific files/environment
        wsl_indicators = [
            "/proc/sys/fs/binfmt_misc/WSLInterop",
            "/run/WSL",
        ]
        
        for indicator in wsl_indicators:
            if os.path.exists(indicator):
                return True
                
        # Check environment variable
        if "WSL_DISTRO_NAME" in os.environ:
            return True
            
        # Check /proc/version for Microsoft/WSL
        try:
            with open("/proc/version", "r") as f:
                version = f.read().lower()
                if "microsoft" in version or "wsl" in version:
                    return True
        except:
            pass
            
        return False
        
    def _get_wsl_info(self) -> Dict[str, Any]:
        """Get WSL-specific information."""
        wsl_info = {
            "is_wsl": True,
            "distro": os.environ.get("WSL_DISTRO_NAME", "Unknown"),
            "interop": os.environ.get("WSL_INTEROP", None) is not None,
        }
        
        # Try to get Windows host information
        if self._check_command_exists("wslpath"):
            try:
                import subprocess
                
                # Get Windows root
                result = subprocess.run(
                    ["wslpath", "-w", "/"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    wsl_info["windows_root"] = result.stdout.strip()
                
                # Get Windows home directory
                result = subprocess.run(
                    ["wslpath", "-w", str(Path.home())],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    wsl_info["windows_home"] = result.stdout.strip()
                    
                # Try to determine actual Windows user home
                # Check common paths
                windows_username = os.environ.get("USER", "")
                possible_paths = [
                    f"/mnt/c/Users/{windows_username}",
                    "/mnt/c/Users/seanp",  # Fallback based on current path
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        result = subprocess.run(
                            ["wslpath", "-w", path],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            wsl_info["windows_user_home"] = result.stdout.strip()
                            break
                            
            except:
                pass
                
        return wsl_info
        
    def _get_windows_info(self) -> Dict[str, Any]:
        """Get Windows-specific information."""
        win_info = {}
        
        try:
            # Get Windows version using platform
            win_info["version"] = platform.win32_ver()[0]
            win_info["build"] = platform.win32_ver()[1]
            
            # Get Windows edition if available
            win_info["edition"] = platform.win32_edition()
        except:
            pass
            
        return win_info


# Global instance for convenience
_env_config = EnvironmentConfig()


def get_environment_info(refresh: bool = False) -> Dict[str, Any]:
    """
    Get comprehensive environment information.
    
    Args:
        refresh: If True, force refresh the configuration cache
        
    Returns:
        Dictionary containing environment information
    """
    return _env_config.get_environment_info(refresh=refresh)


def get_agent_prompt_context() -> str:
    """
    Get a formatted string of environment information suitable for agent prompts.
    
    Returns:
        Formatted string with key environment details
    """
    return _env_config.get_agent_prompt_context()


def save_environment_config() -> None:
    """Save current environment configuration to disk."""
    _env_config.save_config()


def load_environment_config() -> Optional[Dict[str, Any]]:
    """
    Load environment configuration from disk.
    
    Returns:
        Loaded configuration or None if not found
    """
    return _env_config.load_config()