---
title: "Gradio MCP Playground: Comprehensive User Guide"
subtitle: "Build, Deploy, and Manage AI-Powered Gradio Apps as MCP Servers"
author: "Gradio MCP Playground Contributors"
date: \today
documentclass: article
geometry: margin=1in
fontsize: 11pt
linestretch: 1.2
colorlinks: true
linkcolor: blue
urlcolor: blue
citecolor: blue
toccolor: black
toc: true
toc-depth: 3
numbersections: true
header-includes:
  - \usepackage{xcolor}
  - \usepackage{fancyhdr}
  - \usepackage{graphicx}
  - \usepackage{listings}
  - \usepackage{booktabs}
  - \usepackage{hyperref}
  - \usepackage{amsmath}
  - \usepackage{amsfonts}
  - \usepackage{amssymb}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \fancyhead[L]{Gradio MCP Playground User Guide}
  - \fancyhead[R]{\thepage}
  - \renewcommand{\headrulewidth}{0.4pt}
  - \lstset{basicstyle=\ttfamily\footnotesize, breaklines=true, frame=single, backgroundcolor=\color{gray!10}}
---

# Executive Summary

The **Gradio MCP Playground** is a comprehensive toolkit that revolutionizes how developers create, deploy, and manage AI-powered applications by seamlessly bridging Gradio interfaces with the Model Context Protocol (MCP). This toolkit enables developers to transform any Gradio application into a fully-functional MCP server with minimal code changes, making AI tools accessible to Claude Desktop, Cursor, Cline, and other MCP-compatible clients.

## Key Benefits

- **Rapid Development**: Transform existing Gradio apps into MCP servers with a single line of code
- **Universal Compatibility**: Works with any MCP-compatible client including Claude Desktop
- **Production Ready**: Built-in monitoring, deployment tools, and enterprise features
- **Developer Friendly**: Comprehensive CLI, web dashboard, and extensive documentation

---

# Introduction

## What is Gradio MCP Playground?

Gradio MCP Playground is a sophisticated toolkit designed to bridge the gap between Gradio's intuitive interface creation capabilities and the Model Context Protocol's powerful tool integration system. It provides developers with everything needed to create professional-grade AI tools that can be seamlessly integrated into various AI assistants and development environments.

## Architecture Overview

The toolkit consists of several interconnected components:

1. **Core Framework**: Python package for creating MCP servers from Gradio apps
2. **Command Line Interface (CLI)**: Comprehensive management tools via `gmp` command
3. **Web Dashboard**: Visual interface for monitoring and managing servers
4. **Template System**: Pre-built templates for common use cases
5. **Registry System**: Discovery and sharing of MCP servers
6. **Deployment Tools**: One-click deployment to cloud platforms

## Prerequisites

- **Python**: Version 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Dependencies**: Gradio 4.44.0+, MCP 1.0.0+
- **Optional**: Hugging Face account for deployment

---

# Installation and Setup

## Standard Installation

Install the package via pip:

```bash
pip install gradio-mcp-playground
```

## Complete Installation with All Features

For full functionality including all optional dependencies:

```bash
pip install "gradio-mcp-playground[all]"
```

## Development Installation

For contributors and developers:

```bash
git clone https://github.com/gradio-mcp-playground/gradio-mcp-playground.git
cd gradio-mcp-playground
pip install -e ".[dev,all]"
```

## Troubleshooting Installation Issues

### Common Error: "mcp (optional) missing"

If you encounter dependency issues:

```bash
# Install MCP specifically
pip install mcp>=1.0.0

# Verify installation
python check_dependencies.py

# Complete installation
pip install -e .
```

### Windows-Specific Issues

On Windows systems, use:

```cmd
pip install --user -e .
pip install --user mcp>=1.0.0 gradio>=4.44.0
```

## Initial Configuration

Run the interactive setup wizard:

```bash
gmp setup
```

This wizard configures:
- Default port settings
- MCP protocol preferences
- Hugging Face integration
- Development environment options
- Logging preferences

---

# Quick Start Guide

## Creating Your First MCP Server

### Method 1: From Scratch

Create a simple greeting server:

```python
import gradio as gr

def greet(name: str) -> str:
    """Greet someone by name.
    
    Args:
        name: The name of the person to greet
        
    Returns:
        A personalized greeting message
    """
    if not name.strip():
        return "Hello there! Please enter your name."
    return f"Hello, {name}! Welcome to Gradio MCP Playground!"

# Create Gradio interface
demo = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="Your Name", placeholder="Enter your name..."),
    outputs=gr.Textbox(label="Greeting"),
    title="Personal Greeter",
    description="A simple greeting tool that can be used by AI assistants"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=True)
```

### Method 2: Using Templates

Create from a pre-built template:

```bash
# List available templates
gmp server list-templates

# Create a calculator server
gmp server create my-calculator --template calculator

# Navigate and start
cd my-calculator
python app.py
```

### Method 3: Using the CLI

```bash
# Interactive server creation
gmp server create my-first-server

# Start the server
gmp server start my-first-server --port 7860

# Monitor via dashboard
gmp dashboard
```

---

# Core Concepts

## MCP Server Architecture

### Tool Definition

Every function in your Gradio interface becomes an MCP tool:

```python
def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of text.
    
    Args:
        text: Text to analyze for sentiment
        
    Returns:
        Dictionary containing sentiment analysis results
    """
    # Your sentiment analysis logic
    return {
        "sentiment": "positive",
        "confidence": 0.95,
        "emotions": ["joy", "satisfaction"]
    }
```

### Resource Management

Handle file uploads and processing:

```python
def process_document(file_path: str, operation: str) -> str:
    """Process uploaded documents.
    
    Args:
        file_path: Path to the uploaded file
        operation: Type of processing to perform
        
    Returns:
        Processing results as text
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    if operation == "summarize":
        return f"Summary: {content[:100]}..."
    elif operation == "word_count":
        return f"Word count: {len(content.split())}"
    
    return "Processing complete"
```

## Communication Protocols

### STDIO Protocol

Direct standard input/output communication:

```python
demo.launch(
    mcp_server=True,
    mcp_protocol="stdio"
)
```

### Server-Sent Events (SSE)

HTTP-based communication for web clients:

```python
demo.launch(
    mcp_server=True,
    mcp_protocol="sse",
    server_port=7860
)
```

---

# Advanced Usage Examples

## Multi-Tool Server

Create a server with multiple specialized tools:

```python
import gradio as gr
from gradio_mcp_playground import MCPServer
import json
import re
from datetime import datetime

# Initialize custom MCP server
mcp_server = MCPServer(
    name="productivity-suite",
    version="1.0.0",
    description="A comprehensive productivity toolkit"
)

@mcp_server.tool()
def format_json(json_string: str) -> str:
    """Format and validate JSON strings.
    
    Args:
        json_string: Raw JSON string to format
        
    Returns:
        Formatted JSON or error message
    """
    try:
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        return f"JSON Error: {str(e)}"

@mcp_server.tool()
def extract_emails(text: str) -> list:
    """Extract email addresses from text.
    
    Args:
        text: Text content to search for emails
        
    Returns:
        List of email addresses found
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return list(set(emails))  # Remove duplicates

@mcp_server.tool()
def calculate_age(birth_date: str) -> dict:
    """Calculate age from birth date.
    
    Args:
        birth_date: Birth date in YYYY-MM-DD format
        
    Returns:
        Dictionary with age information
    """
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        
        return {
            "years": age,
            "days": (today - birth).days,
            "next_birthday": f"{birth.month:02d}-{birth.day:02d}"
        }
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

# Create Gradio interfaces for each tool
json_formatter = gr.Interface(
    fn=format_json,
    inputs=gr.Textbox(label="JSON String", lines=10),
    outputs=gr.Textbox(label="Formatted JSON", lines=10),
    title="JSON Formatter"
)

email_extractor = gr.Interface(
    fn=extract_emails,
    inputs=gr.Textbox(label="Text Content", lines=5),
    outputs=gr.JSON(label="Extracted Emails"),
    title="Email Extractor"
)

age_calculator = gr.Interface(
    fn=calculate_age,
    inputs=gr.Textbox(label="Birth Date (YYYY-MM-DD)", placeholder="1990-01-15"),
    outputs=gr.JSON(label="Age Information"),
    title="Age Calculator"
)

# Combine interfaces
demo = gr.TabbedInterface(
    [json_formatter, email_extractor, age_calculator],
    ["JSON Formatter", "Email Extractor", "Age Calculator"],
    title="Productivity Suite"
)

# Launch with custom MCP server
if __name__ == "__main__":
    demo.launch(mcp_server=mcp_server, share=False)
```

## File Processing Server

Handle various file types and operations:

```python
import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64

def process_csv(file_path: str, operation: str, column: str = "") -> tuple:
    """Process CSV files with various operations.
    
    Args:
        file_path: Path to uploaded CSV file
        operation: Type of operation (stats, plot, filter)
        column: Column name for operations
        
    Returns:
        Tuple of (text_result, plot_image)
    """
    try:
        df = pd.read_csv(file_path)
        
        if operation == "stats":
            if column and column in df.columns:
                stats = df[column].describe().to_string()
                return f"Statistics for '{column}':\n{stats}", None
            else:
                return f"Dataset shape: {df.shape}\nColumns: {list(df.columns)}", None
        
        elif operation == "plot" and column:
            if column in df.columns:
                plt.figure(figsize=(10, 6))
                if df[column].dtype in ['int64', 'float64']:
                    df[column].hist(bins=20)
                    plt.title(f"Distribution of {column}")
                    plt.xlabel(column)
                    plt.ylabel("Frequency")
                else:
                    df[column].value_counts().plot(kind='bar')
                    plt.title(f"Count of {column}")
                    plt.xticks(rotation=45)
                
                plt.tight_layout()
                plot_path = "temp_plot.png"
                plt.savefig(plot_path)
                plt.close()
                return f"Plot generated for '{column}'", plot_path
        
        elif operation == "filter" and column:
            if column in df.columns:
                # Simple filter: show top 10 rows
                filtered = df.head(10)
                return f"First 10 rows:\n{filtered.to_string()}", None
        
        return "Operation completed", None
        
    except Exception as e:
        return f"Error processing file: {str(e)}", None

def resize_image(image_file: str, width: int, height: int) -> str:
    """Resize uploaded images.
    
    Args:
        image_file: Path to uploaded image
        width: Target width in pixels
        height: Target height in pixels
        
    Returns:
        Path to resized image
    """
    try:
        img = Image.open(image_file)
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        output_path = "resized_image.png"
        resized_img.save(output_path)
        
        return output_path
    except Exception as e:
        return f"Error resizing image: {str(e)}"

# Create interfaces
csv_processor = gr.Interface(
    fn=process_csv,
    inputs=[
        gr.File(label="CSV File"),
        gr.Radio(["stats", "plot", "filter"], label="Operation"),
        gr.Textbox(label="Column Name (for plot/filter)", value="")
    ],
    outputs=[
        gr.Textbox(label="Results"),
        gr.Image(label="Plot")
    ],
    title="CSV Processor"
)

image_resizer = gr.Interface(
    fn=resize_image,
    inputs=[
        gr.File(label="Image File"),
        gr.Number(label="Width", value=800),
        gr.Number(label="Height", value=600)
    ],
    outputs=gr.Image(label="Resized Image"),
    title="Image Resizer"
)

# Combine interfaces
demo = gr.TabbedInterface(
    [csv_processor, image_resizer],
    ["CSV Processor", "Image Resizer"],
    title="File Processing Suite"
)

if __name__ == "__main__":
    demo.launch(mcp_server=True)
```

---

# Command Line Interface Reference

## Server Management Commands

### Creating Servers

```bash
# Create from template
gmp server create my-app --template calculator

# Create with custom settings
gmp server create my-app --port 8080 --directory ./servers

# Interactive creation
gmp server create
```

### Managing Servers

```bash
# List all servers
gmp server list

# Show detailed server information
gmp server info my-app

# Start a server
gmp server start my-app --port 7860 --reload

# Stop a server
gmp server stop my-app

# Delete a server (from registry only)
gmp server delete my-app

# Delete a server including all files
gmp server delete my-app --files

# Force delete without confirmation
gmp server delete my-app --force --files
```

### Server Configuration

```bash
# Edit server configuration
gmp server config my-app

# Validate server configuration
gmp server validate my-app

# Export server configuration
gmp server export my-app --format json
```

### Server Deletion

The delete command provides flexible options for removing servers from your system:

```bash
# Delete server from registry only (keeps files)
gmp server delete my-app

# Delete server and all associated files
gmp server delete my-app --files

# Force deletion without confirmation prompts
gmp server delete my-app --force

# Combine options for complete removal
gmp server delete my-app --files --force
```

**Important Safety Features:**

- **Registry vs Files**: By default, delete only removes the server from the registry, preserving files
- **Safety Checks**: Without `--force`, the command will check for unexpected files before deletion
- **Confirmation Prompts**: Interactive confirmation prevents accidental deletions
- **Process Management**: Automatically stops running server processes before deletion

**Use Cases:**

1. **Clean Removal**: `gmp server delete my-app --files` - Remove everything cleanly
2. **Registry Cleanup**: `gmp server delete my-app` - Keep files, remove from management
3. **Automated Scripts**: `gmp server delete my-app --files --force` - Non-interactive deletion
4. **Safe Testing**: Default behavior prevents accidental data loss

## Client Management Commands

### Connection Management

```bash
# Connect to a server
gmp client connect http://localhost:7860/mcp --name local-server

# List saved connections
gmp client list

# Test a connection
gmp client test local-server

# Remove a connection
gmp client remove local-server
```

### Tool Interaction

```bash
# List available tools on a server
gmp client tools local-server

# Call a tool
gmp client call local-server greet --args '{"name": "World"}'

# Interactive tool testing
gmp client interactive local-server
```

## Registry Commands

### Searching and Discovery

```bash
# Search for servers
gmp registry search "image processing"

# Browse by category
gmp registry search --category "data-analysis"

# List all categories
gmp registry categories

# Show trending servers
gmp registry trending
```

### Publishing

```bash
# Publish server to registry
gmp registry publish my-app

# Update published server
gmp registry update my-app

# Remove from registry
gmp registry unpublish my-app
```

## Deployment Commands

### Hugging Face Spaces

```bash
# Deploy to Hugging Face Spaces
gmp deploy my-app --platform huggingface --public

# Update existing Space
gmp deploy my-app --update

# Check deployment status
gmp deploy status my-app
```

### Docker Deployment

```bash
# Build Docker image
gmp docker build my-app

# Run in container
gmp docker run my-app --port 7860

# Push to registry
gmp docker push my-app
```

## Development Commands

```bash
# Start development mode with auto-reload
gmp dev server --watch

# Run tests
gmp dev test

# Code formatting
gmp dev format

# Lint code
gmp dev lint

# Generate documentation
gmp dev docs
```

---

# Web Dashboard Guide

## Accessing the Dashboard

Launch the web dashboard:

```bash
gmp dashboard --port 8080 --public
```

## Dashboard Features

### Server Management Panel

- **Server Overview**: Visual status indicators for all servers
- **Quick Actions**: Start, stop, restart servers with one click
- **Resource Monitoring**: CPU, memory, and network usage graphs
- **Log Viewer**: Real-time server logs with filtering options

### Server Creation Wizard

1. **Template Selection**: Choose from pre-built templates
2. **Configuration**: Set server parameters via form interface
3. **Code Editor**: Built-in editor with syntax highlighting
4. **Testing**: Test tools before deployment
5. **Deployment**: One-click deployment options

### Tool Testing Interface

- **Tool Explorer**: Browse available tools on connected servers
- **Interactive Testing**: Test tools with custom inputs
- **Response Viewer**: Formatted display of tool outputs
- **Performance Metrics**: Response times and success rates

### Connection Manager

- **Server Discovery**: Automatically discover local servers
- **Connection Health**: Monitor connection status
- **Protocol Selection**: Switch between STDIO and SSE protocols
- **Authentication**: Manage API keys and tokens

### Deployment Center

- **Platform Integration**: Connect to Hugging Face, Docker registries
- **Deployment History**: Track all deployments
- **Environment Management**: Manage staging and production environments
- **Rollback Options**: Quick rollback to previous versions

---

# Template System

## Available Templates

### Basic Template

Simple single-function server template:

```python
def main_function(input_text: str) -> str:
    """Process input text."""
    return f"Processed: {input_text}"
```

**Use Cases**: Simple text processing, basic calculations, proof of concepts

### Calculator Template

Mathematical operations server:

```python
def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions."""
    # Safe evaluation implementation
    return str(result)

def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between different units."""
    # Unit conversion logic
    return converted_value
```

**Use Cases**: Mathematical tools, unit converters, formula calculators

### Image Generator Template

AI image generation server:

```python
def generate_image(prompt: str, style: str = "realistic") -> str:
    """Generate images from text prompts."""
    # Image generation logic
    return image_path

def edit_image(image_path: str, instructions: str) -> str:
    """Edit existing images based on instructions."""
    # Image editing logic
    return edited_image_path
```

**Use Cases**: AI art generation, image editing, creative tools

### Data Analyzer Template

Data processing and visualization:

```python
def analyze_dataset(file_path: str, analysis_type: str) -> dict:
    """Analyze uploaded datasets."""
    # Data analysis logic
    return analysis_results

def create_visualization(data: dict, chart_type: str) -> str:
    """Create data visualizations."""
    # Visualization logic
    return chart_path
```

**Use Cases**: Business intelligence, research tools, reporting systems

## Creating Custom Templates

### Template Structure

```
template_name/
├── app.py              # Main server file
├── config.yaml         # Template configuration
├── requirements.txt    # Dependencies
├── README.md          # Template documentation
└── examples/          # Usage examples
    └── example_usage.py
```

### Template Configuration (`config.yaml`)

```yaml
name: "my-custom-template"
version: "1.0.0"
description: "Custom template for specific use case"
author: "Your Name"
category: "productivity"
tags: ["custom", "productivity", "automation"]

# Template parameters
parameters:
  - name: "model_name"
    type: "string"
    description: "AI model to use"
    default: "gpt-3.5-turbo"
    required: true
  
  - name: "max_tokens"
    type: "integer"
    description: "Maximum tokens for responses"
    default: 1000
    required: false

# Required dependencies
dependencies:
  - "openai>=1.0.0"
  - "requests>=2.28.0"

# Deployment settings
deployment:
  cpu_requirements: "1 core"
  memory_requirements: "2GB"
  gpu_requirements: "none"
```

### Publishing Templates

```bash
# Validate template
gmp template validate ./my-template

# Package template
gmp template package ./my-template

# Publish to registry
gmp template publish ./my-template
```

---

# Client Integration

## Python Client

### Basic Usage

```python
from gradio_mcp_playground import GradioMCPClient
import asyncio

async def main():
    # Create client instance
    client = GradioMCPClient()
    
    # Connect to server
    await client.connect("http://localhost:7860/mcp")
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[tool['name'] for tool in tools]}")
    
    # Call a tool
    result = await client.call_tool(
        "greet",
        {"name": "Alice"}
    )
    print(f"Result: {result}")
    
    # Disconnect
    await client.disconnect()

# Run the client
asyncio.run(main())
```

### Advanced Client Features

```python
import asyncio
from gradio_mcp_playground import GradioMCPClient

class AdvancedMCPClient:
    def __init__(self):
        self.client = GradioMCPClient()
        self.connected_servers = {}
    
    async def connect_multiple_servers(self, servers: dict):
        """Connect to multiple servers simultaneously."""
        for name, url in servers.items():
            try:
                client = GradioMCPClient()
                await client.connect(url)
                self.connected_servers[name] = client
                print(f"✓ Connected to {name}")
            except Exception as e:
                print(f"✗ Failed to connect to {name}: {e}")
    
    async def parallel_tool_calls(self, calls: list):
        """Execute multiple tool calls in parallel."""
        tasks = []
        for call in calls:
            server_name = call["server"]
            tool_name = call["tool"]
            args = call["args"]
            
            if server_name in self.connected_servers:
                task = self.connected_servers[server_name].call_tool(tool_name, args)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def tool_pipeline(self, pipeline: list):
        """Execute tools in sequence, passing outputs as inputs."""
        current_data = None
        
        for step in pipeline:
            server_name = step["server"]
            tool_name = step["tool"]
            args = step.get("args", {})
            
            # Use output from previous step if specified
            if step.get("use_previous_output") and current_data:
                args.update(current_data)
            
            if server_name in self.connected_servers:
                current_data = await self.connected_servers[server_name].call_tool(
                    tool_name, args
                )
            else:
                raise ValueError(f"Server {server_name} not connected")
        
        return current_data

# Usage example
async def pipeline_example():
    client = AdvancedMCPClient()
    
    # Connect to multiple servers
    servers = {
        "text-processor": "http://localhost:7860/mcp",
        "translator": "http://localhost:7861/mcp",
        "summarizer": "http://localhost:7862/mcp"
    }
    await client.connect_multiple_servers(servers)
    
    # Define processing pipeline
    pipeline = [
        {
            "server": "text-processor",
            "tool": "clean_text",
            "args": {"text": "Hello, World! This is a test."}
        },
        {
            "server": "translator",
            "tool": "translate",
            "args": {"target_language": "es"},
            "use_previous_output": True
        },
        {
            "server": "summarizer",
            "tool": "summarize",
            "args": {"max_length": 50},
            "use_previous_output": True
        }
    ]
    
    # Execute pipeline
    final_result = await client.tool_pipeline(pipeline)
    print(f"Pipeline result: {final_result}")

# Run example
asyncio.run(pipeline_example())
```

## Claude Desktop Integration

### Configuration File

Add to Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gradio-productivity": {
      "command": "python",
      "args": ["/path/to/your/server.py"],
      "env": {
        "GRADIO_MCP_MODE": "stdio"
      }
    },
    "gradio-data-analyzer": {
      "command": "gmp",
      "args": ["server", "start", "data-analyzer", "--stdio"],
      "env": {
        "PORT": "7860"
      }
    }
  }
}
```

### Server Preparation for Claude

```python
import gradio as gr
import os

def analyze_text(text: str, analysis_type: str) -> dict:
    """Analyze text with various methods.
    
    Args:
        text: Text content to analyze
        analysis_type: Type of analysis (sentiment, keywords, summary)
        
    Returns:
        Dictionary containing analysis results
    """
    # Implementation here
    return {"analysis": "results"}

# Configure for Claude integration
demo = gr.Interface(
    fn=analyze_text,
    inputs=[
        gr.Textbox(label="Text to Analyze"),
        gr.Radio(["sentiment", "keywords", "summary"], label="Analysis Type")
    ],
    outputs=gr.JSON(label="Analysis Results"),
    title="Text Analyzer for Claude"
)

if __name__ == "__main__":
    # Check if running in MCP mode for Claude
    mcp_mode = os.getenv("GRADIO_MCP_MODE", "server")
    
    if mcp_mode == "stdio":
        # STDIO mode for Claude Desktop
        demo.launch(mcp_server=True, mcp_protocol="stdio")
    else:
        # Regular server mode
        demo.launch(mcp_server=True, server_port=7860)
```

## JavaScript/Web Integration

### Browser Client

```html
<!DOCTYPE html>
<html>
<head>
    <title>Gradio MCP Web Client</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
</head>
<body>
    <div id="app">
        <h1>Gradio MCP Web Client</h1>
        <div id="tools"></div>
        <div id="results"></div>
    </div>

    <script>
        class GradioMCPWebClient {
            constructor(serverUrl) {
                this.serverUrl = serverUrl;
                this.tools = [];
            }
            
            async connect() {
                try {
                    const response = await axios.get(`${this.serverUrl}/mcp/tools`);
                    this.tools = response.data.tools;
                    this.renderTools();
                } catch (error) {
                    console.error('Connection failed:', error);
                }
            }
            
            async callTool(toolName, args) {
                try {
                    const response = await axios.post(
                        `${this.serverUrl}/mcp/call`,
                        {
                            tool: toolName,
                            arguments: args
                        }
                    );
                    return response.data;
                } catch (error) {
                    console.error('Tool call failed:', error);
                    return { error: error.message };
                }
            }
            
            renderTools() {
                const toolsDiv = document.getElementById('tools');
                toolsDiv.innerHTML = '<h2>Available Tools</h2>';
                
                this.tools.forEach(tool => {
                    const toolDiv = document.createElement('div');
                    toolDiv.innerHTML = `
                        <h3>${tool.name}</h3>
                        <p>${tool.description}</p>
                        <button onclick="testTool('${tool.name}')">Test Tool</button>
                    `;
                    toolsDiv.appendChild(toolDiv);
                });
            }
        }
        
        // Initialize client
        const client = new GradioMCPWebClient('http://localhost:7860');
        client.connect();
        
        async function testTool(toolName) {
            const args = prompt(`Enter arguments for ${toolName} (JSON format):`);
            try {
                const parsedArgs = JSON.parse(args || '{}');
                const result = await client.callTool(toolName, parsedArgs);
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `<h3>Result:</h3><pre>${JSON.stringify(result, null, 2)}</pre>`;
            } catch (error) {
                alert('Invalid JSON arguments');
            }
        }
    </script>
</body>
</html>
```

---

# Deployment Guide

## Local Development Deployment

### Development Server

```bash
# Start with auto-reload
gmp server start my-app --reload --port 7860

# Start with debugging
gmp dev server --debug --watch

# Start multiple servers
gmp server start app1 --port 7860 &
gmp server start app2 --port 7861 &
gmp server start app3 --port 7862 &
```

### Docker Development

```dockerfile
# Dockerfile for development
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Install in development mode
RUN pip install -e .

EXPOSE 7860

CMD ["python", "app.py"]
```

Build and run:

```bash
# Build development image
docker build -t my-gradio-mcp-dev .

# Run with volume mounting for live reload
docker run -p 7860:7860 -v $(pwd):/app my-gradio-mcp-dev
```

## Production Deployment

### Hugging Face Spaces

#### Automatic Deployment

```bash
# Configure Hugging Face token
gmp config set hf_token YOUR_TOKEN

# Deploy with custom settings
gmp deploy my-app \
    --platform huggingface \
    --public \
    --hardware cpu-upgrade \
    --title "My MCP Server" \
    --description "Production MCP server"
```

#### Manual Deployment

Create `app.py` for Hugging Face Spaces:

```python
import gradio as gr
import os

# Your server implementation
def my_tool(input_data: str) -> str:
    """Tool implementation."""
    return f"Processed: {input_data}"

demo = gr.Interface(
    fn=my_tool,
    inputs="text",
    outputs="text",
    title="My MCP Server"
)

if __name__ == "__main__":
    # Hugging Face Spaces configuration
    demo.launch(
        mcp_server=True,
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        share=False
    )
```

Create `requirements.txt`:

```
gradio>=4.44.0
gradio-mcp-playground>=0.1.0
# Add your specific dependencies
```

### Cloud Platforms

#### AWS Deployment

```bash
# Create AWS Lambda deployment package
gmp deploy my-app --platform aws-lambda --region us-east-1

# Deploy to ECS
gmp deploy my-app --platform aws-ecs --cluster my-cluster

# Deploy to EC2
gmp deploy my-app --platform aws-ec2 --instance-type t3.medium
```

#### Google Cloud Platform

```bash
# Deploy to Cloud Run
gmp deploy my-app --platform gcp-cloudrun --region us-central1

# Deploy to App Engine
gmp deploy my-app --platform gcp-appengine --service my-service
```

#### Azure Deployment

```bash
# Deploy to Container Instances
gmp deploy my-app --platform azure-aci --resource-group my-group

# Deploy to App Service
gmp deploy my-app --platform azure-appservice --plan my-plan
```

### Docker Production Deployment

#### Production Dockerfile

```dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /home/app
USER app

# Copy application
COPY --chown=app:app . .

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start application
CMD ["python", "app.py"]
```

#### Docker Compose for Production

```yaml
version: '3.8'

services:
  gradio-mcp-server:
    build: .
    ports:
      - "7860:7860"
    environment:
      - GRADIO_SERVER_NAME=0.0.0.0
      - GRADIO_SERVER_PORT=7860
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - gradio-mcp-server
    restart: unless-stopped

volumes:
  ssl_data:
```

## Monitoring and Maintenance

### Health Checks

```python
import gradio as gr
from datetime import datetime

def health_check() -> dict:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Add health check to your server
@app.route("/health")
def health():
    return health_check()
```

### Logging Configuration

```python
import logging
import os

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def my_tool(input_data: str) -> str:
    """Tool with logging."""
    logger.info(f"Processing input: {input_data[:50]}...")
    
    try:
        result = process_data(input_data)
        logger.info("Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise
```

### Monitoring Dashboard

```bash
# Start monitoring dashboard
gmp monitor start --port 8080

# View metrics
gmp monitor metrics my-app

# Generate reports
gmp monitor report my-app --period 24h --format json
```

---

# Troubleshooting

## Common Issues and Solutions

### Installation Problems

#### Issue: "mcp (optional) missing - some features will be limited"

**Solution:**
```bash
# Install MCP package explicitly
pip install mcp>=1.0.0

# Verify installation
python -c "import mcp; print('MCP installed successfully')"

# Reinstall if needed
pip uninstall mcp gradio-mcp-playground
pip install gradio-mcp-playground[all]
```

#### Issue: "ModuleNotFoundError: No module named 'gradio_mcp_playground'"

**Solution:**
```bash
# Install in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"

# Verify installation
pip list | grep gradio-mcp-playground
```

#### Issue: CLI commands not working

**Solution:**
```bash
# Check if CLI is installed
which gmp  # On Unix/Linux/macOS
where gmp  # On Windows

# Reinstall with CLI tools
pip install --force-reinstall gradio-mcp-playground

# Check executable path
python -m gradio_mcp_playground.cli --help
```

### Runtime Issues

#### Issue: Server fails to start

**Debugging Steps:**
```bash
# Check dependencies
python check_dependencies.py

# Validate server configuration
gmp server validate my-app

# Start with debug mode
gmp server start my-app --debug

# Check logs
gmp server logs my-app
```

#### Issue: Connection refused

**Solution:**
```bash
# Check if port is available
netstat -an | grep 7860  # Unix/Linux
netstat -an | findstr 7860  # Windows

# Try different port
gmp server start my-app --port 8080

# Check firewall settings
# Allow port 7860 in firewall configuration
```

#### Issue: MCP protocol errors

**Solution:**
```python
# Ensure proper protocol configuration
demo.launch(
    mcp_server=True,
    mcp_protocol="stdio",  # or "sse"
    mcp_timeout=30
)

# Test protocol connectivity
gmp client test --protocol stdio localhost:7860
```

### Performance Issues

#### Issue: Slow response times

**Optimization:**
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(data: str) -> str:
    """Cached expensive operation."""
    # Your expensive computation
    return result

# Use async operations
import asyncio

async def async_tool(data: str) -> str:
    """Async tool implementation."""
    result = await async_operation(data)
    return result
```

#### Issue: High memory usage

**Solution:**
```python
# Optimize memory usage
import gc

def memory_efficient_tool(data: str) -> str:
    """Memory-efficient tool."""
    try:
        # Process data in chunks
        result = process_in_chunks(data)
        return result
    finally:
        # Force garbage collection
        gc.collect()

# Monitor memory usage
import psutil
import os

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB
```

### Deployment Issues

#### Issue: Hugging Face Spaces deployment fails

**Solution:**
```bash
# Check token permissions
gmp config get hf_token

# Validate Space configuration
gmp deploy validate my-app

# Try manual deployment
git clone https://huggingface.co/spaces/username/my-app
# Copy files and push manually
```

#### Issue: Docker build fails

**Solution:**
```dockerfile
# Use more specific base image
FROM python:3.11-slim-bullseye

# Add build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies separately for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .
```

### Client Integration Issues

#### Issue: Claude Desktop not recognizing server

**Solution:**
```json
{
  "mcpServers": {
    "my-gradio-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/gradio-mcp-playground",
        "GRADIO_MCP_MODE": "stdio"
      }
    }
  }
}
```

#### Issue: Tool calls failing

**Debugging:**
```python
# Add detailed error handling
def robust_tool(input_data: str) -> dict:
    """Tool with comprehensive error handling."""
    try:
        # Validate input
        if not input_data or not input_data.strip():
            return {"error": "Empty input provided"}
        
        # Process data
        result = process_data(input_data)
        
        # Validate output
        if not result:
            return {"error": "Processing returned empty result"}
        
        return {"success": True, "result": result}
        
    except ValueError as e:
        return {"error": f"Invalid input: {str(e)}"}
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}
```

## Diagnostic Tools

### Built-in Diagnostics

```bash
# Run comprehensive diagnostics
python run_all_tests.py

# Check specific components
python test_imports.py
python test_mcp_functionality.py
python test_cli_comprehensive.py

# Validate dependencies
python check_dependencies.py

# Test server functionality
gmp test my-app --comprehensive
```

### Custom Diagnostics

```python
#!/usr/bin/env python3
"""Custom diagnostic script for Gradio MCP Playground."""

import sys
import importlib
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    if version < (3, 8):
        print(f"❌ Python {version.major}.{version.minor} not supported. Need 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check required dependencies."""
    required = [
        'gradio',
        'mcp',
        'click',
        'rich',
        'pydantic',
        'aiohttp'
    ]
    
    missing = []
    for dep in required:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing.append(dep)
    
    return len(missing) == 0

def check_cli_installation():
    """Check CLI installation."""
    try:
        result = subprocess.run(['gmp', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ CLI installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ CLI not working")
            return False
    except FileNotFoundError:
        print("❌ CLI not found in PATH")
        return False

def check_server_creation():
    """Test server creation."""
    try:
        # Try to import server components
        from gradio_mcp_playground import ServerRegistry
        registry = ServerRegistry()
        templates = registry.list_templates()
        print(f"✅ Server creation: {len(templates)} templates available")
        return True
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return False

def main():
    """Run all diagnostic checks."""
    print("🔍 Gradio MCP Playground Diagnostics\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("CLI Installation", check_cli_installation),
        ("Server Creation", check_server_creation)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        results.append(check_func())
    
    print(f"\n📊 Summary: {sum(results)}/{len(results)} checks passed")
    
    if not all(results):
        print("\n🔧 Recommended fixes:")
        print("1. pip install --upgrade gradio-mcp-playground[all]")
        print("2. pip install --force-reinstall mcp>=1.0.0")
        print("3. Check PATH for CLI tools")
        
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

Run diagnostics:

```bash
# Save as diagnose.py and run
python diagnose.py

# Or use built-in diagnostics
gmp diagnose --full
```

---

# Best Practices

## Code Organization

### Project Structure

```
my-gradio-mcp-server/
├── app.py                 # Main server file
├── config.yaml           # Configuration
├── requirements.txt       # Dependencies
├── README.md             # Documentation
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Multi-service setup
├── tests/               # Test files
│   ├── test_tools.py
│   └── test_server.py
├── src/                 # Source code
│   ├── __init__.py
│   ├── tools/           # Tool implementations
│   │   ├── __init__.py
│   │   ├── text_tools.py
│   │   └── image_tools.py
│   ├── utils/           # Utility functions
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── config/          # Configuration modules
│       ├── __init__.py
│       └── settings.py
└── docs/                # Documentation
    ├── api.md
    └── deployment.md
```

### Tool Organization

```python
# tools/text_tools.py
"""Text processing tools."""

from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """Text processing utilities."""
    
    def __init__(self):
        self.word_count_cache = {}
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        logger.info(f"Cleaning text: {len(text)} characters")
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters if needed
        cleaned = re.sub(r'[^\w\s.,!?-]', '', cleaned)
        
        logger.info(f"Cleaned text: {len(cleaned)} characters")
        return cleaned
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = text.lower().split()
        word_freq = {}
        
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:max_keywords]]

# tools/__init__.py
"""Tool implementations."""

from .text_tools import TextProcessor
from .image_tools import ImageProcessor

__all__ = ['TextProcessor', 'ImageProcessor']
```

### Configuration Management

```python
# config/settings.py
"""Application settings."""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Server settings
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=7860, env="SERVER_PORT")
    
    # MCP settings
    mcp_protocol: str = Field(default="auto", env="MCP_PROTOCOL")
    mcp_timeout: int = Field(default=30, env="MCP_TIMEOUT")
    
    # Feature flags
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    enable_logging: bool = Field(default=True, env="ENABLE_LOGGING")
    
    # API keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    huggingface_token: Optional[str] = Field(default=None, env="HF_TOKEN")
    
    # Performance settings
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT")
    cache_size: int = Field(default=100, env="CACHE_SIZE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Initialize settings
settings = Settings()
```

## Error Handling

### Comprehensive Error Handling

```python
import logging
from typing import Any, Dict, Union
from functools import wraps

logger = logging.getLogger(__name__)

class MCPError(Exception):
    """Base MCP error class."""
    pass

class ValidationError(MCPError):
    """Input validation error."""
    pass

class ProcessingError(MCPError):
    """Processing error."""
    pass

def handle_errors(func):
    """Decorator for comprehensive error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            result = func(*args, **kwargs)
            return {
                "success": True,
                "data": result,
                "error": None
            }
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Invalid input: {str(e)}"
            }
        except ProcessingError as e:
            logger.error(f"Processing error in {func.__name__}: {e}")
            return {
                "success": False,
                "data": None,
                "error": f"Processing failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": "An unexpected error occurred"
            }
    
    return wrapper

@handle_errors
def process_text_with_validation(text: str) -> str:
    """Process text with proper validation."""
    # Input validation
    if not isinstance(text, str):
        raise ValidationError("Input must be a string")
    
    if not text.strip():
        raise ValidationError("Text cannot be empty")
    
    if len(text) > 10000:
        raise ValidationError("Text too long (max 10,000 characters)")
    
    # Processing
    try:
        result = expensive_text_processing(text)
        if not result:
            raise ProcessingError("Processing returned empty result")
        
        return result
    except Exception as e:
        raise ProcessingError(f"Text processing failed: {e}")
```

## Performance Optimization

### Caching Strategies

```python
import asyncio
import time
from functools import lru_cache, wraps
from typing import Any, Callable

# Simple LRU cache for synchronous functions
@lru_cache(maxsize=100)
def cached_expensive_operation(input_data: str) -> str:
    """Expensive operation with caching."""
    time.sleep(2)  # Simulate expensive computation
    return f"Processed: {input_data}"

# TTL cache implementation
class TTLCache:
    """Time-to-live cache implementation."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Any:
        """Get value from cache if not expired."""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                # Expired, remove from cache
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self.cache[key] = value
        self.timestamps[key] = time.time()

# Global cache instance
ttl_cache = TTLCache(ttl_seconds=300)

def ttl_cached(func: Callable) -> Callable:
    """TTL cache decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
        
        # Try to get from cache
        cached_result = ttl_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache result
        result = func(*args, **kwargs)
        ttl_cache.set(cache_key, result)
        return result
    
    return wrapper

@ttl_cached
def expensive_api_call(query: str) -> dict:
    """Expensive API call with TTL caching."""
    # Simulate API call
    time.sleep(1)
    return {"result": f"API result for {query}"}
```

### Async Processing

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AsyncProcessor:
    """Async processing utilities."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def process_urls(self, urls: list) -> list:
        """Process multiple URLs concurrently."""
        async def fetch_url(url: str) -> dict:
            try:
                async with self.session.get(url) as response:
                    text = await response.text()
                    return {"url": url, "status": response.status, "content": text[:100]}
            except Exception as e:
                return {"url": url, "error": str(e)}
        
        tasks = [fetch_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def cpu_bound_task(self, data: str) -> str:
        """Handle CPU-bound tasks asynchronously."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            expensive_cpu_operation,
            data
        )
        return result

def expensive_cpu_operation(data: str) -> str:
    """CPU-intensive operation."""
    # Simulate heavy computation
    import hashlib
    result = data
    for _ in range(1000):
        result = hashlib.sha256(result.encode()).hexdigest()
    return result[:20]

# Usage in Gradio interface
async def async_tool(input_data: str) -> str:
    """Async tool implementation."""
    async with AsyncProcessor() as processor:
        if input_data.startswith("http"):
            # Process as URL
            results = await processor.process_urls([input_data])
            return str(results[0])
        else:
            # Process as text
            result = await processor.cpu_bound_task(input_data)
            return result
```

## Security Best Practices

### Input Validation and Sanitization

```python
import re
import html
import os
from pathlib import Path
from typing import List, Optional

class SecurityValidator:
    """Input validation and security utilities."""
    
    ALLOWED_FILE_EXTENSIONS = {'.txt', '.csv', '.json', '.md', '.py'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input."""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove potentially dangerous patterns
        sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """Validate file path for security."""
        path = Path(file_path)
        
        # Check if path is absolute and within allowed directory
        if path.is_absolute():
            allowed_dirs = ['/tmp', '/app/uploads']
            if not any(str(path).startswith(allowed) for allowed in allowed_dirs):
                return False
        
        # Check file extension
        if path.suffix.lower() not in SecurityValidator.ALLOWED_FILE_EXTENSIONS:
            return False
        
        # Check file size
        if path.exists() and path.stat().st_size > SecurityValidator.MAX_FILE_SIZE:
            return False
        
        # Check for directory traversal
        if '..' in str(path) or path.name.startswith('.'):
            return False
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL for security."""
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Block local/private IPs
        forbidden_patterns = [
            'localhost',
            '127.0.0.1',
            '192.168.',
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.'
        ]
        
        return not any(pattern in url.lower() for pattern in forbidden_patterns)

def secure_tool(func):
    """Decorator for secure tool implementation."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Sanitize string inputs
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(SecurityValidator.sanitize_text(arg))
            else:
                sanitized_args.append(arg)
        
        # Sanitize string values in kwargs
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = SecurityValidator.sanitize_text(value)
            else:
                sanitized_kwargs[key] = value
        
        return func(*sanitized_args, **sanitized_kwargs)
    
    return wrapper

@secure_tool
def secure_text_processor(text: str) -> str:
    """Securely process text input."""
    # Additional validation
    if len(text) > 50000:
        raise ValueError("Text too long")
    
    # Process the sanitized text
    return f"Securely processed: {text[:100]}..."
```

### Environment Variable Management

```python
import os
from typing import Optional

class SecureConfig:
    """Secure configuration management."""
    
    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment with fallback."""
        value = os.getenv(key, default)
        if value and key.endswith('_KEY') or key.endswith('_TOKEN'):
            # Log that secret was accessed but don't log the value
            logger.info(f"Secret {key} accessed")
        return value
    
    @staticmethod
    def require_secret(key: str) -> str:
        """Get required secret or raise error."""
        value = SecureConfig.get_secret(key)
        if not value:
            raise ValueError(f"Required secret {key} not found")
        return value

# Usage
api_key = SecureConfig.get_secret('OPENAI_API_KEY')
db_password = SecureConfig.require_secret('DATABASE_PASSWORD')
```

---

*This comprehensive guide covers all aspects of the Gradio MCP Playground toolkit. For the latest updates and additional resources, visit the [official documentation](https://gradio-mcp-playground.readthedocs.io/).*