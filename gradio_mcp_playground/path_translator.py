"""Path Translation for Cross-Platform MCP Server Support

This module handles path translation between Windows and WSL/Linux environments
to ensure MCP servers work correctly regardless of where they're running.
"""

import os
import platform
from pathlib import Path
from typing import List, Dict, Any


class PathTranslator:
    """Handles path translation between Windows and WSL/Linux environments"""
    
    def __init__(self):
        self.is_wsl = self._detect_wsl()
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux" and not self.is_wsl
        
    def _detect_wsl(self) -> bool:
        """Detect if running in WSL"""
        # Check for WSL-specific indicators
        if platform.system() != "Linux":
            return False
            
        # Check for /mnt/c and microsoft in kernel release
        has_mnt_c = os.path.exists("/mnt/c")
        has_microsoft = "microsoft" in platform.release().lower()
        
        # Check /proc/version for WSL indicators
        try:
            with open("/proc/version", "r") as f:
                version_info = f.read().lower()
                has_wsl_indicator = "microsoft" in version_info or "wsl" in version_info
        except:
            has_wsl_indicator = False
            
        return has_mnt_c and (has_microsoft or has_wsl_indicator)
    
    def translate_path(self, path: str) -> str:
        """Translate a path based on the current environment
        
        Args:
            path: The path to translate
            
        Returns:
            The translated path appropriate for the current environment
        """
        if not path:
            return path
            
        # If we're in WSL and the path is a Windows path, convert to WSL path
        if self.is_wsl:
            if path.startswith("C:\\") or path.startswith("c:\\"):
                # Convert C:\Users\... to /mnt/c/Users/...
                translated = path.replace("C:\\", "/mnt/c/").replace("c:\\", "/mnt/c/")
                translated = translated.replace("\\", "/")
                return translated
            elif path.startswith("D:\\") or path.startswith("d:\\"):
                # Handle other drive letters
                translated = path.replace("D:\\", "/mnt/d/").replace("d:\\", "/mnt/d/")
                translated = translated.replace("\\", "/")
                return translated
        
        # If we're in Windows and the path is a WSL path, convert to Windows path
        elif self.is_windows:
            if path.startswith("/mnt/c/"):
                # Convert /mnt/c/Users/... to C:\Users\...
                translated = path.replace("/mnt/c/", "C:\\")
                translated = translated.replace("/", "\\")
                return translated
            elif path.startswith("/mnt/d/"):
                translated = path.replace("/mnt/d/", "D:\\")
                translated = translated.replace("/", "\\")
                return translated
                
        # Return the path as-is if no translation needed
        return path
    
    def translate_server_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Translate paths in a server configuration
        
        Args:
            config: Server configuration dictionary
            
        Returns:
            Configuration with translated paths
        """
        translated_config = config.copy()
        
        # Translate paths in args
        if "args" in translated_config:
            translated_args = []
            for arg in translated_config["args"]:
                # Check if the arg looks like a path
                if isinstance(arg, str) and (
                    arg.startswith("C:\\") or arg.startswith("c:\\") or
                    arg.startswith("/mnt/") or arg.startswith("/home/") or
                    "\\" in arg or "/" in arg
                ):
                    # Skip package names (they contain @ or -)
                    if "@" not in arg and not arg.startswith("-"):
                        translated_args.append(self.translate_path(arg))
                    else:
                        translated_args.append(arg)
                else:
                    translated_args.append(arg)
            translated_config["args"] = translated_args
            
        return translated_config
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the current environment"""
        return {
            "platform": platform.system(),
            "is_wsl": self.is_wsl,
            "is_windows": self.is_windows,
            "is_linux": self.is_linux,
            "release": platform.release(),
            "has_mnt_c": os.path.exists("/mnt/c") if not self.is_windows else False
        }


# Global instance for convenience
path_translator = PathTranslator()


def translate_path(path: str) -> str:
    """Convenience function to translate a single path"""
    return path_translator.translate_path(path)


def translate_server_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to translate a server configuration"""
    return path_translator.translate_server_config(config)