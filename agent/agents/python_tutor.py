"""
python_tutor

Build a Python tutor agent

AGENT_INFO = {
    "name": "python_tutor",
    "description": "Build a Python tutor agent",
    "category": "Tools/Utilities",
    "difficulty": "Intermediate",
    "features": [],
    "version": "1.0.0",
    "author": "Agent Builder System"
}
"""

import gradio as gr
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import asyncio

# Hugging Face integration
try:
    from huggingface_hub import InferenceClient
    HAS_HF_INFERENCE = True
except ImportError:
    HAS_HF_INFERENCE = False
    print("Warning: huggingface_hub not installed. Install with: pip install huggingface_hub")

# Import secure storage for HF tokens
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from gradio_mcp_playground.secure_storage import get_secure_storage
except ImportError:
    get_secure_storage = lambda: None


class PythonTutorAgent:
    """Main agent class implementing the core functionality"""
    
    def __init__(self):
        self.system_prompt = """You are an expert Python programming tutor with deep knowledge of Python syntax, best practices, and common patterns. 

Your role is to:
- Explain Python concepts clearly and concisely
- Provide practical code examples that demonstrate concepts
- Help debug code and explain errors
- Suggest best practices and pythonic approaches
- Guide learners from beginner to advanced topics
- Use analogies and real-world examples when helpful

Always format code examples in markdown code blocks with proper syntax highlighting.
Be encouraging and patient with learners at all levels."""
        
        self.conversation_history = []
        self.agent_state = {
            "initialized": True,
            "last_activity": datetime.now(),
            "user_preferences": {},
            "session_data": {}
        }
        
        # Initialize HF client
        self.hf_client = None
        self.model_name = "Qwen/Qwen2.5-Coder-32B-Instruct"  # Default model
        self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the LLM client with HF token"""
        if not HAS_HF_INFERENCE:
            print("HF Inference not available - responses will be static")
            return
            
        try:
            # Get secure storage
            secure_storage = get_secure_storage()
            if not secure_storage:
                print("Secure storage not available - using static responses")
                return
                
            # Get HF token
            hf_token = secure_storage.retrieve_key("huggingface", "token")
            if not hf_token:
                print("No HF token found - using static responses")
                return
                
            # Initialize inference client
            self.hf_client = InferenceClient(
                model=self.model_name,
                token=hf_token
            )
            print(f"Connected to {self.model_name} via Inference API")
            
        except Exception as e:
            print(f"Failed to initialize LLM: {e}")
            self.hf_client = None
        
    def process_request(self, user_input: str, *args) -> Tuple[str, Any]:
        """Process user request and generate response"""
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            })
            
            # Generate response based on system prompt and context
            response = self._generate_response(user_input, *args)
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now()
            })
            
            # Update state
            self.agent_state["last_activity"] = datetime.now()
            
            return response, self.agent_state
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            return error_msg, self.agent_state
    
    def _generate_response(self, user_input: str, *args) -> str:
        """Generate response using the agent's system prompt"""
        if self.hf_client:
            # Use LLM for response
            return self._generate_llm_response(user_input)
        else:
            # Fallback to static response
            return self._create_contextual_response(user_input)
    
    def _generate_llm_response(self, user_input: str) -> str:
        """Generate response using HF Inference API"""
        try:
            # Build conversation context
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add recent conversation history
            for msg in self.conversation_history[-4:]:  # Last 4 messages
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = self.hf_client.chat_completion(
                messages=messages,
                max_tokens=1024,  # More tokens for detailed explanations
                temperature=0.7,
                top_p=0.9
            )
            
            # Extract response text
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"LLM generation error: {e}")
            # Fallback to static response
            return self._create_contextual_response(user_input)
    
    def _create_contextual_response(self, user_input: str) -> str:
        """Create a contextual response based on the agent's specialization"""
        # Fallback response when LLM is not available
        response = f"""I understand you're asking about: {user_input}

As a Python tutor, I can help you with:
- Python syntax and concepts
- Code examples and best practices
- Debugging and error fixing
- Project structure and design patterns

(Note: Running in static mode. For AI-powered responses, ensure HF token is configured)"""
        
        return response
    
    def clear_conversation(self) -> None:
        """Clear the conversation history"""
        self.conversation_history = []
        self.agent_state["last_activity"] = datetime.now()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history


# Create agent instance
agent_instance = PythonTutorAgent()

# Enhanced Gradio interface
with gr.Blocks(title="Python Tutor Agent", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # 🐍 Python Tutor Agent
    **Your AI-powered Python programming assistant**
    
    I can help you learn Python, debug code, understand concepts, and write better programs!
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                show_label=True,
                container=True
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask me anything about Python...",
                    lines=3,
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
        
        with gr.Column(scale=1):
            clear_btn = gr.Button("Clear Conversation", variant="secondary", size="lg")
            
            gr.Markdown("## 📊 Agent Status")
            status_display = gr.JSON(value=agent_instance.agent_state, label="Status")
            
            gr.Markdown("## 💡 Quick Examples")
            gr.Examples(
                examples=[
                    "How do I create a list in Python?",
                    "Explain Python decorators with examples",
                    "What's the difference between list and tuple?",
                    "How do I handle exceptions in Python?",
                    "Show me an example of a class with inheritance",
                    "What are Python's best practices for function naming?",
                    "How do I work with files in Python?",
                    "Explain list comprehensions with examples"
                ],
                inputs=user_input
            )
            
            # Show LLM status
            llm_status = "🟢 AI-Powered" if agent_instance.hf_client else "🔴 Static Mode"
            gr.Markdown(f"### LLM Status: {llm_status}")
    
    def handle_message(message, history):
        if not message.strip():
            return history, "", agent_instance.agent_state
        
        response, state = agent_instance.process_request(message)
        
        # Update history in Gradio format
        history.append([message, response])
        
        return history, "", state
    
    def clear_conversation():
        agent_instance.clear_conversation()
        return [], agent_instance.agent_state
    
    # Wire up the events
    send_btn.click(
        handle_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input, status_display]
    )
    
    user_input.submit(
        handle_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input, status_display]
    )
    
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot, status_display]
    )

if __name__ == "__main__":
    interface.launch(
        server_port=int(os.environ.get('AGENT_PORT', 7860)),
        share=False,
        server_name="0.0.0.0"
    )