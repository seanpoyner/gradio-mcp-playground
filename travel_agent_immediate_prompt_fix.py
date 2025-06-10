"""
Fix for Travel Agent to show user prompt immediately on send
"""

import gradio as gr
from typing import List, Generator, Optional

# SOLUTION 1: Modify interact_with_agent to yield immediately
def fixed_interact_with_agent(self, task, chat_history, file_upload):
    """
    Fixed version that shows user message immediately
    """
    # CRITICAL: Show user message IMMEDIATELY
    if task and task.strip():
        # Add user message to history
        chat_history.append([task, None])
        yield chat_history  # This yield is crucial!
        
        # Add thinking indicator
        chat_history[-1][1] = "🤔 Thinking..."
        yield chat_history
    else:
        yield chat_history  # Return unchanged if no task
        return
    
    # Now process with agent
    files = [file_upload.name] if file_upload else None
    
    try:
        # Initialize response
        full_response = ""
        
        # Stream from agent
        for response in stream_to_gradio(self.agent, task, files=files):
            # Accumulate response
            if hasattr(response, 'content'):
                full_response += response.content + "\n"
            else:
                full_response += str(response) + "\n"
            
            # Update the assistant's response
            chat_history[-1][1] = full_response.strip()
            yield chat_history
            
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        chat_history[-1][1] = error_msg
        yield chat_history


# SOLUTION 2: Better launch method with proper event handling
def fixed_launch_method(self, share=False):
    """
    Fixed launch method with immediate prompt display
    """
    with gr.Blocks() as demo:
        gr.Markdown("# Travel Agent Assistant 🌍")
        
        # Chat interface
        chatbot = gr.Chatbot(
            label="Chat",
            height=600,
            show_copy_button=True,
            avatar_images=("👤", "🤖")
        )
        
        # Input row
        with gr.Row():
            msg = gr.Textbox(
                label="Message",
                placeholder="Ask about travel planning...",
                lines=1,
                scale=9,
                autofocus=True
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        # File upload if enabled
        if self.file_upload:
            file = gr.File(label="Upload file", file_types=["image", "pdf", "text"])
        else:
            file = None
        
        # CRITICAL: Handle submission properly
        def user_submit(message, history, file_upload=None):
            """
            Handle user submission with immediate display
            """
            if not message or not message.strip():
                return "", history, history  # Return empty message, unchanged history
            
            # Clear the input immediately
            # Return generator for chat history updates
            return "", history, self.interact_with_agent(message, history, file_upload)
        
        # Set up the submit events
        if self.file_upload:
            # With file upload
            msg.submit(
                user_submit,
                inputs=[msg, chatbot, file],
                outputs=[msg, chatbot, chatbot],  # Note: chatbot appears twice
                queue=True
            )
            
            submit_btn.click(
                user_submit,
                inputs=[msg, chatbot, file],
                outputs=[msg, chatbot, chatbot],
                queue=True
            )
        else:
            # Without file upload
            msg.submit(
                user_submit,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, chatbot],
                queue=True
            )
            
            submit_btn.click(
                user_submit,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, chatbot],
                queue=True
            )
    
    demo.queue()
    demo.launch(share=share)


# SOLUTION 3: Alternative approach using Gradio's built-in chat interface
def alternative_chat_interface(agent, share=False):
    """
    Alternative using gr.ChatInterface which handles prompt display automatically
    """
    def respond(message, history):
        """
        Simple response function that yields updates
        """
        # First yield to show thinking
        yield history + [[message, "🤔 Thinking..."]]
        
        # Process with agent
        full_response = ""
        for chunk in stream_to_gradio(agent, message):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            
            # Update the last message
            yield history + [[message, full_response]]
    
    # Use Gradio's ChatInterface
    demo = gr.ChatInterface(
        fn=respond,
        title="Travel Agent Assistant 🌍",
        description="Ask me anything about travel planning!",
        examples=[
            "Plan a 7-day trip to Japan",
            "What's the best time to visit Paris?",
            "Find budget hotels in New York"
        ],
        theme="soft",
        submit_btn="Send",
        retry_btn=None,
        undo_btn=None,
        clear_btn="Clear"
    )
    
    demo.queue()
    demo.launch(share=share)


# SOLUTION 4: Minimal fix - just ensure interact_with_agent yields immediately
def minimal_fix_for_interact_with_agent(original_method):
    """
    Wrapper to fix any interact_with_agent method
    """
    def fixed_method(self, task, chat_history, file_upload=None):
        # ALWAYS yield user message first
        if task and task.strip():
            chat_history.append([task, None])
            yield chat_history  # CRITICAL LINE
            
            # Show thinking
            chat_history[-1][1] = "🤔 Processing your request..."
            yield chat_history
        
        # Then call original method logic
        # But skip the first append since we already did it
        generator = original_method(self, task, chat_history, file_upload)
        
        # Skip first yield if it's trying to append the same message
        first = True
        for update in generator:
            if first and len(update) > 0 and update[-1][0] == task:
                # Skip duplicate user message
                first = False
                continue
            yield update
    
    return fixed_method


# Example of how to apply the fix in your Gradio_UI.py:
"""
# In your Gradio_UI.py file:

class GradioUI:
    def __init__(self, agent, file_upload=False):
        self.agent = agent
        self.file_upload = file_upload
    
    def interact_with_agent(self, task, chat_history, file_upload):
        # FIX: Yield user message immediately
        if task and task.strip():
            chat_history.append([task, None])
            yield chat_history  # <-- THIS IS THE KEY LINE
            
            chat_history[-1][1] = "🤔 Thinking..."
            yield chat_history
        
        # Rest of your existing logic here...
        files = [file_upload.name] if file_upload else None
        
        # Your agent processing...
        for response in stream_to_gradio(self.agent, task, files=files):
            # Update response
            # ...
            yield chat_history
"""