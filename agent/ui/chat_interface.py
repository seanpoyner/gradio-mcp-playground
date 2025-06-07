"""Chat Interface Component

Provides the main conversational interface for the GMP Agent.
"""

import asyncio
from typing import List, Dict, Any, Tuple, Optional
import gradio as gr


class ChatInterface:
    """Main chat interface for the GMP Agent"""
    
    def __init__(self, agent):
        self.agent = agent
        self.conversation_history = []
        
    def create_interface(self) -> None:
        """Create the chat interface components"""
        
        with gr.Column(scale=1):
            # Chat display area
            self.chatbot = gr.Chatbot(
                label="GMP Agent",
                height=500,
                show_label=True,
                container=True,
                bubble_full_width=False,
                type="messages",
                value=[
                    {"role": "assistant", "content": "👋 Hello! I'm the GMP Agent, your intelligent assistant for building MCP servers. How can I help you today?"}
                ]
            )
            
            with gr.Row():
                # Message input
                self.message_input = gr.Textbox(
                    label="Message",
                    placeholder="Describe what you want to build... (e.g., 'Create a calculator server')",
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
                            "Create a basic calculator server",
                            "Build an image processing pipeline",
                            "Make a text analyzer with sentiment analysis",
                            "Create a data visualization dashboard",
                            "Build a file converter tool",
                            "Help me understand MCP protocol",
                            "Show me available server templates",
                            "How do I deploy my server?"
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
        
        # Set up event handlers
        self._setup_event_handlers()
    
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
    
    async def _handle_message(self, message: str, chat_history: List[Dict]) -> Tuple[List[Dict], str, Dict[str, Any], str]:
        """Handle user message and generate response"""
        
        if not message.strip():
            return chat_history, "", {}, ""
        
        # Add user message to chat
        chat_history.append({"role": "user", "content": message})
        
        try:
            # Process message with agent
            response, metadata = await self.agent.process_message(message)
            
            # Add agent response to chat
            chat_history.append({"role": "assistant", "content": response})
            
            # Update context display
            context_info = {
                "intent": metadata.get("intent", "unknown"),
                "confidence": metadata.get("confidence", 0.0),
                "entities": metadata.get("entities", {}),
                "action": metadata.get("action", "respond")
            }
            
            # Generate suggestions
            suggestions = self._generate_suggestions(metadata)
            
            return chat_history, "", context_info, suggestions
            
        except Exception as e:
            # Handle errors gracefully
            error_response = f"I encountered an error: {str(e)}. Please try rephrasing your request or ask for help."
            chat_history.append({"role": "assistant", "content": error_response})
            
            return chat_history, "", {"error": str(e)}, "Try asking for help or rephrasing your request."
    
    def _handle_example_selection(self, selected_example: str, chat_history: List[Dict]) -> Tuple[List[Dict], str, str, Dict[str, Any], str]:
        """Handle selection of an example prompt"""
        
        if not selected_example:
            return chat_history, "", "", {}, ""
        
        # Set the example as the current message
        return chat_history, selected_example, "", {}, ""
    
    def _clear_conversation(self) -> Tuple[List[Dict], Dict[str, Any], str]:
        """Clear the conversation history"""
        
        self.agent.clear_conversation()
        
        # Return initial state with system message
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
        
        suggestions = "## 💡 What you can do next:\n\n"
        
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