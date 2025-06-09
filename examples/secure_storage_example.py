#!/usr/bin/env python3
"""Example demonstrating secure storage usage for API keys with MCP servers"""

from gradio_mcp_playground.secure_storage import SecureStorage, get_secure_storage


def main():
    """Demonstrate secure storage functionality"""
    
    # Get secure storage instance
    storage = get_secure_storage()
    if not storage:
        print("Secure storage not available. Please install cryptography: pip install cryptography")
        return
    
    print("Secure Storage Example for Gradio MCP Playground")
    print("=" * 50)
    
    # Example 1: Store individual API keys
    print("\n1. Storing individual API keys:")
    
    # Store OpenAI API key
    if storage.store_key("openai", "api_key", "sk-1234567890abcdef"):
        print("✓ Stored OpenAI API key")
    
    # Store Anthropic API key
    if storage.store_key("anthropic", "api_key", "sk-ant-1234567890"):
        print("✓ Stored Anthropic API key")
    
    # Store HuggingFace token
    if storage.store_key("huggingface", "token", "hf_1234567890abcdef"):
        print("✓ Stored HuggingFace token")
    
    # Example 2: Store multiple keys for an MCP server
    print("\n2. Storing multiple keys for an MCP server:")
    
    server_keys = {
        "openai_api_key": "sk-1234567890abcdef",
        "google_api_key": "AIza1234567890abcdef",
        "webhook_secret": "whsec_1234567890"
    }
    
    if storage.store_server_keys("my-ai-server", server_keys):
        print("✓ Stored all keys for my-ai-server")
    
    # Example 3: List stored services and keys
    print("\n3. Listing stored services and keys:")
    
    services = storage.list_services()
    print(f"Services with stored keys: {services}")
    
    for service in services:
        keys = storage.list_keys(service)
        print(f"  {service}: {keys}")
    
    # Example 4: Retrieve keys
    print("\n4. Retrieving keys:")
    
    openai_key = storage.retrieve_key("openai", "api_key")
    if openai_key:
        print(f"✓ Retrieved OpenAI key: {openai_key[:10]}...")
    
    # Retrieve all keys for a server
    server_keys = storage.retrieve_server_keys("my-ai-server")
    print(f"✓ Retrieved keys for my-ai-server: {list(server_keys.keys())}")
    
    # Example 5: Check if server has required keys
    print("\n5. Checking required keys:")
    
    required_keys = ["openai_api_key", "google_api_key"]
    if storage.has_server_keys("my-ai-server", required_keys):
        print("✓ my-ai-server has all required keys")
    
    # Example 6: Get key metadata (without actual values)
    print("\n6. Getting key metadata:")
    
    info = storage.get_all_keys_info()
    for service, keys in info.items():
        print(f"\n{service}:")
        for key_name, metadata in keys.items():
            print(f"  {key_name}: created={metadata['created_at'][:10]}")
    
    # Example 7: Update a key
    print("\n7. Updating a key:")
    
    if storage.update_key("openai", "api_key", "sk-new-key-1234567890"):
        print("✓ Updated OpenAI API key")
    
    # Example 8: Export and import keys
    print("\n8. Exporting and importing keys:")
    
    # Export all keys with a password
    export_data = storage.export_keys("my-backup-password")
    if export_data:
        print(f"✓ Exported keys: {export_data[:50]}...")
        
        # Clear a service's keys
        storage.delete_key("openai")
        print("✓ Deleted OpenAI keys for testing")
        
        # Import keys back
        if storage.import_keys(export_data, "my-backup-password"):
            print("✓ Imported keys successfully")
            
            # Verify OpenAI key is back
            if storage.retrieve_key("openai", "api_key"):
                print("✓ Verified OpenAI key restored")
    
    # Example 9: Integration with MCP server installation
    print("\n9. MCP Server Installation Integration:")
    
    def install_mcp_server_with_keys(server_name: str, required_keys: dict):
        """Example function showing how to integrate with MCP server installation"""
        
        # Check if we have all required keys
        missing_keys = []
        for key_name in required_keys:
            if not storage.retrieve_key(server_name, key_name):
                missing_keys.append(key_name)
        
        if missing_keys:
            print(f"Missing API keys for {server_name}: {missing_keys}")
            print("Please provide the following keys:")
            
            # In a real implementation, this would prompt the user
            for key_name in missing_keys:
                key_value = f"demo-{key_name}-value"  # Would be user input
                storage.store_key(server_name, key_name, key_value)
                print(f"  Stored {key_name}")
        
        # Now install the server with the keys
        server_keys = storage.retrieve_server_keys(server_name)
        print(f"Installing {server_name} with keys: {list(server_keys.keys())}")
        # ... actual MCP server installation would happen here ...
        
        return True
    
    # Example server installation
    required_keys = {
        "api_key": "Main API key for the service",
        "secret_key": "Secret key for webhooks"
    }
    
    install_mcp_server_with_keys("example-mcp-server", required_keys)
    
    # Clean up (optional)
    print("\n10. Cleanup (commented out):")
    print("# storage.clear_all_keys()  # Would delete all stored keys")
    
    print("\n✓ Secure storage example completed!")
    print(f"Keys are stored encrypted in: {storage.config_dir}")


if __name__ == "__main__":
    main()