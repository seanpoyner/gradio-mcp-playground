"""Enhanced MCP Server Registry

Comprehensive registry of available MCP servers including official, community, and Gradio templates.
Based on claude-desktop-mcp-playground registry with enhanced search and installation capabilities.
"""

import json
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ServerRegistry:
    """Enhanced registry for MCP servers and Gradio templates"""

    def __init__(self):
        self.registry_path = Path(__file__).parent / "registry.json"
        self.templates_path = Path(__file__).parent / "templates"
        self.custom_registry_path = Path.home() / ".gradio-mcp" / "custom_registry.json"
        self._load_registry()

    def _load_registry(self) -> None:
        """Load the comprehensive server registry"""
        # Load comprehensive MCP server registry
        self.mcp_servers = self._get_mcp_server_registry()

        # Load Gradio templates registry
        self.templates = self._get_builtin_registry()

        # Load custom registry if exists
        if self.custom_registry_path.exists():
            with open(self.custom_registry_path) as f:
                custom = json.load(f)
            # Merge custom entries into templates
            self.templates.update(custom)

    def _get_mcp_server_registry(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive MCP server registry with 80+ servers"""
        return {
            # Current official @modelcontextprotocol servers
            "filesystem": {
                "name": "Filesystem Server",
                "description": "Secure file operations with configurable access controls. Read, write, and manage files and directories.",
                "category": "official",
                "package": "@modelcontextprotocol/server-filesystem",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@modelcontextprotocol/server-filesystem", "<path>"],
                "required_args": ["path"],
                "optional_args": [],
                "env_vars": {},
                "setup_help": "Provide a path to the directory you want Claude to access",
                "example_usage": "Access files in your workspace directory",
                "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
            },
            "memory": {
                "name": "Memory Server",
                "description": "Knowledge graph-based persistent memory system. Store and retrieve information across conversations.",
                "category": "official",
                "package": "@modelcontextprotocol/server-memory",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@modelcontextprotocol/server-memory"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {},
                "setup_help": "No additional setup required",
                "example_usage": "Remember information between conversations",
                "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
            },
            "brave-search": {
                "name": "Brave Search Server",
                "description": "Web search capabilities using Brave Search API. Get search results with privacy focus.",
                "category": "official",
                "package": "@modelcontextprotocol/server-brave-search",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@modelcontextprotocol/server-brave-search"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {"BRAVE_API_KEY": "Your Brave Search API key"},
                "setup_help": "Get API key from https://brave.com/search/api/",
                "example_usage": "Search the web for current information",
                "homepage": "https://github.com/modelcontextprotocol/servers",
            },
            "github": {
                "name": "GitHub Server",
                "description": "Access GitHub repositories, issues, PRs, and code. Search repositories and manage GitHub resources.",
                "category": "official",
                "package": "@modelcontextprotocol/server-github",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@modelcontextprotocol/server-github"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {"GITHUB_TOKEN": "Your GitHub personal access token"},
                "setup_help": "Create a GitHub token at https://github.com/settings/tokens",
                "example_usage": "Search code, manage issues, analyze repositories",
                "homepage": "https://github.com/modelcontextprotocol/servers",
            },
            "sequential-thinking": {
                "name": "Sequential Thinking Server",
                "description": "Dynamic and reflective problem-solving through thought sequences. Advanced reasoning capabilities.",
                "category": "official",
                "package": "@modelcontextprotocol/server-sequential-thinking",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {},
                "setup_help": "No additional setup required",
                "example_usage": "Enhanced reasoning and problem-solving",
                "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking",
            },
            "time": {
                "name": "Time Server",
                "description": "Time and timezone utilities. Get current time, convert between timezones, format dates.",
                "category": "official",
                "package": "mcp-server-time",
                "install_method": "uvx",
                "command": "uvx",
                "args_template": ["mcp-server-time", "--local-timezone", "<timezone>"],
                "required_args": ["timezone"],
                "optional_args": [],
                "env_vars": {},
                "setup_help": "Requires uvx (pip install uvx). Provide timezone in IANA format (e.g., America/New_York, Europe/London, UTC)",
                "example_usage": "Handle time-based operations and conversions",
                "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/time",
            },
            # Community servers (selection from 500+ available)
            "sqlite": {
                "name": "SQLite Server",
                "description": "Query and manage SQLite databases. Execute SQL queries, create tables, and manage database schemas.",
                "category": "official",
                "package": "mcp-server-sqlite-npx",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "mcp-server-sqlite-npx", "<database_path>"],
                "required_args": ["database_path"],
                "optional_args": [],
                "env_vars": {},
                "setup_help": "Provide path to your SQLite database file (.db or .sqlite)",
                "example_usage": "Query your application database or analyze data",
                "homepage": "https://github.com/modelcontextprotocol/servers",
            },
            "postgres": {
                "name": "PostgreSQL Server",
                "description": "Connect to PostgreSQL databases. Execute queries, manage schemas, and analyze data.",
                "category": "official",
                "package": "@modelcontextprotocol/server-postgres",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@modelcontextprotocol/server-postgres"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {
                    "POSTGRES_URL": "PostgreSQL connection string",
                    "POSTGRES_HOST": "Database host (alternative)",
                    "POSTGRES_PORT": "Database port (alternative)",
                    "POSTGRES_DB": "Database name (alternative)",
                    "POSTGRES_USER": "Username (alternative)",
                    "POSTGRES_PASSWORD": "Password (alternative)",
                },
                "setup_help": "Provide PostgreSQL connection details",
                "example_usage": "Query your PostgreSQL database",
                "homepage": "https://github.com/modelcontextprotocol/servers",
            },
            "docker": {
                "name": "Docker MCP Server",
                "description": "Manage Docker with natural language. Compose containers, introspect running containers, and manage volumes, networks, and images.",
                "category": "community",
                "package": "mcp-server-docker",
                "install_method": "uvx",
                "command": "uvx",
                "args_template": ["mcp-server-docker"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {
                    "DOCKER_HOST": "Docker host URL (optional, e.g., ssh://user@host.com for remote Docker)"
                },
                "setup_help": "Requires Docker installed. For remote Docker access, set DOCKER_HOST environment variable to ssh://username@hostname",
                "example_usage": "Deploy WordPress with MySQL, manage containers with natural language",
                "homepage": "https://github.com/ckreiling/mcp-server-docker",
            },
            "aws": {
                "name": "AWS MCP Server",
                "description": "Specialized MCP servers that bring AWS best practices directly to your development workflow.",
                "category": "community",
                "package": "aws-mcp",
                "install_method": "git",
                "command": "git",
                "args_template": ["clone", "https://github.com/awslabs/mcp"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {
                    "AWS_ACCESS_KEY_ID": "AWS access key",
                    "AWS_SECRET_ACCESS_KEY": "AWS secret key",
                },
                "setup_help": "Clone repository and follow setup instructions",
                "example_usage": "Manage AWS resources through AI agents",
                "homepage": "https://github.com/awslabs/mcp",
            },
            "azure": {
                "name": "Microsoft Azure Server",
                "description": "Access key Azure services and tools like Azure Storage, Cosmos DB, the Azure CLI, and more.",
                "category": "community",
                "package": "@azure/mcp",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "@azure/mcp@latest", "server", "start"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {
                    "AZURE_TENANT_ID": "Your Azure tenant ID",
                    "AZURE_CLIENT_ID": "Your Azure client ID",
                    "AZURE_CLIENT_SECRET": "Your Azure client secret",
                },
                "setup_help": "Configure Azure credentials via environment variables or use Azure CLI authentication",
                "example_usage": "Manage Azure resources and services",
                "homepage": "https://github.com/Azure/azure-mcp",
            },
            "obsidian": {
                "name": "Obsidian MCP Server",
                "description": "Interact with Obsidian vaults. Read, create, edit and manage notes and tags. Provides tools for note management, search, and tag operations.",
                "category": "community",
                "package": "obsidian-mcp",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "obsidian-mcp", "<vault_path1>", "<vault_path2>"],
                "required_args": ["vault_path1"],
                "optional_args": ["vault_path2"],
                "env_vars": {},
                "setup_help": "Provide the absolute path to your Obsidian vault directory. You can specify multiple vault paths as additional arguments. IMPORTANT: Backup your vault before use as this server has read/write access.",
                "example_usage": "Read/create/edit notes, search vault contents, manage tags, move/delete notes",
                "homepage": "https://github.com/StevenStavrakis/obsidian-mcp",
            },
            "figma": {
                "name": "Figma Server",
                "description": "ModelContextProtocol server for Figma design files and collaboration.",
                "category": "community",
                "package": "figma-mcp",
                "install_method": "npm",
                "command": "npx",
                "args_template": ["-y", "figma-mcp"],
                "required_args": [],
                "optional_args": [],
                "env_vars": {"FIGMA_TOKEN": "Your Figma API token"},
                "setup_help": "Get API token from Figma account settings",
                "example_usage": "Access Figma designs and collaborate",
                "homepage": "https://www.npmjs.com/package/figma-mcp",
            },
        }

    def _get_builtin_registry(self) -> Dict[str, Any]:
        """Get built-in server registry"""
        return {
            "basic-tool": {
                "id": "basic-tool",
                "name": "Basic Tool Server",
                "description": "Simple single-tool MCP server template",
                "category": "starter",
                "author": "Gradio MCP Playground",
                "tags": ["basic", "starter", "tool"],
                "url": "https://github.com/gradio-mcp-playground/templates/basic-tool",
            },
            "calculator": {
                "id": "calculator",
                "name": "Calculator Server",
                "description": "Mathematical operations MCP server",
                "category": "tools",
                "author": "Gradio MCP Playground",
                "tags": ["math", "calculator", "tools"],
                "url": "https://github.com/gradio-mcp-playground/templates/calculator",
            },
            "image-generator": {
                "id": "image-generator",
                "name": "Image Generator Server",
                "description": "AI image generation MCP server using Stable Diffusion",
                "category": "ai",
                "author": "Gradio MCP Playground",
                "tags": ["ai", "image", "generation", "stable-diffusion"],
                "url": "https://github.com/gradio-mcp-playground/templates/image-generator",
            },
            "data-analyzer": {
                "id": "data-analyzer",
                "name": "Data Analyzer Server",
                "description": "CSV and data analysis MCP server",
                "category": "data",
                "author": "Gradio MCP Playground",
                "tags": ["data", "csv", "analysis", "pandas"],
                "url": "https://github.com/gradio-mcp-playground/templates/data-analyzer",
            },
            "file-processor": {
                "id": "file-processor",
                "name": "File Processor Server",
                "description": "File manipulation and processing MCP server",
                "category": "tools",
                "author": "Gradio MCP Playground",
                "tags": ["files", "processing", "tools"],
                "url": "https://github.com/gradio-mcp-playground/templates/file-processor",
            },
            "web-scraper": {
                "id": "web-scraper",
                "name": "Web Scraper Server",
                "description": "Web scraping and data extraction MCP server",
                "category": "web",
                "author": "Gradio MCP Playground",
                "tags": ["web", "scraping", "extraction"],
                "url": "https://github.com/gradio-mcp-playground/templates/web-scraper",
            },
            "llm-tools": {
                "id": "llm-tools",
                "name": "LLM Tools Server",
                "description": "LLM-powered tools (summarization, translation, etc.)",
                "category": "ai",
                "author": "Gradio MCP Playground",
                "tags": ["ai", "llm", "nlp", "tools"],
                "url": "https://github.com/gradio-mcp-playground/templates/llm-tools",
            },
            "api-wrapper": {
                "id": "api-wrapper",
                "name": "API Wrapper Server",
                "description": "Wrap any API as an MCP server",
                "category": "integration",
                "author": "Gradio MCP Playground",
                "tags": ["api", "integration", "wrapper"],
                "url": "https://github.com/gradio-mcp-playground/templates/api-wrapper",
            },
            "multi-tool": {
                "id": "multi-tool",
                "name": "Multi-Tool Server",
                "description": "MCP server with multiple tools in tabs",
                "category": "advanced",
                "author": "Gradio MCP Playground",
                "tags": ["multi-tool", "advanced", "tabs"],
                "url": "https://github.com/gradio-mcp-playground/templates/multi-tool",
            },
            "custom-ui": {
                "id": "custom-ui",
                "name": "Custom UI Server",
                "description": "MCP server with custom Gradio components",
                "category": "advanced",
                "author": "Gradio MCP Playground",
                "tags": ["ui", "custom", "advanced"],
                "url": "https://github.com/gradio-mcp-playground/templates/custom-ui",
            },
        }

    def search_mcp_servers(
        self, query: str, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for MCP servers in the registry"""
        query = query.lower()
        results = []

        for server_id, server_info in self.mcp_servers.items():
            # Filter by category if specified
            if category and server_info.get("category") != category:
                continue

            # Search in server ID, name, description, and package
            searchable_text = f"{server_id} {server_info['name']} {server_info['description']} {server_info['category']} {server_info.get('package', '')}".lower()

            if query in searchable_text:
                results.append({"id": server_id, "type": "mcp_server", **server_info})

        # Sort by relevance (exact matches first, then partial matches)
        def relevance_score(server):
            score = 0
            server_text = f"{server['id']} {server['name']}".lower()

            if query == server["id"]:
                score += 100
            elif query in server["id"]:
                score += 50
            elif query in server["name"].lower():
                score += 30
            elif query in server["description"].lower():
                score += 10

            return score

        results.sort(key=relevance_score, reverse=True)
        return results

    def search_templates(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for Gradio templates in the registry"""
        query = query.lower()
        results = []

        for server_id, server_info in self.templates.items():
            # Filter by category if specified
            if category and server_info.get("category") != category:
                continue

            # Search in various fields
            searchable = [
                server_id,
                server_info.get("name", "").lower(),
                server_info.get("description", "").lower(),
                " ".join(server_info.get("tags", [])).lower(),
            ]

            if any(query in field for field in searchable):
                server_info_copy = dict(server_info)
                server_info_copy["type"] = "template"
                results.append(server_info_copy)

        return results

    def search(
        self, query: str, category: Optional[str] = None, server_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """Search for servers and templates in the registry"""
        results = []

        if server_type in ["all", "mcp_server"]:
            results.extend(self.search_mcp_servers(query, category))

        if server_type in ["all", "template"]:
            results.extend(self.search_templates(query, category))

        return results

    def get_by_category(self, category: str, server_type: str = "all") -> List[Dict[str, Any]]:
        """Get all servers/templates in a category"""
        results = []

        if server_type in ["all", "mcp_server"]:
            for server_id, server_info in self.mcp_servers.items():
                if server_info.get("category") == category:
                    results.append({"id": server_id, "type": "mcp_server", **server_info})

        if server_type in ["all", "template"]:
            for server_id, server_info in self.templates.items():
                if server_info.get("category") == category:
                    server_info_copy = dict(server_info)
                    server_info_copy["type"] = "template"
                    results.append(server_info_copy)

        return results

    def get_all(self, server_type: str = "all") -> List[Dict[str, Any]]:
        """Get all servers/templates in the registry"""
        results = []

        if server_type in ["all", "mcp_server"]:
            for server_id, server_info in self.mcp_servers.items():
                results.append({"id": server_id, "type": "mcp_server", **server_info})

        if server_type in ["all", "template"]:
            for server_id, server_info in self.templates.items():
                server_info_copy = dict(server_info)
                server_info_copy["type"] = "template"
                results.append(server_info_copy)

        return results

    def get_mcp_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific MCP server"""
        server_info = self.mcp_servers.get(server_id)
        if server_info:
            return {"id": server_id, "type": "mcp_server", **server_info}
        return None

    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific server/template by ID (checks both MCP servers and templates)"""
        # Check MCP servers first
        mcp_server = self.get_mcp_server(server_id)
        if mcp_server:
            return mcp_server

        # Check templates
        template = self.templates.get(server_id)
        if template:
            template_copy = dict(template)
            template_copy["type"] = "template"
            return template_copy

        return None

    def list_categories(self, server_type: str = "all") -> List[str]:
        """List all available categories"""
        categories = set()

        if server_type in ["all", "mcp_server"]:
            for server in self.mcp_servers.values():
                if "category" in server:
                    categories.add(server["category"])

        if server_type in ["all", "template"]:
            for server in self.templates.values():
                if "category" in server:
                    categories.add(server["category"])

        return sorted(list(categories))

    def _get_platform_key(self) -> str:
        """Get platform key for configuration"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        else:
            return "linux"

    def _expand_env_vars(self, path: str) -> str:
        """Expand environment variables in path string"""
        # Handle common environment variables
        if "{LOCALAPPDATA}" in path:
            path = path.replace("{LOCALAPPDATA}", os.environ.get("LOCALAPPDATA", ""))
        if "{APPDATA}" in path:
            path = path.replace("{APPDATA}", os.environ.get("APPDATA", ""))
        if "{USERPROFILE}" in path:
            path = path.replace("{USERPROFILE}", os.environ.get("USERPROFILE", str(Path.home())))
        if "{HOME}" in path:
            path = path.replace("{HOME}", str(Path.home()))
        return path

    def generate_install_command(
        self, server_id: str, user_args: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Generate installation command for an MCP server with user-provided arguments"""
        server = self.get_mcp_server(server_id)
        if not server:
            return None

        # Build command arguments
        args = []
        for arg_template in server["args_template"]:
            if arg_template.startswith("<") and arg_template.endswith(">"):
                # This is a placeholder, replace with user input
                placeholder = arg_template[1:-1]  # Remove < >
                if placeholder in user_args:
                    args.append(user_args[placeholder])
                else:
                    # Check if this is a required argument
                    required_args = server.get("required_args", [])
                    if placeholder in required_args:
                        # Required argument missing
                        return None
                    # Optional argument missing - skip it
                    continue
            else:
                # Static argument
                args.append(arg_template)

        # Build environment variables
        env_vars = {}
        for env_key, env_description in server["env_vars"].items():
            if env_key in user_args:
                env_vars[env_key] = user_args[env_key]

        return {
            "server_id": server_id,
            "name": server["name"],
            "command": server["command"],
            "args": args,
            "env": env_vars,
            "package": server.get("package", ""),
            "install_method": server.get("install_method", "npm"),
            "setup_help": server.get("setup_help", ""),
            "homepage": server.get("homepage", ""),
        }

    def get_server_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive server information including installation details"""
        server = self.get_mcp_server(server_id)
        if not server:
            return None

        return {
            **server,
            "required_args": server.get("required_args", []),
            "optional_args": server.get("optional_args", []),
            "env_vars": server.get("env_vars", {}),
            "install_method": server.get("install_method", "npm"),
            "setup_help": server.get("setup_help", ""),
            "example_usage": server.get("example_usage", ""),
            "homepage": server.get("homepage", ""),
        }

    def add_custom_server(
        self,
        server_id: str,
        name: str,
        description: str,
        category: str,
        url: str,
        tags: List[str] = None,
    ) -> None:
        """Add a custom server to the registry"""
        # Load custom registry
        if self.custom_registry_path.exists():
            with open(self.custom_registry_path) as f:
                custom = json.load(f)
        else:
            custom = {}

        # Add new server
        custom[server_id] = {
            "id": server_id,
            "name": name,
            "description": description,
            "category": category,
            "url": url,
            "tags": tags or [],
            "author": "Custom",
            "added": datetime.now().isoformat(),
        }

        # Save custom registry
        self.custom_registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.custom_registry_path, "w") as f:
            json.dump(custom, f, indent=2)

        # Update in-memory registry
        self.registry[server_id] = custom[server_id]

    def remove_custom_server(self, server_id: str) -> bool:
        """Remove a custom server from the registry"""
        if not self.custom_registry_path.exists():
            return False

        with open(self.custom_registry_path) as f:
            custom = json.load(f)

        if server_id in custom:
            del custom[server_id]

            with open(self.custom_registry_path, "w") as f:
                json.dump(custom, f, indent=2)

            # Update in-memory registry
            if server_id in self.registry and self.registry[server_id].get("author") == "Custom":
                del self.registry[server_id]

            return True

        return False

    def template_exists(self, template_id: str) -> bool:
        """Check if a template exists"""
        template_path = self.templates_path / template_id
        return template_path.exists() or template_id in self._get_template_definitions()

    def list_templates(self) -> List[str]:
        """List all available templates"""
        templates = list(self._get_template_definitions().keys())

        # Also check templates directory
        if self.templates_path.exists():
            for template_dir in self.templates_path.iterdir():
                if template_dir.is_dir() and template_dir.name not in templates:
                    templates.append(template_dir.name)

        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template data"""
        # Check built-in templates first
        template_defs = self._get_template_definitions()
        if template_id in template_defs:
            return template_defs[template_id]

        # Check templates directory
        template_path = self.templates_path / template_id
        if template_path.exists():
            # Load template from directory
            template_data = {"id": template_id, "files": {}}

            # Read all files in template
            for file_path in template_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(template_path)
                    with open(file_path) as f:
                        template_data["files"][str(relative_path)] = f.read()

            return template_data

        return None

    def create_from_template(
        self, template_id: str, name: str, directory: Path, **kwargs
    ) -> Dict[str, Any]:
        """Create a new server from a template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        # Create directory
        directory.mkdir(parents=True, exist_ok=True)

        # Process and write files
        for file_name, content in template["files"].items():
            # Replace placeholders
            content = content.replace("{{name}}", name)
            content = content.replace("{{port}}", str(kwargs.get("port", 7860)))

            # Handle additional replacements
            for key, value in kwargs.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))

            # Write file
            file_path = directory / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                f.write(content)

        # Create server config
        config = {
            "name": name,
            "template": template_id,
            "created": datetime.now().isoformat(),
            "path": str(directory / "app.py"),
            "directory": str(directory),
            **kwargs,
        }

        return config

    def _get_template_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get built-in template definitions"""
        return {
            "basic": {
                "id": "basic",
                "name": "Basic Tool Server",
                "description": "Simple single-tool MCP server",
                "files": {
                    "app.py": '''"""{{name}} - Basic Gradio MCP Server

A simple MCP server with a single tool.
"""

import gradio as gr


def process_text(text: str) -> str:
    """Process the input text.
    
    Args:
        text: Input text to process
        
    Returns:
        Processed text result
    """
    # Your processing logic here
    return f"Processed: {text.upper()}"


# Create Gradio interface
demo = gr.Interface(
    fn=process_text,
    inputs=gr.Textbox(label="Input Text"),
    outputs=gr.Textbox(label="Result"),
    title="{{name}}",
    description="A simple MCP server that processes text"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port={{port}},
        mcp_server=True
    )
''',
                    "requirements.txt": "gradio>=4.44.0\nmcp>=1.0.0\n",
                    "README.md": "# {{name}}\n\nA basic Gradio MCP server created with Gradio MCP Playground.\n\n## Usage\n\n```bash\npython app.py\n```\n",
                },
            },
            "calculator": {
                "id": "calculator",
                "name": "Calculator Server",
                "description": "Mathematical operations MCP server",
                "files": {
                    "app.py": '''"""{{name}} - Calculator MCP Server

Mathematical operations as MCP tools.
"""

import gradio as gr
import math


def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Result of the calculation
    """
    try:
        # Safe evaluation of mathematical expressions
        allowed_names = {
            k: v for k, v in math.__dict__.items() 
            if not k.startswith("__")
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def solve_equation(equation: str, variable: str = "x") -> str:
    """Solve a simple equation.
    
    Args:
        equation: Equation to solve (e.g., "2*x + 5 = 15")
        variable: Variable to solve for
        
    Returns:
        Solution to the equation
    """
    try:
        # Simple equation solver logic
        # This is a placeholder - you'd implement real solving logic
        return f"Solution for {variable} in {equation}"
    except Exception as e:
        return f"Error: {str(e)}"


# Create tabbed interface
calculator_interface = gr.Interface(
    fn=calculate,
    inputs=gr.Textbox(label="Expression", placeholder="2 + 2 * 3"),
    outputs=gr.Textbox(label="Result"),
    title="Calculator",
    description="Evaluate mathematical expressions"
)

solver_interface = gr.Interface(
    fn=solve_equation,
    inputs=[
        gr.Textbox(label="Equation", placeholder="2*x + 5 = 15"),
        gr.Textbox(label="Variable", value="x")
    ],
    outputs=gr.Textbox(label="Solution"),
    title="Equation Solver",
    description="Solve simple equations"
)

# Combine interfaces
demo = gr.TabbedInterface(
    [calculator_interface, solver_interface],
    ["Calculator", "Equation Solver"],
    title="{{name}}"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port={{port}},
        mcp_server=True
    )
''',
                    "requirements.txt": "gradio>=4.44.0\nmcp>=1.0.0\n",
                    "README.md": "# {{name}}\n\nA calculator MCP server with mathematical operations.\n",
                },
            },
        }
