# Basic Text Processor Template

This is a simple Gradio MCP server template that demonstrates how to create a basic text processing tool.

## Features

- Single text input/output interface
- MCP server support enabled
- Ready to be used with Claude Desktop, Cursor, or other MCP clients

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python app.py
   ```

3. The server will start on port 7860 (by default)

4. Connect to it using an MCP client

## Customization

Edit `app.py` to:
- Change the processing logic in the `process_text` function
- Modify the UI components
- Add more examples
- Change the server configuration
