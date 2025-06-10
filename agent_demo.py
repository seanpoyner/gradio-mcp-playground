#!/usr/bin/env python3
"""
Gradio MCP Playground - Agent System Demo
Quick demo script to showcase agent capabilities
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    """Print a nice banner"""
    print("\n" + "="*60)
    print("🛝 Gradio MCP Playground - Agent System Demo")
    print("="*60 + "\n")

def demo_info():
    """Show what the demo will do"""
    print("This demo will showcase:")
    print("✓ Agent Control Panel - Deploy and monitor agents")
    print("✓ Pipeline Builder - Visual workflow creation")
    print("✓ Three AI Modes - General, MCP, and Agent Builder")
    print("✓ Pre-built Agents - Twitter, Web Scraper, Data Processor")
    print("\n")

def check_dependencies():
    """Check if all dependencies are available"""
    print("Checking dependencies...")
    
    dependencies = {
        "gradio": "Core UI framework",
        "mcp": "Model Context Protocol",
        "psutil": "System monitoring",
        "pydantic": "Data validation"
    }
    
    missing = []
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module}: {description}")
        except ImportError:
            print(f"✗ {module}: {description} (MISSING)")
            missing.append(module)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: pip install gradio-mcp-playground[all]")
        return False
    
    print("\nAll dependencies satisfied!")
    return True

def launch_demo():
    """Launch the agent demo"""
    print("\nLaunching Agent System Demo...")
    print("This will start the full agent platform with:")
    print("- Agent Control Panel")
    print("- Pipeline Builder")
    print("- Server Manager")
    print("- MCP Connections")
    
    try:
        # Import and launch the agent app
        from agent.app import main as agent_main
        
        print("\nStarting on http://localhost:8080")
        print("Press Ctrl+C to stop\n")
        
        # Launch with development settings for demo
        sys.argv = ['agent_demo.py', '--dev', '--port', '8080']
        agent_main()
        
    except ImportError as e:
        print(f"\nError: Could not import agent components: {e}")
        print("\nTrying alternative launch method...")
        
        # Try launching the unified dashboard instead
        try:
            from gradio_mcp_playground.cli import main as cli_main
            print("\nLaunching unified dashboard with agent features...")
            sys.argv = ['gmp', 'dashboard', '--port', '8080']
            cli_main()
        except Exception as e2:
            print(f"\nError: {e2}")
            print("\nPlease ensure you're in the project directory and run:")
            print("  python agent/app.py")

def main():
    """Main demo function"""
    print_banner()
    demo_info()
    
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        return
    
    print("\nReady to launch!")
    input("Press Enter to start the demo...")
    
    launch_demo()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nFor full functionality, please run:")
        print("  cd agent && python app.py --dev")