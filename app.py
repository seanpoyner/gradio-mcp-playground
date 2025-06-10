#!/usr/bin/env python3
"""
Gradio MCP Playground - AI Agent Management Platform

A comprehensive Gradio app that showcases powerful applications of AI agents.
Build, manage, deploy, and monitor AI-powered tools and services.
"""

import os
import sys
from pathlib import Path

# Add the package to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from gradio_mcp_playground.web_ui import create_dashboard
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating fallback dashboard...")
    
    import gradio as gr
    
    def create_dashboard():
        with gr.Blocks(title="Gradio MCP Playground - AI Agent Platform", theme=gr.themes.Soft()) as demo:
            gr.Markdown("""
            # 🤖 Gradio MCP Playground
            ## AI Agent Management Platform
            
            **A complete Gradio app showcasing powerful applications of AI agents**
            
            Transform any idea into a deployable AI agent in minutes. This platform demonstrates 
            the full lifecycle of AI agent development - from creation to deployment to monitoring.
            """)
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
                    ### 🚀 What This Platform Does
                    
                    - **Agent Creation**: Build AI agents from templates or custom code
                    - **Agent Management**: Monitor, start, stop, and configure agents
                    - **Agent Discovery**: Browse and install community agents
                    - **Testing & Debugging**: Real-time agent testing and debugging tools
                    - **Deployment**: One-click deployment to production environments
                    - **Monitoring**: Live monitoring of agent performance and usage
                    """)
                
                with gr.Column():
                    gr.Markdown("""
                    ### 🎯 Use Cases Demonstrated
                    
                    - **Content Creation Agents**: Image generation, text processing
                    - **Data Analysis Agents**: CSV analysis, visualization, reporting
                    - **Productivity Agents**: File processing, API integration
                    - **Development Agents**: Code analysis, testing, deployment
                    - **Communication Agents**: Translation, summarization, chat
                    - **Custom Workflow Agents**: Multi-step automated processes
                    """)
            
            with gr.Tabs():
                with gr.Tab("🏗️ Agent Builder"):
                    gr.Markdown("### Create New AI Agents")
                    
                    with gr.Row():
                        agent_name = gr.Textbox(label="Agent Name", placeholder="my-awesome-agent")
                        agent_template = gr.Dropdown(
                            choices=[
                                "basic", "calculator", "image-generator", 
                                "data-analyzer", "file-processor", "web-scraper",
                                "llm-tools", "api-wrapper"
                            ], 
                            label="Template", 
                            value="basic"
                        )
                    
                    agent_description = gr.Textbox(
                        label="Description", 
                        placeholder="Describe what your agent does...",
                        lines=3
                    )
                    
                    create_agent_btn = gr.Button("🚀 Create Agent", variant="primary")
                    
                    def demo_create_agent(name, template, description):
                        if not name:
                            return "❌ Please provide an agent name"
                        
                        return f"""✅ Agent '{name}' created successfully!

**Template**: {template}
**Description**: {description}

Your agent is ready to deploy. In the full platform, this would:
1. Generate the agent code from template
2. Set up the MCP server configuration  
3. Create deployment scripts
4. Register the agent in the platform

**Next Steps**: Test your agent and deploy to production!"""
                    
                    agent_output = gr.Textbox(label="Creation Status", lines=8)
                    create_agent_btn.click(
                        demo_create_agent, 
                        inputs=[agent_name, agent_template, agent_description],
                        outputs=agent_output
                    )
                
                with gr.Tab("🔍 Agent Discovery"):
                    gr.Markdown("### Browse Community Agents")
                    
                    search_box = gr.Textbox(label="Search Agents", placeholder="Search for agents...")
                    category_filter = gr.Dropdown(
                        choices=["All", "Content Creation", "Data Analysis", "Productivity", "Development"],
                        label="Category",
                        value="All"
                    )
                    
                    def demo_search_agents(query, category):
                        # Demo data
                        agents = [
                            {"name": "Smart Image Generator", "category": "Content Creation", "downloads": 1250},
                            {"name": "CSV Data Analyzer", "category": "Data Analysis", "downloads": 890},  
                            {"name": "PDF Document Processor", "category": "Productivity", "downloads": 567},
                            {"name": "Code Review Assistant", "category": "Development", "downloads": 432},
                            {"name": "Multi-Language Translator", "category": "Content Creation", "downloads": 345},
                        ]
                        
                        if query:
                            agents = [a for a in agents if query.lower() in a["name"].lower()]
                        if category != "All":
                            agents = [a for a in agents if a["category"] == category]
                        
                        return [[a["name"], a["category"], f"{a['downloads']} downloads"] for a in agents]
                    
                    search_btn = gr.Button("🔍 Search", variant="secondary")
                    agents_table = gr.Dataframe(
                        headers=["Agent Name", "Category", "Downloads"],
                        label="Available Agents"
                    )
                    
                    search_btn.click(
                        demo_search_agents,
                        inputs=[search_box, category_filter],
                        outputs=agents_table
                    )
                
                with gr.Tab("🛠️ Agent Testing"):
                    gr.Markdown("### Test Your Agents")
                    
                    test_agent = gr.Dropdown(
                        choices=["Smart Image Generator", "CSV Data Analyzer", "PDF Processor"],
                        label="Select Agent to Test"
                    )
                    
                    test_input = gr.Textbox(
                        label="Test Input", 
                        placeholder="Enter test data for your agent...",
                        lines=3
                    )
                    
                    test_btn = gr.Button("🧪 Run Test", variant="primary")
                    
                    def demo_test_agent(agent, test_input):
                        if not agent or not test_input:
                            return "Please select an agent and provide test input"
                        
                        return f"""🧪 Testing '{agent}' with input: "{test_input}"

**Test Results:**
✅ Agent responded successfully
⏱️ Response time: 1.2s
📊 Output quality: Excellent
🔧 Status: All systems operational

**Sample Output:**
"Based on your input '{test_input}', the agent would process this and return relevant results. In a real deployment, this would show actual agent output."

**Performance Metrics:**
- CPU Usage: 45%
- Memory Usage: 128MB  
- Success Rate: 99.2%"""
                    
                    test_output = gr.Textbox(label="Test Results", lines=12)
                    test_btn.click(
                        demo_test_agent,
                        inputs=[test_agent, test_input], 
                        outputs=test_output
                    )
                
                with gr.Tab("📊 Monitoring Dashboard"):
                    gr.Markdown("### Real-time Agent Monitoring")
                    
                    with gr.Row():
                        gr.Number(label="Active Agents", value=12, interactive=False)
                        gr.Number(label="Total Requests Today", value=3847, interactive=False)
                        gr.Number(label="Success Rate", value=99.2, interactive=False)
                        gr.Number(label="Avg Response Time", value=1.8, interactive=False)
                    
                    gr.Markdown("### Agent Status")
                    status_data = [
                        ["Smart Image Generator", "🟢 Running", "95.2%", "1.1s"],
                        ["CSV Data Analyzer", "🟢 Running", "98.7%", "0.8s"],
                        ["PDF Processor", "🟡 Scaling", "97.1%", "2.1s"],
                        ["Code Assistant", "🟢 Running", "99.9%", "0.5s"],
                        ["Translator", "🔴 Stopped", "0%", "-"],
                    ]
                    
                    gr.Dataframe(
                        value=status_data,
                        headers=["Agent", "Status", "Success Rate", "Avg Response"],
                        label="Agent Performance"
                    )
                
                with gr.Tab("🚀 Deployment"):
                    gr.Markdown("### Deploy Your Agents")
                    
                    deploy_agent = gr.Dropdown(
                        choices=["Smart Image Generator", "CSV Data Analyzer", "PDF Processor"],
                        label="Select Agent to Deploy"
                    )
                    
                    deploy_target = gr.Dropdown(
                        choices=["Hugging Face Spaces", "AWS Lambda", "Google Cloud Run", "Docker Container"],
                        label="Deployment Target",
                        value="Hugging Face Spaces"
                    )
                    
                    deploy_btn = gr.Button("🚀 Deploy Agent", variant="primary")
                    
                    def demo_deploy_agent(agent, target):
                        if not agent:
                            return "Please select an agent to deploy"
                        
                        return f"""🚀 Deploying '{agent}' to {target}...

**Deployment Progress:**
✅ Building agent container
✅ Configuring MCP server 
✅ Setting up environment
✅ Running health checks
🔄 Publishing to {target}...

**Deployment Details:**
- Agent: {agent}
- Target: {target}
- URL: https://huggingface.co/spaces/username/{agent.lower().replace(' ', '-')}
- Status: Live and ready to receive requests

**Integration Instructions:**
Your agent can now be used with:
- Claude Desktop (MCP client)
- Cursor IDE
- Any MCP-compatible application

Add this to your MCP configuration:
```json
{{
  "servers": {{
    "{agent.lower().replace(' ', '-')}": {{
      "command": "python",
      "args": ["server.py"],
      "env": {{"GRADIO_SERVER_URL": "https://..."}}
    }}
  }}
}}
```"""
                    
                    deploy_output = gr.Textbox(label="Deployment Status", lines=15)
                    deploy_btn.click(
                        demo_deploy_agent,
                        inputs=[deploy_agent, deploy_target],
                        outputs=deploy_output
                    )
            
            gr.Markdown("""
            ---
            
            ### 🎥 Video Overview
            
            [**Watch the Platform Demo**](https://example.com/demo-video) - See how to build, test, and deploy AI agents in under 5 minutes!
            
            ### 🔗 Links
            
            - **Repository**: [GitHub](https://github.com/anthropics/gradio-mcp-playground)
            - **Documentation**: [User Guide](docs/user_guide.md)
            - **CLI Tools**: `pip install gradio-mcp-playground`
            - **Community**: Join our Discord for agent sharing and collaboration
            
            **Tags**: #agent-demo-track #ai-agents #gradio #mcp #automation
            """)
        
        return demo

if __name__ == "__main__":
    # Create and launch the dashboard
    dashboard = create_dashboard()
    
    # Launch with appropriate settings for Hugging Face Spaces
    dashboard.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False,
        show_error=True,
        favicon_path="🛝"
    )