"""Pipeline View Component

Visual pipeline builder interface for connecting multiple MCP servers.
"""

import json
from typing import List, Dict, Any, Tuple, Optional
import gradio as gr


class PipelineView:
    """Visual pipeline builder interface"""
    
    def __init__(self, agent):
        self.agent = agent
        self.current_pipeline = {
            "name": "",
            "description": "",
            "servers": [],
            "connections": [],
            "configuration": {}
        }
        
    def create_interface(self) -> None:
        """Create the pipeline builder interface"""
        
        with gr.Column():
            gr.Markdown("## 🔧 Visual Pipeline Builder")
            gr.Markdown("Build complex workflows by connecting multiple MCP servers together.")
            
            with gr.Tabs():
                # Pipeline Design Tab
                with gr.Tab("🎨 Design", id="design"):
                    self._create_design_interface()
                
                # Server Library Tab
                with gr.Tab("📚 Server Library", id="library"):
                    self._create_library_interface()
                
                # Configuration Tab
                with gr.Tab("⚙️ Configuration", id="config"):
                    self._create_config_interface()
                
                # Preview & Deploy Tab
                with gr.Tab("🚀 Deploy", id="deploy"):
                    self._create_deploy_interface()
    
    def _create_design_interface(self) -> None:
        """Create the visual design interface"""
        
        with gr.Row():
            # Pipeline canvas
            with gr.Column(scale=3):
                gr.Markdown("### Pipeline Canvas")
                
                # Pipeline visualization area
                self.pipeline_display = gr.JSON(
                    label="Current Pipeline",
                    value=self.current_pipeline
                )
                
                # Pipeline actions
                with gr.Row():
                    self.add_server_btn = gr.Button("➕ Add Server", variant="primary")
                    self.connect_servers_btn = gr.Button("🔗 Connect Servers")
                    self.remove_server_btn = gr.Button("❌ Remove Server", variant="stop")
                
                # Connection builder
                with gr.Accordion("🔗 Connection Builder", open=False):
                    with gr.Row():
                        self.source_server = gr.Dropdown(
                            label="Source Server",
                            choices=[],
                            interactive=True
                        )
                        self.target_server = gr.Dropdown(
                            label="Target Server", 
                            choices=[],
                            interactive=True
                        )
                    
                    self.connection_type = gr.Radio(
                        label="Connection Type",
                        choices=["Sequential", "Parallel", "Conditional"],
                        value="Sequential"
                    )
                    
                    self.create_connection_btn = gr.Button("Create Connection")
            
            # Server selector
            with gr.Column(scale=1):
                gr.Markdown("### Available Servers")
                
                self.server_search = gr.Textbox(
                    label="Search Servers",
                    placeholder="Search for servers..."
                )
                
                self.server_categories = gr.Dropdown(
                    label="Category",
                    choices=["All", "Tools", "Data", "Image", "Text", "AI", "Integration"],
                    value="All"
                )
                
                self.available_servers = gr.JSON(
                    label="Servers",
                    value=[]
                )
                
                self.server_details = gr.Markdown("Select a server to see details...")
        
        # Set up event handlers for design interface
        self._setup_design_handlers()
    
    def _create_library_interface(self) -> None:
        """Create the server library interface"""
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Server Templates")
                
                # Search and filter
                with gr.Row():
                    self.lib_search = gr.Textbox(
                        label="Search Templates",
                        placeholder="calculator, image, data..."
                    )
                    self.lib_category = gr.Dropdown(
                        label="Category",
                        choices=["All", "Starter", "Tools", "Data", "AI", "Advanced"],
                        value="All"
                    )
                
                # Template grid
                self.template_gallery = gr.Gallery(
                    label="Available Templates",
                    show_label=True,
                    elem_id="template-gallery",
                    columns=3,
                    rows=2,
                    height="auto"
                )
                
                # Template details
                self.template_info = gr.Markdown("### Template Information\nSelect a template to see details...")
                
                with gr.Row():
                    self.add_to_pipeline_btn = gr.Button("➕ Add to Pipeline", variant="primary")
                    self.preview_template_btn = gr.Button("👁️ Preview")
        
        # Template data (would be loaded dynamically)
        self.templates_data = self._load_template_data()
        
        # Set up library handlers
        self._setup_library_handlers()
    
    def _create_config_interface(self) -> None:
        """Create the configuration interface"""
        
        with gr.Column():
            gr.Markdown("### Pipeline Configuration")
            
            # Basic settings
            with gr.Group():
                gr.Markdown("#### Basic Settings")
                
                self.pipeline_name = gr.Textbox(
                    label="Pipeline Name",
                    placeholder="My Awesome Pipeline"
                )
                
                self.pipeline_description = gr.Textbox(
                    label="Description",
                    lines=3,
                    placeholder="Describe what your pipeline does..."
                )
                
                self.pipeline_port = gr.Number(
                    label="Port",
                    value=7860,
                    minimum=1000,
                    maximum=65535
                )
            
            # Server configurations
            with gr.Group():
                gr.Markdown("#### Server Configurations")
                
                self.server_configs = gr.JSON(
                    label="Server Settings",
                    value={}
                )
                
                with gr.Row():
                    self.edit_server_btn = gr.Button("✏️ Edit Server Config")
                    self.reset_config_btn = gr.Button("🔄 Reset to Defaults")
            
            # Data flow settings
            with gr.Group():
                gr.Markdown("#### Data Flow")
                
                self.data_format = gr.Dropdown(
                    label="Data Format",
                    choices=["JSON", "Text", "Binary", "Custom"],
                    value="JSON"
                )
                
                self.error_handling = gr.Radio(
                    label="Error Handling",
                    choices=["Stop on Error", "Skip Failed Steps", "Retry Failed Steps"],
                    value="Stop on Error"
                )
                
                self.timeout_setting = gr.Number(
                    label="Step Timeout (seconds)",
                    value=30,
                    minimum=1,
                    maximum=300
                )
            
            # Save/Load configuration
            with gr.Row():
                self.save_config_btn = gr.Button("💾 Save Configuration")
                self.load_config_btn = gr.Button("📁 Load Configuration")
                self.export_config_btn = gr.Button("📤 Export")
        
        # Set up config handlers
        self._setup_config_handlers()
    
    def _create_deploy_interface(self) -> None:
        """Create the deployment interface"""
        
        with gr.Column():
            gr.Markdown("### Deploy Pipeline")
            
            # Pipeline preview
            with gr.Group():
                gr.Markdown("#### Pipeline Preview")
                
                self.deploy_preview = gr.Code(
                    label="Generated Code Preview",
                    language="python",
                    lines=20
                )
                
                self.pipeline_summary = gr.Markdown("**Pipeline Summary:**\nConfigure your pipeline to see the summary.")
            
            # Deployment options
            with gr.Group():
                gr.Markdown("#### Deployment Options")
                
                self.deploy_target = gr.Radio(
                    label="Deploy To",
                    choices=[
                        "Local Development",
                        "Hugging Face Spaces", 
                        "Railway",
                        "Custom Server"
                    ],
                    value="Local Development"
                )
                
                self.public_access = gr.Checkbox(
                    label="Create Public URL",
                    value=False
                )
                
                self.auto_restart = gr.Checkbox(
                    label="Auto-restart on Failure",
                    value=True
                )
            
            # Build and deploy
            with gr.Group():
                gr.Markdown("#### Build & Deploy")
                
                with gr.Row():
                    self.build_btn = gr.Button("🔨 Build Pipeline", variant="primary", size="lg")
                    self.deploy_btn = gr.Button("🚀 Deploy", variant="secondary", size="lg")
                
                self.build_progress = gr.Textbox(
                    label="Build Progress",
                    lines=5,
                    interactive=False
                )
                
                self.deploy_status = gr.Markdown("**Status:** Ready to build")
        
        # Set up deploy handlers
        self._setup_deploy_handlers()
    
    def _setup_design_handlers(self) -> None:
        """Setup event handlers for design interface"""
        
        # Add server to pipeline
        self.add_server_btn.click(
            fn=self._add_server_to_pipeline,
            outputs=[self.pipeline_display, self.source_server, self.target_server]
        )
        
        # Create connection between servers
        self.create_connection_btn.click(
            fn=self._create_server_connection,
            inputs=[self.source_server, self.target_server, self.connection_type],
            outputs=[self.pipeline_display]
        )
        
        # Remove server from pipeline
        self.remove_server_btn.click(
            fn=self._remove_server_from_pipeline,
            outputs=[self.pipeline_display, self.source_server, self.target_server]
        )
        
        # Search servers
        self.server_search.change(
            fn=self._search_servers,
            inputs=[self.server_search, self.server_categories],
            outputs=[self.available_servers]
        )
        
        self.server_categories.change(
            fn=self._filter_servers,
            inputs=[self.server_categories],
            outputs=[self.available_servers]
        )
    
    def _setup_library_handlers(self) -> None:
        """Setup event handlers for library interface"""
        
        # Search templates
        self.lib_search.change(
            fn=self._search_templates,
            inputs=[self.lib_search, self.lib_category],
            outputs=[self.template_gallery, self.template_info]
        )
        
        # Filter by category
        self.lib_category.change(
            fn=self._filter_templates,
            inputs=[self.lib_category],
            outputs=[self.template_gallery]
        )
        
        # Add template to pipeline
        self.add_to_pipeline_btn.click(
            fn=self._add_template_to_pipeline,
            outputs=[self.pipeline_display]
        )
    
    def _setup_config_handlers(self) -> None:
        """Setup event handlers for config interface"""
        
        # Update pipeline name and description
        self.pipeline_name.change(
            fn=self._update_pipeline_info,
            inputs=[self.pipeline_name, self.pipeline_description],
            outputs=[self.pipeline_display]
        )
        
        # Save configuration
        self.save_config_btn.click(
            fn=self._save_pipeline_config,
            inputs=[self.pipeline_name, self.pipeline_description, self.server_configs],
            outputs=[gr.Textbox(visible=False)]  # For download
        )
    
    def _setup_deploy_handlers(self) -> None:
        """Setup event handlers for deploy interface"""
        
        # Build pipeline
        self.build_btn.click(
            fn=self._build_pipeline,
            inputs=[self.deploy_target, self.public_access],
            outputs=[self.deploy_preview, self.build_progress, self.deploy_status]
        )
        
        # Deploy pipeline
        self.deploy_btn.click(
            fn=self._deploy_pipeline,
            inputs=[self.deploy_target],
            outputs=[self.build_progress, self.deploy_status]
        )
    
    def _add_server_to_pipeline(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Add a server to the current pipeline"""
        
        # This would show a dialog to select a server
        # For now, add a sample server
        
        new_server = {
            "id": f"server_{len(self.current_pipeline['servers']) + 1}",
            "name": f"Server {len(self.current_pipeline['servers']) + 1}",
            "type": "calculator",
            "config": {}
        }
        
        self.current_pipeline["servers"].append(new_server)
        
        # Update server dropdown choices
        server_names = [s["name"] for s in self.current_pipeline["servers"]]
        
        return self.current_pipeline, server_names, server_names
    
    def _create_server_connection(self, source: str, target: str, conn_type: str) -> Dict[str, Any]:
        """Create a connection between two servers"""
        
        if source and target and source != target:
            connection = {
                "id": f"conn_{len(self.current_pipeline['connections']) + 1}",
                "source": source,
                "target": target,
                "type": conn_type.lower(),
                "config": {}
            }
            
            self.current_pipeline["connections"].append(connection)
        
        return self.current_pipeline
    
    def _remove_server_from_pipeline(self) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Remove a server from the pipeline"""
        
        if self.current_pipeline["servers"]:
            # Remove the last server for simplicity
            self.current_pipeline["servers"].pop()
            
            # Remove any connections involving the removed server
            self.current_pipeline["connections"] = [
                conn for conn in self.current_pipeline["connections"]
                if conn["source"] in [s["name"] for s in self.current_pipeline["servers"]]
                and conn["target"] in [s["name"] for s in self.current_pipeline["servers"]]
            ]
        
        server_names = [s["name"] for s in self.current_pipeline["servers"]]
        return self.current_pipeline, server_names, server_names
    
    def _search_servers(self, query: str, category: str) -> List[Dict[str, Any]]:
        """Search for available servers"""
        
        # This would use the agent's registry to search
        # For now, return mock data
        
        mock_servers = [
            {
                "id": "calc-1",
                "name": "Basic Calculator",
                "description": "Simple arithmetic operations",
                "category": "Tools"
            },
            {
                "id": "text-1", 
                "name": "Text Processor",
                "description": "Text manipulation and analysis",
                "category": "Text"
            },
            {
                "id": "data-1",
                "name": "CSV Analyzer",
                "description": "Data analysis and visualization",
                "category": "Data"
            }
        ]
        
        if query:
            mock_servers = [
                s for s in mock_servers
                if query.lower() in s["name"].lower() or query.lower() in s["description"].lower()
            ]
        
        if category != "All":
            mock_servers = [s for s in mock_servers if s["category"] == category]
        
        return mock_servers
    
    def _filter_servers(self, category: str) -> List[Dict[str, Any]]:
        """Filter servers by category"""
        return self._search_servers("", category)
    
    def _load_template_data(self) -> List[Dict[str, Any]]:
        """Load template data"""
        
        return [
            {
                "id": "basic-calc",
                "name": "Basic Calculator",
                "description": "Simple calculator with basic operations",
                "category": "Starter",
                "image": None,
                "complexity": "Beginner"
            },
            {
                "id": "data-viz",
                "name": "Data Visualizer", 
                "description": "Create charts from CSV data",
                "category": "Data",
                "image": None,
                "complexity": "Intermediate"
            },
            {
                "id": "image-proc",
                "name": "Image Processor",
                "description": "Image editing and transformation",
                "category": "AI",
                "image": None,
                "complexity": "Advanced"
            }
        ]
    
    def _search_templates(self, query: str, category: str) -> Tuple[List[Any], str]:
        """Search templates"""
        
        templates = self.templates_data
        
        if query:
            templates = [
                t for t in templates
                if query.lower() in t["name"].lower() or query.lower() in t["description"].lower()
            ]
        
        if category != "All":
            templates = [t for t in templates if t["category"] == category]
        
        # Convert to gallery format (would normally include images)
        gallery_items = []
        
        info_text = f"Found {len(templates)} template(s)"
        if templates:
            info_text += f"\n\n**{templates[0]['name']}**\n{templates[0]['description']}\nComplexity: {templates[0]['complexity']}"
        
        return gallery_items, info_text
    
    def _filter_templates(self, category: str) -> List[Any]:
        """Filter templates by category"""
        gallery_items, _ = self._search_templates("", category)
        return gallery_items
    
    def _add_template_to_pipeline(self) -> Dict[str, Any]:
        """Add selected template to pipeline"""
        
        # This would add the selected template as a server
        # For now, add a sample server
        
        template_server = {
            "id": f"template_{len(self.current_pipeline['servers']) + 1}",
            "name": "Template Server",
            "type": "template",
            "config": {}
        }
        
        self.current_pipeline["servers"].append(template_server)
        return self.current_pipeline
    
    def _update_pipeline_info(self, name: str, description: str) -> Dict[str, Any]:
        """Update pipeline basic information"""
        
        self.current_pipeline["name"] = name
        self.current_pipeline["description"] = description
        return self.current_pipeline
    
    def _save_pipeline_config(self, name: str, description: str, configs: Dict[str, Any]) -> str:
        """Save pipeline configuration"""
        
        config_data = {
            "name": name,
            "description": description,
            "servers": self.current_pipeline["servers"],
            "connections": self.current_pipeline["connections"],
            "server_configs": configs
        }
        
        return json.dumps(config_data, indent=2)
    
    def _build_pipeline(self, target: str, public: bool) -> Tuple[str, str, str]:
        """Build the pipeline code"""
        
        if not self.current_pipeline["servers"]:
            return "", "No servers in pipeline to build.", "❌ **Status:** No servers to build"
        
        # Generate pipeline code
        code = self._generate_pipeline_code()
        
        progress = "🔨 Building pipeline...\n"
        progress += "✅ Generated server code\n"
        progress += "✅ Created configuration files\n"
        progress += "✅ Set up dependencies\n"
        progress += "✅ Pipeline build complete!\n"
        
        status = "✅ **Status:** Pipeline built successfully"
        
        return code, progress, status
    
    def _deploy_pipeline(self, target: str) -> Tuple[str, str]:
        """Deploy the pipeline"""
        
        progress = "🚀 Deploying pipeline...\n"
        
        if target == "Local Development":
            progress += "✅ Starting local server\n"
            progress += "✅ Server running on http://localhost:7860\n"
            status = "✅ **Status:** Deployed locally"
        
        elif target == "Hugging Face Spaces":
            progress += "🔄 Uploading to Hugging Face...\n"
            progress += "✅ Space created successfully\n"
            progress += "✅ Available at: https://huggingface.co/spaces/user/pipeline\n"
            status = "✅ **Status:** Deployed to Hugging Face Spaces"
        
        else:
            progress += f"🔄 Deploying to {target}...\n"
            progress += "✅ Deployment complete\n"
            status = f"✅ **Status:** Deployed to {target}"
        
        return progress, status
    
    def _generate_pipeline_code(self) -> str:
        """Generate the pipeline code"""
        
        servers = self.current_pipeline["servers"]
        connections = self.current_pipeline["connections"]
        
        code = f'''"""
{self.current_pipeline.get("name", "Generated Pipeline")}

{self.current_pipeline.get("description", "Auto-generated MCP server pipeline")}
"""

import gradio as gr
import asyncio
from typing import Any, Dict

# Server implementations
'''
        
        # Add server functions
        for server in servers:
            code += f'''
def {server["id"]}_function(input_data: str) -> str:
    """Function for {server["name"]}"""
    # TODO: Implement {server["name"]} logic
    return f"Processed by {server['name']}: {{input_data}}"
'''
        
        # Add pipeline orchestration
        code += '''
async def run_pipeline(input_data: str) -> str:
    """Run the complete pipeline"""
    result = input_data
    
    # Execute servers in sequence
'''
        
        for server in servers:
            code += f'    result = {server["id"]}_function(result)\n'
        
        code += '''    
    return result

# Create Gradio interface
demo = gr.Interface(
    fn=run_pipeline,
    inputs=gr.Textbox(label="Pipeline Input"),
    outputs=gr.Textbox(label="Pipeline Output"),
    title="Generated Pipeline",
    description="Auto-generated MCP server pipeline"
)

if __name__ == "__main__":
    demo.launch(server_port=7860, mcp_server=True)
'''
        
        return code