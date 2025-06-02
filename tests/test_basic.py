"""Tests for Gradio MCP Playground"""

import pytest
from pathlib import Path
import tempfile
import json

from gradio_mcp_playground import (
    MCPServer,
    GradioMCPServer,
    ConfigManager,
    ServerRegistry
)
from gradio_mcp_playground.utils import (
    find_free_port,
    is_port_in_use,
    validate_server_config,
    parse_tool_docstring
)


def test_mcp_server_creation():
    """Test creating an MCP server"""
    server = MCPServer("test-server", "1.0.0", "Test server")
    
    assert server.name == "test-server"
    assert server.version == "1.0.0"
    assert server.description == "Test server"
    assert server.tools == []


def test_mcp_server_tool_decorator():
    """Test the tool decorator"""
    server = MCPServer("test-server")
    
    @server.tool()
    def test_function(text: str) -> str:
        """Test function that echoes text"""
        return f"Echo: {text}"
    
    assert len(server.tools) == 1
    assert server.tools[0].name == "test_function"
    assert server.tools[0].description == "Test function that echoes text"


def test_find_free_port():
    """Test finding a free port"""
    port = find_free_port()
    assert isinstance(port, int)
    assert 1 <= port <= 65535
    assert not is_port_in_use(port)


def test_validate_server_config():
    """Test server configuration validation"""
    # Valid config
    valid_config = {
        "name": "test-server",
        "path": __file__,  # Use this test file as a valid path
        "port": 7860,
        "protocol": "stdio"
    }
    
    is_valid, errors = validate_server_config(valid_config)
    assert is_valid
    assert len(errors) == 0
    
    # Invalid config - missing required fields
    invalid_config = {
        "port": 7860
    }
    
    is_valid, errors = validate_server_config(invalid_config)
    assert not is_valid
    assert len(errors) > 0
    assert any("name" in error for error in errors)


def test_parse_tool_docstring():
    """Test parsing tool docstrings"""
    docstring = """Test function that processes data.
    
    Args:
        input_data: The data to process
        threshold: Processing threshold value
        
    Returns:
        Processed data as a string
    """
    
    result = parse_tool_docstring(docstring)
    
    assert result["description"] == "Test function that processes data."
    assert "input_data" in result["parameters"]
    assert "threshold" in result["parameters"]


def test_config_manager():
    """Test configuration manager"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override config directory
        config_manager = ConfigManager()
        config_manager.config_dir = Path(tmpdir)
        config_manager.config_path = config_manager.config_dir / "config.json"
        config_manager._ensure_config_dir()
        
        # Test default config
        default_config = config_manager._get_default_config()
        assert "default_port" in default_config
        assert "mcp_protocol" in default_config
        
        # Test saving and loading config
        test_config = {
            "default_port": 8080,
            "mcp_protocol": "sse",
            "custom_field": "test"
        }
        
        config_manager.save_config(test_config)
        loaded_config = config_manager.load_config()
        
        assert loaded_config["default_port"] == 8080
        assert loaded_config["mcp_protocol"] == "sse"
        assert loaded_config["custom_field"] == "test"
        
        # Test get/set methods
        config_manager.set("new_field", "new_value")
        assert config_manager.get("new_field") == "new_value"


def test_server_registry():
    """Test server registry"""
    registry = ServerRegistry()
    
    # Test listing templates
    templates = registry.list_templates()
    assert isinstance(templates, list)
    assert "basic" in templates
    
    # Test searching
    results = registry.search("calculator")
    assert isinstance(results, list)
    
    # Test categories
    categories = registry.list_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0
    
    # Test getting by category
    starter_servers = registry.get_by_category("starter")
    assert isinstance(starter_servers, list)


def test_template_creation():
    """Test creating a server from template"""
    registry = ServerRegistry()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        server_dir = Path(tmpdir) / "test-server"
        
        config = registry.create_from_template(
            "basic",
            "test-server",
            server_dir,
            port=8080
        )
        
        assert config["name"] == "test-server"
        assert config["template"] == "basic"
        assert server_dir.exists()
        
        # Check that files were created
        app_file = server_dir / "app.py"
        assert app_file.exists()
        
        # Check that placeholders were replaced
        with open(app_file) as f:
            content = f.read()
        
        assert "test-server" in content
        assert "8080" in content


def test_gradio_mcp_server_validation():
    """Test Gradio MCP server validation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        server_dir = Path(tmpdir)
        
        # Create a valid server file
        app_file = server_dir / "app.py"
        app_file.write_text("""
import gradio as gr

def test_fn(x):
    return x

demo = gr.Interface(fn=test_fn, inputs="text", outputs="text")
demo.launch(mcp_server=True)
""")
        
        # Validate
        results = GradioMCPServer.validate_server(server_dir)
        
        assert results["valid"]
        assert len(results["errors"]) == 0


@pytest.mark.asyncio
async def test_mcp_client_basic():
    """Test basic MCP client functionality"""
    from gradio_mcp_playground.client_manager import MCPClient
    
    client = MCPClient()
    assert not client.is_connected
    
    # Test that operations fail when not connected
    with pytest.raises(RuntimeError):
        await client.list_tools()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
