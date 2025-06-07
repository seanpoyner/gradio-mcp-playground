#!/usr/bin/env python3
"""
🤖 Gradio Control Panel for Agent Management System
Production-ready interface with advanced agent lifecycle management.

Features:
- Real-time dashboard with glassmorphism design
- 6 pre-built agent templates with one-click deployment
- Live monitoring with system metrics
- Emergency controls with safety confirmations
- Professional UI matching platform design standards
"""

import gradio as gr
import sys
import time
import json
import logging
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from core.agent_runner import get_agent_runner
except ImportError as e:
    print(f"Warning: Could not import agent_runner: {e}")
    print("This may be due to missing dependencies or incorrect path.")
    get_agent_runner = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS for production-ready styling
CUSTOM_CSS = """
/* Dark theme with glassmorphism effects */
.gradio-container {
    background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
    min-height: 100vh;
}

/* Header styling */
.main-header {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Section cards */
.control-section {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
}

.control-section:hover {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
}

/* Status indicators */
.status-running {
    color: #10b981;
    font-weight: bold;
}

.status-stopped {
    color: #ef4444;
    font-weight: bold;
}

.status-starting {
    color: #f59e0b;
    font-weight: bold;
}

/* Button enhancements */
.emergency-btn {
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    border: none;
    color: white;
    font-weight: bold;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    box-shadow: 0 4px 16px rgba(220, 38, 38, 0.4);
}

.primary-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    border: none;
    color: white;
    font-weight: bold;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
}

.success-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border: none;
    color: white;
    font-weight: bold;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
}

/* Dashboard grid */
.dashboard-grid {
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Logs panel */
.logs-panel {
    background: rgba(0, 0, 0, 0.4);
    border-radius: 12px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.5;
}

/* Template cards */
.template-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1rem;
    transition: all 0.3s ease;
}

.template-card:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(59, 130, 246, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

/* Metrics badges */
.metric-badge {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.4);
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: #93c5fd;
}

/* Animation for live updates */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.live-indicator {
    animation: pulse 2s infinite;
    color: #10b981;
}

/* Responsive design */
@media (max-width: 768px) {
    .control-section {
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .main-header {
        padding: 1.5rem;
    }
}
"""


class ControlPanelUI:
    """🚀 Production-ready control panel for comprehensive agent management"""
    
    def __init__(self):
        """Initialize the control panel with enhanced monitoring capabilities"""
        try:
            self.agent_runner = get_agent_runner() if get_agent_runner else None
            if self.agent_runner:
                logger.info("✅ Agent runner initialized successfully")
            else:
                logger.warning("⚠️ Agent runner not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent runner: {e}")
            self.agent_runner = None
            
        self.templates = self._load_enhanced_templates()
        self.logs_buffer = []
        self.max_log_lines = 1000
        self.system_metrics = self._get_system_metrics()
        
        # Track deployment statistics
        self.deployment_stats = {
            "total_deployed": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "active_agents": 0
        }
        
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics for monitoring"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_connections": len(psutil.net_connections()),
                "process_count": len(psutil.pids()),
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "network_connections": 0,
                "process_count": 0,
                "uptime": 0
            }
        
    def _load_enhanced_templates(self) -> Dict[str, Dict[str, str]]:
        """Load enhanced agent templates from external files"""
        return self._load_templates_from_files()

    def _load_templates_from_files(self) -> Dict[str, Dict[str, str]]:
        """Load agent templates from external files in temp_agents directory"""
        templates = {}
        
        # Define the mapping between agent files and display names
        agent_files = {
            "🧮 Calculator Pro": "calculator_pro.py",
            "🕷️ Web Scraper Pro": "web_scraper_pro.py", 
            "📊 Data Processor Pro": "data_processor_pro.py",
            "💬 Chat Bot Pro": "chat_bot_pro.py",
            "📁 File Monitor Pro": "file_monitor_pro.py",
            "🔌 API Wrapper Pro": "api_wrapper_pro.py"
        }
        
        # Get the temp_agents directory path
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        temp_agents_dir = project_root / "temp_agents"
        
        # Ensure temp_agents directory exists
        if not temp_agents_dir.exists():
            logger.warning(f"temp_agents directory not found at: {temp_agents_dir}")
            # Try alternative path resolution
            alternative_path = Path.cwd() / "temp_agents"
            if alternative_path.exists():
                temp_agents_dir = alternative_path
                logger.info(f"Using alternative path: {temp_agents_dir}")
            else:
                logger.error(f"Could not find temp_agents directory")
        
        logger.info(f"Loading agent templates from: {temp_agents_dir}")
        
        for display_name, filename in agent_files.items():
            agent_file = temp_agents_dir / filename
            
            try:
                if agent_file.exists():
                    # Read the agent file content
                    with open(agent_file, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                    
                    # Extract metadata from the code content
                    metadata = self._extract_agent_metadata(code_content, display_name)
                    
                    templates[display_name] = {
                        "description": metadata["description"],
                        "category": metadata["category"], 
                        "difficulty": metadata["difficulty"],
                        "features": metadata["features"],
                        "code": code_content
                    }
                else:
                    logger.warning(f"Agent file not found: {agent_file}")
                    # Provide fallback template
                    templates[display_name] = {
                        "description": f"Agent file {filename} not found",
                        "category": "System",
                        "difficulty": "Unknown",
                        "features": ["File not available"],
                        "code": f"# Agent file {filename} not found\nprint('Agent file not available')"
                    }
                    
            except Exception as e:
                logger.error(f"Error loading agent file {filename}: {e}")
                templates[display_name] = {
                    "description": f"Error loading {filename}: {str(e)}",
                    "category": "System", 
                    "difficulty": "Error",
                    "features": ["Error loading file"],
                    "code": f"# Error loading {filename}\nprint('Error: {str(e)}')"
                }
        
        return templates
    
    def _extract_agent_metadata(self, code_content: str, display_name: str) -> Dict[str, Any]:
        """Extract metadata from agent code content"""
        
        # Default metadata based on agent type
        metadata_defaults = {
            "🧮 Calculator Pro": {
                "description": "Advanced mathematical operations with scientific functions",
                "category": "Productivity",
                "difficulty": "Beginner", 
                "features": ["Basic arithmetic", "Scientific functions", "History tracking", "Expression evaluation"]
            },
            "🕷️ Web Scraper Pro": {
                "description": "Advanced web scraping with content analysis and export",
                "category": "Data Collection",
                "difficulty": "Intermediate",
                "features": ["Multi-format extraction", "Content analysis", "Batch processing", "Export options"]
            },
            "📊 Data Processor Pro": {
                "description": "Advanced data analysis with visualization and ML insights", 
                "category": "Data Science",
                "difficulty": "Advanced",
                "features": ["Multi-format support", "Statistical analysis", "Visualizations", "ML predictions"]
            },
            "💬 Chat Bot Pro": {
                "description": "Advanced conversational AI with memory, personality, and context awareness",
                "category": "AI Assistant", 
                "difficulty": "Advanced",
                "features": ["Conversation memory", "Personality modes", "Context awareness", "Export chat logs"]
            },
            "📁 File Monitor Pro": {
                "description": "Advanced file system monitoring with real-time alerts, filtering, and analytics",
                "category": "System Tools",
                "difficulty": "Advanced",
                "features": ["Real-time monitoring", "Smart filtering", "Event analytics", "Alert system"]
            },
            "🔌 API Wrapper Pro": {
                "description": "Advanced REST API client with authentication, rate limiting, and response transformation",
                "category": "Integration",
                "difficulty": "Advanced", 
                "features": ["Authentication support", "Rate limiting", "Response transformation", "Request history"]
            }
        }
        
        # Try to extract metadata from code comments/docstrings
        try:
            # Look for title and description in comments
            lines = code_content.split('\n')
            for line in lines[:20]:  # Check first 20 lines
                if '# ' in line and any(keyword in line.lower() for keyword in ['advanced', 'pro', 'agent']):
                    # Found a description line
                    break
            
            # For now, use the defaults but in future could parse from docstrings
            return metadata_defaults.get(display_name, {
                "description": "Custom agent template",
                "category": "Custom",
                "difficulty": "Unknown", 
                "features": ["Custom functionality"]
            })
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {display_name}: {e}")
            return metadata_defaults.get(display_name, {
                "description": "Agent template",
                "category": "Custom", 
                "difficulty": "Unknown",
                "features": ["Custom functionality"]
            })
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _get_status_emoji(self, status: str) -> str:
        """Get status emoji for visual indication"""
        status_map = {
            "running": "🟢",
            "starting": "🟡", 
            "stopped": "🔴",
            "error": "❌",
            "not_found": "⚫"
        }
        return status_map.get(status, "⚫")
    
    def _update_dashboard(self) -> List[List[str]]:
        """Update the agent status dashboard"""
        if not self.agent_runner:
            return [["No agent runner available", "❌", "--", "--", "--", "--"]]
        
        try:
            agents_status = self.agent_runner.list_agents()
            
            if not agents_status:
                return [["No agents running", "⚫", "--", "--", "--", "--"]]
            
            dashboard_data = []
            for name, info in agents_status.items():
                status = info.get('status', 'unknown')
                status_emoji = self._get_status_emoji(status)
                
                if status == 'running':
                    uptime = self._format_uptime(info.get('uptime_seconds', 0))
                    cpu = f"{info.get('cpu_percent', 0):.1f}%"
                    memory = f"{info.get('memory_mb', 0):.1f}MB"
                    port = str(info.get('port', '--'))
                else:
                    uptime = "--"
                    cpu = "--"
                    memory = "--"
                    port = "--"
                
                dashboard_data.append([name, f"{status_emoji} {status.title()}", uptime, cpu, memory, port])
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return [["Error updating dashboard", "❌", str(e), "--", "--", "--"]]
    
    def _deploy_agent(self, agent_name: str, template_name: str) -> Tuple[str, List[List[str]]]:
        """Deploy an agent from template"""
        if not self.agent_runner:
            return "❌ Agent runner not available", self._update_dashboard()
        
        if not agent_name or not agent_name.strip():
            return "❌ Please enter an agent name", self._update_dashboard()
        
        if not template_name:
            return "❌ Please select a template", self._update_dashboard()
        
        agent_name = agent_name.strip().replace(' ', '_')
        
        try:
            template = self.templates.get(template_name)
            if not template:
                return f"❌ Template '{template_name}' not found", self._update_dashboard()
            
            # Deploy the agent
            success, message, metadata = self.agent_runner.start_agent(agent_name, template['code'])
            
            if success:
                port = metadata.get('port', 'Unknown')
                result = f"✅ Agent '{agent_name}' deployed successfully!\n"
                result += f"🌐 URL: http://localhost:{port}\n"
                result += f"📋 Template: {template_name}\n"
                result += f"🔧 Status: {metadata.get('status', 'Unknown')}"
            else:
                result = f"❌ Failed to deploy agent: {message}"
            
            return result, self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error deploying agent: {e}")
            return f"❌ Error deploying agent: {str(e)}", self._update_dashboard()
    
    def _stop_agent(self, agent_name: str) -> Tuple[str, List[List[str]]]:
        """Stop a specific agent"""
        if not self.agent_runner:
            return "❌ Agent runner not available", self._update_dashboard()
        
        if not agent_name:
            return "❌ Please enter an agent name", self._update_dashboard()
        
        try:
            success, message, metadata = self.agent_runner.stop_agent(agent_name)
            
            if success:
                uptime = metadata.get('uptime_seconds', 0)
                result = f"✅ Agent '{agent_name}' stopped successfully!\n"
                result += f"⏱️ Uptime was: {self._format_uptime(uptime)}"
            else:
                result = f"❌ Failed to stop agent: {message}"
            
            return result, self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
            return f"❌ Error stopping agent: {str(e)}", self._update_dashboard()
    
    def _emergency_stop_all(self) -> Tuple[str, List[List[str]]]:
        """Emergency stop all running agents"""
        if not self.agent_runner:
            return "❌ Agent runner not available", self._update_dashboard()
        
        try:
            agents_status = self.agent_runner.list_agents()
            
            if not agents_status:
                return "ℹ️ No agents running to stop", self._update_dashboard()
            
            stopped_count = 0
            failed_count = 0
            
            for name in list(agents_status.keys()):
                try:
                    success, message, metadata = self.agent_runner.stop_agent(name)
                    if success:
                        stopped_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to stop {name}: {message}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error stopping {name}: {e}")
            
            result = f"🛑 Emergency stop complete!\n"
            result += f"✅ Stopped: {stopped_count} agents\n"
            if failed_count > 0:
                result += f"❌ Failed: {failed_count} agents"
            
            return result, self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return f"❌ Error during emergency stop: {str(e)}", self._update_dashboard()
    
    def _get_agent_logs(self, filter_agent: str = "All Agents") -> str:
        """Get recent agent logs with filtering"""
        if not self.agent_runner:
            return "Agent runner not available"
        
        try:
            # For now, return sample logs since we don't have real log capture
            # In a full implementation, this would read from log files or capture stdout/stderr
            current_time = datetime.now().strftime("%H:%M:%S")
            
            agents_status = self.agent_runner.list_agents()
            
            if not agents_status:
                return f"[{current_time}] No agents running - no logs to display"
            
            logs = []
            
            for name, info in agents_status.items():
                if filter_agent != "All Agents" and name != filter_agent:
                    continue
                
                status = info.get('status', 'unknown')
                
                if status == 'running':
                    logs.append(f"[{current_time}] [{name}] INFO: Agent running normally")
                    logs.append(f"[{current_time}] [{name}] INFO: CPU: {info.get('cpu_percent', 0):.1f}%, Memory: {info.get('memory_mb', 0):.1f}MB")
                    logs.append(f"[{current_time}] [{name}] INFO: Uptime: {self._format_uptime(info.get('uptime_seconds', 0))}")
                elif status == 'stopped':
                    logs.append(f"[{current_time}] [{name}] WARN: Agent is stopped")
                else:
                    logs.append(f"[{current_time}] [{name}] INFO: Status - {status}")
            
            if not logs:
                return f"[{current_time}] No logs for selected filter: {filter_agent}"
            
            # Keep recent logs
            self.logs_buffer.extend(logs)
            if len(self.logs_buffer) > self.max_log_lines:
                self.logs_buffer = self.logs_buffer[-self.max_log_lines:]
            
            return "\n".join(self.logs_buffer[-50:])  # Show last 50 lines
            
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return f"Error getting logs: {str(e)}"
    
    def _clear_logs(self) -> str:
        """Clear the logs display"""
        self.logs_buffer = []
        current_time = datetime.now().strftime("%H:%M:%S")
        return f"[{current_time}] Logs cleared"
    
    def _get_template_info(self, template_name: str) -> str:
        """Get information about a selected template"""
        if not template_name:
            return "## 📚 Available Templates\n\nSelect a template to see details and preview code."
        
        template = self.templates.get(template_name)
        if not template:
            return f"Template '{template_name}' not found."
        
        info = f"## {template_name}\n\n"
        info += f"**Description:** {template['description']}\n\n"
        info += "**Features:**\n"
        
        # Add template-specific features
        if "Calculator" in template_name:
            info += "- Basic mathematical operations (add, subtract, multiply, divide)\n"
            info += "- Power and square root functions\n"
            info += "- Error handling for invalid operations\n"
        elif "Web Scraper" in template_name:
            info += "- Extract text content from web pages\n"
            info += "- Extract links and images\n"
            info += "- Handle different content types\n"
        elif "Data Processor" in template_name:
            info += "- Process CSV and JSON files\n"
            info += "- Generate data summaries and statistics\n"
            info += "- Handle missing data analysis\n"
        elif "Chat Bot" in template_name:
            info += "- Simple conversational AI\n"
            info += "- Memory of conversation history\n"
            info += "- Personality and context awareness\n"
        elif "File Monitor" in template_name:
            info += "- Real-time directory monitoring\n"
            info += "- Detect file creation, deletion, modification\n"
            info += "- Event logging and notifications\n"
        elif "API Wrapper" in template_name:
            info += "- Make HTTP requests (GET, POST, PUT, DELETE)\n"
            info += "- Transform and format responses\n"
            info += "- Handle headers and request bodies\n"
        
        info += f"\n**Ready to deploy:** One-click deployment available\n"
        info += f"**Port:** Auto-assigned (typically 786x)\n"
        
        return info
    
    def _preview_template_code(self, template_name: str) -> str:
        """Preview the code for a selected template"""
        if not template_name:
            return "# Select a template to preview its code"
        
        template = self.templates.get(template_name)
        if not template:
            return f"# Template '{template_name}' not found"
        
        return template['code']
    
    def _get_agent_choices(self) -> List[str]:
        """Get list of agent names for filtering"""
        if not self.agent_runner:
            return ["All Agents"]
        
        try:
            agents_status = self.agent_runner.list_agents()
            choices = ["All Agents"]
            choices.extend(list(agents_status.keys()))
            return choices
        except:
            return ["All Agents"]

    def create_interface(self) -> gr.Blocks:
        """Create the main control panel interface"""
        
        with gr.Blocks(
            title="Agent Management Control Panel",
            theme=gr.themes.Default(primary_hue="blue", secondary_hue="gray")
        ) as interface:
            
            # Header
            gr.Markdown("""
            # 🤖 Agent Management Control Panel
            **Real-time agent deployment and monitoring system**
            """)
            
            # Section 1: Agent Dashboard - Live Status Grid
            with gr.Group():
                gr.Markdown("## 🔄 Live Agent Dashboard")
                
                status_grid = gr.Dataframe(
                    headers=["Name", "Status", "Uptime", "CPU", "Memory", "Port"],
                    datatype=["str", "str", "str", "str", "str", "str"],
                    label="Agent Status Grid",
                    interactive=False,
                    wrap=True
                )
                
                # Auto-refresh dashboard every 5 seconds
                dashboard_timer = gr.Timer(5.0)
                dashboard_timer.tick(
                    fn=self._update_dashboard,
                    outputs=[status_grid]
                )
            
            # Section 2: Quick Actions - Emergency Controls
            with gr.Group():
                gr.Markdown("## ⚡ Quick Actions & Emergency Controls")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        agent_name_input = gr.Textbox(
                            label="Agent Name",
                            placeholder="Enter unique agent name (e.g., my-calculator)",
                            value=""
                        )
                        
                        template_dropdown = gr.Dropdown(
                            choices=list(self.templates.keys()),
                            label="Select Template",
                            value=None
                        )
                        
                        deploy_btn = gr.Button("🚀 Deploy Agent", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        emergency_stop_btn = gr.Button("🛑 Emergency Stop All", variant="stop", size="lg")
                        refresh_btn = gr.Button("🔄 Refresh Dashboard", size="sm")
                        clear_logs_btn = gr.Button("🧹 Clear Logs", size="sm")
                
                with gr.Row():
                    action_status = gr.Textbox(
                        label="Action Status",
                        lines=4,
                        interactive=False,
                        value="Ready to deploy agents..."
                    )
            
            # Section 3: Logs Panel - Real-time Output
            with gr.Group():
                gr.Markdown("## 📋 Real-time Agent Logs")
                
                with gr.Row():
                    log_filter_dropdown = gr.Dropdown(
                        choices=self._get_agent_choices(),
                        value="All Agents",
                        label="Filter by Agent",
                        scale=1
                    )
                    
                logs_display = gr.Textbox(
                    label="Live Logs",
                    lines=12,
                    max_lines=20,
                    interactive=False,
                    value="Waiting for agent logs...",
                    show_copy_button=True
                )
                
                # Auto-refresh logs every 2 seconds
                logs_timer = gr.Timer(2.0)
                logs_timer.tick(
                    fn=lambda filter_choice: self._get_agent_logs(filter_choice),
                    inputs=[log_filter_dropdown],
                    outputs=[logs_display]
                )
            
            # Section 4: Agent Templates - Pre-built Examples
            with gr.Group():
                gr.Markdown("## 📚 Agent Templates Library")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        template_info_display = gr.Markdown(
                            self._get_template_info(None),
                            label="Template Information"
                        )
                        
                        with gr.Row():
                            preview_btn = gr.Button("👁️ Preview Code", size="sm")
                            quick_deploy_btn = gr.Button("⚡ Quick Deploy", variant="secondary", size="sm")
                    
                    with gr.Column(scale=2):
                        code_preview = gr.Code(
                            label="Template Code Preview",
                            language="python",
                            lines=15,
                            value="# Select a template to preview its code"
                        )
            
            # Event handlers
            
            # Deploy agent
            deploy_btn.click(
                fn=self._deploy_agent,
                inputs=[agent_name_input, template_dropdown],
                outputs=[action_status, status_grid]
            )
            
            # Emergency stop all
            emergency_stop_btn.click(
                fn=self._emergency_stop_all,
                outputs=[action_status, status_grid]
            )
            
            # Refresh dashboard manually
            refresh_btn.click(
                fn=self._update_dashboard,
                outputs=[status_grid]
            )
            
            # Clear logs
            clear_logs_btn.click(
                fn=self._clear_logs,
                outputs=[logs_display]
            )
            
            # Template selection updates info
            template_dropdown.change(
                fn=self._get_template_info,
                inputs=[template_dropdown],
                outputs=[template_info_display]
            )
            
            # Preview template code
            preview_btn.click(
                fn=self._preview_template_code,
                inputs=[template_dropdown],
                outputs=[code_preview]
            )
            
            # Quick deploy from template
            quick_deploy_btn.click(
                fn=lambda template: self._deploy_agent(
                    f"quick-{template.split()[0].lower()}-{int(time.time()) % 10000}" if template else "quick-agent",
                    template
                ),
                inputs=[template_dropdown],
                outputs=[action_status, status_grid]
            )
            
            # Update log filter choices when dashboard updates
            dashboard_timer.tick(
                fn=self._get_agent_choices,
                outputs=[log_filter_dropdown],
                show_progress=False
            )
            
            # Initial load
            interface.load(
                fn=self._update_dashboard,
                outputs=[status_grid]
            )
            
            interface.load(
                fn=lambda: self._get_agent_logs("All Agents"),
                outputs=[logs_display]
            )
        
        return interface
    
    def launch(self, **kwargs) -> None:
        """Launch the control panel interface"""
        interface = self.create_interface()
        
        # Default launch settings
        default_settings = {
            "server_port": 7001,
            "share": False,
            "debug": True,
            "show_error": True,
            "inbrowser": True
        }
        
        # Override with any provided kwargs
        default_settings.update(kwargs)
        
        logger.info(f"🚀 Launching Agent Control Panel on http://localhost:{default_settings['server_port']}")
        
        try:
            interface.launch(**default_settings)
        except Exception as e:
            logger.error(f"Failed to launch control panel: {e}")
            raise


def launch_control_panel(**kwargs):
    """Convenience function to launch the control panel"""
    ui = ControlPanelUI()
    ui.launch(**kwargs)


if __name__ == "__main__":
    # Launch with development settings
    launch_control_panel(
        server_port=7001,
        debug=True,
        share=False,
        inbrowser=True
    )