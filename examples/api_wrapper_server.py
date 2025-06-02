"""API Wrapper Gradio MCP Server Example

This example demonstrates how to wrap external APIs as MCP tools.
"""

import gradio as gr
import requests
import json
from typing import Optional


def weather_api(city: str, units: str = "metric") -> str:
    """Get weather information for a city (mock implementation).
    
    Args:
        city: City name
        units: Temperature units (metric or imperial)
        
    Returns:
        Weather information as JSON
    """
    # In a real implementation, you would call an actual weather API
    # This is a mock response for demonstration
    mock_weather = {
        "city": city,
        "temperature": 22 if units == "metric" else 72,
        "unit": "°C" if units == "metric" else "°F",
        "condition": "Partly cloudy",
        "humidity": "65%",
        "wind_speed": "10 km/h" if units == "metric" else "6 mph"
    }
    
    return json.dumps(mock_weather, indent=2)


def github_repo_info(owner: str, repo: str) -> str:
    """Get GitHub repository information.
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        Repository information as JSON
    """
    try:
        # Make actual API call to GitHub
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Extract relevant information
            info = {
                "name": data.get("name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "language": data.get("language"),
                "created": data.get("created_at"),
                "updated": data.get("updated_at"),
                "url": data.get("html_url")
            }
            return json.dumps(info, indent=2)
        else:
            return f"Error: GitHub API returned status {response.status_code}"
            
    except requests.RequestException as e:
        return f"Error making request: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def ip_geolocation(ip_address: Optional[str] = None) -> str:
    """Get geolocation information for an IP address.
    
    Args:
        ip_address: IP address to lookup (empty for current IP)
        
    Returns:
        Geolocation information as JSON
    """
    try:
        # Use ip-api.com for geolocation (free tier available)
        url = "http://ip-api.com/json/"
        if ip_address:
            url += ip_address
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2)
        else:
            return f"Error: API returned status {response.status_code}"
            
    except requests.RequestException as e:
        return f"Error making request: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def exchange_rates(base_currency: str = "USD", target_currency: str = "EUR") -> str:
    """Get exchange rate between currencies (mock implementation).
    
    Args:
        base_currency: Base currency code
        target_currency: Target currency code
        
    Returns:
        Exchange rate information as JSON
    """
    # Mock exchange rates for demonstration
    mock_rates = {
        "USD": {"EUR": 0.85, "GBP": 0.73, "JPY": 110.0, "CAD": 1.25},
        "EUR": {"USD": 1.18, "GBP": 0.86, "JPY": 129.0, "CAD": 1.47},
        "GBP": {"USD": 1.37, "EUR": 1.16, "JPY": 150.0, "CAD": 1.71}
    }
    
    base_currency = base_currency.upper()
    target_currency = target_currency.upper()
    
    if base_currency in mock_rates and target_currency in mock_rates[base_currency]:
        rate = mock_rates[base_currency][target_currency]
        result = {
            "base": base_currency,
            "target": target_currency,
            "rate": rate,
            "amount": 1,
            "converted": rate,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        return json.dumps(result, indent=2)
    else:
        return json.dumps({
            "error": f"Exchange rate not available for {base_currency} to {target_currency}"
        }, indent=2)


# Create interfaces for each API
weather_interface = gr.Interface(
    fn=weather_api,
    inputs=[
        gr.Textbox(label="City Name", value="London"),
        gr.Radio(["metric", "imperial"], label="Units", value="metric")
    ],
    outputs=gr.Textbox(label="Weather Data", lines=8),
    title="Weather API",
    description="Get weather information for any city"
)

github_interface = gr.Interface(
    fn=github_repo_info,
    inputs=[
        gr.Textbox(label="Repository Owner", value="gradio-app"),
        gr.Textbox(label="Repository Name", value="gradio")
    ],
    outputs=gr.Textbox(label="Repository Info", lines=12),
    title="GitHub Repository Info",
    description="Get information about a GitHub repository"
)

ip_interface = gr.Interface(
    fn=ip_geolocation,
    inputs=gr.Textbox(
        label="IP Address (leave empty for your IP)",
        placeholder="8.8.8.8"
    ),
    outputs=gr.Textbox(label="Geolocation Data", lines=12),
    title="IP Geolocation",
    description="Get geolocation information for an IP address"
)

exchange_interface = gr.Interface(
    fn=exchange_rates,
    inputs=[
        gr.Textbox(label="Base Currency", value="USD"),
        gr.Textbox(label="Target Currency", value="EUR")
    ],
    outputs=gr.Textbox(label="Exchange Rate", lines=8),
    title="Currency Exchange Rates",
    description="Get exchange rates between currencies"
)

# Combine all API interfaces
demo = gr.TabbedInterface(
    [weather_interface, github_interface, ip_interface, exchange_interface],
    ["Weather", "GitHub", "IP Lookup", "Exchange Rates"],
    title="API Wrapper MCP Server",
    analytics_enabled=False
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port=7861,
        mcp_server=True,
        server_name="0.0.0.0",
        share=False
    )
