# Caching System Documentation

The Gradio MCP Playground includes a caching system to significantly improve startup performance by caching MCP server connections, tools, and configuration files.

## Overview

The caching system reduces startup time from 10-30 seconds to 1-3 seconds by:
- Caching MCP server tool definitions
- Caching YAML configuration files
- Skipping server initialization when cached data is available

## How It Works

### Cache Storage

Cache files are stored in platform-specific directories:
- **Windows**: `%USERPROFILE%\AppData\Local\Cache\gradio-mcp-playground\`
- **macOS**: `~/Library/Caches/gradio-mcp-playground/`
- **Linux**: `~/.cache/gradio-mcp-playground/`

### Cache Structure

```
cache/
├── servers/      # MCP server connection data
├── tools/        # Tool definitions from servers  
└── configs/      # YAML configuration files
```

### Cache Invalidation

Caches are automatically invalidated when:
- Cache files are older than 24 hours (configurable)
- Original configuration files are modified
- Server configurations change

## Usage

### Automatic Caching

Caching is enabled by default. When you run the dashboard:

```bash
gmp dashboard --unified
```

You'll see cache indicators:
- `⚡` - Data loaded from cache
- `📦` - Cache statistics on startup

### Manual Cache Management

#### View cache status
```bash
gmp cache status
```

Shows:
- Cache location
- Total cache size
- Number of cached files by type

#### Clear cache
```bash
# Clear all cache
gmp cache clear

# Clear specific cache type
gmp cache clear --type servers
gmp cache clear --type tools
gmp cache clear --type configs
```

#### Force refresh
```bash
gmp cache refresh
```

This clears all cache, forcing a fresh load on next run.

### Disable Caching

To disable caching temporarily:
```bash
export GMP_DISABLE_CACHE=1
gmp dashboard --unified
```

## Security

The caching system includes security features:
- API keys and tokens are **never** cached
- Sensitive environment variables are masked
- Cache files use secure pickle format

## Performance Impact

Typical performance improvements:
- **First run**: 10-30 seconds (no cache)
- **Subsequent runs**: 1-3 seconds (with cache)
- **Improvement**: 80-95% faster startup

## Troubleshooting

### Cache not working

1. Check if caching is enabled:
   ```bash
   gmp cache status
   ```

2. Verify cache directory permissions:
   - Cache directory should be writable
   - Check the path shown in cache status

3. Clear cache and retry:
   ```bash
   gmp cache clear
   ```

### Stale data

If you're seeing outdated information:
1. Clear the cache: `gmp cache clear`
2. Or disable cache temporarily: `export GMP_DISABLE_CACHE=1`

### Performance not improved

Check if servers are actually being cached:
- Look for `⚡` indicators in startup output
- Run `gmp cache status` to see cached file counts

## Configuration

### Cache TTL

Default cache lifetime is 24 hours. To customize, set environment variable:
```bash
export GMP_CACHE_TTL=3600  # 1 hour in seconds
```

### Cache Directory

To use a custom cache directory:
```bash
export GMP_CACHE_DIR=/path/to/custom/cache
```

## Development

### Using Cache Manager in Code

```python
from gradio_mcp_playground.cache_manager import get_cache_manager

cache_manager = get_cache_manager()

# Cache server data
cache_manager.set_server_cache(server_name, config, data)

# Get cached data
cached = cache_manager.get_server_cache(server_name, config)

# Clear all cache
cache_manager.clear_cache()
```

### Cache Keys

Cache keys are generated from:
- Server name and configuration (excluding sensitive env vars)
- File paths for configuration files
- Content hashes for stability

## Best Practices

1. **Regular cache clearing**: Clear cache weekly or when experiencing issues
2. **Monitor cache size**: Use `gmp cache status` to check cache growth
3. **Disable for debugging**: Use `GMP_DISABLE_CACHE=1` when troubleshooting
4. **Security**: Never manually edit cache files as they may contain system information