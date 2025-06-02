"""Gradio MCP Playground Web UI

Web-based dashboard for managing Gradio MCP servers.
"""

import gradio as gr
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .server_manager import GradioMCPServer
from .client_manager import GradioMCPClient, MCPConnectionManager
from .registry import ServerRegistry
from .config_manager import ConfigManager


def create_dashboard() -> gr.Blocks:
    """Create the Gradio MCP Playground dashboard"""
    
    config_manager = ConfigManager()
    registry = ServerRegistry()
    connection_manager = MCPConnectionManager()
    
    with gr.Blocks(title="Gradio MCP Playground", theme=gr.themes.Soft()) as dashboard:
        gr.Markdown(
            """
            # 🚀 Gradio MCP Playground
            
            Build, manage, and deploy Gradio applications as Model Context Protocol (MCP) servers.
            """
        )
        
        with gr.Tabs():
            # Servers Tab
            with gr.Tab("🖥️ Servers"):
                with gr.Row():
                    with gr.Column(scale=3):
                        servers_list = gr.Dataframe(
                            headers=["Name", "Status", "Port", "Template", "Path"],
                            label="Registered Servers",
                            interactive=False
                        )
                        refresh_servers_btn = gr.Button("🔄 Refresh", variant="secondary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### Server Actions")
                        selected_server = gr.Textbox(label="Selected Server", interactive=False)
                        
                        with gr.Row():
                            start_btn = gr.Button("▶️ Start", variant="primary")
                            stop_btn = gr.Button("⏹️ Stop", variant="stop")
                        
                        with gr.Row():
                            info_btn = gr.Button("ℹ️ Info")
                            delete_btn = gr.Button("🗑️ Delete", variant="stop")
                
                server_info_output = gr.JSON(label="Server Information", visible=False)
                
                # Create new server section
                gr.Markdown("### Create New Server")
                with gr.Row():
                    new_server_name = gr.Textbox(label="Server Name", placeholder="my-mcp-server")
                    template_dropdown = gr.Dropdown(
                        choices=registry.list_templates(),
                        label="Template",
                        value="basic"
                    )
                    create_port = gr.Number(
                        label="Port",
                        value=config_manager.default_port,
                        precision=0
                    )
                
                create_server_btn = gr.Button("➕ Create Server", variant="primary")
                create_output = gr.Textbox(label="Creation Output", visible=False)
            
            # Connections Tab
            with gr.Tab("🔌 Connections"):
                with gr.Row():
                    with gr.Column(scale=3):
                        connections_list = gr.Dataframe(
                            headers=["Name", "URL", "Protocol", "Status"],
                            label="Saved Connections",
                            interactive=False
                        )
                        refresh_connections_btn = gr.Button("🔄 Refresh", variant="secondary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### Connection Actions")
                        selected_connection = gr.Textbox(label="Selected Connection", interactive=False)
                        
                        connect_btn = gr.Button("🔗 Connect", variant="primary")
                        disconnect_btn = gr.Button("🔌 Disconnect", variant="stop")
                        test_btn = gr.Button("🧪 Test")
                        remove_conn_btn = gr.Button("🗑️ Remove", variant="stop")
                
                connection_info = gr.JSON(label="Connection Details", visible=False)
                
                # Add new connection section
                gr.Markdown("### Add New Connection")
                with gr.Row():
                    conn_name = gr.Textbox(label="Connection Name", placeholder="my-connection")
                    conn_url = gr.Textbox(label="Server URL", placeholder="http://localhost:7860")
                    conn_protocol = gr.Dropdown(
                        choices=["auto", "stdio", "sse"],
                        label="Protocol",
                        value="auto"
                    )
                
                add_connection_btn = gr.Button("➕ Add Connection", variant="primary")
                add_conn_output = gr.Textbox(label="Connection Output", visible=False)
            
            # Registry Tab
            with gr.Tab("📦 Registry"):
                gr.Markdown("### Browse Available MCP Servers")
                
                with gr.Row():
                    search_query = gr.Textbox(
                        label="Search",
                        placeholder="Search for servers...",
                        scale=3
                    )
                    category_filter = gr.Dropdown(
                        choices=["all"] + registry.list_categories(),
                        label="Category",
                        value="all",
                        scale=1
                    )
                
                search_btn = gr.Button("🔍 Search", variant="primary")
                
                search_results = gr.JSON(label="Search Results")
                
                # Server details
                with gr.Row():
                    selected_registry_server = gr.Textbox(label="Selected Server ID", visible=False)
                    install_from_registry_btn = gr.Button(
                        "📥 Install Selected",
                        variant="primary",
                        visible=False
                    )
            
            # Tools Testing Tab
            with gr.Tab("🧪 Tool Testing"):
                gr.Markdown("### Test MCP Tools")
                
                with gr.Row():
                    test_server_url = gr.Textbox(
                        label="Server URL",
                        placeholder="http://localhost:7860"
                    )
                    test_protocol = gr.Dropdown(
                        choices=["auto", "stdio", "sse"],
                        label="Protocol",
                        value="auto"
                    )
                    connect_test_btn = gr.Button("🔗 Connect", variant="primary")
                
                tools_list = gr.JSON(label="Available Tools", visible=False)
                
                with gr.Row():
                    tool_name = gr.Textbox(label="Tool Name")
                    tool_args = gr.Textbox(
                        label="Arguments (JSON)",
                        placeholder='{"param": "value"}',
                        lines=3
                    )
                
                call_tool_btn = gr.Button("🚀 Call Tool", variant="primary")
                tool_result = gr.JSON(label="Tool Result")
            
            # Settings Tab
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### Gradio MCP Playground Settings")
                
                with gr.Column():
                    settings_port = gr.Number(
                        label="Default Port",
                        value=config_manager.default_port,
                        precision=0
                    )
                    settings_auto_reload = gr.Checkbox(
                        label="Auto-reload on file changes",
                        value=config_manager.auto_reload
                    )
                    settings_protocol = gr.Dropdown(
                        choices=["auto", "stdio", "sse"],
                        label="Default MCP Protocol",
                        value=config_manager.mcp_protocol
                    )
                    settings_log_level = gr.Dropdown(
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        label="Log Level",
                        value=config_manager.log_level
                    )
                    settings_hf_token = gr.Textbox(
                        label="Hugging Face Token (for deployment)",
                        type="password",
                        value=config_manager.hf_token or ""
                    )
                
                save_settings_btn = gr.Button("💾 Save Settings", variant="primary")
                settings_output = gr.Textbox(label="Settings Output", visible=False)
        
        # Event handlers
        
        def refresh_servers():
            """Refresh the servers list"""
            servers = config_manager.list_servers()
            data = []
            for server in servers:
                status = "🟢 Running" if server.get("running") else "⚫ Stopped"
                data.append([
                    server.get("name", "Unknown"),
                    status,
                    str(server.get("port", "N/A")),
                    server.get("template", "custom"),
                    server.get("path", "N/A")
                ])
            return data
        
        def refresh_connections():
            """Refresh the connections list"""
            connections = connection_manager.list_connections()
            data = []
            for conn in connections:
                status = "🟢 Connected" if conn.get("connected") else "⚫ Disconnected"
                data.append([
                    conn.get("name", "Unknown"),
                    conn.get("url", "N/A"),
                    conn.get("protocol", "auto"),
                    status
                ])
            return data
        
        def create_server(name, template, port):
            """Create a new server"""
            try:
                if not name:
                    return gr.update(visible=True, value="❌ Server name is required")
                
                # Create server directory
                server_dir = Path.cwd() / name
                
                # Create from template
                server_config = registry.create_from_template(
                    template,
                    name,
                    server_dir,
                    port=port
                )
                
                # Register server
                config_manager.add_server(server_config)
                
                return gr.update(
                    visible=True,
                    value=f"✅ Server '{name}' created successfully!\n\nLocation: {server_dir}"
                )
            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error: {str(e)}")
        
        def start_server(selected):
            """Start a selected server"""
            if not selected:
                return
            
            server = config_manager.get_server(selected)
            if server:
                server_mgr = GradioMCPServer(Path(server["path"]))
                server_mgr.start(port=server.get("port", 7860))
                return refresh_servers()
        
        def stop_server(selected):
            """Stop a selected server"""
            if not selected:
                return
            
            # In a real implementation, we'd track and stop the process
            return refresh_servers()
        
        def show_server_info(selected):
            """Show detailed server information"""
            if not selected:
                return gr.update(visible=False)
            
            server = config_manager.get_server(selected)
            if server:
                return gr.update(visible=True, value=server)
            return gr.update(visible=False)
        
        def search_registry(query, category):
            """Search the server registry"""
            if category == "all":
                category = None
            
            if query:
                results = registry.search(query, category)
            elif category:
                results = registry.get_by_category(category)
            else:
                results = registry.get_all()
            
            return results
        
        def test_connection(url, protocol):
            """Test a connection to an MCP server"""
            result = GradioMCPClient.test_connection(url, protocol)
            if result["success"]:
                return gr.update(visible=True, value=result["tools"])
            else:
                return gr.update(visible=True, value={"error": result["error"]})
        
        def call_tool(url, protocol, tool_name, args_json):
            """Call a tool on an MCP server"""
            try:
                args = json.loads(args_json) if args_json else {}
                
                client = GradioMCPClient()
                client.connect(url, protocol)
                result = client.call_tool(tool_name, args)
                client.disconnect()
                
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def save_settings(port, auto_reload, protocol, log_level, hf_token):
            """Save settings"""
            try:
                config_manager.set("default_port", port)
                config_manager.set("auto_reload", auto_reload)
                config_manager.set("mcp_protocol", protocol)
                config_manager.set("log_level", log_level)
                if hf_token:
                    config_manager.set("hf_token", hf_token)
                
                return gr.update(visible=True, value="✅ Settings saved successfully!")
            except Exception as e:
                return gr.update(visible=True, value=f"❌ Error: {str(e)}")
        
        # Connect event handlers
        refresh_servers_btn.click(refresh_servers, outputs=servers_list)
        refresh_connections_btn.click(refresh_connections, outputs=connections_list)
        
        create_server_btn.click(
            create_server,
            inputs=[new_server_name, template_dropdown, create_port],
            outputs=create_output
        ).then(refresh_servers, outputs=servers_list)
        
        servers_list.select(
            lambda evt: evt.value[0] if evt.value else None,
            outputs=selected_server
        )
        
        start_btn.click(start_server, inputs=selected_server).then(
            refresh_servers, outputs=servers_list
        )
        stop_btn.click(stop_server, inputs=selected_server).then(
            refresh_servers, outputs=servers_list
        )
        info_btn.click(show_server_info, inputs=selected_server, outputs=server_info_output)
        
        search_btn.click(
            search_registry,
            inputs=[search_query, category_filter],
            outputs=search_results
        )
        
        connect_test_btn.click(
            test_connection,
            inputs=[test_server_url, test_protocol],
            outputs=tools_list
        )
        
        call_tool_btn.click(
            call_tool,
            inputs=[test_server_url, test_protocol, tool_name, tool_args],
            outputs=tool_result
        )
        
        save_settings_btn.click(
            save_settings,
            inputs=[
                settings_port,
                settings_auto_reload,
                settings_protocol,
                settings_log_level,
                settings_hf_token
            ],
            outputs=settings_output
        )
        
        # Load initial data
        dashboard.load(refresh_servers, outputs=servers_list)
        dashboard.load(refresh_connections, outputs=connections_list)
    
    return dashboard


def launch_dashboard(port: int = 8080, share: bool = False):
    """Launch the Gradio MCP Playground dashboard"""
    dashboard = create_dashboard()
    dashboard.launch(
        server_port=port,
        share=share,
        server_name="0.0.0.0" if not share else None,
        show_api=False
    )
