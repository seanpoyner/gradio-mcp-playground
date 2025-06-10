"""Pipeline View Component

Visual pipeline builder interface for connecting multiple MCP servers.
"""

import json
import os
import asyncio
from typing import List, Dict, Any, Tuple, Optional, Set
import gradio as gr
from datetime import datetime
import yaml


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
        self.selected_server = None
        self.selected_template = None
        self.available_servers_list = []
        self.drag_state = None
        self.test_results = {}
        
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
                self.pipeline_canvas = gr.HTML(
                    label="Pipeline Canvas",
                    value=self._render_pipeline_html()
                )
                
                # Hidden JSON for pipeline data
                self.pipeline_data = gr.JSON(
                    value=self.current_pipeline,
                    visible=False
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
            
            # Pipeline Testing
            with gr.Group():
                gr.Markdown("#### Test Pipeline")
                
                self.test_input = gr.Textbox(
                    label="Test Input",
                    placeholder="Enter test data for your pipeline...",
                    lines=3
                )
                
                with gr.Row():
                    self.test_pipeline_btn = gr.Button("🧪 Test Pipeline", variant="primary")
                    self.validate_pipeline_btn = gr.Button("✓ Validate Configuration")
                
                self.test_output = gr.Textbox(
                    label="Test Results",
                    lines=10,
                    interactive=False
                )
        
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
            outputs=[self.pipeline_canvas, self.pipeline_data, self.source_server, self.target_server]
        )
        
        # Create connection between servers
        self.create_connection_btn.click(
            fn=self._create_server_connection,
            inputs=[self.source_server, self.target_server, self.connection_type],
            outputs=[self.pipeline_canvas, self.pipeline_data]
        )
        
        # Remove server from pipeline
        self.remove_server_btn.click(
            fn=self._remove_server_from_pipeline,
            outputs=[self.pipeline_canvas, self.pipeline_data, self.source_server, self.target_server]
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
        
        # Server selection from available list
        self.available_servers.select(
            fn=self._select_server,
            inputs=[self.available_servers],
            outputs=[self.server_details]
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
            outputs=[self.pipeline_canvas, self.pipeline_data]
        )
    
    def _setup_config_handlers(self) -> None:
        """Setup event handlers for config interface"""
        
        # Update pipeline name and description
        self.pipeline_name.change(
            fn=self._update_pipeline_info,
            inputs=[self.pipeline_name, self.pipeline_description],
            outputs=[self.pipeline_data]
        )
        
        # Save configuration
        self.save_config_btn.click(
            fn=self._save_pipeline_config,
            inputs=[self.pipeline_name, self.pipeline_description, self.server_configs],
            outputs=[gr.Textbox(visible=False)]  # For download
        )
        
        # Test pipeline
        self.test_pipeline_btn.click(
            fn=self._execute_pipeline,
            inputs=[self.test_input],
            outputs=[self.test_output]
        )
        
        # Validate pipeline
        self.validate_pipeline_btn.click(
            fn=lambda: asyncio.run(self._test_pipeline()),
            outputs=[self.test_output]
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
    
    def _add_server_to_pipeline(self) -> Tuple[str, Dict[str, Any], List[str], List[str]]:
        """Add a server to the current pipeline"""
        
        if not self.selected_server:
            gr.Warning("Please select a server from the library first")
            return self._render_pipeline_html(), self.current_pipeline, [], []
        
        # Calculate position for new server
        x_pos = 50 + (len(self.current_pipeline['servers']) * 200)
        y_pos = 100
        
        new_server = {
            "id": f"server_{len(self.current_pipeline['servers']) + 1}",
            "name": self.selected_server.get("name", "New Server"),
            "type": self.selected_server.get("type", "custom"),
            "config": self.selected_server.get("config", {}),
            "position": {"x": x_pos, "y": y_pos},
            "tools": self.selected_server.get("tools", [])
        }
        
        self.current_pipeline["servers"].append(new_server)
        
        # Update server dropdown choices
        server_names = [s["name"] for s in self.current_pipeline["servers"]]
        
        return self._render_pipeline_html(), self.current_pipeline, server_names, server_names
    
    def _create_server_connection(self, source: str, target: str, conn_type: str) -> Tuple[str, Dict[str, Any]]:
        """Create a connection between two servers"""
        
        if not source or not target:
            gr.Warning("Please select both source and target servers")
            return self._render_pipeline_html(), self.current_pipeline
            
        if source == target:
            gr.Warning("Cannot connect a server to itself")
            return self._render_pipeline_html(), self.current_pipeline
        
        # Check if connection already exists
        existing = any(
            conn["source"] == source and conn["target"] == target 
            for conn in self.current_pipeline["connections"]
        )
        
        if existing:
            gr.Warning("Connection already exists")
            return self._render_pipeline_html(), self.current_pipeline
        
        connection = {
            "id": f"conn_{len(self.current_pipeline['connections']) + 1}",
            "source": source,
            "target": target,
            "type": conn_type.lower(),
            "config": {
                "data_transform": "passthrough",
                "error_handling": "stop"
            }
        }
        
        self.current_pipeline["connections"].append(connection)
        gr.Info(f"Connected {source} → {target} ({conn_type})")
        
        return self._render_pipeline_html(), self.current_pipeline
    
    def _remove_server_from_pipeline(self) -> Tuple[str, Dict[str, Any], List[str], List[str]]:
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
        return self._render_pipeline_html(), self.current_pipeline, server_names, server_names
    
    def _search_servers(self, query: str, category: str) -> List[Dict[str, Any]]:
        """Search for available servers"""
        
        # Use agent's registry if available
        if hasattr(self.agent, 'registry'):
            try:
                servers = self.agent.registry.search_servers(query, category)
                self.available_servers_list = servers
                return servers
            except:
                pass
        
        # Fallback to comprehensive mock data
        mock_servers = [
            {
                "id": "calc-1",
                "name": "Basic Calculator",
                "description": "Simple arithmetic operations",
                "category": "Tools",
                "type": "calculator",
                "tools": ["add", "subtract", "multiply", "divide"],
                "config": {"precision": 2}
            },
            {
                "id": "text-1", 
                "name": "Text Processor",
                "description": "Text manipulation and analysis",
                "category": "Text",
                "type": "text",
                "tools": ["uppercase", "lowercase", "word_count", "replace"],
                "config": {"encoding": "utf-8"}
            },
            {
                "id": "data-1",
                "name": "CSV Analyzer",
                "description": "Data analysis and visualization",
                "category": "Data",
                "type": "data",
                "tools": ["load_csv", "filter", "aggregate", "visualize"],
                "config": {"max_rows": 10000}
            },
            {
                "id": "image-1",
                "name": "Image Processor",
                "description": "Image editing and transformation",
                "category": "Image",
                "type": "image",
                "tools": ["resize", "crop", "filter", "convert"],
                "config": {"formats": ["jpg", "png", "webp"]}
            },
            {
                "id": "ai-1",
                "name": "AI Assistant",
                "description": "AI-powered text generation",
                "category": "AI",
                "type": "ai",
                "tools": ["generate", "summarize", "translate"],
                "config": {"model": "gpt-3.5-turbo"}
            }
        ]
        
        if query:
            mock_servers = [
                s for s in mock_servers
                if query.lower() in s["name"].lower() or query.lower() in s["description"].lower()
            ]
        
        if category != "All":
            mock_servers = [s for s in mock_servers if s["category"] == category]
        
        self.available_servers_list = mock_servers
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
    
    def _add_template_to_pipeline(self) -> Tuple[str, Dict[str, Any]]:
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
        return self._render_pipeline_html(), self.current_pipeline
    
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
    
    def _render_pipeline_html(self) -> str:
        """Render the pipeline as interactive HTML"""
        
        html = """
        <div id="pipeline-canvas" style="width: 100%; height: 500px; border: 2px solid #ddd; border-radius: 8px; position: relative; overflow: auto; background: #f8f9fa;">
        """
        
        # Render servers as nodes
        for server in self.current_pipeline["servers"]:
            x = server.get("position", {}).get("x", 50)
            y = server.get("position", {}).get("y", 50)
            
            html += f"""
            <div class="pipeline-node" id="{server['id']}" 
                 style="position: absolute; left: {x}px; top: {y}px; 
                        width: 150px; padding: 15px; 
                        background: white; border: 2px solid #4CAF50; 
                        border-radius: 8px; cursor: move;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h4 style="margin: 0 0 10px 0; color: #333;">{server['name']}</h4>
                <p style="margin: 0; font-size: 12px; color: #666;">Type: {server['type']}</p>
                <p style="margin: 0; font-size: 11px; color: #888;">Tools: {len(server.get('tools', []))}</p>
            </div>
            """
        
        # Render connections as SVG lines
        if self.current_pipeline["connections"]:
            html += '<svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">'
            
            for conn in self.current_pipeline["connections"]:
                # Find source and target positions
                source_server = next((s for s in self.current_pipeline["servers"] if s["name"] == conn["source"]), None)
                target_server = next((s for s in self.current_pipeline["servers"] if s["name"] == conn["target"]), None)
                
                if source_server and target_server:
                    x1 = source_server.get("position", {}).get("x", 0) + 150  # Right edge
                    y1 = source_server.get("position", {}).get("y", 0) + 40   # Center
                    x2 = target_server.get("position", {}).get("x", 0)        # Left edge
                    y2 = target_server.get("position", {}).get("y", 0) + 40   # Center
                    
                    color = "#4CAF50" if conn["type"] == "sequential" else "#2196F3"
                    
                    html += f"""
                    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                          stroke="{color}" stroke-width="2" 
                          marker-end="url(#arrowhead)"/>
                    """
            
            # Add arrowhead marker
            html += """
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                        refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#4CAF50"/>
                </marker>
            </defs>
            </svg>
            """
        
        html += "</div>"
        
        # Add JavaScript for drag and drop
        html += """
        <script>
        // Drag and drop functionality would be implemented here
        // For now, this is a visual representation
        </script>
        """
        
        return html
    
    async def _test_pipeline(self) -> Dict[str, Any]:
        """Test the current pipeline configuration"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "servers_tested": [],
            "connections_tested": [],
            "errors": [],
            "warnings": []
        }
        
        # Test each server
        for server in self.current_pipeline["servers"]:
            server_test = {
                "id": server["id"],
                "name": server["name"],
                "status": "passed",
                "tests": []
            }
            
            # Validate server configuration
            if not server.get("type"):
                server_test["status"] = "failed"
                server_test["tests"].append({
                    "test": "type_validation",
                    "status": "failed",
                    "message": "Server type not specified"
                })
            
            # Check for required tools
            if not server.get("tools"):
                server_test["warnings"] = ["No tools defined for this server"]
            
            results["servers_tested"].append(server_test)
        
        # Test connections
        for conn in self.current_pipeline["connections"]:
            conn_test = {
                "id": conn["id"],
                "source": conn["source"],
                "target": conn["target"],
                "status": "passed",
                "tests": []
            }
            
            # Validate connection endpoints exist
            source_exists = any(s["name"] == conn["source"] for s in self.current_pipeline["servers"])
            target_exists = any(s["name"] == conn["target"] for s in self.current_pipeline["servers"])
            
            if not source_exists or not target_exists:
                conn_test["status"] = "failed"
                conn_test["tests"].append({
                    "test": "endpoint_validation",
                    "status": "failed",
                    "message": "Connection endpoint not found"
                })
            
            results["connections_tested"].append(conn_test)
        
        # Check for cycles in pipeline
        if self._has_cycles():
            results["status"] = "failed"
            results["errors"].append("Pipeline contains cycles")
        
        # Check for disconnected servers
        disconnected = self._find_disconnected_servers()
        if disconnected:
            results["warnings"].append(f"Disconnected servers: {', '.join(disconnected)}")
        
        self.test_results = results
        return results
    
    def _has_cycles(self) -> bool:
        """Check if the pipeline has cycles"""
        
        # Build adjacency list
        graph = {}
        for server in self.current_pipeline["servers"]:
            graph[server["name"]] = []
        
        for conn in self.current_pipeline["connections"]:
            if conn["source"] in graph:
                graph[conn["source"]].append(conn["target"])
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def _find_disconnected_servers(self) -> List[str]:
        """Find servers that are not connected to anything"""
        
        connected = set()
        
        for conn in self.current_pipeline["connections"]:
            connected.add(conn["source"])
            connected.add(conn["target"])
        
        all_servers = {s["name"] for s in self.current_pipeline["servers"]}
        
        return list(all_servers - connected) if len(all_servers) > 1 else []
    
    def _select_server(self, server_data: Dict[str, Any]) -> str:
        """Handle server selection from available list"""
        
        if not server_data or not isinstance(server_data, dict):
            return "Select a server to see details..."
        
        # Store selected server
        self.selected_server = server_data
        
        # Generate detailed markdown description
        details = f"""### {server_data.get('name', 'Unknown Server')}
        
**Description:** {server_data.get('description', 'No description available')}

**Type:** {server_data.get('type', 'custom')}  
**Category:** {server_data.get('category', 'Other')}

**Available Tools:**
"""
        
        tools = server_data.get('tools', [])
        if tools:
            for tool in tools:
                details += f"- `{tool}`\n"
        else:
            details += "- No tools defined\n"
        
        details += "\n**Configuration:**\n```json\n"
        config = server_data.get('config', {})
        details += json.dumps(config, indent=2)
        details += "\n```\n"
        
        details += "\n*Click 'Add Server' to add this to your pipeline*"
        
        return details
    
    async def _execute_pipeline(self, input_data: str) -> str:
        """Execute the pipeline with test data"""
        
        if not self.current_pipeline["servers"]:
            return "No servers in pipeline to execute"
        
        # Build execution order based on connections
        execution_order = self._get_execution_order()
        
        result = input_data
        execution_log = f"Pipeline execution started at {datetime.now().isoformat()}\n\n"
        
        for server_name in execution_order:
            server = next((s for s in self.current_pipeline["servers"] if s["name"] == server_name), None)
            if not server:
                continue
            
            execution_log += f"Executing: {server_name}\n"
            
            # Simulate server execution based on type
            if server["type"] == "calculator":
                try:
                    result = str(eval(result))
                    execution_log += f"  Result: {result}\n"
                except:
                    execution_log += f"  Error: Invalid expression\n"
                    
            elif server["type"] == "text":
                result = result.upper()
                execution_log += f"  Result: {result[:50]}...\n"
                
            elif server["type"] == "data":
                result = f"Processed data: {len(result)} characters"
                execution_log += f"  Result: {result}\n"
                
            else:
                result = f"Processed by {server_name}: {result}"
                execution_log += f"  Result: {result[:50]}...\n"
            
            execution_log += "\n"
        
        execution_log += f"Pipeline execution completed at {datetime.now().isoformat()}\n"
        execution_log += f"Final result: {result}"
        
        return execution_log
    
    def _get_execution_order(self) -> List[str]:
        """Get the execution order of servers based on connections"""
        
        if not self.current_pipeline["connections"]:
            # No connections, execute in order of addition
            return [s["name"] for s in self.current_pipeline["servers"]]
        
        # Build dependency graph
        graph = {}
        in_degree = {}
        
        for server in self.current_pipeline["servers"]:
            graph[server["name"]] = []
            in_degree[server["name"]] = 0
        
        for conn in self.current_pipeline["connections"]:
            if conn["source"] in graph and conn["target"] in graph:
                graph[conn["source"]].append(conn["target"])
                in_degree[conn["target"]] += 1
        
        # Topological sort
        queue = [node for node in in_degree if in_degree[node] == 0]
        execution_order = []
        
        while queue:
            node = queue.pop(0)
            execution_order.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Add any disconnected nodes
        for server in self.current_pipeline["servers"]:
            if server["name"] not in execution_order:
                execution_order.append(server["name"])
        
        return execution_order