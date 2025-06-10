#!/usr/bin/env python3
"""
🤖 Gradio Control Panel for Agent Management System
Production-ready interface with advanced agent lifecycle management.
"""

import gradio as gr
import sys
import time
import json
import logging
import psutil
import subprocess
import re
import ast
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
        self.agents = self._load_enhanced_agents()
        self.logs_buffer = []
        self.max_log_lines = 1000
        self.system_metrics = self._get_system_metrics()
        
        # Track agent status for change detection
        self.previous_agent_status = {}
        
        # Track deployment statistics
        self.deployment_stats = {
            "total_deployed": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "active_agents": 0
        }
        
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics for monitoring"""
        try:            return {
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
    def _load_enhanced_agents(self) -> Dict[str, Dict[str, str]]:
        """Load enhanced agent files from external files"""
        return self._load_agents_from_files()

    def _load_agents_from_files(self) -> Dict[str, Dict[str, str]]:
        """Load agent files directly from agents directory"""
        agents = {}
        
        # Get the agents directory path
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        agents_dir = project_root / "agent/agents"
        
        # Ensure agents directory exists
        if not agents_dir.exists():
            logger.warning(f"agents directory not found at: {agents_dir}")
            # Try alternative path resolution
            alternative_path = Path.cwd() / "agents"
            if alternative_path.exists():
                agents_dir = alternative_path
                logger.info(f"Using alternative path: {agents_dir}")
            else:
                logger.error(f"Could not find agents directory")
                return agents
        
        logger.info(f"Loading agents from: {agents_dir}")
        
        # Load all .py files from agents directory
        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name.startswith("__"):  # Skip __pycache__ etc
                continue
            try:
                # Use filename as the agent name (without .py extension)
                agent_name = agent_file.stem
                # Read the agent file content
                with open(agent_file, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                # Extract metadata from the code content
                metadata = self._extract_agent_metadata(code_content, agent_name)
                agents[agent_name] = {
                    "description": metadata["description"],
                    "category": metadata["category"], 
                    "difficulty": metadata["difficulty"],
                    "features": metadata["features"],
                    "code": code_content,
                    "file_path": str(agent_file)  # Store the file path for saving
                }
            except Exception as e:
                logger.error(f"Error loading agent file {agent_file.name}: {e}")
                agents[agent_name] = {
                    "description": f"Error loading {agent_file.name}: {str(e)}",
                    "category": "System", 
                    "difficulty": "Error",
                    "features": ["Error loading file"],
                    "code": f"# Error loading {agent_file.name}\nprint('Error: {str(e)}')",
                    "file_path": str(agent_file)
                }
        return agents
    
    def _extract_agent_metadata(self, code_content: str, display_name: str) -> Dict[str, Any]:
        """Extract metadata from agent code content AGENT_INFO dictionary"""
        
        # Default fallback metadata
        default_metadata = {
            "description": "Custom agent template",
            "category": "Custom",
            "difficulty": "Unknown", 
            "features": ["Custom functionality"]
        }
        
        try:
            # Extract AGENT_INFO from docstring
            import re
            import ast
            
            # Look for AGENT_INFO in the docstring (triple quoted string at the top)
            docstring_pattern = r'"""[\s\S]*?AGENT_INFO\s*=\s*({[\s\S]*?})[\s\S]*?"""'
            match = re.search(docstring_pattern, code_content)
            
            if match:
                # Extract the dictionary string
                dict_str = match.group(1)
                
                # Parse the dictionary safely
                try:
                    # Clean up the string for parsing
                    dict_str = dict_str.replace('\n', ' ').strip()
                    agent_info = ast.literal_eval(dict_str)
                    
                    # Extract the relevant metadata
                    return {
                        "description": agent_info.get("description", default_metadata["description"]),
                        "category": agent_info.get("category", default_metadata["category"]),
                        "difficulty": agent_info.get("difficulty", default_metadata["difficulty"]),
                        "features": agent_info.get("features", default_metadata["features"])
                    }
                except (SyntaxError, ValueError) as parse_error:
                    logger.warning(f"Failed to parse AGENT_INFO for {display_name}: {parse_error}")
            
            # If no AGENT_INFO found, try alternative pattern (multiline)
            # Look for AGENT_INFO = { ... } spanning multiple lines
            agent_info_pattern = r'AGENT_INFO\s*=\s*{\s*([\s\S]*?)\s*}'
            match = re.search(agent_info_pattern, code_content)
            
            if match:
                # Build dictionary from key-value pairs
                content = match.group(1)
                agent_info = {}
                
                # Extract key-value pairs with improved regex
                kv_pattern = r'"([^"]+)"\s*:\s*("([^"]*)"|(\[[^\]]*\])|([^,\n]+))'
                for kv_match in re.finditer(kv_pattern, content):
                    key = kv_match.group(1)
                    value_str = kv_match.group(2).strip()
                    
                    # Parse different value types
                    if value_str.startswith('[') and value_str.endswith(']'):
                        # List value
                        try:
                            value = ast.literal_eval(value_str)
                        except:
                            value = [value_str.strip('[]"')]
                    elif value_str.startswith('"') and value_str.endswith('"'):
                        # String value
                        value = value_str.strip('"')
                    else:
                        # Other value
                        value = value_str.strip('"')
                    
                    agent_info[key] = value
                
                if agent_info:
                    return {
                        "description": agent_info.get("description", default_metadata["description"]),
                        "category": agent_info.get("category", default_metadata["category"]),
                        "difficulty": agent_info.get("difficulty", default_metadata["difficulty"]),
                        "features": agent_info.get("features", default_metadata["features"])
                    }
            
            logger.info(f"No AGENT_INFO found for {display_name}, using defaults")
            return default_metadata
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {display_name}: {e}")
            return default_metadata
    
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
            "not_found": "⚫"        }
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
    def _deploy_agent(self, agent_name: str) -> Tuple[str, List[List[str]]]:
        """Deploy an agent directly from the dropdown selection"""
        if not self.agent_runner:
            return "❌ Agent runner not available", self._update_dashboard()
        
        if not agent_name:
            return "❌ Please select an agent", self._update_dashboard()
        
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                return f"❌ Agent '{agent_name}' not found", self._update_dashboard()
            
            # Deploy the agent using the agent name directly
            success, message, metadata = self.agent_runner.start_agent(agent_name, agent['code'])
            
            if success:
                port = metadata.get('port', 'Unknown')
                result = f"✅ Agent '{agent_name}' deployed successfully!\n"
                result += f"🌐 URL: http://localhost:{port}\n"
                result += f"📋 Agent: {agent_name}\n"
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
    def _get_agent_logs(self) -> str:
        """Get agent status logs - only show changes in health status"""
        if not self.agent_runner:
            return "🔧 Agent runner not available\n\nPlease ensure the agent runner is properly initialized to view logs."
        
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            agents_status = self.agent_runner.list_agents()
            
            # Create header
            header = f"📋 **Agent Health Monitor**\n"
            header += f"🕐 Last checked: {current_time}\n"
            header += "=" * 60 + "\n\n"
            
            if not agents_status:
                if self.previous_agent_status:
                    # Agents were running before but now none are
                    log_entry = f"[{current_time}] ℹ️  All agents have stopped running"
                    self.logs_buffer.append(log_entry)
                    self.previous_agent_status = {}
                return header + f"[{current_time}] ℹ️  No agents are currently running\n\nDeploy some agents to monitor their health status."
            
            # Detect status changes
            current_logs = []
            
            for name, info in agents_status.items():
                status = info.get('status', 'unknown')
                port = info.get('port', 'N/A')
                
                # Check if this is a new agent or status changed
                if name not in self.previous_agent_status:
                    # New agent detected
                    log_entry = f"[{current_time}] [{name}:{port}] 🆕 New agent detected - Status: {status}"
                    current_logs.append(log_entry)
                    
                    # Add initial health status
                    if status == 'running':
                        health_entry = f"[{current_time}] [{name}:{port}] ✅ Agent is healthy - CPU: {info.get('cpu_percent', 0):.1f}%, Memory: {info.get('memory_mb', 0):.1f}MB"
                        current_logs.append(health_entry)
                        
                elif self.previous_agent_status[name].get('status') != status:
                    # Status changed
                    old_status = self.previous_agent_status[name].get('status', 'unknown')
                    log_entry = f"[{current_time}] [{name}:{port}] 🔄 Status changed: {old_status} → {status}"
                    current_logs.append(log_entry)
                    
                elif status == 'running':
                    # Check for significant health metric changes for running agents
                    old_cpu = self.previous_agent_status[name].get('cpu_percent', 0)
                    old_memory = self.previous_agent_status[name].get('memory_mb', 0)
                    new_cpu = info.get('cpu_percent', 0)
                    new_memory = info.get('memory_mb', 0)
                    
                    # Log if CPU or memory changed significantly (>10% change)
                    if abs(new_cpu - old_cpu) > 10 or abs(new_memory - old_memory) > 50:
                        health_entry = f"[{current_time}] [{name}:{port}] 📊 Health update - CPU: {new_cpu:.1f}% ({old_cpu:.1f}%), Memory: {new_memory:.1f}MB ({old_memory:.1f}MB)"
                        current_logs.append(health_entry)
                        
                elif status == 'error':
                    # Always log error status
                    log_entry = f"[{current_time}] [{name}:{port}] ❌ Agent in error state"
                    current_logs.append(log_entry)
            
            # Check for removed agents
            for name in self.previous_agent_status:
                if name not in agents_status:
                    log_entry = f"[{current_time}] [{name}] 🗑️  Agent removed/stopped"
                    current_logs.append(log_entry)
            
            # Update previous status
            self.previous_agent_status = agents_status.copy()
            
            # Add new logs to buffer
            if current_logs:
                self.logs_buffer.extend(current_logs)
                
                # Maintain buffer size
                if len(self.logs_buffer) > self.max_log_lines:
                    self.logs_buffer = self.logs_buffer[-self.max_log_lines:]
            
            # Build display
            if not self.logs_buffer:
                return header + f"[{current_time}] 📭 No status changes detected yet\n\nAgent health changes will appear here when they occur."
            
            # Show recent status changes
            recent_logs = self.logs_buffer[-20:]  # Show last 20 entries
            result = header + "\n".join(recent_logs)
            
            # Add footer with helpful info
            result += f"\n\n📌 Note: Only status changes are logged to reduce noise"
            if len(recent_logs) >= 20:
                result += f" | Showing last {len(recent_logs)} changes"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting agent logs: {e}")
            return f"❌ Error retrieving logs: {str(e)}\n\nPlease check the agent runner configuration and try again."
    def _clear_logs(self) -> str:
        """Clear the logs display"""
        self.logs_buffer = []
        self.previous_agent_status = {}
        current_time = datetime.now().strftime("%H:%M:%S")
        return f"[{current_time}] Logs cleared - Agent health monitoring reset"
    
    def _get_agent_info(self, agent_name: str) -> str:
        """Get information about a selected agent using dynamic metadata"""
        if not agent_name:
            return "## 📚 Available Agents\n\nSelect an agent to see details and preview code."
        
        agent = self.agents.get(agent_name)
        if not agent:
            return f"Agent '{agent_name}' not found."
        
        info = f"## {agent_name}\n\n"
        info += f"**Description:** {agent['description']}\n\n"
        info += f"**Category:** {agent.get('category', 'Custom')}\n"
        info += f"**Difficulty:** {agent.get('difficulty', 'Unknown')}\n\n"
        
        # Use dynamic features from metadata
        features = agent.get('features', [])
        if features and isinstance(features, list):
            info += "**Features:**\n"
            for feature in features:
                info += f"- {feature}\n"
        else:
            info += "**Features:** Custom functionality\n"
        
        info += f"\n**Ready to deploy:** One-click deployment available\n"
        info += f"**Port:** Auto-assigned (typically 786x)\n"
        
        return info
    
    def _load_agent_code(self, agent_name: str) -> str:
        """Load agent code into the editor"""
        if not agent_name:
            return "# Select an agent to load its code"
        
        agent = self.agents.get(agent_name)
        if not agent:
            return f"# Agent '{agent_name}' not found"
        
        return agent['code']
    
    def _validate_code(self, code: str) -> Tuple[str, str]:
        """Validate Python code syntax"""
        if not code.strip():
            return "❌ Validation Failed", "Code is empty"
        
        try:
            # Basic syntax check
            compile(code, '<string>', 'exec')
            
            # Check for required components for MCP agents
            required_patterns = [
                ('class', 'Agent class definition'),
                ('def handle', 'Handle method for requests'),
                ('gradio', 'Gradio import for UI')
            ]
            
            validation_results = []
            for pattern, desc in required_patterns:
                if pattern in code:
                    validation_results.append(f"✅ {desc}")
                else:
                    validation_results.append(f"⚠️ Missing: {desc}")
            
            status = "✅ Validation Passed"
            details = "Code syntax is valid.\n\n" + "\n".join(validation_results)
            
            return status, details
            
        except SyntaxError as e:
            return "❌ Syntax Error", f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return "❌ Validation Failed", str(e)
    
    def _test_code(self, code: str) -> Tuple[str, str]:
        """Test code execution in a safe environment"""
        if not code.strip():
            return "❌ Test Failed", "No code to test"
        
        try:
            # First validate syntax
            compile(code, '<string>', 'exec')
            
            # For now, we'll do basic validation
            # In a full implementation, this could run in a sandboxed environment
            test_results = []
            
            # Check if it's a valid agent structure
            if 'class' in code and 'def' in code:
                test_results.append("✅ Class structure detected")
            
            if 'gradio' in code or 'gr.' in code:
                test_results.append("✅ Gradio components found")
            
            if 'def handle' in code or 'def main' in code:
                test_results.append("✅ Handler methods found")
            
            if not test_results:
                test_results.append("⚠️ No recognizable agent patterns found")
            
            status = "✅ Test Completed"
            details = "Basic structure test completed.\n\n" + "\n".join(test_results)
            details += "\n\nNote: This is a basic validation. Deploy to test full functionality."
            
            return status, details
            
        except SyntaxError as e:
            return "❌ Test Failed", f"Syntax Error - Line {e.lineno}: {e.msg}"
        except Exception as e:
            return "❌ Test Failed", str(e)
    def _save_agent(self, agent_name: str, code: str) -> Tuple[str, str]:
        """Save modified agent code back to the original agent file"""
        if not agent_name:
            return "❌ Save Failed", "No agent selected"
        
        if not code.strip():
            return "❌ Save Failed", "No code to save"
        
        try:
            agent = self.agents.get(agent_name)
            if not agent or 'file_path' not in agent:
                return "❌ Save Failed", f"Cannot find original file path for agent '{agent_name}'"
            original_file_path = Path(agent['file_path'])
            if not original_file_path.exists():
                return "❌ Save Failed", f"Original agent file not found: {original_file_path}"
            backup_path = original_file_path.with_suffix(f".backup_{int(time.time())}.py")
            with open(original_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            with open(original_file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            self.agents[agent_name]['code'] = code
            status = "✅ Save Successful"
            details = f"Agent '{agent_name}' updated successfully!\n"
            details += f"File: {original_file_path}\n"
            details += f"Backup created: {backup_path.name}\n\n"
            details += "Changes have been saved to the original agent file."
            return status, details
        except Exception as e:
            return "❌ Save Failed", f"Error saving to original file: {str(e)}"
    
    def _deploy_from_editor(self, agent_name: str, code: str) -> Tuple[str, List[List[str]]]:
        """Deploy agent directly from the code editor"""
        if not self.agent_runner:
            return "❌ Agent runner not available", self._update_dashboard()
        if not agent_name or not agent_name.strip():
            return "❌ Please provide an agent name", self._update_dashboard()
        
        if not code.strip():
            return "❌ No code to deploy", self._update_dashboard()
        
        agent_name = agent_name.strip().replace(' ', '_')
        
        try:
            # Validate code first
            compile(code, '<string>', 'exec')
            
            # Deploy the agent
            success, message, metadata = self.agent_runner.start_agent(agent_name, code)
            
            if success:
                self.deployment_stats["total_deployed"] += 1
                self.deployment_stats["successful_deployments"] += 1
                result = f"✅ Agent '{agent_name}' deployed successfully!\n"
                result += f"📊 Port: {metadata.get('port', 'auto-assigned')}\n"
                result += f"🔄 Status: {metadata.get('status', 'running')}\n"
                result += f"⏱️ Deployed: {datetime.now().strftime('%H:%M:%S')}"
            else:
                self.deployment_stats["total_deployed"] += 1
                self.deployment_stats["failed_deployments"] += 1
                result = f"❌ Failed to deploy agent '{agent_name}'\n"
                result += f"Error: {message}"
            
            return result, self._update_dashboard()
            
        except SyntaxError as e:
            return f"❌ Code has syntax errors:\nLine {e.lineno}: {e.msg}", self._update_dashboard()
        except Exception as e:
            logger.error(f"Error deploying from editor: {e}")
            return f"❌ Deployment failed: {str(e)}", self._update_dashboard()
    def create_components(self) -> None:
        """Create the control panel components for embedding in another interface"""
        
        # Header
        gr.Markdown("""
        # 🤖 Agent Management Control Panel
        **Real-time agent deployment and monitoring system with integrated code editor**
        """)
        
        # Main layout: Content + Sidebar
        with gr.Row():
            # Main content area
            with gr.Column(scale=2, elem_classes=["main-panel"]):
                
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
                            agent_dropdown = gr.Dropdown(
                                choices=list(self.agents.keys()),
                                label="Available Agents",
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
                
                # Section 3: Logs Panel - Change-based Output
                with gr.Group():
                    gr.Markdown("## 📋 Agent Health Monitor")
                    
                    logs_display = gr.Textbox(
                        label="Status Changes",
                        lines=12,
                        interactive=False,
                        value="Waiting for agent status changes...",
                        show_copy_button=True
                    )
                    
                    # Manual refresh button (no auto-refresh)
                    with gr.Row():
                        manual_refresh_logs_btn = gr.Button("🔄 Check for Changes", size="sm")
                
                # Section 4: Agent Selection
                with gr.Group():
                    gr.Markdown("## 📚 Agents")
                    
                    agent_info_display = gr.Markdown(
                        self._get_agent_info(None),
                        label="Agent Information"
                    )
                    
                    with gr.Row():
                        load_agent_btn = gr.Button("📥 Load Agent", variant="secondary", size="sm")
                        quick_deploy_btn = gr.Button("⚡ Quick Deploy", variant="secondary", size="sm")
            
            # Sidebar: Code Editor
            with gr.Column(scale=1, elem_classes=["side-panel", "sidebar"]):
                gr.Markdown("## 🔧 Code Editor & Testing")
                
                # Editor name input
                editor_agent_name = gr.Textbox(
                    label="Agent Name for Editor",
                    placeholder="Enter name for code deployment",
                    value=""
                )
                
                # Code editor
                code_editor = gr.Code(
                    label="Agent Code Editor",
                    language="python",
                    max_lines=None,
                    value="# Select a template or write your own agent code here\n# Use the buttons below to validate, test, and deploy",
                    elem_classes=["code-editor"]
                )
                
                # Editor actions
                with gr.Group(elem_classes=["editor-actions"]):
                    gr.Markdown("### 🛠️ Editor Actions")
                    
                    with gr.Row():
                        validate_btn = gr.Button("✅ Validate", size="sm", variant="secondary")
                        test_btn = gr.Button("🧪 Test", size="sm", variant="secondary")
                    
                    with gr.Row():
                        save_btn = gr.Button("💾 Save Agent", size="sm")
                        deploy_editor_btn = gr.Button("🚀 Deploy", size="sm", variant="primary")
                
                # Editor status
                editor_status = gr.Textbox(
                    label="Editor Status",
                    lines=6,
                    interactive=False,
                    value="Ready to edit code...",
                    show_copy_button=True
                )
        
        # Event handlers - Updated to remove filter functionality
        
        # Deploy agent from template
        deploy_btn.click(
            fn=self._deploy_agent,
            inputs=[agent_dropdown],
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
        
        # Manual logs refresh
        manual_refresh_logs_btn.click(
            fn=self._get_agent_logs,
            outputs=[logs_display]
        )
        
        # Agent selection updates info
        agent_dropdown.change(
            fn=self._get_agent_info,
            inputs=[agent_dropdown],
            outputs=[agent_info_display]
        )
        
        # Load agent into editor
        load_agent_btn.click(
            fn=self._load_agent_code,
            inputs=[agent_dropdown],
            outputs=[code_editor]
        )
          # Quick deploy from agent
        quick_deploy_btn.click(
            fn=self._deploy_agent,
            inputs=[agent_dropdown],
            outputs=[action_status, status_grid]
        )
        
        # Editor actions
        validate_btn.click(
            fn=self._validate_code,
            inputs=[code_editor],
            outputs=[editor_status]
        )
        
        test_btn.click(
            fn=self._test_code,
            inputs=[code_editor],
            outputs=[editor_status]
        )
        
        save_btn.click(
            fn=self._save_agent,
            inputs=[agent_dropdown, code_editor],
            outputs=[editor_status]
        )
        
        deploy_editor_btn.click(
            fn=self._deploy_from_editor,
            inputs=[editor_agent_name, code_editor],
            outputs=[action_status, status_grid]
        )
        
    def create_interface(self) -> gr.Blocks:
        """Create the main control panel interface"""
        
        with gr.Blocks(
            title="Agent Management Control Panel",
            theme=gr.themes.Default(primary_hue="blue", secondary_hue="gray")
        ) as interface:
            
            # Header
            gr.Markdown("""
            # 🤖 Agent Management Control Panel
            **Real-time agent deployment and monitoring system with integrated code editor**
            """)
            
            # Main layout: Content + Sidebar
            with gr.Row():
                # Main content area
                with gr.Column(scale=2, elem_classes=["main-panel"]):
                    
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
                                agent_dropdown = gr.Dropdown(
                                    choices=list(self.agents.keys()),
                                    label="Available Agents",
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
                
                # Section 3: Logs Panel - Change-based Output
                with gr.Group():
                    gr.Markdown("## 📋 Agent Health Monitor")
                    
                    logs_display = gr.Textbox(
                        label="Status Changes",
                        lines=12,
                        interactive=False,
                        value="Waiting for agent status changes...",
                        show_copy_button=True
                    )
                    
                    # Manual refresh button (no auto-refresh)
                    with gr.Row():
                        manual_refresh_logs_btn = gr.Button("🔄 Check for Changes", size="sm")
                
                # Section 4: Agent Selection
                with gr.Group():
                    gr.Markdown("## 📚 Agents")
                    
                    agent_info_display = gr.Markdown(
                        self._get_agent_info(None),
                        label="Agent Information"
                    )
                    
                    with gr.Row():
                        load_agent_btn = gr.Button("📥 Load Agent", variant="secondary", size="sm")
                        quick_deploy_btn = gr.Button("⚡ Quick Deploy", variant="secondary", size="sm")
            
                # Sidebar: Code Editor
                with gr.Column(scale=1, elem_classes=["side-panel", "sidebar"]):
                    gr.Markdown("## 🔧 Code Editor & Testing")
                    
                    # Editor name input
                    editor_agent_name = gr.Textbox(
                        label="Agent Name for Editor",
                        placeholder="Enter name for code deployment",
                        value=""
                    )
                    
                    # Code editor
                    code_editor = gr.Code(
                        label="Agent Code Editor",
                        language="python",
                        lines=100,
                        value="# Select a template or write your own agent code here\n# Use the buttons below to validate, test, and deploy",
                        elem_classes=["code-editor"]
                    )
                    
                    # Editor actions
                    with gr.Group(elem_classes=["editor-actions"]):
                        gr.Markdown("### 🛠️ Editor Actions")
                        
                        with gr.Row():
                            validate_btn = gr.Button("✅ Validate", size="sm", variant="secondary")
                            test_btn = gr.Button("🧪 Test", size="sm", variant="secondary")
                        
                        with gr.Row():
                            save_btn = gr.Button("💾 Save Agent", size="sm")
                            deploy_editor_btn = gr.Button("🚀 Deploy", size="sm", variant="primary")
                
                    # Editor status
                    editor_status = gr.Textbox(
                        label="Editor Status",
                        lines=6,
                        interactive=False,
                        value="Ready to edit code...",
                        show_copy_button=True
                    )
            
            # Event handlers - Updated to remove filter functionality
            
            # Deploy agent from template
            deploy_btn.click(
                fn=self._deploy_agent,
                inputs=[agent_dropdown],
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
            
            # Manual logs refresh
            manual_refresh_logs_btn.click(
                fn=self._get_agent_logs,
                outputs=[logs_display]
            )
            
            # Agent selection updates info
            agent_dropdown.change(
                fn=self._get_agent_info,
                inputs=[agent_dropdown],
                outputs=[agent_info_display]
            )
            
            # Load agent into editor
            load_agent_btn.click(
                fn=self._load_agent_code,
                inputs=[agent_dropdown],
                outputs=[code_editor]
            )
              # Quick deploy from agent
            quick_deploy_btn.click(
                fn=self._deploy_agent,
                inputs=[agent_dropdown],
                outputs=[action_status, status_grid]
            )

            # Editor actions
            validate_btn.click(
                fn=self._validate_code,
                inputs=[code_editor],
                outputs=[editor_status]
            )
            
            test_btn.click(
                fn=self._test_code,
                inputs=[code_editor],
                outputs=[editor_status]
            )
            
            save_btn.click(
                fn=self._save_agent,
                inputs=[agent_dropdown, code_editor],
                outputs=[editor_status]
            )
            
            deploy_editor_btn.click(
                fn=self._deploy_from_editor,
                inputs=[editor_agent_name, code_editor],
                outputs=[action_status, status_grid]            )
            
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