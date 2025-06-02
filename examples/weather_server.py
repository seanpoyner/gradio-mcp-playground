"""Weather Info - Example Gradio MCP Server

An example MCP server that provides weather information (simulated).
"""

import gradio as gr
import random
from datetime import datetime


def get_weather(city: str) -> str:
    """Get weather information for a city.
    
    Args:
        city: Name of the city
        
    Returns:
        Weather information as formatted text
    """
    # Simulated weather data
    temperatures = range(10, 35)
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Foggy", "Windy"]
    humidity = range(30, 90)
    
    temp = random.choice(temperatures)
    condition = random.choice(conditions)
    humid = random.choice(humidity)
    
    return f"""Weather for {city}:
🌡️ Temperature: {temp}°C
☁️ Condition: {condition}
💧 Humidity: {humid}%
🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""


def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.
    
    Args:
        city: Name of the city
        days: Number of days to forecast (1-7)
        
    Returns:
        Weather forecast as formatted text
    """
    if days < 1 or days > 7:
        return "Please enter a number between 1 and 7 for days."
    
    forecast = f"📅 {days}-Day Forecast for {city}:\n\n"
    
    conditions = ["☀️ Sunny", "☁️ Cloudy", "🌧️ Rainy", "⛅ Partly Cloudy"]
    
    for i in range(days):
        temp_high = random.randint(20, 30)
        temp_low = random.randint(10, 20)
        condition = random.choice(conditions)
        
        forecast += f"Day {i+1}: {condition}, High: {temp_high}°C, Low: {temp_low}°C\n"
    
    return forecast


# Create interfaces
weather_interface = gr.Interface(
    fn=get_weather,
    inputs=gr.Textbox(label="City", placeholder="Enter city name..."),
    outputs=gr.Textbox(label="Current Weather"),
    title="Current Weather",
    description="Get current weather information for any city",
    examples=[["New York"], ["London"], ["Tokyo"], ["Sydney"]]
)

forecast_interface = gr.Interface(
    fn=get_forecast,
    inputs=[
        gr.Textbox(label="City", placeholder="Enter city name..."),
        gr.Slider(minimum=1, maximum=7, value=3, step=1, label="Days")
    ],
    outputs=gr.Textbox(label="Weather Forecast"),
    title="Weather Forecast",
    description="Get weather forecast for up to 7 days",
    examples=[["Paris", 3], ["Berlin", 5], ["Mumbai", 7]]
)

# Combine interfaces
demo = gr.TabbedInterface(
    [weather_interface, forecast_interface],
    ["Current Weather", "Forecast"],
    title="Weather Information Service"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        mcp_server=True,
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860
    )
