# Fix for Immediate Prompt Display in Travel Agent

## The Problem
Your user prompt doesn't show until the agent finishes processing because the `interact_with_agent` method doesn't yield the chat history immediately after adding the user message.

## The Solution

In your `Gradio_UI.py` file, locate the `interact_with_agent` method and modify it like this:

```python
def interact_with_agent(self, task, chat_history, file_upload):
    """
    Runs the agent on a user task and streams the response.
    """
    # FIX: Add these lines at the very beginning
    if task and task.strip():
        # Add user message to chat history
        chat_history.append([task, None])
        yield chat_history  # <-- THIS IS THE CRITICAL LINE!
        
        # Show thinking indicator
        chat_history[-1][1] = "🤔 Thinking..."
        yield chat_history
    else:
        # If no task, just return current history
        yield chat_history
        return
    
    # YOUR EXISTING CODE continues here...
    files = [file_upload.name] if file_upload else None
    
    # Rest of your implementation...
```

## Why This Works

1. **Immediate Yield**: The first `yield chat_history` shows the user message instantly
2. **Thinking Indicator**: The second yield shows a thinking message while processing
3. **Streaming Updates**: Subsequent yields update the assistant's response

## Complete Example

Here's a complete working example of how your method should look:

```python
def interact_with_agent(self, task, chat_history, file_upload):
    """
    Runs the agent on a user task and streams the response.
    """
    # STEP 1: Show user message immediately
    if not task or not task.strip():
        yield chat_history
        return
    
    # Add user message
    chat_history.append([task, None])
    yield chat_history  # <-- Show user message NOW
    
    # STEP 2: Show thinking indicator
    chat_history[-1][1] = "🤔 Processing your request..."
    yield chat_history
    
    # STEP 3: Process with agent
    files = [file_upload.name] if file_upload else None
    
    try:
        # Initialize response accumulator
        accumulated_response = ""
        
        # Stream responses from agent
        for response in stream_to_gradio(self.agent, task, files=files):
            # Extract content based on response type
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict) and 'content' in response:
                content = response['content']
            else:
                content = str(response)
            
            # Accumulate response
            if content:
                accumulated_response += content + "\n"
            
            # Update chat with accumulated response
            chat_history[-1][1] = accumulated_response.strip()
            yield chat_history
            
    except Exception as e:
        # Show error
        chat_history[-1][1] = f"❌ Error: {str(e)}"
        yield chat_history
```

## Alternative: Using gr.ChatInterface

If the above doesn't work, you can switch to Gradio's built-in `ChatInterface` which handles this automatically:

```python
def launch(self, share=False):
    """
    Launches the Gradio interface using ChatInterface.
    """
    def chat_fn(message, history):
        """Chat function that yields updates"""
        # Process with your agent
        full_response = ""
        
        for chunk in stream_to_gradio(self.agent, message):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            
            # Yield updated history
            yield history + [[message, full_response]]
    
    # Create interface
    demo = gr.ChatInterface(
        fn=chat_fn,
        title="Travel Agent Assistant 🌍",
        description="Ask me anything about travel!",
        theme="soft"
    )
    
    demo.queue()
    demo.launch(share=share)
```

## Testing

After making this change:
1. Run your app
2. Type a message and hit Enter
3. You should see your message appear immediately
4. Then see "🤔 Thinking..." 
5. Then see the agent's response stream in

The key is that first `yield chat_history` right after appending the user message!