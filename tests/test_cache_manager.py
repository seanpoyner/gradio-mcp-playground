"""Tests for the cache manager"""

import json
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from gradio_mcp_playground.cache_manager import CacheManager


class TestCacheManager:
    """Test cases for CacheManager"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
            
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager instance with temp directory"""
        return CacheManager(cache_dir=temp_cache_dir)
        
    def test_cache_initialization(self, cache_manager, temp_cache_dir):
        """Test cache manager initialization"""
        assert cache_manager.cache_dir == temp_cache_dir
        assert cache_manager.mcp_cache_dir.exists()
        assert cache_manager.config_cache_dir.exists()
        assert cache_manager.model_cache_dir.exists()
        assert cache_manager.metadata_file.exists()
        
    def test_cache_mcp_server(self, cache_manager):
        """Test caching MCP server data"""
        server_id = "test-server"
        server_data = {
            "command": "npx",
            "args": ["-y", "@test/server"],
            "env": {"TEST_VAR": "value"}
        }
        tools = ["tool1", "tool2", "tool3"]
        
        # Cache the server
        success = cache_manager.cache_mcp_server(server_id, server_data, tools)
        assert success
        
        # Verify metadata
        assert f"mcp_{server_id}" in cache_manager.metadata
        
        # Retrieve cached data
        cached = cache_manager.get_cached_mcp_server(server_id)
        assert cached is not None
        assert cached['server_id'] == server_id
        assert cached['server_data'] == server_data
        assert cached['tools'] == tools
        
    def test_cache_expiration(self, cache_manager):
        """Test cache expiration logic"""
        server_id = "expire-test"
        
        # Cache with old timestamp
        cache_manager.cache_mcp_server(server_id, {"test": "data"}, [])
        
        # Manually set old timestamp
        old_time = datetime.now() - timedelta(hours=25)
        cache_manager.metadata[f"mcp_{server_id}"]["timestamp"] = old_time.isoformat()
        cache_manager._save_metadata()
        
        # Should return None due to expiration
        cached = cache_manager.get_cached_mcp_server(server_id, max_age_hours=24)
        assert cached is None
        
    def test_cache_config(self, cache_manager):
        """Test configuration caching"""
        config_name = "test-config"
        config_data = {
            "setting1": "value1",
            "setting2": {"nested": "value2"}
        }
        
        # Cache config
        success = cache_manager.cache_config(config_name, config_data)
        assert success
        
        # Retrieve cached config
        cached = cache_manager.get_cached_config(config_name)
        assert cached == config_data
        
    def test_cache_invalidation(self, cache_manager):
        """Test cache invalidation"""
        # Add some test data
        cache_manager.cache_mcp_server("server1", {"test": 1}, ["tool1"])
        cache_manager.cache_mcp_server("server2", {"test": 2}, ["tool2"])
        cache_manager.cache_config("config1", {"data": 1})
        
        # Test specific invalidation
        cache_manager.invalidate_cache(cache_type="mcp", cache_id="server1")
        assert f"mcp_server1" not in cache_manager.metadata
        assert f"mcp_server2" in cache_manager.metadata
        
        # Test type invalidation
        cache_manager.invalidate_cache(cache_type="mcp")
        assert f"mcp_server2" not in cache_manager.metadata
        assert f"config_config1" in cache_manager.metadata
        
        # Test full invalidation
        cache_manager.invalidate_cache()
        assert len(cache_manager.metadata) == 0
        
    def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        # Add test data
        cache_manager.cache_mcp_server("server1", {"test": 1}, ["tool1"])
        cache_manager.cache_config("config1", {"data": 1})
        
        stats = cache_manager.get_cache_stats()
        
        assert stats['total_entries'] == 2
        assert stats['mcp_servers'] == 1
        assert stats['configs'] == 1
        assert stats['models'] == 0
        assert 'cache_size_mb' in stats
        assert stats['oldest_entry'] is not None
        assert stats['newest_entry'] is not None
        
    def test_should_refresh_mcp_server(self, cache_manager):
        """Test server refresh logic"""
        server_id = "refresh-test"
        server_config = {
            "command": "npx",
            "args": ["-y", "@test/server"]
        }
        
        # No cache exists - should refresh
        assert cache_manager.should_refresh_mcp_server(server_id, server_config)
        
        # Cache the server
        cache_manager.cache_mcp_server(server_id, server_config, [])
        
        # Same config - should not refresh
        assert not cache_manager.should_refresh_mcp_server(server_id, server_config)
        
        # Changed config - should refresh
        new_config = {
            "command": "npx",
            "args": ["-y", "@test/server", "--new-arg"]
        }
        assert cache_manager.should_refresh_mcp_server(server_id, new_config)
        
    def test_cache_key_generation(self, cache_manager):
        """Test cache key generation"""
        # String input
        key1 = cache_manager._get_cache_key("test string")
        assert len(key1) == 16
        
        # Dict input - should be consistent
        data = {"key": "value", "number": 42}
        key2 = cache_manager._get_cache_key(data)
        key3 = cache_manager._get_cache_key(data)
        assert key2 == key3
        
        # Different data should give different keys
        key4 = cache_manager._get_cache_key({"different": "data"})
        assert key4 != key2
        
    def test_sensitive_data_masking(self, cache_manager):
        """Test that sensitive data is not stored in metadata"""
        server_id = "sensitive-test"
        server_data = {
            "command": "npx",
            "args": ["server"],
            "env": {"API_KEY": "secret123", "TOKEN": "secret456"}
        }
        
        # Cache with sensitive data
        cache_manager.cache_mcp_server(server_id, server_data, [])
        
        # Check metadata doesn't contain actual keys
        metadata = cache_manager.metadata[f"mcp_{server_id}"]
        assert "secret123" not in str(metadata)
        assert "secret456" not in str(metadata)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])