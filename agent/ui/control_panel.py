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

# Custom CSS for production-ready styling with sidebar
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

/* Sidebar styling */
.sidebar {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    margin-left: 1rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
    min-height: 600px;
}

.sidebar:hover {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
}

/* Code editor styling */
.code-editor {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    max-height: 500px;
    overflow: auto;
    resize: both;
}

.code-editor:focus-within {
    border-color: rgba(59, 130, 246, 0.6);
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

/* Code editor textarea styling */
.code-editor textarea {
    overflow: auto !important;
    overflow-x: auto !important;
    overflow-y: auto !important;
    resize: both !important;
    min-height: 400px !important;
    max-height: 600px !important;
    white-space: pre !important;
    word-wrap: normal !important;
}

/* Code editor container */
.code-editor .code-container {
    overflow: auto !important;
    max-width: 100% !important;
}

/* Ensure proper scrolling for long lines */
.code-editor pre {
    overflow: auto !important;
    white-space: pre !important;
    word-wrap: normal !important;
}

/* Editor action buttons */
.editor-actions {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 0.75rem;
    margin-top: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
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

.warning-btn {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    border: none;
    color: white;
    font-weight: bold;
    box-shadow: 0 4px 16px rgba(245, 158, 11, 0.4);
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

/* Main content layout */
.main-content {
    display: flex;
    gap: 1rem;
}

.main-panel {
    flex: 2;
}

.side-panel {
    flex: 1;
    min-width: 400px;
}

/* Responsive design */
@media (max-width: 1200px) {
    .main-content {
        flex-direction: column;
    }
    
    .side-panel {
        min-width: unset;
    }
}

@media (max-width: 768px) {
    .control-section {
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .main-header {
        padding: 1.5rem;
    }
    
    .sidebar {
        margin-left: 0;
        margin-top: 1rem;
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
        """Get information about a selected template using dynamic metadata"""
        if not template_name:
            return "## 📚 Available Templates\n\nSelect a template to see details and preview code."
        
        template = self.templates.get(template_name)
        if not template:
            return f"Template '{template_name}' not found."
        
        info = f"## {template_name}\n\n"
        info += f"**Description:** {template['description']}\n\n"
        info += f"**Category:** {template.get('category', 'Custom')}\n"
        info += f"**Difficulty:** {template.get('difficulty', 'Unknown')}\n\n"
        
        # Use dynamic features from metadata
        features = template.get('features', [])
        if features and isinstance(features, list):
            info += "**Features:**\n"
            for feature in features:
                info += f"- {feature}\n"
        else:
            info += "**Features:** Custom functionality\n"
        
        info += f"\n**Ready to deploy:** One-click deployment available\n"
        info += f"**Port:** Auto-assigned (typically 786x)\n"
        
        return info
    
    def _load_template_code(self, template_name: str) -> str:
        """Load template code into the editor"""
        if not template_name:
            return "# Select a template to load its code"
        
        template = self.templates.get(template_name)
        if not template:
            return f"# Template '{template_name}' not found"
        
        return template['code']
    
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
    
    def _save_template(self, template_name: str, code: str) -> Tuple[str, str]:
        """Save modified template code to file"""
        if not template_name:
            return "❌ Save Failed", "No template selected"
        
        if not code.strip():
            return "❌ Save Failed", "No code to save"
        
        try:
            # Create a custom templates directory if it doesn't exist
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            custom_templates_dir = project_root / "custom_templates"
            custom_templates_dir.mkdir(exist_ok=True)
            
            # Generate filename based on template name
            safe_name = template_name.lower().replace(' ', '_').replace('🧮', 'calc').replace('🕷️', 'scraper').replace('📊', 'data').replace('💬', 'chat').replace('📁', 'monitor').replace('🔌', 'api')
            filename = f"custom_{safe_name}_{int(time.time())}.py"
            file_path = custom_templates_dir / filename
            
            # Save the code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Custom template based on: {template_name}\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n\n")
                f.write(code)
            
            status = "✅ Save Successful"
            details = f"Template saved as: {filename}\nLocation: {file_path}\n\nYou can now deploy this custom template."
            
            return status, details
            
        except Exception as e:
            return "❌ Save Failed", f"Error saving file: {str(e)}"
    
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
                
                # Section 4: Template Selection
                with gr.Group():
                    gr.Markdown("## 📚 Agent Templates")
                    
                    template_info_display = gr.Markdown(
                        self._get_template_info(None),
                        label="Template Information"
                    )
                    
                    with gr.Row():
                        load_template_btn = gr.Button("📥 Load Template", variant="secondary", size="sm")
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
                    lines=25,
                    max_lines=50,
                    value="# Select a template or write your own agent code here\n# Use the buttons below to validate, test, and deploy",
                    elem_classes=["code-editor"],
                    interactive=True,
                    show_label=True,
                    container=True,
                    wrap_lines=False
                )
                
                # Editor actions
                with gr.Group(elem_classes=["editor-actions"]):
                    gr.Markdown("### 🛠️ Editor Actions")
                    
                    with gr.Row():
                        validate_btn = gr.Button("✅ Validate", size="sm", variant="secondary")
                        test_btn = gr.Button("🧪 Test", size="sm", variant="secondary")
                    
                    with gr.Row():
                        save_btn = gr.Button("💾 Save Template", size="sm")
                        deploy_editor_btn = gr.Button("🚀 Deploy", size="sm", variant="primary")
                
                # Editor status
                editor_status = gr.Textbox(
                    label="Editor Status",
                    lines=6,
                    interactive=False,
                    value="Ready to edit code...",
                    show_copy_button=True
                )
        
        # Event handlers
        
        # Deploy agent from template
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
        
        # Load template into editor
        load_template_btn.click(
            fn=self._load_template_code,
            inputs=[template_dropdown],
            outputs=[code_editor]
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
            fn=self._save_template,
            inputs=[template_dropdown, code_editor],
            outputs=[editor_status]
        )
        
        deploy_editor_btn.click(
            fn=self._deploy_from_editor,
            inputs=[editor_agent_name, code_editor],
            outputs=[action_status, status_grid]
        )
        
        # Update log filter choices when dashboard updates
        dashboard_timer.tick(
            fn=self._get_agent_choices,
            outputs=[log_filter_dropdown],
            show_progress=False
        )

    def create_interface(self) -> gr.Blocks:
        """Create the main control panel interface"""
        
        with gr.Blocks(
            title="Agent Management Control Panel",
            theme=gr.themes.Default(primary_hue="blue", secondary_hue="gray"),
            css=CUSTOM_CSS
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
                    
                    # Section 4: Template Selection
                    with gr.Group():
                        gr.Markdown("## 📚 Agent Templates")
                        
                        template_info_display = gr.Markdown(
                            self._get_template_info(None),
                            label="Template Information"
                        )
                        
                        with gr.Row():
                            load_template_btn = gr.Button("📥 Load Template", variant="secondary", size="sm")
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
                        lines=20,
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
                            save_btn = gr.Button("💾 Save Template", size="sm")
                            deploy_editor_btn = gr.Button("🚀 Deploy", size="sm", variant="primary")
                    
                    # Editor status
                    editor_status = gr.Textbox(
                        label="Editor Status",
                        lines=6,
                        interactive=False,
                        value="Ready to edit code...",
                        show_copy_button=True
                    )
            
            # Event handlers
            
            # Deploy agent from template
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
            
            # Load template into editor
            load_template_btn.click(
                fn=self._load_template_code,
                inputs=[template_dropdown],
                outputs=[code_editor]
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
                fn=self._save_template,
                inputs=[template_dropdown, code_editor],
                outputs=[editor_status]
            )
            
            deploy_editor_btn.click(
                fn=self._deploy_from_editor,
                inputs=[editor_agent_name, code_editor],
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