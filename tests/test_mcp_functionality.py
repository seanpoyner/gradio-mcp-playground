#!/usr/bin/env python3
"""MCP Server Functionality Testing Script

Tests the Model Context Protocol server functionality including:
- MCP tool registration and execution
- Gradio interface integration with MCP
- Server-client communication
- Protocol compliance
"""

import asyncio
import json
import tempfile
import time
import subprocess
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Add the parent directory to the path to import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from gradio_mcp_playground.server_manager import MCPServer, GradioMCPServer
from gradio_mcp_playground.client_manager import GradioMCPClient
import gradio as gr


class MCPFunctionalityTestSuite:
    """Test suite for MCP server functionality"""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.temp_dir = None
        self.test_servers = []
        self.test_ports = [7870, 7871, 7872, 7873, 7874]
        self.current_port_index = 0
    
    def get_next_port(self) -> int:
        """Get the next available test port"""
        port = self.test_ports[self.current_port_index]
        self.current_port_index = (self.current_port_index + 1) % len(self.test_ports)
        return port
    
    def assert_test(self, condition: bool, test_name: str, error_msg: str = ""):
        """Assert a test condition and track results"""
        if condition:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")
    
    def setup(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        print(f"MCP test environment created at: {self.temp_dir}")
    
    def teardown(self):
        """Clean up test environment"""
        # Stop any running test servers
        for server_process in self.test_servers:
            if server_process.poll() is None:
                server_process.terminate()
                server_process.wait()
        
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
        print("MCP test environment cleaned up")
    
    def test_basic_mcp_server_creation(self):
        """Test basic MCP server creation and tool registration"""
        print("\n=== Testing Basic MCP Server Creation ===")
        
        try:
            # Create a simple MCP server
            server = MCPServer("test-server", "1.0.0", "Test MCP Server")
            
            @server.tool("greet", "Greet someone by name")
            async def greet(name: str) -> str:
                return f"Hello, {name}!"
            
            @server.tool("add", "Add two numbers")
            async def add(a: int, b: int) -> int:
                return a + b
            
            @server.tool("echo", "Echo back the input")
            async def echo(message: str) -> str:
                return f"Echo: {message}"
            
            # Test tool registration
            self.assert_test(
                len(server.tools) == 3,
                "MCP tool registration",
                f"Expected 3 tools, got {len(server.tools)}"
            )
            
            # Test tool metadata
            tool_names = [tool.name for tool in server.tools]
            expected_tools = ["greet", "add", "echo"]
            
            self.assert_test(
                all(tool in tool_names for tool in expected_tools),
                "MCP tool names registration",
                f"Tools: {tool_names}, Expected: {expected_tools}"
            )
            
            # Test tool execution
            greet_tool = next(tool for tool in server.tools if tool.name == "greet")
            
            async def test_execution():
                return await greet_tool.handler("World")
            
            result = asyncio.run(test_execution())
            
            self.assert_test(
                result == "Hello, World!",
                "MCP tool execution",
                f"Expected 'Hello, World!', got '{result}'"
            )
            
        except Exception as e:
            self.assert_test(
                False,
                "Basic MCP server creation",
                f"Exception: {str(e)}"
            )
    
    def test_gradio_mcp_integration(self):
        """Test Gradio interface integration with MCP"""
        print("\n=== Testing Gradio-MCP Integration ===")
        
        try:
            # Create MCP server with tools
            server = MCPServer("gradio-test-server", "1.0.0")
            
            @server.tool()
            async def calculate_area(length: float, width: float) -> float:
                """Calculate the area of a rectangle"""
                return length * width
            
            @server.tool()
            async def reverse_string(text: str) -> str:
                """Reverse a string"""
                return text[::-1]
            
            # Convert to Gradio functions
            gradio_functions = server.to_gradio_functions()
            
            self.assert_test(
                len(gradio_functions) == 2,
                "Gradio function conversion",
                f"Expected 2 functions, got {len(gradio_functions)}"
            )
            
            # Test function metadata
            func_names = [func["name"] for func in gradio_functions]
            self.assert_test(
                "calculate_area" in func_names and "reverse_string" in func_names,
                "Gradio function names",
                f"Functions: {func_names}"
            )
            
            # Test Gradio interface creation
            if gradio_functions:
                func = gradio_functions[0]
                
                # Test that the function has expected properties
                required_props = ["name", "description", "fn", "inputs", "outputs"]
                has_all_props = all(prop in func for prop in required_props)
                
                self.assert_test(
                    has_all_props,
                    "Gradio function properties",
                    f"Missing properties in function: {func.keys()}"
                )
                
                # Test that inputs are proper Gradio components
                inputs = func["inputs"]
                self.assert_test(
                    isinstance(inputs, list) and len(inputs) > 0,
                    "Gradio input components",
                    f"Invalid inputs: {type(inputs)}"
                )
        
        except Exception as e:
            self.assert_test(
                False,
                "Gradio-MCP integration",
                f"Exception: {str(e)}"
            )
    
    def test_mcp_server_launch(self):
        """Test MCP server launching and HTTP endpoints"""
        print("\n=== Testing MCP Server Launch ===")
        
        try:
            # Create a test server file
            test_server_path = Path(self.temp_dir) / "test_mcp_server.py"
            server_code = '''
import gradio as gr
import asyncio
from gradio_mcp_playground.server_manager import MCPServer

# Create MCP server
mcp_server = MCPServer("test-http-server", "1.0.0", "Test HTTP MCP Server")

@mcp_server.tool()
async def test_function(input_text: str) -> str:
    """Test function for HTTP server"""
    return f"Processed: {input_text}"

# Create Gradio interface
functions = mcp_server.to_gradio_functions()
if functions:
    demo = gr.Interface(
        fn=functions[0]["fn"],
        inputs=functions[0]["inputs"],
        outputs=functions[0]["outputs"],
        title="Test MCP Server",
        description="Test MCP server for functionality testing"
    )
else:
    demo = gr.Interface(
        fn=lambda x: f"Echo: {x}",
        inputs="text",
        outputs="text",
        title="Fallback Server"
    )

if __name__ == "__main__":
    demo.launch(server_port=7875, share=False, quiet=True)
'''
            
            test_server_path.write_text(server_code)
            
            # Start the server in a subprocess
            server_process = subprocess.Popen([
                sys.executable, str(test_server_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.test_servers.append(server_process)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test server is running
            try:
                response = requests.get("http://localhost:7875", timeout=10)
                self.assert_test(
                    response.status_code == 200,
                    "MCP server HTTP endpoint",
                    f"HTTP status: {response.status_code}"
                )
            except requests.RequestException as e:
                self.assert_test(
                    False,
                    "MCP server HTTP endpoint",
                    f"Request failed: {str(e)}"
                )
            
            # Stop the server
            server_process.terminate()
            server_process.wait()
            
        except Exception as e:
            self.assert_test(
                False,
                "MCP server launch",
                f"Exception: {str(e)}"
            )
    
    def test_mcp_client_functionality(self):
        """Test MCP client connection and tool calling"""
        print("\n=== Testing MCP Client Functionality ===")
        
        try:
            # Test client creation
            client = GradioMCPClient()
            
            self.assert_test(
                client is not None,
                "MCP client creation",
                "Failed to create MCP client"
            )
            
            # Test connection methods exist
            required_methods = ["connect", "disconnect", "list_tools", "call_tool"]
            has_methods = all(hasattr(client, method) for method in required_methods)
            
            self.assert_test(
                has_methods,
                "MCP client methods",
                f"Missing methods: {[m for m in required_methods if not hasattr(client, m)]}"
            )
            
            # Test static test_connection method
            if hasattr(GradioMCPClient, "test_connection"):
                result = GradioMCPClient.test_connection("http://invalid-url", "auto")
                
                self.assert_test(
                    isinstance(result, dict) and "success" in result,
                    "MCP client test connection",
                    f"Invalid test connection result: {result}"
                )
            
        except Exception as e:
            self.assert_test(
                False,
                "MCP client functionality",
                f"Exception: {str(e)}"
            )
    
    def test_mcp_tool_schemas(self):
        """Test MCP tool schema generation and validation"""
        print("\n=== Testing MCP Tool Schemas ===")
        
        try:
            server = MCPServer("schema-test", "1.0.0")
            
            @server.tool()
            async def complex_function(
                name: str,
                age: int,
                height: float,
                is_student: bool
            ) -> str:
                """A complex function with multiple parameter types"""
                return f"{name} is {age} years old, {height}m tall, student: {is_student}"
            
            # Test schema generation
            tool = server.tools[0]
            schema = tool.input_schema
            
            # Test schema structure
            self.assert_test(
                "type" in schema and schema["type"] == "object",
                "Schema type",
                f"Invalid schema type: {schema.get('type')}"
            )
            
            self.assert_test(
                "properties" in schema,
                "Schema properties",
                "Schema missing properties"
            )
            
            # Test parameter types
            properties = schema["properties"]
            expected_types = {
                "name": "string",
                "age": "integer", 
                "height": "number",
                "is_student": "boolean"
            }
            
            for param, expected_type in expected_types.items():
                actual_type = properties.get(param, {}).get("type")
                self.assert_test(
                    actual_type == expected_type,
                    f"Parameter {param} type",
                    f"Expected {expected_type}, got {actual_type}"
                )
            
            # Test required parameters
            required = schema.get("required", [])
            self.assert_test(
                len(required) == 4,
                "Required parameters",
                f"Expected 4 required params, got {len(required)}"
            )
            
        except Exception as e:
            self.assert_test(
                False,
                "MCP tool schemas",
                f"Exception: {str(e)}"
            )
    
    def test_mcp_protocol_compliance(self):
        """Test MCP protocol compliance"""
        print("\n=== Testing MCP Protocol Compliance ===")
        
        try:
            server = MCPServer("protocol-test", "1.0.0", "Protocol compliance test")
            
            # Test server properties
            self.assert_test(
                hasattr(server, "name") and server.name == "protocol-test",
                "Server name property",
                f"Server name: {getattr(server, 'name', 'missing')}"
            )
            
            self.assert_test(
                hasattr(server, "version") and server.version == "1.0.0",
                "Server version property",
                f"Server version: {getattr(server, 'version', 'missing')}"
            )
            
            self.assert_test(
                hasattr(server, "description"),
                "Server description property",
                "Server missing description"
            )
            
            # Test tool registration
            @server.tool()
            async def test_tool(param: str) -> str:
                return param
            
            # Test that tool is properly registered
            self.assert_test(
                len(server.tools) == 1,
                "Tool registration in protocol",
                f"Expected 1 tool, got {len(server.tools)}"
            )
            
            # Test tool structure
            tool = server.tools[0]
            required_tool_attrs = ["name", "description", "input_schema", "handler"]
            has_attrs = all(hasattr(tool, attr) for attr in required_tool_attrs)
            
            self.assert_test(
                has_attrs,
                "Tool structure compliance",
                f"Missing attributes: {[attr for attr in required_tool_attrs if not hasattr(tool, attr)]}"
            )
            
        except Exception as e:
            self.assert_test(
                False,
                "MCP protocol compliance",
                f"Exception: {str(e)}"
            )
    
    def test_error_handling(self):
        """Test error handling in MCP operations"""
        print("\n=== Testing MCP Error Handling ===")
        
        try:
            server = MCPServer("error-test", "1.0.0")
            
            @server.tool()
            async def failing_function(input_val: str) -> str:
                """A function that can fail"""
                if input_val == "fail":
                    raise ValueError("Intentional test failure")
                return f"Success: {input_val}"
            
            # Test successful execution
            tool = server.tools[0]
            result = asyncio.run(tool.handler("success"))
            
            self.assert_test(
                result == "Success: success",
                "Successful tool execution",
                f"Unexpected result: {result}"
            )
            
            # Test error handling
            try:
                asyncio.run(tool.handler("fail"))
                self.assert_test(
                    False,
                    "Tool error handling",
                    "Expected exception was not raised"
                )
            except ValueError as e:
                self.assert_test(
                    "Intentional test failure" in str(e),
                    "Tool error handling",
                    f"Unexpected error message: {str(e)}"
                )
            
        except Exception as e:
            self.assert_test(
                False,
                "MCP error handling",
                f"Exception: {str(e)}"
            )
    
    def test_gradio_server_manager(self):
        """Test GradioMCPServer functionality"""
        print("\n=== Testing Gradio Server Manager ===")
        
        try:
            # Create a simple app file
            app_path = Path(self.temp_dir) / "manager_test_app.py"
            app_code = '''
import gradio as gr

def greet(name):
    return f"Hello, {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "__main__":
    demo.launch()
'''
            app_path.write_text(app_code)
            
            # Test GradioMCPServer creation
            server_manager = GradioMCPServer(app_path)
            
            self.assert_test(
                server_manager.app_path == app_path,
                "Server manager app path",
                f"Expected {app_path}, got {server_manager.app_path}"
            )
            
            # Test configuration loading
            config = server_manager._load_config()
            
            self.assert_test(
                isinstance(config, dict),
                "Server manager config loading",
                f"Config type: {type(config)}"
            )
            
            # Test validation
            validation_result = GradioMCPServer.validate_server(Path(self.temp_dir))
            
            self.assert_test(
                isinstance(validation_result, dict) and "valid" in validation_result,
                "Server validation",
                f"Invalid validation result: {validation_result}"
            )
            
        except Exception as e:
            self.assert_test(
                False,
                "Gradio server manager",
                f"Exception: {str(e)}"
            )
    
    def test_multiple_tools_server(self):
        """Test server with multiple tools and complex interactions"""
        print("\n=== Testing Multiple Tools Server ===")
        
        try:
            server = MCPServer("multi-tool-server", "1.0.0")
            
            # Add multiple tools
            @server.tool()
            async def string_operations(text: str, operation: str) -> str:
                """Perform string operations"""
                if operation == "upper":
                    return text.upper()
                elif operation == "lower":
                    return text.lower()
                elif operation == "reverse":
                    return text[::-1]
                else:
                    return text
            
            @server.tool()
            async def math_operations(a: float, b: float, operation: str) -> float:
                """Perform math operations"""
                if operation == "add":
                    return a + b
                elif operation == "subtract":
                    return a - b
                elif operation == "multiply":
                    return a * b
                elif operation == "divide":
                    return a / b if b != 0 else float('inf')
                else:
                    return 0.0
            
            @server.tool()
            async def data_processor(data: str, format_type: str) -> str:
                """Process data in different formats"""
                try:
                    if format_type == "json":
                        parsed = json.loads(data)
                        return json.dumps(parsed, indent=2)
                    elif format_type == "upper":
                        return data.upper()
                    else:
                        return data
                except:
                    return f"Error processing {format_type}: {data}"
            
            # Test all tools are registered
            self.assert_test(
                len(server.tools) == 3,
                "Multiple tools registration",
                f"Expected 3 tools, got {len(server.tools)}"
            )
            
            # Test tool execution
            string_tool = next(tool for tool in server.tools if tool.name == "string_operations")
            
            async def test_string_execution():
                return await string_tool.handler("hello", "upper")
            
            result = asyncio.run(test_string_execution())
            
            self.assert_test(
                result == "HELLO",
                "String operations tool",
                f"Expected 'HELLO', got '{result}'"
            )
            
            math_tool = next(tool for tool in server.tools if tool.name == "math_operations")
            
            async def test_math_execution():
                return await math_tool.handler(10.0, 5.0, "add")
            
            result = asyncio.run(test_math_execution())
            
            self.assert_test(
                result == 15.0,
                "Math operations tool",
                f"Expected 15.0, got {result}"
            )
            
            # Test Gradio conversion for multiple tools
            gradio_functions = server.to_gradio_functions()
            
            self.assert_test(
                len(gradio_functions) == 3,
                "Multiple tools Gradio conversion",
                f"Expected 3 Gradio functions, got {len(gradio_functions)}"
            )
            
        except Exception as e:
            self.assert_test(
                False,
                "Multiple tools server",
                f"Exception: {str(e)}"
            )
    
    def run_all_tests(self):
        """Run all MCP functionality tests"""
        print("🚀 Starting MCP Functionality Test Suite")
        print("=" * 50)
        
        try:
            self.setup()
            
            # Run all test suites
            self.test_basic_mcp_server_creation()
            self.test_gradio_mcp_integration()
            self.test_mcp_server_launch()
            self.test_mcp_client_functionality()
            self.test_mcp_tool_schemas()
            self.test_mcp_protocol_compliance()
            self.test_error_handling()
            self.test_gradio_server_manager()
            self.test_multiple_tools_server()
            
        finally:
            self.teardown()
        
        # Print results
        print("\n" + "=" * 50)
        print("🎯 MCP TEST RESULTS")
        print("=" * 50)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results["errors"]:
            print("\n💥 Errors:")
            for error in self.test_results["errors"]:
                print(f"  - {error}")
        
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        return self.test_results["failed"] == 0


def run_mcp_functionality_tests():
    """Main function to run all MCP functionality tests"""
    test_suite = MCPFunctionalityTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All MCP functionality tests passed!")
        return 0
    else:
        print("\n💔 Some MCP tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_mcp_functionality_tests()
    sys.exit(exit_code)