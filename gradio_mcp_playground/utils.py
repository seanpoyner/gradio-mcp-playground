"""Gradio MCP Playground Utilities

Utility functions for the Gradio MCP Playground.
"""

import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
import hashlib
from datetime import datetime

# Optional imports
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def find_free_port(start_port: int = 7860, max_attempts: int = 100) -> int:
    """Find a free port starting from the given port"""
    for i in range(max_attempts):
        port = start_port + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    
    raise RuntimeError(f"Could not find free port after {max_attempts} attempts")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


def validate_server_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a server configuration"""
    errors = []
    
    # Required fields
    required = ["name", "path"]
    for field in required:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate path exists
    if "path" in config:
        path = Path(config["path"])
        if not path.exists():
            errors.append(f"Server file not found: {config['path']}")
    
    # Validate port if specified
    if "port" in config:
        port = config["port"]
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append(f"Invalid port number: {port}")
    
    return len(errors) == 0, errors


def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
    """Get information about a process"""
    if not HAS_PSUTIL:
        return None
    
    try:
        process = psutil.Process(pid)
        return {
            "pid": pid,
            "name": process.name(),
            "status": process.status(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(interval=0.1)
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def kill_process_on_port(port: int) -> bool:
    """Kill process listening on a specific port"""
    if not HAS_PSUTIL:
        return False
    
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == "LISTEN":
                try:
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    process.wait(timeout=5)
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
    except Exception:
        pass
    
    return False


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version meets requirements"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version >= (3, 8):
        return True, version_str
    else:
        return False, version_str


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed"""
    dependencies = {
        "gradio": "gradio",
        "mcp": "mcp",
        "anthropic": "anthropic",
        "aiohttp": "aiohttp",
        "pydantic": "pydantic",
        "rich": "rich"
    }
    
    results = {}
    for name, module in dependencies.items():
        try:
            __import__(module)
            results[name] = True
        except ImportError:
            results[name] = False
    
    return results


def install_dependencies(packages: List[str]) -> bool:
    """Install missing dependencies"""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + packages
        )
        return True
    except subprocess.CalledProcessError:
        return False


def create_requirements_file(directory: Path, packages: List[str]) -> None:
    """Create a requirements.txt file"""
    requirements_path = directory / "requirements.txt"
    
    # Add default packages
    default_packages = [
        "gradio>=4.44.0",
        "mcp>=1.0.0"
    ]
    
    all_packages = list(set(default_packages + packages))
    
    with open(requirements_path, "w") as f:
        f.write("\n".join(sorted(all_packages)))


def generate_server_id(name: str) -> str:
    """Generate a unique server ID"""
    timestamp = datetime.now().isoformat()
    data = f"{name}:{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()[:8]


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_server_stats(server_path: Path) -> Dict[str, Any]:
    """Get statistics about a server"""
    stats = {
        "files": 0,
        "total_size": 0,
        "last_modified": None
    }
    
    if not server_path.exists():
        return stats
    
    for file_path in server_path.rglob("*"):
        if file_path.is_file():
            stats["files"] += 1
            stats["total_size"] += file_path.stat().st_size
            
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if stats["last_modified"] is None or mtime > stats["last_modified"]:
                stats["last_modified"] = mtime
    
    if stats["last_modified"]:
        stats["last_modified"] = stats["last_modified"].isoformat()
    
    stats["total_size_formatted"] = format_file_size(stats["total_size"])
    
    return stats


def validate_tool_args(args: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate tool arguments against a schema"""
    errors = []
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Check required fields
    for field in required:
        if field not in args:
            errors.append(f"Missing required field: {field}")
    
    # Validate types
    for field, value in args.items():
        if field in properties:
            expected_type = properties[field].get("type")
            
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
    
    return len(errors) == 0, errors


def create_gradio_app_template(
    function_name: str,
    description: str,
    inputs: List[str],
    output_type: str = "text"
) -> str:
    """Generate a Gradio app template"""
    
    # Generate input components
    input_components = []
    for inp in inputs:
        input_components.append(f'    gr.Textbox(label="{inp}")')
    
    inputs_str = ",\n".join(input_components) if input_components else '    "text"'
    
    template = f'''"""Generated Gradio MCP Server

{description}
"""

import gradio as gr


def {function_name}({", ".join(inputs)}):
    """{description}
    
    Args:
        {chr(10).join(f"        {inp}: Input {inp}" for inp in inputs)}
    
    Returns:
        Processed result
    """
    # TODO: Implement your logic here
    result = f"Processing: {{{', '.join(inputs)}}}"
    return result


# Create Gradio interface
demo = gr.Interface(
    fn={function_name},
    inputs=[
{inputs_str}
    ],
    outputs="{output_type}",
    title="{function_name.replace('_', ' ').title()}",
    description="{description}"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
'''
    
    return template


def parse_mcp_url(url: str) -> Dict[str, Any]:
    """Parse an MCP URL to extract connection details"""
    result = {
        "protocol": "auto",
        "url": url,
        "valid": False
    }
    
    if url.startswith("stdio://"):
        result["protocol"] = "stdio"
        result["command"] = url[8:]  # Remove stdio://
        result["valid"] = True
    elif url.startswith("sse://"):
        result["protocol"] = "sse"
        result["url"] = url[6:]  # Remove sse://
        result["valid"] = True
    elif url.startswith("http://") or url.startswith("https://"):
        result["protocol"] = "sse" if "/sse" in url or "/mcp" in url else "gradio"
        result["valid"] = True
    else:
        # Assume it's a command for stdio
        result["protocol"] = "stdio"
        result["command"] = url
        result["valid"] = True
    
    return result


def get_example_servers() -> List[Dict[str, Any]]:
    """Get list of example servers"""
    return [
        {
            "name": "Simple Calculator",
            "description": "Basic arithmetic operations",
            "code": '''import gradio as gr

def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.Interface(
    fn=calculate,
    inputs="text",
    outputs="text",
    title="Calculator"
)

demo.launch(mcp_server=True)'''
        },
        {
            "name": "Text Processor",
            "description": "Various text processing operations",
            "code": '''import gradio as gr

def process_text(text: str, operation: str) -> str:
    """Process text with various operations."""
    if operation == "uppercase":
        return text.upper()
    elif operation == "lowercase":
        return text.lower()
    elif operation == "reverse":
        return text[::-1]
    elif operation == "word_count":
        return str(len(text.split()))
    else:
        return text

demo = gr.Interface(
    fn=process_text,
    inputs=[
        gr.Textbox(label="Text"),
        gr.Dropdown(["uppercase", "lowercase", "reverse", "word_count"], label="Operation")
    ],
    outputs="text",
    title="Text Processor"
)

demo.launch(mcp_server=True)'''
        }
    ]
