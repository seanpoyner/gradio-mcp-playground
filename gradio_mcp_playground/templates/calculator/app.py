"""Calculator - Multi-Tool Gradio MCP Server

A calculator with multiple mathematical tools exposed as MCP functions.
"""

import math

import gradio as gr


def basic_calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2 * 3")

    Returns:
        Result of the calculation or error message
    """
    try:
        # Create a safe namespace with math functions
        safe_dict = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        }

        # Add math module functions
        for name in dir(math):
            if not name.startswith("_"):
                safe_dict[name] = getattr(math, name)

        # Evaluate the expression
        result = eval(expression, safe_dict)
        return f"Result: {result}"

    except Exception as e:
        return f"Error: {str(e)}"


def quadratic_solver(a: float, b: float, c: float) -> str:
    """Solve quadratic equation ax² + bx + c = 0.

    Args:
        a: Coefficient of x²
        b: Coefficient of x
        c: Constant term

    Returns:
        Solutions to the quadratic equation
    """
    if a == 0:
        if b == 0:
            return "Error: Not a valid equation (a=0 and b=0)"
        else:
            # Linear equation: bx + c = 0
            x = -c / b
            return f"Linear equation solution: x = {x}"

    # Calculate discriminant
    discriminant = b**2 - 4 * a * c

    if discriminant > 0:
        # Two real solutions
        x1 = (-b + math.sqrt(discriminant)) / (2 * a)
        x2 = (-b - math.sqrt(discriminant)) / (2 * a)
        return f"Two real solutions: x₁ = {x1:.4f}, x₂ = {x2:.4f}"
    elif discriminant == 0:
        # One real solution
        x = -b / (2 * a)
        return f"One real solution: x = {x:.4f}"
    else:
        # Complex solutions
        real_part = -b / (2 * a)
        imag_part = math.sqrt(-discriminant) / (2 * a)
        return f"Complex solutions: x₁ = {real_part:.4f} + {imag_part:.4f}i, x₂ = {real_part:.4f} - {imag_part:.4f}i"


def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between different units.

    Args:
        value: Numeric value to convert
        from_unit: Source unit
        to_unit: Target unit

    Returns:
        Converted value or error message
    """
    # Define conversion factors to base units
    conversions = {
        # Length (base: meters)
        "m": 1,
        "km": 1000,
        "cm": 0.01,
        "mm": 0.001,
        "ft": 0.3048,
        "in": 0.0254,
        "mi": 1609.34,
        # Weight (base: kg)
        "kg": 1,
        "g": 0.001,
        "mg": 0.000001,
        "lb": 0.453592,
        "oz": 0.0283495,
        # Temperature conversions handled separately
        "°C": "celsius",
        "°F": "fahrenheit",
        "K": "kelvin",
    }

    # Handle temperature conversions
    if from_unit in ["°C", "°F", "K"] and to_unit in ["°C", "°F", "K"]:
        # Convert to Celsius first
        if from_unit == "°F":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "K":
            celsius = value - 273.15
        else:
            celsius = value

        # Convert from Celsius to target
        if to_unit == "°F":
            result = celsius * 9 / 5 + 32
        elif to_unit == "K":
            result = celsius + 273.15
        else:
            result = celsius

        return f"{value} {from_unit} = {result:.4f} {to_unit}"

    # Handle other conversions
    if from_unit not in conversions or to_unit not in conversions:
        return f"Error: Unknown unit(s). Supported units: {', '.join(conversions.keys())}"

    # Check if units are compatible (same dimension)
    length_units = ["m", "km", "cm", "mm", "ft", "in", "mi"]
    weight_units = ["kg", "g", "mg", "lb", "oz"]

    from_is_length = from_unit in length_units
    to_is_length = to_unit in length_units
    from_is_weight = from_unit in weight_units
    to_is_weight = to_unit in weight_units

    if (from_is_length != to_is_length) or (from_is_weight != to_is_weight):
        return "Error: Cannot convert between different unit types"

    # Perform conversion
    base_value = value * conversions[from_unit]
    result = base_value / conversions[to_unit]

    return f"{value} {from_unit} = {result:.6f} {to_unit}"


# Create interfaces for each function
calc_interface = gr.Interface(
    fn=basic_calculator,
    inputs=gr.Textbox(
        label="Expression",
        placeholder="Enter mathematical expression (e.g., 2 + 2 * 3, sqrt(16), sin(pi/2))",
    ),
    outputs=gr.Textbox(label="Result"),
    title="Calculator",
    description="Evaluate mathematical expressions safely",
    examples=[
        ["2 + 2 * 3"],
        ["sqrt(16) + pow(2, 3)"],
        ["sin(pi/2) + cos(0)"],
        ["log(100) / log(10)"],
    ],
)

quadratic_interface = gr.Interface(
    fn=quadratic_solver,
    inputs=[
        gr.Number(label="a (coefficient of x²)"),
        gr.Number(label="b (coefficient of x)"),
        gr.Number(label="c (constant term)"),
    ],
    outputs=gr.Textbox(label="Solution"),
    title="Quadratic Equation Solver",
    description="Solve quadratic equations of the form ax² + bx + c = 0",
    examples=[
        [1, -5, 6],  # x² - 5x + 6 = 0 → x = 2, 3
        [1, 0, -4],  # x² - 4 = 0 → x = ±2
        [1, 2, 5],  # x² + 2x + 5 = 0 → complex solutions
    ],
)

converter_interface = gr.Interface(
    fn=unit_converter,
    inputs=[
        gr.Number(label="Value"),
        gr.Textbox(label="From Unit", placeholder="e.g., m, kg, °C"),
        gr.Textbox(label="To Unit", placeholder="e.g., ft, lb, °F"),
    ],
    outputs=gr.Textbox(label="Result"),
    title="Unit Converter",
    description="Convert between different units of measurement",
    examples=[[100, "m", "ft"], [5, "kg", "lb"], [25, "°C", "°F"], [1, "mi", "km"]],
)

# Create tabbed interface combining all tools
demo = gr.TabbedInterface(
    [calc_interface, quadratic_interface, converter_interface],
    ["Calculator", "Quadratic Solver", "Unit Converter"],
    title="Mathematical Tools MCP Server",
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
