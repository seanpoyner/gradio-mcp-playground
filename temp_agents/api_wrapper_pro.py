"""
🔌 API Wrapper Pro Agent

AGENT_INFO = {
    "name": "🔌 API Wrapper Pro",
    "description": "Advanced REST API client with authentication, rate limiting, and intelligent response transformation",
    "category": "Integration",
    "difficulty": "Advanced",
    "features": [
        "Full REST API support (GET, POST, PUT, DELETE, PATCH)",
        "Multiple authentication methods (API Key, Bearer Token, Basic Auth)",
        "Built-in rate limiting and retry logic",
        "Response transformation and formatting",
        "Request history and analytics",
        "Batch API operations and testing"
    ],
    "version": "1.0.0",
    "author": "Agent System"
}
"""

import gradio as gr
import requests
import json
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
import csv
import io
from urllib.parse import urlparse, parse_qs
import os

class AdvancedAPIWrapper:
    def __init__(self):
        self.request_history: List[Dict] = []
        self.rate_limits = {
            "requests_per_minute": 60,
            "last_minute_requests": [],
            "enabled": False
        }
        self.auth_config = {
            "type": "none",
            "credentials": {}
        }
        self.default_headers = {
            "User-Agent": "API-Wrapper-Pro/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.response_transformers = {
            "json_pretty": self._transform_json_pretty,
            "extract_fields": self._transform_extract_fields,
            "csv_format": self._transform_csv_format,
            "status_only": self._transform_status_only,
            "headers_only": self._transform_headers_only,
            "custom_jq": self._transform_custom_jq
        }
        
    def configure_auth(self, auth_type: str, username: str = "", password: str = "", 
                      api_key: str = "", token: str = "", header_name: str = "Authorization") -> str:
        """Configure authentication settings"""
        try:
            self.auth_config["type"] = auth_type.lower()
            
            if auth_type == "basic":
                if not username or not password:
                    return "❌ Basic auth requires username and password"
                self.auth_config["credentials"] = {"username": username, "password": password}
                return "✅ Basic authentication configured"
                
            elif auth_type == "bearer":
                if not token:
                    return "❌ Bearer auth requires token"
                self.auth_config["credentials"] = {"token": token}
                return "✅ Bearer token authentication configured"
                
            elif auth_type == "api_key":
                if not api_key or not header_name:
                    return "❌ API key auth requires key and header name"
                self.auth_config["credentials"] = {"api_key": api_key, "header_name": header_name}
                return "✅ API key authentication configured"
                
            elif auth_type == "none":
                self.auth_config["credentials"] = {}
                return "✅ Authentication disabled"
                
            else:
                return "❌ Unsupported authentication type"
                
        except Exception as e:
            return f"❌ Error configuring auth: {str(e)}"
    
    def configure_rate_limiting(self, enabled: bool, requests_per_minute: int = 60) -> str:
        """Configure rate limiting"""
        try:
            self.rate_limits["enabled"] = enabled
            self.rate_limits["requests_per_minute"] = max(1, requests_per_minute)
            self.rate_limits["last_minute_requests"] = []
            
            if enabled:
                return f"✅ Rate limiting enabled: {requests_per_minute} requests/minute"
            else:
                return "✅ Rate limiting disabled"
                
        except Exception as e:
            return f"❌ Error configuring rate limiting: {str(e)}"
    
    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        if not self.rate_limits["enabled"]:
            return True
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.rate_limits["last_minute_requests"] = [
            req_time for req_time in self.rate_limits["last_minute_requests"]
            if req_time > minute_ago
        ]
        
        # Check if under limit
        current_count = len(self.rate_limits["last_minute_requests"])
        if current_count >= self.rate_limits["requests_per_minute"]:
            return False
        
        # Add current request
        self.rate_limits["last_minute_requests"].append(now)
        return True
    
    def _prepare_headers(self, custom_headers: str = "") -> Dict[str, str]:
        """Prepare request headers including authentication"""
        headers = self.default_headers.copy()
        
        # Add custom headers
        if custom_headers.strip():
            try:
                for line in custom_headers.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers[key.strip()] = value.strip()
            except Exception:
                pass
        
        # Add authentication headers
        auth_type = self.auth_config["type"]
        creds = self.auth_config["credentials"]
        
        if auth_type == "basic" and creds:
            auth_string = f"{creds['username']}:{creds['password']}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            headers["Authorization"] = f"Basic {auth_b64}"
            
        elif auth_type == "bearer" and creds:
            headers["Authorization"] = f"Bearer {creds['token']}"
            
        elif auth_type == "api_key" and creds:
            headers[creds["header_name"]] = creds["api_key"]
        
        return headers
    
    def make_advanced_request(self, url: str, method: str, headers_text: str = "", 
                            body_text: str = "", transform_type: str = "json_pretty",
                            timeout: int = 30, follow_redirects: bool = True,
                            custom_fields: str = "") -> str:
        """Make advanced API request with comprehensive features"""
        try:
            # Validate inputs
            if not url.strip():
                return "❌ URL is required"
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Check rate limiting
            if not self._check_rate_limit():
                wait_time = 60 - (datetime.now() - min(self.rate_limits["last_minute_requests"])).seconds
                return f"🚫 **Rate limit exceeded**\n\nWait {wait_time} seconds before next request\nCurrent limit: {self.rate_limits['requests_per_minute']} requests/minute"
            
            # Prepare request
            method = method.upper()
            headers = self._prepare_headers(headers_text)
            
            # Parse request body
            data = None
            json_data = None
            
            if body_text.strip() and method in ['POST', 'PUT', 'PATCH']:
                try:
                    # Try to parse as JSON first
                    json_data = json.loads(body_text)
                except json.JSONDecodeError:
                    # Treat as raw data
                    data = body_text
                    headers["Content-Type"] = "text/plain"
            
            # Record request start
            start_time = time.time()
            request_timestamp = datetime.now()
            
            # Make request
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=timeout,
                allow_redirects=follow_redirects
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Parse response data
            try:
                response_data = response.json()
            except (json.JSONDecodeError, ValueError):
                response_data = response.text
            
            # Record request in history
            request_record = {
                "timestamp": request_timestamp.isoformat(),
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "response_time": response_time,
                "response_size": len(response.content),
                "success": response.status_code < 400
            }
            self.request_history.append(request_record)
            
            # Keep only last 100 requests
            if len(self.request_history) > 100:
                self.request_history = self.request_history[-100:]
            
            # Transform response
            transformer = self.response_transformers.get(transform_type, self._transform_json_pretty)
            transformed_response = transformer(response_data, response, custom_fields)
            
            # Format final response with metadata
            status_emoji = "✅" if response.status_code < 400 else "❌"
            
            result = f"{status_emoji} **{method} {url}**\n"
            result += f"**Status:** {response.status_code} {response.reason}\n"
            result += f"**Time:** {response_time:.3f}s\n"
            result += f"**Size:** {len(response.content):,} bytes\n\n"
            result += "**Response:**\n"
            result += transformed_response
            
            return result
            
        except requests.exceptions.Timeout:
            return "⏰ **Request Timeout**\n\nThe request took too long to complete. Try increasing the timeout or check the API availability."
            
        except requests.exceptions.ConnectionError:
            return "🌐 **Connection Error**\n\nCould not connect to the API. Check your internet connection and the API URL."
            
        except requests.exceptions.RequestException as e:
            return f"❌ **Request Error**\n\n{str(e)}"
            
        except Exception as e:
            return f"❌ **Unexpected Error**\n\n{str(e)}"
    
    def _transform_json_pretty(self, data: Any, response: requests.Response, custom_fields: str = "") -> str:
        """Pretty print JSON data"""
        try:
            if isinstance(data, (dict, list)):
                return json.dumps(data, indent=2, ensure_ascii=False)
            else:
                return str(data)
        except Exception:
            return str(data)
    
    def _transform_extract_fields(self, data: Any, response: requests.Response, custom_fields: str = "") -> str:
        """Extract specific fields from JSON response"""
        if not custom_fields or not isinstance(data, dict):
            return self._transform_json_pretty(data, response)
        
        try:
            fields = [field.strip() for field in custom_fields.split(',')]
            extracted = {}
            
            for field in fields:
                if field in data:
                    extracted[field] = data[field]
                else:
                    # Try nested field access with dot notation
                    if '.' in field:
                        parts = field.split('.')
                        current = data
                        try:
                            for part in parts:
                                current = current[part]
                            extracted[field] = current
                        except (KeyError, TypeError):
                            extracted[field] = None
                    else:
                        extracted[field] = None
            
            return json.dumps(extracted, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"❌ Field extraction error: {str(e)}"
    
    def _transform_csv_format(self, data: Any, response: requests.Response, custom_fields: str = "") -> str:
        """Convert JSON array to CSV format"""
        if not isinstance(data, list):
            return "❌ CSV format requires array data"
        
        try:
            if not data:
                return "Empty array"
            
            # Get headers from first item
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
                
                # Filter headers if custom_fields specified
                if custom_fields:
                    requested_fields = [field.strip() for field in custom_fields.split(',')]
                    headers = [h for h in headers if h in requested_fields]
                
                # Create CSV
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                
                for row in data:
                    filtered_row = {k: v for k, v in row.items() if k in headers}
                    writer.writerow(filtered_row)
                
                return output.getvalue()
            else:
                # Simple array to CSV
                return '\n'.join([str(item) for item in data])
                
        except Exception as e:
            return f"❌ CSV conversion error: {str(e)}"
    
    def _transform_status_only(self, data: Any, response: requests.Response, custom_fields: str = "") -> str:
        """Show only response status information"""
        result = "**Response Status:**\n\n"
        result += f"• **Status Code:** {response.status_code}\n"
        result += f"• **Status Text:** {response.reason}\n"
        result += f"• **Content Length:** {len(response.content)} bytes\n"
        result += f"• **Content Type:** {response.headers.get('content-type', 'unknown')}\n"
        
        # Add any redirects
        if response.history:
            result += f"• **Redirects:** {len(response.history)}\n"
            for i, redirect in enumerate(response.history):
                result += f"  {i+1}. {redirect.status_code} → {redirect.url}\n"
        
        return result
    
    def _transform_headers_only(self, data: Any, response: requests.Response, custom_fields: str = "") -> str:
        """Show only response headers"""
        result = "**Response Headers:**\n\n"
        for key, value in response.headers.items():
            result += f"• **{key}:** {value}\n"
        return result
    
    def _transform_custom_jq(self, data: Any, response: requests.Response, custom_fields: str = "") -> str:
        """Apply custom JQ-like transformation (simplified)"""
        if not custom_fields:
            return self._transform_json_pretty(data, response)
        
        try:
            # Simple field extraction syntax: .field1.field2
            if custom_fields.startswith('.') and isinstance(data, dict):
                parts = custom_fields[1:].split('.')
                result = data
                for part in parts:
                    if isinstance(result, dict) and part in result:
                        result = result[part]
                    else:
                        return f"❌ Field '{part}' not found"
                return json.dumps(result, indent=2, ensure_ascii=False)
            
            # Array filtering: .[0] or .[]
            elif '[' in custom_fields and isinstance(data, list):
                if custom_fields == '.[]':
                    return '\n'.join([json.dumps(item, indent=2) for item in data])
                elif custom_fields.startswith('.[') and custom_fields.endswith(']'):
                    try:
                        index = int(custom_fields[2:-1])
                        if 0 <= index < len(data):
                            return json.dumps(data[index], indent=2, ensure_ascii=False)
                        else:
                            return f"❌ Index {index} out of range"
                    except ValueError:
                        return "❌ Invalid array index"
            
            return f"❌ Unsupported transformation: {custom_fields}"
            
        except Exception as e:
            return f"❌ Transformation error: {str(e)}"
    
    def get_request_history(self, limit: int = 20) -> str:
        """Get formatted request history"""
        if not self.request_history:
            return "📭 No requests made yet"
        
        history = f"📋 **Request History** (Last {min(limit, len(self.request_history))})\n\n"
        
        for req in reversed(self.request_history[-limit:]):
            timestamp = datetime.fromisoformat(req["timestamp"]).strftime("%H:%M:%S")
            status_emoji = "✅" if req["success"] else "❌"
            
            history += f"{status_emoji} `[{timestamp}]` **{req['method']}** {req['url']}\n"
            history += f"   ↳ {req['status_code']} • {req['response_time']:.3f}s • {req['response_size']:,} bytes\n\n"
        
        return history
    
    def get_statistics(self) -> str:
        """Get request statistics"""
        if not self.request_history:
            return "📊 No statistics available yet"
        
        total_requests = len(self.request_history)
        successful_requests = sum(1 for req in self.request_history if req["success"])
        failed_requests = total_requests - successful_requests
        
        avg_response_time = sum(req["response_time"] for req in self.request_history) / total_requests
        total_data = sum(req["response_size"] for req in self.request_history)
        
        # Method distribution
        methods = {}
        for req in self.request_history:
            methods[req["method"]] = methods.get(req["method"], 0) + 1
        
        # Status code distribution
        status_codes = {}
        for req in self.request_history:
            code = req["status_code"] 
            status_codes[code] = status_codes.get(code, 0) + 1
        
        stats = f"📊 **API Usage Statistics**\n\n"
        stats += f"**📈 Overview:**\n"
        stats += f"• Total Requests: {total_requests}\n"
        stats += f"• Success Rate: {(successful_requests/total_requests*100):.1f}%\n"
        stats += f"• Average Response Time: {avg_response_time:.3f}s\n"
        stats += f"• Total Data Received: {total_data:,} bytes\n\n"
        
        stats += f"**🔧 Method Distribution:**\n"
        for method, count in sorted(methods.items()):
            percentage = (count / total_requests) * 100
            stats += f"• {method}: {count} ({percentage:.1f}%)\n"
        
        stats += f"\n**📊 Status Codes:**\n"
        for code, count in sorted(status_codes.items()):
            percentage = (count / total_requests) * 100
            stats += f"• {code}: {count} ({percentage:.1f}%)\n"
        
        # Rate limiting info
        if self.rate_limits["enabled"]:
            current_minute_requests = len([
                req for req in self.rate_limits["last_minute_requests"]
                if req > datetime.now() - timedelta(minutes=1)
            ])
            stats += f"\n**⚡ Rate Limiting:**\n"
            stats += f"• Current Minute: {current_minute_requests}/{self.rate_limits['requests_per_minute']}\n"
            stats += f"• Remaining: {self.rate_limits['requests_per_minute'] - current_minute_requests}\n"
        
        return stats

# Create advanced API wrapper instance
api_wrapper = AdvancedAPIWrapper()

# Enhanced Gradio interface
with gr.Blocks(title="🔌 API Wrapper Pro", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # 🔌 API Wrapper Pro Agent
    **Advanced REST API client with authentication, rate limiting, and response transformation**
    
    Features: Multiple auth methods, rate limiting, response transformers, request history
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Main request section
            with gr.Group():
                gr.Markdown("### 🚀 Make Request")
                
                with gr.Row():
                    url_input = gr.Textbox(
                        label="API URL",
                        placeholder="https://api.example.com/endpoint",
                        value="https://jsonplaceholder.typicode.com/posts/1",
                        scale=3
                    )
                    method_selector = gr.Dropdown(
                        choices=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
                        label="Method",
                        value="GET",
                        scale=1
                    )
                    send_btn = gr.Button("📤 Send Request", variant="primary", scale=1)
                
                with gr.Row():
                    headers_input = gr.Textbox(
                        label="Custom Headers (one per line: Key: Value)",
                        placeholder="X-API-Key: your-key\nContent-Type: application/json",
                        lines=3,
                        scale=1
                    )
                    body_input = gr.Textbox(
                        label="Request Body (JSON or text)",
                        placeholder='{"key": "value"}',
                        lines=3,
                        scale=1
                    )
                
                with gr.Row():
                    transform_selector = gr.Dropdown(
                        choices=["json_pretty", "extract_fields", "csv_format", "status_only", "headers_only", "custom_jq"],
                        label="Response Transform",
                        value="json_pretty",
                        scale=2
                    )
                    custom_transform = gr.Textbox(
                        label="Custom Fields/JQ Query",
                        placeholder="id,name,email or .data.users[0]",
                        scale=2
                    )
                    timeout_input = gr.Number(
                        label="Timeout (s)",
                        value=30,
                        minimum=1,
                        maximum=300,
                        scale=1
                    )
        
        with gr.Column(scale=1):
            # Configuration section
            with gr.Accordion("🔐 Authentication", open=False):
                auth_type = gr.Dropdown(
                    choices=["none", "basic", "bearer", "api_key"],
                    label="Auth Type",
                    value="none"
                )
                
                with gr.Group():
                    username_input = gr.Textbox(label="Username", visible=False)
                    password_input = gr.Textbox(label="Password", type="password", visible=False)
                    token_input = gr.Textbox(label="Token", type="password", visible=False)
                    api_key_input = gr.Textbox(label="API Key", type="password", visible=False)
                    header_name_input = gr.Textbox(label="Header Name", value="X-API-Key", visible=False)
                
                configure_auth_btn = gr.Button("🔧 Configure Auth", variant="secondary")
                auth_status = gr.Textbox(label="Auth Status", lines=2, interactive=False)
            
            with gr.Accordion("⚡ Rate Limiting", open=False):
                rate_limit_enabled = gr.Checkbox(label="Enable Rate Limiting", value=False)
                requests_per_minute = gr.Number(
                    label="Requests per Minute",
                    value=60,
                    minimum=1,
                    maximum=1000
                )
                configure_rate_btn = gr.Button("⚙️ Configure Rate Limit", variant="secondary")
                rate_status = gr.Textbox(label="Rate Limit Status", lines=2, interactive=False)
    
    # Response and analysis section
    with gr.Row():
        response_output = gr.Textbox(
            label="API Response",
            lines=15,
            max_lines=25,
            interactive=False
        )
    
    # History and statistics tabs
    with gr.Tabs():
        with gr.TabItem("📋 Request History"):
            history_limit = gr.Slider(
                label="History Limit",
                minimum=5,
                maximum=100,
                value=20,
                step=5
            )
            history_output = gr.Textbox(
                label="Recent Requests",
                lines=10,
                interactive=False
            )
            refresh_history_btn = gr.Button("🔄 Refresh History")
        
        with gr.TabItem("📊 Statistics"):
            stats_output = gr.Textbox(
                label="Usage Statistics",
                lines=10,
                interactive=False
            )
            refresh_stats_btn = gr.Button("🔄 Refresh Stats")
    
    # Event handlers
    def toggle_auth_fields(auth_type):
        """Show/hide auth fields based on type"""
        show_basic = auth_type == "basic"
        show_bearer = auth_type == "bearer"
        show_api_key = auth_type == "api_key"
        
        return (
            gr.update(visible=show_basic),  # username
            gr.update(visible=show_basic),  # password
            gr.update(visible=show_bearer), # token
            gr.update(visible=show_api_key), # api_key
            gr.update(visible=show_api_key)  # header_name
        )
    
    def configure_auth_handler(auth_type, username, password, token, api_key, header_name):
        """Configure authentication"""
        return api_wrapper.configure_auth(auth_type, username, password, api_key, token, header_name)
    
    def configure_rate_handler(enabled, rpm):
        """Configure rate limiting"""
        return api_wrapper.configure_rate_limiting(enabled, int(rpm))
    
    def send_request_handler(url, method, headers, body, transform, custom, timeout):
        """Send API request"""
        return api_wrapper.make_advanced_request(
            url, method, headers, body, transform, int(timeout), True, custom
        )
    
    def refresh_history_handler(limit):
        """Refresh request history"""
        return api_wrapper.get_request_history(int(limit))
    
    def refresh_stats_handler():
        """Refresh statistics"""
        return api_wrapper.get_statistics()
    
    # Connect event handlers
    auth_type.change(
        toggle_auth_fields,
        inputs=[auth_type],
        outputs=[username_input, password_input, token_input, api_key_input, header_name_input]
    )
    
    configure_auth_btn.click(
        configure_auth_handler,
        inputs=[auth_type, username_input, password_input, token_input, api_key_input, header_name_input],
        outputs=[auth_status]
    )
    
    configure_rate_btn.click(
        configure_rate_handler,
        inputs=[rate_limit_enabled, requests_per_minute],
        outputs=[rate_status]
    )
    
    send_btn.click(
        send_request_handler,
        inputs=[url_input, method_selector, headers_input, body_input, 
               transform_selector, custom_transform, timeout_input],
        outputs=[response_output]
    )
    
    refresh_history_btn.click(
        refresh_history_handler,
        inputs=[history_limit],
        outputs=[history_output]
    )
    
    refresh_stats_btn.click(
        refresh_stats_handler,
        outputs=[stats_output]
    )
    
    # Auto-refresh history when new requests are made
    send_btn.click(
        refresh_history_handler,
        inputs=[history_limit],
        outputs=[history_output]
    )
    
    # Initialize displays
    interface.load(
        refresh_history_handler,
        inputs=[history_limit],
        outputs=[history_output]
    )

if __name__ == "__main__":
    interface.launch(server_port=int(os.environ.get('AGENT_PORT', 7860)))
