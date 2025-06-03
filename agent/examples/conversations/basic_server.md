# Example Conversation: Building a Basic Server

This example shows how to build a simple calculator server using the GMP Agent.

## Conversation Flow

### User Request
```
User: Create a basic calculator server
```

### Agent Response
```
Agent: I'll help you create a calculator server! I found a perfect template that includes:

- Basic arithmetic operations (+, -, *, /)
- Mathematical functions (sin, cos, sqrt, etc.)
- Expression evaluation with error handling
- Clean Gradio interface

Would you like me to:
1. Create a basic calculator with arithmetic only
2. Create an advanced calculator with scientific functions
3. Create a multi-tab calculator with different operation types

Which option interests you?
```

### User Choice
```
User: Create option 2 - the advanced calculator
```

### Agent Building Process
```
Agent: Perfect! I'm creating your advanced calculator server with:

✅ Basic arithmetic operations
✅ Scientific functions (sin, cos, tan, log, sqrt)
✅ Constants (pi, e)
✅ Expression parsing and validation
✅ Error handling for invalid expressions
✅ Clean Gradio interface with examples

Building your server...

[Progress indicators showing file generation]

✅ Calculator server created successfully!

**Location:** ./calculator-server/
**Port:** 7860
**Files created:**
- app.py (main application)
- requirements.txt (dependencies)
- README.md (documentation)
- config.json (configuration)

**Next steps:**
1. Test locally: `cd calculator-server && python app.py`
2. Customize further: Tell me what you'd like to modify
3. Deploy online: "Deploy to Hugging Face Spaces"

Your calculator is ready to use! 🚀
```

### User Testing
```
User: Start the server for me
```

### Agent Response
```
Agent: Starting your calculator server...

🟢 Server is now running!
📍 Access it at: http://localhost:7860

The server includes:
- **Basic Operations**: +, -, *, /, ^
- **Scientific Functions**: sin, cos, tan, log, sqrt, abs
- **Constants**: pi, e
- **Examples**: Pre-filled with sample calculations

**Test it out with:**
- `2 + 3 * 4` (basic arithmetic)
- `sin(pi/2)` (trigonometric)
- `sqrt(16) + log(10)` (mixed functions)

Try entering an expression and see the results! Let me know if you'd like any modifications.
```

### User Customization
```
User: Add a history feature that shows the last 10 calculations
```

### Agent Enhancement
```
Agent: Great idea! I'm adding a calculation history feature to your calculator.

Adding:
✅ History storage for last 10 calculations
✅ History display panel below the calculator
✅ Clear history button
✅ Timestamp for each calculation
✅ Click to reuse previous expressions

The history will show:
- Expression entered
- Result calculated
- Timestamp
- Quick "Use Again" button

Updated files:
- app.py (added history functionality)
- Enhanced UI with history panel

Your calculator now has calculation history! The server will restart automatically to apply changes.

**New features:**
- See your last 10 calculations
- Click any previous calculation to reuse it
- Clear history when needed
- Timestamps for reference

Test the new history feature and let me know what you think!
```

## Generated Files

### app.py
```python
"""Advanced Calculator MCP Server

A calculator with basic arithmetic and scientific functions, plus calculation history.
"""

import gradio as gr
import math
import re
from datetime import datetime
from typing import List, Tuple

# Global history storage
calculation_history: List[Tuple[str, str, str]] = []

def calculate(expression: str) -> Tuple[str, List[List[str]]]:
    """Evaluate a mathematical expression and update history.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Tuple of (result, updated_history)
    """
    global calculation_history
    
    if not expression.strip():
        return "Please enter an expression", format_history()
    
    try:
        # Clean the expression
        clean_expr = expression.strip()
        
        # Define allowed names for safe evaluation
        allowed_names = {
            k: v for k, v in math.__dict__.items() 
            if not k.startswith("__")
        }
        allowed_names.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max
        })
        
        # Evaluate the expression
        result = eval(clean_expr, {"__builtins__": {}}, allowed_names)
        result_str = str(result)
        
        # Add to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        calculation_history.append((clean_expr, result_str, timestamp))
        
        # Keep only last 10 calculations
        if len(calculation_history) > 10:
            calculation_history = calculation_history[-10:]
        
        return result_str, format_history()
        
    except ZeroDivisionError:
        return "Error: Division by zero", format_history()
    except NameError as e:
        return f"Error: Unknown function or variable", format_history()
    except SyntaxError:
        return "Error: Invalid syntax", format_history()
    except Exception as e:
        return f"Error: {str(e)}", format_history()

def format_history() -> List[List[str]]:
    """Format calculation history for display"""
    if not calculation_history:
        return [["No calculations yet", "", ""]]
    
    return [
        [expr, result, time] 
        for expr, result, time in reversed(calculation_history)
    ]

def clear_history() -> Tuple[str, List[List[str]]]:
    """Clear calculation history"""
    global calculation_history
    calculation_history = []
    return "History cleared", format_history()

def use_previous_calculation(evt: gr.SelectData) -> str:
    """Use a previous calculation"""
    if evt.index[0] < len(calculation_history):
        # Get the expression from the selected row
        selected_calc = list(reversed(calculation_history))[evt.index[0]]
        return selected_calc[0]  # Return the expression
    return ""

# Create the Gradio interface
with gr.Blocks(title="Advanced Calculator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧮 Advanced Calculator")
    gr.Markdown("Enter mathematical expressions using basic operations and scientific functions.")
    
    with gr.Row():
        with gr.Column(scale=2):
            # Calculator input
            expression_input = gr.Textbox(
                label="Expression",
                placeholder="Enter expression (e.g., sin(pi/2), sqrt(16), 2+3*4)",
                lines=1
            )
            
            with gr.Row():
                calculate_btn = gr.Button("Calculate", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")
            
            # Result display
            result_output = gr.Textbox(
                label="Result",
                interactive=False,
                lines=1
            )
        
        with gr.Column(scale=1):
            # Examples and help
            gr.Markdown("""
            ### Examples:
            - `2 + 3 * 4`
            - `sin(pi/2)`
            - `sqrt(16) + log(10)`
            - `pow(2, 8)`
            - `abs(-5) + max(1,2,3)`
            
            ### Available Functions:
            - **Basic**: +, -, *, /, **, %
            - **Trig**: sin, cos, tan, asin, acos, atan
            - **Log**: log, log10, log2, exp
            - **Other**: sqrt, abs, ceil, floor, round
            - **Constants**: pi, e
            """)
    
    # History section
    gr.Markdown("## 📜 Calculation History")
    
    with gr.Row():
        clear_history_btn = gr.Button("🗑️ Clear History", size="sm")
    
    history_display = gr.Dataframe(
        headers=["Expression", "Result", "Time"],
        datatype=["str", "str", "str"],
        value=format_history(),
        interactive=False,
        wrap=True,
        height=200
    )
    
    # Event handlers
    calculate_btn.click(
        fn=calculate,
        inputs=[expression_input],
        outputs=[result_output, history_display]
    )
    
    expression_input.submit(
        fn=calculate,
        inputs=[expression_input],
        outputs=[result_output, history_display]
    )
    
    clear_btn.click(
        fn=lambda: "",
        outputs=[expression_input]
    )
    
    clear_history_btn.click(
        fn=clear_history,
        outputs=[result_output, history_display]
    )
    
    history_display.select(
        fn=use_previous_calculation,
        outputs=[expression_input]
    )

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port=7860,
        mcp_server=True,
        share=False,
        show_api=False
    )
```

### requirements.txt
```
gradio>=4.44.0
mcp>=1.0.0
```

### README.md
```markdown
# Advanced Calculator MCP Server

A powerful calculator server with scientific functions and calculation history.

## Features

- **Basic Arithmetic**: +, -, *, /, **, %
- **Scientific Functions**: sin, cos, tan, log, sqrt, etc.
- **Calculation History**: Last 10 calculations with timestamps
- **Error Handling**: Graceful handling of invalid expressions
- **MCP Integration**: Ready for AI model integration

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

Access at: http://localhost:7860

## Examples

- `2 + 3 * 4` → 14
- `sin(pi/2)` → 1.0
- `sqrt(16) + log(10)` → 6.302585092994046
- `pow(2, 8)` → 256
```

## Key Learning Points

1. **Progressive Enhancement**: Started simple, added features incrementally
2. **User Feedback**: Agent responded to specific user requests for customization
3. **Error Handling**: Comprehensive error management for edge cases
4. **UI Design**: Clean, intuitive interface with helpful examples
5. **Documentation**: Complete documentation and setup instructions

This conversation demonstrates how the GMP Agent can build sophisticated servers through natural conversation and iterative enhancement.