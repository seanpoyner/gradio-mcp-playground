# Performance Optimization Guide

This guide provides tips for optimizing the startup performance of Gradio MCP Playground.

## Current Performance Bottlenecks

The main bottleneck during startup is loading MCP servers, which involves:
1. Starting server processes (npx, python, etc.)
2. Initializing server connections
3. Fetching tool lists from each server
4. Creating tool wrappers

With 20+ servers, this can take 10-30 seconds.

## Optimization Strategies

### 1. Disable MCP Server Loading on Startup

The quickest way to speed up startup is to skip loading MCP servers:

```bash
export GMP_SKIP_MCP_LOAD=1
gmp dashboard
```

This will start the dashboard immediately without loading any MCP servers. You can then manually connect to specific servers as needed.

### 2. Load Only Essential Servers

Create a minimal server configuration with only the servers you need:

```bash
# Create a minimal config
cp ~/.gmp/mcp_servers.json ~/.gmp/mcp_servers_minimal.json
# Edit to keep only essential servers

# Use the minimal config
export GMP_MCP_CONFIG=~/.gmp/mcp_servers_minimal.json
gmp dashboard
```

### 3. Use Server Groups

Instead of loading all servers at once, organize them into groups:

```json
{
  "groups": {
    "essential": ["filesystem", "memory"],
    "development": ["github", "code-sandbox-mcp"],
    "search": ["brave-search", "google-search"],
    "productivity": ["obsidian", "notion"]
  }
}
```

Then load only specific groups:
```bash
export GMP_SERVER_GROUPS=essential,development
gmp dashboard
```

### 4. Parallel Server Loading

For systems with multiple CPU cores, enable parallel loading:

```bash
export GMP_PARALLEL_LOAD=1
export GMP_MAX_WORKERS=8  # Adjust based on your CPU
gmp dashboard
```

### 5. Cache Optimization

The caching system stores server tool definitions. To maximize cache benefits:

```bash
# Ensure cache is enabled
gmp cache status

# Pre-warm cache by loading all servers once
gmp dashboard --exit-after-load

# Subsequent runs will use cache
gmp dashboard
```

### 6. Lazy Loading

Enable lazy loading to defer server initialization:

```bash
export GMP_LAZY_LOAD=1
gmp dashboard
```

Servers will only be started when their tools are first used.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GMP_SKIP_MCP_LOAD` | Skip loading MCP servers on startup | 0 |
| `GMP_MCP_CONFIG` | Path to custom MCP servers config | ~/.gmp/mcp_servers.json |
| `GMP_SERVER_GROUPS` | Comma-separated list of server groups to load | all |
| `GMP_PARALLEL_LOAD` | Enable parallel server loading | 0 |
| `GMP_MAX_WORKERS` | Max parallel workers | 5 |
| `GMP_LAZY_LOAD` | Enable lazy server loading | 0 |
| `GMP_DISABLE_CACHE` | Disable caching system | 0 |

## Recommended Configuration

For fastest startup with commonly used servers:

```bash
# Create startup script
cat > ~/gmp-fast.sh << 'EOF'
#!/bin/bash
export GMP_PARALLEL_LOAD=1
export GMP_MAX_WORKERS=8
export GMP_SERVER_GROUPS=essential,development
gmp dashboard "$@"
EOF

chmod +x ~/gmp-fast.sh
./gmp-fast.sh
```

## Future Improvements

Planned optimizations include:
- Background server loading after UI starts
- Server connection pooling
- Persistent server processes
- WebSocket-based server connections
- Tool metadata caching without process startup