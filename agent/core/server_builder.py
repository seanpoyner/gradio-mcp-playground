"""Server Builder Module

Handles the construction and generation of MCP servers using the GMP toolkit.
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

# Import from parent GMP project
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from gradio_mcp_playground.registry import ServerRegistry
    from gradio_mcp_playground.config_manager import ConfigManager
    from gradio_mcp_playground.server_manager import GradioMCPServer
except ImportError:
    # Fallback for development
    ServerRegistry = None
    ConfigManager = None
    GradioMCPServer = None


@dataclass
class ServerSpec:
    """Specification for a server to be built"""
    name: str
    description: str
    template: str
    tools: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    dependencies: List[str]
    ui_config: Dict[str, Any]


@dataclass
class BuildResult:
    """Result of a server build operation"""
    success: bool
    server_path: Optional[Path] = None
    config: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ServerBuilder:
    """Builds MCP servers from specifications"""
    
    def __init__(self):
        if ServerRegistry:
            self.registry = ServerRegistry()
        else:
            self.registry = None
        
        if ConfigManager:
            self.config_manager = ConfigManager()
        else:
            self.config_manager = None
    
    async def build_server(self, spec: ServerSpec, output_dir: Path) -> BuildResult:
        """Build a server from specification"""
        
        try:
            # Validate specification
            validation_result = self._validate_spec(spec)
            if not validation_result["valid"]:
                return BuildResult(
                    success=False,
                    errors=validation_result["errors"]
                )
            
            # Create server directory
            server_path = output_dir / spec.name
            server_path.mkdir(parents=True, exist_ok=True)
            
            # Generate server code
            generated_code = await self._generate_server_code(spec)
            
            # Write files
            await self._write_server_files(server_path, generated_code, spec)
            
            # Create configuration
            config = self._create_server_config(spec, server_path)
            
            # Register with GMP if available
            if self.config_manager:
                self.config_manager.add_server(config)
            
            return BuildResult(
                success=True,
                server_path=server_path,
                config=config
            )
            
        except Exception as e:
            return BuildResult(
                success=False,
                errors=[f"Build failed: {str(e)}"]
            )
    
    def _validate_spec(self, spec: ServerSpec) -> Dict[str, Any]:
        """Validate server specification"""
        errors = []
        warnings = []
        
        # Check required fields
        if not spec.name:
            errors.append("Server name is required")
        
        if not spec.description:
            warnings.append("Server description is empty")
        
        if not spec.tools:
            warnings.append("No tools specified - server will have minimal functionality")
        
        # Validate name format
        if spec.name and not spec.name.replace("-", "").replace("_", "").isalnum():
            errors.append("Server name must contain only alphanumeric characters, hyphens, and underscores")
        
        # Check template exists
        if self.registry and spec.template:
            if not self.registry.template_exists(spec.template):
                errors.append(f"Template '{spec.template}' not found")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _generate_server_code(self, spec: ServerSpec) -> Dict[str, str]:
        """Generate server code from specification"""
        
        # Start with template if available
        if self.registry and spec.template:
            template = self.registry.get_template(spec.template)
            if template and "files" in template:
                code_files = template["files"].copy()
            else:
                code_files = self._get_basic_template()
        else:
            code_files = self._get_basic_template()
        
        # Customize the main app.py file
        app_code = await self._generate_app_code(spec)
        code_files["app.py"] = app_code
        
        # Generate requirements.txt
        requirements = self._generate_requirements(spec)
        code_files["requirements.txt"] = requirements
        
        # Generate README.md
        readme = self._generate_readme(spec)
        code_files["README.md"] = readme
        
        # Add configuration files if needed
        if spec.configuration:
            code_files["config.json"] = json.dumps(spec.configuration, indent=2)
        
        return code_files
    
    def _get_basic_template(self) -> Dict[str, str]:
        """Get basic template structure"""
        return {
            "app.py": "# Basic server template\n",
            "requirements.txt": "gradio>=4.44.0\n",
            "README.md": "# Server\n\nGenerated MCP server\n"
        }
    
    async def _generate_app_code(self, spec: ServerSpec) -> str:
        """Generate the main application code"""
        
        # Generate imports
        imports = self._generate_imports(spec)
        
        # Generate tool functions
        tool_functions = self._generate_tool_functions(spec.tools)
        
        # Generate UI components
        ui_components = self._generate_ui_components(spec)
        
        # Generate main interface
        main_interface = self._generate_main_interface(spec)
        
        # Combine all parts
        app_code = f'''"""{spec.name} - {spec.description}

Generated MCP server using GMP Agent.
"""

{imports}

{tool_functions}

{ui_components}

{main_interface}

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port={spec.configuration.get("port", 7860)},
        mcp_server=True,
        share={str(spec.configuration.get("share", False)).lower()}
    )
'''
        
        return app_code
    
    def _generate_imports(self, spec: ServerSpec) -> str:
        """Generate import statements"""
        imports = ["import gradio as gr"]
        
        # Add imports based on tools and dependencies
        if any("math" in tool.get("category", "") for tool in spec.tools):
            imports.append("import math")
        
        if any("data" in tool.get("category", "") for tool in spec.tools):
            imports.append("import pandas as pd")
            imports.append("import numpy as np")
        
        if any("image" in tool.get("category", "") for tool in spec.tools):
            imports.append("from PIL import Image")
        
        if any("text" in tool.get("category", "") for tool in spec.tools):
            imports.append("import re")
        
        # Add custom dependencies
        for dep in spec.dependencies:
            if dep not in ["gradio", "pandas", "numpy", "pillow"]:
                imports.append(f"import {dep}")
        
        return "\n".join(imports) + "\n"
    
    def _generate_tool_functions(self, tools: List[Dict[str, Any]]) -> str:
        """Generate tool function definitions"""
        if not tools:
            return ""
        
        functions = []
        
        for tool in tools:
            func_name = tool.get("name", "process").lower().replace(" ", "_")
            func_description = tool.get("description", "Process input")
            func_params = tool.get("parameters", [])
            func_category = tool.get("category", "general")
            
            # Generate function signature
            params = []
            for param in func_params:
                param_name = param.get("name", "input")
                param_type = param.get("type", "str")
                params.append(f"{param_name}: {param_type}")
            
            param_signature = ", ".join(params) if params else "input_data: str"
            
            # Generate function body based on category
            func_body = self._generate_function_body(func_category, tool)
            
            function_code = f'''
def {func_name}({param_signature}) -> str:
    """{func_description}
    
    Args:
        {param_signature.split(":")[0]}: Input data to process
        
    Returns:
        Processed result
    """
{func_body}
'''
            functions.append(function_code)
        
        return "\n".join(functions)
    
    def _generate_function_body(self, category: str, tool: Dict[str, Any]) -> str:
        """Generate function body based on category"""
        
        if category == "math" or "calculator" in tool.get("name", "").lower():
            return '''    try:
        # Safe evaluation of mathematical expressions
        allowed_names = {
            k: v for k, v in math.__dict__.items() 
            if not k.startswith("__")
        }
        result = eval(input_data, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"'''
        
        elif category == "text":
            return '''    try:
        # Process text input
        if isinstance(input_data, str):
            # Example: convert to uppercase
            result = input_data.upper()
            return f"Processed: {result}"
        else:
            return "Please provide text input"
    except Exception as e:
        return f"Error: {str(e)}"'''
        
        elif category == "data":
            return '''    try:
        # Process data input
        if isinstance(input_data, str):
            # Example: basic data analysis
            lines = input_data.strip().split("\\n")
            result = f"Lines: {len(lines)}, Characters: {len(input_data)}"
            return result
        else:
            return "Please provide data input"
    except Exception as e:
        return f"Error: {str(e)}"'''
        
        else:
            return '''    try:
        # Generic processing
        result = f"Processed: {str(input_data)}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"'''
    
    def _generate_ui_components(self, spec: ServerSpec) -> str:
        """Generate UI component definitions"""
        
        ui_config = spec.ui_config
        layout = ui_config.get("layout", "single")
        
        if layout == "tabbed" and len(spec.tools) > 1:
            return self._generate_tabbed_interface(spec)
        else:
            return self._generate_single_interface(spec)
    
    def _generate_single_interface(self, spec: ServerSpec) -> str:
        """Generate single interface"""
        
        if not spec.tools:
            return '''
# Create basic interface
demo = gr.Interface(
    fn=lambda x: f"Processed: {x}",
    inputs=gr.Textbox(label="Input"),
    outputs=gr.Textbox(label="Output"),
    title=f"{spec.name}",
    description=f"{spec.description}"
)
'''
        
        tool = spec.tools[0]
        func_name = tool.get("name", "process").lower().replace(" ", "_")
        
        return f'''
# Create single interface
demo = gr.Interface(
    fn={func_name},
    inputs=gr.Textbox(label="Input", placeholder="Enter your input here"),
    outputs=gr.Textbox(label="Result"),
    title="{spec.name}",
    description="{spec.description}"
)
'''
    
    def _generate_tabbed_interface(self, spec: ServerSpec) -> str:
        """Generate tabbed interface for multiple tools"""
        
        interfaces = []
        tab_names = []
        
        for tool in spec.tools:
            func_name = tool.get("name", "process").lower().replace(" ", "_")
            tool_name = tool.get("name", "Tool")
            tool_desc = tool.get("description", "Tool description")
            
            interface_code = f'''gr.Interface(
    fn={func_name},
    inputs=gr.Textbox(label="Input"),
    outputs=gr.Textbox(label="Result"),
    title="{tool_name}",
    description="{tool_desc}"
)'''
            
            interfaces.append(interface_code)
            tab_names.append(f'"{tool_name}"')
        
        return f'''
# Create tabbed interface
interfaces = [
    {",\\n    ".join(interfaces)}
]

demo = gr.TabbedInterface(
    interfaces,
    [{", ".join(tab_names)}],
    title="{spec.name}"
)
'''
    
    def _generate_main_interface(self, spec: ServerSpec) -> str:
        """Generate main interface setup"""
        
        if spec.ui_config.get("layout") == "custom":
            return self._generate_custom_interface(spec)
        else:
            return ""  # Interface already generated in UI components
    
    def _generate_custom_interface(self, spec: ServerSpec) -> str:
        """Generate custom Blocks interface"""
        
        return f'''
# Create custom interface with Blocks
with gr.Blocks(title="{spec.name}") as demo:
    gr.Markdown("# {spec.name}")
    gr.Markdown("{spec.description}")
    
    # Add your custom components here
    with gr.Row():
        input_box = gr.Textbox(label="Input")
        output_box = gr.Textbox(label="Output")
    
    submit_btn = gr.Button("Process")
    
    # Add event handlers
    submit_btn.click(
        fn=lambda x: f"Processed: {{x}}",
        inputs=input_box,
        outputs=output_box
    )
'''
    
    def _generate_requirements(self, spec: ServerSpec) -> str:
        """Generate requirements.txt content"""
        
        requirements = ["gradio>=4.44.0"]
        
        # Add dependencies based on tools
        if any("math" in tool.get("category", "") for tool in spec.tools):
            requirements.append("numpy>=1.24.0")
        
        if any("data" in tool.get("category", "") for tool in spec.tools):
            requirements.append("pandas>=2.0.0")
            requirements.append("numpy>=1.24.0")
        
        if any("image" in tool.get("category", "") for tool in spec.tools):
            requirements.append("Pillow>=10.0.0")
        
        # Add custom dependencies
        for dep in spec.dependencies:
            if dep not in requirements:
                requirements.append(dep)
        
        # Add MCP support
        requirements.append("mcp>=1.0.0")
        
        return "\n".join(requirements) + "\n"
    
    def _generate_readme(self, spec: ServerSpec) -> str:
        """Generate README.md content"""
        
        tools_section = ""
        if spec.tools:
            tools_section = "## Tools\n\n"
            for tool in spec.tools:
                tools_section += f"- **{tool.get('name', 'Tool')}**: {tool.get('description', 'No description')}\n"
            tools_section += "\n"
        
        return f'''# {spec.name}

{spec.description}

Generated using GMP Agent - an intelligent assistant for building MCP servers.

{tools_section}## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The server will start on the configured port (default: 7860) and can be accessed via web browser.

## MCP Integration

This server is built with MCP (Model Context Protocol) support, allowing it to be used as a tool in AI workflows.

## Configuration

Configuration options can be found in `config.json` (if present) or modified directly in `app.py`.

---

Built with ❤️ using Gradio MCP Playground and GMP Agent.
'''
    
    async def _write_server_files(self, server_path: Path, code_files: Dict[str, str], spec: ServerSpec) -> None:
        """Write generated files to disk"""
        
        for filename, content in code_files.items():
            file_path = server_path / filename
            
            # Create subdirectories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _create_server_config(self, spec: ServerSpec, server_path: Path) -> Dict[str, Any]:
        """Create server configuration for GMP"""
        
        config = {
            "name": spec.name,
            "description": spec.description,
            "template": spec.template,
            "path": str(server_path / "app.py"),
            "directory": str(server_path),
            "created": "2024-01-01T00:00:00",  # Would use actual timestamp
            "tools": spec.tools,
            **spec.configuration
        }
        
        return config
    
    async def test_server(self, server_path: Path) -> Dict[str, Any]:
        """Test a built server"""
        
        try:
            # Run basic syntax check
            result = subprocess.run(
                ["python", "-m", "py_compile", str(server_path / "app.py")],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Syntax error in generated code",
                    "details": result.stderr
                }
            
            # TODO: Add more comprehensive testing
            # - Import test
            # - Function execution test
            # - UI component test
            
            return {
                "success": True,
                "message": "Server passed basic tests"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test failed: {str(e)}"
            }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates"""
        
        if not self.registry:
            return [
                {
                    "id": "basic",
                    "name": "Basic Server",
                    "description": "Simple single-tool server"
                }
            ]
        
        templates = []
        for template_id in self.registry.list_templates():
            template_info = self.registry.get_server(template_id)
            if template_info:
                templates.append({
                    "id": template_id,
                    "name": template_info.get("name", template_id),
                    "description": template_info.get("description", "No description")
                })
        
        return templates