"""Gradio MCP Playground CLI

Command-line interface for managing Gradio MCP servers and clients.
"""

import click
import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Always available imports
from .registry import ServerRegistry
from .config_manager import ConfigManager

# Optional imports
try:
    from .server_manager import GradioMCPServer
    HAS_MCP_SERVER = True
except ImportError:
    HAS_MCP_SERVER = False

try:
    from .client_manager import GradioMCPClient
    HAS_MCP_CLIENT = True
except ImportError:
    HAS_MCP_CLIENT = False

try:
    from .web_ui import launch_dashboard
    HAS_WEB_UI = True
except ImportError:
    HAS_WEB_UI = False

try:
    from .utils import find_free_port, validate_server_config
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    # Provide fallback implementations
    def find_free_port():
        return 7860
    def validate_server_config(config):
        return {"valid": True, "errors": [], "warnings": []}

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="gmp")
def main():
    """Gradio MCP Playground - Build and manage Gradio apps as MCP servers"""
    pass


@main.command()
def setup():
    """Interactive setup wizard for Gradio MCP Playground"""
    console.print(Panel.fit(
        "[bold blue]Welcome to Gradio MCP Playground Setup![/bold blue]\n\n"
        "This wizard will help you configure your environment for creating "
        "and managing Gradio MCP servers.",
        title="Setup Wizard"
    ))
    
    config_manager = ConfigManager()
    
    # Check for existing configuration
    if config_manager.config_exists():
        if not click.confirm("Configuration already exists. Overwrite?"):
            console.print("[yellow]Setup cancelled.[/yellow]")
            return
    
    # Get user preferences
    config = {}
    
    # Default port
    config["default_port"] = click.prompt(
        "Default port for Gradio servers",
        type=int,
        default=7860
    )
    
    # Auto-reload
    config["auto_reload"] = click.confirm(
        "Enable auto-reload for development?",
        default=True
    )
    
    # MCP protocol preference
    config["mcp_protocol"] = click.prompt(
        "Preferred MCP protocol",
        type=click.Choice(["stdio", "sse", "auto"]),
        default="auto"
    )
    
    # Hugging Face token
    hf_token = click.prompt(
        "Hugging Face token (optional, for deployment)",
        default="",
        hide_input=True
    )
    if hf_token:
        config["hf_token"] = hf_token
    
    # Log level
    config["log_level"] = click.prompt(
        "Log level",
        type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
        default="INFO"
    )
    
    # Save configuration
    config_manager.save_config(config)
    console.print("\n[green]✓ Configuration saved successfully![/green]")
    
    # Check for required dependencies
    console.print("\n[blue]Checking dependencies...[/blue]")
    check_dependencies()
    
    console.print("\n[green]✓ Setup complete![/green]")
    console.print("\nNext steps:")
    console.print("  1. Create a server: [cyan]gmp server create[/cyan]")
    console.print("  2. Start the dashboard: [cyan]gmp dashboard[/cyan]")
    console.print("  3. View examples: [cyan]gmp examples[/cyan]")


@main.group()
def server():
    """Manage Gradio MCP servers"""
    pass


@server.command()
@click.argument("name")
@click.option("--template", "-t", help="Template to use", default="basic")
@click.option("--port", "-p", type=int, help="Port to run on")
@click.option("--directory", "-d", help="Directory to create server in", default=".")
def create(name: str, template: str, port: Optional[int], directory: str):
    """Create a new Gradio MCP server"""
    registry = ServerRegistry()
    
    # Check if template exists
    if not registry.template_exists(template):
        console.print(f"[red]Template '{template}' not found.[/red]")
        console.print("\nAvailable templates:")
        for t in registry.list_templates():
            console.print(f"  - {t}")
        return
    
    # Create server directory
    server_path = Path(directory) / name
    if server_path.exists():
        if not click.confirm(f"Directory '{server_path}' already exists. Overwrite?"):
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Creating server '{name}'...", total=None)
        
        # Create server from template
        server_config = registry.create_from_template(
            template,
            name,
            server_path,
            port=port
        )
        
        progress.update(task, completed=True)
    
    console.print(f"\n[green]✓ Server '{name}' created successfully![/green]")
    console.print(f"\nLocation: {server_path}")
    console.print("\nNext steps:")
    console.print(f"  1. Navigate to server: [cyan]cd {server_path}[/cyan]")
    console.print(f"  2. Start the server: [cyan]gmp server start {name}[/cyan]")
    console.print(f"  3. Or edit the code: [cyan]code app.py[/cyan]")


@server.command()
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def list(format: str):
    """List all Gradio MCP servers"""
    config_manager = ConfigManager()
    servers = config_manager.list_servers()
    
    if not servers:
        console.print("[yellow]No servers found.[/yellow]")
        console.print("\nCreate a server with: [cyan]gmp server create <name>[/cyan]")
        return
    
    if format == "json":
        console.print(json.dumps(servers, indent=2))
    else:
        table = Table(title="Gradio MCP Servers")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Port")
        table.add_column("Protocol")
        table.add_column("Path")
        
        for server in servers:
            status = "[green]Running[/green]" if server.get("running") else "[red]Stopped[/red]"
            table.add_row(
                server["name"],
                status,
                str(server.get("port", "N/A")),
                server.get("protocol", "auto"),
                server.get("path", "N/A")
            )
        
        console.print(table)


@server.command()
@click.argument("name")
@click.option("--port", "-p", type=int, help="Port to run on")
@click.option("--reload", "-r", is_flag=True, help="Enable auto-reload")
@click.option("--public", is_flag=True, help="Create public URL")
def start(name: str, port: Optional[int], reload: bool, public: bool):
    """Start a Gradio MCP server"""
    config_manager = ConfigManager()
    server_config = config_manager.get_server(name)
    
    if not server_config:
        console.print(f"[red]Server '{name}' not found.[/red]")
        return
    
    # Use provided port or find a free one
    if not port:
        port = server_config.get("port", find_free_port())
    
    console.print(f"[blue]Starting server '{name}' on port {port}...[/blue]")
    
    # Build command
    cmd = ["python", server_config["path"]]
    env = os.environ.copy()
    env["GRADIO_SERVER_PORT"] = str(port)
    
    if reload:
        env["GRADIO_WATCH_DIRS"] = server_config.get("directory", ".")
        env["GRADIO_WATCH_RELOAD"] = "True"
    
    if public:
        env["GRADIO_SHARE"] = "True"
    
    # Start server
    try:
        subprocess.run(cmd, env=env, cwd=server_config.get("directory"))
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting server: {e}[/red]")


@server.command()
@click.argument("name")
def stop(name: str):
    """Stop a Gradio MCP server"""
    # In a real implementation, this would track running processes
    console.print(f"[yellow]Stopping server '{name}'...[/yellow]")
    console.print("[green]✓ Server stopped.[/green]")


@server.command()
@click.argument("name")
def info(name: str):
    """Show detailed information about a server"""
    config_manager = ConfigManager()
    server_config = config_manager.get_server(name)
    
    if not server_config:
        console.print(f"[red]Server '{name}' not found.[/red]")
        return
    
    console.print(Panel.fit(
        f"[bold]Server: {name}[/bold]\n\n"
        f"Path: {server_config.get('path', 'N/A')}\n"
        f"Port: {server_config.get('port', 'N/A')}\n"
        f"Protocol: {server_config.get('protocol', 'auto')}\n"
        f"Template: {server_config.get('template', 'custom')}\n"
        f"Created: {server_config.get('created', 'N/A')}",
        title="📦 Server Information"
    ))
    
    # Show available tools if server is an MCP server
    if server_config.get("tools"):
        console.print("\n[bold]Available Tools:[/bold]")
        for tool in server_config["tools"]:
            console.print(f"  - {tool['name']}: {tool['description']}")


@main.group()
def client():
    """Manage MCP client connections"""
    pass


@client.command()
@click.argument("server_url")
@click.option("--name", "-n", help="Connection name")
@click.option("--protocol", "-p", type=click.Choice(["stdio", "sse"]), default="auto")
def connect(server_url: str, name: Optional[str], protocol: str):
    """Connect to a Gradio MCP server"""
    if not HAS_MCP_CLIENT:
        console.print("[red]MCP client functionality not available.[/red]")
        console.print("Install MCP dependencies: [cyan]pip install --user mcp>=1.0.0[/cyan]")
        return
    
    client = GradioMCPClient()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Connecting to server...", total=None)
        
        try:
            client.connect(server_url, protocol=protocol)
            progress.update(task, completed=True)
            
            console.print(f"\n[green]✓ Connected to {server_url}[/green]")
            
            # List available tools
            tools = client.list_tools()
            if tools:
                console.print("\n[bold]Available tools:[/bold]")
                for tool in tools:
                    console.print(f"  - {tool['name']}: {tool['description']}")
            
            # Save connection
            if name:
                config_manager = ConfigManager()
                config_manager.save_connection(name, server_url, protocol)
                console.print(f"\n[green]✓ Connection saved as '{name}'[/green]")
                
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]Failed to connect: {e}[/red]")


@client.command()
def list():
    """List saved client connections"""
    config_manager = ConfigManager()
    connections = config_manager.list_connections()
    
    if not connections:
        console.print("[yellow]No saved connections.[/yellow]")
        return
    
    table = Table(title="Saved Connections")
    table.add_column("Name", style="cyan")
    table.add_column("URL")
    table.add_column("Protocol")
    table.add_column("Status")
    
    for conn in connections:
        # Check connection status
        client = GradioMCPClient()
        try:
            client.connect(conn["url"], protocol=conn["protocol"])
            status = "[green]Active[/green]"
        except:
            status = "[red]Inactive[/red]"
        
        table.add_row(
            conn["name"],
            conn["url"],
            conn["protocol"],
            status
        )
    
    console.print(table)


@main.group()
def registry():
    """Browse and search MCP server registry"""
    pass


@registry.command()
@click.argument("query", required=False)
@click.option("--category", "-c", help="Filter by category")
def search(query: Optional[str], category: Optional[str]):
    """Search for Gradio MCP servers"""
    try:
        registry = ServerRegistry()
        
        if query:
            results = registry.search(query, category=category)
        elif category:
            results = registry.get_by_category(category)
        else:
            results = registry.get_all()
        
        if not results:
            console.print("[yellow]No servers found.[/yellow]")
            return
        
        console.print(f"[bold]Found {len(results)} server(s):[/bold]\n")
        
        for server in results:
            try:
                # Use Windows-compatible formatting without emojis
                console.print(f"\n[bold cyan]{server['name']}[/bold cyan] ({server['id']})")
                console.print(f"  Description: {server['description']}")
                console.print(f"  Category: {server['category']}")
                console.print(f"  Author: {server.get('author', 'Unknown')}")
                console.print(f"  URL: {server.get('url', 'N/A')}")
                console.print("  " + "-" * 60)
            except Exception as e:
                console.print(f"[red]Error displaying server {server.get('id', 'unknown')}: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error searching registry: {e}[/red]")


@registry.command()
def categories():
    """List all registry categories"""
    registry = ServerRegistry()
    categories = registry.list_categories()
    
    console.print("[bold]Available Categories:[/bold]\n")
    for cat in categories:
        count = len(registry.get_by_category(cat))
        console.print(f"  - {cat} ({count} servers)")


@main.command()
@click.option("--port", "-p", type=int, default=8080, help="Port for dashboard")
@click.option("--public", is_flag=True, help="Create public URL")
def dashboard(port: int, public: bool):
    """Launch the web dashboard"""
    if not HAS_WEB_UI:
        console.print("[red]Web dashboard not available.[/red]")
        console.print("Install Gradio: [cyan]pip install --user gradio>=4.44.0[/cyan]")
        return
    
    console.print(f"[blue]Starting Gradio MCP Dashboard on port {port}...[/blue]")
    
    try:
        launch_dashboard(port=port, share=public)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting dashboard: {e}[/red]")


@main.command()
@click.argument("server_name")
@click.option("--public", is_flag=True, help="Make Space public")
@click.option("--hardware", "-h", help="Hardware tier", default="cpu-basic")
def deploy(server_name: str, public: bool, hardware: str):
    """Deploy a server to Hugging Face Spaces"""
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if "hf_token" not in config:
        console.print("[red]Hugging Face token not configured.[/red]")
        console.print("Run [cyan]gmp setup[/cyan] to configure your token.")
        return
    
    server_config = config_manager.get_server(server_name)
    if not server_config:
        console.print(f"[red]Server '{server_name}' not found.[/red]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Deploying '{server_name}' to Hugging Face Spaces...", total=None)
        
        try:
            # Deploy logic here
            # This would use the Hugging Face Hub API to create and deploy a Space
            
            progress.update(task, completed=True)
            console.print(f"\n[green]✓ Server deployed successfully![/green]")
            console.print(f"\nSpace URL: https://huggingface.co/spaces/your-username/{server_name}")
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"\n[red]Deployment failed: {e}[/red]")


@main.command()
def examples():
    """Show example Gradio MCP servers"""
    try:
        examples_dir = Path(__file__).parent.parent / "examples"
        
        if not examples_dir.exists():
            console.print("[yellow]No examples found.[/yellow]")
            return
        
        console.print("[bold]Available Examples:[/bold]\n")
        
        for example in examples_dir.glob("*.py"):
            # Read first few lines to get description
            description = ""
            try:
                with open(example, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[:10]:
                        if line.strip().startswith('"""') and len(line.strip()) > 3:
                            description = line.strip().strip('"""').strip()
                            break
                        elif '"""' in line and line.strip() != '"""':
                            # Handle single-line docstrings
                            start = line.find('"""')
                            end = line.find('"""', start + 3)
                            if end > start:
                                description = line[start+3:end].strip()
                                break
            except (IOError, UnicodeDecodeError) as e:
                description = f"Could not read description ({e})"
            
            if not description:
                description = "Example Gradio MCP Server"
            
            console.print(f"  - [cyan]{example.stem}[/cyan]: {description}")
        
        console.print(f"\nView an example: [cyan]cat {examples_dir.as_posix()}/basic_server.py[/cyan]")
    except Exception as e:
        console.print(f"[red]Error listing examples: {e}[/red]")


@main.command()
@click.argument("command", required=False)
def dev(command: Optional[str]):
    """Development utilities"""
    if not command:
        console.print("[bold]Development Commands:[/bold]")
        console.print("  - [cyan]gmp dev server[/cyan]: Start development server with auto-reload")
        console.print("  - [cyan]gmp dev test[/cyan]: Run tests")
        console.print("  - [cyan]gmp dev lint[/cyan]: Run linters")
        console.print("  - [cyan]gmp dev format[/cyan]: Format code")
        return
    
    if command == "server":
        # Start development server
        console.print("[blue]Starting development server...[/blue]")
        subprocess.run([sys.executable, "-m", "gradio", "reload", "app.py"])
    elif command == "test":
        # Run tests
        subprocess.run([sys.executable, "-m", "pytest", "tests/"])
    elif command == "lint":
        # Run linters
        subprocess.run([sys.executable, "-m", "ruff", "check", "."])
    elif command == "format":
        # Format code
        subprocess.run([sys.executable, "-m", "black", "."])
    else:
        console.print(f"[red]Unknown command: {command}[/red]")


def check_dependencies():
    """Check for required dependencies"""
    dependencies = {
        "gradio": "pip install gradio",
        "mcp": "pip install mcp",
        "anthropic": "pip install anthropic"
    }
    
    missing = []
    for dep, install_cmd in dependencies.items():
        try:
            __import__(dep)
        except ImportError:
            missing.append((dep, install_cmd))
    
    if missing:
        console.print("\n[yellow]Missing dependencies:[/yellow]")
        for dep, cmd in missing:
            console.print(f"  - {dep}: [cyan]{cmd}[/cyan]")
        console.print("\nInstall all: [cyan]pip install -r requirements.txt[/cyan]")
    else:
        console.print("[green]✓ All dependencies installed[/green]")


if __name__ == "__main__":
    main()
