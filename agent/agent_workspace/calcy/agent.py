#!/usr/bin/env python3
"""Generated agent: calcy"""

import sys
import os
import logging

# Setup logging for the agent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calcy")

try:
    logger.info("Starting agent: calcy")
    
    # User's agent code
    """
    🧮 Calculator Pro Agent

    AGENT_INFO = {
        "name": "🧮 Calculator Pro",
        "description": "Advanced mathematical operations with scientific functions and expression evaluation",
        "category": "Productivity",
        "difficulty": "Beginner",
        "features": [
            "Basic arithmetic operations (add, subtract, multiply, divide)",
            "Advanced math functions (power, square root, trigonometry)",
            "Expression evaluation with mathematical constants",
            "Calculation history tracking",
            "Error handling and validation"
        ],
        "version": "1.0.0",
        "author": "Agent System"
    }
    """

    import gradio as gr
    import math
    import numpy as np
    import os
    from datetime import datetime

    class CalculatorAgent:
        def __init__(self):
            self.history = []
        
        def calculate(self, operation, a, b=None, expression=None):
            """Enhanced calculator with multiple operation modes"""
            timestamp = datetime.now().strftime("%H:%M:%S")
        
            try:
                if operation == "Expression":
                    # Safe expression evaluation
                    if expression:
                        # Replace common math functions
                        safe_expr = expression.replace('^', '**')
                        allowed_names = {
                            k: v for k, v in math.__dict__.items() if not k.startswith("__")
                        }
                        allowed_names.update({"abs": abs, "round": round, "pow": pow})
                    
                        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
                        self.history.append(f"[{timestamp}] {expression} = {result}")
                        return result, "\n".join(self.history[-10:])
                    else:
                        return "Please enter an expression", "\n".join(self.history[-10:])
            
                # Standard operations
                if b is None and operation not in ["Square Root", "Factorial", "Sin", "Cos", "Tan", "Log"]:
                    return "Please provide both numbers", "\n".join(self.history[-10:])
            
                if operation == "Add":
                    result = a + b
                elif operation == "Subtract":
                    result = a - b
                elif operation == "Multiply":
                    result = a * b
                elif operation == "Divide":
                    result = a / b if b != 0 else "Error: Division by zero"
                elif operation == "Power":
                    result = a ** b
                elif operation == "Square Root":
                    result = math.sqrt(a) if a >= 0 else "Error: Negative square root"
                elif operation == "Factorial":
                    result = math.factorial(int(a)) if a >= 0 and a == int(a) else "Error: Invalid factorial"
                elif operation == "Sin":
                    result = math.sin(math.radians(a))
                elif operation == "Cos":
                    result = math.cos(math.radians(a))
                elif operation == "Tan":
                    result = math.tan(math.radians(a))
                elif operation == "Log":
                    result = math.log10(a) if a > 0 else "Error: Invalid logarithm"
                else:
                    result = "Unknown operation"
            
                # Add to history
                if operation != "Expression":
                    if b is not None:
                        self.history.append(f"[{timestamp}] {a} {operation} {b} = {result}")
                    else:
                        self.history.append(f"[{timestamp}] {operation}({a}) = {result}")
            
                return result, "\n".join(self.history[-10:])
            
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self.history.append(f"[{timestamp}] Error: {str(e)}")
                return error_msg, "\n".join(self.history[-10:])

    # Create calculator instance
    calc = CalculatorAgent()

    # Enhanced Gradio interface
    with gr.Blocks(title="🧮 Calculator Pro Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🧮 Calculator Pro Agent
        **Advanced mathematical operations with history tracking**
    
        Supports basic arithmetic, scientific functions, and expression evaluation.
        """)
    
        with gr.Row():
            with gr.Column(scale=2):
                operation = gr.Dropdown(
                    choices=["Add", "Subtract", "Multiply", "Divide", "Power", 
                            "Square Root", "Factorial", "Sin", "Cos", "Tan", "Log", "Expression"], 
                    label="Operation",
                    value="Add"
                )
            
                with gr.Row():
                    num1 = gr.Number(label="First Number", value=0)
                    num2 = gr.Number(label="Second Number", value=0)
            
                expression_input = gr.Textbox(
                    label="Expression (for Expression mode)",
                    placeholder="e.g., 2*3 + sqrt(16) - log(100)",
                    visible=False
                )
            
                calculate_btn = gr.Button("🔢 Calculate", variant="primary", size="lg")
        
            with gr.Column(scale=1):
                result_output = gr.Textbox(label="Result", lines=2, interactive=False)
                history_output = gr.Textbox(label="Recent History", lines=8, interactive=False)
                clear_btn = gr.Button("🧹 Clear History", size="sm")
    
        def toggle_expression_input(operation):
            return gr.update(visible=(operation == "Expression"))
    
        def clear_history():
            calc.history.clear()
            return "", ""
    
        operation.change(toggle_expression_input, inputs=[operation], outputs=[expression_input])
        calculate_btn.click(calc.calculate, 
                           inputs=[operation, num1, num2, expression_input], 
                           outputs=[result_output, history_output])
        clear_btn.click(clear_history, outputs=[result_output, history_output])

    if __name__ == "__main__":
        interface.launch(server_port=int(os.environ.get('AGENT_PORT', 7860)))

    
    logger.info("Agent calcy started successfully")
    
except Exception as e:
    logger.error(f"Agent calcy failed to start: {e}")
    sys.exit(1)
