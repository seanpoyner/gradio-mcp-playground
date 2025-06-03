"""Server Manager Component

Interface for managing MCP servers - viewing status, starting/stopping, 
configuring, and monitoring servers.
"""

import asyncio
import subprocess
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import gradio as gr


class ServerManager:
    """Server management interface"""
    
    def __init__(self, agent):
        self.agent = agent
        self.servers_data = []
        self.selected_server = None
        
    def create_interface(self) -> None:
        """Create the server management interface"""
        
        with gr.Column():
            gr.Markdown("## 🖥️ Server Management")
            gr.Markdown("Monitor and manage your MCP servers.")
            
            with gr.Tabs():
                # Server Overview Tab
                with gr.Tab("📊 Overview", id="overview"):
                    self._create_overview_interface()
                
                # Server Details Tab
                with gr.Tab("🔍 Details", id="details"):
                    self._create_details_interface()
                
                # Logs & Monitoring Tab
                with gr.Tab("📈 Monitoring", id="monitoring"):
                    self._create_monitoring_interface()
                
                # Settings Tab
                with gr.Tab("⚙️ Settings", id="settings"):
                    self._create_settings_interface()
    
    def _create_overview_interface(self) -> None:
        """Create the server overview interface"""
        
        with gr.Row():
            # Server list
            with gr.Column(scale=2):
                gr.Markdown("### Your Servers")
                
                # Refresh and actions
                with gr.Row():
                    self.refresh_btn = gr.Button("🔄 Refresh", size="sm")
                    self.create_new_btn = gr.Button("➕ Create New", variant="primary", size="sm")
                    self.import_btn = gr.Button("📥 Import", size="sm")
                
                # Server table
                self.servers_table = gr.Dataframe(
                    headers=["Name", "Status", "Port", "Type", "Last Modified"],
                    datatype=["str", "str", "number", "str", "str"],
                    interactive=False,
                    wrap=True,
                    value=self._get_mock_servers_data()
                )
                
                # Quick actions
                with gr.Row():
                    self.start_btn = gr.Button("▶️ Start", variant="primary")
                    self.stop_btn = gr.Button("⏹️ Stop", variant="stop") 
                    self.restart_btn = gr.Button("🔄 Restart")
                    self.delete_btn = gr.Button("🗑️ Delete", variant="stop")
            
            # Server status panel
            with gr.Column(scale=1):
                gr.Markdown("### Quick Status")
                
                # Status cards
                self.total_servers = gr.Number(
                    label="Total Servers",
                    value=3,
                    interactive=False
                )
                
                self.running_servers = gr.Number(
                    label="Running",
                    value=1,
                    interactive=False
                )
                
                self.stopped_servers = gr.Number(
                    label="Stopped",
                    value=2,
                    interactive=False
                )
                
                # Recent activity
                gr.Markdown("### Recent Activity")
                self.activity_log = gr.Textbox(
                    label="",
                    value="🟢 calculator-server started at 14:30\n🔴 data-processor stopped at 14:25\n🟡 image-tool restarted at 14:20",
                    lines=5,
                    interactive=False,
                    show_label=False
                )
                
                # System resources
                gr.Markdown("### System Resources")
                with gr.Row():
                    self.cpu_usage = gr.Number(
                        label="CPU %",
                        value=45,
                        interactive=False
                    )
                    self.memory_usage = gr.Number(
                        label="Memory %", 
                        value=32,
                        interactive=False
                    )
        
        # Set up overview handlers
        self._setup_overview_handlers()
    
    def _create_details_interface(self) -> None:
        """Create the server details interface"""
        
        with gr.Row():
            # Server selector
            with gr.Column(scale=1):
                gr.Markdown("### Select Server")
                
                self.server_selector = gr.Dropdown(
                    label="Server",
                    choices=["calculator-server", "data-processor", "image-tool"],
                    value="calculator-server",
                    interactive=True
                )
                
                # Server info panel
                self.server_info_panel = gr.Markdown("""
**Server:** calculator-server  
**Status:** 🟢 Running  
**Port:** 7860  
**Type:** Calculator  
**Created:** 2024-01-15  
**Last Modified:** 2024-01-20  
                """)
                
                # Quick actions
                with gr.Column():
                    self.open_browser_btn = gr.Button("🌐 Open in Browser", variant="primary")
                    self.view_code_btn = gr.Button("📝 View Code")
                    self.edit_config_btn = gr.Button("⚙️ Edit Config")
                    self.backup_btn = gr.Button("💾 Backup")
            
            # Server details
            with gr.Column(scale=2):
                gr.Markdown("### Server Details")
                
                with gr.Tabs():
                    # Configuration tab
                    with gr.Tab("Configuration"):
                        self.server_config = gr.Code(
                            label="Server Configuration",
                            language="json",
                            value='''{
  "name": "calculator-server",
  "port": 7860,
  "mcp_server": true,
  "share": false,
  "tools": [
    {
      "name": "calculate",
      "description": "Perform mathematical calculations"
    }
  ]
}''',
                            lines=15
                        )
                    
                    # Files tab
                    with gr.Tab("Files"):
                        self.server_files = gr.File(
                            label="Server Files",
                            file_count="multiple",
                            interactive=False
                        )
                        
                        self.file_tree = gr.Textbox(
                            label="File Structure",
                            value="""calculator-server/
├── app.py
├── requirements.txt
├── README.md
├── config.json
└── logs/
    └── server.log""",
                            lines=10,
                            interactive=False
                        )
                    
                    # Performance tab
                    with gr.Tab("Performance"):
                        self.performance_metrics = gr.JSON(
                            label="Performance Metrics",
                            value={
                                "requests_per_minute": 12,
                                "average_response_time": "150ms",
                                "error_rate": "0.5%",
                                "uptime": "99.8%",
                                "memory_usage": "45MB",
                                "cpu_usage": "8%"
                            }
                        )
        
        # Set up details handlers
        self._setup_details_handlers()
    
    def _create_monitoring_interface(self) -> None:
        """Create the monitoring interface"""
        
        with gr.Column():
            gr.Markdown("### Server Monitoring")
            
            # Monitoring controls
            with gr.Row():
                self.auto_refresh = gr.Checkbox(
                    label="Auto-refresh (30s)",
                    value=True
                )
                
                self.monitoring_server = gr.Dropdown(
                    label="Monitor Server",
                    choices=["All Servers", "calculator-server", "data-processor", "image-tool"],
                    value="All Servers"
                )
                
                self.export_logs_btn = gr.Button("📤 Export Logs")
            
            with gr.Row():
                # Logs panel
                with gr.Column(scale=2):
                    gr.Markdown("#### Live Logs")
                    
                    self.log_level = gr.Radio(
                        label="Log Level",
                        choices=["All", "Error", "Warning", "Info", "Debug"],
                        value="All",
                        interactive=True
                    )
                    
                    self.live_logs = gr.Textbox(
                        label="",
                        value="""[14:30:15] INFO - Server started on port 7860
[14:30:16] INFO - MCP server initialized
[14:30:45] INFO - Received calculation request: 2+2
[14:30:45] INFO - Calculation result: 4
[14:31:02] INFO - Received calculation request: sqrt(16)
[14:31:02] INFO - Calculation result: 4.0
[14:31:15] WARNING - High CPU usage detected: 85%
[14:31:20] INFO - CPU usage normalized: 45%""",
                        lines=12,
                        interactive=False,
                        show_label=False,
                        autoscroll=True
                    )
                
                # Metrics panel
                with gr.Column(scale=1):
                    gr.Markdown("#### Metrics")
                    
                    # Real-time metrics
                    self.requests_count = gr.Number(
                        label="Total Requests",
                        value=1247,
                        interactive=False
                    )
                    
                    self.active_connections = gr.Number(
                        label="Active Connections",
                        value=3,
                        interactive=False
                    )
                    
                    self.error_count = gr.Number(
                        label="Errors (24h)",
                        value=2,
                        interactive=False
                    )
                    
                    # Alerts
                    gr.Markdown("#### Alerts")
                    self.alerts_panel = gr.Markdown("""
🟡 **Warning**  
High memory usage: 85%  
*2 minutes ago*

🟢 **Info**  
Server restarted successfully  
*1 hour ago*
                    """)
        
        # Set up monitoring handlers
        self._setup_monitoring_handlers()
    
    def _create_settings_interface(self) -> None:
        """Create the settings interface"""
        
        with gr.Column():
            gr.Markdown("### Server Settings")
            
            with gr.Row():
                # Global settings
                with gr.Column():
                    gr.Markdown("#### Global Settings")
                    
                    self.default_port = gr.Number(
                        label="Default Port",
                        value=7860,
                        minimum=1000,
                        maximum=65535
                    )
                    
                    self.auto_start = gr.Checkbox(
                        label="Auto-start servers on system boot",
                        value=False
                    )
                    
                    self.log_retention = gr.Number(
                        label="Log Retention (days)",
                        value=30,
                        minimum=1,
                        maximum=365
                    )
                    
                    self.max_memory = gr.Number(
                        label="Max Memory per Server (MB)",
                        value=512,
                        minimum=128,
                        maximum=4096
                    )
                
                # Server-specific settings
                with gr.Column():
                    gr.Markdown("#### Server-Specific Settings")
                    
                    self.settings_server = gr.Dropdown(
                        label="Configure Server",
                        choices=["calculator-server", "data-processor", "image-tool"],
                        value="calculator-server"
                    )
                    
                    self.server_port = gr.Number(
                        label="Port",
                        value=7860,
                        minimum=1000,
                        maximum=65535
                    )
                    
                    self.server_public = gr.Checkbox(
                        label="Create public URL",
                        value=False
                    )
                    
                    self.server_auth = gr.Checkbox(
                        label="Enable authentication",
                        value=False
                    )
                    
                    self.server_ssl = gr.Checkbox(
                        label="Enable SSL",
                        value=False
                    )
            
            # Environment variables
            with gr.Group():
                gr.Markdown("#### Environment Variables")
                
                self.env_vars = gr.Dataframe(
                    headers=["Variable", "Value", "Server"],
                    datatype=["str", "str", "str"],
                    value=[
                        ["GRADIO_SERVER_PORT", "7860", "All"],
                        ["MCP_SERVER_MODE", "true", "All"], 
                        ["LOG_LEVEL", "INFO", "All"]
                    ],
                    interactive=True
                )
                
                with gr.Row():
                    self.add_env_btn = gr.Button("➕ Add Variable")
                    self.remove_env_btn = gr.Button("➖ Remove Selected")
            
            # Actions
            with gr.Row():
                self.save_settings_btn = gr.Button("💾 Save Settings", variant="primary")
                self.reset_settings_btn = gr.Button("🔄 Reset to Defaults")
                self.export_settings_btn = gr.Button("📤 Export Settings")
        
        # Set up settings handlers
        self._setup_settings_handlers()
    
    def _setup_overview_handlers(self) -> None:
        """Setup event handlers for overview interface"""
        
        # Refresh servers list
        self.refresh_btn.click(
            fn=self._refresh_servers,
            outputs=[self.servers_table, self.total_servers, self.running_servers, self.stopped_servers]
        )
        
        # Server control actions
        self.start_btn.click(
            fn=self._start_server,
            outputs=[self.servers_table, self.activity_log]
        )
        
        self.stop_btn.click(
            fn=self._stop_server,
            outputs=[self.servers_table, self.activity_log]
        )
        
        self.restart_btn.click(
            fn=self._restart_server,
            outputs=[self.servers_table, self.activity_log]
        )
        
        # Create new server
        self.create_new_btn.click(
            fn=self._create_new_server,
            outputs=[self.servers_table]
        )
    
    def _setup_details_handlers(self) -> None:
        """Setup event handlers for details interface"""
        
        # Server selection
        self.server_selector.change(
            fn=self._load_server_details,
            inputs=[self.server_selector],
            outputs=[self.server_info_panel, self.server_config, self.file_tree, self.performance_metrics]
        )
        
        # Quick actions
        self.open_browser_btn.click(
            fn=self._open_server_browser,
            inputs=[self.server_selector]
        )
        
        self.view_code_btn.click(
            fn=self._view_server_code,
            inputs=[self.server_selector],
            outputs=[self.server_config]
        )
    
    def _setup_monitoring_handlers(self) -> None:
        """Setup event handlers for monitoring interface"""
        
        # Auto-refresh logs
        self.auto_refresh.change(
            fn=self._toggle_auto_refresh,
            inputs=[self.auto_refresh]
        )
        
        # Filter logs by level
        self.log_level.change(
            fn=self._filter_logs,
            inputs=[self.log_level],
            outputs=[self.live_logs]
        )
        
        # Export logs
        self.export_logs_btn.click(
            fn=self._export_logs,
            outputs=[gr.File(visible=False)]  # For download
        )
    
    def _setup_settings_handlers(self) -> None:
        """Setup event handlers for settings interface"""
        
        # Server selection for settings
        self.settings_server.change(
            fn=self._load_server_settings,
            inputs=[self.settings_server],
            outputs=[self.server_port, self.server_public, self.server_auth, self.server_ssl]
        )
        
        # Save settings
        self.save_settings_btn.click(
            fn=self._save_settings,
            inputs=[
                self.default_port, self.auto_start, self.log_retention,
                self.server_port, self.server_public, self.env_vars
            ],
            outputs=[gr.Textbox(visible=False)]  # Status message
        )
    
    def _get_mock_servers_data(self) -> List[List[str]]:
        """Get mock server data for display"""
        
        return [
            ["calculator-server", "🟢 Running", "7860", "Calculator", "2024-01-20 14:30"],
            ["data-processor", "🔴 Stopped", "7861", "Data Analysis", "2024-01-19 16:45"],
            ["image-tool", "🔴 Stopped", "7862", "Image Processing", "2024-01-18 09:15"]
        ]
    
    def _refresh_servers(self) -> Tuple[List[List[str]], int, int, int]:
        """Refresh servers list and status"""
        
        servers_data = self._get_mock_servers_data()
        
        total = len(servers_data)
        running = sum(1 for server in servers_data if "🟢" in server[1])
        stopped = total - running
        
        return servers_data, total, running, stopped
    
    def _start_server(self) -> Tuple[List[List[str]], str]:
        """Start a selected server"""
        
        # Mock server start
        servers_data = self._get_mock_servers_data()
        
        # Update first stopped server to running
        for server in servers_data:
            if "🔴" in server[1]:
                server[1] = "🟢 Running"
                break
        
        activity = "🟢 Server started successfully\n" + self.activity_log.value
        
        return servers_data, activity
    
    def _stop_server(self) -> Tuple[List[List[str]], str]:
        """Stop a selected server"""
        
        servers_data = self._get_mock_servers_data()
        
        # Update first running server to stopped
        for server in servers_data:
            if "🟢" in server[1]:
                server[1] = "🔴 Stopped"
                break
        
        activity = "🔴 Server stopped\n" + self.activity_log.value
        
        return servers_data, activity
    
    def _restart_server(self) -> Tuple[List[List[str]], str]:
        """Restart a selected server"""
        
        servers_data = self._get_mock_servers_data()
        activity = "🔄 Server restarted\n" + self.activity_log.value
        
        return servers_data, activity
    
    def _create_new_server(self) -> List[List[str]]:
        """Create a new server"""
        
        servers_data = self._get_mock_servers_data()
        new_server = [f"new-server-{len(servers_data)+1}", "🔴 Stopped", "7863", "Custom", "2024-01-20 15:00"]
        servers_data.append(new_server)
        
        return servers_data
    
    def _load_server_details(self, server_name: str) -> Tuple[str, str, str, Dict[str, Any]]:
        """Load details for selected server"""
        
        # Mock server details
        server_info = f"""
**Server:** {server_name}  
**Status:** 🟢 Running  
**Port:** 7860  
**Type:** Calculator  
**Created:** 2024-01-15  
**Last Modified:** 2024-01-20  
**Memory Usage:** 45MB  
**CPU Usage:** 8%  
        """
        
        config = f'''{
  "name": "{server_name}",
  "port": 7860,
  "mcp_server": true,
  "share": false,
  "tools": [
    {{
      "name": "main_function",
      "description": "Main server function"
    }}
  ]
}'''
        
        file_tree = f"""{server_name}/
├── app.py
├── requirements.txt
├── README.md
├── config.json
└── logs/
    └── server.log"""
        
        metrics = {
            "requests_per_minute": 12,
            "average_response_time": "150ms", 
            "error_rate": "0.5%",
            "uptime": "99.8%",
            "memory_usage": "45MB",
            "cpu_usage": "8%"
        }
        
        return server_info, config, file_tree, metrics
    
    def _open_server_browser(self, server_name: str) -> None:
        """Open server in browser"""
        
        # This would open the server URL in browser
        # For now, just a placeholder
        pass
    
    def _view_server_code(self, server_name: str) -> str:
        """View server source code"""
        
        return f'''# {server_name} - Generated MCP Server

import gradio as gr

def main_function(input_text):
    """Main server function"""
    return f"Processed: {{input_text}}"

demo = gr.Interface(
    fn=main_function,
    inputs=gr.Textbox(label="Input"),
    outputs=gr.Textbox(label="Output"),
    title="{server_name}"
)

if __name__ == "__main__":
    demo.launch(server_port=7860, mcp_server=True)
'''
    
    def _toggle_auto_refresh(self, enabled: bool) -> None:
        """Toggle auto-refresh for monitoring"""
        
        # This would start/stop auto-refresh timer
        pass
    
    def _filter_logs(self, level: str) -> str:
        """Filter logs by level"""
        
        all_logs = """[14:30:15] INFO - Server started on port 7860
[14:30:16] INFO - MCP server initialized
[14:30:45] INFO - Received calculation request: 2+2
[14:30:45] INFO - Calculation result: 4
[14:31:02] INFO - Received calculation request: sqrt(16)
[14:31:02] INFO - Calculation result: 4.0
[14:31:15] WARNING - High CPU usage detected: 85%
[14:31:20] INFO - CPU usage normalized: 45%
[14:31:25] ERROR - Invalid calculation: division by zero
[14:31:30] DEBUG - Memory usage: 45MB"""
        
        if level == "All":
            return all_logs
        else:
            lines = all_logs.split('\n')
            filtered = [line for line in lines if level.upper() in line]
            return '\n'.join(filtered)
    
    def _export_logs(self) -> str:
        """Export logs to file"""
        
        return "Server logs exported successfully"
    
    def _load_server_settings(self, server_name: str) -> Tuple[int, bool, bool, bool]:
        """Load settings for selected server"""
        
        # Mock server settings
        return 7860, False, False, False
    
    def _save_settings(self, default_port: int, auto_start: bool, log_retention: int, 
                      server_port: int, server_public: bool, env_vars: List[List[str]]) -> str:
        """Save server settings"""
        
        return "Settings saved successfully"