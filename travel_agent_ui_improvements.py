"""
Improvements for Travel Agent UI to match gradio-mcp-playground behavior

Key changes needed:
1. Show user prompt immediately when they hit enter
2. Display agent's thinking process clearly
3. Format tool calls and responses better
"""

import gradio as gr
from typing import List, Generator, Optional, Tuple

def enhanced_interact_with_agent(
    prompt: str, 
    chat_history: List[List[str]],
    files: Optional[List] = None
) -> Generator[List[List[str]], None, None]:
    """
    Enhanced interaction that shows user prompt immediately and streams agent thinking
    """
    # 1. IMMEDIATELY show the user's prompt in the chat
    if prompt.strip():
        chat_history.append([prompt, None])
        yield chat_history
    
    # 2. Start showing "thinking" indicator
    chat_history[-1][1] = "🤔 Thinking..."
    yield chat_history
    
    # 3. Stream agent responses with clear formatting
    full_response = ""
    for message in stream_agent_response(prompt, files):
        if message.type == "thought":
            # Show thinking process in italics
            full_response = f"*💭 {message.content}*\n\n"
            chat_history[-1][1] = full_response
            yield chat_history
        
        elif message.type == "tool_call":
            # Format tool calls clearly
            full_response += f"🔧 **Using tool:** `{message.tool_name}`\n"
            full_response += f"📥 **Input:** `{message.tool_input}`\n\n"
            chat_history[-1][1] = full_response
            yield chat_history
        
        elif message.type == "tool_response":
            # Show tool response in a collapsible format
            full_response += f"📤 **Result:**\n```\n{message.content[:500]}"
            if len(message.content) > 500:
                full_response += "\n... (truncated)"
            full_response += "\n```\n\n"
            chat_history[-1][1] = full_response
            yield chat_history
        
        elif message.type == "final_answer":
            # Show final answer clearly
            full_response += f"✅ **Answer:**\n{message.content}"
            chat_history[-1][1] = full_response
            yield chat_history

def create_enhanced_gradio_interface(agent):
    """
    Create an enhanced Gradio interface with better UX
    """
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🌍 Travel Agent Assistant")
        
        # Chat interface
        chatbot = gr.Chatbot(
            label="Chat",
            elem_id="chatbot",
            height=600,
            show_copy_button=True,
            likeable=True,
            avatar_images=("👤", "🤖")
        )
        
        # Message input with submit on enter
        with gr.Row():
            msg = gr.Textbox(
                label="Message",
                placeholder="Ask me about travel planning...",
                lines=1,
                max_lines=5,
                elem_id="message-input",
                autofocus=True,  # Focus on load
                show_label=False,
                container=False,
                scale=9
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        # Optional file upload
        with gr.Accordion("Upload Files", open=False):
            file_upload = gr.File(
                label="Upload travel documents",
                file_count="multiple",
                file_types=["image", "pdf", "text"]
            )
        
        # Status indicators
        with gr.Row():
            status = gr.Textbox(
                label="Status",
                value="Ready",
                interactive=False,
                scale=8
            )
            clear_btn = gr.Button("Clear Chat", scale=2)
        
        # Define interactions
        def user_submit(message, history, files):
            """Handle user submission"""
            if not message.strip():
                return "", history, "Please enter a message"
            
            # Clear input immediately for better UX
            return "", list(enhanced_interact_with_agent(message, history, files)), "Processing..."
        
        def clear_chat():
            """Clear the chat history"""
            return [], "Chat cleared"
        
        # Wire up events
        # Submit on Enter key
        msg.submit(
            user_submit,
            inputs=[msg, chatbot, file_upload],
            outputs=[msg, chatbot, status],
            queue=True
        )
        
        # Submit on button click
        submit_btn.click(
            user_submit,
            inputs=[msg, chatbot, file_upload],
            outputs=[msg, chatbot, status],
            queue=True
        )
        
        # Clear button
        clear_btn.click(
            clear_chat,
            outputs=[chatbot, status],
            queue=False
        )
        
        # Auto-focus message input after submission
        msg.submit(
            lambda: gr.update(autofocus=True),
            outputs=[msg]
        )
    
    return demo

# CSS improvements for better UX
custom_css = """
#message-input {
    font-size: 16px !important;
}

#chatbot {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

#chatbot .message {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 4px 0;
}

#chatbot .user {
    background-color: #e3f2fd;
}

#chatbot .bot {
    background-color: #f5f5f5;
}

/* Thinking animation */
@keyframes thinking {
    0% { opacity: 0.3; }
    50% { opacity: 1; }
    100% { opacity: 0.3; }
}

.thinking {
    animation: thinking 1.5s ease-in-out infinite;
}

/* Code blocks */
#chatbot pre {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
}

/* Tool calls */
#chatbot .tool-call {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 8px 12px;
    margin: 8px 0;
}
"""

# Enhanced message formatting functions
def format_thought_process(step_info):
    """Format agent thinking for display"""
    formatted = "**🧠 Thinking Process:**\n\n"
    
    if "reasoning" in step_info:
        formatted += f"💭 *{step_info['reasoning']}*\n\n"
    
    if "plan" in step_info:
        formatted += "**📋 Plan:**\n"
        for i, item in enumerate(step_info['plan'], 1):
            formatted += f"{i}. {item}\n"
        formatted += "\n"
    
    return formatted

def format_tool_call(tool_name, tool_input, tool_output):
    """Format tool calls for better readability"""
    formatted = f"""
<div class="tool-call">
<strong>🔧 Tool:</strong> <code>{tool_name}</code><br>
<strong>📥 Input:</strong>
<pre>{tool_input}</pre>
<strong>📤 Output:</strong>
<pre>{tool_output[:500]}{'...' if len(tool_output) > 500 else ''}</pre>
</div>
"""
    return formatted

# Example of how to modify your existing stream_to_gradio function
def enhanced_stream_to_gradio(agent, task_input, files=None):
    """Enhanced version with better formatting"""
    # Show task input immediately
    yield gr.ChatMessage(
        role="user",
        content=task_input
    )
    
    # Show thinking indicator
    thinking_msg = gr.ChatMessage(
        role="assistant", 
        content="🤔 Processing your request..."
    )
    yield thinking_msg
    
    # Process agent steps
    full_response = ""
    current_step = 1
    
    for event in agent.stream(task_input):
        # Extract step information
        step_type = event.get("type", "")
        
        if step_type == "thought":
            # Update with thinking process
            full_response = format_thought_process(event)
            yield gr.ChatMessage(
                role="assistant",
                content=full_response,
                metadata={"step": current_step}
            )
        
        elif step_type == "tool_call":
            # Add tool call to response
            tool_response = format_tool_call(
                event.get("tool_name"),
                event.get("tool_input"),
                event.get("tool_output", "Processing...")
            )
            full_response += tool_response
            yield gr.ChatMessage(
                role="assistant",
                content=full_response,
                metadata={"step": current_step}
            )
        
        elif step_type == "final_answer":
            # Show final answer
            full_response += f"\n\n✅ **Final Answer:**\n{event.get('content')}"
            yield gr.ChatMessage(
                role="assistant",
                content=full_response,
                metadata={"step": current_step, "final": True}
            )
        
        current_step += 1