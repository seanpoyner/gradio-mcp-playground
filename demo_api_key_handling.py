#!/usr/bin/env python3
"""Demo script showing improved API key handling in chat UI"""

import re

def simulate_chat_api_key_parsing(message):
    """Simulate how the chat UI parses natural language API key input"""
    
    print(f"User message: {message}")
    
    # Pattern 1: "install brave search with key YOUR_KEY"
    brave_key_match = re.search(r"install brave search with (?:key|token) ([\w-]+)", message, re.IGNORECASE)
    if brave_key_match:
        api_key = brave_key_match.group(1)
        parsed_message = f"install_mcp_server_from_registry(server_id='brave-search', token='{api_key}')"
        print(f"✅ Parsed as: {parsed_message}")
        return parsed_message
    
    # Pattern 2: "install github with token YOUR_TOKEN"
    github_key_match = re.search(r"install github with (?:key|token) ([\w-]+)", message, re.IGNORECASE)
    if github_key_match:
        api_key = github_key_match.group(1)
        parsed_message = f"install_mcp_server_from_registry(server_id='github', token='{api_key}')"
        print(f"✅ Parsed as: {parsed_message}")
        return parsed_message
    
    # Pattern 3: "my brave api key is YOUR_KEY"
    brave_key_statement = re.search(r"(?:my )?brave (?:api )?key (?:is |= ?)([\w-]+)", message, re.IGNORECASE)
    if brave_key_statement:
        api_key = brave_key_statement.group(1)
        parsed_message = f"I have your Brave API key. Let me install the brave search server: install_mcp_server_from_registry(server_id='brave-search', token='{api_key}')"
        print(f"✅ Parsed as: {parsed_message}")
        return parsed_message
    
    print("❌ No API key pattern detected")
    return message


def simulate_error_response_enhancement(response):
    """Simulate how error responses are enhanced with helpful prompts"""
    
    print("\nAI Response:")
    print(response)
    
    # Check if Brave Search API key is needed
    if "BRAVE_API_KEY not set" in response:
        api_key_prompt = f"\n\n🔑 **Brave Search API Key Required**\n\n"
        api_key_prompt += "To use Brave Search, you need to provide an API key.\n\n"
        api_key_prompt += "🌐 **Get your API key:**\n"
        api_key_prompt += "1. Visit https://brave.com/search/api/\n"
        api_key_prompt += "2. Sign up for a free account\n"
        api_key_prompt += "3. Copy your API key\n\n"
        api_key_prompt += "🔧 **To install with your key:**\n"
        api_key_prompt += "Please type: `install brave search with key YOUR_API_KEY_HERE`\n\n"
        api_key_prompt += "Or use the exact command:\n"
        api_key_prompt += "`install_mcp_server_from_registry(server_id='brave-search', token='YOUR_API_KEY_HERE')`"
        
        print("\nEnhanced response with helpful prompt:")
        print(api_key_prompt)
        return response.replace("Error: BRAVE_API_KEY not set", "") + api_key_prompt
    
    return response


def main():
    """Run demo of API key handling improvements"""
    
    print("=== Gradio MCP Playground: API Key Handling Demo ===\n")
    
    # Test natural language API key input
    print("1. Testing natural language API key input parsing:\n")
    
    test_messages = [
        "install brave search with key BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh",
        "Install Brave Search with token my-api-key-123",
        "my brave api key is BSAcIbrB5nHtrlV5iqt98NaYDhfjOCh",
        "brave key = test-key-456",
        "install github with token ghp_1234567890abcdef",
        "search the web for MCP servers"  # No API key
    ]
    
    for msg in test_messages:
        print("-" * 60)
        simulate_chat_api_key_parsing(msg)
        print()
    
    # Test error response enhancement
    print("\n2. Testing error response enhancement:\n")
    print("-" * 60)
    
    error_response = """Thought: The brave-search server has been started. Now I can perform the web search for information on MCP servers.
Action: brave_search
Action Input: {'query': 'MCP servers', 'count': 10}
Observation: Error: BRAVE_API_KEY not set. Please install the brave-search server first using install_mcp_server_from_registry()"""
    
    enhanced = simulate_error_response_enhancement(error_response)
    
    print("\n3. Summary of improvements:\n")
    print("✅ Natural language API key input is automatically parsed")
    print("✅ Clear instructions provided when API keys are missing")
    print("✅ Links to get API keys are included in error messages")
    print("✅ Multiple input formats supported for user convenience")
    print("✅ API keys are stored securely after first use")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()