import gradio as gr
import os
import time
import threading
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
import fnmatch
import hashlib

class AdvancedFileMonitor:
    def __init__(self):
        self.monitoring: bool = False
        self.events: List[Dict] = []
        self.watch_directory: Optional[Path] = None
        self.last_scan: Dict[str, Dict] = {}
        self.monitor_thread: Optional[threading.Thread] = None
        self.filters = {
            "extensions": set(),
            "exclude_patterns": set(),
            "min_size": 0,
            "max_size": float('inf'),
            "event_types": {"created", "modified", "deleted", "moved"}
        }
        self.analytics = {
            "total_events": 0,
            "events_by_type": {"created": 0, "modified": 0, "deleted": 0, "moved": 0},
            "most_active_files": {},
            "hourly_activity": [0] * 24,
            "file_types": {}
        }
        self.alert_rules = []
        
    def set_filters(self, extensions: str = "", exclude_patterns: str = "", 
                   min_size: int = 0, max_size: int = 0, event_types: List[str] = None) -> str:
        """Configure monitoring filters"""
        try:
            # Parse extensions
            if extensions.strip():
                self.filters["extensions"] = {ext.strip().lower() for ext in extensions.split(",")}
            else:
                self.filters["extensions"] = set()
            
            # Parse exclude patterns
            if exclude_patterns.strip():
                self.filters["exclude_patterns"] = {pattern.strip() for pattern in exclude_patterns.split(",")}
            else:
                self.filters["exclude_patterns"] = set()
            
            # Set size limits
            self.filters["min_size"] = max(0, min_size)
            self.filters["max_size"] = max_size if max_size > 0 else float('inf')
            
            # Set event types
            if event_types:
                self.filters["event_types"] = set(event_types)
            else:
                self.filters["event_types"] = {"created", "modified", "deleted", "moved"}
            
            active_filters = []
            if self.filters["extensions"]:
                active_filters.append(f"Extensions: {', '.join(self.filters['extensions'])}")
            if self.filters["exclude_patterns"]:
                active_filters.append(f"Exclude: {', '.join(self.filters['exclude_patterns'])}")
            if self.filters["min_size"] > 0:
                active_filters.append(f"Min size: {self.filters['min_size']} bytes")
            if self.filters["max_size"] < float('inf'):
                active_filters.append(f"Max size: {self.filters['max_size']} bytes")
            
            return f"✅ Filters updated:\n" + "\n".join([f"• {f}" for f in active_filters]) if active_filters else "✅ All filters cleared"
            
        except Exception as e:
            return f"❌ Error setting filters: {str(e)}"
    
    def add_alert_rule(self, rule_name: str, condition: str, action: str) -> str:
        """Add alert rule for specific conditions"""
        try:
            rule = {
                "name": rule_name,
                "condition": condition.lower(),
                "action": action.lower(),
                "created": datetime.now().isoformat(),
                "triggered_count": 0
            }
            self.alert_rules.append(rule)
            return f"✅ Alert rule '{rule_name}' added"
        except Exception as e:
            return f"❌ Error adding alert rule: {str(e)}"
    
    def start_monitoring(self, directory_path: str) -> str:
        """Start advanced monitoring with enhanced capabilities"""
        try:
            if not directory_path.strip():
                return "❌ Please specify a directory path"
            
            if directory_path == ".":
                directory_path = os.getcwd()
            
            directory_path = os.path.abspath(directory_path)
            
            if not os.path.exists(directory_path):
                return f"❌ Directory '{directory_path}' does not exist"
            
            if not os.path.isdir(directory_path):
                return f"❌ '{directory_path}' is not a directory"
            
            # Stop existing monitoring
            if self.monitoring:
                self.stop_monitoring()
            
            self.watch_directory = Path(directory_path)
            self.monitoring = True
            self.events = []
            
            # Reset analytics
            self.analytics = {
                "total_events": 0,
                "events_by_type": {"created": 0, "modified": 0, "deleted": 0, "moved": 0},
                "most_active_files": {},
                "hourly_activity": [0] * 24,
                "file_types": {}
            }
            
            # Initialize baseline scan
            self.last_scan = self._comprehensive_scan()
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._advanced_monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            return f"🚀 **Advanced monitoring started**\n\n• **Directory**: {directory_path}\n• **Files tracked**: {len(self.last_scan)}\n• **Filters active**: {len([f for f in [self.filters['extensions'], self.filters['exclude_patterns']] if f])}\n• **Alert rules**: {len(self.alert_rules)}"
            
        except Exception as e:
            return f"❌ Failed to start monitoring: {str(e)}"
    
    def stop_monitoring(self) -> str:
        """Stop monitoring with summary"""
        if not self.monitoring:
            return "ℹ️ Monitoring is not active"
        
        self.monitoring = False
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        # Generate summary
        summary = f"🛑 **Monitoring stopped**\n\n"
        summary += f"• **Total events**: {self.analytics['total_events']}\n"
        summary += f"• **Created**: {self.analytics['events_by_type']['created']}\n"
        summary += f"• **Modified**: {self.analytics['events_by_type']['modified']}\n"
        summary += f"• **Deleted**: {self.analytics['events_by_type']['deleted']}\n"
        
        if self.analytics['most_active_files']:
            most_active = max(self.analytics['most_active_files'].items(), key=lambda x: x[1])
            summary += f"• **Most active file**: {os.path.basename(most_active[0])} ({most_active[1]} events)\n"
        
        return summary
    
    def _comprehensive_scan(self) -> Dict[str, Dict]:
        """Perform comprehensive directory scan"""
        current_files = {}
        
        try:
            for file_path in self.watch_directory.rglob('*'):
                if file_path.is_file():
                    if self._should_monitor_file(file_path):
                        stat = file_path.stat()
                        
                        # Calculate file hash for content change detection
                        file_hash = None
                        try:
                            if stat.st_size < 10 * 1024 * 1024:  # Only hash files < 10MB
                                with open(file_path, 'rb') as f:
                                    file_hash = hashlib.md5(f.read()).hexdigest()
                        except:
                            pass
                        
                        current_files[str(file_path)] = {
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'created': stat.st_ctime,
                            'hash': file_hash,
                            'extension': file_path.suffix.lower()
                        }
                        
        except Exception as e:
            self._add_event("error", f"Scan error: {str(e)}", "system")
            
        return current_files
    
    def _should_monitor_file(self, file_path: Path) -> bool:
        """Check if file should be monitored based on filters"""
        # Check extension filter
        if self.filters["extensions"]:
            if file_path.suffix.lower() not in self.filters["extensions"]:
                return False
        
        # Check exclude patterns
        for pattern in self.filters["exclude_patterns"]:
            if fnmatch.fnmatch(file_path.name, pattern) or fnmatch.fnmatch(str(file_path), pattern):
                return False
        
        # Check size filter (if file exists)
        try:
            if file_path.exists():
                size = file_path.stat().st_size
                if size < self.filters["min_size"] or size > self.filters["max_size"]:
                    return False
        except:
            pass
        
        return True
    
    def _advanced_monitor_loop(self):
        """Advanced monitoring loop with enhanced detection"""
        while self.monitoring:
            try:
                current_scan = self._comprehensive_scan()
                
                # Detect new files
                for file_path in current_scan:
                    if file_path not in self.last_scan:
                        if "created" in self.filters["event_types"]:
                            self._add_event("created", file_path, "file", 
                                          size=current_scan[file_path]['size'],
                                          extension=current_scan[file_path]['extension'])
                
                # Detect deleted files
                for file_path in self.last_scan:
                    if file_path not in current_scan:
                        if "deleted" in self.filters["event_types"]:
                            self._add_event("deleted", file_path, "file",
                                          size=self.last_scan[file_path]['size'],
                                          extension=self.last_scan[file_path]['extension'])
                
                # Detect modified files
                for file_path in current_scan:
                    if file_path in self.last_scan:
                        old_info = self.last_scan[file_path]
                        new_info = current_scan[file_path]
                        
                        # Check for modifications
                        if old_info['modified'] != new_info['modified']:
                            if "modified" in self.filters["event_types"]:
                                change_type = "content" if old_info.get('hash') != new_info.get('hash') else "timestamp"
                                self._add_event("modified", file_path, "file",
                                              change_type=change_type,
                                              size_change=new_info['size'] - old_info['size'],
                                              extension=new_info['extension'])
                
                self.last_scan = current_scan
                
                # Clean old events (keep last 1000)
                if len(self.events) > 1000:
                    self.events = self.events[-1000:]
                    
            except Exception as e:
                self._add_event("error", f"Monitor error: {str(e)}", "system")
            
            time.sleep(1)  # Check every second for responsiveness
    
    def _add_event(self, event_type: str, file_path: str, source: str, **metadata):
        """Add event with metadata and analytics"""
        timestamp = datetime.now()
        
        event = {
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "source": source,
            "metadata": metadata
        }
        
        self.events.append(event)
        
        # Update analytics
        self.analytics["total_events"] += 1
        
        if event_type in self.analytics["events_by_type"]:
            self.analytics["events_by_type"][event_type] += 1
        
        # Track file activity
        if file_path not in self.analytics["most_active_files"]:
            self.analytics["most_active_files"][file_path] = 0
        self.analytics["most_active_files"][file_path] += 1
        
        # Track hourly activity
        self.analytics["hourly_activity"][timestamp.hour] += 1
        
        # Track file types
        if "extension" in metadata:
            ext = metadata["extension"] or "no_ext"
            if ext not in self.analytics["file_types"]:
                self.analytics["file_types"][ext] = 0
            self.analytics["file_types"][ext] += 1
        
        # Check alert rules
        self._check_alert_rules(event)
    
    def _check_alert_rules(self, event: Dict):
        """Check if event triggers any alert rules"""
        for rule in self.alert_rules:
            try:
                condition = rule["condition"]
                triggered = False
                
                if "large file" in condition and event.get("metadata", {}).get("size", 0) > 100 * 1024 * 1024:
                    triggered = True
                elif "frequent" in condition and self.analytics["most_active_files"].get(event["file_path"], 0) > 10:
                    triggered = True
                elif condition in event["type"]:
                    triggered = True
                
                if triggered:
                    rule["triggered_count"] += 1
                    self._add_event("alert", f"Alert: {rule['name']} - {event['file_name']}", "system",
                                  rule_name=rule["name"], original_event=event["type"])
                    
            except Exception as e:
                continue
    
    def get_formatted_events(self, filter_type: str = "all", limit: int = 50) -> str:
        """Get formatted events for display"""
        if not self.events:
            return "📭 No events recorded yet\n\nStart monitoring a directory to see file system changes in real-time."
        
        # Filter events
        filtered_events = self.events
        if filter_type != "all":
            filtered_events = [e for e in self.events if e["type"] == filter_type]
        
        # Get recent events
        recent_events = filtered_events[-limit:]
        
        if not recent_events:
            return f"📭 No {filter_type} events found"
        
        # Format events
        formatted = f"📋 **Recent Events ({len(recent_events)}/{len(self.events)} total)**\n\n"
        
        for event in reversed(recent_events[-20:]):  # Show last 20
            timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
            event_type = event["type"].upper()
            file_name = event["file_name"]
            
            # Add emoji based on event type
            emoji_map = {
                "created": "🆕", "modified": "✏️", "deleted": "🗑️", 
                "moved": "📦", "error": "⚠️", "alert": "🚨"
            }
            emoji = emoji_map.get(event["type"], "📄")
            
            line = f"{emoji} `[{timestamp}]` **{event_type}**: {file_name}"
            
            # Add metadata if available
            metadata = event.get("metadata", {})
            if "size" in metadata:
                size_mb = metadata["size"] / (1024 * 1024)
                line += f" ({size_mb:.1f}MB)"
            elif "size_change" in metadata:
                change = metadata["size_change"]
                if change > 0:
                    line += f" (+{change} bytes)"
                elif change < 0:
                    line += f" ({change} bytes)"
            
            if "change_type" in metadata:
                line += f" [{metadata['change_type']}]"
            
            if "rule_name" in metadata:
                line += f" [Rule: {metadata['rule_name']}]"
            
            formatted += line + "\n"
        
        return formatted
    
    def get_analytics_summary(self) -> str:
        """Get comprehensive analytics summary"""
        if self.analytics["total_events"] == 0:
            return "📊 **Analytics Summary**\n\nNo events to analyze yet. Start monitoring to collect data!"
        
        summary = f"📊 **Analytics Summary**\n\n"
        
        # Basic stats
        summary += f"**📈 Event Statistics:**\n"
        summary += f"• Total Events: {self.analytics['total_events']}\n"
        for event_type, count in self.analytics['events_by_type'].items():
            if count > 0:
                percentage = (count / self.analytics['total_events']) * 100
                summary += f"• {event_type.title()}: {count} ({percentage:.1f}%)\n"
        
        # Most active files
        if self.analytics['most_active_files']:
            summary += f"\n**🔥 Most Active Files:**\n"
            sorted_files = sorted(self.analytics['most_active_files'].items(), 
                                key=lambda x: x[1], reverse=True)[:5]
            for file_path, count in sorted_files:
                summary += f"• {os.path.basename(file_path)}: {count} events\n"
        
        # File types
        if self.analytics['file_types']:
            summary += f"\n**📄 File Types:**\n"
            sorted_types = sorted(self.analytics['file_types'].items(), 
                                key=lambda x: x[1], reverse=True)[:5]
            for ext, count in sorted_types:
                ext_display = ext if ext != "no_ext" else "No extension"
                summary += f"• {ext_display}: {count} events\n"
        
        # Hourly activity
        current_hour = datetime.now().hour
        most_active_hour = self.analytics['hourly_activity'].index(max(self.analytics['hourly_activity']))
        summary += f"\n**⏰ Activity Patterns:**\n"
        summary += f"• Most active hour: {most_active_hour:02d}:00 ({self.analytics['hourly_activity'][most_active_hour]} events)\n"
        summary += f"• Current hour activity: {self.analytics['hourly_activity'][current_hour]} events\n"
        
        # Alert summary
        if self.alert_rules:
            summary += f"\n**🚨 Alert Rules:**\n"
            for rule in self.alert_rules:
                summary += f"• {rule['name']}: {rule['triggered_count']} triggers\n"
        
        return summary
    
    def export_data(self) -> str:
        """Export monitoring data"""
        if not self.events:
            return "📭 No data to export"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "monitoring_config": {
                "directory": str(self.watch_directory) if self.watch_directory else None,
                "filters": {
                    "extensions": list(self.filters["extensions"]),
                    "exclude_patterns": list(self.filters["exclude_patterns"]),
                    "size_limits": [self.filters["min_size"], self.filters["max_size"]],
                    "event_types": list(self.filters["event_types"])
                }
            },
            "analytics": {
                **self.analytics,
                "most_active_files": dict(list(self.analytics["most_active_files"].items())[:10])
            },
            "alert_rules": self.alert_rules,
            "events": self.events[-100:]  # Last 100 events
        }
        
        summary = f"📤 **Export Summary**\n\n"
        summary += f"• **Events exported**: {len(self.events[-100:])}\n"
        summary += f"• **Total events**: {len(self.events)}\n"
        summary += f"• **Export timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"• **Analytics included**: Yes\n"
        summary += f"• **Alert rules**: {len(self.alert_rules)}\n\n"
        
        # Sample data preview
        summary += f"**Sample Export Data:**\n```json\n{json.dumps(export_data, indent=2)[:500]}...\n```"
        
        return summary

# Create advanced monitor instance
monitor = AdvancedFileMonitor()

# Enhanced Gradio interface
with gr.Blocks(title="📁 File Monitor Pro", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # 📁 File Monitor Pro Agent
    **Advanced file system monitoring with real-time alerts, filtering, and analytics**
    
    Features: Smart filtering, event analytics, alert rules, comprehensive monitoring
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Row():
                directory_input = gr.Textbox(
                    label="📂 Directory to Monitor",
                    placeholder="/path/to/directory or . for current directory",
                    scale=3
                )
                start_btn = gr.Button("🚀 Start", variant="primary", scale=1)
                stop_btn = gr.Button("🛑 Stop", variant="stop", scale=1)
            
            status_output = gr.Textbox(label="📊 Status", lines=4, interactive=False)
            
            # Filters section
            with gr.Accordion("🔧 Advanced Filters", open=False):
                with gr.Row():
                    extensions_filter = gr.Textbox(
                        label="File Extensions (comma-separated)",
                        placeholder=".txt,.py,.js,.log",
                        scale=2
                    )
                    exclude_patterns = gr.Textbox(
                        label="Exclude Patterns",
                        placeholder="*.tmp,node_modules/*,*.pyc",
                        scale=2
                    )
                
                with gr.Row():
                    min_size = gr.Number(label="Min Size (bytes)", value=0, scale=1)
                    max_size = gr.Number(label="Max Size (bytes)", value=0, scale=1)
                    event_types = gr.CheckboxGroup(
                        choices=["created", "modified", "deleted", "moved"],
                        value=["created", "modified", "deleted"],
                        label="Event Types",
                        scale=2
                    )
                
                apply_filters_btn = gr.Button("✅ Apply Filters", variant="secondary")
            
            # Alert rules section
            with gr.Accordion("🚨 Alert Rules", open=False):
                with gr.Row():
                    rule_name = gr.Textbox(label="Rule Name", placeholder="Large File Alert", scale=2)
                    rule_condition = gr.Dropdown(
                        choices=["large file", "frequent changes", "created", "modified", "deleted"],
                        label="Condition",
                        scale=1
                    )
                    rule_action = gr.Dropdown(
                        choices=["log", "highlight", "count"],
                        label="Action",
                        value="log",
                        scale=1
                    )
                
                add_rule_btn = gr.Button("➕ Add Alert Rule", variant="secondary")
                rule_status = gr.Textbox(label="Rule Status", lines=2, interactive=False)
        
        with gr.Column(scale=2):
            # Event display tabs
            with gr.Tabs():
                with gr.TabItem("📋 Live Events"):
                    event_filter = gr.Dropdown(
                        choices=["all", "created", "modified", "deleted", "moved", "error", "alert"],
                        value="all",
                        label="Filter Events"
                    )
                    events_display = gr.Textbox(
                        label="Recent Events",
                        lines=15,
                        interactive=False,
                        max_lines=20
                    )
                    refresh_events_btn = gr.Button("🔄 Refresh Events")
                
                with gr.TabItem("📊 Analytics"):
                    analytics_display = gr.Textbox(
                        label="Analytics Summary",
                        lines=15,
                        interactive=False
                    )
                    refresh_analytics_btn = gr.Button("🔄 Refresh Analytics")
                
                with gr.TabItem("📤 Export"):
                    export_display = gr.Textbox(
                        label="Export Data",
                        lines=15,
                        interactive=False
                    )
                    export_btn = gr.Button("📥 Export Data", variant="secondary")
    
    # Event handlers
    def start_monitoring_handler(directory):
        return monitor.start_monitoring(directory)
    
    def stop_monitoring_handler():
        return monitor.stop_monitoring()
    
    def apply_filters_handler(ext, excl, min_s, max_s, evt_types):
        return monitor.set_filters(ext, excl, int(min_s or 0), int(max_s or 0), evt_types)
    
    def add_rule_handler(name, condition, action):
        if not name.strip():
            return "❌ Please provide a rule name"
        return monitor.add_alert_rule(name, condition, action)
    
    def refresh_events_handler(filter_type):
        return monitor.get_formatted_events(filter_type)
    
    def refresh_analytics_handler():
        return monitor.get_analytics_summary()
    
    def export_handler():
        return monitor.export_data()
    
    # Connect event handlers
    start_btn.click(
        start_monitoring_handler,
        inputs=[directory_input],
        outputs=[status_output]
    )
    
    stop_btn.click(
        stop_monitoring_handler,
        outputs=[status_output]
    )
    
    apply_filters_btn.click(
        apply_filters_handler,
        inputs=[extensions_filter, exclude_patterns, min_size, max_size, event_types],
        outputs=[status_output]
    )
    
    add_rule_btn.click(
        add_rule_handler,
        inputs=[rule_name, rule_condition, rule_action],
        outputs=[rule_status]
    )
    
    refresh_events_btn.click(
        refresh_events_handler,
        inputs=[event_filter],
        outputs=[events_display]
    )
    
    event_filter.change(
        refresh_events_handler,
        inputs=[event_filter],
        outputs=[events_display]
    )
    
    refresh_analytics_btn.click(
        refresh_analytics_handler,
        outputs=[analytics_display]
    )
    
    export_btn.click(
        export_handler,
        outputs=[export_display]
    )
    
    # Auto-refresh events every 3 seconds when monitoring
    interface.load(
        refresh_events_handler,
        inputs=[event_filter],
        outputs=[events_display],
        every=3
    )

if __name__ == "__main__":
    interface.launch(server_port=int(os.environ.get('AGENT_PORT', 7860)))
