# Travel Agent UI Improvements Implementation Guide

## Overview
This guide shows how to modify your travel agent's Gradio UI to behave more like the gradio-mcp-playground chatbot, with immediate user prompt display, visible thinking process, and better formatted responses.

## Key Changes Needed

### 1. Immediate User Prompt Display

**Current Issue:** User prompt might not appear immediately when they hit enter.

**Solution:** Modify your `interact_with_agent` method in `Gradio_UI.py`:

```python
def interact_with_agent(self, task, chat_history, file_upload):
    """
    Runs the agent on a user task and streams the response.
    """
    # IMMEDIATE FEEDBACK: Show user message right away
    if task.strip():
        chat_history.append([task, None])
        yield chat_history
        
        # Show thinking indicator
        chat_history[-1][1] = "🤔 Processing..."
        yield chat_history
    
    # Then process with agent
    files = [file_upload.name] if file_upload else None
    try:
        # Your existing streaming logic here
        response_generator = stream_to_gradio(self.agent, task, files=files)
        
        accumulated_response = ""
        for response in response_generator:
            # Accumulate and format response
            accumulated_response += format_response(response)
            chat_history[-1][1] = accumulated_response
            yield chat_history
    except Exception as e:
        chat_history[-1][1] = f"❌ Error: {str(e)}"
        yield chat_history
```

### 2. Enhanced Message Formatting

**Current Issue:** Agent thinking and tool calls might not be clearly distinguished.

**Solution:** Enhance your `pull_messages_from_step` function:

```python
def pull_messages_from_step(step_log):
    """
    Extracts ChatMessage objects from a step log.
    """
    messages = []
    
    # Format step header with clear visual indicators
    if step_number := step_log.get("step"):
        messages.append(ChatMessage(
            role="assistant",
            content=f"### 🔄 Step {step_number}",
            metadata={"title": "step_number"}
        ))
    
    # Format reasoning/thinking with visual cues
    if model_output := (
        step_log.get("response") or 
        step_log.get("model_output") or 
        step_log.get("output")
    ):
        # Clean up the output
        output = clean_output(model_output)
        
        # Add thinking emoji and italics for reasoning
        if "thinking" in output.lower() or "reasoning" in output.lower():
            content = f"💭 *{output}*"
        else:
            content = output
            
        messages.append(ChatMessage(
            role="assistant",
            content=content,
            metadata={"title": "reasoning"}
        ))
    
    # Format tool calls with better structure
    if tool_calls := step_log.get("tool_calls"):
        for tool_call in tool_calls:
            # Tool call header
            tool_content = f"🔧 **Tool:** `{tool_call.get('tool_name', 'unknown')}`\n"
            
            # Tool input (formatted as code block)
            if tool_input := tool_call.get("input"):
                tool_content += f"📥 **Input:**\n```json\n{json.dumps(tool_input, indent=2)}\n```\n"
            
            # Tool output (truncated if too long)
            if tool_output := tool_call.get("output"):
                output_str = str(tool_output)
                if len(output_str) > 500:
                    output_str = output_str[:500] + "\n... (truncated)"
                tool_content += f"📤 **Output:**\n```\n{output_str}\n```"
            
            messages.append(ChatMessage(
                role="assistant",
                content=tool_content,
                metadata={"title": "tool_call", "tool_name": tool_call.get('tool_name')}
            ))
    
    # Add execution logs with proper formatting
    if execution_logs := step_log.get("execution_logs"):
        for log in execution_logs:
            log_content = f"📝 **{log.get('type', 'Log')}:** {log.get('content', '')}"
            messages.append(ChatMessage(
                role="assistant",
                content=log_content,
                metadata={"title": "execution_log"}
            ))
    
    # Format errors prominently
    if error := step_log.get("error"):
        messages.append(ChatMessage(
            role="assistant",
            content=f"❌ **Error:** {error}",
            metadata={"title": "error"}
        ))
    
    # Add step metrics in a subtle way
    if any(k in step_log for k in ["input_tokens", "output_tokens", "duration"]):
        metrics = []
        if input_tokens := step_log.get("input_tokens"):
            metrics.append(f"📊 Input tokens: {input_tokens}")
        if output_tokens := step_log.get("output_tokens"):
            metrics.append(f"📊 Output tokens: {output_tokens}")
        if duration := step_log.get("duration"):
            metrics.append(f"⏱️ Duration: {duration:.2f}s")
        
        if metrics:
            messages.append(ChatMessage(
                role="assistant",
                content=" | ".join(metrics),
                metadata={"title": "metrics"}
            ))
    
    return messages
```

### 3. Better Input Handling

**Current Issue:** Input field might not clear or refocus properly.

**Solution:** Update your `launch` method:

```python
def launch(self, share=False):
    """
    Launches the Gradio interface for interacting with the agent.
    """
    with gr.Blocks(css=custom_css) as demo:
        gr.Markdown("# Travel Agent Assistant 🌍")
        
        chat = gr.Chatbot(
            label="Chat History",
            height=600,
            elem_id="chatbot",
            show_copy_button=True,
            avatar_images=("👤", "🤖")
        )
        
        with gr.Row():
            task_input = gr.Textbox(
                label="Your Question",
                placeholder="Ask me anything about travel planning...",
                lines=1,
                elem_id="message-input",
                autofocus=True,
                show_label=False,
                scale=9
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        file_upload = gr.File(
            label="Upload a file",
            visible=self.file_upload,
            elem_id="file-upload"
        )
        
        # Handle submit with immediate feedback
        def handle_submit(task, history, file):
            """Clear input and start processing"""
            if not task.strip():
                return gr.update(), history
            
            # Return empty string to clear input immediately
            return "", self.interact_with_agent(task, history, file)
        
        # Wire up both enter key and button click
        task_input.submit(
            handle_submit,
            inputs=[task_input, chat, file_upload],
            outputs=[task_input, chat],
            queue=True
        ).then(
            # Refocus the input after submission
            lambda: gr.update(autofocus=True),
            outputs=[task_input]
        )
        
        submit_btn.click(
            handle_submit,
            inputs=[task_input, chat, file_upload],
            outputs=[task_input, chat],
            queue=True
        ).then(
            lambda: gr.update(autofocus=True),
            outputs=[task_input]
        )
    
    demo.launch(share=share)
```

### 4. Custom CSS for Better Appearance

Add this CSS to make the chat interface more polished:

```python
custom_css = """
/* Input field styling */
#message-input textarea {
    font-size: 16px !important;
    line-height: 1.5;
}

/* Chat message styling */
#chatbot .message {
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 8px;
}

/* User messages */
#chatbot .user {
    background-color: #e3f2fd;
    margin-left: 20%;
}

/* Assistant messages */
#chatbot .bot {
    background-color: #f5f5f5;
    margin-right: 20%;
}

/* Code blocks */
#chatbot pre {
    background-color: #282c34;
    color: #abb2bf;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 14px;
}

/* Tool call styling */
#chatbot strong {
    color: #1976d2;
}

/* Thinking indicator animation */
@keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
}

.thinking {
    animation: pulse 1.5s ease-in-out infinite;
}

/* Step headers */
#chatbot h3 {
    color: #424242;
    font-size: 14px;
    margin: 16px 0 8px 0;
    font-weight: 500;
}

/* Metrics styling */
#chatbot .message[title="metrics"] {
    font-size: 12px;
    color: #666;
    font-style: italic;
}
"""
```

### 5. Helper Functions

Add these utility functions to improve formatting:

```python
def clean_output(text):
    """Clean up model output for display"""
    # Remove common XML-style tags
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    text = re.sub(r'<(\w+)>', '', text)
    text = re.sub(r'</(\w+)>', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

def format_response(response):
    """Format different types of responses"""
    if isinstance(response, ChatMessage):
        content = response.content
        
        # Add visual indicators based on metadata
        if response.metadata.get("title") == "reasoning":
            return f"💭 *{content}*\n\n"
        elif response.metadata.get("title") == "tool_call":
            return f"🔧 {content}\n\n"
        elif response.metadata.get("title") == "error":
            return f"❌ {content}\n\n"
        else:
            return f"{content}\n\n"
    
    return str(response)
```

## Implementation Steps

1. **Backup your current `Gradio_UI.py`**
2. **Add the custom CSS** to your file
3. **Update the `interact_with_agent` method** to show user prompts immediately
4. **Enhance the `pull_messages_from_step` function** with better formatting
5. **Update the `launch` method** with better input handling
6. **Add the helper functions** for cleaning and formatting
7. **Test thoroughly** with various prompts

## Expected Results

After implementing these changes:
- ✅ User prompts appear immediately when hitting enter
- ✅ Input field clears and refocuses automatically
- ✅ Agent thinking process is clearly visible
- ✅ Tool calls are well-formatted and easy to read
- ✅ Errors are prominently displayed
- ✅ Overall chat experience is more responsive and polished

## Additional Enhancements

Consider adding:
- **Typing indicators** while agent is thinking
- **Collapsible sections** for long tool outputs
- **Copy buttons** for code blocks
- **Syntax highlighting** for code outputs
- **Progress indicators** for long-running operations