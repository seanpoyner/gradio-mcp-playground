"""Cache Manager for Gradio MCP Playground

Handles caching of MCP server connections, tools, and configurations
to improve startup performance.
"""

import json
import pickle
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import platform
import os
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for MCP servers and configurations"""
    
    # Cache TTL in seconds (24 hours by default)
    DEFAULT_TTL = 86400
    
    # Sensitive keys to mask in cache
    SENSITIVE_KEYS = {
        'token', 'key', 'password', 'secret', 'api_key', 
        'access_token', 'refresh_token', 'client_secret'
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache manager with optional custom cache directory"""
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = self._get_default_cache_dir()
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache subdirectories
        self.servers_cache_dir = self.cache_dir / "servers"
        self.tools_cache_dir = self.cache_dir / "tools"
        self.config_cache_dir = self.cache_dir / "configs"
        
        for dir in [self.servers_cache_dir, self.tools_cache_dir, self.config_cache_dir]:
            dir.mkdir(exist_ok=True)
            
        # Check if caching is disabled
        self.enabled = os.environ.get('GMP_DISABLE_CACHE', '').lower() != '1'
        
        if not self.enabled:
            logger.info("Caching is disabled via GMP_DISABLE_CACHE environment variable")
    
    def _get_default_cache_dir(self) -> Path:
        """Get platform-specific cache directory"""
        system = platform.system()
        
        if system == "Windows":
            # Windows: %USERPROFILE%\AppData\Local\Cache\gradio-mcp-playground
            cache_base = Path(os.environ.get('LOCALAPPDATA', '~')) / 'Cache'
        elif system == "Darwin":
            # macOS: ~/Library/Caches/gradio-mcp-playground
            cache_base = Path.home() / 'Library' / 'Caches'
        else:
            # Linux and others: ~/.cache/gradio-mcp-playground
            cache_base = Path.home() / '.cache'
        
        return cache_base.expanduser() / 'gradio-mcp-playground'
    
    def _get_cache_key(self, data: Any) -> str:
        """Generate a cache key from data"""
        # Convert to stable string representation
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            stable_str = json.dumps(data, sort_keys=True)
        else:
            stable_str = str(data)
        
        # Generate hash
        return hashlib.sha256(stable_str.encode()).hexdigest()[:16]
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Mask sensitive data before caching"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                # Check if key contains sensitive terms
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    masked[key] = "***MASKED***"
                elif isinstance(value, dict):
                    masked[key] = self._mask_sensitive_data(value)
                elif isinstance(value, list):
                    masked[key] = [self._mask_sensitive_data(item) for item in value]
                else:
                    masked[key] = value
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        else:
            return data
    
    def _is_cache_valid(self, cache_file: Path, ttl: Optional[int] = None) -> bool:
        """Check if cache file is still valid"""
        if not cache_file.exists():
            return False
        
        # Check age
        age = time.time() - cache_file.stat().st_mtime
        max_age = ttl or self.DEFAULT_TTL
        
        return age < max_age
    
    def get_server_cache(self, server_name: str, server_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached server information if available"""
        if not self.enabled:
            return None
            
        # Generate cache key based on server config
        cache_key = self._get_cache_key({
            'name': server_name,
            'command': server_config.get('command', ''),
            'args': server_config.get('args', []),
            # Don't include env vars in key as they may contain secrets
        })
        
        cache_file = self.servers_cache_dir / f"{server_name}_{cache_key}.pkl"
        
        if self._is_cache_valid(cache_file):
            try:
                with cache_file.open('rb') as f:
                    cached_data = pickle.load(f)
                logger.debug(f"Cache hit for server {server_name}")
                return cached_data
            except Exception as e:
                logger.debug(f"Failed to load cache for {server_name}: {e}")
                
        return None
    
    def set_server_cache(self, server_name: str, server_config: Dict[str, Any], 
                        server_data: Dict[str, Any]):
        """Cache server information"""
        if not self.enabled:
            return
            
        # Generate cache key
        cache_key = self._get_cache_key({
            'name': server_name,
            'command': server_config.get('command', ''),
            'args': server_config.get('args', []),
        })
        
        cache_file = self.servers_cache_dir / f"{server_name}_{cache_key}.pkl"
        
        try:
            # Mask sensitive data before caching
            masked_data = self._mask_sensitive_data(server_data)
            
            with cache_file.open('wb') as f:
                pickle.dump(masked_data, f)
            logger.debug(f"Cached server data for {server_name}")
        except Exception as e:
            logger.debug(f"Failed to cache server {server_name}: {e}")
    
    def get_tools_cache(self, server_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached tools for a server"""
        if not self.enabled:
            return None
            
        cache_file = self.tools_cache_dir / f"{server_name}_tools.json"
        
        if self._is_cache_valid(cache_file):
            try:
                with cache_file.open('r') as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Failed to load tools cache for {server_name}: {e}")
                
        return None
    
    def set_tools_cache(self, server_name: str, tools: List[Dict[str, Any]]):
        """Cache tools for a server"""
        if not self.enabled:
            return
            
        cache_file = self.tools_cache_dir / f"{server_name}_tools.json"
        
        try:
            with cache_file.open('w') as f:
                json.dump(tools, f, indent=2)
            logger.debug(f"Cached {len(tools)} tools for {server_name}")
        except Exception as e:
            logger.debug(f"Failed to cache tools for {server_name}: {e}")
    
    def get_config_cache(self, config_path: str) -> Optional[Dict[str, Any]]:
        """Get cached configuration file"""
        if not self.enabled:
            return None
            
        # Check if original file has been modified
        original_path = Path(config_path)
        if not original_path.exists():
            return None
            
        cache_key = self._get_cache_key(config_path)
        cache_file = self.config_cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            # Compare modification times
            if original_path.stat().st_mtime > cache_file.stat().st_mtime:
                # Original file is newer, cache is invalid
                return None
                
            try:
                with cache_file.open('r') as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Failed to load config cache for {config_path}: {e}")
                
        return None
    
    def set_config_cache(self, config_path: str, config_data: Dict[str, Any]):
        """Cache configuration file"""
        if not self.enabled:
            return
            
        cache_key = self._get_cache_key(config_path)
        cache_file = self.config_cache_dir / f"{cache_key}.json"
        
        try:
            with cache_file.open('w') as f:
                json.dump(config_data, f, indent=2)
            logger.debug(f"Cached config file {config_path}")
        except Exception as e:
            logger.debug(f"Failed to cache config {config_path}: {e}")
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache (all or specific type)"""
        if cache_type == "servers":
            dirs_to_clear = [self.servers_cache_dir]
        elif cache_type == "tools":
            dirs_to_clear = [self.tools_cache_dir]
        elif cache_type == "configs":
            dirs_to_clear = [self.config_cache_dir]
        else:
            # Clear all
            dirs_to_clear = [self.servers_cache_dir, self.tools_cache_dir, self.config_cache_dir]
        
        for dir in dirs_to_clear:
            for file in dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.debug(f"Failed to delete cache file {file}: {e}")
        
        logger.info(f"Cleared cache: {cache_type or 'all'}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "enabled": self.enabled,
            "cache_dir": str(self.cache_dir),
            "size": 0,
            "files": {
                "servers": 0,
                "tools": 0,
                "configs": 0
            }
        }
        
        # Count files and calculate size
        for cache_type, cache_dir in [
            ("servers", self.servers_cache_dir),
            ("tools", self.tools_cache_dir),
            ("configs", self.config_cache_dir)
        ]:
            for file in cache_dir.glob("*"):
                stats["files"][cache_type] += 1
                stats["size"] += file.stat().st_size
        
        # Convert size to human readable
        size_mb = stats["size"] / (1024 * 1024)
        stats["size_readable"] = f"{size_mb:.2f} MB"
        
        return stats


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager