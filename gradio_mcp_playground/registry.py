"""Gradio MCP Server Registry

Registry of available Gradio MCP servers and templates.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ServerRegistry:
    """Registry for Gradio MCP servers and templates"""
    
    def __init__(self):
        self.registry_path = Path(__file__).parent / "registry.json"
        self.templates_path = Path(__file__).parent / "templates"
        self.custom_registry_path = Path.home() / ".gradio-mcp" / "custom_registry.json"
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load the server registry"""
        # Load built-in registry
        self.registry = self._get_builtin_registry()
        
        # Load custom registry if exists
        if self.custom_registry_path.exists():
            with open(self.custom_registry_path) as f:
                custom = json.load(f)
            
            # Merge custom entries
            self.registry.update(custom)
    
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
                "url": "https://github.com/gradio-mcp-playground/templates/basic-tool"
            },
            "calculator": {
                "id": "calculator",
                "name": "Calculator Server",
                "description": "Mathematical operations MCP server",
                "category": "tools",
                "author": "Gradio MCP Playground",
                "tags": ["math", "calculator", "tools"],
                "url": "https://github.com/gradio-mcp-playground/templates/calculator"
            },
            "image-generator": {
                "id": "image-generator",
                "name": "Image Generator Server",
                "description": "AI image generation MCP server using Stable Diffusion",
                "category": "ai",
                "author": "Gradio MCP Playground",
                "tags": ["ai", "image", "generation", "stable-diffusion"],
                "url": "https://github.com/gradio-mcp-playground/templates/image-generator"
            },
            "data-analyzer": {
                "id": "data-analyzer",
                "name": "Data Analyzer Server",
                "description": "CSV and data analysis MCP server",
                "category": "data",
                "author": "Gradio MCP Playground",
                "tags": ["data", "csv", "analysis", "pandas"],
                "url": "https://github.com/gradio-mcp-playground/templates/data-analyzer"
            },
            "file-processor": {
                "id": "file-processor",
                "name": "File Processor Server",
                "description": "File manipulation and processing MCP server",
                "category": "tools",
                "author": "Gradio MCP Playground",
                "tags": ["files", "processing", "tools"],
                "url": "https://github.com/gradio-mcp-playground/templates/file-processor"
            },
            "web-scraper": {
                "id": "web-scraper",
                "name": "Web Scraper Server",
                "description": "Web scraping and data extraction MCP server",
                "category": "web",
                "author": "Gradio MCP Playground",
                "tags": ["web", "scraping", "extraction"],
                "url": "https://github.com/gradio-mcp-playground/templates/web-scraper"
            },
            "llm-tools": {
                "id": "llm-tools",
                "name": "LLM Tools Server",
                "description": "LLM-powered tools (summarization, translation, etc.)",
                "category": "ai",
                "author": "Gradio MCP Playground",
                "tags": ["ai", "llm", "nlp", "tools"],
                "url": "https://github.com/gradio-mcp-playground/templates/llm-tools"
            },
            "api-wrapper": {
                "id": "api-wrapper",
                "name": "API Wrapper Server",
                "description": "Wrap any API as an MCP server",
                "category": "integration",
                "author": "Gradio MCP Playground",
                "tags": ["api", "integration", "wrapper"],
                "url": "https://github.com/gradio-mcp-playground/templates/api-wrapper"
            },
            "multi-tool": {
                "id": "multi-tool",
                "name": "Multi-Tool Server",
                "description": "MCP server with multiple tools in tabs",
                "category": "advanced",
                "author": "Gradio MCP Playground",
                "tags": ["multi-tool", "advanced", "tabs"],
                "url": "https://github.com/gradio-mcp-playground/templates/multi-tool"
            },
            "custom-ui": {
                "id": "custom-ui",
                "name": "Custom UI Server",
                "description": "MCP server with custom Gradio components",
                "category": "advanced",
                "author": "Gradio MCP Playground",
                "tags": ["ui", "custom", "advanced"],
                "url": "https://github.com/gradio-mcp-playground/templates/custom-ui"
            }
        }
    
    def search(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for servers in the registry"""
        query = query.lower()
        results = []
        
        for server_id, server_info in self.registry.items():
            # Filter by category if specified
            if category and server_info.get("category") != category:
                continue
            
            # Search in various fields
            searchable = [
                server_id,
                server_info.get("name", "").lower(),
                server_info.get("description", "").lower(),
                " ".join(server_info.get("tags", [])).lower()
            ]
            
            if any(query in field for field in searchable):
                results.append(server_info)
        
        return results
    
    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all servers in a category"""
        return [
            server for server in self.registry.values()
            if server.get("category") == category
        ]
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all servers in the registry"""
        return list(self.registry.values())
    
    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific server by ID"""
        return self.registry.get(server_id)
    
    def list_categories(self) -> List[str]:
        """List all available categories"""
        categories = set()
        for server in self.registry.values():
            if "category" in server:
                categories.add(server["category"])
        return sorted(list(categories))
    
    def add_custom_server(
        self,
        server_id: str,
        name: str,
        description: str,
        category: str,
        url: str,
        tags: List[str] = None
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
            "added": datetime.now().isoformat()
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
            template_data = {
                "id": template_id,
                "files": {}
            }
            
            # Read all files in template
            for file_path in template_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(template_path)
                    with open(file_path) as f:
                        template_data["files"][str(relative_path)] = f.read()
            
            return template_data
        
        return None
    
    def create_from_template(
        self,
        template_id: str,
        name: str,
        directory: Path,
        **kwargs
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
            **kwargs
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
                    "README.md": "# {{name}}\n\nA basic Gradio MCP server created with Gradio MCP Playground.\n\n## Usage\n\n```bash\npython app.py\n```\n"
                }
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
                    "README.md": "# {{name}}\n\nA calculator MCP server with mathematical operations.\n"
                }
            }
        }
