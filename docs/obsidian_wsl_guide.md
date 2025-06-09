# Obsidian MCP Server on WSL

## Issue

When running the Gradio MCP Playground from WSL (Windows Subsystem for Linux), the Obsidian MCP server cannot access Windows paths through WSL mounts (e.g., `/mnt/c/Users/...`). This is because the Obsidian MCP server has security restrictions that prevent access to network or remote filesystems.

## Solutions

### Option 1: Run from Windows (Recommended)

The easiest solution is to run the Gradio MCP Playground directly from Windows instead of WSL:

1. Install Python on Windows
2. Install the playground: `pip install gradio-mcp-playground`
3. Run the dashboard: `gmp dashboard`
4. Install Obsidian server with Windows path: `C:\Users\YourName\YourVault`

### Option 2: Use a Linux Vault

Create an Obsidian vault within the WSL filesystem:

1. Create a vault in your WSL home directory:
   ```bash
   mkdir ~/obsidian-vault
   ```

2. Install the Obsidian server with the Linux path:
   ```python
   install_mcp_server_from_registry(
       server_id='obsidian',
       vault_path1='/home/username/obsidian-vault'
   )
   ```

### Option 3: Use Alternative Tools

For cross-platform file access, consider using the filesystem MCP server instead:

```python
install_mcp_server_from_registry(
    server_id='filesystem',
    path='/mnt/c/Users/YourName/Documents'
)
```

The filesystem server supports WSL mount paths and provides similar file operations.

## Technical Details

The Obsidian MCP server validates vault paths to ensure they are:
- On a local filesystem (not network/remote)
- Not using symlinks that point outside their directory
- Not on mounted network drives

WSL mounts (`/mnt/c/...`) are treated as network filesystems and are therefore blocked.