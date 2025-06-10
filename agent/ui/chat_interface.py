"""Chat Interface Component

Provides the main conversational interface for the GMP Agent.
"""

import asyncio
from typing import List, Dict, Any, Tuple, Optional
import gradio as gr

# Import Agent Builder and MCP Agent
try:
    # Try relative imports first (when used as package)
    from ..core.agent_builder import AgentBuilder
    from ..core.agent import GMPAgent
except ImportError:
    try:
        # Try absolute imports (when running as script from agent directory)
        from core.agent_builder import AgentBuilder
        from core.agent import GMPAgent
    except ImportError:
        # Last resort - add path and import
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from core.agent_builder import AgentBuilder
        from core.agent import GMPAgent


class ChatInterface:
    """Main chat interface for the GMP Agent"""
    
    def __init__(self, agent=None):
        # Initialize MCP agent
        if agent is None:
            self.mcp_agent = GMPAgent()
        else:
            self.mcp_agent = agent
            
        # Initialize Agent Builder
        try:
            self.agent_builder = AgentBuilder()
        except Exception as e:
            print(f"Warning: Could not initialize AgentBuilder: {e}")
            self.agent_builder = None
            
        # Start with Agent Builder as default if available, otherwise MCP Agent
        if self.agent_builder is not None:
            self.agent = self.agent_builder
            self.current_agent_mode = "Agent Builder"
        else:
            self.agent = self.mcp_agent
            self.current_agent_mode = "MCP Agent"
            
        self.conversation_history = []
        self.mcp_connections_panel = None  # Will be set later
        
    def create_interface(self) -> None:
        """Create the chat interface components"""
        
        with gr.Column(scale=1):
            # Agent Selection Dropdown
            with gr.Row():
                # Determine available choices and default
                choices = []
                default_value = "MCP Agent"
                
                if self.agent_builder is not None:
                    choices.append("Agent Builder")
                    default_value = "Agent Builder"
                    
                choices.append("MCP Agent")
                
                self.agent_selector = gr.Dropdown(
                    label="🤖 Select Agent Mode",
                    choices=choices,
                    value=default_value,
                    info="Choose between Agent creation (Agent Builder) or MCP Server building (MCP Agent)",
                    scale=2
                )
                
                # Dynamic agent info based on current mode
                info_text = "**MCP Agent**: Build and manage Model Context Protocol servers"
                if self.current_agent_mode == "Agent Builder":
                    info_text = "**Agent Builder**: Create custom Gradio agents using AI and system prompts"
                    
                self.agent_info = gr.Markdown(
                    info_text,
                    elem_classes="agent-info"
                )
            
            # Chat display area
            self.chatbot = gr.Chatbot(
                label="GMP Agent",
                height=500,
                show_label=True,
                container=True,
                bubble_full_width=False,
                type="messages",
                value=[
                    {"role": "assistant", "content": "🤖 Hello! I'm the Agent Builder, your intelligent assistant for creating custom Gradio agents. I can help you build specialized agents using system prompts from top AI assistants. What kind of agent would you like to create?"}
                ]
            )
            
            with gr.Row():
                # Message input
                self.message_input = gr.Textbox(
                    label="Message",
                    placeholder="Describe what you want to build",
                    lines=2,
                    scale=4,
                    show_label=False
                )
                
                # Send button
                self.send_button = gr.Button(
                    "Send",
                    variant="primary",
                    scale=1
                )
            
            with gr.Row():
                # Action buttons
                self.clear_button = gr.Button("🗑️ Clear Chat", size="sm")
                self.save_button = gr.Button("💾 Save Conversation", size="sm")
                self.load_button = gr.Button("📁 Load Conversation", size="sm")
                
                # Examples dropdown
                with gr.Column(scale=2):
                    self.examples_dropdown = gr.Dropdown(
                        label="Quick Examples",
                        choices=[
                            "Create a code review agent using Claude's system prompt",
                            "Build a creative writing assistant with v0's style",
                            "Make a data analysis agent with GitHub Copilot's approach",
                            "Create a UI component builder like Cursor IDE",
                            "Build a conversational agent using Anthropic's prompt",
                            "Make a debugging assistant with advanced reasoning",
                            "Create a documentation writer agent",
                            "Build a Python tutor agent"
                        ],
                        value=None,
                        interactive=True
                    )
            
            # Status and metadata display
            with gr.Accordion("💡 Context & Suggestions", open=False):
                self.context_display = gr.JSON(
                    label="Current Context",
                    value={}
                )
                
                self.suggestions_display = gr.Markdown(
                    "**Suggestions will appear here based on our conversation...**"
                )
            
            # Hugging Face Model Configuration
            with gr.Accordion("🤖 AI Model Configuration", open=False):
                with gr.Row():
                    with gr.Column(scale=2):
                        self.hf_token_input = gr.Textbox(
                            label="Hugging Face Token",
                            placeholder="Enter your HF token (hf_...)",
                            type="password",
                            interactive=True
                        )
                    
                    with gr.Column(scale=2):
                        self.model_dropdown = gr.Dropdown(
                            label="Model Selection",
                            choices=[
                                "Qwen/Qwen2.5-Coder-32B-Instruct",
                                "mistralai/Mixtral-8x7B-Instruct-v0.1",
                                "HuggingfaceH4/zephyr-7b-beta"
                            ],
                            value=None,
                            interactive=True
                        )
                
                with gr.Row():
                    self.save_token_btn = gr.Button("💾 Save Token", variant="secondary", size="sm")
                    self.load_model_btn = gr.Button("🔄 Load Model", variant="primary", size="sm")
                    self.unload_model_btn = gr.Button("🗑️ Unload Model", variant="secondary", size="sm")
                
                self.model_status = gr.Markdown("**Model Status**: Initializing...")

            # Agent mode selection (duplicate removed - using agent_selector instead)
            # The agent_mode_dropdown is redundant with agent_selector
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Initialize HF interface after setup
        self._initialize_hf_interface()
    
    def _initialize_hf_interface(self) -> None:
        """Initialize HF interface components after agent setup"""
        try:
            # Use the current agent based on mode
            current_agent = self.agent_builder if self.current_agent_mode == "Agent Builder" else self.mcp_agent
            
            # Load existing token if available
            existing_token = current_agent.get_hf_token()
            if existing_token:
                self.hf_token_input.value = "••••••••••••" + existing_token[-8:] if len(existing_token) > 8 else "••••••••"
            
            # Set current model selection
            current_model = current_agent.get_current_model()
            if current_model:
                self.model_dropdown.value = current_model
            
            # Update model status
            status_text = self._update_model_status()
            self.model_status.value = status_text
            
        except Exception as e:
            print(f"Warning: Failed to initialize HF interface: {e}")

    def set_mcp_connections_panel(self, panel) -> None:
        """Set the MCP connections panel reference"""
        self.mcp_connections_panel = panel
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for the interface"""
        
        # Send message on button click or Enter
        self.send_button.click(
            fn=self._handle_message,
            inputs=[self.message_input, self.chatbot],
            outputs=[self.chatbot, self.message_input, self.context_display, self.suggestions_display],
            show_progress=True
        )
        
        self.message_input.submit(
            fn=self._handle_message,
            inputs=[self.message_input, self.chatbot],
            outputs=[self.chatbot, self.message_input, self.context_display, self.suggestions_display],
            show_progress=True
        )
        
        # Example selection
        self.examples_dropdown.change(
            fn=self._handle_example_selection,
            inputs=[self.examples_dropdown, self.chatbot],
            outputs=[self.chatbot, self.message_input, self.examples_dropdown, self.context_display, self.suggestions_display]
        )
        
        # Clear conversation
        self.clear_button.click(
            fn=self._clear_conversation,
            outputs=[self.chatbot, self.context_display, self.suggestions_display]
        )
        
        # Save conversation
        self.save_button.click(
            fn=self._save_conversation,
            outputs=[gr.Textbox(visible=False)]  # Hidden output for download
        )
        
        # Load conversation  
        self.load_button.click(
            fn=self._show_load_dialog,
            outputs=[self.chatbot, self.context_display]
        )
        
        # HF Model configuration handlers
        self.save_token_btn.click(
            fn=self._save_hf_token,
            inputs=[self.hf_token_input],
            outputs=[self.model_status]
        )
        
        self.load_model_btn.click(
            fn=self._load_hf_model,
            inputs=[self.model_dropdown],
            outputs=[self.model_status],
            show_progress=True
        )
        
        self.unload_model_btn.click(
            fn=self._unload_hf_model,
            outputs=[self.model_status]
        )

        # Agent selector change
        self.agent_selector.change(
            fn=self._change_agent_mode,
            inputs=[self.agent_selector],
            outputs=[self.chatbot, self.context_display, self.suggestions_display, self.agent_info]
        )

    async def _handle_message(self, message: str, chat_history: List[Dict]) -> Tuple[List[Dict], str, Dict[str, Any], str]:
        """Handle user message and generate response"""
        
        if not message.strip():
            return chat_history, "", {}, ""
        
        # Add user message to chat
        chat_history.append({"role": "user", "content": message})
        
        try:
            # Update agent with current MCP connections if available (only for MCP Agent)
            if self.mcp_connections_panel and self.current_agent_mode == "MCP Agent":
                active_connections = self.mcp_connections_panel.get_active_connections()
                self.mcp_agent.set_mcp_connections(active_connections)
            
            # Process message with the current agent
            if self.current_agent_mode == "Agent Builder":
                response, metadata = await self.agent_builder.process_agent_request(message)
            else:
                response, metadata = await self.mcp_agent.process_message(message)
            
            # Add agent response to chat
            chat_history.append({"role": "assistant", "content": response})
            
            # Update context display
            context_info = {
                "agent_mode": self.current_agent_mode,
                "intent": metadata.get("intent", "unknown"),
                "confidence": metadata.get("confidence", 0.0),
                "entities": metadata.get("entities", {}),
                "action": metadata.get("action", "respond"),
                "source": metadata.get("source", "rule_based")
            }
            
            # Add model info if HF was used
            if metadata.get("source") == "huggingface_model":
                context_info["model"] = metadata.get("model", "unknown")
            
            # Generate suggestions based on current mode
            suggestions = self._generate_suggestions(metadata)
            
            return chat_history, "", context_info, suggestions
            
        except Exception as e:
            # Handle errors gracefully
            error_response = f"I encountered an error: {str(e)}. Please try rephrasing your request or ask for help."
            chat_history.append({"role": "assistant", "content": error_response})
            
            return chat_history, "", {"error": str(e), "agent_mode": self.current_agent_mode}, "Try asking for help or rephrasing your request."
    
    def _handle_example_selection(self, selected_example: str, chat_history: List[Dict]) -> Tuple[List[Dict], str, str, Dict[str, Any], str]:
        """Handle selection of an example prompt"""
        
        if not selected_example:
            return chat_history, "", "", {}, ""
        
        # Set the example as the current message
        return chat_history, selected_example, "", {}, ""
    
    def _clear_conversation(self) -> Tuple[List[Dict], Dict[str, Any], str]:
        """Clear the conversation history"""
        
        # Clear conversation for current agent
        if self.current_agent_mode == "Agent Builder":
            # Agent Builder doesn't have clear_conversation method, so just reset locally
            self.conversation_history = []
        else:
            self.mcp_agent.clear_conversation()
        
        # Return initial state with system message based on current mode
        if self.current_agent_mode == "Agent Builder":
            initial_history = [
                {"role": "assistant", "content": "🤖 Hello! I'm the Agent Builder, your intelligent assistant for creating custom Gradio agents. I can help you build specialized agents using system prompts from top AI assistants. What kind of agent would you like to create?"}
            ]
        else:
            initial_history = [
                {"role": "assistant", "content": "👋 Hello! I'm the GMP Agent, your intelligent assistant for building MCP servers. How can I help you today?"}
            ]
        
        return initial_history, {}, ""
    
    def _save_conversation(self) -> str:
        """Save conversation to file"""
        
        try:
            # Get conversation history
            history = self.agent.get_conversation_history()
            
            # Create downloadable content
            content = "# GMP Agent Conversation\n\n"
            
            for msg in history:
                role = msg["role"].title()
                timestamp = msg["timestamp"]
                content += f"## {role} ({timestamp})\n\n{msg['content']}\n\n---\n\n"
            
            return content
            
        except Exception as e:
            return f"Error saving conversation: {str(e)}"
    
    def _show_load_dialog(self) -> Tuple[List[List[str]], Dict[str, Any]]:
        """Show dialog for loading conversation"""
        
        # This would typically show a file upload dialog
        # For now, return current state
        return self.chatbot.value, {}
    
    def _generate_suggestions(self, metadata: Dict[str, Any]) -> str:
        """Generate contextual suggestions based on conversation metadata"""
        
        action = metadata.get("action", "")
        intent = metadata.get("intent", "")
        source = metadata.get("source", "rule_based")
        agent_mode = metadata.get("agent_mode", self.current_agent_mode)
        
        suggestions = "## 💡 What you can do next:\n\n"
        
        # Add AI model info if used
        if source == "huggingface_model":
            model_name = metadata.get("model", "Unknown")
            suggestions += f"🤖 *Response generated using {model_name}*\n\n"
        
        # Agent Builder specific suggestions
        if agent_mode == "Agent Builder":
            if action == "request_agent_details":
                suggestions += """
- **"Create a code review agent"** - Build an AI coding assistant
- **"Make a creative writing helper"** - Generate content creation agent
- **"Build a data analysis agent"** - Create data science assistant
- **"I want a UI component builder"** - Make interface generation agent
"""
            elif action == "ready_to_build":
                suggestions += """
- **"Use Claude's system prompt"** - Professional conversational style
- **"Apply v0's approach"** - UI/UX focused generation
- **"Use GitHub Copilot style"** - Code-focused assistance
- **"Apply default style"** - Balanced general-purpose agent
"""
            elif action == "agent_created":
                suggestions += """
- **"Create another agent"** - Build a different type of agent
- **"Test the new agent"** - Try out your created agent
- **"Show me the code"** - View generated agent code
- **"Customize further"** - Add more features to the agent
"""
            else:
                suggestions += """
- **"Create a Python tutor agent"** - Educational assistant
- **"Build a debugging helper"** - Code troubleshooting agent
- **"Make a documentation writer"** - Technical writing assistant
- **"Create a conversational agent"** - General purpose chat agent
"""
        
        # MCP Agent specific suggestions
        else:
            if action == "show_recommendations":
                suggestions += """
- **"Create the first option"** - Build the top recommended server
- **"Customize option 2"** - Modify a recommended server for your needs  
- **"Show me more options"** - See additional server templates
- **"Explain how X works"** - Learn about a specific server type
"""
            elif action == "request_clarification":
                suggestions += """
- **Be more specific** about your requirements
- **Mention the type of data** you'll work with
- **Describe your use case** in more detail
- **Ask for examples** of similar servers
"""
            elif action == "show_search_results":
                suggestions += """
- **"Create server X"** - Build one of the found servers
- **"Tell me more about Y"** - Get details about a specific server
- **"Show similar servers"** - Find related options
- **"Search for Z"** - Try a different search
"""
            elif intent == "create_server":
                suggestions += """
- **"Start building"** - Begin server creation
- **"Use template X"** - Choose a specific template
- **"Add custom features"** - Extend beyond basic templates
- **"Show me the code"** - See what will be generated
"""
            elif intent == "get_help":
                suggestions += """
- **"Show me an example"** - See sample implementations
- **"What can you build?"** - Explore available options
- **"How do I deploy?"** - Learn about deployment
- **"Explain MCP protocol"** - Understand the technology
"""
            else:
                suggestions += """
- **"Create a new server"** - Start building something
- **"Show available templates"** - Browse options
- **"Help me understand MCP"** - Learn the basics
- **"Deploy my existing server"** - Put it online
"""
        
        return suggestions
    
    # Hugging Face Model Configuration Methods
    
    def _update_model_status(self) -> str:
        """Update and return current model status"""
        try:
            # Use the current agent based on mode
            current_agent = self.agent_builder if self.current_agent_mode == "Agent Builder" else self.mcp_agent
            status = current_agent.get_model_status()
            
            if not status["has_transformers"]:
                return "**Model Status**: ❌ Transformers library not installed. Run: `pip install transformers torch`"
            
            if not status["has_secure_storage"]:
                return "**Model Status**: ❌ Secure storage not available. Install cryptography: `pip install cryptography`"
            
            if not status.get("has_token", False):
                return "**Model Status**: ⚠️ No HuggingFace token found. Please enter your token above."
            
            if status["model_loaded"]:
                return f"**Model Status**: ✅ Model loaded: `{status['current_model']}`"
            
            return "**Model Status**: 🔄 Ready to load model. Select a model and click 'Load Model'."
            
        except Exception as e:
            return f"**Model Status**: ❌ Error checking status: {str(e)}"
    
    def _save_hf_token(self, token: str) -> str:
        """Save HuggingFace token securely"""
        try:
            if not token or len(token.strip()) < 10:
                return "**Model Status**: ❌ Please enter a valid HuggingFace token"
            
            # Don't save if it's the masked display value
            if "••••" in token:
                return "**Model Status**: ⚠️ Token already saved. Enter a new token to update."
            
            # Use the current agent based on mode
            current_agent = self.agent_builder if self.current_agent_mode == "Agent Builder" else self.mcp_agent
            
            if current_agent.set_hf_token(token.strip()):
                return "**Model Status**: ✅ Token saved securely!"
            else:
                return "**Model Status**: ❌ Failed to save token. Check secure storage setup."
                
        except Exception as e:
            return f"**Model Status**: ❌ Error saving token: {str(e)}"
    
    async def _load_hf_model(self, model_name: str) -> str:
        """Load selected HuggingFace model"""
        try:
            if not model_name:
                return "**Model Status**: ❌ Please select a model"
            
            # Use the current agent based on mode
            current_agent = self.agent_builder if self.current_agent_mode == "Agent Builder" else self.mcp_agent
            
            # Check if token is available
            if not current_agent.get_hf_token():
                return "**Model Status**: ❌ Please save your HuggingFace token first"
            
            success = await current_agent.load_hf_model(model_name)
            
            if success:
                return f"**Model Status**: ✅ Model loaded successfully: `{model_name}`"
            else:
                return f"**Model Status**: ❌ Failed to load model: `{model_name}`. Check logs for details."
                
        except Exception as e:
            return f"**Model Status**: ❌ Error loading model: {str(e)}"
    
    def _unload_hf_model(self) -> str:
        """Unload current HuggingFace model"""
        try:
            # Use the current agent based on mode
            current_agent = self.agent_builder if self.current_agent_mode == "Agent Builder" else self.mcp_agent
            current_agent.unload_hf_model()
            return "**Model Status**: ✅ Model unloaded successfully"
        except Exception as e:
            return f"**Model Status**: ❌ Error unloading model: {str(e)}"

    # Additional helper methods for server building UI

    def update_chat_with_progress(self, progress_message: str) -> None:
        """Update chat with progress information"""
        # This would be called during long-running operations
        # to show progress to the user
        pass
    
    def show_server_preview(self, server_info: Dict[str, Any]) -> str:
        """Show a preview of a server being built"""
        
        preview = f"""
## 🔍 Server Preview: {server_info.get('name', 'New Server')}

**Description:** {server_info.get('description', 'No description')}

**Features:**
"""
        
        tools = server_info.get('tools', [])
        if tools:
            for tool in tools:
                preview += f"- {tool.get('name', 'Tool')}: {tool.get('description', 'No description')}\n"
        else:
            preview += "- Basic functionality (will be customized)\n"
        
        preview += f"""
**Template:** {server_info.get('template', 'custom')}
**Port:** {server_info.get('port', 7860)}

Ready to build this server?
"""
        
        return preview
    
    def show_build_progress(self, steps: List[str], current_step: int) -> str:
        """Show build progress"""
        
        progress = "## 🔧 Building Your Server...\n\n"
        
        for i, step in enumerate(steps):
            if i < current_step:
                progress += f"✅ {step}\n"
            elif i == current_step:
                progress += f"🔄 {step} (in progress)\n"
            else:
                progress += f"⏳ {step}\n"
        
        return progress
    
    def show_server_ready(self, server_info: Dict[str, Any]) -> str:
        """Show server ready message"""
        
        message = f"""
## 🎉 Server Ready!

Your **{server_info.get('name', 'server')}** is now ready to use!

**Location:** `{server_info.get('directory', 'unknown')}`
**Access URL:** http://localhost:{server_info.get('port', 7860)}

### Next Steps:
1. **Test it locally:** The server should start automatically
2. **Customize further:** Edit the generated code if needed
3. **Deploy it:** Put your server online when ready
4. **Share it:** Let others use your creation

### What you can say:
- "Start the server" 
- "Show me the code"
- "Deploy to Hugging Face"
- "Create another server"

Great work! 🚀
"""
        
        return message
    
    def _change_agent_mode(self, selected_mode: str) -> Tuple[List[Dict], Dict[str, Any], str, str]:
        """Change the agent mode between MCP Agent and Agent Builder"""
        
        self.current_agent_mode = selected_mode
        
        if selected_mode == "Agent Builder" and self.agent_builder is not None:
            # Switch to Agent Builder
            self.agent = self.agent_builder
            
            initial_message = [
                {"role": "assistant", "content": "🤖 Switched to Agent Builder mode! I can help you create custom Gradio agents with AI capabilities. Each agent I create will have its own HuggingFace model configuration. What kind of agent would you like to build?"}
            ]
            agent_info = "**Agent Builder**: Create custom Gradio agents with AI capabilities"
            
        else:
            # Switch back to MCP Agent (or fallback if Agent Builder not available)
            self.agent = self.mcp_agent
            self.current_agent_mode = "MCP Agent"  # Ensure consistency
            initial_message = [
                {"role": "assistant", "content": "👋 Switched to MCP Agent mode! I'm here to help you build MCP servers using the Gradio MCP Playground. What would you like to create?"}
            ]
            agent_info = "**MCP Agent**: Build and manage MCP servers using Gradio MCP Playground"
        
        # Clear conversation context for new mode
        self.conversation_history = []
        
        return initial_message, {}, "**Suggestions will appear here based on our conversation...**", agent_info
