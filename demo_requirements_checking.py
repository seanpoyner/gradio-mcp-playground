#!/usr/bin/env python3
"""Demo script showing server requirements checking before installation"""

from gradio_mcp_playground.registry import ServerRegistry
from gradio_mcp_playground.secure_storage import SecureTokenStorage


def check_server_requirements_demo(server_id: str) -> None:
    """Demo of checking server requirements"""
    
    print(f"\n{'='*60}")
    print(f"Checking requirements for: {server_id}")
    print(f"{'='*60}\n")
    
    registry = ServerRegistry()
    storage = SecureTokenStorage()
    
    # Get server info
    server_info = registry.get_server_info(server_id)
    if not server_info:
        print(f"❌ Server '{server_id}' not found in registry")
        return
    
    print(f"📋 **Requirements for {server_info['name']}**\n")
    
    # Check required arguments
    required_args = server_info.get('required_args', [])
    if required_args:
        print("**Required Arguments:**")
        for arg in required_args:
            print(f"- `{arg}`: ", end="")
            if arg == 'path':
                print("Directory path to provide access to")
            elif arg == 'timezone':
                print("Timezone (e.g., 'UTC', 'America/New_York')")
            elif arg == 'vault_path1':
                print("Path to your Obsidian vault")
            else:
                print("Required value")
    else:
        print("**Required Arguments:** None")
    
    # Check environment variables
    env_vars = server_info.get('env_vars', {})
    if env_vars:
        print("\n**Required Environment Variables:**")
        
        # Check if we have stored keys
        stored_keys = storage.retrieve_server_keys(server_id)
        
        for env_var, description in env_vars.items():
            print(f"- `{env_var}`: {description}")
            
            # Check if we already have this key stored
            if stored_keys and env_var in stored_keys:
                print(f"  ✅ Already stored securely")
            else:
                print(f"  ❌ Not yet provided")
                
                # Add instructions for getting the key
                if server_id == 'brave-search':
                    print(f"  📝 Get your API key from: https://brave.com/search/api/")
                elif server_id == 'github':
                    print(f"  📝 Create a token at: https://github.com/settings/tokens")
    else:
        print("\n**Required Environment Variables:** None")
    
    # Add setup help
    if server_info.get('setup_help'):
        print(f"\n**Setup Help:** {server_info['setup_help']}")
    
    # Add example installation command
    print("\n**Example Installation:**")
    print("```")
    
    # Build example command
    example_args = {}
    for arg in required_args:
        if arg == 'path':
            example_args[arg] = '/home/user/workspace'
        elif arg == 'timezone':
            example_args[arg] = 'UTC'
        elif arg == 'vault_path1':
            example_args[arg] = '/path/to/obsidian/vault'
        else:
            example_args[arg] = f'YOUR_{arg.upper()}'
    
    # Add tokens for env vars
    if 'BRAVE_API_KEY' in env_vars:
        example_args['token'] = 'YOUR_BRAVE_API_KEY'
    elif 'GITHUB_TOKEN' in env_vars:
        example_args['token'] = 'YOUR_GITHUB_TOKEN'
    
    # Format the command
    if example_args:
        args_str = ', '.join([f"{k}='{v}'" for k, v in example_args.items()])
        print(f"install_mcp_server_from_registry(server_id='{server_id}', {args_str})")
    else:
        print(f"install_mcp_server_from_registry(server_id='{server_id}')")
    
    print("```")


def simulate_agent_workflow(server_id: str) -> None:
    """Simulate how the agent would handle server installation"""
    
    print(f"\n\n{'*'*60}")
    print(f"SIMULATED AGENT WORKFLOW for {server_id}")
    print(f"{'*'*60}\n")
    
    registry = ServerRegistry()
    server_info = registry.get_server_info(server_id)
    
    if not server_info:
        print(f"❌ Server '{server_id}' not found")
        return
    
    print("User: I want to use", server_info['name'])
    print("\nAgent: Let me check what's required for this server...\n")
    print("[Agent calls: check_server_requirements('" + server_id + "')]")
    
    # Simulate the requirements check
    check_server_requirements_demo(server_id)
    
    print("\nAgent: Based on the requirements, I need to ask you for the following:\n")
    
    # Check what's needed
    required_args = server_info.get('required_args', [])
    env_vars = server_info.get('env_vars', {})
    
    if required_args:
        for arg in required_args:
            if arg == 'path':
                print("📁 Which directory would you like to provide access to?")
                print("   Example response: `use path /home/user/workspace`")
            elif arg == 'vault_path1':
                print("📁 Where is your Obsidian vault located?")
                print("   Example response: `my obsidian vault is at /path/to/vault`")
            elif arg == 'timezone':
                print("🕐 What timezone should I use?")
                print("   Example response: `use timezone America/New_York`")
    
    if env_vars:
        for env_var in env_vars:
            if env_var == 'BRAVE_API_KEY':
                print("\n🔑 Please provide your Brave Search API key:")
                print("   Get it from: https://brave.com/search/api/")
                print("   Example response: `my brave api key is YOUR_KEY_HERE`")
            elif env_var == 'GITHUB_TOKEN':
                print("\n🔑 Please provide your GitHub personal access token:")
                print("   Create one at: https://github.com/settings/tokens")
                print("   Example response: `my github token is YOUR_TOKEN_HERE`")
    
    if not required_args and not env_vars:
        print("✅ No additional information needed! I can install this server directly.")
        print(f"\n[Agent calls: install_mcp_server_from_registry(server_id='{server_id}')]")


def main():
    """Run the requirements checking demo"""
    
    print("=== MCP Server Requirements Checking Demo ===")
    print("\nThis demo shows how the improved system checks server requirements")
    print("before attempting installation.\n")
    
    # Demo servers with different requirements
    servers_to_check = [
        "memory",        # No requirements
        "filesystem",    # Requires path argument
        "brave-search",  # Requires API key (env var)
        "github",        # Requires token (env var)
        "obsidian",      # Requires vault path
        "time",          # Requires timezone
    ]
    
    # Check requirements for each server
    for server_id in servers_to_check:
        check_server_requirements_demo(server_id)
    
    # Simulate agent workflows
    print("\n\n" + "="*60)
    print("AGENT WORKFLOW SIMULATIONS")
    print("="*60)
    
    # Simulate a few key workflows
    simulate_agent_workflow("brave-search")
    simulate_agent_workflow("filesystem")
    simulate_agent_workflow("memory")
    
    print("\n\n=== Summary ===")
    print("\nThe improved system now:")
    print("✅ Always checks requirements before attempting installation")
    print("✅ Shows which arguments and environment variables are needed")
    print("✅ Indicates whether API keys are already stored")
    print("✅ Provides clear instructions on how to obtain API keys")
    print("✅ Gives example commands with proper syntax")
    print("✅ Uses natural language patterns for user input")


if __name__ == "__main__":
    main()